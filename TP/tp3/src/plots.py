"""Gráficos de la descripción multivariante."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

from .config import (
    ACCENT,
    AXIS,
    DIVERGING_COLORS,
    FIGURES_DIR,
    GRID,
    HIGHLIGHT,
    INK,
    INK_MUTED,
    INK_SECONDARY,
    SEQUENTIAL_COLORS,
    SURFACE,
)
from .multivariate import variable_label

DIVERGING_CMAP = LinearSegmentedColormap.from_list("divergente", DIVERGING_COLORS)
SEQUENTIAL_CMAP = LinearSegmentedColormap.from_list("secuencial", SEQUENTIAL_COLORS)


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


def _heatmap(data: pd.DataFrame, ax: plt.Axes, **kwargs) -> None:
    """Mapa de calor con celdas separadas por el color de fondo."""
    sns.heatmap(data, linewidths=1, linecolor=SURFACE, ax=ax, **kwargs)
    ax.grid(False)
    ax.tick_params(length=0)
    ax.set_xlabel("")
    ax.set_ylabel("")


def cluster_order(distances: pd.DataFrame) -> list[str]:
    """Orden de las filas de una matriz de distancias según un clustering jerárquico.

    Pone juntos a los vectores más parecidos (enlace promedio), así los
    bloques de vectores similares se ven en el mapa de calor.
    """
    tree = linkage(squareform(distances.to_numpy(), checks=False), method="average")
    return distances.index[leaves_list(tree)].tolist()


def plot_mean_profiles(standardized: pd.DataFrame, title: str) -> Figure:
    """Vectores de medias (filas) en desvíos estándar respecto de la media global."""
    data = standardized.rename(columns=variable_label)
    limit = np.abs(data.to_numpy()).max()
    fig, ax = plt.subplots(figsize=(15, 0.45 * len(data) + 3.2))
    _heatmap(
        data,
        ax,
        annot=True,
        fmt=".2f",
        annot_kws={"fontsize": 7},
        cmap=DIVERGING_CMAP,
        vmin=-limit,
        vmax=limit,
        center=0,
        cbar_kws={"label": "Desvíos estándar respecto de la media global", "shrink": 0.8},
    )
    ax.set_title(title, fontsize=13, pad=12)
    fig.tight_layout()
    return fig


def plot_distance_matrix(distances: pd.DataFrame, title: str, label: str) -> Figure:
    """Mapa de calor de una matriz de distancias, ordenada por clustering."""
    order = cluster_order(distances)
    fig, ax = plt.subplots(figsize=(9.5, 8))
    _heatmap(
        distances.loc[order, order],
        ax,
        annot=True,
        fmt=".2f",
        annot_kws={"fontsize": 8},
        cmap=SEQUENTIAL_CMAP,
        vmin=0,
        square=True,
        cbar_kws={"label": label, "shrink": 0.8},
    )
    ax.set_title(title, fontsize=13, pad=12)
    fig.tight_layout()
    return fig


def plot_global_distances(distances: pd.DataFrame) -> Figure:
    """Distancia de cada país al vector global, una barra por métrica."""
    data = distances.sort_values(distances.columns[0])
    fig, axes = plt.subplots(1, len(data.columns), figsize=(6 * len(data.columns), 4.8), sharey=True)
    for ax, metric in zip(np.atleast_1d(axes), data.columns):
        ax.barh(data.index, data[metric], color=SEQUENTIAL_COLORS[2], height=0.7)
        for y, value in enumerate(data[metric]):
            ax.text(value, y, f" {value:.2f}", va="center", fontsize=9, color=INK_SECONDARY)
        ax.set_title(metric, fontsize=11)
        ax.set_xlabel("Distancia al vector de medias global")
        ax.grid(axis="y", visible=False)
        ax.margins(x=0.15)
    fig.suptitle("Distancia de cada país al perfil global", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_correlation_heatmap(corr: pd.DataFrame, title: str) -> Figure:
    """Mapa de calor de una matriz de correlación (triángulo inferior)."""
    data = corr.rename(index=variable_label, columns=variable_label)
    mask = np.triu(np.ones(data.shape, dtype=bool), k=1)
    size = 0.55 * len(data) + 3
    fig, ax = plt.subplots(figsize=(size + 2, size))
    _heatmap(
        data,
        ax,
        mask=mask,
        annot=True,
        fmt=".2f",
        annot_kws={"fontsize": 6},
        cmap=DIVERGING_CMAP,
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        cbar_kws={"label": "Correlación de Pearson", "shrink": 0.6},
    )
    ax.set_title(title, fontsize=14, pad=12)
    fig.tight_layout()
    return fig


def plot_country_correlation_grid(correlations: dict[str, pd.DataFrame], ncols: int = 5) -> Figure:
    """Matrices de correlación de cada país en paneles chicos, misma escala."""
    nrows = int(np.ceil(len(correlations) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.4 * ncols, 3.4 * nrows + 0.8))
    axes = np.atleast_1d(axes).flatten()
    for ax, (country, corr) in zip(axes, correlations.items()):
        mask = np.triu(np.ones(corr.shape, dtype=bool), k=1)
        _heatmap(
            corr,
            ax,
            mask=mask,
            cmap=DIVERGING_CMAP,
            vmin=-1,
            vmax=1,
            center=0,
            square=True,
            cbar=False,
            xticklabels=False,
            yticklabels=False,
        )
        ax.set_title(country, fontsize=11)
    for ax in axes[len(correlations):]:
        ax.set_axis_off()

    colorbar = fig.colorbar(
        axes[0].collections[0], ax=axes.tolist(), orientation="horizontal", fraction=0.04, pad=0.04
    )
    colorbar.set_label("Correlación de Pearson")
    colorbar.outline.set_visible(False)
    fig.suptitle(
        "Matrices de correlación por país (mismas variables y orden que la global)",
        fontsize=14,
        fontweight="bold",
    )
    return fig


def plot_scree(parallel: pd.DataFrame, var_exp: np.ndarray, n_components: int) -> Figure:
    """Scree plot con el nulo del análisis paralelo, y varianza acumulada.

    ``parallel`` es la salida de :func:`src.pca.parallel_analysis`;
    ``n_components`` es la cantidad elegida, que se marca en ambos paneles.
    """
    components = np.arange(1, len(parallel) + 1)
    null_column = next(c for c in parallel.columns if c.startswith("nulo_p"))
    fig, (ax_eig, ax_cum) = plt.subplots(1, 2, figsize=(14, 5))

    colors = [ACCENT if c <= n_components else SEQUENTIAL_COLORS[1] for c in components]
    ax_eig.bar(components, parallel["autovalor"], width=0.7, color=colors, label="Autovalor (datos)")
    ax_eig.plot(
        components,
        parallel[null_column],
        color=INK,
        linewidth=2,
        marker="o",
        markersize=4,
        label=f"Autovalor nulo (análisis paralelo, percentil {null_column.removeprefix('nulo_p')})",
    )
    ax_eig.axhline(1, color=INK_SECONDARY, linestyle="--", linewidth=1, label="Criterio de Kaiser (λ = 1)")
    ax_eig.set_title("Autovalor por componente", fontsize=11)
    ax_eig.set_ylabel("Autovalor")
    ax_eig.legend(loc="upper right", fontsize=9)

    cumulative = np.cumsum(var_exp)
    ax_cum.plot(components, cumulative, color=ACCENT, marker="o", markersize=5, linewidth=2)
    ax_cum.axhline(0.8, color=INK_SECONDARY, linestyle="--", linewidth=1)
    ax_cum.text(1, 0.81, "80%", fontsize=9, color=INK_SECONDARY, va="bottom")
    ax_cum.annotate(
        f"{n_components} componentes: {cumulative[n_components - 1]:.0%}",
        xy=(n_components, cumulative[n_components - 1]),
        xytext=(n_components + 2, cumulative[n_components - 1] - 0.12),
        fontsize=9,
        color=INK,
        arrowprops={"arrowstyle": "-", "color": INK_SECONDARY, "linewidth": 0.8},
    )
    ax_cum.set_ylim(0, 1.05)
    ax_cum.yaxis.set_major_formatter(lambda value, _: f"{value * 100:.0f}%")
    ax_cum.set_title("Varianza explicada acumulada", fontsize=11)
    ax_cum.set_ylabel("Proporción acumulada")

    for ax in (ax_eig, ax_cum):
        ax.set_xlabel("Componente principal (PC)")
        ax.set_xticks(components[::2])
        ax.grid(axis="x", visible=False)
        ax.axvline(n_components + 0.5, color=AXIS, linewidth=1)

    fig.suptitle("Gráfico de sedimentación (scree plot)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_loadings(loadings: pd.DataFrame, names: dict[str, str] | None = None) -> Figure:
    """Mapa de calor de los loadings (correlación variable-componente)."""
    data = loadings.rename(index=variable_label)
    if names:
        data = data.rename(columns=lambda c: f"{c}\n{names.get(c, '')}".strip())
    fig, ax = plt.subplots(figsize=(1.6 * data.shape[1] + 5, 0.4 * len(data) + 2))
    _heatmap(
        data,
        ax,
        annot=True,
        fmt=".2f",
        annot_kws={"fontsize": 8},
        cmap=DIVERGING_CMAP,
        vmin=-1,
        vmax=1,
        center=0,
        cbar_kws={"label": "Loading (correlación con la componente)", "shrink": 0.8},
    )
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", labelsize=9)
    ax.set_title("Loadings de las componentes retenidas", fontsize=13, pad=12)
    fig.tight_layout()
    return fig


def _repel_labels(fig: Figure, labels: list, step: float = 2.0, max_iter: int = 200) -> None:
    """Separa verticalmente las etiquetas de texto que se superponen.

    Corre en coordenadas de pantalla: mientras dos etiquetas se pisen, aleja
    la de más abajo hacia abajo y la de más arriba hacia arriba.
    """
    renderer = fig.canvas.get_renderer()
    for _ in range(max_iter):
        moved = False
        boxes = [label.get_window_extent(renderer).expanded(1.02, 1.1) for label in labels]
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                if not boxes[i].overlaps(boxes[j]):
                    continue
                lower, upper = (i, j) if boxes[i].y0 < boxes[j].y0 else (j, i)
                for index, sign in ((lower, -1), (upper, 1)):
                    x, y = labels[index].xyann
                    labels[index].xyann = (x, y + sign * step)
                moved = True
        if not moved:
            return


def plot_biplot(
    scores: pd.DataFrame,
    loadings: pd.DataFrame,
    var_exp: np.ndarray,
    outliers: pd.Series,
    min_loading: float = 0.35,
) -> Figure:
    """Biplot PC1 vs PC2: densidad de eventos, outliers y flechas de los loadings.

    Con más de 10^5 eventos un scatter se satura, así que la nube se muestra
    como densidad (hexágonos, escala logarítmica). Sólo se dibujan las
    flechas de las variables con loading de módulo >= ``min_loading`` en el
    plano, para que se puedan leer.
    """
    fig, ax = plt.subplots(figsize=(11, 8.5))
    hexes = ax.hexbin(
        scores["PC1"],
        scores["PC2"],
        gridsize=70,
        bins="log",
        cmap=SEQUENTIAL_CMAP,
        mincnt=1,
        linewidths=0,
    )
    ax.scatter(
        scores.loc[outliers, "PC1"],
        scores.loc[outliers, "PC2"],
        s=9,
        color=HIGHLIGHT,
        edgecolors=SURFACE,
        linewidths=0.3,
        label=f"Outliers multivariantes ({outliers.sum():,} eventos)",
    )
    colorbar = fig.colorbar(hexes, ax=ax, shrink=0.8)
    colorbar.set_label("Eventos por hexágono (escala log)")
    colorbar.outline.set_visible(False)

    plane = loadings[["PC1", "PC2"]]
    shown = plane[np.hypot(plane["PC1"], plane["PC2"]) >= min_loading]
    scale = 0.8 * scores[["PC1", "PC2"]].abs().quantile(0.999).min()
    labels = []
    for feature, (x, y) in shown.iterrows():
        ax.annotate(
            "",
            xy=(x * scale, y * scale),
            xytext=(0, 0),
            arrowprops={"arrowstyle": "-|>", "color": INK, "linewidth": 1.3},
        )
        # Flechas casi verticales: etiqueta centrada sobre la punta; si no,
        # hacia afuera del origen.
        vertical = abs(x) < 0.5 * abs(y)
        labels.append(
            ax.annotate(
                variable_label(feature),
                xy=(x * scale, y * scale),
                xytext=(0 if vertical else 6 * np.sign(x), 6 * np.sign(y)),
                textcoords="offset points",
                ha="center" if vertical else ("left" if x > 0 else "right"),
                va="bottom" if y > 0 else "top",
                fontsize=9,
                fontweight="bold",
                color=INK,
                bbox={"boxstyle": "round,pad=0.15", "facecolor": SURFACE, "edgecolor": "none", "alpha": 0.85},
            )
        )

    ax.axhline(0, color=AXIS, linewidth=0.8)
    ax.axvline(0, color=AXIS, linewidth=0.8)
    ax.grid(False)
    ax.set_xlabel(f"PC1 ({var_exp[0] * 100:.1f}% var. explicada)", fontsize=12)
    ax.set_ylabel(f"PC2 ({var_exp[1] * 100:.1f}% var. explicada)", fontsize=12)
    ax.set_title("Biplot: eventos en el plano PC1 vs PC2", fontsize=13, pad=12)
    ax.legend(loc="lower left", fontsize=9, markerscale=2)
    fig.tight_layout()
    _repel_labels(fig, labels)
    return fig


def plot_group_centroids(centroids: dict[str, pd.DataFrame], var_exp: np.ndarray) -> Figure:
    """Centroides (score medio) de grupos de eventos en el plano PC1 vs PC2.

    Un panel por agrupación (p. ej. país o tipo de interacción), cada uno con
    su propia escala: los grupos de una agrupación pueden estar mucho más
    cerca entre sí que los de otra.
    """
    fig, axes = plt.subplots(1, len(centroids), figsize=(7.5 * len(centroids), 6.5))
    labels = []
    for ax, (title, data) in zip(np.atleast_1d(axes), centroids.items()):
        ax.scatter(data["PC1"], data["PC2"], s=70, color=ACCENT, edgecolors=SURFACE, linewidths=2, zorder=3)
        labels += [
            ax.annotate(name, xy=(x, y), xytext=(7, 0), textcoords="offset points", va="center", fontsize=10, color=INK)
            for name, (x, y) in data[["PC1", "PC2"]].iterrows()
        ]
        ax.axhline(0, color=AXIS, linewidth=0.8)
        ax.axvline(0, color=AXIS, linewidth=0.8)
        ax.set_xlabel(f"PC1 ({var_exp[0] * 100:.1f}% var. explicada)", fontsize=11)
        ax.set_ylabel(f"PC2 ({var_exp[1] * 100:.1f}% var. explicada)", fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.margins(0.3)
    fig.suptitle("Score medio de cada grupo en el plano PC1 vs PC2", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _repel_labels(fig, labels)
    return fig


def plot_outlier_distances(d2: pd.Series, threshold: float, n_components: int) -> Figure:
    """Histograma de la distancia de Mahalanobis al cuadrado, con el umbral chi-cuadrado."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    bins = np.linspace(0, d2.max(), 80)
    ax.hist(d2[d2 <= threshold], bins=bins, color=ACCENT, label="Eventos")
    ax.hist(d2[d2 > threshold], bins=bins, color=HIGHLIGHT, label="Outliers")
    ax.axvline(threshold, color=INK, linestyle="--", linewidth=1)
    ax.text(
        threshold,
        ax.get_ylim()[1] * 0.5,
        f" umbral χ²({n_components}) al 99,9% = {threshold:.1f}",
        fontsize=9,
        color=INK,
    )
    ax.set_yscale("log")
    ax.set_xlabel(f"Distancia de Mahalanobis al cuadrado en las primeras {n_components} componentes")
    ax.set_ylabel("Eventos (escala log)")
    ax.set_title("Distribución de la distancia multivariante de cada evento", fontsize=13, pad=12)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def plot_pairs_by_country(pairs_by_country: pd.DataFrame, title: str) -> Figure:
    """Correlación de cada par de variables (filas) en cada país (columnas)."""
    fig, ax = plt.subplots(figsize=(13, 0.5 * len(pairs_by_country) + 2.5))
    _heatmap(
        pairs_by_country,
        ax,
        annot=True,
        fmt=".2f",
        annot_kws={"fontsize": 8},
        cmap=DIVERGING_CMAP,
        vmin=-1,
        vmax=1,
        center=0,
        cbar_kws={"label": "Correlación de Pearson", "shrink": 0.8},
    )
    ax.set_title(title, fontsize=13, pad=12)
    fig.tight_layout()
    return fig
