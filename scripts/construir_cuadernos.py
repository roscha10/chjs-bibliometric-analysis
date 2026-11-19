# -*- coding: utf-8 -*-
"""Construye los cinco cuadernos de notebooks/ y, con --ejecutar, los corre de principio a fin (nbclient).

  01_extraccion_metadatos        OCR, extracción, validación y base final (Sección 4.1, Anexo A)
  02_tendencias_tematicas        palabras clave (Sección 4.2, Anexo B)
  03_redes_colaboracion          redes de autores, universidades y países (Sección 4.3, Anexo D)
  04_clusterizacion_tematica     TF-IDF, LSA, K-means, partición final, tendencias y cruces (Sección 4.4)
  05_robustez_identificabilidad  estabilidad y sensibilidad de la partición (Sección 4.4, Anexo C)

Uso:  python scripts/construir_cuadernos.py [--ejecutar] [01 02 ...]
"""
import sys
from pathlib import Path
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / "notebooks"

INICIO = r'''import sys, json
from pathlib import Path
RAIZ = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(RAIZ / "src"))
import numpy as np
import pandas as pd
from IPython.display import display
from chjs import rutas
from chjs.cuadernos import ejecutar, figuras
pd.set_option("display.max_colwidth", 90)
pd.set_option("display.width", 200)'''

def md(t):
    return ("md", t)

def py(t):
    return ("py", t)

CUADERNOS = {}

# ===================================================================================================== 01
CUADERNOS["01_extraccion_metadatos"] = [
md(r'''# 1. Extracción de metadatos y validación del OCR

Este cuaderno reproduce la construcción de la base de datos de la tesis (Sección 4.1 y Anexo A): el texto de los artículos obtenido por OCR, la extracción de sus metadatos, la validación contra la base de referencia y la base final de 183 artículos.

La descarga de los PDF y el OCR no se ejecutan por defecto, porque requieren los archivos de la revista, Tesseract 5 y Poppler. Sus resultados están en `data/interim/`, de modo que el resto del cuaderno corre sin ellos.'''),
py(INICIO),
md(r'''## Descarga y OCR

Los PDF se descargan del sitio de la revista (`chjs.descarga`). Cada página se convierte en una imagen de 400 ppp y se lee con Tesseract en inglés, español y portugués (`chjs.ocr`), hasta la página que contiene las palabras clave. Una segunda pasada (`scripts/ocr_superindices.py`) vuelve a leer, ampliados, los superíndices de la línea de autores, que en la primera pasada se confundían con signos de puntuación.

Además de los 183 artículos, el texto OCR incluye las presentaciones de cada número y los editoriales, que no forman parte de la población de estudio.'''),
py(r'''EJECUTAR_OCR = False                     # requiere los PDF en data/raw/, Tesseract 5 y Poppler
if EJECUTAR_OCR:
    from chjs.descarga import descargar_pdfs
    from chjs.ocr import ocr_lote
    descargar_pdfs(rutas.CRUDOS)
    ocr_lote(sorted(rutas.CRUDOS.glob("*.pdf")), rutas.OCR_TEXTO)
    print(ejecutar("ocr_superindices.py"))

ocr = json.load(open(rutas.OCR_TEXTO, encoding="utf-8"))
sup = json.load(open(rutas.SUPERINDICES, encoding="utf-8"))
print(f"{len(ocr)} documentos con texto OCR; {len(sup)} con la segunda pasada de superíndices")'''),
md(r'''## Extracción de metadatos

Las reglas de `chjs.extraccion` identifican en el texto el título, el resumen, las palabras clave, los autores y las afiliaciones. Las afiliaciones se numeran por orden de aparición y cada autor se vincula con la suya mediante los superíndices. Por ejemplo:'''),
py(r'''from chjs.extraccion import extraer
doc = next(o for o in ocr if "Alzaid" in o["archivo"])
meta = extraer(doc["texto"], sup.get(doc["archivo"], {}).get("grupos"))
print("Título:        ", meta["titulo"])
print("Palabras clave:", meta["palabras_clave"])
print("Afiliaciones:  ", meta["afiliaciones"])
pd.DataFrame(meta["autores"])'''),
md(r'''## Validación de la extracción (Tabla 4.3)

Cada campo extraído se compara con la base de referencia de la primera etapa del estudio, construida con la capa de texto de los PDF y una revisión manual. Los artículos se emparejan uno a uno por título (asignación húngara) y los autores de cada artículo, por nombre. La tabla muestra el porcentaje de concordancia con la primera pasada del OCR y con las dos pasadas.'''),
py(r'''from chjs.validacion import comparar
CAMPOS = {"titulo": "Título", "resumen": "Resumen", "palabras_clave": "Palabras clave",
          "n_autores": "Número de autores", "autores": "Nombres de los autores",
          "afiliaciones_articulo": "Afiliaciones del artículo", "paises_articulo": "Países del artículo",
          "afiliacion_autor": "Afiliación de cada autor", "pais_autor": "País de cada autor"}
ref = json.load(open(rutas.BASE_REFERENCIA, encoding="utf-8"))
concordancia = {}
for nombre, s in [("Primera pasada", None), ("Dos pasadas", sup)]:
    df = comparar(ref, ocr, s)
    concordancia[nombre] = (100 * df[list(CAMPOS)].mean()).round(1)
pd.DataFrame(concordancia).rename(index=CAMPOS)'''),
md(r'''Las discrepancias que quedan se listaron una a una (`scripts/listar_discrepancias.py`) y se revisaron contra la imagen de la primera página de cada artículo. La mayoría son diferencias de grafía en los nombres de los autores, como las tildes de los nombres escritos en versalitas.'''),
py(r'''ejecutar("listar_discrepancias.py")
disc = pd.read_csv(rutas.VALIDACION / "discrepancias.csv")
print(f"{len(disc)} discrepancias en {disc['archivo'].nunique()} artículos")
disc.groupby("campo").size().rename("discrepancias")'''),
md(r'''## Base final

Las correcciones confirmadas en la revisión (`chjs.correcciones`) se aplican sobre la base de referencia, junto con la normalización de instituciones (`chjs.instituciones`) y de nombres de autores (`chjs.autores`). El resultado es idéntico a `data/processed/base_final.json`.'''),
py(r'''from chjs.correcciones import construir, resumen
base, cambios = construir(ref)
final = json.load(open(rutas.BASE_FINAL, encoding="utf-8"))
print("Idéntica a data/processed/base_final.json:", base == final)
print(resumen(base))
cambios.groupby("campo").size().rename("cambios")'''),
md(r'''La normalización reduce 340 formas de escritura de las afiliaciones a 204 instituciones. La Universidade de São Paulo, por ejemplo, aparece escrita de las siguientes formas:'''),
py(r'''usp = sorted({a["universidad_raw"] for r in base for a in r["Autores"]
              if a.get("universidad") == "Universidade de São Paulo"})
print(len(usp), "formas distintas")
usp[:10]'''),
md(r'''## Artículos por año (Tabla 4.1)'''),
py(r'''import re
anios = pd.DataFrame([{"Año": int(re.search(r"\d{4}", r["fecha"]).group()), "Volumen": r["Volumen"],
                       "Número": r["numero"]} for r in base])
t41 = anios.groupby("Año").agg(Volumen=("Volumen", "first"), Números=("Número", "nunique"),
                               Artículos=("Número", "size"))
print("Total:", t41["Artículos"].sum(), "artículos en", t41["Números"].sum(), "números")
t41'''),
]

# ===================================================================================================== 02
CUADERNOS["02_tendencias_tematicas"] = [
md(r'''# 2. Tendencias temáticas a partir de las palabras clave

Objetivo específico 1 (Sección 4.2). Las palabras clave de los autores se normalizan, se unifican sus variantes y se describe su evolución anual mediante la frecuencia, la persistencia, el año medio de aparición y la pendiente de su proporción anual. La tendencia de cada palabra presente en tres años o más se evalúa con un modelo lineal generalizado binomial, con corrección de Benjamini-Hochberg. Las series anuales incluyen los años en que la palabra no aparece.'''),
py(INICIO + r'''
from chjs.palabras_clave import VARIANTES, tablas, tabla_anual, metricas, tendencias_glm, seleccion, validaciones'''),
md(r'''## Normalización y unificación de variantes'''),
py(r'''base = json.load(open(rutas.BASE_FINAL, encoding="utf-8"))
_, kw0 = tablas(base, unificar=False)
art, kw = tablas(base)
print(f"{kw['article_id'].nunique()} artículos con palabras clave y {len(kw)} asignaciones")
print(f"{kw0['keyword_std'].nunique()} palabras clave distintas antes de unificar variantes y "
      f"{kw['keyword_std'].nunique()} después")
pd.DataFrame([(k, "; ".join(v)) for k, v in VARIANTES.items()], columns=["Forma unificada", "Variantes"])'''),
md(r'''## Indicadores por palabra clave'''),
py(r'''cuenta, prop, total = tabla_anual(art, kw)
m = metricas(cuenta, prop)
una = (m["articulos"] == 1)
print(f"{una.sum()} de {len(m)} palabras clave ({100 * una.mean():.0f} %) aparecen en un solo artículo; "
      f"{(m['persistencia'] >= 3).sum()} están presentes en tres años o más")
m.sort_values("frecuencia_total", ascending=False).head(15).round(3)'''),
md(r'''## Pruebas de tendencia

Para cada palabra presente en tres años o más se ajusta un modelo binomial con el número anual de artículos que la usan sobre el total de artículos del año, y se prueba si la pendiente del año es distinta de cero.'''),
py(r'''glm = tendencias_glm(cuenta, total)
print(f"{len(glm)} palabras clave evaluadas; p mínimo {glm['p'].min():.3f}; "
      f"p corregido mínimo {glm['p_bh'].min():.2f}; significativas tras la corrección: {(glm['p_bh'] <= 0.05).sum()}")
glm.sort_values("p").head(10).round(3)'''),
md(r'''Ninguna tendencia individual resulta significativa después de la corrección por comparaciones múltiples: con 16 años y frecuencias bajas, las pruebas tienen poca potencia. La lectura de la Sección 4.2 es, por eso, descriptiva.

## Las 25 palabras clave de mayor relevancia

El puntaje combina la frecuencia total (peso 0,7) y la persistencia (peso 0,3), ambas reescaladas al intervalo [0, 1]. La selección se valida de tres formas (Tabla 4.5): la correlación de Spearman del puntaje con cada indicador, el cambio de la lista al seleccionar 24 o 26 palabras, y la proporción de palabras con pendiente positiva y presencia en tres años o más que quedan incluidas.'''),
py(r'''m = m.join(glm)
top, orden = seleccion(m)
display(orden.head(25).round(3))
validaciones(m)'''),
md(r'''## Figuras 4.2 y 4.3'''),
py(r'''ejecutar("analisis_palabras_clave.py")
figuras("figuras_palabras_clave.py", ["fig_kw_burbujas", "fig_kw_mapa_calor"])'''),
]

# ===================================================================================================== 03
CUADERNOS["03_redes_colaboracion"] = [
md(r'''# 3. Redes de colaboración

Objetivo específico 2 (Sección 4.3 y Anexo D). Se construyen tres redes de coautoría: de autores, de universidades y de países. Dos participantes se conectan si firman juntos al menos un artículo, y el peso de la arista es el número de artículos que comparten; una institución o un país con varios autores en un artículo cuenta una sola vez. Las comunidades se detectan con el algoritmo de Louvain, con semilla fija.'''),
py(INICIO + r'''
import networkx as nx
from chjs.redes import construir_redes, resumen, centrales'''),
md(r'''## Estructura de las tres redes (Tabla 4.6)'''),
py(r'''base = json.load(open(rutas.BASE_FINAL, encoding="utf-8"))
redes, articulos = construir_redes(base)
pd.DataFrame.from_dict({red: {"articulos": articulos[red], **resumen(G)} for red, G in redes.items()},
                       orient="index").round(3)'''),
md(r'''## Autores (Tabla 4.7)

Autores entre los diez primeros por grado (número de coautores distintos) o por intermediación normalizada.'''),
py(r'''G = redes["autores"]
display(centrales(G))
btw = nx.betweenness_centrality(G)
pd.DataFrame([{"autor": a, "coautores": G.degree(a), "intermediacion": round(btw[a], 4),
               "agrupamiento_local": round(nx.clustering(G, a), 2)}
              for a in ["Gauss M. Cordeiro", "Josmar Mazucheli", "Francisco Louzada", "Vera L.D. Tomazella"]])'''),
md(r'''## Universidades (Tabla 4.8)'''),
py(r'''centrales(redes["universidades"])'''),
md(r'''## Países'''),
py(r'''centrales(redes["paises"])'''),
md(r'''## Figuras 4.4 a 4.7 y D.1 a D.3

`scripts/resumen_redes.py` guarda los grafos y las particiones de Louvain en `results/redes/`, y `scripts/figuras_redes.py` dibuja las redes a partir de ellos.'''),
py(r'''ejecutar("resumen_redes.py")
figuras("figuras_redes.py", ["fig_red_autores", "fig_ego_autores", "fig_red_universidades", "fig_red_paises",
                             "fig_anx_red_autores_completa", "fig_anx_red_universidades_completa",
                             "fig_anx_ego_tomazella"])'''),
]

# ===================================================================================================== 04
CUADERNOS["04_clusterizacion_tematica"] = [
md(r'''# 4. Estructura temática: agrupamiento de los artículos

Objetivo específico 3 (Sección 4.4). El título, el resumen y las palabras clave de cada artículo se limpian y se reducen a sus raíces; se representan con TF-IDF (unigramas y bigramas) y se proyectan con análisis semántico latente (LSA). Sobre esa representación, K-means con k = 7 agrupa los artículos.

El modelo se ajustó con los 177 artículos de la primera etapa, el mismo presentado en la defensa, y los seis artículos incorporados después se asignan al centroide más cercano.'''),
py(INICIO + r'''
from sklearn.metrics import adjusted_rand_score
from chjs.corpus import documento, palabras_vacias, exclusiones, limpiar, tfidf_lsa
from chjs.agrupamiento import kmeans, describir'''),
md(r'''## Preprocesamiento del texto

Se pasa a minúsculas, se eliminan los acentos, las palabras vacías en inglés y español y los términos de los nombres de autores e instituciones, y cada palabra se reduce a su raíz (Snowball). El texto limpio de cada artículo está en `data/processed/`. Se conserva tal como se generó, porque la lista de exclusiones depende de los nombres de la base y estos se corrigieron después: regenerarlo hoy da el mismo texto en la mayoría de los artículos y diferencias de pocos términos en el resto.'''),
py(r'''c177 = pd.read_csv(rutas.CORPUS_177)
c183 = pd.read_csv(rutas.CORPUS_183)
base = json.load(open(rutas.BASE_FINAL, encoding="utf-8"))
vacias, excluidas = palabras_vacias(), exclusiones(base)
print("Texto original:", c183.loc[1, "text_raw"][:300], "...")
print()
print("Texto limpio:  ", limpiar(documento(base[1]), vacias, excluidas)[:300], "...")
iguales = sum(limpiar(documento(r), vacias, excluidas) == t for r, t in zip(base, c183["text_clean"].fillna("")))
print(f"\nTexto regenerado idéntico al guardado en {iguales} de {len(base)} artículos")
print("Términos por documento: mediana", c183["n_tokens"].median(), "| mínimo", c183["n_tokens"].min(),
      "| máximo", c183["n_tokens"].max())'''),
md(r'''## TF-IDF y LSA'''),
py(r'''X, vect, Z, svd = tfidf_lsa(c177["text_clean"].fillna("").tolist())
print(f"TF-IDF: {X.shape[0]} artículos y {X.shape[1]} términos; "
      f"{100 * (1 - X.nnz / np.prod(X.shape)):.1f} % de celdas en cero")
print(f"LSA: {Z.shape[1]} componentes, {100 * svd.explained_variance_ratio_.sum():.1f} % de la varianza")
print("Idéntica a data/processed/lsa_177.npz:", np.allclose(Z, np.load(rutas.LSA_177)["Z"]))'''),
md(r'''## Selección del número de grupos (Figura 4.8)

Silhouette, Calinski-Harabasz y Davies-Bouldin para k entre 3 y 15, con 25 semillas por valor de k, y Silhouette de referencia con las dimensiones de la representación permutadas al azar. Estos cálculos forman parte de `scripts/estabilidad_k7.py`, que tarda entre 15 y 30 minutos; si sus resultados ya existen, se leen.'''),
py(r'''if not (rutas.AGRUPAMIENTO / "seleccion_k.csv").exists():
    ejecutar("estabilidad_k7.py")
sel = pd.read_csv(rutas.AGRUPAMIENTO / "seleccion_k.csv", index_col=0)
sel.round(4)'''),
md(r'''Ningún índice señala un k claro: Calinski-Harabasz favorece k = 3, Silhouette y Davies-Bouldin el mayor k evaluado. Con k = 7, la Silhouette es baja, pero casi tres veces la de los datos sin estructura, y los grupos tienen una lectura temática clara.

## Partición de siete grupos (Tabla 4.9)

Términos de mayor peso de cada grupo (en su raíz) y artículo más cercano al centroide.'''),
py(r'''modelo = kmeans(Z, 7)
y0 = pd.read_csv(rutas.ETIQUETAS_177)["cluster"].values
print("ARI con la partición original:", adjusted_rand_score(y0, modelo.labels_))
describir(X, Z, modelo, vect.get_feature_names_out(), c177["title"].values, c177["year"].values)'''),
md(r'''## Asignación de los seis artículos de la segunda etapa'''),
py(r'''nuevos = [5] + list(range(178, 183))           # Yang et al. (2010) y el Vol. 16, N.º 2 (2025)
Zn = svd.transform(vect.transform(c183.loc[nuevos, "text_clean"].fillna("")))
pd.DataFrame({"articulo": c183.loc[nuevos, "title"].values, "anio": c183.loc[nuevos, "year"].values,
              "grupo": modelo.predict(Zn) + 1})'''),
md(r'''## Tamaño de los grupos, evolución temporal y cruces (Tablas 4.11 y 4.12)

`scripts/particion_final.py` reúne la partición de los 183 artículos y calcula las tendencias de cada grupo (Mann-Kendall y pendiente de Sen con corrección de Benjamini-Hochberg; regresión de Poisson, con y sin el total anual como exposición) y los cruces por país e institución.'''),
py(r'''ejecutar("particion_final.py")
A = rutas.AGRUPAMIENTO
display(pd.read_csv(A / "tamanos_grupos.csv"))
display(pd.read_csv(A / "tendencias_grupos.csv").round(3))
pd.read_csv(A / "grupo_por_pais.csv", index_col=0).head(10)'''),
md(r'''Ningún grupo muestra una tendencia significativa con Mann-Kendall después de la corrección. La caída del grupo 1 en la regresión de Poisson desaparece al usar el total anual como exposición: refleja que la revista publica menos artículos por año, no un cambio en la proporción del tema.

## Figuras 4.8, 4.9 y 4.11, y figuras del Anexo B'''),
py(r'''figuras("figuras_agrupamiento.py", ["fig_k_seleccion", "fig_grupos", "fig_series_grupos"])
figuras("figuras_corpus.py", ["fig_anx_longitud", "fig_anx_terminos", "fig_anx_nube"])'''),
]

# ===================================================================================================== 05
CUADERNOS["05_robustez_identificabilidad"] = [
md(r'''# 5. Robustez e identificabilidad de la partición

Sección 4.4 y Anexo C. Se evalúa si la partición de siete grupos se sostiene ante perturbaciones de los datos y del algoritmo: remuestreo con reposición (bootstrap), submuestras del 80 % (co-asociación y PAC), distintas semillas, otros algoritmos (Ward y DBSCAN) y la repetición del procedimiento completo con los 183 artículos.

Los cálculos de `scripts/estabilidad_k7.py` tardan entre 15 y 30 minutos. Si sus resultados ya están en `results/agrupamiento/`, el cuaderno los lee; con `RECALCULAR = True` se rehacen.'''),
py(INICIO),
py(r'''RECALCULAR = False
A = rutas.AGRUPAMIENTO
if RECALCULAR or not (A / "resumen_estabilidad.json").exists():
    ejecutar("estabilidad_k7.py")
res = json.load(open(A / "resumen_estabilidad.json", encoding="utf-8"))
print("Reproduce la partición original (ARI):", res["reproduccion_ari"])'''),
md(r'''## Estructura frente a datos sin estructura'''),
py(r'''print(f"Silhouette con k = 7: {res['silhouette_k7']:.3f}")
print(f"Silhouette con las dimensiones permutadas al azar: {res['silhouette_azar_k7']:.3f} "
      f"({res['silhouette_k7'] / res['silhouette_azar_k7']:.1f} veces menor)")'''),
md(r'''## Bootstrap y co-asociación por grupo (Tabla 4.10)

En cada una de las 200 réplicas se ajusta K-means sobre una muestra con reposición, se asignan todos los artículos y las etiquetas se alinean con las originales (método húngaro). El índice de Jaccard mide cuánto se conserva cada grupo. La co-asociación interna es la proporción media de submuestras en que dos artículos del mismo grupo quedan juntos.'''),
py(r'''boot = pd.read_csv(A / "bootstrap.csv")
print(f"ARI del bootstrap: mediana {boot['ari'].median():.3f}, media {boot['ari'].mean():.3f}")
pd.read_csv(A / "estabilidad_grupos.csv").round(2)'''),
md(r'''## Semillas, Ward y DBSCAN (Tabla C.1)'''),
py(r'''print(f"ARI medio entre las particiones de 25 semillas: {res['semillas_ari_medio']:.2f}")
print(f"Ward: ARI {res['ward_ari']:.2f} con K-means; tamaños {res['ward_tamanos']}")
display(pd.read_csv(A / "kmeans_ward.csv", index_col=0))
pd.read_csv(A / "dbscan.csv")'''),
md(r'''## Proporción de pares ambiguos (Tabla C.2)

El PAC disminuye de forma continua con k, sin un mínimo que identifique un número natural de grupos.'''),
py(r'''pd.read_csv(A / "pac.csv").round(2).set_index("k").T'''),
md(r'''## Particiones vecinas (k = 6 y k = 8)'''),
py(r'''display(pd.read_csv(A / "k6_k7.csv", index_col=0))
pd.read_csv(A / "k8_k7.csv", index_col=0)'''),
md(r'''## Sensibilidad a la incorporación de los artículos de la segunda etapa (Tabla C.3)

Se repite el procedimiento completo (TF-IDF, LSA y K-means) con los 183 artículos y se compara con la partición presentada. Los grupos del reajuste se identifican con letras porque su numeración no corresponde a la presentada.'''),
py(r'''ejecutar("sensibilidad_183.py")
sens = json.load(open(A / "resumen_sensibilidad.json", encoding="utf-8"))
print(f"ARI entre ambas particiones: {sens['ari']:.2f}")
pd.read_csv(A / "sensibilidad_contingencia.csv", index_col=0)'''),
md(r'''## Matriz de co-asociación (Figura 4.10)'''),
py(r'''figuras("figuras_agrupamiento.py", ["fig_coasociacion"])'''),
]


def construir(nombre, celdas):
    nb = new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.cells = [new_markdown_cell(t) if k == "md" else new_code_cell(t) for k, t in celdas]
    return nb

def ejecutar_cuaderno(nb, nombre):
    from nbclient import NotebookClient
    NotebookClient(nb, timeout=3600, kernel_name="python3", resources={"metadata": {"path": str(CARPETA)}}).execute()
    return nb

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for nombre, celdas in CUADERNOS.items():
        if args and nombre[:2] not in args:
            continue
        nb = construir(nombre, celdas)
        if "--ejecutar" in sys.argv:
            nb = ejecutar_cuaderno(nb, nombre)
        nbformat.write(nb, CARPETA / f"{nombre}.ipynb")
        print("escrito", nombre)
