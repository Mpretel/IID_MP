# Clase 05 — Detección no supervisada de anomalías en cardiotocografías

**Dataset:** [Cardiotocography](https://archive.ics.uci.edu/dataset/193/cardiotocography) (UCI) — Ayres de Campos et al. 2000.

2126 cardiotocogramas (CTG) fetales con 21 variables medidas automáticamente,
clasificados por tres obstetras según el estado fetal (`NSP`): normal,
sospechoso o patológico. Se buscan métodos no supervisados que detecten los CTG
no normales (`NSP` > 1, el 22% de los registros) mejor que los vistos en clase,
y se comparan todos en una misma tabla (TP, FP, FN, precisión, recall y
ROC-AUC).

El mejor método es una distancia al centro **direccional**: sobre 8 variables
clínicas en escala log + z-score, sólo cuenta los desvíos en la dirección de
riesgo. Llega a un ROC-AUC de 0,91 y, marcando el 5% de los registros, a 96 TP,
11 FP y 375 FN. El mejor método de clase (Isolation Forest) da 0,73 y 68 TP,
39 FP y 403 FN.

## Estructura

```
notebooks/
  IID_05.ipynb                     # notebook orquestador: tabla comparativa de métodos
  IID_05_distancia_direccional.ipynb  # el mejor método, paso a paso y con gráficos
  Cardiotocography outliers.ipynb  # notebook de referencia de la clase
src/
  config.py      # rutas, variables, dirección de riesgo y umbrales
  data.py        # carga del dataset y escalados (RobustScaler, log + z-score)
  detectors.py   # puntajes de anomalía: métodos de clase, propuestos y de PyOD
  evaluation.py  # matriz de confusión, precisión, recall y ROC-AUC
  plots.py       # gráficos de la distancia direccional
data/
  raw/         # CSV del dataset descargado de UCI (ignorado por git)
  processed/   # tabla comparativa en CSV y figuras PNG (ignorado por git)
```

## Uso

```bash
pip install -r ../../requirements.txt
jupyter notebook notebooks/IID_05.ipynb
```
