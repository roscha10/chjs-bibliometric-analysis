import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# ----------------------------------------------------------------------
md(r"""# Extracción de metadatos académicos desde PDFs escaneados (OCR)

**Fuente de datos** — construcción del corpus a partir de los PDFs de la Chilean Journal of Statistics
(2010–2025), tal como se describe en la Sección 4.1 y el Anexo A de la tesis.

La mayoría de los números de la revista corresponden a versiones **digitalizadas sin texto embebido**,
por lo que la extracción de título, autores, afiliaciones, palabras clave, resumen y metadatos de
publicación (volumen, número, fecha) requirió combinar:

1. **Extracción directa de texto** con `PyMuPDF` (`fitz`) cuando el PDF sí tenía texto seleccionable.
2. **OCR** con `pytesseract` (motor Tesseract) sobre las dos primeras páginas cuando no lo tenía,
   convertidas a imagen de 300 DPI.
3. **Heurísticas de expresiones regulares**, diseñadas a partir de la exploración manual de los
   formatos editoriales reales de la revista, para segmentar el texto plano en campos estructurados.
4. **Inferencia de país** de cada afiliación institucional con `pycountry` + un diccionario de alias.

> **Nota de reproducibilidad:** este notebook expone el código real usado para procesar cada artículo
> individual. No incluye los PDFs originales (no se redistribuyen por tamaño y por los derechos de la
> editorial), así que las celdas que dependen de un PDF están marcadas como **demostrativas** — se
> pueden ejecutar sobre tu propia copia de un PDF de la revista cambiando `pdf_path`. La celda final,
> en cambio, sí es completamente reproducible: carga el JSON consolidado final (`data/reorganized_data_c_CLEAN_NORMALIZADO.json`,
> incluido en este repo) y valida la cobertura de campos reportada en la Sección 4.1.5 de la tesis.
""")

# ----------------------------------------------------------------------
md("## 0. Configuración e imports")

code(r"""
import os
import io
import re
import csv
import json
import unicodedata
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import pandas as pd

# Rutas a los binarios de Tesseract OCR y Poppler (ajustar según tu instalación local).
# Solo son necesarias para procesar PDFs escaneados desde cero; no se requieren para
# la celda de validación final (Sección 5), que usa el JSON ya consolidado.
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# os.environ["PATH"] += os.pathsep + r"C:\ruta\a\poppler\Library\bin"

DATA_JSON = Path("../data/reorganized_data_c_CLEAN_NORMALIZADO.json")
""")

# ----------------------------------------------------------------------
md(r"""## 1. Extracción de texto (PyMuPDF + OCR de respaldo)

Para cada PDF se extrae el texto de las primeras páginas con `PyMuPDF`. Si una página no tiene texto
seleccionable (menos de 20 caracteres), se renderiza a imagen (300 DPI) y se aplica OCR con
`pytesseract`. El corte se hace en cuanto aparece `Abstract` o `Keywords`, ya que toda la metadata
relevante (título, autores, afiliaciones) se concentra en la primera página del artículo.
""")

code(r"""
def extraer_texto_pdf(path):
    doc = fitz.open(path)
    texto_total = ""

    for i, page in enumerate(doc):
        texto = page.get_text().strip()
        # Si no hay texto embebido, se aplica OCR sobre la página renderizada.
        if len(texto) < 20:
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            texto = pytesseract.image_to_string(image, lang="eng")
            print(f"[OCR aplicado en página {i+1}]")
        texto_total += texto + "\n"

        # 1-2 páginas suelen bastar para los metadatos (volumen, autores, abstract, keywords).
        if i >= 1:
            if re.search(r"(?i)^\s*abstract\b", texto_total, re.M) or re.search(r"(?i)^\s*keywords?\b", texto_total, re.M):
                break

    return texto_total
""")

# ----------------------------------------------------------------------
md(r"""## 2. Normalización y limpieza de texto

El texto crudo (ya sea de OCR o de extracción directa) presenta errores tipográficos recurrentes:
ligaduras (`ﬁ`, `ﬀ`, `ﬂ`), guiones partidos por saltos de línea, y variantes de caracteres especiales
(p. ej. "Renyi" en lugar de "Rényi"). Estas correcciones se aplican de forma consistente antes de
cualquier extracción de campos.
""")

code(r"""
def normalize_text(s: str) -> str:
    s = s.replace("ﬁ", "fi").replace("ﬀ", "ff").replace("ﬂ", "fl")
    s = s.replace("di erence", "difference").replace("Di erence", "Difference")
    s = s.replace("Renyi", "Rényi")
    # punto suelto justo tras el primer token: "Weaam. M. Alhadlaq" -> "Weaam M. Alhadlaq"
    s = re.sub(r"^([A-Z][a-zÀ-ÖØ-öø-ÿ]+)\.\s+", r"\1 ", s)
    # reparar guiones partidos por OCR: "Jacobs - Lewis" / "Jacobs  Lewis"
    s = re.sub(r"\b-\s+\b", "-", s)
    s = re.sub(r"\bJacobs\s+Lewis\b", "Jacobs-Lewis", s)
    s = re.sub(r"[∗•·◦]+", "·", s)  # unificar bullets al punto medio
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


# patrón de "persona": Nombre Apellido (con iniciales opcionales)
NAME_TOKEN = r"[A-Z][a-zÀ-ÖØ-öø-ÿ]+(?:\s+[A-Z]\.)*"
PERSON_RE = re.compile(rf"{NAME_TOKEN}\s+[A-Z][a-zÀ-ÖØ-öø-ÿ\-']+", flags=re.UNICODE)

AFFI_HINTS = r"(department|universit[a|á]d|universidade|university|faculty|facultad|institute|instituto|school|centro|centre|laboratory|laboratorio)"

def looks_like_authors_line(line: str) -> bool:
    '''Heurística: 2+ nombres tipo Nombre Apellido, separados por comas o and/y.'''
    L = normalize_text(line)
    if re.search(AFFI_HINTS, L, flags=re.I):
        return False
    hits = PERSON_RE.findall(L)
    sep = ("," in L) or re.search(r"\b(and|y|e)\b", L, flags=re.I)
    return len(hits) >= 2 and sep
""")

# ----------------------------------------------------------------------
md(r"""## 3. Extracción de campos estructurados

Cada campo se extrae con una función independiente, basada en patrones observados directamente en los
PDFs de la revista (encabezado "Vol. X, No. Y, Month Year", líneas de autores seguidas de superíndices
numéricos referidos a afiliaciones, secciones "Abstract"/"Keywords" bien delimitadas).
""")

code(r"""
def extraer_volumen_numero_fecha_paginas(texto):
    '''Soporta encabezados tipo Vol. 8, No. 2, September 2017, 65-91 y variantes.'''
    header = " ".join(texto.splitlines()[:10])
    header = normalize_text(header)

    m = re.search(
        r"Vol\.\s*(\d+)\s*,\s*No\.\s*(\d+)\s*,\s*([A-Za-z]+)\s+(\d{4})(?:\s*,\s*([0-9]+(?:\s*-\s*[0-9]+)?))?",
        header
    )
    if m:
        vol, num, month, year = int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4))
        pages = m.group(5) if m.group(5) else None
        return vol, num, f"{month}, {year}", pages

    m2 = re.search(
        r"Volume\s+(\d+)\s*,?\s*Number\s+(\d+).{0,30}\(\s*([A-Za-z]+)\s+(\d{4})\s*\)",
        header
    )
    if m2:
        vol, num, month, year = int(m2.group(1)), int(m2.group(2)), m2.group(3), int(m2.group(4))
        return vol, num, f"{month}, {year}", None

    return None, None, None, None


def extraer_titulo_articulo(texto):
    lines = [normalize_text(ln) for ln in texto.splitlines() if ln.strip()]
    cut = len(lines)
    for i, ln in enumerate(lines):
        if re.match(r"(?i)^abstract\b", ln) or re.match(r"(?i)^keywords?\b", ln):
            cut = i
            break
    head = lines[:cut]
    head = [ln for ln in head if not re.search(r"(Chilean Journal of Statistics|Vol\.|Volume|No\.)", ln, re.I)]

    title_lines = []
    for ln in head:
        if looks_like_authors_line(ln):
            break
        if re.search(AFFI_HINTS, ln, re.I):
            break
        if len(ln.split()) >= 3 and re.match(r"^[A-Z]", ln):
            title_lines.append(ln)
        elif title_lines:
            break
        if len(title_lines) >= 3:
            break

    title = normalize_text(" ".join(title_lines))
    return re.sub(r"\b-\s+\b", "-", title) or "TITLE NOT FOUND"


def extraer_abstract(texto):
    m = re.search(r"(?is)Abstract\s*(.*?)\n\s*Keywords?", texto, re.DOTALL)
    if not m:
        m = re.search(r"(?is)Abstract\.\s*(.*?)\n\s*Keywords?", texto, re.DOTALL)
    return m.group(1).strip() if m else ""


def limpiar_abstract(s: str) -> str:
    if not s:
        return s
    s = normalize_text(s)
    s = re.sub(r"\b-\s+\b", "-", s)
    s = s.replace("R ́enyi", "Rényi").replace("R ´enyi", "Rényi").replace("Renyi", "Rényi")
    s = s.replace("exibility", "flexibility").replace("weighhted", "weighted")
    return s


def extraer_keywords(texto):
    m = re.search(r"(?is)Keywords?\s*:?\s*(.+)", texto)
    kws = []
    if not m:
        return kws
    tail = m.group(1)
    lines = tail.splitlines()
    blob = lines[0]
    if len(lines) > 1 and not re.match(r"(?i)^(abstract|introduction|section|1\.|received)", lines[1].strip()):
        blob += " " + lines[1].strip()

    blob = normalize_text(blob)
    blob = re.sub(r"[;,\u2022\u2027\u2219]+", "·", blob)
    parts = re.split(r"\s*[\u00B7·–—]\s*", blob)
    for p in parts:
        t = normalize_text(p).strip(" .;:-").lower()
        if t:
            kws.append(t)
    return kws
""")

# ----------------------------------------------------------------------
md(r"""## 4. Autores, afiliaciones y país

La parte más delicada del pipeline: vincular cada autor con su afiliación institucional a través de
superíndices numéricos, que el OCR a menudo fragmenta o pierde (Sección 4.1.3.5 y 4.1.4.4 de la tesis).
Una vez identificada la afiliación de cada autor, se infiere el país mediante un diccionario de alias
comunes (USA, UK, Corea, Irán, etc.) y, como respaldo, `pycountry`.
""")

code(r"""
COUNTRY_ALIASES = {
    "usa": "United States", "u.s.a.": "United States", "u.s.": "United States", "us": "United States",
    "uk": "United Kingdom", "u.k.": "United Kingdom", "england": "United Kingdom",
    "scotland": "United Kingdom", "wales": "United Kingdom",
    "korea": "South Korea", "republic of korea": "South Korea",
    "iran": "Iran, Islamic Republic of", "islamic republic of iran": "Iran, Islamic Republic of",
    "turkey": "Turkey", "türkiye": "Turkey",
    "united states of america": "United States",
    "uae": "United Arab Emirates", "u.a.e.": "United Arab Emirates",
}


def extraer_autores_y_afiliaciones(texto):
    lines = [normalize_text(ln) for ln in texto.splitlines() if ln.strip()]

    abs_idx = None
    for i, ln in enumerate(lines):
        if re.match(r"(?i)^abstract\b", ln):
            abs_idx = i; break
    if abs_idx is None:
        for i, ln in enumerate(lines):
            if re.match(r"(?i)^keywords?\b", ln):
                abs_idx = i; break
    header = lines[:abs_idx] if abs_idx is not None else lines[:80]
    header = [h for h in header if not re.search(r"(Chilean Journal of Statistics|Vol\.|Volume|No\.)", h, re.I)]

    author_line_idx = None
    for i, ln in enumerate(header[:20]):
        if looks_like_authors_line(ln):
            author_line_idx = i
            break

    autores = []
    if author_line_idx is not None:
        blob = header[author_line_idx]
        parts = re.split(r",|\b(?:and|y|e)\b", blob, flags=re.I)
        for p in parts:
            p = normalize_text(p)
            if not p or re.search(AFFI_HINTS, p, re.I):
                continue
            m = PERSON_RE.search(p)
            if m:
                name = m.group(0).strip(" ,")
                idx_m = re.search(r"([0-9]{1,2}|[\*\u2020\u2021])\s*$", p)
                autores.append((name, idx_m.group(1) if idx_m else None))

    affi = {}
    for ln in header[author_line_idx+1 if author_line_idx is not None else 0:]:
        if re.search(AFFI_HINTS, ln, re.I):
            m = re.match(r"^\s*([0-9]{1,2}|[\*\u2020\u2021])\s*[\).:-]?\s*(.+)$", ln)
            if m:
                affi[m.group(1)] = normalize_text(m.group(2))
            else:
                affi.setdefault("0", []).append(normalize_text(ln))

    autores_dict = {}
    for nm, idx in autores:
        if idx and idx in affi:
            autores_dict.setdefault(nm, []).append(idx)
        elif "0" in affi:
            autores_dict.setdefault(nm, []).append("0")
        else:
            autores_dict.setdefault(nm, []).append(None)

    afiliacion_map = {k: (" ".join(v) if isinstance(v, list) else v) for k, v in affi.items()}

    if not autores_dict and author_line_idx is not None:
        for nm in PERSON_RE.findall(header[author_line_idx]):
            autores_dict.setdefault(nm, []).append("0" if "0" in afiliacion_map else None)

    return autores_dict, afiliacion_map


def inferir_pais(afiliacion: str) -> str:
    if not afiliacion:
        return ""
    raw = afiliacion.strip()
    low = _strip_accents(raw).lower()

    tail = _strip_accents(raw.split(",")[-1]).strip().lower()
    tail = re.sub(r"[^\w\s\-\.]", " ", tail)
    tail = re.sub(r"\s+", " ", tail).strip()
    if tail in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[tail]

    for alias, canonical in COUNTRY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", low):
            return canonical

    try:
        import pycountry
    except ImportError:
        return ""

    candidates = [t.strip() for t in raw.split(",")[::-1]]
    country_names = {c.name: c for c in pycountry.countries}
    common_names = {getattr(c, "common_name", ""): c for c in pycountry.countries if getattr(c, "common_name", None)}

    for cand in candidates:
        cnorm = _strip_accents(cand).strip().lower()
        for name in list(country_names.keys()) + list(common_names.keys()):
            if name and _strip_accents(name).lower() == cnorm:
                return (common_names.get(name) or country_names[name]).name

    low_noacc = _strip_accents(raw).lower()
    for c in pycountry.countries:
        for nm in {c.name, getattr(c, "common_name", "")}:
            if nm and re.search(rf"\b{re.escape(_strip_accents(nm).lower())}\b", low_noacc):
                return c.name
    return ""
""")

# ----------------------------------------------------------------------
md(r"""## 5. Ejemplo de uso sobre un PDF individual (demostrativo)

Esta celda procesa un único artículo de principio a fin. **Requiere** tener el PDF localmente y
Tesseract/Poppler instalados — no se ejecuta como parte del flujo reproducible de este repositorio,
se deja como referencia de cómo se invoca el pipeline completo.
""")

code(r"""
RUN_DEMO = False  # cambiar a True y ajustar pdf_path si se dispone de un PDF local

if RUN_DEMO:
    pdf_path = "ruta/a/un/articulo.pdf"
    texto = extraer_texto_pdf(pdf_path)

    volumen, numero, fecha, paginas = extraer_volumen_numero_fecha_paginas(texto)
    titulo = extraer_titulo_articulo(texto)
    abstract = limpiar_abstract(extraer_abstract(texto))
    keywords = extraer_keywords(texto)
    autores_dict, afiliacion_map = extraer_autores_y_afiliaciones(texto)

    print(f"Volumen: {volumen} | Número: {numero} | Fecha: {fecha}")
    print(f"Título: {titulo}")
    print(f"Autores: {autores_dict}")
    print(f"Afiliaciones: {afiliacion_map}")
    print(f"Países: {[inferir_pais(a) for a in afiliacion_map.values()]}")
    print(f"Keywords: {keywords}")
    print(f"Abstract (len): {len(abstract)}")
""")

# ----------------------------------------------------------------------
md(r"""## 6. Validación de cobertura sobre el corpus consolidado (reproducible)

El resultado de aplicar este pipeline a los 177 artículos de la revista (Vol. 1 N°1, 2010 — Vol. 16
N°1, 2025) es el JSON consolidado `data/reorganized_data_c_CLEAN_NORMALIZADO.json`. Esta celda —a
diferencia de las anteriores— **sí se ejecuta directamente en este repositorio**, y reproduce las
cifras de cobertura reportadas en la Sección 4.1.5 de la tesis.
""")

code(r"""
with open(DATA_JSON, "r", encoding="utf-8") as f:
    records = json.load(f)

n = len(records)
con_titulo = sum(1 for r in records if r.get("Articulo"))
con_abstract = sum(1 for r in records if r.get("abstract"))
con_keywords = sum(1 for r in records if r.get("keywords"))
con_autores = sum(1 for r in records if r.get("Autores"))

print(f"Artículos en el corpus: {n}")
print(f"Título:    {con_titulo}/{n} ({con_titulo/n:.1%})")
print(f"Abstract:  {con_abstract}/{n} ({con_abstract/n:.1%})")
print(f"Keywords:  {con_keywords}/{n} ({con_keywords/n:.1%})")
print(f"Autores:   {con_autores}/{n} ({con_autores/n:.1%})")
""")

md(r"""**Resultado esperado** (Sección 4.1.5 de la tesis): título 177/177 (100%), abstract 177/177
(100%), palabras clave 175/177 (98.9%), autores con afiliaciones 177/177 (100%). Los dos artículos sin
`keywords` corresponden a números tempranos de la revista donde ese campo no figuraba explícitamente
en el PDF; para el análisis temático (notebook `04_clusterizacion_tematica.ipynb`) el texto de estos
dos artículos se construye igualmente a partir de título + abstract.

**Siguiente paso:** el corpus consolidado aquí validado es el insumo del notebook
`04_clusterizacion_tematica.ipynb` (Objetivo Específico 3) y del notebook
`03_redes_colaboracion.ipynb` (Objetivos Específicos 1 y 2, a partir del campo `Autores`).
""")

nb['cells'] = cells
nb['metadata'] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10"}
}

out_path = "../notebooks/01_extraccion_metadatos.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook escrito en {out_path}")
