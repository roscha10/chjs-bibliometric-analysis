"""chjs: análisis bibliométrico, temático y de redes de la Chilean Journal of Statistics (2010–2025).

Módulos:
  descarga       descarga de los PDF desde el sitio oficial de la revista
  ocr            conversión de páginas a imagen y reconocimiento óptico de caracteres
  extraccion     reglas para extraer título, resumen, palabras clave, autores y afiliaciones
  normalizacion  acentos, superíndices, nombres, instituciones y países
  palabras_clave unificación de variantes e indicadores temporales
  redes          redes de coautoría y sus métricas
  agrupamiento   TF-IDF, LSA, K-means, estabilidad y tendencias
  figuras        figuras de la tesis en formato vectorial
"""
__version__ = "2.0.0"
