"""
backend/services/data_service.py — Single responsibility: loading and querying the Titanic dataset.
All pandas operations live here. Nothing else imports pandas.
"""

import logging
import pandas as pd
from functools import lru_cache
import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from config import TITANIC_CSV_PATH

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_dataframe() -> pd.DataFrame:
    """Load Titanic CSV once and cache it. Never reloads on each request."""
    logger.info(f"Loading Titanic dataset from: {TITANIC_CSV_PATH}")
    return pd.read_csv(TITANIC_CSV_PATH)


def get_male_percentage() -> str:
    """Returns the percentage of male passengers."""
    df = get_dataframe()
    pct = round((df["Sex"] == "male").mean() * 100, 2)
    return f"{pct}%"


def get_female_percentage() -> str:
    """Returns the percentage of female passengers."""
    df = get_dataframe()
    pct = round((df["Sex"] == "female").mean() * 100, 2)
    return f"{pct}%"


def get_average_fare() -> str:
    """Returns the average ticket fare paid by passengers."""
    df = get_dataframe()
    avg = round(df["Fare"].mean(), 2)
    return f"${avg}"


def get_survival_rate() -> str:
    """Returns the overall survival rate as a percentage."""
    df = get_dataframe()
    rate = round(df["Survived"].mean() * 100, 2)
    return f"{rate}%"


def get_embarkation_counts() -> str:
    """Returns the number of passengers per embarkation port."""
    df = get_dataframe()
    port_labels = {"S": "Southampton", "C": "Cherbourg", "Q": "Queenstown"}
    counts = df["Embarked"].value_counts().to_dict()
    result = {port_labels.get(k, k): v for k, v in counts.items()}
    return str(result)


def get_age_data() -> list:
    """Returns list of passenger ages (NaN values dropped)."""
    df = get_dataframe()
    return df["Age"].dropna().tolist()


def get_age_stats() -> str:
    """Returns mean, min and max passenger age."""
    df = get_dataframe()
    ages = df["Age"].dropna()
    return (
        f"Average age: {round(ages.mean(), 1)}, "
        f"Youngest: {int(ages.min())}, "
        f"Oldest: {int(ages.max())}"
    )


def get_total_passengers() -> str:
    """Returns the number of passenger records in the dataset (not the full Titanic manifest)."""
    df = get_dataframe()
    total = len(df)
    return f"{total} records (note: this is an ML training sample, not the full ~2,224 passenger manifest)"


def get_dataset_summary() -> str:
    """Returns a computed summary of key dataset statistics — no hardcoded values."""
    df = get_dataframe()
    total       = len(df)
    survived    = int(df["Survived"].sum())
    not_survived = total - survived
    survival_pct = round(df["Survived"].mean() * 100, 2)
    male_count   = int((df["Sex"] == "male").sum())
    female_count = int((df["Sex"] == "female").sum())
    avg_fare     = round(df["Fare"].mean(), 2)
    avg_age      = round(df["Age"].dropna().mean(), 1)
    return (
        f"Dataset has {total} records. "
        f"Survived: {survived} ({survival_pct}%), "
        f"Did not survive: {not_survived}. "
        f"Male: {male_count}, Female: {female_count}. "
        f"Avg fare: ${avg_fare}, Avg age: {avg_age}."
    )


def get_class_distribution() -> str:
    """Returns the number of passengers per travel class."""
    df = get_dataframe()
    counts = df["Pclass"].value_counts().sort_index().to_dict()
    labels = {1: "First Class", 2: "Second Class", 3: "Third Class"}
    result = {labels[k]: v for k, v in counts.items()}
    return str(result)


def get_top_wealthiest_passengers(limit: int = 50) -> pd.DataFrame:
    """Returns a DataFrame of the top wealthiest passengers based on Fare."""
    df = get_dataframe()
    # Sort by Fare descending, drop duplicates by Name just in case, take top N
    top_df = df.sort_values(by="Fare", ascending=False).drop_duplicates(subset=["Name"]).head(limit)
    return top_df


def get_survival_by_sex() -> str:
    """Returns survival counts broken down by sex."""
    df = get_dataframe()
    result = df.groupby("Sex")["Survived"].agg(["sum", "count"]).to_dict()
    male_survived = result["sum"]["male"]
    male_total = result["count"]["male"]
    female_survived = result["sum"]["female"]
    female_total = result["count"]["female"]
    return (
        f"Male: {male_survived}/{male_total} survived "
        f"({round(male_survived/male_total*100, 1)}%), "
        f"Female: {female_survived}/{female_total} survived "
        f"({round(female_survived/female_total*100, 1)}%)"
    )