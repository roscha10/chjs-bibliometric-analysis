# -*- coding: utf-8 -*-
"""Figuras de la Sección 4.2 (palabras clave), en PDF vectorial para la tesis.

  fig_kw_burbujas.pdf   palabras clave presentes en tres o más años: año medio vs. pendiente; tamaño = artículos
  fig_kw_mapa_calor.pdf Top-25: porcentaje anual de artículos que incluyen cada palabra clave, 2010–2025

Entrada: results/palabras_clave/ (scripts/analisis_palabras_clave.py).
Uso:  python scripts/figuras_palabras_clave.py [carpeta_vista_previa]
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs.figuras import estilo, cm, guardar, coma, ANCHO_CM, VERDE, AZUL, TINTA, TINTA_SUAVE, GRILLA, SECUENCIAL
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

from chjs import rutas
R = rutas.PALABRAS
FIG = rutas.FIGURAS
VISTA = Path(sys.argv[1]) if len(sys.argv) > 1 else None
estilo()
m = pd.read_csv(R / "metricas.csv", index_col=0)

# ------------------------------------------------------------- burbujas
from chjs.figuras import etiquetar_puntos
d = m[m["persistencia"] >= 3].copy()
d["pend_pp"] = 100 * d["pendiente"]                       # puntos porcentuales por año
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM), cm(12)))
ax.axhline(0, color=TINTA_SUAVE, lw=0.6, zorder=1)
ax.grid(axis="y", color=GRILLA, lw=0.5, zorder=0)
tam = 18 + 12 * d["articulos"]
col = np.where(d["pend_pp"] > 0, VERDE, AZUL)
ax.scatter(d["anio_medio"], d["pend_pp"], s=tam, c=col, alpha=0.85, edgecolors="white", linewidths=1.2, zorder=3)
ax.set_xlim(2011.9, 2023.9); ax.set_ylim(-0.5, 1.12)
ax.set_xlabel("Año medio de aparición (ponderado por la proporción anual)")
ax.set_ylabel("Pendiente (puntos porcentuales por año)")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: coma(v, 1)))
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
ley_color = [Line2D([0], [0], marker="o", ls="", markersize=7, markerfacecolor=c, markeredgecolor="white", label=l)
             for c, l in [(VERDE, "Pendiente positiva"), (AZUL, "Pendiente negativa")]]
ley_tam = [plt.scatter([], [], s=18 + 12 * n, c="#BBBBBB", edgecolors="white", label=f"{n} artículos") for n in (3, 10, 25)]
l1 = ax.legend(handles=ley_color, loc="upper left", frameon=False, handletextpad=0.3)
ax.add_artist(l1)
l2 = ax.legend(handles=ley_tam, loc="lower right", frameon=False, ncol=1, handletextpad=0.4, labelspacing=0.9,
               borderpad=0.2)
# etiquetas: cada una en la primera posición libre alrededor de su punto (sin superposiciones)
fig.canvas.draw(); rend = fig.canvas.get_renderer()
etiquetar_puntos(ax, d["anio_medio"].values, d["pend_pp"].values, list(d.index), list(np.sqrt(tam.values) / 2),
                 fontsize=8.5, obstaculos=[l1.get_window_extent(rend), l2.get_window_extent(rend)],
                 fijas={"mcmc": (0, -6, "center", "top")})          # justo debajo de su punto, sin ambigüedad
guardar(fig, FIG / "fig_kw_burbujas.pdf", VISTA / "fig_kw_burbujas.png" if VISTA else None)

# ------------------------------------------------------------- mapa de calor
top = pd.read_csv(R / "top25.csv", index_col=0).index.tolist()
prop = pd.read_csv(R / "proporciones_top25.csv", index_col=0).loc[top]
orden = m.loc[top].sort_values("anio_medio").index                # filas en orden cronológico
P = 100 * prop.loc[orden]
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM - 1.6), cm(13.5)))   # con las etiquetas, mide 15,9 cm
datos = np.ma.masked_where(P.values == 0, P.values)
cmap = SECUENCIAL.copy(); cmap.set_bad("white")
im = ax.pcolormesh(datos, cmap=cmap, vmin=0, vmax=P.values.max(), edgecolors="white", linewidth=1.0)
ax.set_xticks(np.arange(P.shape[1]) + 0.5, [str(c) for c in P.columns], rotation=90)
ax.set_yticks(np.arange(P.shape[0]) + 0.5, P.index)
ax.invert_yaxis()
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xlabel("Año")
cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
cb.set_label("Porcentaje de artículos del año")
cb.outline.set_visible(False)
cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
guardar(fig, FIG / "fig_kw_mapa_calor.pdf", VISTA / "fig_kw_mapa_calor.png" if VISTA else None)
print("figuras en", FIG)
