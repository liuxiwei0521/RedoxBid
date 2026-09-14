"""Adapters that keep market-model inputs and comparison outputs consistent."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyomo.environ as pyo

from utils.regulation_data import expand_hourly_to_intervals


def build_regulation_market_frame(
    hourly_forecast: pd.DataFrame,
    *,
    capacity_price_cny_per_mw_h: float,
    performance_score: float,
    mileage_ratio: float,
) -> pd.DataFrame:
    required = {
        "regulation_demand_mw",
        "mileage_price_cny_per_mw",
    }
    missing = required.difference(hourly_forecast.columns)
    if missing:
        raise ValueError(f"missing regulation forecast columns: {sorted(missing)}")
    if len(hourly_forecast) != 24:
        raise ValueError("regulation forecast must contain exactly 24 hourly rows")
    if capacity_price_cny_per_mw_h < 0 or not 0 <= performance_score <= 1:
        raise ValueError("invalid capacity price or performance score")
    if mileage_ratio < 0:
        raise ValueError("mileage ratio must be non-negative")

    return pd.DataFrame(
        {
            "regulation_demand_mw": expand_hourly_to_intervals(
                hourly_forecast["regulation_demand_mw"]
            ),
            "capacity_price_cny_per_mw_h": np.full(
                96, float(capacity_price_cny_per_mw_h)
            ),
            "mileage_price_cny_per_mw": expand_hourly_to_intervals(
                hourly_forecast["mileage_price_cny_per_mw"]
            ),
            "performance_score": np.full(96, float(performance_score)),
            "mileage_ratio": np.full(96, float(mileage_ratio)),
        }
    )


def build_baseline_schedule(model, day_ahead_prices) -> pd.DataFrame:
    prices = np.asarray(day_ahead_prices, dtype=float)
    if prices.shape != (96,):
        raise ValueError("day-ahead prices must contain exactly 96 intervals")
    return pd.DataFrame(
        {
            "charge_power_mw": [pyo.value(model.P_charge[t]) for t in range(96)],
            "discharge_power_mw": [
                pyo.value(model.P_discharge[t]) for t in range(96)
            ],
            "energy_mwh": [pyo.value(model.E[t]) for t in range(96)],
            "day_ahead_price_cny_per_mwh": prices,
        }
    )


def build_market_comparison(
    day_ahead_profit_cny: float,
    sequential_profit_cny: float,
    joint_profit_cny: float,
) -> pd.DataFrame:
    baseline = float(day_ahead_profit_cny)
    totals = [baseline, float(sequential_profit_cny), float(joint_profit_cny)]
    return pd.DataFrame(
        {
            "scenario": ["day_ahead_only", "sequential", "joint"],
            "total_profit_cny": totals,
            "increment_vs_day_ahead_cny": [value - baseline for value in totals],
        }
    )
