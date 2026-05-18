import pygame

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE AUDIO
# ─────────────────────────────────────────────
TASA_MUESTREO = 44100  # Antes SAMPLE_RATE
DURACION_NOTA = 1.5
NOTA_BASE = "A4"
FREQ_BASE = 440.0
NUM_ARMONICOS = 20

#───────────────────────────────────────────
# LISTAS Y DICCIONARIOS DE AUDIO
# ─────────────────────────────────────────────
INSTRUMENTOS_LISTA = ["electrica", "acustica"]

INSTRUMENTOS = {
    "electrica": "audios/guitarra_electrica.wav",
    "acustica":  "audios/guitarra_acustica.wav",
}

NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
OCTAVAS = [4, 5]

# ─────────────────────────────────────────────
# CONFIGURACIÓN VISUAL Y LAYOUT (INTERFAZ DASC)
# ─────────────────────────────────────────────
ANCHO_VENTANA = 1600
ALTO_VENTANA = 500

ALTO_PANEL = 155
ANCHO_INFO = 185
ANCHO_FFT = 220
ANCHO_LCD = ANCHO_VENTANA - ANCHO_INFO - ANCHO_FFT
Y_AREA_TECLADO = ALTO_PANEL + 2
ALTO_AREA_TECLADO = ALTO_VENTANA - Y_AREA_TECLADO - 22
ALTO_BARRA_INFERIOR = 22

# Configuración de Renderizado FFT / Visual
TIEMPO_DECAIMIENTO_MS = 200
NUM_BARRAS_FFT = 12
BINS_FFT = 2048

# ─────────────────────────────────────────────
# PALETA POR INSTRUMENTO (TEMAS)
# ─────────────────────────────────────────────
TEMAS = {
    "electrica": {
        "primary":   (0,   200, 255),
        "lcd_bg":    (4,    10,  16),
        "lcd_text":  (77,  255, 145),
        "lcd_mid":   (30,  140,  80),
        "led_color": (0,   200, 255),
    },
    "acustica": {
        "primary":   (255, 140,   0),
        "lcd_bg":    (16,    8,   0),
        "lcd_text":  (255, 200,  80),
        "lcd_mid":   (160, 100,  20),
        "led_color": (255, 140,   0),
    },
    "morfado": {
        "primary":   (0,   255, 150),
        "lcd_bg":    (0,    10,   8),
        "lcd_text":  (100, 255, 200),
        "lcd_mid":   (30,  160, 100),
        "led_color": (0,   255, 150),
    },
}

TEMA_POR_DEFECTO = TEMAS["electrica"]

# ─────────────────────────────────────────────
# MAPEO QWERTY
# ─────────────────────────────────────────────
MAPEO_TECLAS = {
    pygame.K_z: "C4",  pygame.K_s: "C#4", pygame.K_x: "D4",
    pygame.K_d: "D#4", pygame.K_c: "E4",  pygame.K_v: "F4",
    pygame.K_g: "F#4", pygame.K_b: "G4",  pygame.K_h: "G#4",
    pygame.K_n: "A4",  pygame.K_j: "A#4", pygame.K_m: "B4",
    pygame.K_COMMA: "C5", pygame.K_l: "C#5", pygame.K_PERIOD: "D5",
    
    pygame.K_q: "C5",  pygame.K_2: "C#5", pygame.K_w: "D5",
    pygame.K_3: "D#5", pygame.K_e: "E5",  pygame.K_r: "F5",
    pygame.K_5: "F#5", pygame.K_t: "G5",  pygame.K_6: "G#5",
    pygame.K_y: "A5",  pygame.K_7: "A#5", pygame.K_u: "B5",
    pygame.K_i: "C6"
}