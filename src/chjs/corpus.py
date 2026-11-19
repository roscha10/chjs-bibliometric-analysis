# -*- coding: utf-8 -*-
"""
Texto de cada artículo y su representación vectorial (objetivo específico 3).

  documento(registro)        unión del título, el resumen y las palabras clave
  exclusiones(base)          términos de nombres de autores e instituciones, que se eliminan del texto
  limpiar(texto, ...)        minúsculas, sin acentos, sin palabras vacías (inglés y español) ni exclusiones,
                             raíz de Snowball (inglés)
  tfidf_lsa(textos)          TF-IDF (unigramas y bigramas; frecuencia documental mínima 3 y máxima 95 %;
                             norma L2) y LSA con N - 1 componentes (semilla 42)

El modelo de agrupamiento de la tesis se ajustó sobre el texto limpio de los 177 artículos de la primera etapa
(data/processed/corpus_177.csv). Ese texto se conserva tal como se generó: la lista de exclusiones depende de los
nombres de la base, y una base corregida produciría diferencias mínimas que impedirían reproducir el modelo.
"""
import re
import unicodedata
import numpy as np

PALABRAS_EXTRA = {"et", "al", "via", "doi", "preprint", "article", "study", "journal", "revista", "volume", "issue",
                  "http", "https"}

def sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def tokens(texto):
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", texto)

def palabras_vacias():
    import nltk
    from nltk.corpus import stopwords
    try:
        stopwords.words("english")
    except LookupError:
        nltk.download("stopwords", quiet=True)
    base = set(stopwords.words("english")) | set(stopwords.words("spanish"))
    return {w.lower() for w in base | {sin_acentos(w) for w in base} | PALABRAS_EXTRA}

def exclusiones(base, minimo=2):
    """Términos (normalizados) de los nombres de autores y de las instituciones de la base."""
    nombres = set()
    for r in base:
        for a in r.get("Autores") or []:
            for k in ("nombre", "universidad"):
                if a.get(k):
                    nombres.add(a[k])
    return {sin_acentos(t).lower() for n in nombres for t in tokens(str(n)) if len(t) >= minimo}

def documento(registro):
    return " ".join(x for x in [registro.get("Articulo"), registro.get("abstract"), registro.get("keywords")]
                    if isinstance(x, str) and x)

def limpiar(texto, vacias, excluidas=frozenset(), minimo=2):
    from nltk.stem.snowball import SnowballStemmer
    st = SnowballStemmer("english")
    t = sin_acentos((texto or "").lower())
    salida = [st.stem(w.lower()) for w in tokens(t)
              if len(w) >= minimo and w.lower() not in vacias and w.lower() not in excluidas]
    return " ".join(salida)

def tfidf_lsa(textos, semilla=42):
    """Matriz TF-IDF, vectorizador, representación LSA (N - 1 componentes) y modelo SVD."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    vect = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_df=0.95)
    X = vect.fit_transform(textos)
    svd = TruncatedSVD(n_components=min(200, X.shape[0] - 1), random_state=semilla)
    Z = svd.fit_transform(X)
    return X, vect, Z, svd
