"""Gráficos del análisis multivariante GDELT (matplotlib/seaborn)."""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def plot_correlation_heatmap(correlaciones, titulo='Matriz de correlación', figsize=(12, 10)):
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(correlaciones, cmap='coolwarm', center=0, vmin=-1, vmax=1,
                ax=ax, square=False, cbar_kws={'label': 'Correlación de Pearson'})
    ax.set_title(titulo)
    fig.tight_layout()
    return fig


def plot_distance_heatmap(distancias, titulo='Distancias entre países', figsize=(10, 8)):
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(distancias, cmap='viridis', ax=ax)
    ax.set_title(titulo)
    fig.tight_layout()
    return fig


def plot_scree(eigenvalues, var_exp):
    """Autovalores y varianza explicada acumulada (var_exp como proporción)."""
    autovalores = np.asarray(eigenvalues)
    proporciones = np.asarray(var_exp)
    if len(autovalores) != len(proporciones):
        raise ValueError('eigenvalues y var_exp deben tener igual longitud')
    x = np.arange(1, len(autovalores) + 1)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x, autovalores, alpha=0.7, label='Autovalor')
    ax.axhline(1, linestyle='--', color='gray', label='Kaiser: autovalor = 1')
    ax.set_xlabel('Componente principal')
    ax.set_ylabel('Autovalor')
    ax.set_xticks(x)
    ax2 = ax.twinx()
    ax2.plot(x, 100 * np.cumsum(proporciones), marker='o', color='tab:red',
             label='Varianza acumulada')
    ax2.set_ylabel('Varianza acumulada (%)')
    ax2.set_ylim(0, 105)
    ax.set_title('Scree plot y varianza acumulada')
    fig.tight_layout()
    return fig


def _etiquetas_grupos(scores, grupos):
    """Alinea las etiquetas con los índices de los scores del PCA."""
    import pandas as pd
    if grupos is None:
        return None
    if not isinstance(grupos, pd.Series):
        grupos = pd.Series(grupos, index=scores.index)
    if not grupos.index.is_unique:
        raise ValueError("El índice de grupos debe ser único")
    return grupos.reindex(scores.index).fillna("UNKNOWN").astype(str)


def _etiquetas_ejes(ax, var_exp):
    p1 = f" ({100 * var_exp[0]:.1f}%)" if var_exp is not None else ""
    p2 = f" ({100 * var_exp[1]:.1f}%)" if var_exp is not None else ""
    ax.set_xlabel("PC1" + p1)
    ax.set_ylabel("PC2" + p2)
    ax.axhline(0, color="gray", lw=0.7)
    ax.axvline(0, color="gray", lw=0.7)


def plot_biplot(scores, loadings, grupos=None, var_exp=None,
                max_flechas=8, figsize=(12, 8), alpha=0.22,
                max_puntos=3000, random_state=42, max_grupos=8):
    """Biplot PC1-PC2 con submuestreo SOLO para visualización.

    `scores` y `loadings` provienen del PCA completo. `max_puntos=None`
    permite mostrar todos los eventos. Las flechas se reescalan solo
    visualmente, y representan la dirección de los loadings.
    """
    import pandas as pd
    requeridas = {"PC1", "PC2"}
    if not requeridas.issubset(scores.columns) or not requeridas.issubset(loadings.columns):
        raise ValueError("scores y loadings necesitan columnas PC1 y PC2")
    if scores.empty or loadings.empty:
        raise ValueError("scores y loadings no pueden estar vacíos")
    if max_puntos is not None and max_puntos <= 0:
        raise ValueError("max_puntos debe ser positivo o None")

    etiquetas = _etiquetas_grupos(scores, grupos)
    puntos = scores if max_puntos is None or len(scores) <= max_puntos else scores.sample(
        n=max_puntos, random_state=random_state
    )
    fig, ax = plt.subplots(figsize=figsize)
    if etiquetas is None:
        ax.scatter(puntos.PC1, puntos.PC2, s=8, alpha=alpha, rasterized=True)
    else:
        # Determinar grupos principales con la población completa, no la muestra.
        principales = etiquetas.value_counts().head(max_grupos).index
        etiquetas_muestra = etiquetas.reindex(puntos.index).where(
            etiquetas.reindex(puntos.index).isin(principales), "OTHER"
        )
        for nombre in etiquetas_muestra.unique():
            sel = etiquetas_muestra == nombre
            ax.scatter(puntos.loc[sel, "PC1"], puntos.loc[sel, "PC2"],
                       s=9, alpha=alpha, label=nombre, rasterized=True)
        ax.legend(title="País del evento", loc="upper left", bbox_to_anchor=(1.02, 1),
                  fontsize=8, markerscale=2)

    vectores = loadings[["PC1", "PC2"]].copy()
    vectores["magnitud"] = np.hypot(vectores.PC1, vectores.PC2)
    vectores = vectores.nlargest(max_flechas, "magnitud")
    limite_scores = np.percentile(np.abs(scores[["PC1", "PC2"]].to_numpy()), 95)
    limite_loadings = max(vectores["magnitud"].max(), 1e-12)
    escala = 0.65 * limite_scores / limite_loadings if limite_scores else 1
    for variable, fila in vectores.iterrows():
        x, y = fila.PC1 * escala, fila.PC2 * escala
        ax.annotate("", xy=(x, y), xytext=(0, 0),
                    arrowprops={"arrowstyle": "->", "color": "black", "lw": 1})
        ax.annotate(str(variable), xy=(x, y), xytext=(4, 3),
                    textcoords="offset points", fontsize=8)
    _etiquetas_ejes(ax, var_exp)
    ax.set_title(f"Biplot PCA (muestra de {len(puntos):,} de {len(scores):,} eventos)")
    fig.tight_layout()
    return fig


def plot_centroides_paises(scores, grupos, var_exp=None, min_eventos=100,
                           max_paises=20, figsize=(11, 8),
                           incluir_other=False, mostrar_dispersion=False):
    """Dibuja la media de PC1 y PC2 de cada país.

    Los centroides son medias de los scores del PCA ya ajustado, NO un PCA
    nuevo sobre medias. Excluye grupos con menos de `min_eventos` eventos.
    """
    import pandas as pd
    if not {"PC1", "PC2"}.issubset(scores.columns):
        raise ValueError("scores necesita columnas PC1 y PC2")
    etiquetas = _etiquetas_grupos(scores, grupos)
    if etiquetas is None:
        raise ValueError("grupos es obligatorio")
    datos = scores[["PC1", "PC2"]].copy()
    datos["Pais"] = etiquetas
    if not incluir_other:
        datos = datos[~datos.Pais.isin(["OTHER", "UNKNOWN", "", "<NA>"])]
    estadisticas = datos.groupby("Pais").agg(
        PC1=("PC1", "mean"), PC2=("PC2", "mean"),
        n=("PC1", "size"),
        sd_PC1=("PC1", "std"), sd_PC2=("PC2", "std")
    )
    estadisticas = estadisticas[estadisticas.n >= min_eventos]
    estadisticas = estadisticas.nlargest(max_paises, "n")
    if estadisticas.empty:
        raise ValueError("No hay países con suficientes eventos; reducí min_eventos")

    fig, ax = plt.subplots(figsize=figsize)
    tamanos = 35 + 200 * np.sqrt(estadisticas.n / estadisticas.n.max())
    ax.scatter(estadisticas.PC1, estadisticas.PC2, s=tamanos,
               alpha=0.75, edgecolors="black", linewidths=0.5)
    if mostrar_dispersion:
        ax.errorbar(estadisticas.PC1, estadisticas.PC2,
                    xerr=estadisticas.sd_PC1.fillna(0),
                    yerr=estadisticas.sd_PC2.fillna(0),
                    fmt="none", color="gray", alpha=0.25, zorder=0)
    for pais, fila in estadisticas.iterrows():
        ax.annotate(f"{pais} (n={int(fila.n):,})", (fila.PC1, fila.PC2),
                    xytext=(5, 5), textcoords="offset points", fontsize=9)
    _etiquetas_ejes(ax, var_exp)
    ax.set_title("Centroides por país en el espacio PCA (PC1–PC2)")
    fig.tight_layout()
    return fig


def plot_pc_histograms(scores, grupos=None, var_exp=None, bins=30):
    """Histogramas de las primeras dos componentes."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for i, (ax, componente) in enumerate(zip(axes, ('PC1', 'PC2'))):
        if grupos is None:
            ax.hist(scores[componente], bins=bins, alpha=0.75)
        else:
            etiquetas = grupos.reindex(scores.index).fillna('UNKNOWN').astype(str)
            principales = etiquetas.value_counts().head(8).index
            etiquetas = etiquetas.where(etiquetas.isin(principales), 'OTHER')
            for grupo in etiquetas.unique():
                ax.hist(scores.loc[etiquetas == grupo, componente], bins=bins,
                        alpha=0.4, label=grupo)
            ax.legend(fontsize=8)
        porcentaje = f' ({100 * var_exp[i]:.1f}%)' if var_exp is not None else ''
        ax.set_xlabel(componente + porcentaje)
        ax.set_ylabel('Eventos')
    fig.tight_layout()
    return fig


def save_figure(fig, nombre, carpeta='figures', dpi=160):
    from pathlib import Path
    destino = Path(carpeta)
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / f'{nombre}.png'
    fig.savefig(ruta, dpi=dpi, bbox_inches='tight')
    return ruta
