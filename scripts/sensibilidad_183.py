# -*- coding: utf-8 -*-
"""Análisis de sensibilidad (Sección 4.4.4 y Tabla C.3): se repite el procedimiento completo (TF-IDF, LSA y K-means
con k = 7) sobre los 183 artículos y se compara la partición resultante con la presentada.

Entrada: data/processed/corpus_183.csv y results/agrupamiento/particion_183.csv (scripts/particion_final.py)
Salida en results/agrupamiento/: reajuste_183.csv (grupo de cada artículo en el reajuste),
         sensibilidad_contingencia.csv (filas: grupos presentados 1-7; columnas: grupos del reajuste A-G)
         y resumen_sensibilidad.json
Uso:  python scripts/sensibilidad_183.py
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs import rutas
from chjs.corpus import tfidf_lsa
from chjs.agrupamiento import kmeans
from sklearn.metrics import adjusted_rand_score

OUT = rutas.AGRUPAMIENTO
c183 = pd.read_csv(rutas.CORPUS_183)
final = pd.read_csv(OUT / "particion_183.csv")
assert (final["doc_id"].values == c183["doc_id"].values).all()

X, _, Z, svd = tfidf_lsa(c183["text_clean"].fillna("").tolist())
reajuste = kmeans(Z, 7).labels_
letras = np.array(list("ABCDEFG"))[reajuste]           # los grupos del reajuste no se corresponden con los numerados
pd.DataFrame({"doc_id": c183["doc_id"], "grupo_presentado": final["grupo"], "grupo_reajuste": letras}).to_csv(
    OUT / "reajuste_183.csv", index=False)
tabla = pd.crosstab(final["grupo"], letras, rownames=["grupo_presentado"], colnames=["grupo_reajuste"])
tabla.to_csv(OUT / "sensibilidad_contingencia.csv")
ari = adjusted_rand_score(final["grupo"], reajuste)
res = dict(articulos=int(len(c183)), terminos=int(X.shape[1]), componentes=int(Z.shape[1]),
           varianza_lsa=float(svd.explained_variance_ratio_.sum()), ari=float(ari),
           conservados={int(g): int(fila.max()) for g, fila in tabla.iterrows()},
           tamanos_grupo={int(g): int(fila.sum()) for g, fila in tabla.iterrows()})
json.dump(res, open(OUT / "resumen_sensibilidad.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
print(tabla.to_string())
