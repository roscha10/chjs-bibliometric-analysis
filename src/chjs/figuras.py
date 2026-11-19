# -*- coding: utf-8 -*-
"""
Estilo común de las figuras de la tesis (vectoriales, en PDF).

- Tipografía Calibri, la del texto de la tesis, en 9 pt: legible al ancho final de impresión.
- Ancho de 15,9 cm, el ancho de la caja de texto (A4 con márgenes de 2,54 cm), para que la figura se
  incluya sin reescalar y el tamaño de letra sea el real.
- Sin título dentro de la figura: el número y el título van en la tesis, sobre la figura (APA 7).
- Colores de la marca Kaimind; la pareja verde/azul supera la prueba de separación para daltonismo
  (ΔE 25,3), y cada marca lleva además su etiqueta.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

ANCHO_CM = 15.9
VERDE, AZUL_OSCURO, AZUL, VIOLETA, TURQUESA = "#4CAE7E", "#1F2AA5", "#465DA9", "#635DC2", "#7FD7C3"
TINTA, TINTA_SUAVE, GRILLA = "#1A1A1A", "#555555", "#DDDDDD"
SECUENCIAL = LinearSegmentedColormap.from_list("kaimind_azul", ["#EEF0FA", "#9FA9DE", AZUL, AZUL_OSCURO])

def estilo():
    plt.rcParams.update({
        "font.family": "Calibri", "font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5, "legend.fontsize": 8.5, "axes.edgecolor": TINTA_SUAVE,
        "axes.labelcolor": TINTA, "xtick.color": TINTA_SUAVE, "ytick.color": TINTA_SUAVE,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
        "pdf.fonttype": 42, "svg.fonttype": "none", "figure.dpi": 150, "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03, "axes.formatter.use_locale": False,
    })

def cm(x):
    return x / 2.54

def coma(x, dec=1):
    """Número con coma decimal (convención de la tesis)."""
    return f"{x:.{dec}f}".replace(".", ",")

def etiquetar_puntos(ax, xs, ys, textos, radios_pt, fontsize=8.5, color=TINTA, obstaculos=(),
                     distancias=(2, 5, 9, 14, 20, 28, 38), linea_desde=9, orden=None, fijas=None):
    """Coloca la etiqueta de cada punto sin superponerla a otras etiquetas, a los puntos ni a los obstáculos.

    Para cada punto (primero los más rodeados) evalúa 16 direcciones a distancias crecientes del borde del punto, en
    una o dos líneas, y elige la posición libre más cercana dentro de los ejes, penalizando las líneas guía que cruzan
    otras etiquetas o puntos. Si la etiqueta queda a más de `linea_desde` puntos del borde, la une al punto con una
    línea guía. El resultado es determinista.
    radios_pt: radio de cada punto en puntos tipográficos. obstaculos: Bbox en coordenadas de pantalla (leyendas).
    fijas: {texto: (dx, dy, ha, va)} posiciones forzadas, en puntos desde el centro del punto; se colocan primero.
    """
    fijas = fijas or {}
    import math
    import numpy as np
    from matplotlib.transforms import ScaledTranslation
    fig = ax.figure; fig.canvas.draw(); r = fig.canvas.get_renderer(); k = fig.dpi / 72
    P = ax.transData.transform(np.column_stack([xs, ys]))
    circ = [(p[0], p[1], rad * k) for p, rad in zip(P, radios_pt)]
    ocupados = list(obstaculos); lineas = []; caja = ax.get_window_extent(r)
    dirs = []
    for a in range(0, 360, 22):                                   # 16 direcciones; la alineación sigue al ángulo
        dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
        ha = "left" if dx > 0.3 else ("right" if dx < -0.3 else "center")
        va = "bottom" if dy > 0.3 else ("top" if dy < -0.3 else "center")
        dirs.append((dx, dy, ha, va))
    def choca(bb, c):
        cx, cy = min(max(c[0], bb.x0), bb.x1), min(max(c[1], bb.y0), bb.y1)
        return (cx - c[0]) ** 2 + (cy - c[1]) ** 2 < (c[2] + 1.5 * k) ** 2
    def cruza(p, q, bb):                                          # el segmento p-q atraviesa la caja bb
        for s in np.linspace(0.15, 0.85, 8):
            x, y = p[0] + s * (q[0] - p[0]), p[1] + s * (q[1] - p[1])
            if bb.x0 < x < bb.x1 and bb.y0 < y < bb.y1:
                return True
        return False
    def partir(s):                                                # versión en dos líneas para etiquetas largas
        w = s.split()
        if len(s) < 16 or len(w) < 2:
            return None
        mejor = min(range(1, len(w)), key=lambda c: abs(len(" ".join(w[:c])) - len(" ".join(w[c:]))))
        return " ".join(w[:mejor]) + "\n" + " ".join(w[mejor:])
    if orden is None:                                             # primero los puntos más rodeados
        vec = [sum(1 for c in circ if abs(c[0] - p[0]) < 60 * k and abs(c[1] - p[1]) < 30 * k) for p in P]
        orden = sorted(range(len(xs)), key=lambda i: (-vec[i], -radios_pt[i]))
    for i, txt in enumerate(textos):                              # posiciones forzadas, antes que las demás
        if txt in fijas:
            dx, dy, ha, va = fijas[txt]
            a = ax.annotate(txt, (xs[i], ys[i]), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                            fontsize=fontsize, color=color, zorder=5, linespacing=1.0)
            ocupados.append(a.get_window_extent(r).padded(1.5 * k))
    orden = [i for i in orden if textos[i] not in fijas]
    for i in orden:
        mejor = None
        for txt in [textos[i]] + ([partir(textos[i])] if partir(textos[i]) else []):
            t = ax.text(xs[i], ys[i], txt, fontsize=fontsize, linespacing=1.0)
            for d in distancias:
                for dx, dy, ha, va in dirs:
                    off = radios_pt[i] + d
                    t.set_ha(ha); t.set_va(va)
                    t.set_transform(ax.transData + ScaledTranslation(dx * off / 72, dy * off / 72, fig.dpi_scale_trans))
                    bb = t.get_window_extent(r).padded(1.5 * k)
                    fuera = bb.x0 < caja.x0 or bb.x1 > caja.x1 or bb.y0 < caja.y0 or bb.y1 > caja.y1
                    n = sum(bb.overlaps(o) for o in ocupados) + sum(choca(bb, c) for j, c in enumerate(circ) if j != i)
                    ancla = (P[i][0] + dx * off * k, P[i][1] + dy * off * k)
                    cruces = 0
                    if d >= linea_desde:
                        cruces = sum(cruza(P[i], ancla, o) for o in ocupados) + \
                                 sum(1 for j, c in enumerate(circ) if j != i and cruza(P[i], ancla, __import__("matplotlib").transforms.Bbox.from_extents(c[0] - c[2], c[1] - c[2], c[0] + c[2], c[1] + c[2])))
                    costo = 1000 * (fuera + n) + 60 * cruces + d + (6 if "\n" in txt else 0) + (0 if abs(dy) < 0.5 else 1.5)
                    if mejor is None or costo < mejor[0]:
                        mejor = (costo, txt, d, dx, dy, ha, va, bb, ancla)
            t.remove()
        _, txt, d, dx, dy, ha, va, bb, ancla = mejor
        off = radios_pt[i] + d
        flecha = dict(arrowstyle="-", color="#8A8A8A", lw=0.5, shrinkA=0, shrinkB=radios_pt[i] + 0.5) if d >= linea_desde else None
        ax.annotate(txt, (xs[i], ys[i]), xytext=(dx * off, dy * off), textcoords="offset points", ha=ha, va=va,
                    fontsize=fontsize, color=color, zorder=5, arrowprops=flecha, linespacing=1.0)
        ocupados.append(bb)

def guardar(fig, ruta_pdf, vista_png=None):
    fig.savefig(ruta_pdf)
    if vista_png:
        fig.savefig(vista_png, dpi=150)
    plt.close(fig)
