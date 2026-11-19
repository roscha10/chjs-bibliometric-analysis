# -*- coding: utf-8 -*-
"""Lista todas las discrepancias entre la extracción OCR (primera y segunda pasada) y la base, campo por campo,
para su revisión manual contra la imagen del PDF.

Entrada: data/interim/ocr_texto.json, superindices.json y base_referencia.json
Salida:  results/validacion/discrepancias.csv, con una fila por discrepancia:
  archivo, campo, autor (si corresponde), valor en la base, valor OCR, decision (vacía: se completa al revisar)

Uso:  python scripts/listar_discrepancias.py
"""
import sys, json, re
from pathlib import Path
import pandas as pd
from rapidfuzz import fuzz
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs import rutas
from chjs.extraccion import extraer
from chjs.validacion import emparejar, plano, parte_institucional
from chjs.normalizacion import reparar_acentos

DIR = rutas.VALIDACION
ocr = json.load(open(rutas.OCR_TEXTO, encoding="utf-8"))
base = json.load(open(rutas.BASE_REFERENCIA, encoding="utf-8"))
sup = json.load(open(rutas.SUPERINDICES, encoding="utf-8")) if rutas.SUPERINDICES.exists() else {}

filas = []
def agregar(arch, campo, autor, vb, vo):
    filas.append(dict(archivo=arch, campo=campo, autor=autor, base=vb, ocr=vo, decision=""))

for r, (k, _) in zip(base, emparejar(base, ocr)):
    arch = ocr[k]["archivo"]
    e = extraer(ocr[k]["texto"], sup.get(arch, {}).get("grupos"))
    if fuzz.ratio(plano(r["Articulo"]), plano(e["titulo"])) < 90:
        agregar(arch, "titulo", "", r["Articulo"], e["titulo"])
    if fuzz.token_sort_ratio(plano(r["abstract"]), plano(e["resumen"])) < 90:
        agregar(arch, "resumen", "", r["abstract"][:300], e["resumen"][:300])
    ko = {plano(x): x for x in e["palabras_clave"]}
    for kw in [x.strip() for x in re.split(r"[·;,]", r.get("keywords") or "") if plano(x)]:
        if max([fuzz.ratio(plano(kw), y) for y in ko] or [0]) < 90:
            agregar(arch, "palabra_clave", "", kw, " · ".join(e["palabras_clave"]))
    nombres_o = [x["nombre"] for x in e["autores"]]
    vistos = set()
    for a in r["Autores"]:
        nb = reparar_acentos(a["nombre"])
        if nb in vistos:
            continue
        vistos.add(nb)
        mejor = max(nombres_o, key=lambda y: fuzz.token_sort_ratio(plano(nb), plano(y)), default="")
        if fuzz.token_sort_ratio(plano(nb), plano(mejor)) < 85:
            agregar(arch, "autor", nb, nb, mejor)
        elif plano(nb) != plano(mejor):
            agregar(arch, "autor_grafia", nb, nb, mejor)      # mismo autor, grafía distinta (para revisar)
    for a in r["Autores"]:
        if not a.get("universidad_raw"):
            continue
        cand = [x for x in e["autores"] if fuzz.token_sort_ratio(plano(a["nombre"]), plano(x["nombre"])) >= 85]
        afs = " | ".join(" ; ".join(x["afiliaciones"]) for x in cand)
        if fuzz.partial_ratio(parte_institucional(a["universidad_raw"]), plano(afs)) < 85:
            agregar(arch, "afiliacion_autor", reparar_acentos(a["nombre"]), reparar_acentos(a["universidad_raw"]), afs)

df = pd.DataFrame(filas)
df.to_csv(DIR / "discrepancias.csv", index=False, encoding="utf-8-sig")
print(df.groupby("campo").size().to_string())
print("artículos con alguna discrepancia:", df["archivo"].nunique())
