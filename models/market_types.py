"""Shared result contracts for deterministic market optimization models."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class MarketSolveResult:
    status: str
    objective_value: float | None
    schedule: pd.DataFrame
    kpis: dict[str, float] = field(default_factory=dict)
    diagnostics: tuple[str, ...] = ()
    solver_name: str = "CBC"
    raw_model: object | None = None


def interval_labels(total_steps: int = 96, minutes: int = 15) -> list[str]:
    labels = []
    for step in range(total_steps):
        start_minutes = step * minutes
        end_minutes = (step + 1) * minutes
        labels.append(
            f"{start_minutes // 60:02d}:{start_minutes % 60:02d}-"
            f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
        )
    return labels
