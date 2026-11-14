# Workload Forecasting for Autoscaling (Project-14) 


## Project Overview

Workload Forecasting for Autoscaling is a Python-based project that analyzes historical CPU workload data, predicts future workload demand, and compares different autoscaling strategies.

The project uses Google Cluster Data to study CPU utilization over time. It applies forecasting techniques to estimate upcoming workload and simulates how different autoscaling strategies allocate servers according to predicted or observed demand.

A Streamlit dashboard is provided to visualize workload patterns, forecasting performance, autoscaling results, and failure injection experiments.

## Objectives

- Analyze historical CPU workload data.
- Forecast future CPU demand using Naive and Holt forecasting methods.
- Compare different autoscaling strategies.
- Evaluate forecasting accuracy using RMSE and MAPE.
- Analyze SLA overload and wasted server capacity.
- Test system behavior under workload spikes and invalid data.
- Present results through an interactive dashboard.

## Features

- CPU workload preprocessing and aggregation into 5-minute intervals.
- Rolling one-step-ahead workload forecasting.
- Comparison of Naive and Holt forecasting models.
- Four autoscaling strategies:
  - Threshold-based autoscaling
  - Naive Forecast autoscaling
  - Holt Forecast autoscaling
  - Hybrid Forecast autoscaling
- Performance evaluation using RMSE and MAPE.
- Autoscaling evaluation using SLA overload steps, wasted capacity, and average servers.
- Failure injection experiments for workload spikes and malformed data.
- Graph generation using Matplotlib.
- Interactive Streamlit dashboard.

## Technologies Used

- Python
- Pandas
- NumPy
- Matplotlib
- Statsmodels
- Streamlit

## Dataset

The project uses Google Cluster Data v1 to analyze CPU workload.

The workload is cleaned and aggregated into 5-minute intervals before being used for forecasting and autoscaling experiments.

## Project Structure

```text
Workload-Autoscaling/
│
├── data/
│   └── google_trace.csv.gz
│
├── results/
│   ├── CSV result files
│   └── Generated graphs
│
├── src/
│   └── pipeline.py
│
├── app.py
├── run.py
├── requirements.txt
├── README.md
├── ARCHITECTURE.md
└── .gitignore
```

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/shambhavi-chandrawat/Workload-Forecasting-for-Autoscaling.git
```

2. Navigate to the project directory:

```bash
cd Workload-Forecasting-for-Autoscaling
```

3. Create a virtual environment:

```bash
python -m venv .venv
```

4. Activate the virtual environment.

For macOS/Linux:

```bash
source .venv/bin/activate
```

For Windows:

```bash
.venv\Scripts\activate
```

5. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Project

Run the workload forecasting and autoscaling pipeline:

```bash
python src/pipeline.py
```

After the pipeline completes, generated CSV files and graphs will be available in the `results/` directory.

Launch the Streamlit dashboard:

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal to access the dashboard.

Alternatively, use the main runner if configured:

```bash
python run.py
```

## Evaluation Metrics

| Metric | Description |
|---|---|
| RMSE | Measures forecasting error |
| MAPE | Measures average percentage forecasting error |
| SLA Overload Steps | Counts intervals where workload exceeds available capacity |
| Wasted Capacity | Measures unused allocated server capacity |
| Average Servers | Measures average number of allocated servers |

## Experimental Analysis

The project evaluates forecasting models using 70%, 75%, and 80% training splits.

It also compares four autoscaling strategies under normal workload, injected workload spikes, and malformed-data scenarios.

The actual experimental results are stored in the generated CSV files inside the `results/` directory.

## Limitations

- The project uses historical workload data rather than live cloud infrastructure.
- Autoscaling is simulated and does not provision actual cloud servers.
- Forecasting performance depends on the available dataset and workload patterns.
- Experimental results represent the tested workload and configurations.

## Future Scope

- Integrate real-time workload monitoring.
- Explore advanced forecasting models.
- Extend the simulation to larger datasets.
- Implement autoscaling on cloud platforms.
- Improve workload spike detection and resource allocation.

## Author
### Group: O_P2

**Shambhavi Chandrawat(1000025732)**
**Shorya Rajput(1000024565)**
**Kasish Singh(1000026074)**
**Vivek Kumar Gupta(1000025291)**

B.Tech Computer Science and Engineering
DIT University
