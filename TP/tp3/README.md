# TP3 — Análisis multivariante de eventos GDELT 2.0

**Caso:** el equipo de Investigación & Ciencia de Datos de un medio
internacional de noticias necesita analizar el comportamiento multivariante
del ecosistema global de noticias. Continúa el TP2: se extiende el almacén de
datos con los actores 1 y 2, el tipo de interacción, la región del evento, el
tono y el impacto estimado por la escala de Goldstein.

**Preguntas de investigación:**

1. Perfil multivariante de eventos: vectores de medias.
2. Topología de cobertura mediática: distancias entre perfiles.
3. Estructura de correlación entre las variables de los eventos.
4. Compresión del ecosistema: cantidad de componentes principales e
   interpretación de sus cargas.

**Actividades:**

1. Ingesta: extensión del modelo del TP2, agrupación de categorías con
   frecuencia < 5% en `OTHER`, codificación indicadora (dummy) y matriz de
   datos integrada (continuas + indicadoras).
2. Descripción multivariante: vector de medias global y por país, distancias
   (global vs país y país vs país) y mapas de calor de correlación.
3. ACP sobre las variables escaladas: scree plot, interpretación de loadings
   y biplot PC1 vs PC2 (agrupamientos y outliers multivariantes).

## Estructura

```
notebooks/
  TP3.ipynb       # informe / notebook orquestador
src/
  config.py       # rutas, URLs, muestra, columnas y variables del análisis
  master_list.py  # streaming + filtrado de la lista maestra de archivos
  fetch.py        # descarga y parseo de un archivo de eventos de 15 min
  pipeline.py     # descarga en paralelo de la muestra
  regions.py      # países FIPS de GDELT y su región (Banco Mundial)
  warehouse.py    # almacén SQLite: esquema estrella, carga, JOIN y merge
  features.py     # reducción de cardinalidad, indicadoras y matriz
  multivariate.py # vectores de medias, distancias y correlaciones
  pca.py          # ACP, análisis paralelo de Horn y outliers multivariantes
  plots.py        # gráficos: medias, distancias, correlaciones, scree, biplot
data/
  raw/            # ZIP de eventos y tabla FIPS, cacheados (ignorado por git)
  processed/      # eventos (staging), almacen.sqlite, matriz y figuras (ignorado por git)
```

**Muestra:** una semana completa (28/09 al 04/10/2026), un archivo de 15
minutos por hora (el de hh:00).

## Uso

```bash
pip install -r ../../requirements.txt
jupyter notebook notebooks/TP3.ipynb
```

## Recursos

- [Lista maestra de archivos (actualizada cada 15 min)](https://data.gdeltproject.org/gdeltv2/masterfilelist.txt)
- [Codebook de eventos GDELT 2.0](https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)
- [Manual de campos CAMEO](https://gdeltproject.org/data/documentation/CAMEO.Manual.1.1b3.pdf)
