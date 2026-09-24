# IID_MP
Repositorio de la materia Introducción a la ingeniería de datos (ITBA).

El trabajo se organiza en `clases/` (una carpeta por clase) y `TP/` (una
carpeta por trabajo práctico). Cada subcarpeta es autocontenida (su
notebook, su código en `src/`, sus datos en `data/`) y no comparte datasets
con las demás.

## Estructura

```
clases/
  clase_01/          # Análisis de complejidad en EEG de sueño (Sleep-EDF)
    notebooks/
      IID_01.ipynb   # notebook orquestador
    src/             # pipeline reutilizable de la clase
    data/            # datos crudos y procesados (ignorados por git)
    README.md
TP/
  tp1/                # Métricas diarias de eventos globales (GDELT 2.0)
    notebooks/
      TP1.ipynb      # notebook orquestador
    src/             # pipeline reutilizable del TP
    data/            # datos crudos y procesados (ignorados por git)
    README.md
  tp2/                # Modelado OLTP y dimensional de noticias (GDELT/CAMEO)
    TP2.drawio       # diagramas ER y estrella (draw.io, XML)
    notebooks/
      TP2_informe.ipynb  # informe; implementa la tabla puente en DuckDB
    README.md
requirements.txt     # dependencias comunes a todas las clases y TPs
```

## Uso

```bash
pip install -r requirements.txt
jupyter notebook clases/clase_01/notebooks/IID_01.ipynb
jupyter notebook TP/tp1/notebooks/TP1.ipynb
jupyter notebook TP/tp2/notebooks/TP2_informe.ipynb
```

Cada clase y cada TP tiene su propio `README.md` con el detalle del análisis.
