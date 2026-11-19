# -*- coding: utf-8 -*-
"""Redes de coautoría (Sección 4.3): construcción, métricas, comunidades y actores centrales.

Entrada: data/processed/base_final.json
Salida:  results/redes/{autores,universidades,paises}.graphml, louvain_<red>.json, centrales_<red>.csv y
         resumen_redes.json (tamaño, densidad, componentes, comunidades, actores destacados y sus vecinos)

Uso:  python scripts/resumen_redes.py
"""
import sys, json
from pathlib import Path
import networkx as nx
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs import rutas
from chjs.redes import construir_redes, resumen, louvain, centrales

OUT = rutas.REDES
EGO = {"autores": ["Gauss M. Cordeiro", "Vera L.D. Tomazella", "Josmar Mazucheli", "Francisco Louzada"],
       "universidades": ["Universidade de São Paulo (Brazil)", "Universidade Federal de Pernambuco (Brazil)",
                         "Pontificia Universidad Católica de Chile (Chile)"],
       "paises": ["Brazil", "Chile", "United States"]}
base = json.load(open(rutas.BASE_FINAL, encoding="utf-8"))
redes, articulos = construir_redes(base)
salida = {}
for red, G in redes.items():
    nx.write_graphml(G, OUT / f"{red}.graphml")
    part = louvain(G)
    json.dump(part, open(OUT / f"louvain_{red}.json", "w", encoding="utf-8"), ensure_ascii=False)
    tabla = centrales(G); tabla.to_csv(OUT / f"centrales_{red}.csv", index=False, encoding="utf-8-sig")
    btw = nx.betweenness_centrality(G, normalized=True)
    s = resumen(G)
    s.update(articulos=articulos[red], tam_comunidades_gigante=sorted(
        __import__("collections").Counter(part[n] for n in max(nx.connected_components(G), key=len)).values(), reverse=True),
        ego={e: dict(grado=G.degree(e), intermediacion=round(btw[e], 4), agrupamiento=round(nx.clustering(G, e), 3),
                     vecinos=sorted(G.neighbors(e), key=lambda v: -G[e][v]["weight"])) for e in EGO[red] if e in G})
    salida[red] = s
    print(f"== {red}: {articulos[red]} artículos, {s['nodos']} nodos, {s['aristas']} aristas, componente gigante "
          f"{s['componente_gigante']} ({100 * s['pct_gigante']:.0f} %), {s['comunidades']} comunidades "
          f"(modularidad {s['modularidad']:.3f}), intermediación nula {s['intermediacion_nula']}")
    print(tabla.head(6).to_string(index=False))
json.dump(salida, open(OUT / "resumen_redes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
