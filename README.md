# IID_MP
Repositorio de la materia Introducción a la ingeniería de datos (ITBA)

## Estructura

```
data/
  raw/         # datos crudos descargados
  processed/   # salidas (CSV de métricas)
notebooks/
  IID_01.ipynb # análisis de complejidad en EEG de sueño (orquestador)
src/
  config.py        # rutas y constantes (canal, duración, mapping de etapas)
  data.py          # descarga del dataset Sleep-EDF (PhysioNet)
  preprocessing.py # carga de la señal y segmentación en épocas
  complexity.py    # métricas de complejidad / entropía por época
```

## Uso

```bash
pip install -r requirements.txt
jupyter notebook notebooks/IID_01.ipynb
```
