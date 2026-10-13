"""Gráficos de la distancia direccional."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from sklearn.metrics import roc_auc_score, roc_curve

from .config import (
    AXIS,
    FIGURES_DIR,
    GRID,
    INK,
    INK_MUTED,
    INK_SECONDARY,
    SERIES_COLORS,
    SURFACE,
)

CLASS_LABELS = {0: "Normal", 1: "No normal (sospechoso o patológico)"}


def set_style() -> None:
    """Fija el estilo común a todos los gráficos de la clase."""
    sns.set_theme(
        style="ticks",
        rc={
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": AXIS,
            "axes.labelcolor": INK_SECONDARY,
            "axes.titlecolor": INK,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "text.color": INK,
            "xtick.color": INK_MUTED,
            "ytick.color": INK_MUTED,
            "xtick.labelcolor": INK_SECONDARY,
            "ytick.labelcolor": INK_SECONDARY,
            "legend.frameon": False,
        },
    )


def save_figure(fig: Figure, name: str) -> None:
    """Guarda la figura como PNG en ``data/processed/figures/``."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / f"{name}.png", dpi=200, bbox_inches="tight")


def plot_score_distribution(score: np.ndarray, y: pd.Series, threshold: float) -> Figure:
    """Distribución del puntaje en los CTG normales y no normales, con el umbral."""
    fig, ax = plt.subplots(figsize=(10, 5))
    bins = np.linspace(0, np.quantile(score, 0.995), 50)
    for label, color in zip(CLASS_LABELS, SERIES_COLORS):
        ax.hist(
            score[y.to_numpy() == label],
            bins=bins,
            density=True,
            histtype="step",
            linewidth=2,
            color=color,
            label=f"{CLASS_LABELS[label]} (n = {(y == label).sum()})",
        )
    ax.axvline(threshold, color=INK, linestyle="--", linewidth=1)
    ax.text(threshold, ax.get_ylim()[1] * 0.95, "  umbral: 5% con mayor puntaje",
            fontsize=9, color=INK_SECONDARY, va="top")
    ax.set_xlabel("Distancia direccional (desvíos de riesgo, en z-scores)")
    ax.set_ylabel("Densidad")
    ax.set_title("Distribución del puntaje según el estado fetal", fontsize=13, pad=12)
    ax.grid(axis="x", visible=False)
    # Debajo del gráfico, para no tapar los histogramas.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)
    fig.tight_layout()
    return fig


def plot_roc(scores: dict[str, np.ndarray], y: pd.Series) -> Figure:
    """Curvas ROC de varios puntajes, con su AUC en la leyenda."""
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot([0, 1], [0, 1], color=AXIS, linestyle="--", linewidth=1, label="Azar (AUC = 0,5)")
    for (name, score), color in zip(scores.items(), SERIES_COLORS):
        fpr, tpr, _ = roc_curve(y, score)
        auc = roc_auc_score(y, score)
        ax.plot(fpr, tpr, color=color, linewidth=2, label=f"{name} (AUC = {auc:.2f})".replace(".", ","))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    ax.set_aspect("equal")
    ax.set_xlabel("Tasa de falsos positivos (1 − especificidad)")
    ax.set_ylabel("Tasa de verdaderos positivos (recall)")
    ax.set_title("Curva ROC", fontsize=13, pad=12)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    return fig


def plot_contributions(contributions: pd.DataFrame, y: pd.Series) -> Figure:
    """Desvío de riesgo medio de cada variable en los CTG normales y no normales."""
    means = contributions.groupby(y.to_numpy()).mean().T.rename(columns=CLASS_LABELS)
    means = means.sort_values(CLASS_LABELS[1])
    positions = np.arange(len(means))
    height = 0.38

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for offset, (column, color) in zip((-height / 2, height / 2), zip(means.columns, SERIES_COLORS)):
        ax.barh(positions + offset, means[column], height=height, color=color,
                edgecolor=SURFACE, linewidth=2, label=column)
    for position, value in zip(positions, means[CLASS_LABELS[1]]):
        ax.text(value, position + height / 2, f" {value:.2f}".replace(".", ","),
                va="center", fontsize=8, color=INK_SECONDARY)
    ax.set_yticks(positions, means.index)
    ax.set_xlabel("Desvío de riesgo medio (z-scores; 0 = sin desvío de riesgo)")
    ax.set_title("Qué variables alejan a los CTG del centro en la dirección de riesgo", fontsize=13, pad=12)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig


def plot_tradeoff(score: np.ndarray, y: pd.Series, marks: dict[str, float]) -> Figure:
    """TP, FP y FN según la proporción de registros marcados como anomalía.

    ``marks`` son proporciones de referencia que se marcan con líneas
    verticales (nombre -> proporción).
    """
    y_true = y.to_numpy()
    order = np.argsort(-score)
    flagged = np.arange(1, len(score) + 1)
    tp = np.cumsum(y_true[order])
    counts = {"TP (anomalías detectadas)": tp, "FP (falsas alarmas)": flagged - tp,
              "FN (anomalías no detectadas)": y_true.sum() - tp}
    rate = flagged / len(score)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    limit = rate <= 0.5
    for (name, values), color in zip(counts.items(), SERIES_COLORS):
        ax.plot(rate[limit], values[limit], color=color, linewidth=2, label=name)
    for name, value in marks.items():
        ax.axvline(value, color=INK_MUTED, linestyle="--", linewidth=1)
        index = int(np.ceil(value * len(score))) - 1
        ax.text(value, ax.get_ylim()[1] * 0.98,
                f" {name}\n TP {tp[index]} · FP {flagged[index] - tp[index]} · FN {y_true.sum() - tp[index]}",
                fontsize=8.5, color=INK_SECONDARY, va="top")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_xlabel("Proporción de CTG marcados como anomalía")
    ax.set_ylabel("Cantidad de CTG")
    ax.set_title("Compromiso entre detectar anomalías y generar falsas alarmas", fontsize=13, pad=12)
    ax.legend(loc="center right")
    fig.tight_layout()
    return fig
