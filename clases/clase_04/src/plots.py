"""Gráficos del análisis exploratorio y del PCA."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from .config import (
    AXIS,
    DIVERGING_COLORS,
    FEATURE_LABELS,
    FIGURES_DIR,
    GRID,
    INK,
    INK_MUTED,
    INK_SECONDARY,
    PALETTE,
    SURFACE,
    TARGET,
)

CORRELATION_CMAP = LinearSegmentedColormap.from_list("correlacion", DIVERGING_COLORS)


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


def _class_legend(fig: Figure, **kwargs) -> None:
    """Leyenda de cultivares a nivel figura (una sola para todos los paneles)."""
    handles = [Patch(color=color, label=name) for name, color in PALETTE.items()]
    fig.legend(handles=handles, title="Cultivar", **kwargs)


def _class_histogram(data: pd.DataFrame, x: str, ax: plt.Axes, **kwargs) -> None:
    """Histograma + KDE de ``x``, una serie por cultivar."""
    sns.histplot(
        data=data,
        x=x,
        hue=TARGET,
        kde=True,
        element="step",
        palette=PALETTE,
        ax=ax,
        linewidth=0.8,
        legend=False,
        **kwargs,
    )


def plot_distributions(wine: pd.DataFrame, features: list[str], ncols: int = 4) -> Figure:
    """Histograma con KDE de cada variable, separado por cultivar."""
    nrows = int(np.ceil(len(features) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.6 * ncols, 3 * nrows))
    axes = axes.flatten()

    for ax, feature in zip(axes, features):
        _class_histogram(wine, feature, ax, bins=15)
        ax.set_title(FEATURE_LABELS.get(feature, feature), fontsize=11)
        ax.set_xlabel("")
        ax.set_ylabel("Frecuencia", fontsize=9)
    for ax in axes[len(features):]:
        ax.set_axis_off()

    fig.suptitle(
        "Distribución univariante de las variables originales por cultivar",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    # La leyenda ocupa el lugar de los paneles vacíos del final de la grilla.
    _class_legend(fig, loc="lower right", bbox_to_anchor=(0.97, 0.08), fontsize=11)
    return fig


def plot_correlation_heatmap(corr: pd.DataFrame) -> Figure:
    """Mapa de calor de una matriz de correlación."""
    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        annot_kws={"fontsize": 7},
        cmap=CORRELATION_CMAP,
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        linewidths=1,
        linecolor=SURFACE,
        cbar_kws={"label": "Correlación de Pearson", "shrink": 0.8},
        ax=ax,
    )
    ax.grid(False)
    ax.tick_params(length=0)
    ax.set_title("Matriz de correlación (Wine dataset)", fontsize=14, pad=12)
    fig.tight_layout()
    return fig


def plot_pairplot(wine: pd.DataFrame, features: list[str]) -> Figure:
    """Matriz de dispersión de ``features``, coloreada por cultivar."""
    grid = sns.pairplot(
        wine,
        vars=features,
        hue=TARGET,
        palette=PALETTE,
        diag_kind="kde",
        plot_kws={"alpha": 0.7, "s": 28, "edgecolor": SURFACE, "linewidth": 0.5},
        height=2.1,
    )
    grid.legend.set_title("Cultivar")
    grid.figure.suptitle(
        "Matriz de dispersión multivariante: Wine dataset",
        y=1.02,
        fontsize=14,
        fontweight="bold",
    )
    return grid.figure


def plot_scree(eigenvalues: np.ndarray, var_exp: np.ndarray) -> Figure:
    """Scree plot: autovalores (con el corte de Kaiser) y varianza acumulada."""
    components = np.arange(1, len(eigenvalues) + 1)
    fig, (ax_eig, ax_cum) = plt.subplots(1, 2, figsize=(13, 4.8))

    ax_eig.bar(components, eigenvalues, width=0.7, color=PALETTE["class_0"])
    ax_eig.axhline(1, color=INK_SECONDARY, linestyle="--", linewidth=1)
    ax_eig.text(
        components[-1] + 0.4,
        1.05,
        "Criterio de Kaiser (λ = 1)",
        ha="right",
        va="bottom",
        fontsize=9,
        color=INK_SECONDARY,
    )
    for component, eigenvalue, ratio in zip(components, eigenvalues, var_exp):
        if ratio >= 0.05:
            ax_eig.text(
                component,
                eigenvalue + 0.08,
                f"{ratio * 100:.1f}%",
                ha="center",
                fontsize=9,
                color=INK_SECONDARY,
            )
    ax_eig.set_title("Autovalor por componente (% de varianza explicada)", fontsize=11)
    ax_eig.set_ylabel("Autovalor")

    ax_cum.plot(components, np.cumsum(var_exp), color=PALETTE["class_0"], marker="o", linewidth=2)
    ax_cum.set_ylim(0, 1.05)
    ax_cum.yaxis.set_major_formatter(lambda value, _: f"{value * 100:.0f}%")
    ax_cum.set_title("Varianza explicada acumulada", fontsize=11)
    ax_cum.set_ylabel("Proporción acumulada")

    for ax in (ax_eig, ax_cum):
        ax.set_xlabel("Componente principal (PC)")
        ax.set_xticks(components)
        ax.grid(axis="x", visible=False)

    fig.suptitle("Scree plot: gráfico de codo", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_biplot(
    scores: pd.DataFrame,
    loadings: pd.DataFrame,
    classes: pd.Series,
    var_exp: np.ndarray,
) -> Figure:
    """Biplot PC1 vs PC2: observaciones por cultivar y flechas de los loadings."""
    fig, ax = plt.subplots(figsize=(10, 8))

    for name, color in PALETTE.items():
        mask = classes == name
        ax.scatter(
            scores.loc[mask, "PC1"],
            scores.loc[mask, "PC2"],
            label=name,
            color=color,
            alpha=0.75,
            s=45,
            edgecolors=SURFACE,
            linewidths=0.6,
        )

    # Los loadings viven en [-1, 1]: se reescalan para ocupar el rango de los scores.
    scale = 0.9 * scores[["PC1", "PC2"]].abs().to_numpy().max()
    for feature, (x, y) in loadings[["PC1", "PC2"]].iterrows():
        ax.annotate(
            "",
            xy=(x * scale, y * scale),
            xytext=(0, 0),
            arrowprops={"arrowstyle": "-|>", "color": INK_SECONDARY, "linewidth": 1.2},
        )
        # La etiqueta va pasando la punta, alineada hacia afuera del origen.
        ax.annotate(
            feature,
            xy=(x * scale, y * scale),
            xytext=(6 * np.sign(x), 6 * np.sign(y)),
            textcoords="offset points",
            ha="left" if x > 0 else "right",
            va="bottom" if y > 0 else "top",
            fontsize=9,
            fontweight="bold",
            color=INK,
        )

    ax.margins(0.12)
    ax.axhline(0, color=AXIS, linewidth=0.8)
    ax.axvline(0, color=AXIS, linewidth=0.8)
    ax.set_xlabel(f"PC1 ({var_exp[0] * 100:.1f}% var. explicada)", fontsize=12)
    ax.set_ylabel(f"PC2 ({var_exp[1] * 100:.1f}% var. explicada)", fontsize=12)
    ax.set_title("Biplot: análisis de componentes principales (PC1 vs PC2)", fontsize=13, pad=15)
    ax.legend(title="Cultivar", loc="best")
    fig.tight_layout()
    return fig


def plot_pc_histograms(scores: pd.DataFrame, classes: pd.Series, var_exp: np.ndarray) -> Figure:
    """Histograma con KDE de los scores de PC1 y PC2, separado por cultivar."""
    data = scores[["PC1", "PC2"]].assign(**{TARGET: classes})
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    for ax, component, ratio in zip(axes, ["PC1", "PC2"], var_exp):
        _class_histogram(data, component, ax, bins=20)
        ax.set_title(f"Distribución de {component} ({ratio * 100:.1f}% var. exp.)", fontsize=12)
        ax.set_xlabel(f"Puntuaciones de {component}", fontsize=11)
        ax.set_ylabel("Frecuencia", fontsize=11)

    fig.suptitle(
        "Análisis univariante de las componentes principales",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 0.92, 1])
    _class_legend(fig, loc="center right")
    return fig
