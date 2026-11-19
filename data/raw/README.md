# data/raw

Carpeta para los PDF de los artículos de la *Chilean Journal of Statistics* (2010–2025). Los PDF no se incluyen
en el repositorio: son publicaciones de la revista y se descargan desde su sitio oficial.

```python
from chjs.descarga import descargar_pdfs
descargar_pdfs("data/raw")
```

Los notebooks no necesitan los PDF: trabajan con el texto OCR ya procesado (`data/interim/ocr_texto.json`) y con
la base final (`data/processed/base_final.json`). Los PDF solo son necesarios para repetir el OCR
(`scripts/ocr_superindices.py`, `chjs.ocr`) o para revisar la muestra de referencia contra la imagen.
