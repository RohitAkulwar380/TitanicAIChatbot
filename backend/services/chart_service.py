"""
backend/services/chart_service.py — Single responsibility: generating charts.
Returns base64-encoded PNG strings for JSON transport.
All matplotlib operations live here.
"""

import io
import base64
import logging
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — required for server environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.services.data_service import (
    get_dataframe,
    get_age_data,
    get_embarkation_counts,
    get_top_wealthiest_passengers,
)

logger = logging.getLogger(__name__)

# Shared color palette
PALETTE = {
    "blue": "#4A90D9",
    "coral": "#E07B6A",
    "green": "#5BAD6F",
    "purple": "#9B6BC9",
    "gray": "#A0A0A0",
    "bg": "#1E1E2E",
    "text": "#E0E0E0",
}


def _apply_dark_style(ax, fig) -> None:
    """Apply consistent dark theme to any matplotlib axes."""
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
    ax.tick_params(colors=PALETTE["text"])
    ax.xaxis.label.set_color(PALETTE["text"])
    ax.yaxis.label.set_color(PALETTE["text"])
    ax.title.set_color(PALETTE["text"])
    for spine in ax.spines.values():
        spine.set_edgecolor("#444455")


def fig_to_base64(fig) -> str:
    """Convert any matplotlib figure to a base64 PNG string for JSON transport."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def age_histogram() -> str:
    """Generates a histogram of passenger ages. Returns base64 PNG."""
    ages = get_age_data()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(ages, bins=20, color=PALETTE["blue"], edgecolor=PALETTE["bg"], linewidth=0.8, alpha=0.9)
    ax.set_title("Distribution of Passenger Ages", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Age", fontsize=11)
    ax.set_ylabel("Number of Passengers", fontsize=11)
    _apply_dark_style(ax, fig)
    logger.info("Generated age histogram")
    return fig_to_base64(fig)


def embarkation_bar_chart() -> str:
    """Generates a bar chart of passengers per embarkation port. Returns base64 PNG."""
    df = get_dataframe()
    port_labels = {"S": "Southampton", "C": "Cherbourg", "Q": "Queenstown"}
    counts = df["Embarked"].value_counts()
    labels = [port_labels.get(k, k) for k in counts.index]
    colors = [PALETTE["blue"], PALETTE["coral"], PALETTE["green"]]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(labels, counts.values, color=colors, edgecolor=PALETTE["bg"], linewidth=0.8)
    ax.set_title("Passengers by Embarkation Port", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Number of Passengers", fontsize=11)
    for bar, val in zip(bars, counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 5,
            str(val),
            ha="center", va="bottom",
            color=PALETTE["text"], fontsize=11, fontweight="bold"
        )
    _apply_dark_style(ax, fig)
    logger.info("Generated embarkation bar chart")
    return fig_to_base64(fig)


def survival_pie_chart() -> str:
    """Generates a pie chart showing survival rates. Returns base64 PNG."""
    df = get_dataframe()
    survived = df["Survived"].sum()
    not_survived = len(df) - survived
    values = [survived, not_survived]
    labels = [f"Survived\n({survived})", f"Did Not Survive\n({not_survived})"]
    colors = [PALETTE["green"], PALETTE["coral"]]
    explode = (0.05, 0)

    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        explode=explode,
        autopct="%1.1f%%",
        startangle=140,
        textprops={"color": PALETTE["text"], "fontsize": 11},
    )
    for autotext in autotexts:
        autotext.set_fontweight("bold")
    ax.set_title("Passenger Survival Distribution", fontsize=14, fontweight="bold", pad=15)
    fig.patch.set_facecolor(PALETTE["bg"])
    logger.info("Generated survival pie chart")
    return fig_to_base64(fig)


def survival_by_class_bar_chart() -> str:
    """Generates a grouped bar chart of survival by passenger class. Returns base64 PNG."""
    df = get_dataframe()
    class_labels = {1: "1st Class", 2: "2nd Class", 3: "3rd Class"}
    groups = df.groupby("Pclass")["Survived"].agg(["sum", "count"])
    classes = [class_labels[c] for c in groups.index]
    survived = groups["sum"].tolist()
    not_survived = (groups["count"] - groups["sum"]).tolist()

    x = range(len(classes))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    b1 = ax.bar([i - width / 2 for i in x], survived, width, label="Survived", color=PALETTE["green"])
    b2 = ax.bar([i + width / 2 for i in x], not_survived, width, label="Did Not Survive", color=PALETTE["coral"])
    ax.set_xticks(list(x))
    ax.set_xticklabels(classes)
    ax.set_title("Survival by Passenger Class", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Number of Passengers", fontsize=11)
    ax.legend(facecolor="#2A2A3E", labelcolor=PALETTE["text"])
    _apply_dark_style(ax, fig)
    logger.info("Generated survival by class bar chart")
    return fig_to_base64(fig)


def sex_distribution_pie_chart() -> str:
    """Generates a pie chart of male vs female distribution. Returns base64 PNG."""
    df = get_dataframe()
    counts = df["Sex"].value_counts()
    
    # Capitalize for labels
    labels = [f"{str(idx).capitalize()}\n({val})" for idx, val in counts.items()]
    
    # Use standard palette colors for distinction
    colors = [PALETTE["blue"], PALETTE["purple"]]
    explode = (0.05, 0)

    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=labels,
        colors=colors,
        explode=explode,
        autopct="%1.1f%%",
        startangle=90,
        textprops={"color": PALETTE["text"], "fontsize": 11},
    )
    for autotext in autotexts:
        autotext.set_fontweight("bold")
    ax.set_title("Passenger Sex Distribution", fontsize=14, fontweight="bold", pad=15)
    fig.patch.set_facecolor(PALETTE["bg"])
    logger.info("Generated sex distribution pie chart")
    return fig_to_base64(fig)



def top_wealthiest_bar_chart() -> str:
    """Generates a horizontal bar chart of the top 50 wealthiest passengers by fare. Returns base64 PNG."""
    df_top = get_top_wealthiest_passengers(50)
    
    # We want highest fare at the top, so we sort ascending before plotting horizontal bars
    df_plot = df_top.sort_values(by="Fare", ascending=True)
    
    names = df_plot["Name"].tolist()
    fares = df_plot["Fare"].tolist()

    # For 50 passengers, we need a very tall chart
    fig, ax = plt.subplots(figsize=(10, 15))
    
    # Clean up names for better display (e.g. remove titles like Mr/Mrs if too long, or just take last name)
    # Most Titanic names are "LastName, Title. FirstName" -> we'll just use the full string but trim it
    short_names = [n[:25] + "..." if len(n) > 25 else n for n in names]

    bars = ax.barh(short_names, fares, color=PALETTE["blue"], edgecolor=PALETTE["bg"], linewidth=0.5)
    
    ax.set_title("Top 50 Wealthiest Passengers (by Ticket Fare)", fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Ticket Fare (£)", fontsize=12)
    # Hide Y-axis label since the names are self-explanatory
    
    _apply_dark_style(ax, fig)
    
    # Add fare values next to bars for readability
    for bar in bars:
        ax.text(
            bar.get_width() + 2,
            bar.get_y() + bar.get_height() / 2,
            f"£{int(bar.get_width())}",
            va="center",
            color=PALETTE["text"],
            fontsize=8
        )
        
    plt.tight_layout()
    logger.info("Generated top wealthiest passengers chart")
    return fig_to_base64(fig)

