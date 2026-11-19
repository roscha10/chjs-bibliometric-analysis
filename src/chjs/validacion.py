# -*- coding: utf-8 -*-
"""
Validación de la extracción por OCR frente a la base de metadatos.

Para cada artículo de la base se identifica el texto OCR que le corresponde (por su título y el inicio de su
resumen, con asignación uno a uno) y se mide la concordancia de cada campo:

  titulo                 similitud del título completo >= 90 (rapidfuzz.ratio)
  resumen                similitud del resumen >= 90 (token_sort_ratio)
  palabras_clave         proporción de palabras clave de la base recuperadas por la regla (similitud >= 90)
  n_autores              coincidencia exacta del número de autores distintos
  autores                proporción de autores de la base recuperados (similitud de nombre >= 85)
  afiliacion_autor       proporción de autores cuya afiliación original (parte institucional, tal como figura
                         en el PDF) aparece en la afiliación que la regla OCR le asigna
  pais_autor             proporción de autores cuyo país coincide con el de la afiliación OCR asignada
  afiliaciones_articulo  proporción de afiliaciones originales del artículo presentes en el bloque de afiliaciones OCR
  paises_articulo        proporción de países del artículo presentes en las afiliaciones OCR

La comparación es de extracción: texto contra texto. La asignación del nombre canónico de cada institución
(normalización) se audita por separado, porque una diferencia allí no es un error de lectura.
"""
import re, unicodedata
import pandas as pd
from rapidfuzz import fuzz
from .extraccion import extraer
from .normalizacion import reparar_acentos, pais_de

def plano(s):
    s = unicodedata.normalize("NFKD", reparar_acentos(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())

def emparejar(base, ocr):
    """Asigna a cada registro de la base el texto OCR que mejor contiene su título y el inicio de su resumen.
    La asignación es uno a uno (algoritmo húngaro), de modo que dos registros con el mismo título
    (la carta al editor de Rau, 2015, y el artículo que comenta) no compiten por el mismo PDF."""
    from scipy.optimize import linear_sum_assignment
    import numpy as np
    planos = [plano(o["texto"])[:6000] for o in ocr]
    P = np.array([[0.5 * fuzz.partial_ratio(plano(r["Articulo"]), t) + 0.5 * fuzz.partial_ratio(plano(r["abstract"])[:200], t)
                   for t in planos] for r in base])
    filas, cols = linear_sum_assignment(-P)
    asig = dict(zip(filas, cols))
    return [(int(asig[i]), float(P[i, asig[i]])) for i in range(len(base))]

INSTITUCIONAL = re.compile(r"(?i)univ|instit|college|school|centre|center|centro|escola|company|bank|banco|council|"
                           r"hospital|foundation|fundac|nucleus|caja|cnr|imati|laborat|ministry|ltd|inc\b|s\.a\b")

def parte_institucional(raw):
    """Segmento institucional de una afiliación ('Department of X, University of Y, City' -> 'university of y')."""
    partes = [p for p in re.split(r"[,;]", raw or "") if INSTITUCIONAL.search(p)]
    univ = [p for p in partes if re.search(r"(?i)univ", p)]        # la universidad antes que el centro o instituto
    partes = univ or partes
    return plano(partes[0]) if partes else plano((raw or "").split(",")[0])

def comparar(base, ocr, superindices=None):
    """superindices: resultado de la segunda pasada ({archivo: {"grupos": [...]}}), opcional."""
    pares = emparejar(base, ocr)
    filas = []
    for r, (k, punt) in zip(base, pares):
        grupos = (superindices or {}).get(ocr[k]["archivo"], {}).get("grupos")
        e = extraer(ocr[k]["texto"], grupos)
        kb = [plano(x) for x in re.split(r"[·;,]", r.get("keywords") or "") if plano(x)]
        ko = {plano(x) for x in e["palabras_clave"]}
        nb = list(dict.fromkeys(plano(a["nombre"]) for a in r["Autores"]))      # autores únicos (la base repite al autor por afiliación)
        no = list(dict.fromkeys(plano(a["nombre"]) for a in e["autores"]))
        ok_a = [max([fuzz.token_sort_ratio(x, y) for y in no] or [0]) >= 85 for x in nb]
        ok_i, ok_p = [], []
        for a in r["Autores"]:
            cand = [x for x in e["autores"] if fuzz.token_sort_ratio(plano(a["nombre"]), plano(x["nombre"])) >= 85]
            afs = plano(" ".join(" ".join(x["afiliaciones"]) for x in cand))
            if a.get("universidad_raw"):
                ok_i.append(fuzz.partial_ratio(parte_institucional(a["universidad_raw"]), afs) >= 85)
            if a.get("pais"):
                ok_p.append(a["pais"] in sum((x["paises"] for x in cand), []))
        pais_b = {a["pais"] for a in r["Autores"] if a.get("pais")}
        pais_o = {p for x in e["autores"] for p in x["paises"] if p} | {pais_de(v) for v in e["afiliaciones"].values()} - {""}
        bloque_afil = plano(" ".join(e["afiliaciones"].values()))
        raws = {parte_institucional(a.get("universidad_raw")) for a in r["Autores"] if a.get("universidad_raw")} - {""}
        filas.append(dict(articulo=r["Articulo"][:80], archivo=ocr[k]["archivo"], emparejamiento=round(punt, 1),
                          titulo=fuzz.ratio(plano(r["Articulo"]), plano(e["titulo"])) >= 90,   # título completo, no un fragmento
                          resumen=fuzz.token_sort_ratio(plano(r["abstract"]), plano(e["resumen"])) >= 90,
                          palabras_clave=sum(max([fuzz.ratio(x, y) for y in ko] or [0]) >= 90 for x in kb) / len(kb) if kb else 1.0,
                          n_autores=len(nb) == len(no), autores=sum(ok_a) / len(ok_a),
                          afiliacion_autor=sum(ok_i) / len(ok_i) if ok_i else 1.0,
                          pais_autor=sum(ok_p) / len(ok_p) if ok_p else 1.0,
                          afiliaciones_articulo=sum(fuzz.partial_ratio(x, bloque_afil) >= 85 for x in raws) / len(raws) if raws else 1.0,
                          paises_articulo=len(pais_b & pais_o) / len(pais_b) if pais_b else 1.0))
    return pd.DataFrame(filas)

def resumen_concordancia(df):
    out = {"articulos": len(df)}
    for c in ["titulo", "resumen", "n_autores"]:
        out[c] = f"{df[c].sum()} / {len(df)} ({100 * df[c].mean():.1f} %)"
    for c in ["palabras_clave", "autores", "afiliacion_autor", "pais_autor", "afiliaciones_articulo", "paises_articulo"]:
        out[c] = f"{100 * df[c].mean():.1f} % (completos en {(df[c] == 1).sum()} artículos)"
    return out
