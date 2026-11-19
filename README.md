# Análisis de redes temático y colaborativo de la revista *Chilean Journal of Statistics* (2010–2025)

Código y datos del trabajo de grado de Roberto Schaefer para optar al título de Licenciado en Estadística (Universidad de Los Andes, Escuela de Estadística, Mérida, Venezuela).

El estudio analiza los 183 artículos publicados por la *Chilean Journal of Statistics* entre el Vol. 1, N.º 1 (2010) y el Vol. 16, N.º 2 (2025). El repositorio permite reproducir, a partir de los datos incluidos, todas las tablas y figuras de los resultados de la tesis:

1. **Base de datos** (Sección 4.1, Anexo A): metadatos extraídos de los PDF por OCR en dos pasadas y validados campo por campo.
2. **Tendencias temáticas** (Sección 4.2): evolución anual de las palabras clave.
3. **Redes de colaboración** (Sección 4.3, Anexo D): coautoría entre autores, universidades y países.
4. **Estructura temática** (Sección 4.4, Anexo C): agrupamiento de los artículos con TF-IDF, LSA y K-means, y su estabilidad.

## Tesis

- [Versión final de la tesis (PDF)](tesis/Tesis_Roberto_Schaefer_version_final.pdf)
- [Presentación de la defensa, actualizada (PDF)](tesis/Presentacion_defensa_version_final.pdf)

Las figuras de la tesis están en [`results/figures/`](results/figures/), en PDF vectorial, y se regeneran con los guiones indicados en la [correspondencia con la tesis](#correspondencia-con-la-tesis).

## Resultados principales

- **Extracción:** con las dos pasadas del OCR, todos los campos concuerdan con la base de referencia en al menos el 99,1 % de los casos. La segunda pasada, dirigida a los superíndices, elevó la correcta asignación de la afiliación de cada autor del 86,1 % al 99,5 %.
- **Palabras clave:** 697 palabras clave distintas en 181 artículos; el 88 % aparece una sola vez. Ninguna tendencia individual es significativa después de la corrección por comparaciones múltiples.
- **Redes:** 377 autores, 176 instituciones y 39 países. Gauss M. Cordeiro, Josmar Mazucheli y Francisco Louzada son los ejes de la red de autores; la UFPE, la USP y la PUC de Chile, de la de universidades. Brasil es el nodo central y Chile actúa como puente. El 73 % de los artículos se produjo dentro de un solo país.
- **Líneas temáticas:** siete grupos. Cuatro de ellos (inferencia paramétrica por máxima verosimilitud, modelos bayesianos y mixtos, bondad de ajuste y distribuciones simétricas) reúnen el 81,4 % de los artículos; estadística espacial, muestreo y control de procesos completan el perfil. Ningún grupo muestra una tendencia temporal significativa.

## Estructura

```
src/chjs/          módulos del análisis (se importan desde los guiones y los cuadernos)
  descarga.py        descarga de los PDF desde el sitio de la revista
  ocr.py             primera pasada de OCR (Tesseract, 400 ppp, inglés, español y portugués)
  superindices.py    segunda pasada sobre los superíndices de la línea de autores
  extraccion.py      título, resumen, palabras clave, autores y afiliaciones a partir del texto
  validacion.py      emparejamiento con la base de referencia y concordancia por campo
  normalizacion.py   limpieza de texto, países e instituciones
  instituciones.py   tabla de nombres canónicos de instituciones
  autores.py         unificación de nombres de autores
  correcciones.py    correcciones verificadas y construcción de la base final
  palabras_clave.py  unificación de variantes, indicadores anuales, modelo binomial y selección
  redes.py           construcción de las redes, Louvain y actores centrales
  corpus.py          limpieza del texto, TF-IDF y LSA
  agrupamiento.py    K-means, selección de k, bootstrap, co-asociación, PAC, Ward, DBSCAN y tendencias
  figuras.py         estilo común de las figuras
  cuadernos.py       utilidades para los cuadernos
  rutas.py           rutas del repositorio
scripts/           guiones que generan los resultados y las figuras (ver la tabla de correspondencia)
notebooks/         cinco cuadernos que recorren el análisis en orden, ya ejecutados
tesis/             versión final de la tesis y presentación de la defensa (PDF)
data/
  raw/               PDF de los artículos (no incluidos; ver data/raw/README.md)
  interim/           texto OCR, superíndices y base de referencia
  processed/         base final, corpus textual y modelo de agrupamiento de 177 artículos
results/
  validacion/        concordancia del OCR, discrepancias y cambios aplicados a la base
  palabras_clave/    indicadores, pruebas de tendencia y selección
  redes/             grafos, comunidades y actores centrales
  agrupamiento/      selección de k, partición, estabilidad, sensibilidad, tendencias y cruces
  figures/           figuras de la tesis en PDF
docs/
  metodologia.md            procedimiento y parámetros de cada etapa
  diccionario_de_datos.md   contenido de cada archivo de datos y resultados
  registro_de_decisiones.md decisiones metodológicas y de datos, con su motivo
```

## Cómo reproducir

Se usó Python 3.10. Las versiones de `requirements.txt` son las de los resultados de la tesis; K-means, LSA y Louvain pueden dar particiones algo distintas con otras versiones.

```bash
python -m venv venv
venv\Scripts\activate          # en Linux o macOS: source venv/bin/activate
pip install -r requirements.txt
```

Los cuadernos de `notebooks/` recorren el análisis en orden y muestran sus resultados. Para regenerarlos desde cero:

```bash
python scripts/construir_cuadernos.py --ejecutar
```

Los guiones también pueden ejecutarse por separado, en este orden:

| Paso | Guion | Tiempo aprox. |
|---|---|---|
| Concordancia del OCR (Tabla 4.3) | `probar_extraccion.py`, `listar_discrepancias.py` | 1 min |
| Base final | `construir_base_final.py` | segundos |
| Palabras clave | `analisis_palabras_clave.py` | segundos |
| Redes | `resumen_redes.py` | segundos |
| Selección de k y estabilidad | `estabilidad_k7.py` | 15 a 30 min |
| Partición final, tendencias y cruces | `particion_final.py` | 1 min |
| Sensibilidad con 183 artículos | `sensibilidad_183.py` | 1 min |
| Figuras | `figuras_palabras_clave.py`, `figuras_redes.py`, `figuras_agrupamiento.py`, `figuras_corpus.py` | 1 min |

Las figuras se guardan en `results/figures/`. Para escribirlas en otra carpeta, por ejemplo la del documento LaTeX, se define la variable de entorno `CHJS_FIGURAS`.

La descarga de los PDF, el OCR (`chjs.ocr`, `scripts/ocr_superindices.py`) y la muestra de referencia (`scripts/muestra_referencia.py`) necesitan los PDF en `data/raw/`, Tesseract 5 con los modelos `eng`, `spa` y `por`, y Poppler. Sus resultados ya están en `data/interim/`, de modo que el resto del análisis no los requiere.

## Correspondencia con la tesis

| Tesis | Guion | Resultado |
|---|---|---|
| Tabla 4.1 | cuaderno 01 | `data/processed/base_final.json` |
| Tabla 4.3 | `probar_extraccion.py` | `results/validacion/concordancia_resumen.json` |
| Tabla 4.5, Figuras 4.2 y 4.3 | `analisis_palabras_clave.py`, `figuras_palabras_clave.py` | `results/palabras_clave/` |
| Tabla B.1 | cuaderno 02 | variantes en `src/chjs/palabras_clave.py` |
| Tablas 4.6 a 4.8, Figuras 4.4 a 4.7 | `resumen_redes.py`, `figuras_redes.py` | `results/redes/` |
| Figura 4.8 | `estabilidad_k7.py`, `figuras_agrupamiento.py` | `results/agrupamiento/seleccion_k.csv` |
| Tabla 4.9, Figura 4.9 | `particion_final.py`, cuaderno 04 | `results/agrupamiento/particion_183.csv`, `tamanos_grupos.csv` |
| Tabla 4.10, Figura 4.10 | `estabilidad_k7.py` | `results/agrupamiento/estabilidad_grupos.csv`, `bootstrap.csv`, `coasociacion.npy` |
| Tabla 4.11, Figura 4.11 | `particion_final.py` | `results/agrupamiento/tendencias_grupos.csv`, `conteos_grupo_anio.csv` |
| Tabla 4.12 | `particion_final.py` | `results/agrupamiento/grupo_por_pais.csv`, `grupo_por_universidad.csv` |
| Anexo B (Figuras B.1 a B.3) | `figuras_corpus.py` | `results/agrupamiento/diagnostico_corpus.json` |
| Anexo C (Tablas C.1 y C.2) | `estabilidad_k7.py` | `results/agrupamiento/dbscan.csv`, `pac.csv` |
| Anexo C (Tabla C.3) | `sensibilidad_183.py` | `results/agrupamiento/sensibilidad_contingencia.csv` |
| Anexo D (Figuras D.1 a D.3) | `figuras_redes.py` | `results/figures/fig_anx_*.pdf` |

## Notas metodológicas

- **Número de grupos.** Ningún índice interno señala un número natural de grupos: Calinski-Harabasz favorece k = 3, Silhouette y Davies-Bouldin mejoran hasta k = 15, y la proporción de pares ambiguos (PAC) disminuye de forma continua. Por eso k se eligió con tres criterios definidos antes de interpretar los grupos: parsimonia, interpretabilidad disciplinar y validación semántica, verificados con las particiones vecinas de k = 6 y k = 8 (Sección 3.7.2). La Silhouette de la partición de k = 7 (0,025) es baja, pero casi tres veces la de los mismos datos con las dimensiones permutadas al azar (0,009). Las pruebas de estabilidad muestran un núcleo con fronteras móviles y líneas aplicadas reconocibles (Sección 4.4 y Anexo C).
- **Modelo de 177 artículos.** El modelo de agrupamiento se ajustó con los 177 artículos de la primera etapa. Los seis incorporados después (Yang et al., 2010, y el Vol. 16, N.º 2) se asignan al centroide más cercano. Repetir el procedimiento con los 183 artículos da una partición con ARI de 0,45 frente a la presentada, que conserva la mayoría de las líneas (`sensibilidad_183.py`).
- **Texto del corpus.** El texto limpio de `data/processed/` se conserva tal como se generó, porque la lista de términos excluidos depende de los nombres de la base, que se corrigieron después. Regenerarlo desde la base final da el mismo texto en 156 de los 183 artículos y diferencias de pocos términos en el resto.
- **Louvain.** El resultado de `python-louvain` depende del orden en que se agregan los nodos y las aristas, además de la semilla. `chjs.redes` construye las redes siempre en el mismo orden, el de los artículos en la base.

El detalle de cada decisión está en `docs/registro_de_decisiones.md`.

## Datos no incluidos

Los PDF de los artículos no se incluyen, porque son publicaciones de la revista. Se descargan desde su sitio (<https://soche.cl/chjs/issues.html>) con `chjs.descarga`. Los archivos de `data/` contienen solo los metadatos (títulos, resúmenes, palabras clave, autores y afiliaciones) y el texto OCR de las primeras páginas de cada artículo, hasta sus palabras clave.

## Cita

> Schaefer, R. (2026). *Análisis de redes temático y colaborativo de la revista Chilean Journal of Statistics (2010–2025)* [Trabajo de grado, Universidad de Los Andes]. https://github.com/roscha10/chjs-bibliometric-analysis

## Licencia

El código se distribuye bajo licencia MIT (ver `LICENSE`). Los metadatos de `data/` se comparten con fines de investigación y reproducibilidad; los derechos sobre los artículos pertenecen a la revista y a sus autores.
