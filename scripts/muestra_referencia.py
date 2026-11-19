# -*- coding: utf-8 -*-
"""Muestra de referencia para medir la exactitud real de la extracción (revisión visual contra el PDF).

Selecciona al azar (semilla fija) n artículos de los 183, guarda la imagen de la cabecera de cada uno
(título, autores y afiliaciones) y una planilla con lo extraído por OCR y lo registrado en la base, para
anotar en cada campo cuál de las dos lecturas coincide con la imagen.

Uso:  python scripts/muestra_referencia.py [n=25] [semilla=2026]
Requiere los PDF en data/raw/. Salida: results/validacion/muestra_referencia/ (PNG por artículo + planilla.csv)
"""
import sys, os, json, random
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from PIL import Image
from chjs import rutas
from chjs.extraccion import extraer
from chjs.validacion import emparejar
from chjs.normalizacion import reparar_acentos
from chjs.superindices import _pagina

n = int(sys.argv[1]) if len(sys.argv) > 1 else 25
semilla = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
OUT = rutas.VALIDACION / "muestra_referencia"; OUT.mkdir(exist_ok=True)
ocr = json.load(open(rutas.OCR_TEXTO, encoding="utf-8"))
base = json.load(open(rutas.BASE_FINAL, encoding="utf-8"))
sup = json.load(open(rutas.SUPERINDICES, encoding="utf-8")) if rutas.SUPERINDICES.exists() else {}
pares = emparejar(base, ocr)
idx = sorted(random.Random(semilla).sample(range(len(base)), n))
filas = []
for i in idx:
    r, (k, _) = base[i], pares[i]
    arch = ocr[k]["archivo"]
    s = sup.get(arch, {})
    e = extraer(ocr[k]["texto"], s.get("grupos"))
    pag = s.get("pagina") or ocr[k]["paginas"]
    img = _pagina(str(rutas.pdf(arch)), pag, dpi=150)
    Image.fromarray(img[: int(img.shape[0] * 0.55)]).save(OUT / f"{i:03d}.png")
    filas.append(dict(
        id=i, archivo=arch, pagina=pag,
        titulo_ocr=e["titulo"], titulo_base=r["Articulo"],
        autores_ocr=" | ".join(f"{a['nombre']} {a['indices']}" for a in e["autores"]),
        autores_base=" | ".join(dict.fromkeys(reparar_acentos(a["nombre"]) for a in r["Autores"])),
        afiliaciones_ocr=" | ".join(f"{a['nombre']}: {'; '.join(a['afiliaciones'])}" for a in e["autores"]),
        afiliaciones_base=" | ".join(f"{reparar_acentos(a['nombre'])}: {reparar_acentos(a.get('universidad_raw') or '')}" for a in r["Autores"]),
        palabras_clave_ocr=" · ".join(e["palabras_clave"]), palabras_clave_base=r.get("keywords") or "",
        titulo_correcto="", autores_correcto="", afiliaciones_correcto="", palabras_clave_correcto=""))
pd.DataFrame(filas).to_csv(OUT / "planilla.csv", index=False, encoding="utf-8-sig")
print("muestra:", idx)
