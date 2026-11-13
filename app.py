import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ------------------------------------------------
# PROJECT PATHS AND PAGE CONFIGURATION
# ------------------------------------------------

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

st.set_page_config(
    page_title="Workload Autoscaling Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Workload Forecasting for Autoscaling")
st.caption(
    "Analysis of workload prediction, resource allocation, "
    "and failure-handling behaviour"
)

# ------------------------------------------------
# CHECK AND LOAD RESULT FILES
# ------------------------------------------------

base_required_files = [
    "workload_data.csv",
    "failure_injection_results.csv"
]

missing_files = [
    file for file in base_required_files
    if not (RESULTS / file).exists()
]

if missing_files:
    st.error(
        "Some required result files are missing. "
        "Run `python src/pipeline.py` first."
    )
    st.write("Missing files:", missing_files)
    st.stop()

workload = pd.read_csv(RESULTS / "workload_data.csv")
failure = pd.read_csv(RESULTS / "failure_injection_results.csv")

# Prefer repeated-run summary files. Fall back to the original
# result files if the repeated-run summaries are not available.
repeated_forecast_path = RESULTS / "repeated_forecast_summary.csv"
repeated_autoscaling_path = RESULTS / "repeated_autoscaling_summary.csv"

if repeated_forecast_path.exists():
    forecast = pd.read_csv(repeated_forecast_path)
    forecast_mode = "repeated"
elif (RESULTS / "forecast_metrics_by_split.csv").exists():
    forecast = pd.read_csv(RESULTS / "forecast_metrics_by_split.csv")
    forecast_mode = "single"
else:
    st.error("Forecast results not found. Run `python src/pipeline.py` first.")
    st.stop()

if repeated_autoscaling_path.exists():
    autoscaling = pd.read_csv(repeated_autoscaling_path)
    autoscaling_mode = "repeated"
elif (RESULTS / "autoscaling_summary.csv").exists():
    autoscaling = pd.read_csv(RESULTS / "autoscaling_summary.csv")
    autoscaling_mode = "single"
else:
    st.error("Autoscaling results not found. Run `python src/pipeline.py` first.")
    st.stop()

# ------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------

def format_number(value, digits=2):
    """Format a numeric value safely for display."""
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "N/A"


def make_bar_chart(data, x_column, y_column, title, y_label,
                   x_rotation=0):
    """Create and display a simple bar chart."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(data[x_column].astype(str), data[y_column])
    ax.set_title(title)
    ax.set_ylabel(y_label)
    ax.tick_params(axis="x", rotation=x_rotation)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ------------------------------------------------
# SIDEBAR NAVIGATION
# ------------------------------------------------

st.sidebar.title("Dashboard Navigation")

section = st.sidebar.radio(
    "Select Section",
    [
        "Overview",
        "Workload Analysis",
        "Forecasting Results",
        "Autoscaling Comparison",
        "Failure Injection"
    ]
)

# ------------------------------------------------
# OVERVIEW
# ------------------------------------------------

if section == "Overview":

    st.header("Project Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Workload Intervals", len(workload))
    col2.metric("Forecasting Models", forecast["Model"].nunique())
    col3.metric("Autoscaling Strategies", autoscaling["Strategy"].nunique())

    st.subheader("Project Objectives")

    st.markdown("""
    - Analyze historical computing workload.
    - Forecast future CPU demand using Naive and Holt models.
    - Compare threshold-based and forecast-based autoscaling.
    - Measure forecasting error using RMSE and MAPE.
    - Evaluate SLA overload steps and wasted capacity.
    - Test the system with a sudden workload spike and invalid data.
    """)

    st.info(
        "This project uses a local simulator. "
        "It does not create or manage actual cloud servers."
    )

    st.subheader("System Architecture")

    st.markdown("""
    **Public Workload Trace → Data Processing → Forecasting Models
    → Autoscaling Simulator → Performance Metrics → Dashboard**
    """)

    st.subheader("Experiment Information")

    if forecast_mode == "repeated" and autoscaling_mode == "repeated":
        st.success(
            "Repeated-run summary files are being used. "
            "The current five reruns use identical inputs, so they check "
            "reproducibility rather than independent trial variation."
        )
    else:
        st.warning(
            "The dashboard is displaying the original experiment results. "
            "Run the updated pipeline to generate repeated-run summaries."
        )

    st.write(
        f"Forecast result mode: **{forecast_mode.title()}**  \n"
        f"Autoscaling result mode: **{autoscaling_mode.title()}**"
    )

# ------------------------------------------------
# WORKLOAD ANALYSIS
# ------------------------------------------------

elif section == "Workload Analysis":

    st.header("Historical Workload Analysis")
    st.write("CPU demand aggregated into five-minute intervals.")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(workload["cpu_demand"], linewidth=1.5)
    ax.set_title("CPU Workload Over Time")
    ax.set_xlabel("Time Interval")
    ax.set_ylabel("Normalized CPU Demand")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Workload Statistics")
    st.dataframe(
        workload["cpu_demand"].describe().to_frame(),
        use_container_width=True
    )

# ------------------------------------------------
# FORECASTING RESULTS
# ------------------------------------------------

elif section == "Forecasting Results":

    st.header("Forecasting Model Evaluation")

    selected_split = st.selectbox(
        "Select Training Data Percentage",
        sorted(forecast["Training_Percentage"].unique())
    )

    filtered = forecast[
        forecast["Training_Percentage"] == selected_split
    ].copy()

    st.subheader("Forecasting Metrics")

    if forecast_mode == "repeated":
        display_columns = [
            "Model", "RMSE_Mean", "RMSE_Std",
            "MAPE_Mean", "MAPE_Std"
        ]
        st.dataframe(
            filtered[display_columns],
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Mean and standard deviation are calculated across five "
            "deterministic reruns. A standard deviation of zero reflects "
            "identical rerun inputs, not independent experiments."
        )

        rmse_column = "RMSE_Mean"
        mape_column = "MAPE_Mean"
    else:
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )
        rmse_column = "RMSE"
        mape_column = "MAPE_Percentage"

    col1, col2 = st.columns(2)

    with col1:
        make_bar_chart(
            filtered,
            "Model",
            rmse_column,
            "RMSE Comparison",
            "RMSE"
        )

    with col2:
        make_bar_chart(
            filtered,
            "Model",
            mape_column,
            "MAPE Comparison",
            "MAPE (%)"
        )

    st.caption(
        "Lower RMSE and MAPE values indicate more accurate forecasts. "
        "MAPE may exclude intervals where actual demand is zero."
    )

# ------------------------------------------------
# AUTOSCALING COMPARISON
# ------------------------------------------------

elif section == "Autoscaling Comparison":

    st.header("Autoscaling Strategy Comparison")

    selected_split = st.selectbox(
        "Select Training Data Percentage",
        sorted(autoscaling["Training_Percentage"].unique())
    )

    filtered = autoscaling[
        autoscaling["Training_Percentage"] == selected_split
    ].copy()

    st.subheader("Simulation Results")

    if autoscaling_mode == "repeated":
        display_columns = [
            "Strategy",
            "SLA_Overload_Mean",
            "SLA_Overload_Std",
            "Wasted_Capacity_Mean",
            "Wasted_Capacity_Std",
            "Average_Servers_Mean",
            "Average_Servers_Std"
        ]
        st.dataframe(
            filtered[display_columns],
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "The standard deviations are zero because the five reruns "
            "currently use identical inputs."
        )

        overload_column = "SLA_Overload_Mean"
        wasted_column = "Wasted_Capacity_Mean"
        servers_column = "Average_Servers_Mean"
    else:
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )
        overload_column = "SLA_Overload_Steps"
        wasted_column = "Wasted_Capacity"
        servers_column = "Average_Servers"

    col1, col2 = st.columns(2)

    with col1:
        make_bar_chart(
            filtered,
            "Strategy",
            overload_column,
            "SLA Overload Steps",
            "Overload Steps",
            x_rotation=25
        )

    with col2:
        make_bar_chart(
            filtered,
            "Strategy",
            servers_column,
            "Average Servers Required",
            "Average Servers",
            x_rotation=25
        )

    make_bar_chart(
        filtered,
        "Strategy",
        wasted_column,
        "Wasted Capacity Comparison",
        "Unused Capacity",
        x_rotation=25
    )

    st.caption(
        "Compare all three measures together: fewer overload steps, "
        "lower wasted capacity, and fewer average servers."
    )

# ------------------------------------------------
# FAILURE INJECTION
# ------------------------------------------------

elif section == "Failure Injection":

    st.header("Failure Injection Experiments")

    st.markdown("""
    This section evaluates the autoscaling strategies under:
    - **Normal Workload:** original workload without injected faults.
    - **Injected Workload Spike:** a sudden increase in workload.
    - **Bad Data (Sanitized):** invalid values are introduced and then
      handled by the pipeline's data-sanitization logic.
    """)

    st.subheader("Failure Injection Results")
    st.dataframe(
        failure,
        use_container_width=True,
        hide_index=True
    )

    scenarios = failure["Scenario"].unique()

    selected_scenario = st.selectbox(
        "Select Experiment Scenario",
        scenarios
    )

    filtered = failure[
        failure["Scenario"] == selected_scenario
    ].copy()

    st.subheader(selected_scenario)

    col1, col2 = st.columns(2)

    with col1:
        make_bar_chart(
            filtered,
            "Strategy",
            "SLA_Overload_Steps",
            "SLA Overload Steps",
            "Overload Steps",
            x_rotation=25
        )

    with col2:
        make_bar_chart(
            filtered,
            "Strategy",
            "Wasted_Capacity",
            "Wasted Capacity",
            "Unused Capacity",
            x_rotation=25
        )

    if {
        "Invalid_Values_Injected",
        "Invalid_Values_Sanitized"
    }.issubset(failure.columns):
        st.subheader("Data Sanitization Check")

        bad_data = failure[
            failure["Scenario"] == "Bad Data (Sanitized)"
        ]

        if not bad_data.empty:
            injected = int(bad_data["Invalid_Values_Injected"].max())
            sanitized = int(bad_data["Invalid_Values_Sanitized"].max())

            col1, col2 = st.columns(2)
            col1.metric("Invalid Values Injected", injected)
            col2.metric("Invalid Values Sanitized", sanitized)

            if injected == sanitized:
                st.success(
                    "All injected invalid values were handled "
                    "by the data-sanitization step."
                )
            else:
                st.warning(
                    "The number of sanitized values does not match "
                    "the number of injected values."
                )

st.divider()

st.caption(
    "Workload Forecasting for Autoscaling | Academic Project"
)
