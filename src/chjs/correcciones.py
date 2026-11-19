# -*- coding: utf-8 -*-
"""
Base de datos final: aplica a la base de referencia las correcciones verificadas en la validación OCR.

Para cada autor de los 183 artículos:
  - nombre: nombre canónico (acentos reparados, sin superíndices pegados, grafías verificadas contra la imagen del
    PDF y variantes de un mismo autor unificadas; chjs.autores);
  - afiliación original (universidad_raw): acentos reparados y correcciones verificadas por autor;
  - institución (universidad): nombre canónico corregido (chjs.instituciones);
  - país: completado cuando faltaba.
Además, agrega las afiliaciones que faltaban. El título, el resumen y las palabras clave no se modifican, para que la
partición temática siga siendo reproducible.

  construir(base_referencia) -> (base_final, cambios)   cambios: DataFrame con cada modificación
"""
import copy
import pandas as pd
from .autores import nombre_canonico
from .instituciones import canonica_final, PAIS_DE_INSTITUCION
from .normalizacion import reparar_acentos

# afiliación corregida, verificada contra la imagen del PDF: (inicio del título, apellido) -> valores
POR_AUTOR = {
    ("Training school teachers to teach probability", "Díaz"): dict(
        universidad_raw="Departamento de Psicología, Universidad de Huelva, Spain",
        universidad="Universidad de Huelva", pais="Spain"),
}
# afiliaciones que faltaban en la base (verificadas en la imagen)
AGREGAR = {
    ("On an elliptical thin-plate spline", "Moraga"): dict(
        universidad_raw="Instituto de Estadística, Universidad de Valparaíso, Valparaíso, Chile",
        universidad="Universidad de Valparaíso", pais="Chile"),
}
TEXTO = {"Pontificia Universidad Catolica del Perú, Per´": "Pontificia Universidad Catolica del Perú, Perú"}

def raw_limpio(s):
    s = reparar_acentos(s or "")
    for a, b in TEXTO.items():
        s = s.replace(reparar_acentos(a), b)
    return s

def construir(base_referencia):
    base = copy.deepcopy(base_referencia)
    cambios = []

    def anotar(r, campo, antes, despues):
        if (antes or "") != (despues or ""):
            cambios.append(dict(articulo=r["Articulo"][:70], campo=campo, antes=antes, despues=despues))

    for r in base:
        for a in r["Autores"]:
            nombre = nombre_canonico(a["nombre"])
            anotar(r, "nombre", a["nombre"], nombre)
            raw = raw_limpio(a.get("universidad_raw"))
            inst = canonica_final(a.get("universidad"), a.get("universidad_raw")) if a.get("universidad") else a.get("universidad")
            pais = a.get("pais") or PAIS_DE_INSTITUCION.get(inst, a.get("pais"))
            for (titulo, apellido), v in POR_AUTOR.items():
                if r["Articulo"].startswith(titulo) and apellido in nombre:
                    raw, inst, pais = v["universidad_raw"], v["universidad"], v["pais"]
            anotar(r, "universidad", a.get("universidad"), inst)
            anotar(r, "pais", a.get("pais"), pais)
            a.update(nombre=nombre, universidad=inst, universidad_raw=raw, pais=pais)
        # la base repite al autor una vez por afiliación: la afiliación faltante se agrega como una entrada más
        for (titulo, apellido), v in AGREGAR.items():
            if r["Articulo"].startswith(titulo):
                k = next(i for i, a in enumerate(r["Autores"]) if apellido in a["nombre"])
                nombre = r["Autores"][k]["nombre"]
                r["Autores"].insert(k + 1, dict(nombre=nombre, **v))
                anotar(r, "afiliacion_agregada", "", f"{nombre}: {v['universidad_raw']}")
    return base, pd.DataFrame(cambios)

def resumen(base):
    return dict(autores=len({a["nombre"] for r in base for a in r["Autores"]}),
                afiliaciones_originales=len({a["universidad_raw"] for r in base for a in r["Autores"] if a.get("universidad_raw")}),
                instituciones=len({a["universidad"] for r in base for a in r["Autores"] if a.get("universidad")}),
                paises=len({a["pais"] for r in base for a in r["Autores"] if a.get("pais")}))
