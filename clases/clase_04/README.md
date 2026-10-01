# Clase 04 — Análisis exploratorio multivariado y PCA del Wine dataset

**Dataset:** [Wine recognition dataset](https://scikit-learn.org/stable/datasets/toy_dataset.html#wine-recognition-dataset) (UCI / scikit-learn) — Forina et al. 1991.

Se analizan 178 vinos de 3 cultivares descritos por 13 variables químicas:
distribución de cada variable por cultivar, medias, covarianzas y
correlaciones, y un análisis de componentes principales (PCA) sobre las
variables estandarizadas. Replica sobre Wine el análisis de Iris visto en
clase, usando `scikit-learn` para el PCA y `seaborn` para los gráficos.

## Estructura

```
notebooks/
  IID_04.ipynb     # notebook orquestador (análisis sobre Wine)
  EDA Iris.ipynb   # notebook de referencia de la clase (Iris)
src/
  config.py        # rutas y constantes (variables, indicadoras, colores)
  data.py          # carga del dataset y codificación indicadora del cultivar
  pca.py           # PCA estandarizado y ranking de variables por F de ANOVA
  plots.py         # gráficos: distribuciones, heatmap, pairplot, scree, biplot
data/
  raw/         # copia cruda del dataset en CSV (ignorado por git)
  processed/   # salidas: scores del PCA y figuras PNG (ignorado por git)
```

## Uso

```bash
pip install -r ../../requirements.txt
jupyter notebook notebooks/IID_04.ipynb
```
