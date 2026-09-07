"""Structural checks on the four dataset CSVs.

These guard the deployed app: a single unquoted comma in a free-text column
makes ``pd.read_csv`` raise a ParserError whose message Streamlit Cloud
redacts, so the whole app dies with no usable diagnostic.

Run: ``pytest`` from the repo root.
"""

import csv
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent
DATASETS = ["actuators.csv", "motors.csv", "gearboxes.csv", "drivers.csv"]


@pytest.mark.parametrize("name", DATASETS)
def test_dataset_is_rectangular(name):
    """Every row carries exactly as many fields as the header."""
    path = HERE / name
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        ragged = [
            (i, len(row))
            for i, row in enumerate(reader, start=2)
            if row and len(row) != len(header)
        ]
    assert not ragged, (
        f"{name}: rows {ragged} do not have {len(header)} fields — "
        "an unquoted comma inside a field is the usual cause"
    )


@pytest.mark.parametrize("name", DATASETS)
def test_dataset_parses_with_pandas(name):
    df = pd.read_csv(HERE / name)
    assert len(df) > 0


@pytest.mark.parametrize("name", DATASETS)
def test_dataset_has_key_columns(name):
    df = pd.read_csv(HERE / name)
    assert {"manufacturer", "model"} <= set(df.columns)
