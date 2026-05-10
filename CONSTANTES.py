# ==============================
# CONFIGURACIÓN GLOBAL
# ==============================
SAMPLE_RATE = 44100
DURACION = 2.0

# Dimensiones de la ventana
WIDTH = 800
HEIGHT = 450

# ==============================
# LÓGICA DE INTERFAZ GRÁFICA
# ==============================
COLOR_BG = (24, 26, 31)
COLOR_PANEL = (34, 38, 46)
COLOR_KEY_UP = (240, 240, 245)
COLOR_KEY_DOWN = (180, 230, 255)
COLOR_SHADOW = (15, 15, 15)
COLOR_NEON = (0, 255, 170) 

# ==============================
# MOTOR DE SÍNTESIS (CATÁLOGO B4)
# ==============================
# Amplitudes Placeholder (Reemplazar con los resultados de analizar_audio.py)
AMPS_GUITARRA_ELECTRICA = [1.000, 0.850, 0.400, 0.200, 0.100, 0.050, 0.020, 0.010, 0.000, 0.000]
AMPS_GUITARRA_ACUSTICA  = [1.000, 0.900, 0.600, 0.400, 0.250, 0.150, 0.080, 0.040, 0.020, 0.010]
AMPS_GUITARRA_MIDI      = [1.000, 0.750, 0.500, 0.300, 0.150, 0.050, 0.010, 0.005, 0.000, 0.000]

# Catálogo: Nombre -> (Amplitudes, (Attack, Decay, Sustain_Level, Release))
CATALOGO_INSTRUMENTOS = {
    "Guitarra Eléctrica": (AMPS_GUITARRA_ELECTRICA, (0.003, 0.15, 0.35, 0.50)),
    "Guitarra Acústica":  (AMPS_GUITARRA_ACUSTICA,  (0.005, 0.30, 0.20, 0.60)),
    "Guitarra MIDI":      (AMPS_GUITARRA_MIDI,      (0.008, 0.25, 0.40, 0.70))
}