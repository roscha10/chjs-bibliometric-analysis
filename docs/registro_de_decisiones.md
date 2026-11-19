# Registro de decisiones

Decisiones metodológicas y de datos tomadas durante el estudio, con su motivo. Cada entrada indica la fecha, la decisión y dónde queda implementada.

---

## 2026-11-16. Censo 2010–2025 de 183 artículos

- **Decisión:** completar el censo con el artículo de Yang, Müller y Rosner (2010), que se había omitido, y con los cinco artículos del Vol. 16, N.º 2 (diciembre de 2025). El Vol. 17 (2026) queda fuera del período.
- **Motivo:** el estudio es un censo de la revista entre 2010 y 2025; con 177 artículos el censo estaba incompleto.

## 2026-11-16. Partición temática de siete líneas

- **Decisión:** se conserva el modelo K-means de siete grupos, ajustado sobre los 177 artículos originales. Los seis artículos nuevos se asignan al centroide más cercano. El reajuste con los 183 artículos se informa como análisis de sensibilidad.
- **Motivo:** la partición original es la evaluada y aprobada. El reajuste (ARI 0,44 con la partición original) muestra un continuo temático, coherente con la conclusión del estudio, y no una estructura distinta.

## 2026-11-17. Extracción por OCR en dos pasadas

- **Decisión:** los metadatos se extraen del texto OCR (Tesseract 5, 400 ppp, inglés, español y portugués) con reglas documentadas en `src/chjs/extraccion.py`. Una segunda pasada (`src/chjs/superindices.py`) lee los superíndices de afiliación a partir de la geometría de la imagen.
- **Motivo:** en la primera pasada, Tesseract confunde los superíndices pequeños con signos parecidos ('1' con '!', '2' con '?', '3' con '*') o los omite. De las 112 asignaciones autor–afiliación que fallaban, 102 se debían a esa lectura.
- **Implementación:** la segunda pasada ubica la línea de autores en la imagen y separa los componentes elevados sobre la línea base que no se superponen con una letra (así descarta tildes y puntos). Luego los recorta, los amplía tres veces y los lee con Tesseract restringido a dígitos, coma y asterisco.

## 2026-11-17. Afiliaciones numeradas por orden de aparición

- **Decisión:** las afiliaciones de cada artículo se numeran por su orden de aparición (1, 2, 3...), no por el signo que el OCR leyó al inicio de la línea.
- **Motivo:** la revista lista las afiliaciones en orden numérico, pero el OCR lee a veces el índice con otro signo ('*Department' por '3Department').

## 2026-11-17. Emparejamiento uno a uno entre registros y PDF

- **Decisión:** cada registro de la base se asigna a un único PDF mediante el algoritmo húngaro, a partir de la similitud del título y del inicio del resumen.
- **Motivo:** la carta al editor de Rau (2015) y el artículo que comenta (Dietrich, Kalke y Richter, 2013) tienen el mismo título en la base. Con una asignación independiente, ambos registros apuntaban al mismo PDF.

## 2026-11-17. Validación separada de extracción y normalización

- **Decisión:** la concordancia de la extracción se mide comparando texto con texto (la afiliación tal como figura en el PDF). La asignación del nombre canónico se audita aparte.
- **Motivo:** la comparación anterior ponía el nombre canónico de la base ('Universidade Federal do Ceará') frente al texto del PDF ('Federal University of Ceara') y contaba como error de lectura lo que era solo una diferencia de idioma.

## 2026-11-17. Corrección de la normalización de instituciones (218 → 203)

- **Decisión:** se revisan uno por uno los 218 nombres canónicos de la base y se corrigen con la tabla de `src/chjs/instituciones.py`. Resultado: 203 instituciones.
- **Asignaciones erróneas corregidas:**
  - 'University of Campinas' estaba asignada a la Universidade de Brasília (6 casos), y una afiliación de la Universidade de Brasília, a Campinas.
  - 'Acharya Nagarjuna University' (India) estaba asignada a A.C. Camargo Cancer Center.
  - 'Acroama Gnan Vikas Pvt. Ltd.' (India) estaba asignada al Banco do Nordeste do Brasil.
- **Duplicados unificados** (una institución con dos o tres nombres; en la red de universidades eran nodos distintos):
  - Universidade de Brasília;
  - Universidade Federal do Paraná;
  - Universidade Federal do Rio Grande do Norte;
  - Universidade Federal de Minas Gerais;
  - Universidade Estadual de Maringá;
  - Universidade Federal de São Carlos;
  - Universidade Federal de Mato Grosso do Sul;
  - Universidad de Concepción;
  - University of Baghdad;
  - UNAM;
  - University of Padua;
  - Université Djillali Liabès de Sidi Bel Abbès;
  - Millennium Nucleus on Intergenerational Mobility (MOVI).
- **Nombres que no eran instituciones:**
  - 'Piazza Arechi II' es la dirección del departamento DEMM de la Università del Sannio.
  - 'Viale Maresciallo Pilsudski' es la dirección del Gestore dei Servizi Energetici.
  - 'Punjab' es una región; la institución es el Crop Reporting Service del Agriculture Department de Punjab.
  - 'Laboratoire Modélisation Mathématique...' pertenece a la Université de Tunis El Manar.
- **Caso interpretado:** 'UTFPR - Universidade Federal do Paraná, Cornélio Procópio' se asigna a la Universidade Tecnológica Federal do Paraná (UTFPR). La sigla y el campus corresponden a esa universidad, aunque el PDF escribe "Universidade Federal do Paraná".
- **Consecuencia:** se recalculan la red de universidades, el número de instituciones y los cruces por institución.

## 2026-11-17. Revisión del 100 % de las discrepancias entre el OCR y la base

- **Decisión:** cada diferencia entre la lectura OCR y la base se resolvió mirando la imagen del PDF (`scripts/listar_discrepancias.py`). La muestra aleatoria de referencia se reserva para estimar el error cuando ambas lecturas coinciden.
- **Resultado:** la base tenía errores que el OCR leyó bien. Por ejemplo:
  - Carmen Díaz figuraba en la Universidad de Granada; el PDF dice Universidad de Huelva.
  - Seis nombres en versalitas habían perdido sus diacríticos: Ednário Mendonça, Flávio B. Gonçalves, José María Sarabia, Moizés da S. Melo, María Dueñas, y G.R. Mohtashami Borzadaran, que además había perdido las iniciales.
  - Otros nombres estaban truncados o tenían restos de superíndices: "abrizio Ruggeri", "Gauss Cordeiro3", "Caroline P. de Moraes3".
- **Grafía de los nombres:** el OCR comete errores de carácter en las versalitas ("Miiller" por Müller, "Kirsos" por Kitsos). Por eso la grafía final de cada nombre es la de la base, corregida en los casos verificados contra la imagen.

## 2026-11-17. Unificación de variantes de un mismo autor (424 → 396 nombres)

- **Decisión:** las variantes de un mismo autor (mismo apellido, nombre e institución) se llevan a una sola forma con `src/chjs/autores.py`. Ejemplos: 'Vera L.D. Tomazella', 'Vera L. D. Tomazella' y 'Vera Tomazella'; 'Dipak Dey' y 'Dipak Kumar Dey'; 'Victor Hugo Lachos' y 'Victor H. Lachos'.
- **Motivo:** en la red de coautoría cada nombre distinto era un nodo, de modo que un mismo autor aparecía dividido en dos o tres nodos.
- **Casos no unificados:** Cecília Azevedo y Caio L.N. Azevedo, y Giovana O. Silva, Geiza Silva y Guilherme P. da Silva, son personas distintas.

## 2026-11-17. Base final y nueva ejecución de las redes

- **Base final:** `scripts/construir_base_final.py` aplica las correcciones sobre la base de referencia (`data/interim/base_referencia.json`, que se conserva sin cambios) y escribe `data/processed/base_final.json`. No modifica el título, el resumen ni las palabras clave, para que la partición temática siga siendo reproducible.
- **Cifras finales:**
  - 396 autores distintos;
  - 340 formas originales de afiliación;
  - 204 instituciones (incluida la Universidad de Huelva);
  - 44 países.
- **Red de autores:**
  - 404 → 377 nodos y 531 → 515 aristas;
  - autores con intermediación nula: 368 → 331;
  - grado de Cordeiro: 21 → 24;
  - Vera L.D. Tomazella, antes dividida en tres nodos, es la tercera autora por grado (12) y la segunda por intermediación.
- **Red de universidades:**
  - 186 → 176 nodos;
  - grado: UFPE 22, USP 19, PUC de Chile y UnB 12.
- **Red de países:** sin cambios.

## 2026-11-17. Muestra aleatoria de referencia (25 artículos)

- **Procedimiento:** se eligieron 25 artículos al azar con semilla 2026 (`scripts/muestra_referencia.py`) y en cada uno se revisaron, contra la imagen de la primera página, el título, los autores, sus índices y sus afiliaciones.
- **Resultado:** en los 25 artículos, el título, los autores y sus afiliaciones coinciden con el PDF. Errores encontrados:
  - Moraga (Vol. 12, N.º 2) tiene los índices ¹ y ²; tanto la base como el OCR registraban solo el primero. Se agregó la afiliación de la Universidad de Valparaíso.
  - Tres nombres en versalitas habían perdido la tilde: Germán Tirao, Ramón Giraldo y José J. de Santana e Silva. Una búsqueda en todo el corpus de nombres que difieren solo en diacríticos encontró, además, Ramón Gutiérrez-Jáimez, Eduardo Alarcón-Bustamante, Lanciné Bamba y Sônia M. De Stefano Piedade, todos verificados en la imagen.
- **Erratas del propio PDF:** el PDF escribe "State University of Marigá" y "Centro Universitrio". Se conservan en la afiliación original y se corrigen en el nombre canónico.

## 2026-11-17. Composición del corpus por tipo de artículo

- **Hallazgo:** según la categoría impresa en cada PDF, el corpus incluye 174 artículos de investigación y nueve de otros tipos. Los 174 cuentan los 18 que no imprimen categoría, propios del número especial del Vol. 3 y de los Vol. 8 y 9. Los nueve son:
  - tres artículos invitados;
  - dos de revisión, uno de ellos el homenaje a Pilar Iglesias;
  - un artículo docente;
  - una nota breve (Vol. 9);
  - una entrevista ("A conversation with Oscar Bustos", Vol. 6);
  - una carta al editor (Rau, 2015).
- **Decisión:** se conservan todos, porque el estudio es un censo de lo publicado. La tesis ya no dice "183 artículos de investigación", sino "183 artículos", y la composición queda en la nota de la Tabla 4.1. Solo se excluyen las presentaciones de número y los editoriales.

## 2026-11-17. Corrección del análisis de tendencias de palabras clave

- **Problema detectado:** el cálculo anterior estimaba la pendiente de cada palabra clave, tanto la del GLM binomial como la de la regresión lineal, solo con los años en que la palabra clave aparecía. Los años sin aparición, que son ceros, quedaban fuera, de modo que la "tendencia" reflejaba sobre todo las variaciones del número de artículos por año. Además, el puntaje de relevancia sumaba la frecuencia (suma de proporciones) y la persistencia (número de años) en sus escalas originales, así que los pesos efectivos no eran 70/30.
- **Corrección:** `src/chjs/palabras_clave.py` construye la serie completa 2010–2025 con ceros y ajusta el GLM binomial con el total de artículos de cada año como número de ensayos, corrigiendo con Benjamini–Hochberg. Reescala la frecuencia y la persistencia a [0, 1] antes de ponderarlas.
- **Resultado:** la conclusión no cambia, ya que ninguna tendencia es significativa (menor p = 0,027 para *monte carlo simulation*; corregido, 0,61). Cambios:
  - el Top-25 solo cambia en una palabra: entra *skew-normal distribution* y sale *non-response*;
  - correlación de Spearman con la pendiente: 0,25 → 0,46;
  - sensibilidad 4 % / 4 %;
  - cobertura de pendientes positivas: 15 de 15;
  - las palabras clave recientes son *functional data analysis*, *bootstrapping*, *heavy-tailed distributions*, *extreme-value distribution* y *r software*; *partial identification* y *bayesian estimation* ya no aparecen.
- **Hallazgo nuevo:** de las 697 palabras clave, 611 (88 %) aparecen en un solo artículo y solo 26 se repiten en tres o más años.
- **Figuras:** se conservan el gráfico de burbujas (26 palabras clave recurrentes) y el mapa de calor (Top-25), en PDF vectorial (`scripts/figuras_palabras_clave.py`). El gráfico "año de máximo vs. pendiente" se omite porque repetía la información del de burbujas con una medida menos estable: con tres apariciones, el año de máximo depende de un solo artículo.

## 2026-11-17. Sección 4.3: lectura corregida de las redes y formato de las figuras

- **Corrección de interpretación:** la versión anterior afirmaba que la componente gigante de la red de autores "concentra a la mayoría de los autores" y describía una red "robusta, modular y resiliente". Con la base corregida, la componente gigante reúne 78 de 377 autores (21 %), y la red se divide en 89 componentes con modularidad de 0,93: la colaboración ocurre en equipos pequeños y cerrados. La tesis describe ahora la red como fragmentada y evita esos calificativos.
- **Medidas nuevas que sostienen la lectura:**
  - **Agrupamiento local:** el de Cordeiro (0,12) es menor que el de Tomazella (0,18), es decir, sus coautores colaboran poco entre sí; por eso es a la vez el autor central y el principal puente.
  - **Universidad de Concepción:** tiene grado 3 pero es la 8.ª en intermediación.
  - **Países fuera de la red internacional:** Costa de Marfil, Japón, Marruecos, Suecia y Uruguay (solo artículos de un país).
- **Formato:**
  - Las tres secciones repetidas por red (metodología, red global, barras de grado, barras de intermediación, comunidades y tres ego-redes) se reemplazan por:
    - una tabla comparativa de las tres redes;
    - una figura por red, con las comunidades coloreadas;
    - una tabla de actores centrales por red, que reúne grado e intermediación con sus posiciones.
  - La única figura de ego-redes contrasta a Cordeiro con Tomazella. Las ego-redes de las universidades y de los países se describen en el texto.
- **Paleta de comunidades:** azul y verde de la marca, más naranja y amarillo. Las comunidades menores van en gris. Todos los pares superan la prueba de daltonismo (ΔE ≥ 8,5). Las etiquetas se unen a su nodo con una línea guía trazada después de reacomodarlas.

## 2026-11-17. Sección 4.3: continuidad con la defensa

- **Criterio (decisión del autor):** las diferencias con lo presentado en la defensa se informan, pero sin que la sección cambie de lectura. En el cuerpo se destacan los resultados coherentes con la presentación; lo nuevo se mantiene, pero en otro espacio.
  - En el cuerpo:
    - la red global (componente gigante) de autores y de universidades;
    - Cordeiro, Mazucheli y Louzada como ejes de la red, con sus tres ego-redes, las mismas de la defensa;
    - la tabla de autores centrales;
    - Brasil como centro y Chile como enlace.
  - En el texto, la estructura se describe como "núcleo conectado y grupos más pequeños", en lugar de "red fragmentada".
  - En el Anexo D:
    - la red completa de autores y de universidades, con el núcleo arriba y las componentes periféricas debajo, de mayor a menor y rotuladas las principales;
    - la ego-red de Tomazella.
  - Tomazella figura en la tabla y entre los autores puente, sin destacar la diferencia con la defensa.

## 2026-11-17. Sección 4.4: estabilidad recalculada sobre el modelo de la defensa

- **Modelo:** el de 177 artículos presentado en la defensa (K-means, k = 7, 50 inicializaciones, semilla 42), reproducido con ARI = 1 por `scripts/estabilidad_k7.py`. Los seis artículos de la segunda etapa se asignan al centroide más cercano.
- **Cifras:**
  - **Selección de k:** Silhouette 0,025 en k = 7. La referencia al azar (cada dimensión permutada, mismos parámetros del modelo, 20 réplicas) es 0,009. Calinski-Harabasz alcanza su máximo en k = 3; Silhouette y Davies-Bouldin mejoran hasta k = 15.
  - **Partición:** ARI medio entre 25 semillas = 0,37. El PAC disminuye de forma continua con k.
  - **Ward:** ARI 0,34, con un grupo de 87 artículos.
  - **DBSCAN, radio 1,20:** grupos de 77, 14 y 7 artículos.
  - **Co-asociación interna:**
    - muestreo 0,63 y control de procesos 0,58 (en la defensa, 0,59 y 0,61, por la variación del remuestreo);
    - en bondad de ajuste hay un subconjunto compacto.
- **Tendencias:** Mann-Kendall con corrección BH, todas p ≥ 0,40.
  - Poisson: solo distribuciones simétricas queda en el límite (p corregido 0,050).
  - Esa baja deja de ser significativa con cuasi-Poisson, con binomial negativo y con el total anual como exposición (p corregido ≥ 0,13). La revista publicó menos artículos en los últimos años.
- **Sensibilidad (reajuste con 183 artículos):**
  - ARI 0,45 frente a la partición presentada.
  - Se conservan distribuciones simétricas (18 de 20), muestreo (14 de 15), espacial (9 de 12), inferencia paramétrica (37 de 51) y bondad de ajuste (19 de 32).
  - Control de procesos deja de formar un grupo propio.
  - Se informa en una subsección breve, según el criterio de continuidad con la defensa.

## 2026-11-18. Figuras reproducibles y repositorio verificado

- **Problema:** dos ejecuciones del mismo guion daban dibujos distintos en las redes, la nube de términos y el gráfico de burbujas, aunque los datos eran idénticos.
- **Causas y correcciones** (`scripts/figuras_*.py`):
  - `G.subgraph()` y `nx.ego_graph()` recorren el conjunto de nodos cuando el subgrafo es pequeño, y ese orden cambia en cada ejecución de Python. Los subgrafos se construyen ahora con un orden fijo: la componente gigante, de mayor a menor grado (empates por nombre), y los coautores de cada ego-red, en orden alfabético.
  - `adjustText` deja de mover las etiquetas al cabo de un segundo si no se fija el número de iteraciones, de modo que el resultado dependía de la velocidad del equipo. El gráfico de burbujas usa ahora 1000 iteraciones.
  - La nube de términos asignaba el color con `hash()`, que cambia entre ejecuciones; ahora usa `zlib.crc32`.
- **Elección del orden:** entre los órdenes probados (el de la red, alfabético y por grado), el orden por grado da las redes más legibles y las más parecidas a las de la versión anterior: Cordeiro al centro del núcleo, Mazucheli y Louzada como ejes de la segunda comunidad, y UFPE, USP y PUC Chile bien rotuladas.
- **Consecuencia:** las 16 figuras de la tesis se generan desde el repositorio (`CHJS_FIGURAS=<carpeta de figuras de la tesis>`) y coinciden píxel a píxel con las que contiene el documento. Las comunidades, los tamaños y las métricas no cambian; solo la disposición de algunos nodos y etiquetas.
- **Verificación del repositorio:** con los datos de `data/`, los guiones reproducen la base final (idéntica), la Tabla 4.3, las redes y sus comunidades de Louvain, las palabras clave, la partición de siete grupos (ARI = 1), la estabilidad (Tabla 4.10, Anexo C) y la sensibilidad (Tabla C.3, ARI 0,45).

## 2026-11-18. Pruebas de tendencia complementarias en el repositorio

- **Decisión:** `chjs.agrupamiento.tendencias` calcula, además de Mann-Kendall, Poisson y Poisson con exposición, un modelo cuasi-Poisson y uno binomial negativo, con corrección de Benjamini-Hochberg.
- **Motivo:** la Sección 4.4.5 afirma que la disminución de distribuciones simétricas (Poisson, *p* corregido 0,050) deja de ser significativa con esos modelos; ahora la afirmación se reproduce desde el repositorio.
- **Resultado:** *p* corregido de 0,29 con cuasi-Poisson, 0,24 con binomial negativa y 0,34 con el total anual como exposición. En series sin sobredispersión el modelo binomial negativo no converge y se usa el valor de Poisson.
