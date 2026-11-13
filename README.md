
# Workload Forecasting for Autoscaling

## 1. Introduction

Workload Forecasting for Autoscaling is a Python-based project
that predicts future computing workload and simulates automatic
resource allocation.

The project compares traditional threshold-based autoscaling
with forecasting-based autoscaling techniques.

## 2. Objectives

- Analyze historical computing workload.
- Forecast future CPU demand.
- Compare Naive and Holt forecasting models.
- Implement threshold-based autoscaling.
- Implement forecast-based autoscaling.
- Evaluate SLA overload and wasted capacity.
- Test system behaviour under sudden workload spikes.
- Evaluate forecasting performance using multiple training splits.
- Perform repeated reproducibility checks.
- Test system behaviour under invalid and missing workload data.

## 3. Technologies Used

- Python
- NumPy
- Pandas
- Matplotlib
- Statsmodels
- Streamlit
- Certifi

## 4. Dataset

Google Cluster Data is used as the workload source.

The project processes CPU usage records and aggregates them
into five-minute workload intervals.

Dataset source:
https://github.com/google/cluster-data

## 5. Forecasting Models

1. Naive Forecasting
2. Holt Exponential Smoothing

## 6. Autoscaling Strategies

1. Threshold-Based Autoscaling
2. Naive Forecast-Based Autoscaling
3. Holt Forecast-Based Autoscaling
4. Hybrid Forecast-Based Autoscaling

## 7. Failure Injection

The project evaluates autoscaling strategies under different scenarios:

1. Normal Workload
2. Injected Workload Spike
3. Bad Data (Sanitized)

Invalid workload values are handled through data sanitization
before the simulation is performed.

## 7. Project Structure

Workload-Autoscaling/
|
|-- data/
|
|-- results/
|   |-- workload_data.csv
|   |-- forecast_metrics_by_split.csv
|   |-- autoscaling_summary.csv
|   |-- failure_injection_results.csv
|   |-- repeated_forecast_summary.csv
|   |-- repeated_autoscaling_summary.csv
|
|-- src/
|   |-- pipeline.py
|
|-- app.py
|-- run.py
|-- requirements.txt
|-- README.md
|-- ARCHITECTURE.md

## 8. Installation

Clone the repository:

git clone YOUR_REPOSITORY_URL

Move into the project folder:

cd Workload-Autoscaling

Create virtual environment:

python3 -m venv .venv

Activate environment:

source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

## 9. Execution

Run the complete project using:

python run.py

This command automatically:
- Processes the workload dataset.
- Executes forecasting experiments.
- Simulates autoscaling strategies.
- Performs failure injection experiments.
- Generates result files and graphs.
- Launches the Streamlit dashboard.

Alternatively, run individual components:

python src/pipeline.py

streamlit run app.py

## 10. Output

The project generates:

- Historical workload analysis graph
- Forecasting comparison graphs
- Autoscaling comparison graphs
- RMSE and MAPE evaluation metrics
- Repeated experiment summary files
- SLA overload measurements
- Wasted capacity measurements
- Failure injection results
- Interactive Streamlit dashboard

## 11. Limitations

- The project uses a simulated autoscaling environment.
- It does not provision real cloud infrastructure.
- The selected historical trace is a short dataset.
- Results depend on the selected workload and simulation assumptions.
- Repeated runs currently use identical inputs and verify reproducibility rather than independent statistical variation.
- The workload dataset contains only 76 aggregated intervals.
- The workload trace is historical and may not represent modern cloud workloads.
- MAPE evaluation excludes zero-demand intervals.
- The simulator does not account for real cloud provisioning delays.

## 12. Future Scope

- Use larger workload datasets.
- Implement ARIMA and machine learning models.
- Add real-time workload monitoring.
- Integrate with cloud-based infrastructure.
- Improve scaling decisions using adaptive policies.
