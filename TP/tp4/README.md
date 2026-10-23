# TP4 — Detección de eventos atípicos en GDELT 2.0

**Caso:** último TP de la serie sobre GDELT 2.0. Después de procesar el flujo
de datos (TP1), diseñar el almacén (TP2) y analizar el comportamiento
multivariante del ecosistema de noticias (TP3), la tarea es encontrar eventos
"raros" que valga la pena investigar.

**Uso de IA:** el notebook se construye guiando a Claude Code (Claude Opus
5.5) con prompts. Cada celda está precedida por el prompt que la generó, como
guía para reproducir el resultado (*Human-in-the-loop*).

**Actividades:**

1. Ingesta: eventos de 15 minutos de los últimos 7 días en una tabla
   desnormalizada (*One Big Table*), guardada en parquet.
2. Limpieza:
   - nulos y ceros: identificarlos y descartarlos o imputarlos con criterio;
   - reducción de cardinalidad: categorías con frecuencia < 5% en `OTHER`;
   - variables indicadoras (dummy);
   - ACP sobre las variables escaladas y cantidad mínima de componentes;
   - detección de eventos atípicos multivariantes, exportados en una tabla
     aparte.

## Estructura

```
notebooks/
  TP4.ipynb       # notebook orquestador, con el prompt antes de cada celda
src/
  config.py       # rutas, URLs de GDELT, ventana de 7 días y esquema de los eventos
  ingestion.py    # lista maestra en streaming y descarga en paralelo con caché
  obt.py          # One Big Table: eventos + descripciones de sus códigos
  quality.py      # perfil de calidad: nulos, ceros y strings vacíos por columna
  cleaning.py     # limpieza: ceros que son datos faltantes
  features.py     # selección de variables, cardinalidad, indicadoras y matriz de datos
  pca.py          # ACP estandarizado y criterios para elegir la cantidad de componentes
  outliers.py     # atípicos: distancia al centro con Tukey fences e Isolation Forest
  plots.py        # gráficos del TP
data/
  raw/            # ZIP de eventos y tablas de códigos de GDELT (ignorado por git)
  processed/      # OBT, matriz de datos, atípicos (parquet y CSV) y figuras (ignorado por git)
```

## Uso

```bash
pip install -r ../../requirements.txt
jupyter notebook notebooks/TP4.ipynb
```

## Recursos

- [Lista maestra de archivos (actualizada cada 15 min)](https://data.gdeltproject.org/gdeltv2/masterfilelist.txt)
- [Codebook de eventos GDELT 2.0](https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)
- [Manual de campos CAMEO](https://gdeltproject.org/data/documentation/CAMEO.Manual.1.1b3.pdf)
