# -*- coding: utf-8 -*-
"""Segunda pasada de OCR sobre los superíndices de la línea de autores de todos los artículos.

Requiere los PDF en data/raw/ (chjs.descarga.descargar_pdfs) y Tesseract con los modelos eng, spa y por
(variable de entorno TESSDATA_PREFIX). Lee el texto de la primera pasada (data/interim/ocr_texto.json), ubica la
línea de autores de cada artículo y guarda los superíndices leídos en data/interim/superindices.json. La corrida es
incremental: si se interrumpe, continúa con los artículos pendientes.

Uso:  python scripts/ocr_superindices.py
"""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs import rutas
from chjs.extraccion import lineas_autores
from chjs.superindices import superindices_lote

ocr = json.load(open(rutas.OCR_TEXTO, encoding="utf-8"))
tareas = [(o["archivo"], str(rutas.pdf(o["archivo"])), o["paginas"], lineas_autores(o["texto"])) for o in ocr
          if rutas.pdf(o["archivo"]).exists()]
if not tareas:
    sys.exit("No hay PDF en data/raw/. Descárguelos con chjs.descarga.descargar_pdfs('data/raw').")
t = time.time()
res = superindices_lote(tareas, rutas.SUPERINDICES)
print(f"artículos: {len(res)} | con grupos: {sum(1 for r in res.values() if r['grupos'])} | "
      f"errores: {sum(1 for r in res.values() if r.get('error'))} | sin línea ubicada: "
      f"{sum(1 for r in res.values() if r['pagina'] is None)} | {time.time() - t:.0f} s")
