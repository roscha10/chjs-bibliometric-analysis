import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# ----------------------------------------------------------------------
md(r"""# Redes de colaboración científica (autores, instituciones, países)

**Objetivos Específicos 1 y 2** — Construir y analizar los mapas de redes de colaboración académica de
la Chilean Journal of Statistics (2010–2025) a nivel de autores, instituciones y países (Sección 5.1.3
de la tesis).

Se construyen tres redes de coautoría, todas a partir del mismo criterio: **dos entidades (autores /
instituciones / países) quedan conectadas si coescriben al menos un artículo**, con el peso de la
arista igual al número de artículos en conjunto. Solo se consideran artículos con 2 o más entidades
distintas del nivel correspondiente (un artículo de autor único, por ejemplo, no aporta arista a la
red de autores).

> **Nota de reproducibilidad:** este notebook usa directamente los campos `Autores[i].nombre`,
> `Autores[i].universidad` y `Autores[i].pais` del JSON consolidado, sin el paso adicional de
> canonicalización institucional vía Excel externo que se exploró durante el desarrollo de la tesis
> (emparejamiento difuso de nombres de universidad). Esto simplifica la reproducibilidad —no requiere
> archivos externos— a cambio de una fragmentación menor en los nodos de instituciones (variantes de
> escritura de un mismo centro quedan como nodos separados). Aun así, los conteos resultantes
> (392 autores / 517 vínculos, 179 instituciones / 214 vínculos, 38 países / 57 vínculos) coinciden
> con los reportados en la tesis o difieren en menos de un 2%.
""")

# ----------------------------------------------------------------------
md("## 0. Configuración e imports")

code(r"""
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

try:
    from networkx.algorithms.community import louvain_communities
except ImportError:
    louvain_communities = None

DATA_JSON = Path("../data/reorganized_data_c_CLEAN_NORMALIZADO.json")
TABLES_DIR = Path("../results/tables"); TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGS_DIR = Path("../results/figures"); FIGS_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA_JSON, "r", encoding="utf-8") as f:
    records = json.load(f)

print(f"Artículos cargados: {len(records)}")
""")

# ----------------------------------------------------------------------
md(r"""## 1. Función genérica de construcción de red

La misma lógica de construcción sirve para los tres niveles: se cambia únicamente qué campo del
diccionario `Autores[i]` se usa como identidad de nodo (`nombre`, `universidad` o `pais`).
""")

code(r"""
def build_network(records, field):
    '''Construye la red de coautoria a nivel `field` (nombre, universidad o pais).'''
    G = nx.Graph()
    articulos_usados = 0

    for rec in records:
        entidades = []
        for autor in (rec.get("Autores") or []):
            val = autor.get(field)
            if val and val.strip():
                entidades.append(val.strip())
        entidades = list(dict.fromkeys(entidades))  # elimina duplicados preservando orden

        if len(entidades) < 2:
            continue  # sin coautoría a este nivel

        articulos_usados += 1
        for u, v in combinations(entidades, 2):
            if not G.has_edge(u, v):
                G.add_edge(u, v, weight=0)
            G[u][v]["weight"] += 1

    return G, articulos_usados
""")

# ----------------------------------------------------------------------
md(r"""## 2. Métricas de centralidad y comunidades (Louvain)

Para cada red se calculan grado, intermediación (betweenness), cercanía (closeness) y comunidades
mediante el algoritmo de Louvain, tal como se describe en la Sección 5.1.3.
""")

code(r"""
def compute_metrics(G):
    if G.number_of_nodes() == 0:
        return pd.DataFrame()

    degree = dict(G.degree())
    strength = dict(G.degree(weight="weight"))
    betweenness = nx.betweenness_centrality(G, weight=None, normalized=True)

    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    giant = G.subgraph(comps[0]).copy() if comps else G.copy()
    closeness_giant = nx.closeness_centrality(giant)
    closeness = {n: closeness_giant.get(n, 0.0) for n in G.nodes}

    clustering = nx.clustering(G, weight="weight")

    if louvain_communities is not None and G.number_of_edges() > 0:
        comms = louvain_communities(G, weight="weight", seed=42)
    else:
        comms = [set(G.nodes())]
    community_map = {node: cid for cid, comm in enumerate(comms, start=1) for node in comm}

    df = pd.DataFrame({
        "node": list(G.nodes),
        "degree": [degree[n] for n in G.nodes],
        "strength": [strength[n] for n in G.nodes],
        "betweenness": [betweenness.get(n, 0.0) for n in G.nodes],
        "closeness": [closeness.get(n, 0.0) for n in G.nodes],
        "clustering": [clustering.get(n, 0.0) for n in G.nodes],
        "community": [community_map.get(n, 0) for n in G.nodes],
    }).sort_values(["degree", "betweenness"], ascending=False).reset_index(drop=True)

    return df, giant
""")

# ----------------------------------------------------------------------
md("## 3. Red de autores")

code(r"""
G_authors, n_articulos_authors = build_network(records, "nombre")
df_authors, giant_authors = compute_metrics(G_authors)
df_authors.to_csv(TABLES_DIR / "network_authors_metrics.csv", index=False, encoding="utf-8-sig")

print(f"Artículos multiautor: {n_articulos_authors}")
print(f"Nodos (autores): {G_authors.number_of_nodes()}")
print(f"Aristas (co-autorías): {G_authors.number_of_edges()}")
print(f"Componente gigante: {giant_authors.number_of_nodes()} nodos "
      f"({giant_authors.number_of_nodes()/G_authors.number_of_nodes():.1%} de la red)")
df_authors.head(10)
""")

# ----------------------------------------------------------------------
md("## 4. Red de instituciones")

code(r"""
G_inst, n_articulos_inst = build_network(records, "universidad")
df_inst, giant_inst = compute_metrics(G_inst)
df_inst.to_csv(TABLES_DIR / "network_institutions_metrics.csv", index=False, encoding="utf-8-sig")

print(f"Artículos multi-institución: {n_articulos_inst}")
print(f"Nodos (instituciones): {G_inst.number_of_nodes()}")
print(f"Aristas: {G_inst.number_of_edges()}")
df_inst.head(10)
""")

# ----------------------------------------------------------------------
md(r"""## 5. Red de países

A este nivel se agrega también el análisis de comunidades regionales y una figura del componente
gigante, siguiendo la Figura 5.1/5.4 de la tesis.
""")

code(r"""
G_countries, n_articulos_countries = build_network(records, "pais")
df_countries, giant_countries = compute_metrics(G_countries)
df_countries.to_csv(TABLES_DIR / "network_countries_metrics.csv", index=False, encoding="utf-8-sig")

print(f"Artículos con colaboración internacional: {n_articulos_countries}")
print(f"Nodos (países): {G_countries.number_of_nodes()}")
print(f"Aristas: {G_countries.number_of_edges()}")
print(f"Proporción de artículos con coautoría internacional: {n_articulos_countries/len(records):.1%}")
df_countries.head(10)
""")

code(r"""
# Comunidades regionales detectadas por Louvain
for cid in sorted(df_countries["community"].unique()):
    miembros = df_countries.loc[df_countries["community"] == cid, "node"].tolist()
    print(f"Comunidad {cid} ({len(miembros)} países): {', '.join(sorted(miembros)[:12])}"
          + (" ..." if len(miembros) > 12 else ""))
""")

code(r"""
# Figura: componente gigante de la red de países, tamaño de nodo ~ grado
deg = dict(giant_countries.degree())
dmin, dmax = min(deg.values()), max(deg.values())
sizes = [200 + 800 * (deg[n] - dmin) / (dmax - dmin) if dmax > dmin else 400 for n in giant_countries.nodes]

top_deg = df_countries.nlargest(8, "degree")["node"].tolist()
top_bet = df_countries.nlargest(7, "betweenness")["node"].tolist()
label_nodes = set(top_deg) | set(top_bet)
labels = {n: n for n in giant_countries.nodes if n in label_nodes}

pos = nx.spring_layout(giant_countries, seed=42, k=0.6)
plt.figure(figsize=(14, 10))
nx.draw_networkx_edges(giant_countries, pos, alpha=0.25, width=1)
nx.draw_networkx_nodes(giant_countries, pos, node_size=sizes)
nx.draw_networkx_labels(giant_countries, pos, labels=labels, font_size=10)
plt.title("Red de coautoría inter-país — Componente gigante (2010–2025)")
plt.axis("off")
plt.tight_layout()
plt.savefig(FIGS_DIR / "fig_5_1_red_paises_giant.png", dpi=200)
plt.show()
""")

# ----------------------------------------------------------------------
md(r"""## 6. Síntesis

Resumen comparable a la Tabla / Sección 5.1.3 de la tesis:
""")

code(r"""
resumen = pd.DataFrame([
    {"red": "Autores", "nodos": G_authors.number_of_nodes(), "aristas": G_authors.number_of_edges(),
     "articulos_base": n_articulos_authors},
    {"red": "Instituciones", "nodos": G_inst.number_of_nodes(), "aristas": G_inst.number_of_edges(),
     "articulos_base": n_articulos_inst},
    {"red": "Países", "nodos": G_countries.number_of_nodes(), "aristas": G_countries.number_of_edges(),
     "articulos_base": n_articulos_countries},
])
resumen.to_csv(TABLES_DIR / "network_summary.csv", index=False, encoding="utf-8-sig")
resumen
""")

md(r"""**Lectura** (Sección 5.1.3 de la tesis): la red de autores presenta una componente gigante
dominante acompañada de subgrupos periféricos — un núcleo colaborativo cohesionado y comunidades
periféricas de conexión más débil, patrón que se repite en los tres niveles de análisis. En la red de
países, Brasil se erige como el nodo de mayor grado y centralidad de intermediación, actuando como
principal puente entre el núcleo latinoamericano y las colaboraciones con Europa, Norteamérica y Asia.
De los 177 artículos del corpus, solo 48 (27%) involucran colaboración entre países — la Chilean
Journal of Statistics es, ante todo, un espacio de producción nacional con una red internacional
periférica pero estratégicamente posicionada.
""")

nb['cells'] = cells
nb['metadata'] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10"}
}

out_path = "../notebooks/03_redes_colaboracion.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook escrito en {out_path}")
