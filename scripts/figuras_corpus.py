# -*- coding: utf-8 -*-
"""Figuras de diagnóstico del corpus textual (Anexo B), en PDF vectorial.

  fig_anx_longitud.pdf  número de términos por documento, después de la limpieza (183 artículos)
  fig_anx_terminos.pdf  los 25 términos presentes en más artículos
  fig_anx_nube.pdf      nube de los 120 términos más frecuentes

Los términos se analizaron por su raíz (Snowball); para que se lean, cada raíz se muestra con la forma completa
más frecuente en el texto original ('distribut' -> 'distribution').
Entrada: data/processed/corpus_183.csv. Uso: python scripts/figuras_corpus.py [carpeta_vista_previa]
"""
import sys, re, json, zlib
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs.figuras import estilo, cm, guardar, coma, ANCHO_CM, AZUL, VERDE, AZUL_OSCURO, VIOLETA, TINTA, TINTA_SUAVE, GRILLA
import matplotlib.pyplot as plt
from nltk.stem.snowball import SnowballStemmer

from chjs import rutas
FIG = rutas.FIGURAS
VISTA = Path(sys.argv[1]) if len(sys.argv) > 1 else None
estilo()
c = pd.read_csv(rutas.CORPUS_183)

# forma completa más frecuente de cada raíz
st = SnowballStemmer("english")
formas = defaultdict(Counter)
for txt in c["text_raw"].fillna(""):
    for w in re.findall(r"[a-záéíóúñ]+", txt.lower()):
        formas[st.stem(w)][w] += 1
legible = lambda r: formas[r].most_common(1)[0][0] if formas[r] else r

def salida(fig, nombre):
    guardar(fig, FIG / f"{nombre}.pdf", VISTA / f"{nombre}.png" if VISTA else None)

# ------------------------------------------------------------- longitud de los documentos
n = c["n_tokens"]
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM), cm(6.5)))
ax.hist(n, bins=np.arange(0, n.max() + 10, 10), color=AZUL, edgecolor="white", linewidth=1.2)
ax.axvline(n.median(), color=VERDE, lw=1.4, ls=(0, (3, 2)))
ax.text(n.median() + 3, ax.get_ylim()[1] * 0.92, f"Mediana: {int(n.median())} términos", color=TINTA, fontsize=8)
ax.set_xlabel("Términos por documento (después de la limpieza)"); ax.set_ylabel("Artículos")
ax.grid(axis="y", color=GRILLA, lw=0.5); ax.set_axisbelow(True)
salida(fig, "fig_anx_longitud")

# ------------------------------------------------------------- términos presentes en más artículos
df = Counter()
for txt in c["text_clean"].fillna(""):
    df.update(set(txt.split()))
top = df.most_common(25)
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM), cm(11)))
y = np.arange(len(top))[::-1]
ax.barh(y, [v for _, v in top], color=AZUL, height=0.65, edgecolor="white")
for yi, (_, v) in zip(y, top):
    ax.text(v + 1, yi, str(v), va="center", fontsize=8, color=TINTA)
ax.set_yticks(y, [legible(r) for r, _ in top], fontsize=8)
ax.set_xlabel("Artículos que contienen el término"); ax.set_xlim(0, top[0][1] * 1.1)
ax.grid(axis="x", color=GRILLA, lw=0.5); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
salida(fig, "fig_anx_terminos")

# ------------------------------------------------------------- nube de palabras
from wordcloud import WordCloud
frec = Counter()
for txt in c["text_clean"].fillna(""):
    frec.update(txt.split())
frec = {legible(r): v for r, v in frec.most_common(120)}
paleta = [AZUL_OSCURO, AZUL, VIOLETA, VERDE]
wc = WordCloud(width=1600, height=900, background_color="white", prefer_horizontal=0.95, random_state=7,
               font_path="C:/Windows/Fonts/calibri.ttf", max_words=120,
               # color fijo por palabra (crc32 no cambia entre ejecuciones, a diferencia de hash())
               color_func=lambda *a, **k: paleta[zlib.crc32(a[0].encode("utf-8")) % len(paleta)]
               ).generate_from_frequencies(frec)
fig, ax = plt.subplots(figsize=(cm(ANCHO_CM), cm(ANCHO_CM * 0.56)))
ax.imshow(wc, interpolation="bilinear"); ax.set_axis_off()
salida(fig, "fig_anx_nube")
json.dump(dict(documentos=int(len(c)), mediana=float(n.median()), media=float(n.mean()), minimo=int(n.min()), maximo=int(n.max()),
               top10=[(legible(r), v) for r, v in top[:10]]),
          open(rutas.AGRUPAMIENTO / "diagnostico_corpus.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("figuras en", FIG, "| mediana", n.median(), "| top", [(legible(r), v) for r, v in top[:8]])
