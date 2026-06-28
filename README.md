# Efficiency Analysis - CallMeMaybe

Operator efficiency analysis for **CallMeMaybe**, a virtual telephony service. The project identifies inefficient operators based on missed call rates, waiting times, and outgoing call volume, using exploratory data analysis, composite scoring, and statistical hypothesis testing.

## Project Structure

```
├── Telecom Project.ipynb                  # Main analysis notebook (English)
├── Proyecto de Telecomunicaciones.ipynb   # Main analysis notebook (Spanish)
├── Dashboards.py                          # Interactive Dash dashboard
├── telecom_dataset_new.csv                # Call records dataset
├── telecom_clients.csv                    # Client/tariff plan dataset
├── Efficiency Analysis.pdf                # Analysis report (English)
├── Análisis de Eficiencia CallMeMaybe.pdf # Analysis report (Spanish)
└── requirements.txt                       # Python dependencies
```

## Datasets

| File | Rows | Description |
|------|------|-------------|
| `telecom_dataset_new.csv` | 53,902 | Call records with direction, duration, operator, missed status, and wait times |
| `telecom_clients.csv` | 732 | Client information with user ID, tariff plan, and registration date |

### Key Columns (`telecom_dataset_new.csv`)

| Column | Description |
|--------|-------------|
| `user_id` | Client identifier |
| `date` | Call date (UTC+3) |
| `direction` | `in` (incoming) / `out` (outgoing) |
| `internal` | Whether the call was between staff |
| `operator_id` | Operator handling the call |
| `is_missed_call` | Whether the call was missed |
| `calls_count` | Number of calls in the record |
| `call_duration` | Active call duration (seconds) |
| `total_call_duration` | Total duration including wait (seconds) |

## Analysis Overview

### 1. Data Exploration & Cleaning
- Converted date columns to datetime
- Removed 4,900 duplicate records that were inflating operator metrics
- Removed records with missing `operator_id` or `internal` values
- Fixed `internal` column type from string to boolean (`.astype(bool)` on `"False"` incorrectly returns `True`)

### 2. Operator Metrics
For each operator, the following metrics were computed:
- **Missed call rate** (`missed_rate`): proportion of missed incoming calls
- **Average wait time** (`wait_time`): `total_call_duration - call_duration`
- **Total calls** (`calls_count`): total call volume handled
- **Outgoing calls** (`outgoing_calls`): number of outgoing calls made

### 3. Inefficiency Score
A composite score was built using Min-Max normalization and weighted aggregation:

| Metric | Weight | Direction |
|--------|--------|-----------|
| Missed call rate | 50% | Higher = worse |
| Wait time | 40% | Higher = worse |
| Call volume | 5% | Lower = worse |
| Outgoing calls | 5% | Lower = worse (inbound-only operators are not penalized) |

Operators in the **95th percentile** of this score are flagged as inefficient. Inbound-only operators are excluded from the outgoing calls penalty to avoid false positives.

### 4. Statistical Hypothesis Testing

| Hypothesis | Test | p-value | Result |
|------------|------|---------|--------|
| Inefficient operators have higher wait times | Welch's t-test (one-tailed) | < 0.05 | Significant |
| Missed rate correlates with wait time | Pearson correlation (r=0.237) | 2.09e-15 | Significant |
| Inefficient operators make fewer calls | Welch's t-test (two-tailed) | 0.035 | Significant (opposite direction) |

**Key counter-intuitive finding:** Inefficient operators handle *more* calls, not fewer. Inefficiency is driven by poorly managed overload, not inactivity.

### 5. Cross-Analysis by Tariff Plan
The clients dataset is merged with call data to analyze whether operator behavior varies by customer tariff plan, revealing patterns that could inform resource allocation.

## Interactive Dashboard

The Dash dashboard (`Dashboards.py`) provides:
- **Call type filter**: all, incoming, or outgoing
- **Date range picker**
- **Duration histogram**: average call duration by range, split by direction
- **Pie chart**: internal vs. external call proportion
- **Daily call volume**: bar chart of calls per day
- **Operator efficiency chart**: top 20 operators by missed call rate, colored by average wait time

### Running the Dashboard

```bash
pip install -r requirements.txt
python Dashboards.py
```

Then open http://localhost:8051 in your browser.

## Setup

```bash
# Clone the repository
git clone https://github.com/DevLearnsAI/Efficency-Analysis---CallMe-Maybe.git
cd Efficency-Analysis---CallMe-Maybe

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Key Findings

- Most calls are **external** (87%) and **outgoing** (69%), indicating operators actively contact customers.
- A small group of operators (top 5%) shows significantly higher wait times and missed call rates.
- **Wait time and missed calls are positively correlated** (r=0.237, p<0.001), validating the inefficiency model.
- **Inefficiency is driven by overload, not inactivity** — operators flagged as inefficient handle more calls on average, but manage them poorly.
- The inefficiency score effectively separates low-performing operators, providing an actionable metric for management decisions.

## Tech Stack

- **Python 3.8+**
- **pandas** / **NumPy** - data manipulation
- **Matplotlib** / **Seaborn** - static visualizations
- **Plotly** - interactive charts
- **SciPy** - statistical testing
- **Dash** - interactive web dashboard
