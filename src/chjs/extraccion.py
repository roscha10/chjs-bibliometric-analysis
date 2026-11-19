# -*- coding: utf-8 -*-
"""
Reglas de extracción de metadatos a partir del texto de un artículo (OCR).

  titulo(texto)          líneas iniciales con mayúscula, antes de autores o afiliaciones
  resumen(texto)         texto entre 'Abstract' y 'Keywords'
  palabras_clave(texto)  línea(s) posteriores a 'Keywords', separadas por ·, ; o ,
  autores_afiliaciones(texto)
      Regla de tres pasos: (1) limpieza; (2) línea de autores: primera línea antes del resumen
      con nombres separados por comas, 'and' o '&' y sin palabras de afiliación; (3) los
      superíndices pegados a cada nombre se traducen con el mapa de confusiones del OCR
      (normalizacion.separar_superindices) y se emparejan con la línea de afiliación que
      comienza con el mismo índice. Una afiliación única se asigna a todos los autores.
  extraer(texto)         todos los campos en un diccionario
"""
import re
from .normalizacion import limpiar_ocr, nombre_propio, separar_superindices, pais_de, MAPA_SUPER, PARTICULAS

AFI = re.compile(r"(?i)\b(universi|department|departament|faculty|facultad|institut|school|college|centre|center|"
                 r"centro|laborat|escola|escuela|program|research|ministry|bank|company|hospital|inc\b|s\.r\.o)")
CABECERA = re.compile(r"(?i)(chilean journal of statistics|^vol(ume)?\.?\s*\d|^doi|research (paper|article)|"
                      r"^short (paper|communication)|^review|special issue|in memory of|issn|copyright|"
                      r"^\(?received|uncorrected proofs|^pages?\s+\d)")

def _lineas(texto):
    return [l for l in (limpiar_ocr(x) for x in texto.splitlines()) if l]

def _corte(lineas):
    return next((i for i, l in enumerate(lineas) if re.match(r"(?i)^abstract\b", l)), len(lineas))

VOCAB_TITULO = re.compile(r"(?i)\b(the|of|for|with|using|via|on|in|to|an|model|models|modeling|modelling|distribution|"
                          r"distributions|regression|test|tests|testing|data|series|family|analysis|estimation|"
                          r"estimator|estimators|charts?|control|sampling|bayesian|inference|method|methods|"
                          r"approach|application|applications|study|new|time|process|processes)\b")
INICIALES = re.compile(r"^\s*(?:[A-ZÀ-Ý]\.\s*-?\s*){1,4}\s*$")
SUP = r"!?*'‘’`|¹²³⁴0-9"                      # caracteres con los que el OCR lee los superíndices de afiliación
INICIO_AFI = re.compile(r"(?:Department|Departamento|Departament|Dept\.|Institute|Instituto|Faculty|Facultad|School|"
                        r"Universi\w*|Escola|Escuela|Centre|Center|Centro|Laborat\w*)\b")

def _preparar_linea_autores(l):
    """Limpia una posible línea de autores leída por OCR:
    - elimina símbolos que el OCR introduce en lugar de letras acentuadas, superíndices o íconos ORCID
      ({, }, ®, %, la 'O' que sigue a un superíndice...) y el 'by' inicial de las cartas al editor;
    - convierte un '&' aislado en 'and' y elimina fragmentos sin letras (superíndices separados: '14', '%&*'),
      conservando la coma que puedan llevar ('SEN! *, IBRAHIM' -> 'SEN!, IBRAHIM');
    - une los pares 'Apellido, Iniciales' ('Case, B.S.1*' -> 'B.S. Case1*')."""
    l = re.sub(r"[{}\[\]®©°º%#@$~<>]", "", l)
    l = re.sub(r"^\s*by\s+", "", l)
    l = re.sub(r"\s&\s", " and ", l)
    l = re.sub(r"(?<=[" + SUP + r"]):|:(?=[" + SUP + r"])", "", l)            # "Martin!:?:3*" -> "Martin!?3*"
    l = re.sub(r"(?<=[!?*'‘’¹²³⁴0-9])O(?=[\s,]|$)", "", l)                     # ícono ORCID leído como 'O'
    l = re.sub(r"\b([A-ZÀ-Ý])\s+\.(?=[\s,]|[" + SUP + r"]|$)", r"\1.", l)      # "Y .3" -> "Y.3"
    # coma leída como punto después de los superíndices: "BUSTAMANTE!?34*. INES" -> "BUSTAMANTE!?34*, INES"
    l = re.sub(r"([!?*'‘’0-9])\.\s+(?=[A-ZÀ-Ý])", r"\1, ", l)
    toks = []
    for t in l.split():
        if re.search(r"[A-Za-zÀ-ÿ]", t) or t in {",", "and"}:
            toks.append(t)
        elif "," in t and toks and not toks[-1].endswith(","):
            toks[-1] += ","
    l = " ".join(toks)
    partes = [p.strip() for p in l.split(",")]
    sin_marcas = [re.sub(r"[!?*'‘’`|¹²³⁴0-9†‡§]", "", p) for p in partes]
    if len(partes) >= 2 and sum(bool(INICIALES.match(s)) for s in sin_marcas[1::2]) >= max(1, len(partes) // 2 - 1):
        unidas = []
        for k in range(0, len(partes) - 1, 2):
            ape, ini = re.sub(r"(?i)^and\s+", "", partes[k]), partes[k + 1]
            marca = re.search(r"[!?*'‘’`|¹²³⁴0-9†‡§]+$", ini)
            ini_limpia = ini[:marca.start()] if marca else ini
            unidas.append(f"{ini_limpia} {ape}{marca.group(0) if marca else ''}")
        if len(partes) % 2:
            unidas.append(partes[-1])
        l = ", ".join(unidas)
    return l

def _es_linea_autores(l):
    if AFI.search(l) or CABECERA.search(l) or len(l) < 5 or len(l.split()) > 45:
        return False
    l = _preparar_linea_autores(l)
    if not l:
        return False
    sin = re.sub(r"[!?*'‘’`|¹²³⁴0-9†‡§\"“”]", "", l)
    piezas = [p for p in re.split(r",|(?i:\band\b)|&", sin) if p.strip()]

    def es_nombre(p):
        # nombre propio: 2 a 6 palabras, la mayoría con mayúscula inicial y sin vocabulario de títulos;
        # admite un segundo apellido entre paréntesis ("Nitu Mehta (Ranka)")
        w = [x.strip("()") for x in p.split() if x.lower() not in PARTICULAS]
        return (re.fullmatch(r"\s*[A-ZÀ-Ý][A-Za-zÀ-ÿ\.\-'() ]{2,60}\s*", p) is not None
                and 2 <= len(p.split()) <= 6 and sum(x[:1].isupper() for x in w) >= 0.75 * len(w)
                and not VOCAB_TITULO.search(p))

    nombres = [p for p in piezas if es_nombre(p)]
    return bool(nombres) and len(nombres) == len(piezas)

CATEGORIA = re.compile(r"^\W*(RESEARCH|REVIEW|INVITED|TEACHING|SHORT|SURVEY|DISCUSSION)\s+(PAPER|ARTICLE|COMMUNICATION)\b|"
                       r"^\W*LETTER TO THE EDITOR\b")

def _es_afiliacion(l):
    """Línea de afiliación (no un título que contiene 'school' o 'research'): empieza como afiliación
    o combina una palabra institucional con comas."""
    return bool(INICIO_AFI.match(l) or _inicio_afiliacion(l) or (AFI.search(l) and "," in l))

def titulo(texto):
    lineas = _lineas(texto)
    cab = _separar_autor_afiliacion(lineas[:_corte(lineas)])
    # el título sigue a la categoría del artículo (RESEARCH PAPER...); el OCR a veces lee antes un bloque
    # del cuerpo del texto, que así se omite
    cat = [k for k, l in enumerate(cab) if CATEGORIA.match(l)]
    cab = [l for l in cab[cat[-1] + 1 if cat else 0:] if not CABECERA.search(l)]
    out = []
    for k, l in enumerate(cab):
        letras = [c for c in l if c.isalpha()]
        if letras and sum(c.isupper() for c in letras) > 0.8 * len(letras) and not out:
            continue                                   # cabeceras en mayúsculas (sección, número especial)
        # la primera línea de texto tras las cabeceras es siempre el título, aunque esté en "Title Case";
        # termina en la línea de autores, en una afiliación o en una línea de superíndices sueltos ("fy 1,2,3,* Z")
        if out and (_autores_en(cab, k) or _es_afiliacion(l) or not re.search(r"[A-Za-zÀ-ÿ]{3,}", l)):
            break
        if not out and _es_afiliacion(l):
            break
        if out or (len(l.split()) >= 2 and re.match(r"^[\"“'‘]?[A-Z0-9]", l)):
            out.append(l)                              # el título continúa (también en minúscula) hasta los autores
        if len(out) >= 4:
            break
    return re.sub(r"\s+", " ", " ".join(out)).strip()

def resumen(texto):
    """Texto entre 'Abstract' y 'Keywords'; si el artículo no tiene palabras clave, hasta la clasificación
    temática o la introducción."""
    m = (re.search(r"(?is)\babstract\.?\s*(.*?)\n\s*key\s?words?\b", texto) or
         re.search(r"(?is)\babstract\.?\s*(.*?)\n\s*(?:mathematics subject|ams subject|jel\b|1\.?\s+introduction\b|"
                   r"introduction\s*\n|\*\s*corresponding author)", texto))
    return re.sub(r"\s+", " ", limpiar_ocr(m.group(1))).strip() if m else ""

def palabras_clave(texto):
    """Palabras clave tras la etiqueta 'Keywords' al inicio de línea (no la palabra 'keywords' dentro del resumen).
    El separador '·' de la revista se lee por OCR como ' - ', ':', '«' o '- ' pegado a la palabra anterior."""
    m = (re.search(r"(?im)^\s*key\s?words?\s*[:.]\s*(.+(?:\n.*){0,3})", texto) or
         re.search(r"(?im)^\s*key\s?words?\s*(.+(?:\n.*){0,3})", texto))
    if not m:
        return []
    lineas = m.group(1).splitlines()
    blob = lineas[0].strip()
    for sig in lineas[1:3]:
        if sig.strip() and not re.match(r"(?i)^\s*(abstract|introduction|1\.|received|mathematics|ams|msc|jel|subject)", sig):
            blob = blob + sig.strip() if blob.endswith("-") and not blob.endswith(" -") else blob + " " + sig.strip()
        else:
            break
    blob = re.sub(r"[;,•‧∙«»]+", "·", limpiar_ocr(blob))
    blob = re.sub(r"\s+-\s+|^\s*-\s+", "·", blob)               # " - " entre términos
    blob = re.sub(r"(?<=[A-Za-zÀ-ÿ])-\s+(?=[A-Za-zÀ-ÿ])", "·", blob)  # "analysis- Change point"
    blob = re.sub(r":\s+", "·", blob)                           # "Correlated pairs: Likelihood ratio test"
    blob = re.sub(r"\.\s+(?=[a-z])", "·", blob)                 # "distribution. cumulative damage"
    return [p.strip(" .;:-").lower() for p in re.split(r"\s*[·–—]\s*", blob) if p.strip(" .;:-")]

def _separar_autor_afiliacion(cab):
    """Separa en dos líneas un autor y su afiliación leídos en la misma línea:
    'Ruth Fuentes-García!* Department of Mathematics, ...' -> 'Ruth Fuentes-García!*' / 'Department of ...'."""
    out = []
    for l in cab:
        m = re.match(r"^(.+?[" + SUP + r"\"“”]+)\s+(" + INICIO_AFI.pattern + r".*)$", l)
        if m and _es_linea_autores(m.group(1)):
            out += [m.group(1), m.group(2)]
        else:
            out.append(l)
    return out

def _inicio_afiliacion(l):
    """Línea que empieza con un índice de afiliación seguido de mayúscula ('‘Department', '2School', '*Gerencia')."""
    return re.match(r"^[" + SUP + r"\"“”]{1,3}\s*[A-ZÀ-Ý]", l) is not None and (AFI.search(l) or pais_de(l))

def _fragmento_nombre(l):
    """Resto de un nombre partido en dos líneas ('Pérez-Rodriguez', 'ZEVIANI!, and ISADORA ...')."""
    return (not AFI.search(l) and not CABECERA.search(l) and not _inicio_afiliacion(l)
            and re.match(r"^[A-ZÀ-Ý][A-Za-zÀ-ÿ\-']+[" + SUP + r"\"“”]*\s*(,|$|\s+and\b)", l) is not None)

def _autores_en(cab, k):
    """Línea de autores en la posición k de la cabecera (sola o completada con un fragmento de nombre en k + 1).
    Devuelve (texto, última línea usada) o None. Un nombre suelto solo cuenta como autor si lleva superíndice
    o si le sigue su afiliación; así, una segunda línea de título como 'Population Variance' no se confunde."""
    l = cab[k]
    sig = cab[k + 1] if k + 1 < len(cab) else ""
    if _es_linea_autores(l):
        unida = False
    elif re.search(r"(?i),|\band\b", l) and sig and _fragmento_nombre(sig) and _es_linea_autores(l + " " + sig):
        l, unida = l + " " + sig, True
    else:
        return None
    sig2 = cab[k + 2] if unida and k + 2 < len(cab) else sig
    if (re.search(r"(?i),|\band\b|&", l) or re.search(r"[!?*'‘’¹²0-9\"“”]\W*$", l)
            or (sig2 and (AFI.search(sig2) or pais_de(sig2)))):              # autor único seguido de su afiliación
        return l, k + 1 if unida else k
    return None

def _cabecera(texto):
    lineas = _lineas(texto)
    return _separar_autor_afiliacion(lineas[:_corte(lineas)])

def _bloque_autores(cab):
    """Ubica la línea (o líneas) de autores en la cabecera: (texto unido, primera línea, última línea) o None."""
    # los autores van después del título: se omiten cabeceras y categorías en mayúsculas iniciales
    def mayus(l):
        le = [c for c in l if c.isalpha()]
        return bool(le) and sum(c.isupper() for c in le) > 0.8 * len(le)
    t0 = next((k for k, l in enumerate(cab) if not CABECERA.search(l) and not mayus(l) and len(l.split()) >= 2), 0)
    ini, hallado = None, None
    for k in range(t0 + 1, len(cab)):
        hallado = _autores_en(cab, k)
        if hallado:
            ini = k
            break
    if hallado is None:
        return None
    bloque, fin = hallado
    i = fin
    # continuación de la línea de autores: tras una coma o 'and' final, si la línea siguiente empieza con 'and'
    # o si completa un nombre partido; se saltan líneas de ruido sin nombres (superíndices sueltos: "1,2,*")
    j = i + 1
    while j < len(cab) and j <= i + 3:
        sig = cab[j]
        if not re.search(r"[A-Za-zÀ-ÿ]{2,}", sig):
            j += 1
            continue
        sigue = ((re.search(r"(?i)(,|\band)\s*$", bloque) or re.match(r"(?i)^and\b", sig)) and
                 (_es_linea_autores(sig) or _es_linea_autores(re.sub(r"(?i)^and\s+", "", sig))))
        if sigue or (_fragmento_nombre(sig) and _es_linea_autores(bloque + " " + sig)):
            bloque += " " + sig
            fin = j
            j += 1
            continue
        break
    return bloque, ini, fin

def lineas_autores(texto):
    """Líneas del texto OCR que forman la línea de autores (las usa la pasada de superíndices)."""
    cab = _cabecera(texto)
    r = _bloque_autores(cab)
    return cab[r[1]:r[2] + 1] if r else []

# índice al inicio de una afiliación: un dígito (no un número: '800 W. Campbell Road' es una dirección)
# o el signo con que el OCR lo leyó
MARCA_AFI = re.compile(r"^((?:[0-9](?![0-9])|[!?'‘’`|¹²³⁴*>\"“”°º§†‡]){1,3})\s?(?=[A-ZÀ-Ý])"
                       r"|^([SBGO])(?=[A-ZÀ-Ý][a-zà-ÿ])")     # dígito leído como letra: 'SGerencia' por '6Gerencia'

def _afiliaciones(lineas):
    """Lista ordenada de afiliaciones [(marca leída o None, texto)] a partir de las líneas que siguen a los autores.
    Abre una afiliación nueva: una línea con marca de índice; o, sin marca, una línea institucional cuando la
    anterior ya terminó (llegó al país). Lo demás continúa la afiliación en curso."""
    entradas = []
    for l in lineas:
        if re.match(r"(?i)^\(?\s*(received|accepted)", l):
            break
        m = MARCA_AFI.match(l)
        completa = bool(entradas) and bool(pais_de(entradas[-1][1]))
        marca = (m.group(1) or m.group(2)) if m else None
        # un índice numérico abre siempre una afiliación ('3Millennium Nucleus ... (MOVI).', sin país);
        # un signo, solo si la línea es institucional o trae país
        if m and (marca[0].isdigit() or AFI.search(l) or pais_de(l)):
            entradas.append([marca, l[m.end():].strip()])
        elif not entradas and (AFI.search(l) or pais_de(l)):          # primera afiliación sin marca ('CNR IMATI, Milano, Italy')
            entradas.append([None, l])
        elif completa and (INICIO_AFI.match(l) or (AFI.search(l) and pais_de(l))):
            entradas.append([None, l])                                 # índice no leído por el OCR
        elif entradas and not re.match(r"(?i)^(e-?mail|corresponding|\*\s*corresponding)", l):
            entradas[-1][1] += " " + l
    return [tuple(e) for e in entradas]

def autores_afiliaciones(texto, superindices=None):
    """Autores con sus afiliaciones y países.

    Las afiliaciones se numeran por orden de aparición (la revista las lista como 1, 2, 3...), de modo que
    un índice leído con otro signo al inicio de la línea ('*Department' por '3Department') no rompe la
    correspondencia. Si se entregan `superindices` (segunda pasada, módulo superindices), sus índices
    reemplazan a los de la primera lectura en los autores cuyo apellido coincide."""
    cab = _cabecera(texto)
    r = _bloque_autores(cab)
    if r is None:
        return [], {}
    bloque, ini, fin = r
    bloque = _preparar_linea_autores(bloque)
    autores = []
    for pieza in [p for p in re.split(r",(?![!?*'‘’¹²0-9])|(?i:\band\b)|&", bloque) if p.strip()]:
        toks = pieza.split()
        base, idx = separar_superindices(toks[-1])
        if not idx and toks[-1].endswith("*"):
            idx = ["*"]
        nombre = re.sub(r"[!?*'‘’`|¹²³⁴†‡§\"“”]", "", " ".join(toks[:-1] + [base])).strip()
        if len(nombre.split()) >= 2:
            autores.append({"nombre": nombre_propio(nombre), "indices": idx})
    if superindices:
        _aplicar_superindices(autores, superindices)
    entradas = _afiliaciones(cab[fin + 1:])
    if len(entradas) == 1:
        afil = {"unica": entradas[0][1]}
    else:
        afil = {str(n): t for n, (_, t) in enumerate(entradas, 1)}
    # marca leída al inicio de la afiliación -> número de orden (para índices de autor leídos con el mismo signo)
    por_marca = {}
    for n, (marca, _) in enumerate(entradas, 1):
        if marca:
            por_marca.setdefault(MAPA_SUPER.get(marca[0], marca[0]), str(n))
    hay_indices = any(a["indices"] for a in autores)
    invalidos = []
    for a in autores:
        claves = []
        for k in a["indices"]:
            c = k if k in afil else por_marca.get(k)
            if c and c not in claves:
                claves.append(c)
            elif not c and k.isdigit():
                invalidos.append(a)               # índice imposible ('9' con ocho afiliaciones)
        if "unica" in afil:
            claves = ["unica"]
        elif not claves and not hay_indices:
            claves = list(afil)                    # sin superíndices: todos los autores comparten las afiliaciones
        a["claves"] = claves
    # toda afiliación listada pertenece al menos a un autor: si queda una sola sin autor y un solo índice
    # imposible, ese índice es esa afiliación mal leída
    sin_autor = [k for k in afil if k != "unica" and not any(k in a["claves"] for a in autores)]
    if len(invalidos) == 1 and len(sin_autor) == 1:
        invalidos[0]["claves"].append(sin_autor[0])
    for a in autores:
        a["afiliaciones"] = [afil[k] for k in sorted(a.pop("claves"), key=lambda k: (len(k), k))]
        a["paises"] = [pais_de(x) for x in a["afiliaciones"]]
    return autores, afil

def _aplicar_superindices(autores, grupos):
    """Asigna a cada autor los índices leídos en la segunda pasada, según el apellido que precede a cada grupo."""
    from rapidfuzz import fuzz
    def plano(s):
        return re.sub(r"[^a-z]", "", s.lower())
    con_digitos = [g for g in grupos if any(c.isdigit() for c in g["indices"])]
    if con_digitos and len(con_digitos) == len(autores):
        # un grupo por autor: la correspondencia es el orden de la línea (no depende de cómo se leyó el apellido)
        for a, g in zip(autores, con_digitos):
            a["indices"] = list(dict.fromkeys(c for c in g["indices"] if c.isdigit()))
        return
    asignados = set()
    for g in grupos:
        digitos = [c for c in g["indices"] if c.isdigit()]
        if not digitos:
            continue
        palabra = plano(re.sub(r"[" + SUP + r"\"“”,.]+$", "", g["palabra"]))
        if len(palabra) < 2:
            continue
        puntajes = [max([fuzz.ratio(palabra, plano(t)) for t in a["nombre"].split()] +
                        [fuzz.ratio(palabra, plano(a["nombre"].split()[-1]))]) for a in autores]
        if not puntajes or max(puntajes) < 75:
            continue
        # ante un empate (dos autores con el mismo apellido: 'von Borries'), el primero aún sin asignar
        empatados = [k for k, p in enumerate(puntajes) if p == max(puntajes)]
        k = next((k for k in empatados if k not in asignados), empatados[0])
        asignados.add(k)
        autores[k]["indices"] = list(dict.fromkeys(digitos))

def extraer(texto, superindices=None):
    autores, afil = autores_afiliaciones(texto, superindices)
    return {"titulo": titulo(texto), "resumen": resumen(texto), "palabras_clave": palabras_clave(texto),
            "autores": autores, "afiliaciones": afil}
