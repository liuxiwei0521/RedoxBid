# RedoxBid

## 👉 Online Demo [Click here to launch the app](https://redoxbid-energy-storage.streamlit.app)

**Multi-Market Optimization for Redox Flow Battery Storage**

RedoxBid is a research-oriented decision-support prototype for exploring how a
vanadium redox flow battery can participate in day-ahead energy and frequency
regulation markets. It converts forecast data and configurable battery and
market parameters into dispatch schedules, bidding recommendations, and
scenario-level performance comparisons.

RedoxBid does **not** connect to an exchange, submit orders, or execute
real-world transactions.

## What the project demonstrates

- A 24-hour, 96-interval day-ahead battery scheduling model.
- Charge, discharge, state-of-charge, ramping, efficiency, and terminal-energy
  constraints formulated with Pyomo.
- A baseline day-ahead optimization workflow using CBC.
- Hourly regulation-demand profile estimation and mileage-price forecasting.
- Sequential regulation optimization after fixing the day-ahead schedule.
- Joint day-ahead and regulation co-optimization with shared power-capacity and
  SOC-headroom constraints.
- Profit and capacity-allocation comparisons across three strategies.
- Bilingual English/Chinese presentation, station-profile management, local
  decision history, charts, tables, and downloadable CSV results.

## Decision workflow

The application presents six conceptual stages:

1. Validate input data.
2. Solve the day-ahead baseline with the selected solver.
3. Evaluate the RARR operating-mode decision.
4. Estimate the next-day regulation-demand profile and forecast mileage prices.
5. Compare sequential and joint multi-market optimization.
6. Produce schedules, KPIs, and bidding recommendations.

The current RARR module is a simplified scenario-analysis component. It
evaluates a fixed day-ahead schedule over 1,000 Monte Carlo price scenarios,
using 15% relative price noise and a 70%–95% clearing-rate range for
quantity-and-price bids. It does not re-optimize the dispatch within each
scenario and should not be interpreted as a complete stochastic-programming
or market-risk model.

The current implementation connects CBC to the optimization backend. The
solver registry can be extended later, but HiGHS, GLPK, and Gurobi are not
currently wired or verified.

## Project structure

```text
RedoxBid/
├── app/                  Streamlit entry point and station-profile page
├── data/                 Bundled synthetic demonstration datasets
├── models/               Day-ahead, sequential, and joint models
├── tests/                Automated tests
├── ui/                   Theme, components, and bilingual text
├── utils/                Database, data, and visualization helpers
├── .streamlit/           Native Streamlit theme configuration
├── requirements.txt      Python dependencies
├── LICENSE               MIT License
├── README.md             Project documentation
└── 启动决策系统.bat       Optional Windows launcher
```

`station_archive.db` is created locally when the application first runs. It is
excluded from version control because it can contain local profile edits and
decision history.

## Installation

Python 3.9 or later is recommended.

### Virtual environment

```powershell
cd RedoxBid
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

### Conda

```powershell
conda create -n redoxbid python=3.9 -y
conda activate redoxbid
python -m pip install -r requirements.txt
```

## CBC solver

Pyomo provides the modeling layer but does not bundle an optimization solver.
CBC must be installed separately and its executable must be available on
`PATH`.

```powershell
conda install -c conda-forge coin-or-cbc
cbc -stop
```

If `cbc -stop` is not recognized, restart the terminal and confirm that the
environment containing CBC is active. Refer to the
[Pyomo documentation](https://pyomo.readthedocs.io/en/stable/) and the
[conda-forge CBC package](https://anaconda.org/conda-forge/coin-or-cbc) for
platform-specific details.

## Running the application

From the project root:

```powershell
python -m streamlit run "app\决策主页面.py"
```

Windows users may also double-click `启动决策系统.bat`. The launcher first uses
a project-local `.venv`, then searches installed Conda environments for a
compatible dependency set and CBC executable, and finally tries an available
`python` or `py` interpreter with Streamlit. It does not depend on a hard-coded
Conda environment name.

## Input data

### Day-ahead price forecast

Upload a CSV containing a numeric `price` column with exactly 96 finite values,
one for each 15-minute interval in the 24-hour horizon.

A ready-to-use synthetic example is provided at
`data/synthetic_day_ahead_price_forecast.csv`.

```csv
timestamp,price
2025-01-01 00:00:00,158.80
2025-01-01 00:15:00,180.19
```

### Regulation-market history

The comparison workflow accepts a continuous hourly CSV with these canonical
fields:

- `timestamp`
- `regulation_demand_mw`
- `mileage_price_cny_per_mw`

The loader also accepts aliases used by the bundled sample, including
`datetime`, `frequency_demand`, and `frequency_price`. Timestamps must be
unique and continuous; demand and price values must be finite and
non-negative. If no regulation file is uploaded, the application uses the
bundled seven-day synthetic sample at
`data/synthetic_regulation_history.csv`.

## Outputs

Depending on the selected workflow, RedoxBid provides:

- charge, discharge, net-power, and energy-state schedules;
- state-of-charge and power-allocation visualizations;
- day-ahead bid recommendations;
- regulation reserve and multi-market schedules;
- net-profit, throughput, equivalent-cycle, and reserve KPIs;
- comparisons of day-ahead-only, sequential, and joint strategies;
- downloadable CSV schedules, bids, and comparison results.

## Tests

Run the complete test suite from the project root:

```powershell
python -m pytest -q
```

The optimization tests require a working CBC executable. If CBC is missing,
CBC-dependent tests return `solver_error`; that environment must not be
reported as a fully validated optimization run. Data-contract, UI, database,
forecasting, and non-solver tests can still be run independently.

## Data and modeling disclaimer

- Both CSV files in `data/` are artificially generated demonstration data.
  They are not measured records from a real power station or electricity
  market.
- The Jimusaer station identity and capacity shown by default are case-study
  parameters. They do not represent verified real-time operating data,
  dispatch instructions, market bids, or official project performance.
- Revenue, cost, degradation, regulation, and operating constraints are
  simplified research assumptions and omit many production-market and
  grid-security requirements.
- Results are intended for education, research, and method demonstration only.
  They are not operational, investment, or trading advice.

## License

The original code in this repository is released under the [MIT License](LICENSE).
Third-party libraries, datasets, and separately attributed material remain
subject to their respective licenses and terms.
