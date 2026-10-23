"""Gráficos del TP."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

from .config import FIGURES_DIR

# Mismo estilo que los TP y clases anteriores.
ACCENT = "#2a78d6"
HIGHLIGHT = "#eb6834"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


def set_style() -> None:
    """Fija el estilo común a todos los gráficos del TP."""
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


def plot_numeric_distributions(
    df: pd.DataFrame,
    kinds: dict[str, str],
    ncols: int = 3,
    max_bars: int = 8,
) -> Figure:
    """Distribución de cada variable numérica, un panel por variable.

    ``kinds`` indica cómo graficar cada columna:

    - ``"hist"``: histograma.
    - ``"hist_log"``: histograma con el eje *y* en escala logarítmica, para
      ver la cola de una variable muy asimétrica.
    - ``"bar"`` / ``"bar_log"``: una barra por valor (variables discretas),
      con el eje *y* lineal o logarítmico. Si hay más de ``max_bars``
      valores, los menos frecuentes se agrupan en "otros".

    El título de cada panel incluye la asimetría (*skewness*) de la variable.
    """
    nrows = int(np.ceil(len(kinds) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 3.8 * nrows))
    axes = np.atleast_1d(axes).flatten()

    for ax, (column, kind) in zip(axes, kinds.items()):
        values = df[column].astype(float)
        if kind.startswith("hist"):
            bins = np.arange(values.min(), values.max() + 2) - 0.5 if values.nunique() < 300 else 100
            # Sin bordes: con barras angostas, el borde blanco del estilo las taparía.
            ax.hist(values, bins=bins, color=ACCENT, edgecolor="none")
        else:
            counts = values.value_counts()
            top = counts.iloc[:max_bars].sort_index()
            labels = [f"{v:g}" for v in top.index]
            if len(counts) > max_bars:
                top = pd.concat([top, pd.Series([counts.iloc[max_bars:].sum()])])
                labels.append("otros")
            ax.bar(labels, top.to_numpy(), color=ACCENT, edgecolor=SURFACE, linewidth=2)
            ax.grid(axis="x", visible=False)
        if kind.endswith("_log"):
            ax.set_yscale("log")
        ax.set_title(f"{column}  (asimetría = {values.skew():.2f})".replace(".", ","), fontsize=11)
        ax.set_ylabel("Eventos" + (" (escala log)" if kind.endswith("_log") else ""))
    for ax in axes[len(kinds):]:
        ax.set_axis_off()

    fig.suptitle("Distribución de las variables numéricas", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_scree(
    eigenvalues: np.ndarray,
    var_exp: np.ndarray,
    elbow: int | None = None,
    thresholds: tuple[float, ...] = (0.80, 0.90),
) -> Figure:
    """Scree plot (autovalores, con la línea de Kaiser) y varianza explicada acumulada."""
    components = np.arange(1, len(eigenvalues) + 1)
    cumulative = np.cumsum(var_exp)
    fig, (ax_eig, ax_cum) = plt.subplots(1, 2, figsize=(14, 5))

    ax_eig.plot(components, eigenvalues, color=ACCENT, marker="o", markersize=5, linewidth=2)
    ax_eig.axhline(1, color=INK_SECONDARY, linestyle="--", linewidth=1)
    ax_eig.text(components[-1], 1.03, "Kaiser (autovalor = 1)", ha="right", va="bottom",
                fontsize=9, color=INK_SECONDARY)
    if elbow is not None:
        ax_eig.plot(elbow, eigenvalues[elbow - 1], marker="o", markersize=10, color=HIGHLIGHT,
                    markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
        ax_eig.annotate(f"codo: PC{elbow}", xy=(elbow, eigenvalues[elbow - 1]),
                        xytext=(elbow + 2, eigenvalues[elbow - 1] + 0.3), fontsize=9, color=INK,
                        arrowprops={"arrowstyle": "-", "color": INK_SECONDARY, "linewidth": 0.8})
    ax_eig.set_title("Scree plot: autovalor de cada componente", fontsize=11)
    ax_eig.set_ylabel("Autovalor")

    ax_cum.plot(components, cumulative, color=ACCENT, marker="o", markersize=5, linewidth=2)
    for threshold in thresholds:
        k = int(np.argmax(cumulative >= threshold) + 1)
        ax_cum.axhline(threshold, color=INK_SECONDARY, linestyle="--", linewidth=1)
        ax_cum.text(1, threshold + 0.01, f"{threshold:.0%}: PC{k}", fontsize=9, color=INK_SECONDARY,
                    va="bottom")
    ax_cum.set_ylim(0, 1.05)
    ax_cum.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax_cum.set_title("Varianza explicada acumulada", fontsize=11)
    ax_cum.set_ylabel("Proporción de la varianza total")

    for ax in (ax_eig, ax_cum):
        ax.set_xlabel("Componente principal")
        ax.set_xticks(components[::2])
        ax.grid(axis="x", visible=False)
    fig.suptitle("Varianza explicada por las componentes principales", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_zero_spike(values: pd.Series, name: str, zoom: float = 0.5, bin_width: float = 0.01) -> Figure:
    """Distribución completa de una variable y zoom alrededor de 0.

    En el zoom, la barra que contiene al 0 exacto se resalta, para ver si
    los ceros forman un pico que no siguen los valores vecinos.
    """
    data = values.dropna().astype(float)
    fig, (ax_full, ax_zoom) = plt.subplots(1, 2, figsize=(14, 5))

    ax_full.hist(data, bins=100, color=ACCENT)
    ax_full.axvline(data.mean(), color=INK, linestyle="--", linewidth=1)
    ax_full.text(data.mean(), ax_full.get_ylim()[1] * 0.95, f"  media = {data.mean():.2f}".replace(".", ","),
                 fontsize=9, color=INK_SECONDARY, va="top")
    ax_full.set_title(f"Distribución completa de {name}", fontsize=11)
    ax_full.set_xlabel(name)
    ax_full.set_ylabel("Eventos")

    # Bordes centrados en 0, para que el 0 exacto caiga en una sola barra.
    edges = np.arange(-zoom, zoom + bin_width, bin_width) - bin_width / 2
    counts, edges, bars = ax_zoom.hist(data[data.abs() <= zoom], bins=edges, color=ACCENT)
    zero_bar = int(np.searchsorted(edges, 0) - 1)
    bars[zero_bar].set_color(HIGHLIGHT)
    n_zeros = int((data == 0).sum())
    ax_zoom.annotate(f"{n_zeros:,} ceros exactos".replace(",", "."),
                     xy=(0, counts[zero_bar]), xytext=(zoom * 0.25, counts[zero_bar] * 0.9),
                     fontsize=9, color=INK,
                     arrowprops={"arrowstyle": "-", "color": INK_SECONDARY, "linewidth": 0.8})
    ax_zoom.set_title(f"Zoom alrededor de 0 (barras de {bin_width:g})".replace(".", ","), fontsize=11)
    ax_zoom.set_xlabel(name)
    ax_zoom.set_ylabel("Eventos")

    for ax in (ax_full, ax_zoom):
        ax.grid(axis="x", visible=False)
    fig.suptitle(f"Distribución de {name}", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig
