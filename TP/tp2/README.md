# TP2 — Modelado OLTP y dimensional de noticias (GDELT 2.0 / CAMEO)

**Caso:** un medio internacional de noticias necesita (a) una base operativa
(OLTP) para registrar en tiempo real noticias, fuentes, actores y eventos, y
(b) un almacén de datos (OLAP) para analizar impacto, cobertura y tendencias.
Ambos modelos se basan en los eventos de GDELT 2.0 y la codificación CAMEO,
usados en el TP1.

**Entrega:**

- [`TP2.drawio`](TP2.drawio): diagramas en XML de draw.io. La página 1 tiene
  el modelo OLTP (Entidad-Relación) y la página 2, el modelo dimensional
  (estrella).
- [`notebooks/TP2_informe.ipynb`](notebooks/TP2_informe.ipynb): informe de las
  actividades 1 y 2, con la justificación del diseño.

La actividad 3 (opcional) no está resuelta.

## Estructura

```
TP2.drawio              # diagramas ER y estrella (abrir con https://app.diagrams.net)
notebooks/
  TP2_informe.ipynb     # informe (actividades 1 y 2)
```

## Recursos

- [Lista maestra de archivos (actualizada cada 15 min)](https://data.gdeltproject.org/gdeltv2/masterfilelist.txt)
- [Codebook de eventos GDELT 2.0](https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)
- [Manual de campos CAMEO](https://gdeltproject.org/data/documentation/CAMEO.Manual.1.1b3.pdf)
