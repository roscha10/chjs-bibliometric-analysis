# -*- coding: utf-8 -*-
"""
Nombre canónico de cada autor (revisión manual, noviembre de 2026).

En la red de coautoría cada nombre distinto es un nodo. Un mismo autor escrito de dos o tres formas en
distintos artículos ('Vera L.D. Tomazella', 'Vera L. D. Tomazella', 'Vera Tomazella') aparecía como
nodos separados. La normalización tiene tres pasos:

  1. limpieza automática: acentos reparados, sin superíndices pegados ('Cordeiro3', 'Griffith∗'),
     iniciales sin espacios ('K. O.' -> 'K.O.'), guiones uniformes y formato 'Nombre Apellido'
     ('Case, B.S.' -> 'B.S. Case');
  2. CORREGIR: grafías verificadas contra la imagen del PDF cuando la lectura OCR y la base diferían
     (diacríticos perdidos en versalitas, letras faltantes);
  3. UNIFICAR: variantes de un mismo autor (mismo apellido, nombre e institución) llevadas a una sola forma.

Las decisiones quedan registradas en docs/registro_de_decisiones.md.
"""
import re
from .normalizacion import reparar_acentos

CORREGIR = {
    "abrizio Ruggeri": "Fabrizio Ruggeri",
    "d Manas Ranjan Tripathy": "Manas Ranjan Tripathy",
    "Ednario Mendonça": "Ednário Mendonça",
    "Flavio B. Gonçalves": "Flávio B. Gonçalves",
    "Jose María Sarabia": "José María Sarabia",
    "Mohtashami Borzadaran": "G.R. Mohtashami Borzadaran",
    "Moizes da S. Melo": "Moizés da S. Melo",
    "María Duenas": "María Dueñas",
    # tildes de versalitas perdidas en la base (verificadas en la imagen; algunas tampoco las lee el OCR)
    "Ramon Gutiérrez-Jaimez": "Ramón Gutiérrez-Jáimez",
    "Eduardo Alarcon-Bustamante": "Eduardo Alarcón-Bustamante",
    "Jose J. de Santana e Silva": "José J. de Santana e Silva",
    "Lancine Bamba": "Lanciné Bamba",
    "Sonia Maria De Stefano Piedade": "Sônia Maria De Stefano Piedade",
    "German Tirao": "Germán Tirao",
    "Ramon Giraldo": "Ramón Giraldo",
}

UNIFICAR = {
    "Gauss Cordeiro": "Gauss M. Cordeiro",
    "Vera L.D. Tomazella": "Vera L.D. Tomazella", "Vera Tomazella": "Vera L.D. Tomazella",
    "Andre F.B. Menezes": "André F.B. Menezes", "André F.B. Menezes": "André F.B. Menezes",
    "Andre Felipe B. Menezes": "André F.B. Menezes",
    "Abraao D.C. Nascimento": "Abraão D.C. Nascimento",
    "Juvencio Santos Nobre": "Juvêncio S. Nobre", "Juvêncio Santos Nobre": "Juvêncio S. Nobre",
    "Juvencio S. Nobre": "Juvêncio S. Nobre",
    "Mohammed Kadi Attouch": "Mohammed K. Attouch",
    "Vicente Garibay Cancho": "Vicente G. Cancho",
    "Renato Cintra": "Renato J. Cintra",
    "Dipak Dey": "Dipak K. Dey", "Dipak Kumar Dey": "Dipak K. Dey",
    "Daniel Griffith": "Daniel A. Griffith",
    "Victor Hugo Lachos": "Víctor H. Lachos", "Victor H. Lachos": "Víctor H. Lachos",
    "Y.L. Lio": "Yuhlong Lio",
    "Francisco de Medeiros": "Francisco M.C. de Medeiros",
    "Francisco Moises Cândido de Medeiros": "Francisco M.C. de Medeiros",
    "Francisco Moises Cándido de Medeiros": "Francisco M.C. de Medeiros",
    "Emilio Gomez-Déniz": "Emilio Gómez-Déniz",
    "Silvia Ojeda": "Silvia M. Ojeda",
    "Andre L.S. de Pinho": "André L.S. de Pinho", "Andre Luís Santos de Pinho": "André L.S. de Pinho",
    "German Ibacache-Pulgar": "Germán Ibacache-Pulgar",
}

def limpiar_nombre(n):
    """Limpieza automática de un nombre de autor de la base."""
    n = reparar_acentos(n or "")
    n = re.sub(r"[\d∗*†‡]+$", "", n.strip())                  # superíndices pegados al final
    n = re.sub(r"[–—]", "-", n)                                # guiones uniformes
    n = re.sub(r"(?<=\b[A-ZÀ-Ý]\.)\s+(?=[A-ZÀ-Ý]\.)", "", n)   # 'K. O.' -> 'K.O.'
    if "," in n:                                               # 'Case, B.S.' -> 'B.S. Case'
        ape, ini = [x.strip() for x in n.split(",", 1)]
        if re.fullmatch(r"(?:[A-ZÀ-Ý]\.\s*)+", ini):
            n = f"{ini.replace(' ', '')} {ape}"
    return re.sub(r"\s+", " ", n).strip()

def nombre_canonico(n):
    """Nombre canónico del autor: limpieza, corrección verificada y unificación de variantes."""
    n = limpiar_nombre(n)
    n = CORREGIR.get(n, n)
    return UNIFICAR.get(n, n)
