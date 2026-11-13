import ssl
import certifi
import gzip
import urllib.request
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")

# --------------------------------------------------
# PROJECT PATHS AND SETTINGS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"

DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

DATA_FILE = DATA_DIR / "google_trace.csv.gz"

DATA_URL = (
    "https://commondatastorage.googleapis.com/"
    "clusterdata-misc/google-cluster-data-1.csv.gz"
)

INTERVAL_SECONDS = 300
MAX_SERVERS = 100
REPEATED_RUNS = 5  # deterministic reruns for reproducibility checking


# --------------------------------------------------
# 1. DOWNLOAD DATASET
# --------------------------------------------------


def download_dataset():
    if DATA_FILE.exists():
        print("Dataset already exists.")
        return

    print("Downloading Google Cluster workload dataset...")

    try:
        ssl_context = ssl.create_default_context(
            cafile=certifi.where()
        )

        with urllib.request.urlopen(
            DATA_URL,
            context=ssl_context,
            timeout=120
        ) as response:

            with open(DATA_FILE, "wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)

                    if not chunk:
                        break

                    output.write(chunk)

        print("Dataset downloaded successfully.")

    except Exception as error:
        # Remove incomplete download if an error occurs
        if DATA_FILE.exists():
            DATA_FILE.unlink()

        raise RuntimeError(
            "Dataset download failed. Check your internet "
            "connection and SSL certificates."
        ) from error


# --------------------------------------------------
# 2. LOAD AND PROCESS DATA
# --------------------------------------------------

def load_workload():

    print("\nLoading workload dataset...")

    column_names = [
        "time",
        "job_id",
        "task_id",
        "job_type",
        "cpu",
        "memory"
    ]

    data = pd.read_csv(
        DATA_FILE,
        compression="gzip",
        sep=r"\s+",
        header=None,
        names=column_names,
        usecols=[0, 1, 2, 3, 4, 5],
        on_bad_lines="skip"
    )

    data["time"] = pd.to_numeric(data["time"], errors="coerce")
    data["cpu"] = pd.to_numeric(data["cpu"], errors="coerce")

    data = data.dropna(subset=["time", "cpu"])

    # Remove invalid negative CPU values
    data = data[data["cpu"] >= 0]

    # Group task CPU usage into 5-minute intervals
    data["time_bin"] = (
        data["time"] // INTERVAL_SECONDS
    ) * INTERVAL_SECONDS

    workload = (
        data.groupby("time_bin")["cpu"]
        .sum()
        .sort_index()
    )

    # Fill missing time intervals
    full_index = np.arange(
        workload.index.min(),
        workload.index.max() + INTERVAL_SECONDS,
        INTERVAL_SECONDS
    )

    workload = workload.reindex(
        full_index,
        fill_value=0
    )

    workload = workload.reset_index(drop=True)
    workload.name = "cpu_demand"

    if len(workload) < 20:
        raise ValueError(
            "Not enough workload observations were found in the dataset."
        )

    workload.to_csv(
        RESULTS_DIR / "workload_data.csv",
        index_label="time_interval"
    )

    print("Total workload intervals:", len(workload))

    return workload


# --------------------------------------------------
# 3. FORECASTING MODELS
# --------------------------------------------------

def naive_forecast(train, test_length):
    """
    Predict future workload using the last observed value.
    """

    last_value = float(train.iloc[-1])

    return np.full(test_length, last_value)


def holt_forecast(train, test_length):
    """
    Holt's Exponential Smoothing model.
    """

    try:
        model = ExponentialSmoothing(
            train.astype(float),
            trend="add",
            damped_trend=True,
            initialization_method="estimated"
        )

        fitted_model = model.fit(optimized=True)

        predictions = fitted_model.forecast(test_length)

        return np.maximum(
            np.asarray(predictions),
            0
        )

    except Exception as error:
        print("Holt model fallback:", error)

        return naive_forecast(train, test_length)


# --------------------------------------------------
# 4. FORECAST EVALUATION
# --------------------------------------------------

def calculate_metrics(actual, predicted):

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    rmse = np.sqrt(
        np.mean((actual - predicted) ** 2)
    )

    # Ignore zero-demand intervals for MAPE
    nonzero = actual > 0

    if np.any(nonzero):
        mape = np.mean(
            np.abs(
                (actual[nonzero] - predicted[nonzero])
                / actual[nonzero]
            )
        ) * 100
    else:
        mape = 0.0

    return round(rmse, 4), round(mape, 2)


# --------------------------------------------------
# 5. AUTOSCALING SIMULATOR
# --------------------------------------------------

def simulate_autoscaling(
    actual,
    predicted,
    strategy,
    server_capacity,
    initial_servers=1
):
    """Simulate autoscaling without using future actual demand.

    The first interval starts with a warm-start allocation derived from
    the final training observation. At the end of each interval, the
    policy decides capacity for the *next* interval.
    """

    actual = np.asarray(actual, dtype=float)
    servers = max(1, min(int(initial_servers), MAX_SERVERS))

    overload_steps = 0
    wasted_capacity = 0.0
    server_history = []

    for i in range(len(actual)):
        demand = float(actual[i])
        available_capacity = servers * server_capacity

        if demand > available_capacity:
            overload_steps += 1

        wasted_capacity += max(available_capacity - demand, 0.0)
        server_history.append(servers)

        # Decide capacity for the next interval, not the current one.
        if i >= len(actual) - 1:
            continue

        if strategy == "Threshold":
            expected_next_demand = demand
        elif strategy == "Naive Forecast":
            expected_next_demand = float(predicted["Naive"][i + 1])
        elif strategy == "Holt Forecast":
            expected_next_demand = float(predicted["Holt"][i + 1])
        elif strategy == "Hybrid Forecast":
            expected_next_demand = max(
                float(predicted["Holt"][i + 1]), demand
            )
        else:
            raise ValueError("Unknown autoscaling strategy")

        required_servers = int(
            np.ceil(expected_next_demand / (server_capacity * 0.70))
        )
        servers = max(1, min(required_servers, MAX_SERVERS))

    return {
        "SLA_Overload_Steps": overload_steps,
        "Wasted_Capacity": round(wasted_capacity, 2),
        "Average_Servers": round(float(np.mean(server_history)), 2)
    }


# --------------------------------------------------
# 6. RUN EXPERIMENTS
# --------------------------------------------------

def run_experiments(workload):
    """Run the original 70/75/80 splits and five reproducibility reruns.

    The five runs intentionally use identical deterministic inputs. They
    verify repeatability; they are not independent workload samples, so
    their standard deviation is expected to be zero.
    """

    split_ratios = [0.70, 0.75, 0.80]
    strategies = [
        "Threshold", "Naive Forecast", "Holt Forecast", "Hybrid Forecast"
    ]

    forecast_results = []
    scaling_results = []
    repeated_forecast_results = []
    repeated_scaling_results = []
    first_split_data = None

    for split in split_ratios:
        split_percent = int(split * 100)
        print(f"\nRunning experiment with {split_percent}% training data...")

        split_index = int(len(workload) * split)
        train = workload.iloc[:split_index]
        test = workload.iloc[split_index:]
        if len(test) == 0 or len(train) < 2:
            continue

        naive_predictions = naive_forecast(train, len(test))
        holt_predictions = holt_forecast(train, len(test))
        predictions = {"Naive": naive_predictions, "Holt": holt_predictions}

        # Capacity calibration uses training data only.
        server_capacity = max(float(train.quantile(0.90)) / 4, 0.01)
        initial_servers = int(np.ceil(
            float(train.iloc[-1]) / (server_capacity * 0.70)
        ))
        initial_servers = max(1, min(initial_servers, MAX_SERVERS))

        for model_name, predicted in predictions.items():
            rmse, mape = calculate_metrics(test, predicted)
            forecast_results.append({
                "Training_Percentage": split_percent,
                "Model": model_name,
                "RMSE": rmse,
                "MAPE_Percentage": mape
            })

        for strategy in strategies:
            simulation = simulate_autoscaling(
                test, predictions, strategy, server_capacity, initial_servers
            )
            scaling_results.append({
                "Training_Percentage": split_percent,
                "Strategy": strategy,
                **simulation
            })

        # Five deterministic reruns of each split. The run number is
        # recorded so the exact repetition count is auditable.
        for run_number in range(1, REPEATED_RUNS + 1):
            for model_name, predicted in predictions.items():
                rmse, mape = calculate_metrics(test, predicted)
                repeated_forecast_results.append({
                    "Run": run_number,
                    "Training_Percentage": split_percent,
                    "Model": model_name,
                    "RMSE": rmse,
                    "MAPE_Percentage": mape
                })

            for strategy in strategies:
                simulation = simulate_autoscaling(
                    test, predictions, strategy, server_capacity, initial_servers
                )
                repeated_scaling_results.append({
                    "Run": run_number,
                    "Training_Percentage": split_percent,
                    "Strategy": strategy,
                    **simulation
                })

        if split == split_ratios[0]:
            first_split_data = (
                test.copy().reset_index(drop=True),
                naive_predictions.copy(),
                holt_predictions.copy(),
                server_capacity,
                initial_servers
            )

    forecast_df = pd.DataFrame(forecast_results)
    scaling_df = pd.DataFrame(scaling_results)
    repeated_forecast_df = pd.DataFrame(repeated_forecast_results)
    repeated_scaling_df = pd.DataFrame(repeated_scaling_results)

    forecast_df.to_csv(RESULTS_DIR / "forecast_metrics_by_split.csv", index=False)
    scaling_df.to_csv(RESULTS_DIR / "autoscaling_summary.csv", index=False)
    repeated_forecast_df.to_csv(
        RESULTS_DIR / "repeated_forecast_metrics.csv", index=False
    )
    repeated_scaling_df.to_csv(
        RESULTS_DIR / "repeated_autoscaling_metrics.csv", index=False
    )

    # Mean and standard deviation across the five recorded reruns.
    forecast_summary = repeated_forecast_df.groupby(
        ["Training_Percentage", "Model"]
    ).agg(
        RMSE_Mean=("RMSE", "mean"), RMSE_Std=("RMSE", "std"),
        MAPE_Mean=("MAPE_Percentage", "mean"),
        MAPE_Std=("MAPE_Percentage", "std")
    ).reset_index().fillna(0)

    scaling_summary = repeated_scaling_df.groupby(
        ["Training_Percentage", "Strategy"]
    ).agg(
        SLA_Overload_Mean=("SLA_Overload_Steps", "mean"),
        SLA_Overload_Std=("SLA_Overload_Steps", "std"),
        Wasted_Capacity_Mean=("Wasted_Capacity", "mean"),
        Wasted_Capacity_Std=("Wasted_Capacity", "std"),
        Average_Servers_Mean=("Average_Servers", "mean"),
        Average_Servers_Std=("Average_Servers", "std")
    ).reset_index().fillna(0)

    forecast_summary.to_csv(
        RESULTS_DIR / "repeated_forecast_summary.csv", index=False
    )
    scaling_summary.to_csv(
        RESULTS_DIR / "repeated_autoscaling_summary.csv", index=False
    )

    print(f"Recorded {REPEATED_RUNS} deterministic reruns per training split.")
    print("Note: reruns use identical inputs; they test reproducibility, not statistical independence.")

    return forecast_df, scaling_df, first_split_data


# --------------------------------------------------
# 7. FAILURE INJECTION EXPERIMENT
# --------------------------------------------------

def run_failure_injection(experiment_data):
    if experiment_data is None:
        return

    print("\nRunning failure injection experiments...")
    test, naive, holt, server_capacity, initial_servers = experiment_data
    normal_demand = test.to_numpy(dtype=float)
    predictions = {"Naive": naive, "Holt": holt}
    strategies = [
        "Threshold", "Naive Forecast", "Holt Forecast", "Hybrid Forecast"
    ]

    # Scenario 1: sudden workload spike.
    spike_demand = normal_demand.copy()
    spike_position = len(spike_demand) // 2
    spike_demand[spike_position] *= 2
    if spike_demand[spike_position] == 0:
        spike_demand[spike_position] = server_capacity * 10

    # Scenario 2: malformed observations. These are sanitized at the
    # simulator input boundary; the original workload remains untouched.
    bad_data = normal_demand.copy()
    positions = sorted(set([
        0, len(bad_data) // 2, max(0, len(bad_data) - 1)
    ]))
    bad_values = [np.nan, -1.0, np.inf]
    for position, bad_value in zip(positions, bad_values):
        bad_data[position] = bad_value
    invalid_count = int((~np.isfinite(bad_data) | (bad_data < 0)).sum())
    sanitized_bad_data = np.nan_to_num(
        bad_data, nan=0.0, posinf=0.0, neginf=0.0
    )
    sanitized_bad_data = np.maximum(sanitized_bad_data, 0.0)

    scenarios = [
        ("Normal Workload", normal_demand, 0),
        ("Injected Workload Spike", spike_demand, 0),
        ("Bad Data (Sanitized)", sanitized_bad_data, invalid_count)
    ]

    results = []
    for scenario, demand, invalid_values in scenarios:
        for strategy in strategies:
            result = simulate_autoscaling(
                demand, predictions, strategy, server_capacity, initial_servers
            )
            results.append({
                "Scenario": scenario,
                "Strategy": strategy,
                "Invalid_Values_Injected": invalid_values,
                "Invalid_Values_Sanitized": invalid_values,
                **result
            })

    pd.DataFrame(results).to_csv(
        RESULTS_DIR / "failure_injection_results.csv", index=False
    )
    print("Failure injection experiments completed (spike and malformed-data scenarios).")


# --------------------------------------------------
# 8. GENERATE GRAPHS
# --------------------------------------------------

def generate_graphs(workload, forecast_df, scaling_df):

    print("\nGenerating graphs...")

    # Workload graph
    plt.figure(figsize=(12, 5))

    plt.plot(workload.values)

    plt.title("Google Cluster CPU Workload")
    plt.xlabel("Time Interval (5 minutes)")
    plt.ylabel("Normalized CPU Demand")
    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR / "workload.png"
    )

    plt.close()

    # Forecast comparison graph
    first_split = forecast_df[
        forecast_df["Training_Percentage"] == 70
    ]

    plt.figure(figsize=(8, 5))

    plt.bar(
        first_split["Model"],
        first_split["RMSE"]
    )

    plt.title("Forecast Model RMSE Comparison")
    plt.xlabel("Forecasting Model")
    plt.ylabel("RMSE")
    plt.grid(axis="y")

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR / "forecast_comparison.png"
    )

    plt.close()

    # Autoscaling comparison graph
    first_scaling = scaling_df[
        scaling_df["Training_Percentage"] == 70
    ]

    plt.figure(figsize=(10, 5))

    plt.bar(
        first_scaling["Strategy"],
        first_scaling["Average_Servers"]
    )

    plt.title("Autoscaling Strategy Comparison")
    plt.xlabel("Autoscaling Strategy")
    plt.ylabel("Average Number of Servers")
    plt.xticks(rotation=20)

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR / "autoscaling_comparison.png"
    )

    plt.close()

    print("Graphs saved successfully.")


# --------------------------------------------------
# 9. MAIN FUNCTION
# --------------------------------------------------

def main():

    print("=" * 55)
    print(" WORKLOAD FORECASTING FOR AUTOSCALING")
    print("=" * 55)

    download_dataset()

    workload = load_workload()

    forecast_df, scaling_df, experiment_data = (
        run_experiments(workload)
    )

    run_failure_injection(experiment_data)

    generate_graphs(
        workload,
        forecast_df,
        scaling_df
    )

    print("\nFORECASTING RESULTS")
    print(forecast_df.to_string(index=False))

    print("\nAUTOSCALING RESULTS")
    print(scaling_df.to_string(index=False))

    print("\nAll experiments completed successfully!")

    print("Check the results folder for CSV files and graphs.")


if __name__ == "__main__":
    main()
