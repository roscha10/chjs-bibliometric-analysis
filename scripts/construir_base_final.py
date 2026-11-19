# -*- coding: utf-8 -*-
"""Construye la base de datos final a partir de la base de referencia y de las correcciones verificadas en la
validación OCR (chjs.correcciones; registro de decisiones del 17 de noviembre de 2026).

Entrada: data/interim/base_referencia.json
Salida:  data/processed/base_final.json y results/validacion/cambios_base_final.csv

Uso:  python scripts/construir_base_final.py
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chjs import rutas
from chjs.correcciones import construir, resumen

ref = json.load(open(rutas.BASE_REFERENCIA, encoding="utf-8"))
base, cambios = construir(ref)
json.dump(base, open(rutas.BASE_FINAL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
cambios.to_csv(rutas.VALIDACION / "cambios_base_final.csv", index=False, encoding="utf-8-sig")
print("cambios por campo:", cambios.groupby("campo").size().to_dict())
print(resumen(base))
