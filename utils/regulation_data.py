"""Regulation-market data normalization and time-resolution helpers."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


_COLUMN_ALIASES = {
    "timestamp": ("timestamp", "datetime", "time", "date_time"),
    "regulation_demand_mw": (
        "regulation_demand_mw",
        "frequency_demand",
        "regulation_demand",
        "demand_mw",
    ),
    "mileage_price_cny_per_mw": (
        "mileage_price_cny_per_mw",
        "frequency_price",
        "regulation_price",
        "mileage_price",
    ),
}


def _resolve_columns(frame: pd.DataFrame) -> dict[str, str]:
    lookup = {str(column).strip().lower(): column for column in frame.columns}
    resolved: dict[str, str] = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lookup:
                resolved[lookup[alias]] = canonical
                break
        else:
            raise ValueError(
                f"missing required column '{canonical}'; accepted aliases: {aliases}"
            )
    return resolved


def normalize_regulation_history(frame: pd.DataFrame) -> pd.DataFrame:
    """Return validated hourly history with stable, unit-bearing column names."""
    if frame is None or frame.empty:
        raise ValueError("regulation history must not be empty")

    normalized = frame.rename(columns=_resolve_columns(frame)).copy()
    preferred = list(_COLUMN_ALIASES)
    remaining = [column for column in normalized.columns if column not in preferred]
    normalized = normalized[preferred + remaining]

    normalized["timestamp"] = pd.to_datetime(
        normalized["timestamp"], errors="coerce"
    )
    if normalized["timestamp"].isna().any():
        raise ValueError("timestamp contains invalid values")
    if normalized["timestamp"].duplicated().any():
        raise ValueError("duplicate timestamp values are not allowed")

    for column in ("regulation_demand_mw", "mileage_price_cny_per_mw"):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        if normalized[column].isna().any():
            raise ValueError(f"{column} must contain numeric values")
        if (normalized[column] < 0).any():
            raise ValueError(f"{column} must be non-negative")

    normalized = normalized.sort_values("timestamp").reset_index(drop=True)
    if len(normalized) > 1:
        gaps = normalized["timestamp"].diff().dropna()
        if not (gaps == pd.Timedelta(hours=1)).all():
            raise ValueError("regulation history must be continuous hourly data")
    return normalized


def expand_hourly_to_intervals(
    values: Iterable[float], intervals_per_hour: int = 4
) -> np.ndarray:
    """Repeat hourly values for the internal 15-minute optimization grid."""
    if intervals_per_hour <= 0:
        raise ValueError("intervals_per_hour must be positive")
    hourly = np.asarray(list(values), dtype=float)
    if hourly.ndim != 1:
        raise ValueError("hourly values must be one-dimensional")
    return np.repeat(hourly, intervals_per_hour)


def build_hourly_demand_forecast(
    history: pd.DataFrame,
    future_demand: Iterable[float] | None = None,
) -> tuple[np.ndarray, str]:
    """Build 24 hourly demand values, using uploaded values or hourly medians."""
    normalized = normalize_regulation_history(history)
    if future_demand is not None:
        demand = np.asarray(list(future_demand), dtype=float)
        if demand.shape != (24,):
            raise ValueError("future demand must contain exactly 24 hourly values")
        if not np.isfinite(demand).all() or (demand < 0).any():
            raise ValueError("future demand must contain finite non-negative values")
        return demand, "uploaded"

    by_hour = normalized.assign(hour=normalized["timestamp"].dt.hour).groupby(
        "hour"
    )["regulation_demand_mw"].median()
    fallback = float(normalized["regulation_demand_mw"].median())
    demand = np.asarray([by_hour.get(hour, fallback) for hour in range(24)], dtype=float)
    return demand, "estimated"
