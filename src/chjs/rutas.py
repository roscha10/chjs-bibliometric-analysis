# -*- coding: utf-8 -*-
"""
Rutas del repositorio.

  data/raw/         PDF de los artículos (no se incluyen en el repositorio; ver data/raw/README.md)
  data/interim/     resultados intermedios: texto OCR, superíndices, base de referencia
  data/processed/   base de datos final, corpus textual y modelo de agrupamiento de 177 artículos
  results/          resultados (validacion, palabras_clave, redes, agrupamiento) y figuras (figures)

La variable de entorno CHJS_RAIZ permite usar otra carpeta raíz.
"""
import os
from pathlib import Path

RAIZ = Path(os.environ.get("CHJS_RAIZ", Path(__file__).resolve().parents[2]))
DATOS = RAIZ / "data"
CRUDOS = DATOS / "raw"
INTERMEDIOS = DATOS / "interim"
PROCESADOS = DATOS / "processed"
RESULTADOS = RAIZ / "results"
FIGURAS = Path(os.environ.get("CHJS_FIGURAS", RESULTADOS / "figures"))   # CHJS_FIGURAS: carpeta de figuras de la tesis
VALIDACION = RESULTADOS / "validacion"
PALABRAS = RESULTADOS / "palabras_clave"
REDES = RESULTADOS / "redes"
AGRUPAMIENTO = RESULTADOS / "agrupamiento"

BASE_FINAL = PROCESADOS / "base_final.json"                 # 183 artículos, metadatos corregidos y normalizados
BASE_REFERENCIA = INTERMEDIOS / "base_referencia.json"      # base de referencia anterior a la validación OCR
OCR_TEXTO = INTERMEDIOS / "ocr_texto.json"                  # texto OCR de los 197 PDF (primera pasada)
SUPERINDICES = INTERMEDIOS / "superindices.json"            # segunda pasada sobre los superíndices
CORPUS_177 = PROCESADOS / "corpus_177.csv"                  # texto limpio del modelo de agrupamiento
CORPUS_183 = PROCESADOS / "corpus_183.csv"                  # texto limpio de los 183 artículos
LSA_177 = PROCESADOS / "lsa_177.npz"                        # representación LSA del modelo (177 x 176)
ETIQUETAS_177 = PROCESADOS / "etiquetas_k7_177.csv"         # partición original de siete grupos

TESSDATA = Path(os.environ.get("TESSDATA_PREFIX", RAIZ / "tessdata"))           # modelos de Tesseract (eng, spa, por)

def pdf(archivo):
    """Ruta local del PDF de un artículo a partir del nombre registrado en el texto OCR."""
    return CRUDOS / Path(str(archivo).replace("\\", "/")).name

for _d in (CRUDOS, INTERMEDIOS, PROCESADOS, FIGURAS, VALIDACION, PALABRAS, REDES, AGRUPAMIENTO):
    _d.mkdir(parents=True, exist_ok=True)
