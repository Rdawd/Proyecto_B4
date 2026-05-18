import os
import pygame
import numpy as np

import CONSTANTES
from analizar_audio_fft import analizar_instrumento
from sintetizador import precalentar_cache, freq_de_nota, nota_a_samples
from interfaz import dibujar_interfaz, inicializar_fuentes

def verificar_archivos():
    for inst, ruta in CONSTANTES.INSTRUMENTOS.items():
        if not os.path.exists(ruta):
            print(f"[ERROR] Falta {ruta}")
            exit(1)
    os.makedirs("datos", exist_ok=True)
    for inst in CONSTANTES.INSTRUMENTOS.keys():
        ruta_json = f"datos/armonicos_{inst}.json"
        if not os.path.exists(ruta_json):
            analizar_instrumento(inst)

def preparar_datos_interfaz(cache_notas, instrumento_actual):
    """
    Construye las estructuras `datos_notas` y `notas_config` que 
    la interfaz DASC V2 espera recibir para dibujar las ondas y teclas.
    """
    datos_notas = {}
    notas_config = {}
    
    for tecla_id, nota_str in CONSTANTES.MAPEO_TECLAS.items():
        notas_config[tecla_id] = [nota_str]
        
        # FIX: Si la nota está mapeada pero no en caché (ej. "C6"), la generamos al vuelo
        if nota_str not in cache_notas:
            cache_notas[nota_str] = nota_a_samples(nota_str, instrumento_actual)
        
        # Preparar la onda para el osciloscopio
        onda_int = cache_notas[nota_str][:380] 
        if len(onda_int) < 380:
            onda_int = np.pad(onda_int, (0, 380 - len(onda_int)))
        
        onda_float = onda_int.astype(np.float32) / 32768.0
        
        datos_notas[tecla_id] = {
            "nombre": nota_str,
            "freq": freq_de_nota(nota_str),
            "onda": onda_float
        }
        
    return datos_notas, notas_config

def main():
    verificar_archivos()
    
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    screen = pygame.display.set_mode((CONSTANTES.ANCHO_VENTANA, CONSTANTES.ALTO_VENTANA))
    pygame.display.set_caption("Sintetizador FFT - DASC")
    clock = pygame.time.Clock()
    
    fuentes = inicializar_fuentes() 

    # Variables de Estado
    instrumento_actual = "acustica"
    cache_notas = precalentar_cache(instrumento_actual)
    
    # Pasamos el instrumento actual para generar cualquier nota extraída del mapeo (como C6)
    datos_notas, notas_config = preparar_datos_interfaz(cache_notas, instrumento_actual)
    
    nota_activa_str = set()
    corriendo = True
    print("Listo")

    while corriendo:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                corriendo = False
                
            elif e.type == pygame.KEYDOWN:
                # Navegación de instrumentos con las flechas
                if e.key == pygame.K_RIGHT:
                    idx = (CONSTANTES.INSTRUMENTOS_LISTA.index(instrumento_actual) + 1) % len(CONSTANTES.INSTRUMENTOS_LISTA)
                    instrumento_actual = CONSTANTES.INSTRUMENTOS_LISTA[idx]
                    cache_notas = precalentar_cache(instrumento_actual)
                    datos_notas, notas_config = preparar_datos_interfaz(cache_notas, instrumento_actual)
                    nota_activa_str.clear()
                elif e.key == pygame.K_LEFT:
                    idx = (CONSTANTES.INSTRUMENTOS_LISTA.index(instrumento_actual) - 1) % len(CONSTANTES.INSTRUMENTOS_LISTA)
                    instrumento_actual = CONSTANTES.INSTRUMENTOS_LISTA[idx]
                    cache_notas = precalentar_cache(instrumento_actual)
                    datos_notas, notas_config = preparar_datos_interfaz(cache_notas, instrumento_actual)
                    nota_activa_str.clear()
                    
                # Detección de notas musicales
                elif e.key in CONSTANTES.MAPEO_TECLAS:
                    nota = CONSTANTES.MAPEO_TECLAS[e.key]
                    if nota not in nota_activa_str:
                        nota_activa_str.add(nota)
                        # Reproducir audio
                        if nota in cache_notas:
                            buffer = np.ascontiguousarray(cache_notas[nota]).tobytes()
                            sonido = pygame.mixer.Sound(buffer=buffer)
                            sonido.set_volume(0.5)
                            sonido.play()
                            
            elif e.type == pygame.KEYUP:
                if e.key in CONSTANTES.MAPEO_TECLAS:
                    nota = CONSTANTES.MAPEO_TECLAS[e.key]
                    if nota in nota_activa_str:
                        nota_activa_str.remove(nota)
                        
        teclas_activas_ids = [k for k, v in CONSTANTES.MAPEO_TECLAS.items() if v in nota_activa_str]
        
        dibujar_interfaz(
            screen=screen,
            teclas_activas=teclas_activas_ids,
            datos_notas=datos_notas,
            notas_config=notas_config,
            fuentes=fuentes,
            instrumento_actual=instrumento_actual,
            mezcla_conversion=None
        )
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()