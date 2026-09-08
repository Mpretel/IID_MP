# IID_MP
Repositorio de la materia Introducción a la ingeniería de datos (ITBA).

El trabajo se organiza por clase. Cada carpeta en `clases/` es autocontenida
(su notebook, su código en `src/`, sus datos en `data/`) y no comparte datasets
con las demás.

## Estructura

```
clases/
  clase_01/          # Análisis de complejidad en EEG de sueño (Sleep-EDF)
    IID_01.ipynb     # notebook orquestador
    src/             # pipeline reutilizable de la clase
    data/            # datos crudos y procesados (ignorados por git)
    README.md
requirements.txt     # dependencias comunes a todas las clases
```

## Uso

```bash
pip install -r requirements.txt
jupyter notebook clases/clase_01/IID_01.ipynb
```

Cada clase tiene su propio `README.md` con el detalle del análisis.
