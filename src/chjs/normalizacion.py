# -*- coding: utf-8 -*-
"""
normalizacion.py
----------------
Reglas de normalización de la extracción de metadatos (texto OCR y texto de los PDF).

  reparar_acentos(s)        "S˜ao" -> "São", "Mart´ın" -> "Martín", "Bragan¸ca" -> "Bragança"
  limpiar_ocr(s)            ligaduras, guiones de corte, comillas y espacios
  nombre_propio(s)          "EDUARDO NAKANO" -> "Eduardo Nakano", "DE OLIVEIRA" -> "de Oliveira"
  separar_superindices(t)   "VILA!" -> ("VILA", ["1"]), "SAULO!?*" -> ("SAULO", ["1", "2"])
  pais_de(afiliacion)       país a partir del nombre, sus variantes y pistas de ciudad o estado
  institucion_canonica(afiliacion, canon)  nombre canónico (exacto, alias, Jaccard >= 0,6 o inclusión)
"""
import re, unicodedata

# ---------------------------------------------------------------- acentos
ACENTO = {"´": "́", "`": "̀", "˜": "̃", "~": "̃", "ˆ": "̂", "^": "̂",
          "¨": "̈", "ˇ": "̌", "˘": "̆", "˚": "̊"}

def reparar_acentos(s):
    """Une los acentos desprendidos (típicos del texto de PDF generados con LaTeX) con su letra."""
    if not s:
        return s
    s = s.replace("ı", "i")                                   # i sin punto que acompaña al acento
    # espacio espurio antes de un acento desprendido dentro de una palabra: "Guti ´ ´errez"
    s = re.sub(r"(?<=[A-Za-z])\s+(?=[´`˜ˆ¨ˇ˘˚](?:\s*[´`˜ˆ¨ˇ˘˚])*\s?[a-z])", "", s)
    # acento (posiblemente repetido o separado por espacios) seguido de la letra
    s = re.sub(r"([´`˜ˆ¨ˇ˘˚])(?:\s*[´`˜ˆ¨ˇ˘˚])*\s?([A-Za-z])",
               lambda m: unicodedata.normalize("NFC", m.group(2) + ACENTO[m.group(1)]), s)
    s = re.sub(r"¸\s?([cC])", lambda m: "ç" if m.group(1) == "c" else "Ç", s)   # cedilla antepuesta
    s = re.sub(r"([cC])¸", lambda m: "ç" if m.group(1) == "c" else "Ç", s)
    return re.sub(r"\s{2,}", " ", s)

# ---------------------------------------------------------------- limpieza general
def limpiar_ocr(s):
    s = unicodedata.normalize("NFC", s or "")
    for a, b in {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "—": "-", "–": "-",
                 "“": '"', "”": '"', "­": ""}.items():
        s = s.replace(a, b)
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)            # palabra cortada al final de línea
    return reparar_acentos(re.sub(r"[ \t]+", " ", s)).strip()

# ---------------------------------------------------------------- nombres
PARTICULAS = {"de", "da", "do", "dos", "das", "del", "della", "di", "la", "le", "van", "von", "der", "den", "y", "e", "du"}

def nombre_propio(n):
    n = re.sub(r"\s+", " ", (n or "").strip(" ,.;:"))
    letras = [c for c in n if c.isalpha()]
    if letras and sum(c.isupper() for c in letras) > 0.7 * len(letras):       # versalitas o mayúsculas
        partes = []
        for i, w in enumerate(n.split()):
            lw = w.lower()
            if lw in PARTICULAS and 0 < i:
                partes.append(lw)
            elif re.fullmatch(r"[a-z]\.?", lw):
                partes.append(lw.upper().rstrip(".") + ".")
            else:
                partes.append("-".join(x[:1].upper() + x[1:] for x in lw.split("-")))
        n = " ".join(partes)
        n = re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), n)
        n = re.sub(r"\bO'([a-z])", lambda m: "O'" + m.group(1).upper(), n)
    return n

# ---------------------------------------------------------------- superíndices
MAPA_SUPER = {"1": "1", "!": "1", "'": "1", "‘": "1", "’": "1", "`": "1", "|": "1", "¹": "1", "l": "1", "i": "1", "I": "1",
              '"': "1", "“": "1", "”": "1",
              "2": "2", "?": "2", "²": "2", "3": "3", "³": "3", "4": "4", "⁴": "4", "5": "5", "6": "6", "7": "7"}
MARCAS = "!?*'‘’`|¹²³⁴0123456789,†‡§\"“”"

def separar_superindices(tok):
    """Separa las marcas de afiliación pegadas al final de un apellido."""
    # las letras 'l' e 'I' no se tratan como superíndice: son finales legítimos de apellidos
    # frecuentes en el corpus (GUGLIELMI, PAGANONI, BIAZATTI, Amaral, Cabral)
    m = re.match(r"^(.*?[A-Za-zÀ-ÿ\.])([" + re.escape(MARCAS) + r"]*)$", tok)
    if not m:
        return tok, []
    base, marca = m.group(1), m.group(2)
    return base, [MAPA_SUPER[c] for c in marca if c in MAPA_SUPER]

# ---------------------------------------------------------------- países
PAISES = {
    "United States": ["united states", "usa", "u.s.a", "u. s. a", "u.s.", "united states of america"],
    "UK": ["united kingdom", "uk", "u.k", "england", "scotland", "wales", "northern ireland", "great britain"],
    "Brazil": ["brazil", "brasil"], "Chile": ["chile"], "Mexico": ["mexico", "méxico"], "Argentina": ["argentina"],
    "Colombia": ["colombia"], "Peru": ["peru", "perú"], "Venezuela": ["venezuela"], "Uruguay": ["uruguay"],
    "Ecuador": ["ecuador"], "Honduras": ["honduras"], "Spain": ["spain", "españa"], "Portugal": ["portugal"],
    "Italy": ["italy", "italia"], "France": ["france"], "Germany": ["germany", "deutschland"], "Belgium": ["belgium"],
    "Netherlands": ["netherlands", "the netherlands", "holland"], "Denmark": ["denmark"], "Sweden": ["sweden"],
    "Greece": ["greece"], "Czech Republic": ["czech republic", "czechia", "česká republika", "ceska republika"],
    "Turkey": ["turkey", "türkiye", "turkiye"], "Iran": ["iran"], "Iraq": ["iraq"], "India": ["india"],
    "Pakistan": ["pakistan"], "China": ["china", "p.r. china", "pr china"], "Japan": ["japan"],
    "South Korea": ["south korea", "korea", "republic of korea"], "Saudi Arabia": ["saudi arabia"],
    "United Arab Emirates": ["united arab emirates", "uae"], "Qatar": ["qatar"], "Jordan": ["jordan"],
    "Egypt": ["egypt"], "Libya": ["libya"], "Tunisia": ["tunisia"], "Algeria": ["algeria"], "Morocco": ["morocco"],
    "Côte d’Ivoire": ["côte d’ivoire", "cote d'ivoire", "ivory coast"], "Canada": ["canada"],
    "Australia": ["australia"], "New Zealand": ["new zealand"],
}
PISTAS = {   # ciudades o estados que identifican el país cuando este no figura
    "Brazil": ["são paulo", "sao paulo", "rio de janeiro", "recife", "brasília", "brasilia", "campinas", "maringá",
               "maringa", "natal", "manaus", "ribeirão preto", "ribeirao preto", "são carlos", "sao carlos", ", sp", ", rj",
               ", mg", ", pr", ", rs", ", pe", "piracicaba", "salvador", "fortaleza", "curitiba", "porto alegre"],
    "Chile": ["santiago", "valparaíso", "valparaiso", "concepción", "concepcion", "talca", "temuco", "antofagasta", "valdivia"],
    "Mexico": ["ciudad de méxico", "mexico city", "guanajuato", "monterrey"],
    "United States": [", tx", ", ny", ", ca ", ", md", ", nj", ", ct", ", nc", ", fl", "houston", "baltimore"],
}

def _plano(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

def pais_de(afiliacion):
    a = " " + _plano(afiliacion) + " "
    # el país suele ir al final de la afiliación: se busca de derecha a izquierda
    mejor, pos = "", -1
    for pais, vs in PAISES.items():
        for v in vs:
            for m in re.finditer(r"(?<![a-z])" + re.escape(_plano(v)) + r"(?![a-z])", a):
                if m.start() > pos:
                    mejor, pos = pais, m.start()
    if mejor:
        return mejor
    for pais, vs in PISTAS.items():
        if any(_plano(v) in a for v in vs):
            return pais
    return ""

# ---------------------------------------------------------------- instituciones
VACIAS = {"of", "de", "do", "da", "the", "and", "e", "y", "del", "di", "la", "at", "für", "fur", "des"}
ALIAS = {   # variantes de idioma o abreviaturas -> nombre canónico usado en la base
    "university of sao paulo": "Universidade de São Paulo", "universidade de sao paulo": "Universidade de São Paulo",
    "usp": "Universidade de São Paulo", "icmc": "Universidade de São Paulo",
    "federal university of pernambuco": "Universidade Federal de Pernambuco", "ufpe": "Universidade Federal de Pernambuco",
    "university of brasilia": "Universidade de Brasília", "unb": "Universidade de Brasília",
    "state university of maringa": "Universidade Estadual de Maringá", "uem": "Universidade Estadual de Maringá",
    "state university of campinas": "Universidade Estadual de Campinas",
    "university of campinas": "Universidade Estadual de Campinas", "unicamp": "Universidade Estadual de Campinas",
    "federal university of sao carlos": "Universidade Federal de São Carlos", "ufscar": "Universidade Federal de São Carlos",
    "pontificia universidad catolica de chile": "Pontificia Universidad Catolica de Chile",
    "pontifical catholic university of chile": "Pontificia Universidad Catolica de Chile",
}

def _tokens(s):
    return {t for t in re.sub(r"[^a-z0-9 ]", " ", _plano(s)).split() if t not in VACIAS and len(t) > 1}

def institucion_canonica(afiliacion, canon):
    """Asigna el nombre canónico: alias conocido, coincidencia exacta, Jaccard >= 0,6 o inclusión."""
    a = _plano(afiliacion)
    for k, v in ALIAS.items():
        if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", a):
            return v, "alias"
    partes = [p.strip() for p in re.split(r"[,;]", afiliacion) if p.strip()]
    ta_total = _tokens(afiliacion)
    mejor, puntaje, como = "", 0.0, ""
    for c in canon:
        tc = _tokens(c)
        if not tc:
            continue
        for p in partes:
            tp = _tokens(p)
            if not tp:
                continue
            if _plano(p) == _plano(c):
                return c, "exacta"
            j = len(tp & tc) / len(tp | tc)
            if j > puntaje:
                mejor, puntaje, como = c, j, "jaccard"
        if tc <= ta_total and len(tc) >= 2 and 0.6 > puntaje:
            mejor, puntaje, como = c, 0.6, "inclusion"
    return (mejor, como) if puntaje >= 0.6 else ("", "")

if __name__ == "__main__":
    pruebas = ["Universidade de S˜ao Paulo", "Ernesto San Mart´ın", "Carlos Alberto de Bragan¸ca Pereira",
               "Ramon Guti ´ ´errez-Jaimez", "Ulrich Stadtm¨uller", "Leandro Rˆego", "Instituto de Computa¸c˜ao"]
    for p in pruebas:
        print(f"{p!r:45} -> {reparar_acentos(p)!r}")
    for t in ["VILA!", "SAULO!?*", "NAKANO!", "Silva2", "Hill"]:
        print(t, "->", separar_superindices(t))
    for n in ["EDUARDO NAKANO", "JOSÉ DE OLIVEIRA", "M. E. J. NEWMAN", "Gauss M. Cordeiro"]:
        print(n, "->", nombre_propio(n))
    for a in ["Department of Statistics, University of Brasilia, Brasilia, Brazil", "Qminers S.R.O., Praha, Česká Republika",
              "Bristol-Myers Squibb Company, Plainsboro, NJ 08536, U.S.A", "ICMC, Universidade de São Paulo, São Carlos, SP"]:
        print(pais_de(a), "|", a)
