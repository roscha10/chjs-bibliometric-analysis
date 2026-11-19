# -*- coding: utf-8 -*-
"""Figuras de la Sección 4.4 (estructura temática), en PDF vectorial para la tesis.

  fig_k_seleccion.pdf   métricas internas para k = 3..15 (media y ±1 d. e. sobre 25 semillas); en Silhouette,
                        la referencia del corpus con dimensiones permutadas al azar
  fig_grupos.pdf        tamaño de los siete grupos (183 artículos), núcleo y líneas aplicadas
  fig_coasociacion.pdf  matriz de co-asociación (177 artículos, 500 submuestras), ordenada por grupo
  fig_series_grupos.pdf artículos por año en cada grupo, con el valor p de Mann-Kendall corregido

Entrada: results/agrupamiento/ (scripts/estabilidad_k7.py y scripts/particion_final.py).
Uso:  python scripts/figuras_agrupamiento.py [carpeta_vista_previa]
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs.figuras import estilo, cm, guardar, coma, ANCHO_CM, VERDE, AZUL, TINTA, TINTA_SUAVE, GRILLA, SECUENCIAL
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

from chjs import rutas
A = rutas.AGRUPAMIENTO
FIG = rutas.FIGURAS
VISTA = Path(sys.argv[1]) if len(sys.argv) > 1 else None
estilo()
NOMBRES = {1: "Distribuciones simétricas y elípticas", 2: "Modelos bayesianos, mixtos y de regresión",
           3: "Pruebas de bondad de ajuste", 4: "Inferencia paramétrica por máxima verosimilitud",
           5: "Estadística espacial", 6: "Muestreo y estimación poblacional", 7: "Control estadístico de procesos"}
NUCLEO = {1, 2, 3, 4}

def salida(fig, nombre):
    guardar(fig, FIG / f"{nombre}.pdf", VISTA / f"{nombre}.png" if VISTA else None)

# ------------------------------------------------------------- selección de k
s = pd.read_csv(A / "seleccion_k.csv", index_col=0)
fig, axs = plt.subplots(1, 3, figsize=(cm(ANCHO_CM), cm(6.2)))
paneles = [("sil", "a) Silhouette (mayor es mejor)"), ("ch", "b) Calinski-Harabasz (mayor es mejor)"),
           ("db", "c) Davies-Bouldin (menor es mejor)")]
for ax, (m, tit) in zip(axs, paneles):
    k = s.index.values
    ax.fill_between(k, s[f"{m}_media"] - s[f"{m}_de"], s[f"{m}_media"] + s[f"{m}_de"], color=AZUL, alpha=0.18, lw=0)
    ax.plot(k, s[f"{m}_media"], color=AZUL, lw=1.6, marker="o", markersize=3)
    if m == "sil":
        ax.plot(k, s["sil_azar_media"], color=TINTA_SUAVE, lw=1.1, ls=(0, (3, 2)))
        ax.text(11.5, s.loc[11, "sil_azar_media"] + 0.0025, "corpus permutado", fontsize=8, color=TINTA_SUAVE,
                ha="center", va="bottom")
    ax.axvline(7, color=VERDE, lw=1.0, ls=(0, (2, 2)))
    ax.set_title(tit, fontsize=8.5, loc="left")
    ax.set_xlabel("Número de grupos ($k$)")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=7))
    ax.grid(axis="y", color=GRILLA, lw=0.5)
    dec = 3 if m == "sil" else (1 if m == "db" else 2)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _, d=dec: coma(v, d)))
fig.tight_layout(w_pad=1.0)
salida(fig, "fig_k_seleccion")

# ------------------------------------------------------------- tamaño de los grupos
t = pd.read_csv(A / "tamanos_grupos.csv").sort_values("grupo")
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM - 3.6), cm(6.8)))   # con las etiquetas, mide 15,9 cm
y = np.arange(len(t))[::-1]
col = [AZUL if g in NUCLEO else VERDE for g in t["grupo"]]
ax.barh(y, t["n"], color=col, height=0.62, edgecolor="white", linewidth=1.5)
for yi, (_, r) in zip(y, t.iterrows()):
    ax.text(r["n"] + 0.8, yi, f"{int(r['n'])} ({coma(r['pct'], 1)} %)", va="center", fontsize=8, color=TINTA)
ax.set_yticks(y, [f"{g}. {NOMBRES[g]}" for g in t["grupo"]])
ax.set_xlabel("Artículos")
ax.set_xlim(0, t["n"].max() * 1.22)
ax.grid(axis="x", color=GRILLA, lw=0.5); ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=AZUL, label="Núcleo metodológico (149 artículos; 81,4 %)"),
                   Patch(color=VERDE, label="Líneas aplicadas (34 artículos; 18,6 %)")],
          loc="lower right", frameon=False, fontsize=8)
salida(fig, "fig_grupos")

# ------------------------------------------------------------- co-asociación
C = np.load(A / "coasociacion.npy")
y0 = pd.read_csv(rutas.ETIQUETAS_177)["cluster"].values + 1
orden = np.lexsort((-C.mean(axis=1), y0))              # por grupo y, dentro de él, de más a menos asociado
Co = C[np.ix_(orden, orden)]
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM * 0.78), cm(ANCHO_CM * 0.72)))
im = ax.imshow(Co, cmap=SECUENCIAL, vmin=0, vmax=1, interpolation="nearest")
lim = np.cumsum(np.bincount(y0[orden])[1:])
ini = np.concatenate([[0], lim[:-1]])
for a, b in zip(ini, lim):
    ax.add_patch(plt.Rectangle((a - 0.5, a - 0.5), b - a, b - a, fill=False, ec=TINTA, lw=0.7))
ax.set_xticks((ini + lim) / 2 - 0.5, [str(g) for g in range(1, 8)])
ax.set_yticks((ini + lim) / 2 - 0.5, [str(g) for g in range(1, 8)])
ax.tick_params(length=0)
ax.set_xlabel("Grupo"); ax.set_ylabel("Grupo")
for sp in ax.spines.values():
    sp.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
cb.set_label("Proporción de submuestras en el mismo grupo"); cb.outline.set_visible(False)
cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: coma(v, 1)))
salida(fig, "fig_coasociacion")

# ------------------------------------------------------------- series anuales por grupo
cont = pd.read_csv(A / "conteos_grupo_anio.csv", index_col=0)
tend = pd.read_csv(A / "tendencias_grupos.csv").set_index("grupo")
fig, axs = plt.subplots(4, 2, figsize=(cm(ANCHO_CM), cm(17)), sharex=True)
axs = axs.ravel()
for i, g in enumerate(range(1, 8)):
    ax = axs[i]; serie = cont[str(g)]
    c = AZUL if g in NUCLEO else VERDE
    ax.bar(serie.index, serie.values, color=c, width=0.7, edgecolor="white", linewidth=0.8)
    ax.set_title(f"{g}. {NOMBRES[g]}", fontsize=8, loc="left")
    p = tend.loc[g, "p_mk_bh"]
    ax.text(0.99, 0.95, f"$p$ = {coma(p, 2)}", transform=ax.transAxes, ha="right", va="top", fontsize=8, color=TINTA_SUAVE)
    ax.set_ylim(0, 7.8); ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=4))
    ax.grid(axis="y", color=GRILLA, lw=0.5); ax.set_axisbelow(True)
tot = cont.sum(axis=1)
ax = axs[7]
ax.bar(tot.index, tot.values, color="#9A9A9A", width=0.7, edgecolor="white", linewidth=0.8)
ax.set_title("Total de artículos del año", fontsize=8, loc="left"); ax.set_ylim(0, 15.5)
ax.grid(axis="y", color=GRILLA, lw=0.5); ax.set_axisbelow(True)
for ax in axs[6:]:
    ax.set_xticks(range(2010, 2026, 3)); ax.tick_params(axis="x", labelsize=8)
fig.supylabel("Artículos", fontsize=8.5)
fig.tight_layout(h_pad=0.8, w_pad=1.0)
salida(fig, "fig_series_grupos")
print("figuras en", FIG)
