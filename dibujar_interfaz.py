import pygame
import numpy as np
import math
from CONSTANTES import WIDTH, HEIGHT

def dibujar_gradiente_tecla(screen, x, y, w, h, color_base, es_oscura=False):
    r, g, b = color_base
    pasos = 20
    altura_gradiente = h // 4
    y_inicio = y + h - altura_gradiente
    
    for i in range(pasos):
        factor = (i / pasos)
        if es_oscura:
            mod_r = max(0, r - (r * factor * 0.8))
            mod_g = max(0, g - (g * factor * 0.8))
            mod_b = max(0, b - (b * factor * 0.8))
        else:
            mod_r = max(0, r - 40 * factor)
            mod_g = max(0, g - 40 * factor)
            mod_b = max(0, b - 40 * factor)
            
        color_actual = (int(mod_r), int(mod_g), int(mod_b))
        y_linea = y_inicio + (i * (altura_gradiente / pasos))
        pygame.draw.line(screen, color_actual, (x + 2, y_linea), (x + w - 3, y_linea), 2)

def dibujar_interfaz(screen, teclas_activas, datos_notas, notas_config, fuentes, instrumento_actual, mezcla_conversion=None):
    font_small, font_lcd, font_main = fuentes
    
    inst_lower = instrumento_actual.lower()
    # Temas de color para Proyecto B4
    if "eléctrica" in inst_lower:
        color_tema = (0, 210, 255)       # Cian
        color_resplandor = (180, 245, 255)
    elif "acústica" in inst_lower:
        color_tema = (255, 140, 0)       # Ámbar
        color_resplandor = (255, 230, 180)
    elif "midi" in inst_lower:
        color_tema = (210, 50, 255)      # Neón Púrpura
        color_resplandor = (245, 200, 255)
    elif "morfado" in inst_lower:
        color_tema = (0, 255, 150)       # Verde Matrix para síntesis híbrida
        color_resplandor = (200, 255, 220)
    else: 
        color_tema = (0, 235, 130)       
        color_resplandor = (200, 255, 220)

    screen.fill((18, 20, 24))
    for i in range(0, WIDTH, 4):
        pygame.draw.line(screen, (22, 24, 28), (i, 0), (i, HEIGHT), 1)

    pygame.draw.rect(screen, (28, 32, 38), (15, 15, WIDTH - 30, 150), border_radius=8)
    pygame.draw.rect(screen, (10, 12, 15), (15, 15, WIDTH - 30, 150), 3, border_radius=8) 
    pygame.draw.rect(screen, (45, 50, 60), (16, 16, WIDTH - 32, 148), 1, border_radius=8) 
    
    rect_img = pygame.Rect(35, 40, 80, 80)
    pygame.draw.rect(screen, (15, 18, 22), rect_img, border_radius=8)
    pygame.draw.rect(screen, (5, 6, 8), rect_img, 4, border_radius=8)
    
    tiempo_actual = pygame.time.get_ticks()
    brillo_led = int(155 + 100 * math.sin(tiempo_actual * 0.003))
    color_led = (int(color_tema[0] * brillo_led/255), int(color_tema[1] * brillo_led/255), int(color_tema[2] * brillo_led/255))
    pygame.draw.circle(screen, color_led, (75, 80), 30, 2)
    
    letra_icono = instrumento_actual[0].upper()
    if "Morfado" in instrumento_actual: letra_icono = "M"
    txt_inicial = font_lcd.render(letra_icono, True, color_tema)
    x_cent = 35 + (80 - txt_inicial.get_width()) // 2
    y_cent = 40 + (80 - txt_inicial.get_height()) // 2
    screen.blit(txt_inicial, (x_cent, y_cent))

    txt_titulo = font_small.render("DASC SIGNAL SYNTHESIZER V2.0", True, (90, 100, 110))
    screen.blit(txt_titulo, (135, 30))
    
    txt_inst = font_small.render(f"PATCH: [ {instrumento_actual.upper()} ]", True, color_tema)
    screen.blit(txt_inst, (135, 55))
    
    # --- BARRA DE CONVERSIÓN TIMBRAL ---
    if mezcla_conversion is not None:
        bar_x, bar_y = 135, 135
        bar_w = 200
        # Línea base
        pygame.draw.rect(screen, (40, 45, 55), (bar_x, bar_y, bar_w, 4), border_radius=2)
        # Indicador deslizante
        ind_x = bar_x + int(bar_w * mezcla_conversion)
        pygame.draw.circle(screen, color_resplandor, (ind_x, bar_y + 2), 6)
        pygame.draw.circle(screen, color_tema, (ind_x, bar_y + 2), 6, 2)
        # Texto ayuda
        txt_morph = font_small.render("MORPH: Z [ELEC] <----> [ACUS] X", True, (120, 130, 140))
        screen.blit(txt_morph, (bar_x, bar_y - 18))

    # Pantalla LCD
    rect_lcd = pygame.Rect(360, 35, 400, 110)
    pygame.draw.rect(screen, (8, 12, 16), rect_lcd, border_radius=5)
    pygame.draw.rect(screen, (40, 50, 60), rect_lcd, 2, border_radius=5)
    
    if teclas_activas:
        nombres = [datos_notas[t]["nombre"] for t in teclas_activas]
        freqs = [f"{datos_notas[t]['freq']:.1f}" for t in teclas_activas]
        str_notas = ", ".join(nombres[:3]) + ("..." if len(nombres)>3 else "")
        str_freqs = " + ".join(freqs[:3]) + ("..." if len(freqs)>3 else "")

        txt_nota = font_lcd.render(f"OUT: {str_notas}", True, (230, 240, 255))
        txt_freq = font_lcd.render(f"HZ:  {str_freqs}", True, color_resplandor)
        screen.blit(txt_nota, (135, 75))
        screen.blit(txt_freq, (135, 100))
        
        # Osciloscopio
        onda_mezclada = np.copy(datos_notas[teclas_activas[0]]['onda'])
        for t in teclas_activas[1:]:
            onda_mezclada += datos_notas[t]['onda']
        
        velocidad_animacion = 0.2
        offset = int((tiempo_actual * velocidad_animacion) % len(onda_mezclada))
        
        inicio_x, inicio_y = 370, 90
        ancho_osc = 380
        alto_osc = 40
        max_val = np.max(np.abs(onda_mezclada)) if np.max(np.abs(onda_mezclada)) != 0 else 1
        
        for i in range(1, 4):
            pygame.draw.line(screen, (20, 30, 40), (inicio_x, inicio_y - alto_osc + i*20), (inicio_x + ancho_osc, inicio_y - alto_osc + i*20), 1)
            pygame.draw.line(screen, (20, 30, 40), (inicio_x + i*95, 45), (inicio_x + i*95, 135), 1)

        # Efecto Ghost (Trail)
        for iteracion_sombra in range(2, 0, -1):
            retraso = iteracion_sombra * 5
            onda_trail = np.roll(onda_mezclada, -(offset - retraso))
            puntos_trail = []
            for i, val in enumerate(onda_trail):
                x = inicio_x + (i / len(onda_trail)) * ancho_osc
                y = inicio_y - (val / max_val) * alto_osc
                puntos_trail.append((x, y))
                
            if len(puntos_trail) > 1:
                divisor_brillo = iteracion_sombra + 1.2 
                color_sombra = (int(color_tema[0] / divisor_brillo), int(color_tema[1] / divisor_brillo), int(color_tema[2] / divisor_brillo))
                pygame.draw.lines(screen, color_sombra, False, puntos_trail, 3)

        # Onda Principal
        onda_animada = np.roll(onda_mezclada, -offset)
        puntos = []
        for i, val in enumerate(onda_animada):
            x = inicio_x + (i / len(onda_animada)) * ancho_osc
            y = inicio_y - (val / max_val) * alto_osc
            puntos.append((x, y))
            
        if len(puntos) > 1:
            pygame.draw.lines(screen, color_tema, False, puntos, 5) 
            pygame.draw.lines(screen, (255, 255, 255), False, puntos, 2)
    else:
        txt_espera = font_lcd.render("AWAITING INPUT...", True, (80, 90, 100))
        screen.blit(txt_espera, (135, 90))
        pygame.draw.line(screen, (20, 40, 30), (370, 90), (750, 90), 2)

    # Teclado (Marfil y Ébano) - Sin cambios estructurales en la física 3D
    teclas_blancas = {k: v for k, v in notas_config.items() if "#" not in v[0]}
    ancho_blanca = (WIDTH - 40) // len(teclas_blancas)
    espaciado = 2 
    y_base = 185
    alto_blanca = 240
    ancho_negra = int(ancho_blanca * 0.55)
    alto_negra = int(alto_blanca * 0.60)
    
    pygame.draw.rect(screen, (5, 5, 5), (10, y_base-15, WIDTH-20, alto_blanca+25), border_radius=8)
    pygame.draw.rect(screen, (140, 10, 20), (15, y_base-10, WIDTH-30, 18), border_radius=2)
    pygame.draw.rect(screen, (80, 5, 10), (15, y_base+4, WIDTH-30, 4))

    posiciones_x_blancas = []
    indice_blanca = 0
    
    for tecla, data in notas_config.items():
        if "#" in data[0]: continue 
        x = 20 + indice_blanca * ancho_blanca
        posiciones_x_blancas.append(x)
        indice_blanca += 1
        
        presionada = pygame.key.get_pressed()[tecla]
        ancho_real = ancho_blanca - espaciado
        
        if presionada:
            rect_tecla = pygame.Rect(x, y_base + 8, ancho_real, alto_blanca - 8)
            pygame.draw.rect(screen, color_resplandor, rect_tecla, border_radius=4)
            pygame.draw.rect(screen, color_tema, rect_tecla, 2, border_radius=4)
            pygame.draw.rect(screen, (0, 0, 0, 60), (x, y_base+8, ancho_real, 12), border_radius=4)
            offset_y = 8
        else:
            rect_sombra = pygame.Rect(x + 3, y_base + 6, ancho_real, alto_blanca)
            pygame.draw.rect(screen, (10, 10, 12), rect_sombra, border_radius=4)
            rect_tecla = pygame.Rect(x, y_base, ancho_real, alto_blanca)
            color_marfil = (248, 248, 242)
            pygame.draw.rect(screen, color_marfil, rect_tecla, border_radius=4)
            dibujar_gradiente_tecla(screen, x, y_base, ancho_real, alto_blanca, color_marfil, False)
            pygame.draw.line(screen, (255, 255, 255), (x+1, y_base+2), (x+1, y_base+alto_blanca-4), 2)
            pygame.draw.rect(screen, (40, 40, 40), rect_tecla, 1, border_radius=4)
            offset_y = 0

        tecla_str = pygame.key.name(tecla).upper()
        color_txt = (140, 140, 140) if not presionada else color_tema
        label_letra = font_main.render(tecla_str, True, color_txt)
        screen.blit(label_letra, (x + (ancho_real // 2) - (label_letra.get_width() // 2), y_base + 175 + offset_y))

    indice_blanca = 0
    for tecla, data in notas_config.items():
        if "#" not in data[0]:
            indice_blanca += 1
            continue
            
        x_blanca_anterior = posiciones_x_blancas[indice_blanca - 1]
        x_negra = x_blanca_anterior + ancho_blanca - (ancho_negra // 2) - (espaciado // 2)
        presionada = pygame.key.get_pressed()[tecla]
        
        if presionada:
            rect_negra = pygame.Rect(x_negra, y_base + 6, ancho_negra, alto_negra)
            pygame.draw.rect(screen, (30, 30, 30), rect_negra, border_radius=2)
            pygame.draw.rect(screen, color_tema, rect_negra, 1, border_radius=2) 
            offset_y = 6
        else:
            pygame.draw.rect(screen, (0, 0, 0), (x_negra + 4, y_base + 4, ancho_negra, alto_negra + 4), border_radius=2)
            rect_negra = pygame.Rect(x_negra, y_base, ancho_negra, alto_negra)
            color_ebano = (25, 25, 25)
            pygame.draw.rect(screen, color_ebano, rect_negra, border_radius=2)
            dibujar_gradiente_tecla(screen, x_negra, y_base, ancho_negra, alto_negra, color_ebano, True)
            pygame.draw.line(screen, (100, 100, 105), (x_negra+2, y_base+2), (x_negra+ancho_negra-3, y_base+2), 2)
            pygame.draw.line(screen, (50, 50, 55), (x_negra+1, y_base+4), (x_negra+1, y_base+alto_negra-6), 1)
            offset_y = 0

        tecla_str = pygame.key.name(tecla).upper()
        color_txt_n = (90, 90, 90) if not presionada else color_tema
        label_letra_n = font_small.render(tecla_str, True, color_txt_n)
        screen.blit(label_letra_n, (x_negra + (ancho_negra // 2) - (label_letra_n.get_width() // 2), y_base + alto_negra - 30 + offset_y))