# System Architecture

## 1. Overview

The Workload Forecasting for Autoscaling project follows a modular architecture in which historical workload data is processed, forecasted, evaluated, and used to simulate different autoscaling strategies.

The system consists of five major stages:

1. Data Loading and Preprocessing
2. Workload Forecasting
3. Autoscaling Simulation
4. Performance Evaluation and Failure Injection
5. Visualization and Dashboard

## 2. System Workflow

```text
       Google Cluster Dataset
                 |
                 v
       Data Loading and Cleaning
                 |
                 v
       CPU Workload Aggregation
          (5-minute intervals)
                 |
                 v
        Train-Test Data Splitting
          (70%, 75%, 80%)
                 |
                 v
        Workload Forecasting
          /             \
         v               v
      Naive            Holt
      Model            Model
          \             /
           \           /
                 |
                 v
        Autoscaling Simulation
                 |
     +-----------+-----------+
     |           |           |
     v           v           v
 Threshold     Forecast    Hybrid
 Strategy      Strategies  Strategy
                 |
                 v
        Performance Evaluation
                 |
       +---------+----------+
       |         |          |
       v         v          v
      RMSE      MAPE    SLA Overload
                         and Capacity
                 |
                 v
         Failure Injection
                 |
                 v
          Result Generation
                 |
          +------+------+
          |             |
          v             v
       CSV Files      Graphs
          |             |
          +------+------+
                 |
                 v
         Streamlit Dashboard
```

## 3. Main Components

### 3.1 Data Loading and Preprocessing

The system loads historical CPU workload data from Google Cluster Data v1.

The preprocessing stage:
- Reads the workload dataset.
- Handles missing and invalid values.
- Cleans CPU utilization data.
- Aggregates workload into 5-minute intervals.
- Produces a time-series workload for further analysis.

### 3.2 Workload Forecasting

The forecasting module predicts future CPU demand using two methods.

**Naive Forecasting**

Uses the most recently observed workload value as the prediction for the next interval.

**Holt Forecasting**

Uses exponential smoothing with trend estimation to predict future workload.

The project uses rolling one-step-ahead forecasting, where actual observations become available after each prediction.

The dataset is divided into 70%, 75%, and 80% training splits for experimentation.

### 3.3 Autoscaling Simulation

The autoscaling module simulates server allocation based on workload demand.

It compares four strategies:

**Threshold-Based Autoscaling**

Allocates servers according to observed workload and predefined capacity thresholds.

**Naive Forecast Autoscaling**

Uses Naive forecasting predictions to estimate the required server capacity.

**Holt Forecast Autoscaling**

Uses Holt forecasting predictions for resource allocation.

**Hybrid Forecast Autoscaling**

Combines forecasting approaches to determine server allocation.

The simulation evaluates how effectively each strategy balances resource availability and utilization.

### 3.4 Performance Evaluation

The system evaluates forecasting and autoscaling performance using the following metrics:

- **RMSE:** Measures the difference between actual and predicted workload.
- **MAPE:** Measures forecasting error as a percentage.
- **SLA Overload Steps:** Counts intervals in which available capacity is insufficient for workload demand.
- **Wasted Capacity:** Measures unused allocated capacity.
- **Average Servers:** Represents the average number of servers allocated during the simulation.

### 3.5 Failure Injection

Failure injection experiments evaluate the system under different conditions.

The tested scenarios include:

- Normal Workload: Uses the original workload.
- Injected Workload Spike: Introduces an artificial increase in workload.
- Bad Data: Introduces invalid values such as NaN, negative values, and infinity to test data sanitization.

The results help analyze the behavior of autoscaling strategies under abnormal conditions.

### 3.6 Result Generation

The pipeline stores experimental results in CSV files and generates graphs using Matplotlib.

These outputs include:
- Forecasting performance comparisons.
- Autoscaling strategy comparisons.
- Workload visualization.
- Failure injection results.

### 3.7 Streamlit Dashboard

The Streamlit dashboard presents the generated results through different sections:

- Overview
- Workload Analysis
- Forecasting Results
- Autoscaling Comparison
- Failure Injection

It allows users to understand workload patterns and compare forecasting and autoscaling performance.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Data Processing | Pandas, NumPy |
| Forecasting | Statsmodels |
| Visualization | Matplotlib |
| Dashboard | Streamlit |
| Dataset | Google Cluster Data v1 |
| Output Storage | CSV files |

## 5. Execution Flow

The complete execution process is:

1. Load and preprocess the workload dataset.
2. Divide the workload into training and testing sets.
3. Generate rolling forecasts using Naive and Holt methods.
4. Simulate the four autoscaling strategies.
5. Calculate forecasting and resource utilization metrics.
6. Perform failure injection experiments.
7. Save experimental results as CSV files.
8. Generate visualization graphs.
9. Display the results through the Streamlit dashboard.

## 6. Architecture Summary

The architecture separates workload preprocessing, forecasting, autoscaling, evaluation, and visualization into distinct stages.

This modular approach makes the project easier to understand, test, maintain, and extend with additional forecasting models or autoscaling strategies.
