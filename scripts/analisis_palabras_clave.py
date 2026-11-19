# -*- coding: utf-8 -*-
"""Palabras clave (Sección 4.2): unificación de variantes, indicadores temporales, selección Top-25, validaciones y
pruebas de tendencia.

Entrada: data/processed/base_final.json
Salida:  results/palabras_clave/{metricas.csv, tendencias_glm.csv, top25.csv, proporciones_top25.csv, resumen.json}

Uso:  python scripts/analisis_palabras_clave.py
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs import rutas
from chjs.palabras_clave import tablas, tabla_anual, metricas, tendencias_glm, seleccion, validaciones

OUT = rutas.PALABRAS
base = json.load(open(rutas.BASE_FINAL, encoding="utf-8"))
_, kw0 = tablas(base, unificar=False)
art, kw = tablas(base)
cuenta, prop, total = tabla_anual(art, kw)
m = metricas(cuenta, prop)
glm = tendencias_glm(cuenta, total)
m = m.join(glm)
top, orden = seleccion(m)
val = validaciones(m)
m.sort_values("frecuencia_total", ascending=False).to_csv(OUT / "metricas.csv")
glm.sort_values("p").to_csv(OUT / "tendencias_glm.csv")
orden.head(25).to_csv(OUT / "top25.csv")
prop.loc[top].to_csv(OUT / "proporciones_top25.csv")
res = dict(palabras_clave_antes=int(kw0["keyword_std"].nunique()), palabras_clave_distintas=int(len(m)),
           articulos_con_palabras_clave=int(kw["article_id"].nunique()), pares_articulo_palabra=int(len(kw)),
           una_sola_vez=int((m["articulos"] == 1).sum()), presentes_3_o_mas_anios=int((m["persistencia"] >= 3).sum()),
           glm_modelos=int(len(glm)), glm_min_p=float(glm["p"].min()), glm_min_p_bh=float(glm["p_bh"].min()),
           glm_significativas_bh=int((glm["p_bh"] <= 0.05).sum()), top25=top, validaciones=val)
json.dump(res, open(OUT / "resumen.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k != "top25"}, ensure_ascii=False, indent=1, default=float))
