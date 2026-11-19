# -*- coding: utf-8 -*-
"""Figuras de la Sección 4.3 (redes de colaboración), en PDF vectorial para la tesis.

  fig_red_autores.pdf        componente gigante de la red de autores, coloreada por comunidad de Louvain
  fig_ego_autores.pdf        ego-redes de los autores que actúan como ejes: Cordeiro, Mazucheli y Louzada
  fig_red_universidades.pdf  componente gigante de la red de universidades
  fig_red_paises.pdf         red completa de países
  Anexo D:
  fig_anx_red_autores_completa.pdf        red de autores completa: núcleo y componentes periféricas
  fig_anx_red_universidades_completa.pdf  red de universidades completa
  fig_anx_ego_tomazella.pdf               ego-red de Vera L.D. Tomazella (segunda en intermediación)

Colores: las cuatro comunidades mayores llevan azul y verde de la marca más naranja y amarillo (paleta validada
para daltonismo, todos los pares con ΔE >= 8,5); las comunidades menores van en gris. El tamaño del nodo es
proporcional a su grado y el grosor de la arista, al número de artículos compartidos.

Entrada: grafos y particiones de results/redes/ (scripts/resumen_redes.py).
Uso:  python scripts/figuras_redes.py [carpeta_vista_previa]
"""
import sys, json
from pathlib import Path
import numpy as np
import networkx as nx
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs.figuras import estilo, cm, guardar, ANCHO_CM, TINTA, TINTA_SUAVE
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from adjustText import adjust_text

from chjs import rutas
R = rutas.REDES
FIG = rutas.FIGURAS
VISTA = Path(sys.argv[1]) if len(sys.argv) > 1 else None
COMUNIDAD = ["#465DA9", "#e05a1c", "#4CAE7E", "#d1a600"]
OTRAS, ARISTA = "#C8C8C8", "#B5B5B5"
estilo()

UNIV = {   # etiquetas breves de universidades (siglas de uso habitual)
    "Universidade Federal de Pernambuco": "UFPE", "Universidade de São Paulo": "USP",
    "Pontificia Universidad Católica de Chile": "PUC Chile", "Universidade de Brasília": "UnB",
    "Universidade Estadual de Maringá": "UEM", "Universidade Estadual de Campinas": "Unicamp",
    "Universidade Federal de São Carlos": "UFSCar", "Universidade Federal do Rio Grande do Norte": "UFRN",
    "Hacettepe University": "Hacettepe", "Persian Gulf University": "Persian Gulf U.",
    "University of Connecticut": "U. Connecticut", "Universidad de Concepción": "U. de Concepción",
    "Universidade Federal da Bahia": "UFBA", "McMaster University": "McMaster",
    "Universidade Federal do Ceará": "UFC", "Universidade Federal de Minas Gerais": "UFMG",
}
PAIS = {"Brazil": "Brasil", "United States": "Estados Unidos", "Chile": "Chile", "Pakistan": "Pakistán",
        "Turkey": "Turquía", "Iran": "Irán", "China": "China", "Czech Republic": "Chequia", "Australia": "Australia",
        "Canada": "Canadá", "Spain": "España", "Portugal": "Portugal", "UK": "Reino Unido", "Germany": "Alemania",
        "Italy": "Italia", "India": "India", "Argentina": "Argentina", "Peru": "Perú", "Mexico": "México",
        "Colombia": "Colombia", "Belgium": "Bélgica", "Netherlands": "Países Bajos", "New Zealand": "Nueva Zelanda",
        "Egypt": "Egipto", "Saudi Arabia": "Arabia Saudita", "Algeria": "Argelia", "Greece": "Grecia",
        "Venezuela": "Venezuela", "Uruguay": "Uruguay", "Ecuador": "Ecuador", "Honduras": "Honduras",
        "Iraq": "Irak", "Jordan": "Jordania", "Japan": "Japón", "France": "Francia", "Sweden": "Suecia",
        "Denmark": "Dinamarca", "Morocco": "Marruecos", "Tunisia": "Túnez", "Libya": "Libia", "Qatar": "Catar",
        "United Arab Emirates": "Emiratos Árabes Unidos", "Côte d’Ivoire": "Costa de Marfil", "South Korea": "Corea del Sur"}

def grafo(nombre):
    return nx.Graph(nx.read_graphml(R / nombre))

def subgrafo(G, nodos, por_grado=False):
    """Subgrafo con un orden de nodos fijo: el de G o, con por_grado, de mayor a menor grado (empates por nombre).
    G.subgraph() recorre el conjunto de nodos cuando el subgrafo es pequeño, y ese orden cambia entre ejecuciones;
    las disposiciones (Kamada-Kawai, circular) dependen del orden de los nodos."""
    s = set(nodos)
    orden = [n for n in G if n in s]
    if por_grado:
        orden.sort(key=lambda n: (-G.degree(n), n))
    S = nx.Graph()
    S.add_nodes_from(orden)
    S.add_edges_from((u, v, d) for u, v, d in G.edges(data=True) if u in s and v in s)
    return S

def colores(G, red):
    part = json.load(open(R / f"louvain_{red}.json", encoding="utf-8"))
    orden = sorted({part[n] for n in G}, key=lambda c: -sum(1 for n in G if part[n] == c))
    mapa = {c: (COMUNIDAD[i] if i < len(COMUNIDAD) else OTRAS) for i, c in enumerate(orden)}
    tam = [sum(1 for n in G if part[n] == c) for c in orden]
    return [mapa[part[n]] for n in G], tam

def dibujar(G, pos, ax, col, etiquetas, escala=14, base=10, fs=8):
    w = np.array([G[u][v].get("weight", 1) for u, v in G.edges()])
    nx.draw_networkx_edges(G, pos, ax=ax, width=0.5 + 0.8 * (w - 1), edge_color=ARISTA, alpha=0.9)
    deg = dict(G.degree())
    nodos = nx.draw_networkx_nodes(G, pos, ax=ax, node_size=[base + escala * deg[n] for n in G], node_color=col,
                                   edgecolors="white", linewidths=0.8)
    # cada etiqueta parte desplazada hacia afuera de su nodo (en dirección opuesta al promedio de sus vecinos)
    # y unida a él por una línea; luego solo se separan las etiquetas que se superponen entre sí
    xs = np.array([pos[n][0] for n in G]); ys = np.array([pos[n][1] for n in G])
    escala_xy = max(np.ptp(xs), np.ptp(ys))
    txt, tx, ty = [], [], []
    for n, et in etiquetas.items():
        p = np.array(pos[n]); vec = [np.array(pos[v]) for v in G.neighbors(n)]
        d = p - (np.mean(vec, axis=0) if vec else p - 1e-3)
        d = d / (np.linalg.norm(d) or 1)
        q = p + 0.07 * escala_xy * d
        ha = "left" if d[0] >= 0 else "right"
        txt.append(ax.text(q[0], q[1], et, fontsize=fs, color=TINTA, zorder=5, ha=ha, va="center",
                           bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85)))
        tx.append(p[0]); ty.append(p[1])
    if txt:
        # la línea guía se traza al final, desde la posición definitiva de cada etiqueta hasta su propio nodo
        # las etiquetas evitan el área real de cada nodo (no solo su centro) y se separan entre sí
        adjust_text(txt, x=xs, y=ys, target_x=tx, target_y=ty, objects=nodos, ax=ax, expand=(1.15, 1.4),
                    force_text=(0.4, 0.6), force_static=(0.3, 0.45), force_pull=(0.02, 0.02), iter_lim=1500,
                    arrowprops=dict(arrowstyle="-", color="#777777", lw=0.5), min_arrow_len=0)
    ax.set_axis_off()

def leyenda(ax, tam, loc="lower left", titulo=None):
    h = [Line2D([0], [0], marker="o", ls="", markersize=6.5, markerfacecolor=COMUNIDAD[i], markeredgecolor="white",
                label=f"Comunidad {i + 1} ({t})") for i, t in enumerate(tam[:4])]
    if len(tam) > 4:
        h.append(Line2D([0], [0], marker="o", ls="", markersize=6.5, markerfacecolor=OTRAS, markeredgecolor="white",
                        label=f"Otras ({sum(tam[4:])})"))
    # fuera del dibujo, debajo, para no tapar nodos
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=min(len(h), 5), frameon=False,
              fontsize=8, handletextpad=0.3, columnspacing=1.0, title=titulo, title_fontsize=8)

def salida(fig, nombre):
    guardar(fig, FIG / f"{nombre}.pdf", VISTA / f"{nombre}.png" if VISTA else None)

PERIFERIA = "#A3A3A3"

def nucleo_periferia(G, red, etq_nucleo, n_rotulos=4, rotulo=None, escala=14, base=12, alto=17.5, ancho_nucleo=2.0, fs=8):
    """Red completa: arriba el núcleo (componente gigante), coloreado por comunidad; debajo, las componentes
    menores ordenadas de mayor a menor, en filas, en gris. Se rotulan las componentes periféricas mayores."""
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    H = subgrafo(G, comps[0], por_grado=True)
    p = nx.kamada_kawai_layout(H)
    xy = np.array(list(p.values())); xy -= xy.mean(axis=0)
    xy[:, 0] *= ancho_nucleo / np.ptp(xy[:, 0])
    xy[:, 1] *= 0.62 * ancho_nucleo / np.ptp(xy[:, 1])           # el núcleo ocupa un rectángulo de proporción fija
    xy[:, 1] -= xy[:, 1].min()                                   # el núcleo ocupa y >= 0
    pos = dict(zip(p.keys(), xy))
    W = ancho_nucleo * 1.12
    radio = lambda k: 0.026 if k == 2 else (0.034 if k == 3 else 0.04 + 0.025 * np.sqrt(k))
    # empaquetado en filas (de mayor a menor), bajo el núcleo
    y, x, alto_fila, centros, fila = -0.45, -W / 2, 0, {}, 0
    for c in comps[1:]:
        # las componentes rotuladas reservan ancho para su rótulo
        d = max(2 * radio(len(c)) + 0.05, 0.62) if len(centros) < n_rotulos else 2 * radio(len(c)) + 0.05
        if x + d > W / 2:
            y -= alto_fila + 0.05; x, alto_fila, fila = -W / 2, 0, fila + 1
        cen = np.array([x + d / 2, y - radio(len(c))])
        S = subgrafo(G, c)
        q = nx.kamada_kawai_layout(S) if len(c) > 3 else nx.circular_layout(S)
        v = np.array(list(q.values())); v -= v.mean(axis=0)
        v /= max(np.linalg.norm(v, axis=1).max(), 1e-9); v *= radio(len(c))
        for n, w in zip(q.keys(), v):
            pos[n] = cen + w
        centros[frozenset(c)] = cen
        rotulada = len(centros) <= n_rotulos                   # las componentes rotuladas reservan alto para el rótulo
        x += d; alto_fila = max(alto_fila, 2 * radio(len(c)) + (0.17 if rotulada else 0.01))
    col_n, tam = colores(H, red)
    cmap = dict(zip(H.nodes(), col_n))
    col = [cmap.get(n, PERIFERIA) for n in G]
    # alto de la figura proporcional a la extensión del dibujo (escala igual en ambos ejes)
    y_min = min(v[1] for v in pos.values()) - 0.05
    rango_y = (xy[:, 1].max() + 0.18) - y_min
    fig, ax = plt.subplots(figsize=(cm(ANCHO_CM), cm(ANCHO_CM * rango_y / (W + 0.1))))
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)        # sin márgenes: la leyenda queda junto al dibujo
    dibujar(G, pos, ax, col, etq_nucleo, escala=escala, base=base, fs=fs)
    ax.axhline(-0.25, color="#BBBBBB", lw=0.6, ls=(0, (4, 3)), xmin=0.02, xmax=0.98)
    ax.text(-W / 2, -0.32, "Componentes periféricas, de mayor a menor", fontsize=fs, color=TINTA_SUAVE, va="center")
    ax.text(-W / 2, xy[:, 1].max() + 0.05, "Núcleo (componente gigante)", fontsize=fs, color=TINTA_SUAVE, va="bottom")
    for c in comps[1:1 + n_rotulos]:                               # rótulo bajo cada componente periférica mayor
        cen = centros[frozenset(c)]
        ax.text(cen[0], cen[1] - radio(len(c)) - 0.035, rotulo(c), fontsize=fs, color=TINTA_SUAVE, ha="center",
                va="top", style="italic", linespacing=1.0)
    ax.set_xlim(-W / 2 - 0.05, W / 2 + 0.05); ax.set_ylim(y_min, xy[:, 1].max() + 0.18)
    ax.set_aspect("equal")
    h = [Line2D([0], [0], marker="o", ls="", markersize=6.5, markerfacecolor=COMUNIDAD[i], markeredgecolor="white",
                label=f"Núcleo, comunidad {i + 1} ({t})") for i, t in enumerate(tam[:4])]
    if len(tam) > 4:
        h.append(Line2D([0], [0], marker="o", ls="", markersize=6.5, markerfacecolor=OTRAS, markeredgecolor="white",
                        label=f"Núcleo, otras comunidades ({sum(tam[4:])})"))
    h.append(Line2D([0], [0], marker="o", ls="", markersize=6.5, markerfacecolor=PERIFERIA, markeredgecolor="white",
                    label=f"Componentes periféricas ({len(comps) - 1})"))
    fig.legend(handles=h, loc="upper center", ncol=2, frameon=False, fontsize=fs, handletextpad=0.3, columnspacing=1.2,
               bbox_to_anchor=(0.5, 0.0))
    return fig

# ------------------------------------------------------------- autores: componente gigante
G = grafo("autores.graphml")
H = subgrafo(G, max(nx.connected_components(G), key=len), por_grado=True)
pos = nx.kamada_kawai_layout(H)
col, tam = colores(H, "autores")
btw = nx.betweenness_centrality(G)
deg = dict(G.degree())
destacados = sorted(H, key=lambda n: (-deg[n], n))[:9] + sorted(H, key=lambda n: (-btw[n], n))[:6]
etq = {n: n for n in dict.fromkeys(destacados)}
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM), cm(12.5)))
dibujar(H, pos, ax, col, etq, escala=16, base=12)
leyenda(ax, tam)
salida(fig, "fig_red_autores")                               # cuerpo de la tesis: red global (componente gigante)

def rot_autores(c):
    top = sorted(c, key=lambda n: (-deg[n], n))[:3]
    def apellido(n):
        w = n.split()
        return w[-2] if w[-1].rstrip(".") in {"Jr", "Neto", "Filho", "Junior"} else w[-1]
    return ", ".join(apellido(n) for n in top[:2]) + "\n" + f"y otros ({len(c)} autores)"
fig = nucleo_periferia(G, "autores", etq, n_rotulos=4, rotulo=rot_autores, escala=12, base=8, fs=10)
salida(fig, "fig_anx_red_autores_completa")                  # Anexo D: núcleo y componentes periféricas

# ------------------------------------------------------------- autores: ego-redes
def abreviar(n):
    """Primer nombre abreviado a su inicial ('Gauss M. Cordeiro' -> 'G. M. Cordeiro'), para etiquetas más cortas."""
    w = n.split()
    if len(w) >= 2 and not w[0].endswith("."):
        w[0] = w[0][0] + "."
    return " ".join(w)

def ego(ax, G, ego, tit, fs=8):
    vec = sorted(G.neighbors(ego))                     # coautores en orden alfabético, en el sentido antihorario
    E = subgrafo(G, [ego] + vec)
    paso = 2 * np.pi / len(vec)
    ang = np.arange(len(vec)) * paso + paso / 2           # ningún nombre exactamente vertical
    pos = {ego: np.array([0.0, 0.0])} | {v: np.array([np.cos(a), np.sin(a)]) for v, a in zip(vec, ang)}
    w = np.array([E[u][v].get("weight", 1) for u, v in E.edges()])
    nx.draw_networkx_edges(E, pos, ax=ax, width=0.5 + 0.8 * (w - 1), edge_color=ARISTA)
    nx.draw_networkx_nodes(E, pos, ax=ax, nodelist=vec, node_size=30, node_color=COMUNIDAD[2], edgecolors="white", linewidths=0.6)
    nx.draw_networkx_nodes(E, pos, ax=ax, nodelist=[ego], node_size=160, node_color=COMUNIDAD[0], edgecolors="white", linewidths=0.8)
    textos = []
    for v, a in zip(vec, ang):
        x, y = 1.12 * np.cos(a), 1.12 * np.sin(a)
        derecha = np.cos(a) >= 0                       # el texto siempre se aleja del centro
        ha = "left" if derecha else "right"
        rot = np.degrees(a) if derecha else np.degrees(a) + 180
        textos.append(ax.text(x, y, abreviar(v), fontsize=fs, ha=ha, va="center", rotation=rot, rotation_mode="anchor", color=TINTA))
    ax.text(0.5, -0.01, tit, fontsize=9, ha="center", va="top", color=TINTA, transform=ax.transAxes)
    ax.set_aspect("equal"); ax.set_axis_off()
    # límites ajustados a la extensión real de los nombres: el texto mide lo mismo en puntos, por eso se itera
    L = 2.4
    for _ in range(6):
        ax.set_xlim(-L, L); ax.set_ylim(-L, L)
        ax.figure.canvas.draw(); r = ax.figure.canvas.get_renderer(); inv = ax.transData.inverted()
        ext = max(np.abs(inv.transform(t.get_window_extent(r).get_points())).max() for t in textos)
        L = max(ext * 1.02, 1.3)

# cuerpo de la tesis: los tres autores destacados en la defensa (Cordeiro, Mazucheli y Louzada), con letra de 8 pt
ALTO_EGO = 20.5
fig = plt.figure(figsize=(cm(ANCHO_CM), cm(ALTO_EGO)))
lado_a, lado_b = 11.0, ANCHO_CM / 2
ego(fig.add_axes([(1 - lado_a / ANCHO_CM) / 2, 1 - lado_a / ALTO_EGO, lado_a / ANCHO_CM, lado_a / ALTO_EGO]),
    G, "Gauss M. Cordeiro", "a) Gauss M. Cordeiro")
ego(fig.add_axes([0.0, 0.03, 0.5, lado_b / ALTO_EGO]), G, "Josmar Mazucheli", "b) Josmar Mazucheli")
ego(fig.add_axes([0.5, 0.03, 0.5, lado_b / ALTO_EGO]), G, "Francisco Louzada", "c) Francisco Louzada")
salida(fig, "fig_ego_autores")
# Anexo D: ego-red de Vera L.D. Tomazella (segunda en intermediación)
lado = ANCHO_CM * 0.62
fig = plt.figure(figsize=(cm(lado), cm(lado * 1.07)))
ego(fig.add_axes([0, 0.065, 1, 1 / 1.07]), G, "Vera L.D. Tomazella", "Vera L.D. Tomazella")
salida(fig, "fig_anx_ego_tomazella")

# ------------------------------------------------------------- universidades: componente gigante
G = grafo("universidades.graphml")
H = subgrafo(G, max(nx.connected_components(G), key=len), por_grado=True)
pos = nx.kamada_kawai_layout(H)
col, tam = colores(H, "universidades")
btw = nx.betweenness_centrality(G); deg = dict(G.degree())
def corto(n):
    nombre = n.rsplit(" (", 1)[0]
    return UNIV.get(nombre, nombre)
destacados = sorted(H, key=lambda n: (-deg[n], n))[:10] + sorted(H, key=lambda n: (-btw[n], n))[:8]
etq = {n: corto(n) for n in dict.fromkeys(destacados)}
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM), cm(12.5)))
dibujar(H, pos, ax, col, etq, escala=14, base=12)
leyenda(ax, tam)
salida(fig, "fig_red_universidades")                         # cuerpo de la tesis: red global (componente gigante)
def rot_univ(c):
    paises = sorted({PAIS.get(n.rsplit(" (", 1)[1].rstrip(")"), "") for n in c} - {""})
    return f"{len(c)} instituciones\n" + ", ".join(paises)
fig = nucleo_periferia(G, "universidades", etq, n_rotulos=3, rotulo=rot_univ, escala=11, base=8)
salida(fig, "fig_anx_red_universidades_completa")            # Anexo D: núcleo y componentes periféricas

# ------------------------------------------------------------- países: red completa
G = grafo("paises.graphml")
gig = subgrafo(G, max(nx.connected_components(G), key=len))
pos = nx.spring_layout(gig, k=1.6 / np.sqrt(gig.number_of_nodes()), iterations=800, seed=7, weight=None)
otras = [c for c in nx.connected_components(G) if len(c) < max(len(x) for x in nx.connected_components(G))]
for k, c in enumerate(sorted(otras, key=len, reverse=True)):       # componentes menores, en una franja inferior
    sub = nx.circular_layout(subgrafo(G, c), scale=0.12)
    for n, p in sub.items():
        pos[n] = p + np.array([-0.9 + 0.6 * k, -1.45])
col, tam = colores(G, "paises")
etq = {n: PAIS.get(n, n) for n in G}
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM), cm(14.5)))
dibujar(G, pos, ax, col, etq, escala=22, base=14, fs=8)
leyenda(ax, tam, loc="upper left")
salida(fig, "fig_red_paises")
print("figuras en", FIG)
