# -*- coding: utf-8 -*-
"""
Indicadores temporales de las palabras clave (objetivo específico 1).

Para cada palabra clave se construye su serie anual completa 2010–2025: la proporción de artículos de cada año
que la incluyen, con cero en los años en que no aparece. Sobre esa serie se calculan:

  frecuencia total     suma de las proporciones anuales
  persistencia         número de años en que aparece
  año medio            promedio de los años ponderado por la proporción anual
  año y valor máximos  año de mayor proporción y su valor
  pendiente            pendiente de la regresión lineal de la proporción sobre el año (puntos por año)
  tendencia            modelo lineal generalizado binomial (logit) del número de artículos con la palabra
                       clave sobre el año, con el total de artículos del año como número de ensayos; valores p
                       corregidos por Benjamini–Hochberg. Se ajusta a las palabras clave presentes en tres o más años.

La selección de los temas más relevantes usa un puntaje que pondera en un 70 % la frecuencia total y en un 30 %
la persistencia, ambas reescaladas a [0, 1] para que los pesos correspondan a lo que indican.

Nota: una versión anterior del análisis estimaba las pendientes solo con los años en que la palabra clave
aparecía (sin los ceros) y sumaba la frecuencia y la persistencia en sus escalas originales; ambos puntos se
corrigieron aquí (docs/registro_de_decisiones.md).
"""
import hashlib
import re
import unicodedata
import numpy as np
import pandas as pd

# variantes ortográficas y morfológicas de un mismo término -> forma unificada (720 -> 697 palabras clave)
VARIANTES = {
    "maximum likelihood": ["maximum likelihood estimation", "maximum likelihood method", "maximum likelihood estimators",
                           "maximum likelihood estimator", "maximum-likelihood method", "maximum-likelihood estimation",
                           "maximum-likelihood"],
    "monte carlo simulation": ["monte carlo simulations"], "mean squared error": ["mean square error"],
    "moment": ["moments"], "order statistics": ["order statistic"], "functional data analysis": ["functional data"],
    "geostatistics": ["geostatistic"], "skew-normal distribution": ["skew-normal", "skew normal", "skew normal distribution"],
    "goodness-of-fit": ["goodness-of-fit test", "goodness-of-fit tests", "goodness of fit"], "mcmc": ["mcmc methods"],
    "stochastic representation": ["stochastic representations"], "generalized distributions": ["generalized distribution"],
    "heavy-tailed distributions": ["heavy-tailed distribution"], "generalized linear models": ["generalized linear model"],
    "extreme-value distribution": ["extreme value distribution", "extremes values"],
    "mixture distributions": ["mixture distribution"],
}
UNIFICAR = {v: k for k, vs in VARIANTES.items() for v in vs}
MESES = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}

def _ascii(s):
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii").lower().strip()

def separar(valor):
    """Palabras clave de un artículo: separadas por '·', ';' o ',', en minúsculas sin acentos y sin signos raros."""
    if not isinstance(valor, str):
        return []
    out = []
    for p in re.split(r"[·;,]", valor):
        k = re.sub(r"\s+", " ", re.sub(r"[^\w\s\-\+./]", "", _ascii(p))).strip(" .")
        if len(k) >= 3:
            out.append(k)
    return list(dict.fromkeys(out))

def tablas(base, unificar=True):
    """Tabla de artículos (id, año) y tabla larga artículo-palabra clave, con las variantes unificadas."""
    arts, filas = {}, []
    for r in base:
        titulo = (r.get("Articulo") or r.get("Titulo") or "").strip()
        aid = hashlib.md5(f"{r.get('Volumen')}||{r.get('numero')}||{_ascii(titulo)}".encode("utf-8")).hexdigest()
        if aid in arts:
            continue
        partes = str(r.get("fecha") or "").replace(",", "").split()
        anio = int(re.sub(r"\D", "", partes[1])) if len(partes) >= 2 and _ascii(partes[0]) in MESES else None
        arts[aid] = dict(article_id=aid, year=anio, titulo=titulo)
        filas += [dict(article_id=aid, keyword_std=k) for k in separar(r.get("keywords"))]
    kw = pd.DataFrame(filas)
    if unificar:
        kw["keyword_std"] = kw["keyword_std"].map(lambda k: UNIFICAR.get(k, k))
        kw = kw.drop_duplicates(["article_id", "keyword_std"])
    return pd.DataFrame(list(arts.values())), kw

def tabla_anual(articulos, kw_long, anios=range(2010, 2026)):
    """Conteo y proporción anual por palabra clave, con ceros en los años sin aparición.
    articulos: DataFrame con article_id y year; kw_long: DataFrame con article_id y keyword_std."""
    d = kw_long.merge(articulos[["article_id", "year"]], on="article_id")
    total = d.groupby("year")["article_id"].nunique().reindex(anios, fill_value=0)   # artículos con palabras clave
    cuenta = d.groupby(["keyword_std", "year"])["article_id"].nunique().unstack(fill_value=0)
    cuenta = cuenta.reindex(columns=list(anios), fill_value=0)
    prop = cuenta.div(total.replace(0, np.nan), axis=1).fillna(0)
    return cuenta, prop, total

def metricas(cuenta, prop):
    anios = np.array(prop.columns, dtype=float)
    out = pd.DataFrame(index=prop.index)
    out["frecuencia_total"] = prop.sum(axis=1)
    out["persistencia"] = (cuenta > 0).sum(axis=1)
    out["articulos"] = cuenta.sum(axis=1)
    out["anio_medio"] = (prop * anios).sum(axis=1) / out["frecuencia_total"]
    out["anio_maximo"] = prop.idxmax(axis=1).astype(int)
    out["valor_maximo"] = prop.max(axis=1)
    xc = anios - anios.mean()
    out["pendiente"] = (prop.values * xc).sum(axis=1) / (xc ** 2).sum()             # MCO sobre la serie completa
    return out

def tendencias_glm(cuenta, total, min_anios=3):
    """Pendiente logit y valor p del GLM binomial por palabra clave (presencia en >= min_anios años)."""
    import statsmodels.api as sm
    from statsmodels.stats.multitest import multipletests
    anios = np.array(cuenta.columns, dtype=float)
    X = sm.add_constant(anios - anios.min())
    filas = []
    for kw, y in cuenta.iterrows():
        if (y > 0).sum() < min_anios:
            continue
        n = total.values.astype(float)
        ok = n > 0
        endog = np.column_stack([y.values[ok], n[ok] - y.values[ok]])
        fit = sm.GLM(endog, X[ok], family=sm.families.Binomial()).fit()
        filas.append(dict(keyword_std=kw, pendiente_logit=fit.params[1], p=fit.pvalues[1],
                          dispersion_pearson=fit.pearson_chi2 / fit.df_resid))
    res = pd.DataFrame(filas).set_index("keyword_std")
    res["p_bh"] = multipletests(res["p"], method="fdr_bh")[1]
    return res

def puntaje(m, peso_frecuencia=0.7):
    f = m["frecuencia_total"] / m["frecuencia_total"].max()
    p = m["persistencia"] / m["persistencia"].max()
    return peso_frecuencia * f + (1 - peso_frecuencia) * p

def seleccion(m, n=25, peso_frecuencia=0.7):
    s = puntaje(m, peso_frecuencia)
    # desempate estable: puntaje, luego frecuencia total y orden alfabético
    orden = m.assign(puntaje=s).sort_values(["puntaje", "frecuencia_total"], ascending=False, kind="mergesort")
    return orden.head(n).index.tolist(), orden

def validaciones(m, n=25, umbral_pendiente=None):
    from scipy.stats import spearmanr
    top, orden = seleccion(m, n)
    s = orden["puntaje"]
    rho = {c: spearmanr(s, orden[c])[0] for c in ["frecuencia_total", "persistencia", "pendiente"]}
    t24, _ = seleccion(m, n - 1); t26, _ = seleccion(m, n + 1)
    cambio_24 = 1 - len(set(top) & set(t24)) / len(top)
    cambio_26 = len(set(t26) - set(top)) / len(top)
    # cobertura de tendencias positivas: palabras clave con pendiente positiva y presencia en 3+ años
    pos = m[(m["pendiente"] > (umbral_pendiente or 0)) & (m["persistencia"] >= 3)].index
    cobertura = len(set(pos) & set(top)) / len(pos) if len(pos) else float("nan")
    return dict(rho=rho, cambio_24=cambio_24, cambio_26=cambio_26, n_positivas=len(pos), cobertura_positivas=cobertura)
