import pygame
from CONSTANTES import *
from generar_nota_instrumento import generar_nota_instrumento
from dibujar_interfaz import dibujar_interfaz

# ==============================
# INICIALIZACIÓN
# ==============================
pygame.init()
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sintetizador Aditivo — Banco de Sonidos")

font_main = pygame.font.Font(None, 28)
font_lcd = pygame.font.Font(None, 34) 
font_small = pygame.font.Font(None, 20)
fuentes_ui = (font_small, font_lcd, font_main)

notas_config = {
    pygame.K_a: ("Do",  261.63), pygame.K_w: ("Do#", 277.18),
    pygame.K_s: ("Re",  293.66), pygame.K_e: ("Re#", 311.13),
    pygame.K_d: ("Mi",  329.63), pygame.K_f: ("Fa",  349.23),
    pygame.K_t: ("Fa#", 369.99), pygame.K_g: ("Sol", 392.00),
    pygame.K_y: ("Sol#", 415.30), pygame.K_h: ("La",  440.00),
    pygame.K_u: ("La#", 466.16), pygame.K_j: ("Si",  493.88),
    pygame.K_k: ("Do+", 523.25),
}

# ==============================
# PRE-CÁLCULO DEL MOTOR DE SÍNTESIS
# ==============================
print("Generando banco de sonidos en memoria... Esto tomará unos segundos.")
banco_sonidos = {}

for nombre_inst, (amplitudes, params_adsr) in CATALOGO_INSTRUMENTOS.items():
    banco_sonidos[nombre_inst] = {}
    for tecla, (nombre_nota, f) in notas_config.items():
        audio_data, onda_grafica = generar_nota_instrumento(f, amplitudes, params_adsr)
        sonido = pygame.sndarray.make_sound(audio_data)
        banco_sonidos[nombre_inst][tecla] = {"sonido": sonido, "onda": onda_grafica, "nombre": nombre_nota, "freq": f}

lista_instrumentos = list(CATALOGO_INSTRUMENTOS.keys())
indice_instrumento = 0
instrumento_actual = lista_instrumentos[indice_instrumento]

# Variables para Morfado Espectral (Conversor de Timbre)
mezcla_conversion = 0.0 # 0.0 = Eléctrica, 1.0 = Acústica
modo_morfado = False

# Función in-line de morfado paramétrico
def recalcular_banco_morfado(mezcla):
    amps_e, adsr_e = CATALOGO_INSTRUMENTOS["Guitarra Eléctrica"]
    amps_a, adsr_a = CATALOGO_INSTRUMENTOS["Guitarra Acústica"]
    
    # Emparejar longitudes de listas de amplitud rellenando con ceros si es necesario
    max_len = max(len(amps_e), len(amps_a))
    amps_e_ext = amps_e + [0.0]*(max_len - len(amps_e))
    amps_a_ext = amps_a + [0.0]*(max_len - len(amps_a))
    
    # Interpolación lineal de amplitudes y parámetros ADSR
    amps_mix = [(1 - mezcla) * e + mezcla * a for e, a in zip(amps_e_ext, amps_a_ext)]
    adsr_mix = [(1 - mezcla) * e + mezcla * a for e, a in zip(adsr_e, adsr_a)]
    
    banco_sonidos["Morfado"] = {}
    for tecla, (nombre_nota, f) in notas_config.items():
        audio_data, onda_grafica = generar_nota_instrumento(f, amps_mix, adsr_mix)
        sonido = pygame.sndarray.make_sound(audio_data)
        banco_sonidos["Morfado"][tecla] = {"sonido": sonido, "onda": onda_grafica, "nombre": nombre_nota, "freq": f}

# ==============================
# BUCLE PRINCIPAL
# ==============================
clock = pygame.time.Clock()
running = True
print("¡Listo! Presiona A-K para tocar. Flechas para cambiar instrumento. Z/X para Morphing.")

while running:
    datos_notas_actual = banco_sonidos[instrumento_actual]
    teclas_estado = pygame.key.get_pressed()
    teclas_activas = [t for t in notas_config.keys() if teclas_estado[t]]

    # Si estamos en morfado, pasamos el valor flotante para dibujar el slider HUD
    valor_mezcla_ui = mezcla_conversion if modo_morfado else None
    dibujar_interfaz(screen, teclas_activas, datos_notas_actual, notas_config, fuentes_ui, instrumento_actual, valor_mezcla_ui)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key in datos_notas_actual:
                datos_notas_actual[event.key]["sonido"].play()
            
            # Navegación entre instrumentos estándar (Sale del modo morfado)
            if event.key in (pygame.K_RIGHT, pygame.K_LEFT):
                modo_morfado = False
                if event.key == pygame.K_RIGHT:
                    indice_instrumento = (indice_instrumento + 1) % len(lista_instrumentos)
                if event.key == pygame.K_LEFT:
                    indice_instrumento = (indice_instrumento - 1) % len(lista_instrumentos)
                instrumento_actual = lista_instrumentos[indice_instrumento]
            
            # --- CONVERSIÓN DE TIMBRE ---
            if event.key in (pygame.K_z, pygame.K_x):
                # Desplazar mezcla
                if event.key == pygame.K_z:
                    mezcla_conversion = max(0.0, mezcla_conversion - 0.1)
                elif event.key == pygame.K_x:
                    mezcla_conversion = min(1.0, mezcla_conversion + 0.1)
                
                # Activar el estado y regenerar
                modo_morfado = True
                instrumento_actual = "Morfado Espectral"
                recalcular_banco_morfado(mezcla_conversion)
            
    pygame.display.flip()
    clock.tick(60)

pygame.quit()