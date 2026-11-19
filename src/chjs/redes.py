# -*- coding: utf-8 -*-
"""
Redes de coautoría (objetivo específico 2).

Para cada artículo se toma el conjunto de sus autores, de sus instituciones (nombre canónico y país, para evitar
homónimos: 'Universidad X (País)') y de sus países. En cada red, los participantes de un mismo artículo quedan
conectados entre sí, y el peso de la arista es el número de artículos que comparten; una institución o un país con
varios autores en un artículo cuenta una sola vez. Solo aportan aristas los artículos con al menos dos
participantes distintos.

  construir_redes(base)   -> {"autores": G, "universidades": G, "paises": G}, {"autores": n_articulos, ...}
  resumen(G)              -> métricas globales y comunidades de Louvain (semilla 42)
  centrales(G, n)         -> tabla de grado e intermediación con sus posiciones
"""
from itertools import combinations
from collections import Counter
import networkx as nx
import pandas as pd

ALIAS_PAIS = {"Brasil": "Brazil", "Estados Unidos": "United States", "EE.UU.": "United States", "USA": "United States",
              "Reino Unido": "United Kingdom", "Países Bajos": "Netherlands", "Alemania": "Germany",
              "República Checa": "Czech Republic", "Turquía": "Turkey", "Irán": "Iran", "Nueva Zelanda": "New Zealand",
              "Corea del Sur": "South Korea"}

def _participantes(registro, red):
    out = []
    for a in registro.get("Autores") or []:
        if red == "autores":
            v = " ".join((a.get("nombre") or "").split())
        elif red == "universidades":
            u, p = (a.get("universidad") or a.get("universidad_raw") or "").strip(), (a.get("pais") or "").strip()
            v = f"{u} ({p})" if u and p else u
        else:
            p = (a.get("pais") or "").strip()
            v = ALIAS_PAIS.get(p, p)
        if v:
            out.append(v)
    return list(dict.fromkeys(out))

def construir_red(base, red):
    """Grafo no dirigido y ponderado de una red; devuelve también el número de artículos que aportan aristas.

    El orden en que se agregan nodos y aristas reproduce el de los programas con que se calcularon las cifras de la
    tesis (la red de autores, en el orden de los artículos; las de universidades y países, de mayor a menor peso).
    El orden no altera las métricas, pero el algoritmo de Louvain, aun con semilla fija, depende de él."""
    G, pesos, n = nx.Graph(), Counter(), 0
    for r in base:
        p = _participantes(r, red)
        if len(p) < 2:
            continue
        n += 1
        if red == "autores":
            for u, v in combinations(p, 2):
                if G.has_edge(u, v):
                    G[u][v]["weight"] += 1
                else:
                    G.add_edge(u, v, weight=1)
        else:
            for u, v in combinations(sorted(set(p)), 2):
                pesos[(u, v)] += 1
    for (u, v), w in sorted(pesos.items(), key=lambda e: (-e[1], e[0][0], e[0][1])):
        G.add_edge(u, v, weight=w)
    return G, n

def construir_redes(base):
    redes, articulos = {}, {}
    for red in ("autores", "universidades", "paises"):
        redes[red], articulos[red] = construir_red(base, red)
    return redes, articulos

def louvain(G, semilla=42):
    import community as community_louvain          # paquete python-louvain
    return community_louvain.best_partition(G, random_state=semilla, weight="weight")

def resumen(G):
    import community as community_louvain
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    part = louvain(G)
    btw = nx.betweenness_centrality(G, normalized=True)
    return dict(nodos=G.number_of_nodes(), aristas=G.number_of_edges(), densidad=nx.density(G),
                grado_medio=2 * G.number_of_edges() / G.number_of_nodes(), transitividad=nx.transitivity(G),
                componentes=len(comps), componente_gigante=len(comps[0]), pct_gigante=len(comps[0]) / G.number_of_nodes(),
                comunidades=len(set(part.values())), modularidad=community_louvain.modularity(part, G, weight="weight"),
                intermediacion_nula=sum(1 for v in btw.values() if v == 0))

def centrales(G, n=10):
    """Actores entre los n primeros por grado o por intermediación (empates de grado por orden alfabético)."""
    deg = dict(G.degree()); btw = nx.betweenness_centrality(G, normalized=True)
    rd = {x: i + 1 for i, x in enumerate(sorted(G, key=lambda x: (-deg[x], x)))}
    rb = {x: i + 1 for i, x in enumerate(sorted(G, key=lambda x: (-btw[x], x)))}
    sel = {x for x in G if rd[x] <= n or rb[x] <= n}
    filas = [dict(actor=x, grado=deg[x], pos_grado=rd[x], intermediacion=round(btw[x], 4), pos_intermediacion=rb[x])
             for x in sel]
    return pd.DataFrame(filas).sort_values(["grado", "intermediacion"], ascending=False).reset_index(drop=True)
