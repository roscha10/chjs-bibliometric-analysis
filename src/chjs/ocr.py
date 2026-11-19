# -*- coding: utf-8 -*-
"""
Reconocimiento óptico de caracteres (OCR) de los artículos.

Cada página se convierte en una imagen (pdf2image, 400 ppp) y se transforma en texto con
Tesseract usando los modelos de inglés, español y portugués, lo que conserva los acentos de
nombres e instituciones. Las páginas previas a la del resumen (portadas del número) se omiten.

Requisitos externos: Tesseract-OCR (con eng, spa y por) y Poppler (pdftoppm).
Las rutas se configuran con las variables de entorno TESSERACT_CMD, TESSDATA_PREFIX y POPPLER_PATH.
"""
import os, re, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

TESSERACT_CMD = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
POPPLER_PATH = os.environ.get("POPPLER_PATH")          # None si pdftoppm está en el PATH
IDIOMAS = "eng+spa+por"
DPI = 400
MAX_PAGINAS = 12

def ocr_articulo(pdf, dpi=DPI, idiomas=IDIOMAS, max_paginas=MAX_PAGINAS):
    """Devuelve el texto OCR desde la página del resumen hasta la de las palabras clave."""
    import pytesseract
    from pdf2image import convert_from_path
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    texto, n = "", 0
    for p in range(1, max_paginas + 1):
        try:
            img = convert_from_path(str(pdf), dpi=dpi, first_page=p, last_page=p, poppler_path=POPPLER_PATH)
        except Exception:
            break
        if not img:
            break
        t = pytesseract.image_to_string(img[0], lang=idiomas)
        n = p
        if not texto and not re.search(r"(?im)^\s*abstract\b", t) and p < max_paginas:
            continue                                   # portada del número o páginas previas
        texto += t + "\n"
        if re.search(r"(?i)\bkeywords?\b", texto):
            break
    return {"archivo": Path(pdf).name, "paginas": n, "texto": texto}

def ocr_lote(pdfs, salida, hilos=4):
    """OCR de una lista de PDF, en paralelo, guardando el avance en `salida` (JSON) cada 10 archivos."""
    salida = Path(salida)
    res = json.load(open(salida, encoding="utf-8")) if salida.exists() else []
    hechos = {r["archivo"] for r in res}
    pend = [p for p in pdfs if Path(p).name not in hechos]
    with ThreadPoolExecutor(hilos) as ex:
        futuros = [ex.submit(ocr_articulo, p) for p in pend]
        for k, f in enumerate(as_completed(futuros), 1):
            res.append(f.result())
            if k % 10 == 0 or k == len(pend):
                json.dump(res, open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res
