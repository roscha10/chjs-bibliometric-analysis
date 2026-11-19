# Metodología

Procedimiento y parámetros de cada etapa del análisis, en el orden en que se ejecutan. Las secciones de la tesis que se citan corresponden al Capítulo 3 (método) y al Capítulo 4 (resultados). El motivo de cada decisión está en `registro_de_decisiones.md`.

## 1. Población

Censo de los artículos publicados por la *Chilean Journal of Statistics* entre el Vol. 1, N.º 1 (abril de 2010) y el Vol. 16, N.º 2 (diciembre de 2025): 183 artículos en 32 números. Se excluyen las presentaciones de cada número y los editoriales. Por tipo, hay 174 artículos de investigación, 3 artículos invitados, 2 de revisión, 1 de enseñanza, 1 nota breve, 1 entrevista y 1 carta.

## 2. Extracción de metadatos (Sección 4.1, Anexo A)

**Descarga** (`chjs.descarga`). Los enlaces a los PDF se obtienen del índice de números del sitio de la revista, con una pausa de un segundo entre descargas.

**Primera pasada de OCR** (`chjs.ocr`). Cada página se convierte en una imagen de 400 ppp (pdf2image) y se lee con Tesseract 5 con los modelos de inglés, español y portugués, que conservan los acentos de nombres e instituciones. Se omiten las páginas anteriores a la del resumen y la lectura se detiene en la página que contiene las palabras clave (como máximo, 12 páginas).

**Segunda pasada sobre los superíndices** (`chjs.superindices`, `scripts/ocr_superindices.py`). En la primera pasada, los superíndices que vinculan a cada autor con su afiliación se confundían con signos de puntuación o se perdían. La segunda pasada vuelve a la imagen de la línea de autores:

1. binariza la página y separa sus componentes conexas;
2. estima la línea base y la altura de las mayúsculas a partir de las letras apoyadas en la línea base;
3. identifica como superíndices las componentes elevadas que no se superponen con letras;
4. recorta cada grupo, lo amplía tres veces y lo lee con Tesseract restringido a dígitos, comas y asteriscos.

**Reglas de extracción** (`chjs.extraccion`). A partir del texto se identifican el título, el resumen, las palabras clave, los autores y las afiliaciones. Las afiliaciones se numeran por orden de aparición, y cada autor se vincula con la suya mediante los superíndices. Cuando la cantidad de superíndices coincide con la de autores, se asignan en orden; si no coincide, se asignan por apellido. Las reglas tratan las confusiones frecuentes del OCR (Tabla A.1), como un superíndice leído como letra pegada al nombre de la institución.

## 3. Validación (Sección 4.1.1)

La extracción se evaluó de tres formas, y la normalización por separado:

1. **Concordancia con la base de referencia** (`chjs.validacion`, `scripts/probar_extraccion.py`). La base de referencia de la primera etapa combinó la capa de texto de los PDF con una revisión manual. Los artículos se emparejan uno a uno por título, con el método húngaro (`scipy.optimize.linear_sum_assignment`), y los autores de cada artículo, por nombre. Cada campo se compara texto con texto, después de normalizar mayúsculas, acentos y espacios, con las medidas de similitud de `rapidfuzz`:

   | Campo | Medida | Umbral |
   |---|---|---|
   | Título completo | razón de similitud | 90 |
   | Resumen | razón de similitud con las palabras ordenadas | 90 |
   | Cada palabra clave | razón de similitud | 90 |
   | Nombre de cada autor | razón de similitud con las palabras ordenadas | 85 |
   | Afiliaciones | coincidencia parcial de la parte institucional | 85 |

   Los países se comparan por igualdad.
2. **Revisión de todas las discrepancias** (`scripts/listar_discrepancias.py`). Cada una se revisó contra la imagen de la primera página. Las correcciones confirmadas están en `chjs.correcciones` y en `results/validacion/cambios_base_final.csv`.
3. **Muestra aleatoria de referencia** (`scripts/muestra_referencia.py`). Se revisaron 25 artículos elegidos al azar (semilla 2026), campo por campo, contra la imagen de la cabecera.

## 4. Normalización (Sección 4.1)

- **Instituciones** (`chjs.instituciones`, `chjs.normalizacion`). Cada afiliación se reduce a su parte institucional y se asigna a un nombre canónico; la tabla de correcciones resuelve asignaciones erróneas, duplicados y nombres que no eran instituciones. Resultado: 340 formas de escritura y 204 instituciones.
- **Autores** (`chjs.autores`). Se unifican las variantes de un mismo autor (iniciales, guiones, tildes y errores de lectura). Resultado: 396 autores distintos.
- **Países.** Se obtienen de la afiliación; hay 44 países.

## 5. Palabras clave (Sección 4.2)

`chjs.palabras_clave`, `scripts/analisis_palabras_clave.py`.

- **Preparación.** Las palabras clave se separan por `·`, `;` o `,`, se pasan a minúsculas sin acentos ni signos sobrantes, y se unifican sus variantes ortográficas y morfológicas: singular y plural, guiones y abreviaturas (Tabla B.1).
- **Series anuales.** Se construye, para cada palabra, el número anual de artículos que la usan y su proporción sobre los artículos del año con palabras clave, entre 2010 y 2025, con ceros en los años sin aparición.
- **Indicadores.**
  - Frecuencia total: suma de las proporciones anuales.
  - Persistencia: número de años con presencia.
  - Año medio de aparición, ponderado por la proporción.
  - Año y valor máximos.
  - Pendiente de la proporción, por mínimos cuadrados sobre la serie completa.
- **Tendencias.** Cada palabra presente en tres años o más se evalúa con un modelo lineal generalizado binomial (artículos con la palabra sobre artículos del año), con corrección de Benjamini-Hochberg sobre los 26 modelos.
- **Selección de las 25 de mayor relevancia.** El puntaje pondera en un 70 % la frecuencia total y en un 30 % la persistencia, ambas reescaladas al intervalo [0, 1]. La selección se valida con tres criterios: la correlación de Spearman del puntaje con cada indicador, el cambio de la lista con 24 y con 26 palabras, y la cobertura de las palabras con pendiente positiva.

## 6. Redes de colaboración (Sección 4.3, Anexo D)

`chjs.redes`, `scripts/resumen_redes.py`.

- **Nodos.** Cada autor (con su nombre unificado), cada institución normalizada y cada país es un nodo de su red.
- **Aristas.** Los participantes de un mismo artículo se conectan todos entre sí. El peso de la arista es el número de artículos compartidos, y una institución o un país con varios autores en un artículo cuenta una sola vez.
- **Métricas.** Grado, intermediación normalizada, coeficiente de agrupamiento local, densidad, transitividad y componentes conexas.
- **Comunidades.** Algoritmo de Louvain (`python-louvain`, semilla 42, con pesos).
- **Orden de construcción.** El resultado de Louvain depende del orden en que se agregan nodos y aristas, por lo que el orden es fijo:
  - en la red de autores, se sigue el orden de los artículos en la base;
  - en las de universidades y países, las aristas se agregan de mayor a menor peso, con empates por nombre.

## 7. Agrupamiento temático (Sección 4.4)

`chjs.corpus`, `chjs.agrupamiento`.

| Etapa | Parámetros |
|---|---|
| Documento | Título, resumen y palabras clave de cada artículo. El modelo se ajustó sobre los 177 artículos de la primera etapa. |
| Preprocesamiento | Minúsculas y sin acentos; se eliminan las palabras vacías en inglés y español y los términos de los nombres de autores e instituciones; raíz de Snowball (inglés). |
| TF-IDF | Unigramas y bigramas; frecuencia documental mínima de 3 artículos y máxima de 95 %; norma L2. Resultado: 1247 términos. |
| LSA | SVD truncada con 176 componentes (N − 1), semilla 42; 99,9 % de la varianza. |
| K-means | k entre 3 y 15; 50 inicializaciones; hasta 1000 iteraciones; semilla 42. |
| Selección de k | Silhouette, Calinski-Harabasz y Davies-Bouldin, con media y desviación sobre 25 semillas; Silhouette de referencia con cada dimensión permutada al azar (20 réplicas); tres criterios sustantivos. |

- **Elección de k.** Los índices internos no identifican un óptimo, por lo que k se eligió con tres criterios definidos antes de interpretar los grupos (Sección 3.7.2):
  - parsimonia;
  - interpretabilidad disciplinar;
  - validación semántica.

  Se verificaron con las tablas de contingencia frente a k = 6 y k = 8.
- **Interpretación.** Cada grupo se describe con los términos de mayor peso TF-IDF medio y con el artículo más cercano a su centroide (`describir`).
- **Artículos de la segunda etapa.** Los seis artículos incorporados después se proyectan en el mismo espacio y se asignan al centroide más cercano (`scripts/particion_final.py`).

### Estabilidad (Sección 4.4.3, Anexo C)

`scripts/estabilidad_k7.py`.

- **Bootstrap.** 200 réplicas con reposición; K-means con 20 inicializaciones y 500 iteraciones; predicción para todos los artículos; alineación de etiquetas con el método húngaro. Se calculan el ARI y el índice de Jaccard por grupo.
- **Co-asociación.** 500 submuestras del 80 % (10 inicializaciones). Se mide la proporción de submuestras en que cada par de artículos queda en el mismo grupo.
- **PAC.** Proporción de pares con co-asociación entre 0,1 y 0,9, para k entre 3 y 15 (200 submuestras).
- **Semillas.** ARI medio entre las particiones de k = 7 obtenidas con 25 semillas.
- **Otros algoritmos.** Ward con k = 7, y DBSCAN con radios de 1,00 a 1,35 y un mínimo de 5 vecinos.

### Sensibilidad (Sección 4.4.4)

`scripts/sensibilidad_183.py`. El procedimiento completo (TF-IDF, LSA y K-means) se repite con los 183 artículos y se compara con la partición presentada: tabla de contingencia y ARI.

### Evolución temporal y cruces (Secciones 4.4.5 y 4.4.6)

`scripts/particion_final.py`.

- **Series anuales por grupo.** Incluyen los años sin artículos.
- **Prueba de Mann-Kendall y pendiente de Sen,** con corrección de Benjamini-Hochberg.
- **Regresión de Poisson** y su dispersión. Como confirmación, se ajustan también:
  - un modelo cuasi-Poisson;
  - un modelo binomial negativo;
  - un modelo de Poisson con el logaritmo del total anual de artículos como exposición.
- **Cruces.**
  - El país de cada artículo es el más frecuente entre sus autores.
  - La institución de cada artículo es la del primer autor.

## 8. Figuras

`chjs.figuras` y `scripts/figuras_*.py`.

- **Formato.** PDF vectorial de 15,9 cm de ancho, con Calibri de 9 puntos.
- **Colores.**
  - Las comunidades usan una paleta validada para daltonismo: todos los pares de colores tienen ΔE ≥ 8,5.
  - Las comunidades menores van en gris.
- **Determinismo.** Las figuras son deterministas:
  - las disposiciones de las redes usan un orden de nodos fijo;
  - las etiquetas se ajustan con un número fijo de iteraciones;
  - los colores de la nube de términos no dependen de `hash()`.
