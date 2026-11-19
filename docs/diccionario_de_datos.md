# Diccionario de datos

Contenido de cada archivo de `data/` y `results/`. Los textos están en UTF-8; algunos CSV llevan marca de orden de bytes (BOM) para que Excel muestre bien los acentos.

## data/interim

### ocr_texto.json

Primera pasada de OCR. Es una lista con un registro por PDF: 197 documentos, que incluyen los 183 artículos y las presentaciones y editoriales de cada número.

| Campo | Tipo | Descripción |
|---|---|---|
| `archivo` | texto | nombre del PDF (con la carpeta original como prefijo) |
| `paginas` | entero | páginas leídas, hasta la que contiene las palabras clave |
| `texto` | texto | texto OCR de esas páginas |

### superindices.json

Segunda pasada sobre los superíndices de la línea de autores. Es un diccionario cuya clave es el `archivo` y cuyo valor tiene estos campos:

| Campo | Tipo | Descripción |
|---|---|---|
| `pagina` | entero | página de la línea de autores |
| `lineas` | lista de textos | líneas de autores encontradas en el texto OCR |
| `grupos` | lista | un elemento por palabra con superíndice: `palabra` (texto OCR), `leido` (lectura ampliada) e `indices` (índices de afiliación) |

### base_referencia.json

Base de la primera etapa del estudio, construida con la capa de texto de los PDF y una revisión manual. Tiene la misma estructura que `base_final.json`, sin las correcciones de la validación OCR. Se conserva sin cambios como punto de partida de `scripts/construir_base_final.py`.

## data/processed

### base_final.json

Base de datos del estudio: 183 artículos, con los metadatos corregidos y normalizados. Es una lista con un registro por artículo.

| Campo | Tipo | Descripción |
|---|---|---|
| `Volumen` | entero | volumen (1 a 16) |
| `numero` | entero | número dentro del volumen (1 o 2) |
| `fecha` | texto | mes y año de publicación, como figura en el PDF (p. ej., "april, 2010" o "September 2010") |
| `Titulo` | texto o nulo | sección o número especial en que se publicó el artículo |
| `Articulo` | texto | título del artículo |
| `abstract` | texto | resumen |
| `keywords` | texto o nulo | palabras clave, separadas por `·`, `;` o `,` (nulo en dos artículos) |
| `Autores` | lista | un elemento por autor y afiliación (un autor con dos afiliaciones aparece dos veces) |

Cada elemento de `Autores`:

| Campo | Descripción |
|---|---|
| `nombre` | nombre unificado del autor |
| `universidad` | institución normalizada (nombre canónico) |
| `universidad_raw` | afiliación tal como figura en el artículo |
| `pais` | país de la afiliación, en inglés |
| `_match_score`, `_match_how` | cómo se asignó la institución canónica: por coincidencia con la tabla (`universidad:...`) o manualmente (`manual`) |

### corpus_177.csv y corpus_183.csv

Texto de cada artículo para el agrupamiento temático. `corpus_177.csv` contiene los 177 artículos con los que se ajustó el modelo; `corpus_183.csv`, los 183. En `corpus_183.csv`, los 177 originales conservan su orden, Yang et al. (2010) ocupa la posición 5 y los cinco artículos de 2025 van al final.

| Columna | Descripción |
|---|---|
| `doc_id` | identificador correlativo |
| `year` | año de publicación |
| `title`, `abstract`, `keywords` | campos originales |
| `text_raw` | unión del título, el resumen y las palabras clave |
| `text_clean` | texto limpio: minúsculas, sin acentos, sin palabras vacías ni nombres, en raíces de Snowball |
| `n_tokens` | número de términos de `text_clean` |

### lsa_177.npz

Matriz `Z` (177 × 176): representación LSA de los 177 artículos del modelo.

### etiquetas_k7_177.csv

Partición original de siete grupos, la presentada en la defensa. Columnas: `doc_id`, `year`, `title` y `cluster`, este último de 0 a 6; el grupo de la tesis es `cluster + 1`.

## results/validacion

| Archivo | Contenido |
|---|---|
| `concordancia.csv` | Una fila por artículo con la concordancia de cada campo (Tabla 4.3). Los campos lógicos o proporciones son `titulo`, `resumen`, `palabras_clave`, `n_autores`, `autores`, `afiliacion_autor`, `pais_autor`, `afiliaciones_articulo` y `paises_articulo`. `emparejamiento` es la similitud del emparejamiento por título. |
| `concordancia_resumen.json` | Porcentaje de concordancia por campo, con la primera pasada y con las dos pasadas. |
| `discrepancias.csv` | Una fila por discrepancia: `archivo`, `campo`, `autor`, valor en la `base` y en el `ocr`. La columna `decision` queda vacía; las decisiones de la revisión están en `chjs.correcciones` y en `cambios_base_final.csv`. |
| `cambios_base_final.csv` | Cambios aplicados a la base de referencia: `articulo`, `campo`, `antes` y `despues`. |

## results/palabras_clave

| Archivo | Contenido |
|---|---|
| `metricas.csv` | Una fila por palabra clave (`keyword_std`). Columnas: `frecuencia_total` (suma de proporciones anuales), `persistencia` (años con presencia), `articulos`, `anio_medio`, `anio_maximo`, `valor_maximo`, `pendiente` (proporción por año) y, si está en tres años o más, `pendiente_logit`, `p`, `dispersion_pearson` y `p_bh` del modelo binomial. |
| `tendencias_glm.csv` | Resultados del modelo binomial para las 26 palabras presentes en tres años o más. |
| `top25.csv` | Las 25 palabras de mayor relevancia, con su `puntaje`. |
| `proporciones_top25.csv` | Proporción anual (2010 a 2025) de esas 25 palabras (Figura 4.3). |
| `resumen.json` | Cifras del texto: palabras distintas antes y después de unificar, artículos, asignaciones, palabras que aparecen una sola vez, resultados del modelo y validaciones de la selección. |

## results/redes

| Archivo | Contenido |
|---|---|
| `autores.graphml`, `universidades.graphml`, `paises.graphml` | Grafos con el peso de cada arista (`weight`, artículos compartidos). En universidades, cada nodo es "Institución (País)". |
| `louvain_<red>.json` | Comunidad de Louvain de cada nodo. |
| `centrales_<red>.csv` | Actores entre los diez primeros por grado o por intermediación: `actor`, `grado`, `pos_grado`, `intermediacion` (normalizada) y `pos_intermediacion` (Tablas 4.7 y 4.8). |
| `resumen_redes.json` | Por red: artículos, nodos, aristas, densidad, grado medio, transitividad, componentes, tamaño de la componente gigante, comunidades, modularidad, nodos con intermediación nula, tamaños de las comunidades del núcleo y ego-redes de los actores destacados (Tabla 4.6). |

## results/agrupamiento

| Archivo | Contenido |
|---|---|
| `seleccion_k.csv` | Por k (3 a 15): media y desviación estándar de Silhouette, Calinski-Harabasz y Davies-Bouldin sobre 25 semillas, y Silhouette media y máxima de la referencia al azar (Figura 4.8). |
| `bootstrap.csv` | ARI de cada una de las 200 réplicas. |
| `estabilidad_grupos.csv` | Por grupo: `n` (de los 177), `jaccard` medio del bootstrap y `coasociacion` interna (Tabla 4.10). |
| `coasociacion.npy` | Matriz 177 × 177 de co-asociación (Figura 4.10). |
| `pac.csv` | PAC por k (Tabla C.2). |
| `dbscan.csv` | Por radio: número de grupos, tamaños, artículos sin grupo y ARI con K-means (Tabla C.1). |
| `kmeans_ward.csv`, `k6_k7.csv`, `k8_k7.csv` | Tablas de contingencia de la partición de k = 7 con Ward y con K-means de k = 6 y k = 8. |
| `resumen_estabilidad.json` | Cifras del texto de la Sección 4.4.3. |
| `particion_183.csv` | Partición final: `doc_id`, `year`, `title`, `grupo` (1 a 7), `nombre_grupo`, `segunda_etapa` (artículo asignado al centroide), `pais` (el más frecuente entre los autores), `n_paises` y `universidad` (la del primer autor). |
| `tamanos_grupos.csv` | Tamaño y porcentaje de cada grupo (Figura 4.9). |
| `conteos_grupo_anio.csv` | Artículos por año (2010 a 2025) y grupo (Figura 4.11). |
| `tendencias_grupos.csv` | Por grupo: `tau` y `p_mk` de Mann-Kendall, pendiente de Sen (`sen`), `p_poisson` y su `dispersion`, `p_cuasipoisson`, `p_binomial_negativa` (si la serie no tiene sobredispersión, igual al de Poisson), `p_proporcion` (Poisson con el total anual como exposición), `r2` de la recta, año y valor máximos, y los valores p corregidos (`_bh`) (Tabla 4.11). |
| `grupo_por_pais.csv`, `grupo_por_universidad.csv` | Artículos por país o institución y grupo, con totales (Tabla 4.12). |
| `resumen_particion.json` | Cifras del texto de las Secciones 4.4.2, 4.4.5 y 4.4.6. |
| `reajuste_183.csv` | Grupo de cada artículo en la partición presentada y en el reajuste con 183 artículos (letras A a G). |
| `sensibilidad_contingencia.csv` | Tabla de contingencia entre ambas particiones (Tabla C.3). |
| `resumen_sensibilidad.json` | ARI, términos, componentes y artículos conservados por grupo. |
| `diagnostico_corpus.json` | Longitud de los documentos y términos más frecuentes (Anexo B). |

## results/figures

Las 16 figuras de los resultados y los anexos, en PDF vectorial, con el nombre del archivo que usa el documento LaTeX: `fig_kw_*` (Sección 4.2), `fig_red_*` y `fig_ego_*` (4.3), `fig_k_seleccion`, `fig_grupos`, `fig_coasociacion` y `fig_series_grupos` (4.4), y `fig_anx_*` (Anexos B y D).
