# -*- coding: utf-8 -*-
"""Concordancia de la extracción por OCR con la base de referencia (183 artículos, Tabla 4.3 de la tesis).

Entrada: data/interim/ocr_texto.json, data/interim/superindices.json, data/interim/base_referencia.json
Salida:  results/validacion/concordancia.csv (por artículo) y concordancia_resumen.json (primera y dos pasadas)

Uso:  python scripts/probar_extraccion.py [campo] [n]   (con un campo, muestra además los n peores casos)
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs import rutas
from chjs.validacion import comparar, resumen_concordancia

CAMPOS = ["titulo", "resumen", "palabras_clave", "n_autores", "autores", "afiliacion_autor", "pais_autor",
          "afiliaciones_articulo", "paises_articulo"]
ocr = json.load(open(rutas.OCR_TEXTO, encoding="utf-8"))
base = json.load(open(rutas.BASE_REFERENCIA, encoding="utf-8"))
sup = json.load(open(rutas.SUPERINDICES, encoding="utf-8")) if rutas.SUPERINDICES.exists() else None
res = {}
for etiqueta, s in [("primera_pasada", None), ("dos_pasadas", sup)]:
    df = comparar(base, ocr, s)
    res[etiqueta] = {c: round(100 * float(df[c].mean()), 1) for c in CAMPOS}
df.to_csv(rutas.VALIDACION / "concordancia.csv", index=False, encoding="utf-8-sig")
json.dump(res, open(rutas.VALIDACION / "concordancia_resumen.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(resumen_concordancia(df), ensure_ascii=False, indent=1))
print("primera pasada vs. dos pasadas:", json.dumps(res, ensure_ascii=False))
print("emparejamiento mínimo:", df["emparejamiento"].min(), "| archivos repetidos:", df["archivo"].duplicated().sum())
if len(sys.argv) > 1:
    campo = sys.argv[1]
    print(df.sort_values(campo).head(int(sys.argv[2]) if len(sys.argv) > 2 else 8)[["articulo", "archivo", campo]].to_string(index=False))
