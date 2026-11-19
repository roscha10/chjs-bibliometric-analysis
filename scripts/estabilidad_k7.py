# -*- coding: utf-8 -*-
"""Selección de k y estabilidad de la partición de siete grupos (Secciones 4.4.1 y 4.4.3, Anexo C).

Se trabaja sobre el modelo de 177 artículos, el presentado en la defensa y conservado en la tesis; los seis artículos
de la segunda etapa se asignan después al centroide más cercano (scripts/particion_final.py).

Entrada: data/processed/lsa_177.npz (matriz Z de 177 x 176) y data/processed/etiquetas_k7_177.csv
Salida en results/agrupamiento/:
  seleccion_k.csv       Silhouette, Calinski-Harabasz y Davies-Bouldin para k = 3..15 con 25 semillas (media y d. e.),
                        y Silhouette de referencia con cada dimensión de Z permutada al azar (20 réplicas por k)
  bootstrap.csv         ARI de cada una de las 200 réplicas con reposición
  coasociacion.npy      proporción de 500 submuestras (80 %) en que cada par de artículos queda en el mismo grupo
  pac.csv               PAC (co-asociación entre 0,1 y 0,9) para k = 3..15 (200 submuestras)
  dbscan.csv            barrido de DBSCAN (radio 1,00 a 1,35; mínimo 5 vecinos)
  kmeans_ward.csv, k6_k7.csv, k8_k7.csv   tablas de contingencia con otras particiones
  estabilidad_grupos.csv  Jaccard medio (bootstrap) y co-asociación interna de cada grupo (Tabla 4.10)
  resumen_estabilidad.json  cifras para el texto
Tarda entre 15 y 30 minutos. Uso:  python scripts/estabilidad_k7.py
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs import rutas
from chjs.agrupamiento import (kmeans, seleccion_k, silhouette_azar, bootstrap, coasociacion, coasociacion_interna,
                               pac, ward, dbscan_barrido)
from sklearn.cluster import DBSCAN
from sklearn.metrics import adjusted_rand_score

OUT = rutas.AGRUPAMIENTO
Z = np.load(rutas.LSA_177)["Z"]
y0 = pd.read_csv(rutas.ETIQUETAS_177)["cluster"].values
res = {"n": int(Z.shape[0]), "dim": int(Z.shape[1])}
res["reproduccion_ari"] = adjusted_rand_score(y0, kmeans(Z, 7).labels_)

# ----------------------------------------------------------- selección de k (25 semillas) y referencia al azar
ks = range(3, 16)
sel = seleccion_k(Z, ks, range(25))
rng = np.random.default_rng(0)                         # una sola secuencia aleatoria para todos los k
azar = pd.DataFrame([dict(k=k, silhouette_azar=v) for k in ks for v in silhouette_azar(Z, k, 20, rng)])
resumen_k = sel.groupby("k").agg(sil_media=("silhouette", "mean"), sil_de=("silhouette", "std"),
                                 ch_media=("ch", "mean"), ch_de=("ch", "std"), db_media=("db", "mean"),
                                 db_de=("db", "std"))
resumen_k = resumen_k.join(azar.groupby("k").agg(sil_azar_media=("silhouette_azar", "mean"),
                                                 sil_azar_max=("silhouette_azar", "max")))
resumen_k.to_csv(OUT / "seleccion_k.csv")
res.update(silhouette_k7=float(resumen_k.loc[7, "sil_media"]), silhouette_azar_k7=float(resumen_k.loc[7, "sil_azar_media"]),
           k_optimo_ch=int(resumen_k["ch_media"].idxmax()), k_optimo_sil=int(resumen_k["sil_media"].idxmax()),
           k_optimo_db=int(resumen_k["db_media"].idxmin()))
p7 = [kmeans(Z, 7, s).labels_ for s in range(25)]
res["semillas_ari_medio"] = float(np.mean([adjusted_rand_score(a, b) for i, a in enumerate(p7) for b in p7[i + 1:]]))

# ----------------------------------------------------------- bootstrap (200 réplicas)
aris, jaccard = bootstrap(Z, y0)
pd.DataFrame({"replica": range(1, len(aris) + 1), "ari": aris}).to_csv(OUT / "bootstrap.csv", index=False)
res.update(bootstrap_ari_mediana=float(np.median(aris)), bootstrap_ari_media=float(aris.mean()),
           bootstrap_jaccard={g + 1: float(v) for g, v in enumerate(jaccard)})

# ----------------------------------------------------------- co-asociación (k = 7) y PAC por k
C7 = coasociacion(Z, 7, 500, n_init=10)
np.save(OUT / "coasociacion.npy", C7)
interna = coasociacion_interna(C7, y0)
res["coasociacion_interna"] = {g + 1: v for g, v in interna.items()}
pd.DataFrame({"grupo": range(1, 8), "n": np.bincount(y0), "jaccard": jaccard,
              "coasociacion": [interna[g] for g in range(7)]}).to_csv(OUT / "estabilidad_grupos.csv", index=False)
tabla_pac = pd.DataFrame([dict(k=k, pac=pac(coasociacion(Z, k, 200, n_init=5, semilla=k))) for k in ks])
tabla_pac.to_csv(OUT / "pac.csv", index=False)
res["pac"] = {int(r.k): round(r.pac, 3) for r in tabla_pac.itertuples()}

# ----------------------------------------------------------- Ward y DBSCAN
w = ward(Z)
res.update(ward_ari=adjusted_rand_score(y0, w), ward_tamanos=sorted(np.bincount(w).tolist(), reverse=True))
pd.crosstab(y0 + 1, w, rownames=["kmeans"], colnames=["ward"]).to_csv(OUT / "kmeans_ward.csv")
db = dbscan_barrido(Z, y_ref=y0)
db.to_csv(OUT / "dbscan.csv", index=False)
res["dbscan"] = db.to_dict("records")
lab = DBSCAN(eps=1.2, min_samples=5).fit_predict(Z)    # composición de los grupos con radio 1,20
res["dbscan_120_composicion"] = {int(c): pd.Series(y0[lab == c] + 1).value_counts().to_dict() for c in set(lab) if c != -1}

# ----------------------------------------------------------- particiones vecinas (k = 6 y k = 8, semilla 42)
for k in (6, 8):
    pd.crosstab(y0 + 1, kmeans(Z, k).labels_ + 1, rownames=["k7"], colnames=[f"k{k}"]).to_csv(OUT / f"k{k}_k7.csv")
json.dump(res, open(OUT / "resumen_estabilidad.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k != "dbscan"}, ensure_ascii=False, indent=1, default=float))
print(db.to_string(index=False))
print(resumen_k.round(4).to_string())
