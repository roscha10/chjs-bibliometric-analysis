# -*- coding: utf-8 -*-
"""
Agrupamiento temático, selección de k, estabilidad y tendencias (objetivo específico 3).

  kmeans(Z, k)                    K-means con los parámetros de la tesis (50 inicializaciones, 1000 iteraciones, semilla 42)
  asignar(modelo, Zn)             grupo de centroide más cercano para artículos nuevos
  seleccion_k(Z, ks, semillas)    Silhouette, Calinski-Harabasz y Davies-Bouldin por k y semilla
  silhouette_azar(Z, k, n)        Silhouette con cada dimensión de Z permutada al azar (referencia sin estructura)
  bootstrap(Z, y0, B)             ARI y Jaccard por grupo en B réplicas con reposición (alineación húngara)
  coasociacion(Z, k, B)           proporción de submuestras (80 %) en que cada par de artículos queda en el mismo grupo
  pac(C)                          proporción de pares ambiguos (co-asociación entre 0,1 y 0,9)
  dbscan_barrido(Z, radios)       DBSCAN con distintos radios (mínimo 5 vecinos)
  tendencias(conteos)             Mann-Kendall y pendiente de Sen con corrección de Benjamini-Hochberg; Poisson,
                                  cuasi-Poisson y Poisson con el total anual como exposición
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score, adjusted_rand_score

def kmeans(Z, k=7, semilla=42, n_init=50, max_iter=1000):
    return KMeans(k, n_init=n_init, max_iter=max_iter, random_state=semilla).fit(Z)

def asignar(modelo, Zn):
    return modelo.predict(Zn)

def describir(X, Z, modelo, vocabulario, titulos, anios, n_terminos=12):
    """Para cada grupo: términos (raíces) de mayor peso TF-IDF medio y artículo más cercano al centroide."""
    y = modelo.labels_; vocabulario = np.asarray(vocabulario)
    filas = []
    for g in range(modelo.n_clusters):
        idx = np.where(y == g)[0]
        peso = np.asarray(X[idx].mean(axis=0)).ravel()
        rep = idx[np.argmin(np.linalg.norm(Z[idx] - modelo.cluster_centers_[g], axis=1))]
        filas.append(dict(grupo=g + 1, n=len(idx), terminos=", ".join(vocabulario[np.argsort(peso)[::-1][:n_terminos]]),
                          representativo=titulos[rep], anio=int(anios[rep])))
    return pd.DataFrame(filas)

def seleccion_k(Z, ks=range(3, 16), semillas=range(25)):
    filas = []
    for k in ks:
        for s in semillas:
            lab = kmeans(Z, k, s).labels_
            filas.append(dict(k=k, semilla=s, silhouette=silhouette_score(Z, lab),
                              ch=calinski_harabasz_score(Z, lab), db=davies_bouldin_score(Z, lab)))
    return pd.DataFrame(filas)

def silhouette_azar(Z, k=7, n=20, semilla=0):
    """semilla puede ser un entero o un np.random.Generator (para compartir la secuencia entre varios k)."""
    rng = semilla if isinstance(semilla, np.random.Generator) else np.random.default_rng(semilla)
    valores = []
    for r in range(n):
        Zp = np.column_stack([rng.permutation(Z[:, j]) for j in range(Z.shape[1])])
        valores.append(silhouette_score(Zp, kmeans(Zp, k, r).labels_))
    return np.array(valores)

def _alinear(y_ref, y, k):
    from scipy.optimize import linear_sum_assignment
    conf = np.zeros((k, k), dtype=int)
    for t, p in zip(y_ref, y):
        conf[int(t), int(p)] += 1
    fil, col = linear_sum_assignment(conf.max() - conf)
    mapa = {c: f for f, c in zip(fil, col)}
    return np.array([mapa[int(p)] for p in y])

def bootstrap(Z, y0, B=200, k=7, semilla=42, n_init=20, max_iter=500):
    """Réplica del procedimiento de la tesis: muestra con reposición, K-means sobre la muestra, predicción para
    todos los artículos y alineación de etiquetas con el método húngaro. Devuelve el ARI por réplica y el
    índice de Jaccard medio de cada grupo."""
    rng = np.random.default_rng(semilla); N = len(Z)
    aris, jac = [], np.zeros((B, k))
    for b in range(B):
        idx = rng.integers(0, N, size=N)
        km = KMeans(k, n_init=n_init, max_iter=max_iter, random_state=rng.integers(0, 10_000)).fit(Z[idx])
        yb = _alinear(y0, km.predict(Z), k)
        aris.append(adjusted_rand_score(y0, yb))
        for i in range(k):
            a, s = set(np.where(y0 == i)[0]), set(np.where(yb == i)[0])
            jac[b, i] = len(a & s) / len(a | s) if a | s else np.nan
    return np.array(aris), jac.mean(axis=0)

def coasociacion(Z, k=7, B=500, fraccion=0.8, n_init=10, semilla=1):
    rg = np.random.default_rng(semilla); n = len(Z)
    juntos = np.zeros((n, n)); ambos = np.zeros((n, n))
    for b in range(B):
        idx = rg.choice(n, int(fraccion * n), replace=False)
        lab = kmeans(Z[idx], k, b, n_init=n_init).labels_
        I = np.zeros((n, k)); I[idx, lab] = 1
        juntos += I @ I.T
        m = np.zeros(n); m[idx] = 1; ambos += np.outer(m, m)
    return np.divide(juntos, ambos, out=np.zeros_like(juntos), where=ambos > 0)

def coasociacion_interna(C, y):
    out = {}
    for g in np.unique(y):
        ii = np.where(y == g)[0]
        out[int(g)] = float(C[np.ix_(ii, ii)][np.triu_indices(len(ii), 1)].mean())
    return out

def pac(C, bajo=0.1, alto=0.9):
    v = C[np.triu_indices(len(C), 1)]
    return float(np.mean((v > bajo) & (v < alto)))

def ward(Z, k=7):
    return AgglomerativeClustering(k, linkage="ward").fit_predict(Z)

def dbscan_barrido(Z, radios=np.round(np.arange(1.00, 1.36, 0.05), 2), minimo=5, y_ref=None):
    filas = []
    for eps in radios:
        lab = DBSCAN(eps=eps, min_samples=minimo).fit_predict(Z)
        tam = sorted([int((lab == c).sum()) for c in set(lab) if c != -1], reverse=True)
        fila = dict(radio=eps, grupos=len(tam), tamanos=tam, sin_grupo=int((lab == -1).sum()))
        if y_ref is not None:
            fila["ari"] = adjusted_rand_score(y_ref, lab)
        filas.append(fila)
    return pd.DataFrame(filas)

def _p_binomial_negativa(s, X, p_poisson):
    """Valor p de la pendiente con un modelo binomial negativo (dispersión estimada). Si la serie no tiene
    sobredispersión, el estimador no converge (la binomial negativa tiende a la Poisson) y se usa el de Poisson."""
    import warnings
    import statsmodels.api as sm
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = sm.NegativeBinomial(s, X).fit(disp=0).pvalues[1]
        return float(p) if np.isfinite(p) else float(p_poisson)
    except Exception:
        return float(p_poisson)

def tendencias(conteos):
    """conteos: DataFrame con un año por fila y un grupo por columna (incluye los años con cero artículos).
    Mann-Kendall y pendiente de Sen; Poisson, cuasi-Poisson, binomial negativa y Poisson con el total anual como
    exposición. Todos los valores p se corrigen por Benjamini-Hochberg sobre los grupos."""
    import pymannkendall as mk
    import statsmodels.api as sm
    from statsmodels.stats.multitest import multipletests
    anios = conteos.index.values.astype(float)
    total = conteos.sum(axis=1).values
    X = sm.add_constant(anios - anios.mean())
    filas = []
    for g in conteos.columns:
        s = conteos[g].values
        t = mk.original_test(s)
        pois = sm.GLM(s, X, family=sm.families.Poisson()).fit()
        cuasi = sm.GLM(s, X, family=sm.families.Poisson()).fit(scale="X2")
        expo = sm.GLM(s, X, family=sm.families.Poisson(), offset=np.log(total)).fit(scale="X2")
        filas.append(dict(grupo=g, tau=t.Tau, sen=t.slope, p_mk=t.p, p_poisson=pois.pvalues[1],
                          dispersion=pois.pearson_chi2 / pois.df_resid, p_cuasipoisson=cuasi.pvalues[1],
                          p_binomial_negativa=_p_binomial_negativa(s, X, pois.pvalues[1]),
                          p_proporcion=expo.pvalues[1],
                          r2=np.corrcoef(anios, s)[0, 1] ** 2, anio_max=int(anios[s.argmax()]), valor_max=int(s.max())))
    d = pd.DataFrame(filas)
    for c in ("p_mk", "p_poisson", "p_cuasipoisson", "p_binomial_negativa", "p_proporcion"):
        d[c + "_bh"] = multipletests(d[c], method="fdr_bh")[1]
    return d
