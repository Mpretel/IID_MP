# TP1 — Eventos globales GDELT 2.0

**Dataset:** [GDELT 2.0](https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/) —
eventos reportados por medios de todo el mundo, publicados cada 15 minutos y
codificados con el esquema [CAMEO](https://gdeltproject.org/data/documentation/CAMEO.Manual.1.1b3.pdf).

Se calculan, para cada día desde el 2 de septiembre de 2026, la cantidad de
eventos registrados y el promedio de artículos/fuentes por evento, accediendo
a los datos de forma incremental (streaming + batches) para no cargar en
memoria más de lo necesario.

## Estructura

```
notebooks/
  TP1.ipynb       # notebook orquestador
src/
  config.py       # rutas, URLs de GDELT y esquema de columnas usado
  master_list.py  # streaming + filtrado de la lista maestra de archivos
  fetch.py        # descarga y parseo de un archivo de eventos de 15 min
  aggregate.py    # acumulador incremental de métricas diarias
  pipeline.py     # orquesta la descarga en paralelo y la agregación
data/
  raw/            # ZIP de eventos descargados, cacheados (ignorado por git)
  processed/      # CSV con las métricas diarias (ignorado por git)
```

## Uso

```bash
pip install -r ../../requirements.txt
jupyter notebook notebooks/TP1.ipynb
```

## Recursos

- [Lista maestra de archivos (actualizada cada 15 min)](https://data.gdeltproject.org/gdeltv2/masterfilelist.txt)
- [Codebook de eventos GDELT 2.0](https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)
- [Manual de campos CAMEO](https://gdeltproject.org/data/documentation/CAMEO.Manual.1.1b3.pdf)
