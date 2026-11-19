# -*- coding: utf-8 -*-
"""
Tabla de corrección del nombre canónico de las instituciones (revisión manual, noviembre de 2026).

La normalización automática (normalizacion.institucion_canonica: alias, coincidencia exacta, Jaccard >= 0,6
o inclusión) dejó tres tipos de problemas, detectados al validar la extracción OCR y al revisar uno por uno
los 218 nombres canónicos de la base:

  1. asignaciones erróneas: la afiliación original corresponde a otra institución
     (p. ej., 'University of Campinas' asignada a la Universidade de Brasília);
  2. duplicados: una misma institución con dos o tres nombres canónicos (idioma, preposición, acentos),
     que en la red de universidades aparecía como nodos distintos;
  3. nombres que no son instituciones (una dirección postal, una región) o que conservan restos del OCR.

POR_AFILIACION corrige por el texto de la afiliación original (casos 1 y 3); UNIFICAR lleva cada nombre
canónico anterior a un nombre único (caso 2 y forma correcta del nombre). Cada decisión queda registrada
en docs/registro_de_decisiones.md.
"""
import re

# texto (en minúsculas, sin acentos) presente en la afiliación original -> institución correcta
POR_AFILIACION = [
    ("acharya nagarjuna", "Acharya Nagarjuna University"),
    ("acroama", "Acroama Gnan Vikas Pvt. Ltd."),
    ("university of campinas", "Universidade Estadual de Campinas"),
    ("engenharia civil e ambiental, universidade of brasilia", "Universidade de Brasília"),
    ("utfpr", "Universidade Tecnológica Federal do Paraná"),     # campus Cornélio Procópio; el PDF dice "UTFPR - Universidade Federal do Paraná"
    ("demm department, piazza arechi", "University of Sannio"),  # DEMM, Benevento: departamento de la Università del Sannio
    ("gestore dei servizi energetici", "Gestore dei Servizi Energetici"),
    ("crop reporting service", "Crop Reporting Service, Agriculture Department, Punjab"),
    ("tunis el-manar", "Université de Tunis El Manar"),
]

# nombre canónico anterior -> nombre canónico final
UNIFICAR = {
    "2Millenium Nucleus on Intergenerational Mobility: From Modelling to Policy": "Millennium Nucleus on Intergenerational Mobility (MOVI)",
    " Modelling to Policy (MOVI)": "Millennium Nucleus on Intergenerational Mobility (MOVI)",
    "Baghdad University": "University of Baghdad",
    "IIMAS, UNAM": "Universidad Nacional Autónoma de México",
    "UNAM": "Universidad Nacional Autónoma de México",
    "Universidad Nacional Autonoma de México": "Universidad Nacional Autónoma de México",
    "Indian School of Mine": "Indian School of Mines",
    "Indian Statistical Institut": "Indian Statistical Institute",
    "State University of Marigá": "Universidade Estadual de Maringá",
    "State University of Maringá": "Universidade Estadual de Maringá",
    "Universidad de Concepcion": "Universidad de Concepción",
    "Universidade de S˜ao Paulo": "Universidade de São Paulo",
    "Universidade Federal de S˜ao Carlos": "Universidade Federal de São Carlos",
    "Universidade Federal of São Carlos": "Universidade Federal de São Carlos",
    "Universidade Federal de Paraná": "Universidade Federal do Paraná",
    "Universidade Federal of Paraná": "Universidade Federal do Paraná",
    "Universidade Federal Paraná ": "Universidade Federal do Paraná",
    "Universidade Federal of Minas Gerais": "Universidade Federal de Minas Gerais",
    "Universidade Federal of Rio Grande do Norte": "Universidade Federal do Rio Grande do Norte",
    "Universidade Federal de Rio Grande do Norte": "Universidade Federal do Rio Grande do Norte",
    "Universidade Federal de Mato Grosso de Sul": "Universidade Federal de Mato Grosso do Sul",
    "Universidade Federal of Mato Grosso do Sul": "Universidade Federal de Mato Grosso do Sul",
    "Universidade of Brasília": "Universidade de Brasília",
    "Universidade of Campinas": "Universidade Estadual de Campinas",
    "Università di Padova": "University of Padua",
    "Sidi Bel Abbes University": "Université Djillali Liabès de Sidi Bel Abbès",
    "University of Djillali Liabes": "Université Djillali Liabès de Sidi Bel Abbès",
    # forma correcta del nombre (sin duplicado, pero con preposición, acento o resto de OCR equivocados)
    "Universidade Federal de Amazonas": "Universidade Federal do Amazonas",
    "Universidade Federal de Ceará": "Universidade Federal do Ceará",
    "Universidade Federal de Piauí": "Universidade Federal do Piauí",
    "Universidade Federal de Rio de Janeiro": "Universidade Federal do Rio de Janeiro",
    "Universidade Federal de Rio Grande do Sul": "Universidade Federal do Rio Grande do Sul",
    "Universidade Federal of Alfenas": "Universidade Federal de Alfenas",
    "Universidade Federal of Espírito Santo": "Universidade Federal do Espírito Santo",
    "Universidade Federal of Juiz de Fora": "Universidade Federal de Juiz de Fora",
    "Universidade Federal of Rondônia": "Universidade Federal de Rondônia",
    "Centro Federal de Educa¸c˜ao Tecnologica Celso Suckow da Fonseca": "Centro Federal de Educação Tecnológica Celso Suckow da Fonseca",
    "Universidad Nacional de Cordoba": "Universidad Nacional de Córdoba",
    "Pontificia Universidad Catolica de Chile": "Pontificia Universidad Católica de Chile",
    "Pontificia Universidad Catolica del Perú": "Pontificia Universidad Católica del Perú",
    "Instituto Tecnologico Autonomo de México": "Instituto Tecnológico Autónomo de México",
    "Instituto Tecnologico de Buenos Aires": "Instituto Tecnológico de Buenos Aires",
    "Universidad Autonoma Agraria Antonio Narro": "Universidad Autónoma Agraria Antonio Narro",
    "Centro de Investigacion en Matemáticas, AC, Guanajuato": "Centro de Investigación en Matemáticas (CIMAT)",
    "Cámara de Control de Medicion de Audiencia, Buenos Aires": "Cámara de Control de Medición de Audiencia",
    "Colegio de Postgraduados, Campus Montecillo": "Colegio de Postgraduados",
    "Data Science Consulting, Ibarra": "Topos: Data Science Consulting",
    "University of Los Andes, Mérida": "Universidad de Los Andes (Venezuela)",
    "National College of Business Administration & Economics, Lahore": "National College of Business Administration & Economics",
    "Hindu College, Guntur": "Hindu College",
    "Universidade Aberta, Lisboa": "Universidade Aberta",
    "IniSEB Centro Universitrio": "IniSEB Centro Universitário",
    " M.L. Sukhadia University": "Mohanlal Sukhadia University",
    "Goverment Sadiq Egerton College Bahawalpur": "Government Sadiq Egerton College",
    "University of California": "University of California, Santa Barbara",
    "University College": "University College, Thiruvananthapuram",
    "State University Julio de Mesquita Filho": "Universidade Estadual Paulista Júlio de Mesquita Filho",
}

PAIS_DE_INSTITUCION = {"Millennium Nucleus on Intergenerational Mobility (MOVI)": "Chile"}

def _plano(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s or "")
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c)).lower())

def canonica_final(universidad, universidad_raw=""):
    """Nombre canónico corregido de una institución, dado el canónico anterior y la afiliación original."""
    raw = _plano(universidad_raw)
    for clave, inst in POR_AFILIACION:
        if clave in raw:
            return inst
    return UNIFICAR.get(universidad, (universidad or "").strip())
