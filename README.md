# Análisis de Redes Temático y Colaborativo de la Chilean Journal of Statistics (2010–2025)

Código y datos de soporte del trabajo de grado **"Análisis de redes Temático y Colaborativo de la Revista Chilean Journal of Statistics (2010–2024)"**, presentado por Roberto Schaefer para optar al título de Licenciado en Estadística — Universidad de Los Andes, Escuela de Estadística (Mérida, Venezuela).

Este repositorio contiene el pipeline completo y reproducible utilizado para:

1. **Extraer metadatos** de los 177 artículos publicados en la ChJS (2010–2025) a partir de PDFs escaneados, mediante OCR y heurísticas de procesamiento de lenguaje.
2. **Analizar tendencias temáticas** a partir de palabras clave normalizadas (bubble chart, heatmap de evolución).
3. **Modelar redes de colaboración científica** entre autores, instituciones y países mediante teoría de grafos.
4. **Clusterizar temáticamente** los artículos mediante TF-IDF → LSA → K-means, con validación estadística (Silhouette, Calinski-Harabasz, Davies-Bouldin, bootstrap re-clustering).

## Estructura del repositorio

```
notebooks/
├── 01_extraccion_metadatos.ipynb        # Objetivo transversal: OCR + extracción de metadatos (Anexo A de la tesis)
├── 02_tendencias_tematicas.ipynb        # Objetivo Específico 1 — Sección 4.2
├── 03_redes_colaboracion.ipynb          # Objetivo Específico 2 — Sección 4.3
└── 04_clusterizacion_tematica.ipynb     # Objetivo Específico 3 — Sección 4.4

data/
└── reorganized_data_c_CLEAN_NORMALIZADO.json   # Metadatos normalizados (177 artículos)

results/
├── figures/    # Figuras clave referenciadas en la tesis
└── tables/     # Tablas de resultados en formato CSV
```

## Nota metodológica importante: selección de k en la clusterización

La solución de clustering reportada en la versión final de la tesis usa **k = 7** (no k = 14, valor explorado en una fase intermedia del análisis). La elección de k = 7 se sustenta en la convergencia simultánea de tres criterios de validación interna (Silhouette, Calinski-Harabasz y Davies-Bouldin) evaluados sobre el rango k ∈ [3, 15]; ver Sección 4.4.2 de la tesis y el notebook `04_clusterizacion_tematica.ipynb` para el detalle completo. Las soluciones de mayor granularidad (k ∈ [12, 15]) fueron exploradas como análisis de sensibilidad y reproducen la misma jerarquía temática dominante con subdivisiones adicionales de baja estabilidad.

## Cómo ejecutar

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/
```

Los notebooks están numerados en el orden lógico del pipeline, pero cada uno puede ejecutarse de forma independiente a partir de los datos ya provistos en `data/` y `results/`.

## Datos no incluidos

Los PDFs originales de los artículos de la Chilean Journal of Statistics **no se incluyen** en este repositorio por razones de derechos de autor de la revista y sus autores. Pueden descargarse directamente desde [soche.cl/chjs](https://soche.cl/chjs/index.html). El JSON de metadatos en `data/` contiene únicamente información extraída (títulos, resúmenes, palabras clave, afiliaciones), no el contenido íntegro de los artículos.

## Cita

Si utiliza este código o pipeline, por favor cite el trabajo de grado original:

> Schaefer, R. (2026). *Análisis de redes Temático y Colaborativo de la Revista Chilean Journal of Statistics (2010–2024)*. Trabajo de grado, Universidad de Los Andes, Escuela de Estadística.

## Licencia

Este proyecto se distribuye bajo licencia MIT (ver `LICENSE`). Los datos de metadatos (`data/`) se distribuyen bajo los mismos términos, respetando los derechos de autor de los artículos originales de la ChJS.
