# -*- coding: utf-8 -*-
"""
Utilidades para los cuadernos de notebooks/.

  ejecutar(guion, *args)     corre un guion de scripts/ en un proceso aparte y devuelve lo que imprime
  figuras(guion, nombres)    corre un guion de figuras y muestra en el cuaderno las figuras indicadas

Los guiones se ejecutan en un proceso aparte para que sus variables no se mezclen con las del cuaderno. Las figuras
en PDF quedan en results/figures/ (o en la carpeta de CHJS_FIGURAS); en el cuaderno se muestra una vista en PNG.
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from . import rutas

GUIONES = rutas.RAIZ / "scripts"
VISTA = Path(tempfile.gettempdir()) / "chjs_vista"

def ejecutar(guion, *args):
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(GUIONES / guion), *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", env=entorno)
    if r.returncode:
        raise RuntimeError(f"{guion} terminó con error:\n{r.stderr[-3000:]}")
    return r.stdout

def figuras(guion, nombres, ancho=720):
    from IPython.display import Image, display
    VISTA.mkdir(exist_ok=True)
    ejecutar(guion, VISTA)
    for n in nombres:
        display(Image(filename=str(VISTA / f"{n}.png"), width=ancho))
