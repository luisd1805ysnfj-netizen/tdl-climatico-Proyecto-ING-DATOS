"""Configuración central del pipeline TDL-Climático (E1).

Todo lo que es una decisión (rangos, umbrales, prioridades de fuente) vive aquí
para que se pueda justificar en la relatoría y cambiar sin tocar el código.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DIR_BRONCE = RAIZ / "data" / "bronce"
DIR_PLATA = RAIZ / "data" / "plata"
DIR_ORO = RAIZ / "data" / "oro"
DIR_CUARENTENA = RAIZ / "data" / "cuarentena"

ESTADO = "Colima"
MUNICIPIOS = {
    "tecoman": {"nombre": "Tecomán", "zona": "Costa"},
    "colima": {"nombre": "Colima", "zona": "Valle"},
    "manzanillo": {"nombre": "Manzanillo", "zona": "Costa"},
}
# Variantes de escritura que se resuelven al nombre canónico (entity resolution).
ALIAS_MUNICIPIOS = {
    "colima_colima": "colima",
    "tecoman_colima": "tecoman",
    "manzanillo_colima": "manzanillo",
}

FUENTES_VALIDAS = ["open-meteo-archive", "smn-conagua"]
# Si dos fuentes reportan la misma variable el mismo día se usa la primera
# de la lista (observación oficial antes que reanálisis); si falta, la siguiente.
PRIORIDAD_FUENTES = ["smn-conagua", "open-meteo-archive"]

VARIABLES = ["tmax_c", "tmin_c", "precip_mm", "viento_max_kmh"]

# Rangos físicos plausibles para el estado de Colima. Fuera de aquí = error
# de captura, no clima: el registro va a cuarentena.
RANGOS_FISICOS = {
    "tmax_c": (-5.0, 50.0),
    "tmin_c": (-5.0, 45.0),
    "precip_mm": (0.0, 500.0),
    "viento_max_kmh": (0.0, 200.0),
}
AMPLITUD_MAX_C = 30.0           # tmax - tmin; negativa = regla de negocio violada
LIMITES_COORD = {"lat": (18.4, 19.8), "lon": (-104.9, -103.2)}
FECHA_MINIMA = "2000-01-01"

# --- Limpieza ---
LIMITE_INTERPOLACION_DIAS = 3
UMBRAL_Z_ROBUSTO = 3.5          # Iglewicz-Hoaglin
K_IQR_LLUVIA = 3.0              # outliers "extremos" de Tukey, sobre días con lluvia
CONTAMINACION_IFOREST = 0.01
SEMILLA = 42

# --- Discretización (umbrales de dominio) ---
BINS_TMAX = [-float("inf"), 28, 32, 35, float("inf")]
ETIQ_TMAX = ["fresco", "calido", "muy_calido", "extremo"]
BINS_PRECIP = [-float("inf"), 0, 5, 20, 50, float("inf")]
ETIQ_PRECIP = ["sin_lluvia", "ligera", "moderada", "fuerte", "muy_fuerte"]
MESES_LLUVIA = {6, 7, 8, 9, 10}  # temporada de lluvias en el Pacífico mexicano

# Perfil de la segunda fuente (CSV del SMN/CONAGUA). AJUSTAR cuando vean el
# formato real de su archivo: nombres de columnas, formato de fecha y nulos.
PERFIL_SMN = {
    "fuente": "smn-conagua",
    "columnas": {"FECHA": "fecha", "MUNICIPIO": "municipio",
                 "TMAX": "tmax_c", "TMIN": "tmin_c", "PRECIP": "precip_mm"},
    "formato_fecha": "%d/%m/%Y",
    "tz_origen": None,           # p. ej. "UTC" si las fechas vienen en UTC
    "conversiones": {},          # p. ej. {"tmax_c": "f_a_c"}
    "valores_nulos": ["Nulo", "NULO", "S/D", "-", ""],
    "encoding": "latin-1",
}
