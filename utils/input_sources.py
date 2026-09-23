from pathlib import Path

import pandas as pd


DAY_AHEAD_SAMPLE_RELATIVE_PATH = (
    Path("data") / "synthetic_day_ahead_price_forecast.csv"
)


def load_day_ahead_frame(source, uploaded_file=None, project_root=None):
    """Load the selected day-ahead input without changing its validation."""
    if source == "bundled":
        root = (
            Path(project_root)
            if project_root is not None
            else Path(__file__).resolve().parents[1]
        )
        return pd.read_csv(root / DAY_AHEAD_SAMPLE_RELATIVE_PATH)

    if source == "upload":
        if uploaded_file is None:
            return None
        return pd.read_csv(uploaded_file)

    raise ValueError(f"Unsupported day-ahead data source: {source}")
