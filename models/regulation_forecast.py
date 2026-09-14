"""Leakage-aware 24-hour regulation mileage-price forecasting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from utils.regulation_data import (
    build_hourly_demand_forecast,
    normalize_regulation_history,
)


FEATURE_COLUMNS = [
    "demand",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "is_weekend",
    "demand_lag_1",
    "demand_lag_24",
    "price_lag_1",
    "price_roll_24_mean",
    "price_roll_24_std",
]


@dataclass(frozen=True)
class RegulationForecastResult:
    hourly_forecast: pd.DataFrame
    model_name: str
    metrics: dict[str, float | None]
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    data_source: str
    demand_source: str


def _feature_frame(history: pd.DataFrame) -> pd.DataFrame:
    frame = history.copy()
    timestamp = frame["timestamp"]
    hour = timestamp.dt.hour
    weekday = timestamp.dt.dayofweek
    price = frame["mileage_price_cny_per_mw"]
    demand = frame["regulation_demand_mw"]

    features = pd.DataFrame(
        {
            "timestamp": timestamp,
            "target": price,
            "demand": demand,
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
            "weekday_sin": np.sin(2 * np.pi * weekday / 7),
            "weekday_cos": np.cos(2 * np.pi * weekday / 7),
            "is_weekend": (weekday >= 5).astype(float),
            "demand_lag_1": demand.shift(1),
            "demand_lag_24": demand.shift(24),
            "price_lag_1": price.shift(1),
            "price_roll_24_mean": price.shift(1).rolling(24).mean(),
            "price_roll_24_std": price.shift(1).rolling(24).std(ddof=0),
        }
    )
    return features.dropna().reset_index(drop=True)


def _models(random_state: int) -> dict[str, object]:
    return {
        "Linear Regression": Pipeline(
            [("scale", StandardScaler()), ("model", LinearRegression())]
        ),
        "Random Forest": RandomForestRegressor(
            n_estimators=120,
            max_depth=8,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=1,
        ),
    }


def _direction_accuracy(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    if len(actual) < 2:
        return None
    actual_direction = np.sign(np.diff(actual))
    predicted_direction = np.sign(np.diff(predicted))
    return float(np.mean(actual_direction == predicted_direction))


def _future_feature_row(
    timestamp: pd.Timestamp,
    demand: float,
    demand_history: list[float],
    price_history: list[float],
) -> pd.DataFrame:
    hour = timestamp.hour
    weekday = timestamp.dayofweek
    recent_prices = np.asarray(price_history[-24:], dtype=float)
    row = {
        "demand": demand,
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "weekday_sin": np.sin(2 * np.pi * weekday / 7),
        "weekday_cos": np.cos(2 * np.pi * weekday / 7),
        "is_weekend": float(weekday >= 5),
        "demand_lag_1": demand_history[-1],
        "demand_lag_24": demand_history[-24],
        "price_lag_1": price_history[-1],
        "price_roll_24_mean": float(recent_prices.mean()),
        "price_roll_24_std": float(recent_prices.std(ddof=0)),
    }
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


def forecast_regulation_prices(
    history: pd.DataFrame,
    *,
    future_demand=None,
    random_state: int = 42,
    data_source: str = "sample",
    price_upper_limit: float = 50.0,
    price_min_unit: float = 0.1,
) -> RegulationForecastResult:
    """Select on a chronological holdout, then forecast the next 24 hours."""
    normalized = normalize_regulation_history(history)
    if len(normalized) < 72:
        raise ValueError("at least 72 hourly history rows are required")
    if price_upper_limit <= 0 or price_min_unit <= 0:
        raise ValueError("price limits must be positive")

    supervised = _feature_frame(normalized)
    split = int(len(supervised) * 0.8)
    split = min(max(split, 1), len(supervised) - 1)
    train = supervised.iloc[:split]
    test = supervised.iloc[split:]
    if test.empty:
        raise ValueError("at least 72 hourly history rows are required")

    evaluations: dict[str, tuple[object, np.ndarray, float]] = {}
    for name, model in _models(random_state).items():
        model.fit(train[FEATURE_COLUMNS], train["target"])
        prediction = np.asarray(model.predict(test[FEATURE_COLUMNS]), dtype=float)
        mae = float(mean_absolute_error(test["target"], prediction))
        evaluations[name] = (model, prediction, mae)

    model_name = min(evaluations, key=lambda name: (evaluations[name][2], name))
    _, holdout_prediction, mae = evaluations[model_name]
    actual = test["target"].to_numpy(dtype=float)
    rmse = float(np.sqrt(mean_squared_error(actual, holdout_prediction)))
    r2 = None
    if len(actual) >= 2 and not np.isclose(np.var(actual), 0.0):
        r2 = float(r2_score(actual, holdout_prediction))

    selected = _models(random_state)[model_name]
    selected.fit(supervised[FEATURE_COLUMNS], supervised["target"])
    demand_forecast, demand_source = build_hourly_demand_forecast(
        normalized, future_demand
    )

    demand_history = normalized["regulation_demand_mw"].astype(float).tolist()
    price_history = normalized["mileage_price_cny_per_mw"].astype(float).tolist()
    start = normalized["timestamp"].max() + pd.Timedelta(hours=1)
    future_timestamps = pd.date_range(start, periods=24, freq="h")
    future_prices: list[float] = []
    for timestamp, demand in zip(future_timestamps, demand_forecast):
        row = _future_feature_row(
            timestamp,
            float(demand),
            demand_history,
            price_history,
        )
        raw_price = float(selected.predict(row)[0])
        clipped = np.clip(raw_price, 0.0, price_upper_limit)
        rounded = round(clipped / price_min_unit) * price_min_unit
        future_prices.append(float(rounded))
        demand_history.append(float(demand))
        price_history.append(float(rounded))

    forecast = pd.DataFrame(
        {
            "timestamp": future_timestamps,
            "regulation_demand_mw": demand_forecast,
            "mileage_price_cny_per_mw": future_prices,
        }
    )
    return RegulationForecastResult(
        hourly_forecast=forecast,
        model_name=model_name,
        metrics={
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "direction_accuracy": _direction_accuracy(actual, holdout_prediction),
        },
        train_end=pd.Timestamp(train["timestamp"].iloc[-1]),
        test_start=pd.Timestamp(test["timestamp"].iloc[0]),
        data_source=data_source,
        demand_source=demand_source,
    )
