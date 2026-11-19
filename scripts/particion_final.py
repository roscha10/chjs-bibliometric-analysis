# -*- coding: utf-8 -*-
"""Partición temática final de los 183 artículos (Sección 4.4).

El modelo (TF-IDF, LSA y K-means con k = 7) se ajustó sobre el texto de los 177 artículos de la primera etapa y se
reproduce aquí desde data/processed/corpus_177.csv (se verifica que coincida con la partición original). Los seis
artículos de la segunda etapa (Yang et al., 2010, y el Vol. 16, N.º 2, de 2025) se proyectan en el mismo espacio y se
asignan al centroide más cercano. Los grupos se numeran del 1 al 7.

Salida en results/agrupamiento/: particion_183.csv, tamanos_grupos.csv, conteos_grupo_anio.csv,
tendencias_grupos.csv, grupo_por_pais.csv, grupo_por_universidad.csv y resumen_particion.json.
Uso:  python scripts/particion_final.py
"""
import sys, json
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs import rutas
from chjs.corpus import tfidf_lsa
from chjs.agrupamiento import kmeans, tendencias
from sklearn.metrics import adjusted_rand_score

OUT = rutas.AGRUPAMIENTO
NOMBRES = {1: "Distribuciones simétricas y elípticas", 2: "Modelos bayesianos, mixtos y de regresión",
           3: "Pruebas de bondad de ajuste", 4: "Inferencia paramétrica por máxima verosimilitud",
           5: "Estadística espacial", 6: "Muestreo y estimación poblacional", 7: "Control estadístico de procesos"}

c177 = pd.read_csv(rutas.CORPUS_177); c183 = pd.read_csv(rutas.CORPUS_183)
y0 = pd.read_csv(rutas.ETIQUETAS_177)["cluster"].values
_, vect, Z0, svd = tfidf_lsa(c177["text_clean"].fillna("").tolist())
km = kmeans(Z0, 7)
assert adjusted_rand_score(y0, km.labels_) == 1.0, "el modelo no reproduce la partición original"
# los 177 originales conservan su orden; Yang et al. (2010) ocupa la posición 5 y los cinco de 2025 van al final
pos_177 = list(range(5)) + list(range(6, 178))
assert (c183.loc[pos_177, "title"].values == c177["title"].values).all()
nuevos = [5] + list(range(178, 183))
etiqueta = np.full(183, -1); etiqueta[pos_177] = y0
etiqueta[nuevos] = km.predict(svd.transform(vect.transform(c183.loc[nuevos, "text_clean"].fillna(""))))
df = c183[["doc_id", "year", "title"]].copy()
df["grupo"] = etiqueta + 1; df["nombre_grupo"] = df["grupo"].map(NOMBRES)
df["segunda_etapa"] = False; df.loc[nuevos, "segunda_etapa"] = True

# país del artículo: el más frecuente entre sus autores; institución: la del primer autor
base = json.load(open(rutas.BASE_FINAL, encoding="utf-8"))
paises = [Counter(a["pais"] for a in r["Autores"] if a.get("pais")).most_common(1) for r in base]
df["pais"] = [p[0][0] if p else "Sin dato" for p in paises]
df["n_paises"] = [len({a["pais"] for a in r["Autores"] if a.get("pais")}) for r in base]
df["universidad"] = [r["Autores"][0].get("universidad") if r["Autores"] else "Sin dato" for r in base]
df.to_csv(OUT / "particion_183.csv", index=False, encoding="utf-8-sig")

tam = df["grupo"].value_counts().sort_index()
pd.DataFrame({"grupo": tam.index, "nombre": [NOMBRES[g] for g in tam.index], "n": tam.values,
              "pct": (100 * tam.values / len(df)).round(1)}).to_csv(OUT / "tamanos_grupos.csv", index=False)
cont = pd.crosstab(df["year"], df["grupo"]).reindex(np.arange(2010, 2026), fill_value=0)
cont.to_csv(OUT / "conteos_grupo_anio.csv")
tend = tendencias(cont); tend.insert(1, "nombre", tend["grupo"].map(NOMBRES))
tend.to_csv(OUT / "tendencias_grupos.csv", index=False)
pd.crosstab(df["pais"], df["grupo"], margins=True, margins_name="Total").sort_values("Total", ascending=False).to_csv(OUT / "grupo_por_pais.csv")
pd.crosstab(df["universidad"], df["grupo"], margins=True, margins_name="Total").sort_values("Total", ascending=False).to_csv(OUT / "grupo_por_universidad.csv")
res = dict(N=len(df), nucleo=int(tam[[1, 2, 3, 4]].sum()), nucleo_pct=round(100 * tam[[1, 2, 3, 4]].sum() / len(df), 1),
           tamanos={int(k): int(v) for k, v in tam.items()},
           nuevos={str(df.loc[i, "title"])[:60]: int(df.loc[i, "grupo"]) for i in nuevos},
           articulos_un_pais=int((df["n_paises"] == 1).sum()), articulos_internacionales=int((df["n_paises"] >= 2).sum()),
           p_mk_bh_min=float(tend["p_mk_bh"].min()), p_poisson_bh_min=float(tend["p_poisson_bh"].min()),
           p_proporcion_bh_min=float(tend["p_proporcion_bh"].min()), r2_max=float(tend["r2"].max()))
json.dump(res, open(OUT / "resumen_particion.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
print(tend.round(3).to_string(index=False))
