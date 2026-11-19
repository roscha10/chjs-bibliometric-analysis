# -*- coding: utf-8 -*-
"""
Descarga de los artículos desde el sitio de la revista.

  descargar_pdfs(destino)  recorre el índice de números (https://soche.cl/chjs/issues.html), sigue cada enlace
                           "Download" y guarda el PDF en `destino`, sin volver a descargar los que ya existen.

Los PDF no se incluyen en el repositorio; se guardan en data/raw/ (ver data/raw/README.md).
"""
import time
from pathlib import Path
from urllib.parse import urljoin

URL_INDICE = "https://soche.cl/chjs/issues.html"

def enlaces_pdf(url=URL_INDICE):
    import requests
    from bs4 import BeautifulSoup
    html = requests.get(url, timeout=60).text
    sopa = BeautifulSoup(html, "html.parser")
    return [urljoin(url, a.get("href")) for a in sopa.find_all("a", string="Download") if a.get("href")]

def descargar_pdfs(destino, url=URL_INDICE, pausa=1.0):
    import requests
    destino = Path(destino); destino.mkdir(parents=True, exist_ok=True)
    nuevos = []
    for u in enlaces_pdf(url):
        ruta = destino / u.split("/")[-1]
        if ruta.exists():
            continue
        r = requests.get(u, timeout=120)
        r.raise_for_status()
        ruta.write_bytes(r.content)
        nuevos.append(ruta)
        time.sleep(pausa)                 # pausa entre descargas, por cortesía con el servidor
    return nuevos
