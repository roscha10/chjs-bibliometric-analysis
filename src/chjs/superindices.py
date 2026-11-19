# -*- coding: utf-8 -*-
"""
Segunda pasada de OCR dirigida a los superíndices de afiliación de la línea de autores.

En la primera pasada, Tesseract lee los superíndices pequeños como signos parecidos ('1' -> '!', '2' -> '?',
'3' -> '*') o los omite, y con ello se pierde la relación entre cada autor y su afiliación. Esta pasada
recupera esa relación a partir de la geometría de la imagen:

  1. se renderiza la página del resumen (400 ppp) y se ubican, con Tesseract (image_to_data), las líneas
     de la imagen que corresponden a la línea de autores ya extraída del texto;
  2. en cada línea se separan los componentes conexos de la imagen binarizada y se estima la línea base
     y la altura de las mayúsculas; un componente elevado sobre la línea base, más pequeño que una letra y
     que no se superpone horizontalmente con ninguna letra (lo que descarta tildes y puntos) es un superíndice;
  3. los superíndices vecinos se agrupan ('1,2,*'), cada grupo se recorta, se amplía tres veces y se lee
     con Tesseract restringido a dígitos, coma y asterisco;
  4. cada grupo se asigna al apellido que lo precede en la línea.

Resultado por artículo: {apellido leído: [índices]}, que extraccion.autores_afiliaciones usa en lugar de
los índices de la primera pasada cuando están disponibles.
"""
import os, re
import numpy as np

TESSERACT_CMD = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
DPI = 400

def _pagina(pdf, n, dpi=DPI):
    import fitz
    doc = fitz.open(pdf)
    try:
        pix = doc[n - 1].get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
        return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy()
    finally:
        doc.close()

def _lineas_imagen(img, idiomas="eng+spa+por"):
    """Líneas de texto de la mitad superior de la página: texto, caja y palabras con sus cajas."""
    import pytesseract
    from PIL import Image
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    alto = int(img.shape[0] * 0.6)
    d = pytesseract.image_to_data(Image.fromarray(img[:alto]), lang=idiomas, output_type=pytesseract.Output.DICT)
    lineas = {}
    for k in range(len(d["text"])):
        if not d["text"][k].strip():
            continue
        clave = (d["block_num"][k], d["par_num"][k], d["line_num"][k])
        x, y, w, h = d["left"][k], d["top"][k], d["width"][k], d["height"][k]
        lineas.setdefault(clave, []).append((d["text"][k], x, y, x + w, y + h))
    out = []
    for pal in lineas.values():
        pal.sort(key=lambda p: p[1])
        out.append({"texto": " ".join(p[0] for p in pal), "palabras": pal,
                    "caja": (min(p[1] for p in pal), min(p[2] for p in pal), max(p[3] for p in pal), max(p[4] for p in pal))})
    return sorted(out, key=lambda l: l["caja"][1])

def _grupos_superindice(img, caja):
    """Grupos de componentes elevados (superíndices) en la línea de la caja dada: [(x0, y0, x1, y1)]."""
    from scipy import ndimage
    x0, y0, x1, y1 = caja
    h = y1 - y0
    top = max(0, int(y0 - 0.7 * h))                       # incluye superíndices que el OCR separó en otra línea
    rec = img[top:int(y1 + 0.15 * h), max(0, x0 - 10):x1 + 40]
    bin_ = rec < 140
    lab, n = ndimage.label(bin_)
    objs = ndimage.find_objects(lab)
    comps = []
    for i, sl in enumerate(objs):
        cy0, cy1, cx0, cx1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if (cy1 - cy0) * (cx1 - cx0) < 12:
            continue
        comps.append((cx0, cy0, cx1, cy1))
    if not comps:
        return [], top, max(0, x0 - 10)
    # línea base: fondo mediano de los componentes altos; altura de mayúscula: la de las letras apoyadas en esa
    # línea (no la de las versalitas, que dominan en los nombres compuestos en VERSALITAS)
    p95 = np.percentile([c[3] - c[1] for c in comps], 95)
    altos = [c for c in comps if (c[3] - c[1]) >= 0.5 * p95]
    if not altos:
        return [], top, max(0, x0 - 10)
    base = np.median([c[3] for c in altos])
    apoyadas = [c for c in comps if abs(c[3] - base) <= 0.12 * p95 and (c[3] - c[1]) >= 0.3 * p95]
    if not apoyadas:
        return [], top, max(0, x0 - 10)
    capH = np.percentile([c[3] - c[1] for c in apoyadas], 90)
    cuerpo = [c for c in apoyadas if (c[3] - c[1]) >= 0.4 * capH]           # letras apoyadas en la línea base
    sup = []
    for c in comps:
        alto_c = c[3] - c[1]
        elevado = (c[3] < base - 0.2 * capH and c[3] > base - 1.0 * capH
                   and 0.3 * capH <= alto_c < 0.85 * capH)
        if not elevado:
            continue
        # tildes y puntos de la i se superponen con una letra; los superíndices no
        if any(min(c[2], b[2]) - max(c[0], b[0]) > 0.3 * (c[2] - c[0]) for b in cuerpo):
            continue
        sup.append(c)
    sup.sort()
    grupos = []
    for c in sup:
        if grupos and c[0] - grupos[-1][2] < 0.8 * capH:
            g = grupos[-1]
            grupos[-1] = (g[0], min(g[1], c[1]), max(g[2], c[2]), max(g[3], c[3]))
        else:
            grupos.append(c)
    # un superíndice cierra la palabra: no lo sigue de inmediato otra letra (descarta fragmentos de letras
    # en versalitas, como el remate de la G, que quedan dentro de la palabra)
    grupos = [g for g in grupos if not any(0 <= b[0] - g[2] < 0.25 * capH for b in cuerpo)]
    return grupos, top, max(0, x0 - 10)

def _leer_grupo(img, g, top, izq):
    import pytesseract
    from PIL import Image
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    x0, y0, x1, y1 = g
    h = y1 - y0
    rec = img[top + max(0, y0 - 4): top + y1 + int(0.35 * h), izq + max(0, x0 - 4): izq + x1 + 4]
    if rec.size == 0:
        return ""
    im = Image.fromarray(rec)
    im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
    lienzo = Image.new("L", (im.width + 60, im.height + 60), 255)
    lienzo.paste(im, (30, 30))
    # una línea de texto; si no se lee nada (un dígito aislado), como palabra y como carácter único
    for psm in (7, 8, 10):
        t = pytesseract.image_to_string(lienzo, config=f"--psm {psm} -c tessedit_char_whitelist=0123456789,*").strip()
        if t:
            return t
    return ""

def superindices_articulo(pdf, pagina, lineas_autores):
    """Lee los superíndices de las líneas de autores. Devuelve [(palabra que precede, índices)] en orden."""
    from rapidfuzz import fuzz
    out = []
    # primero las páginas donde terminó la primera pasada; si la línea no aparece (artículos sin palabras
    # clave, en que el OCR siguió leyendo), el resto del documento desde el inicio
    orden = [p for p in [pagina, pagina - 1, pagina - 2] if p >= 1]
    orden += [p for p in range(1, pagina) if p not in orden]
    for p in orden:
        img = _pagina(pdf, p)
        lin_img = _lineas_imagen(img)
        usadas = [l for l in lin_img if any(fuzz.ratio(l["texto"], la) >= 75 for la in lineas_autores)]
        if not usadas:
            continue
        for l in usadas:
            grupos, top, izq = _grupos_superindice(img, l["caja"])
            for g in grupos:
                gx0 = izq + g[0]
                previas = [w for w in l["palabras"] if w[1] < gx0 - 2]
                palabra = previas[-1][0] if previas else ""
                texto = _leer_grupo(img, g, top, izq)
                indices = [c for c in re.sub(r"[^0-9*]", "", texto)]
                out.append({"palabra": palabra, "leido": texto, "indices": indices})
        return {"pagina": p, "grupos": out}
    return {"pagina": None, "grupos": []}

def superindices_lote(tareas, salida, hilos=4):
    """Segunda pasada para varios artículos, en paralelo y con caché incremental en `salida` (JSON).
    tareas: lista de (archivo, ruta del PDF, página donde terminó el OCR, líneas de autores)."""
    import json
    from pathlib import Path
    from concurrent.futures import ThreadPoolExecutor, as_completed
    salida = Path(salida)
    res = json.load(open(salida, encoding="utf-8")) if salida.exists() else {}
    pend = [t for t in tareas if t[0] not in res and t[3]]

    def una(t):
        archivo, pdf, pagina, lineas = t
        try:
            return archivo, dict(superindices_articulo(pdf, pagina, lineas), lineas=lineas)
        except Exception as e:                                  # se registra y se sigue con el resto
            return archivo, {"pagina": None, "grupos": [], "lineas": lineas, "error": str(e)}

    with ThreadPoolExecutor(hilos) as ex:
        for k, f in enumerate(as_completed([ex.submit(una, t) for t in pend]), 1):
            archivo, r = f.result()
            res[archivo] = r
            if k % 10 == 0 or k == len(pend):
                json.dump(res, open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res
