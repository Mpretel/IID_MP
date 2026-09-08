# Clase 01 — Complejidad en señales EEG de sueño

**Dataset:** [Sleep-EDF Expanded (PhysioNet)](https://physionet.org/content/sleep-edfx/) — Kemp et al. 2000.

Se mide cómo cambia la complejidad de la señal EEG entre etapas de sueño
(W, N1, N2, N3, REM), usando `mne` para descarga y preprocesamiento y `antropy`
para las métricas de entropía / dimensión fractal.

## Estructura

```
IID_01.ipynb   # notebook orquestador
src/
  config.py        # rutas y constantes (canal, duración, mapping de etapas)
  data.py          # descarga del dataset Sleep-EDF (PhysioNet)
  preprocessing.py # carga de la señal y segmentación en épocas
  complexity.py    # métricas de complejidad / entropía por época
data/
  raw/         # datos crudos descargados (ignorado por git)
  processed/   # salidas: CSV de métricas (ignorado por git)
```

## Uso

```bash
pip install -r ../../requirements.txt
jupyter notebook IID_01.ipynb
```
