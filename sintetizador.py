# sintetizador.py
import json
import numpy as np
import CONSTANTES

def freq_de_nota(nota_str: str) -> float:
    """
    Convierte string de nota a frecuencia Hz usando temperamento igual.
    Referencia: A4 = 440 Hz. Cada semitono = factor 2^(1/12).
    Ejemplos: "C4" -> 261.63, "A#3" -> 233.08, "F#5" -> 739.99
    """
    nombre = nota_str[:-1]
    octava = int(nota_str[-1])
    indice_nota = CONSTANTES.NOTAS.index(nombre)
    indice_a4 = 9 
    octava_base = 4
    semitonos = (octava - octava_base) * 12 + (indice_nota - indice_a4)
    return CONSTANTES.FREQ_BASE * (2 ** (semitonos / 12))

def cargar_perfil(instrumento: str) -> list[tuple[float, float]]:
    """Carga los armónicos desde JSON y normaliza frecuencias como ratios (freq/f0)."""
    ruta = f"datos/armonicos_{instrumento}.json"
    with open(ruta, "r") as f:
        datos = json.load(f)
    
    fundamental = datos["fundamental"]
    picos = datos["picos"]
    
    perfil = []
    for freq, amp in picos:
        ratio = freq / fundamental
        perfil.append((ratio, amp))
    return perfil

def aplicar_adsr(señal: np.ndarray, sr: int) -> np.ndarray:
    """Aplica una envolvente ADSR (5% attack, 10% decay a 0.7, 70% sustain, 15% release)."""
    N = len(señal)
    env = np.ones(N, dtype=np.float32) * 0.7
    
    i_attack = int(0.05 * N)
    i_decay = int(0.15 * N)   # 5% attack + 10% decay
    i_sustain = int(0.85 * N) # Restan 15% para release
    
    if i_attack > 0:
        env[:i_attack] = np.linspace(0.0, 1.0, i_attack)
    if i_decay > i_attack:
        env[i_attack:i_decay] = np.linspace(1.0, 0.7, i_decay - i_attack)
    if N > i_sustain:
        env[i_sustain:] = np.linspace(0.7, 0.0, N - i_sustain)
        
    return señal * env

def sintetizar_nota(freq: float, perfil: list, sr: int, duracion: float) -> np.ndarray:
    """Genera la onda sumando los armónicos escalados con su respectiva amplitud."""
    t = np.linspace(0, duracion, int(sr * duracion), False)
    señal = np.zeros_like(t)
    
    for ratio, amp in perfil:
        freq_armonico = freq * ratio
        # Limitar frecuencias arriba de Nyquist
        if freq_armonico < sr / 2:
            señal += amp * np.sin(2 * np.pi * freq_armonico * t)
            
    # Normalización del master
    max_val = np.max(np.abs(señal))
    if max_val > 0:
        señal /= max_val
        
    return aplicar_adsr(señal, sr)

def nota_a_samples(nota_str: str, instrumento: str) -> np.ndarray:
    """Wrapper para generar la onda y convertida a formato de 16-bits."""
    freq = freq_de_nota(nota_str)
    perfil = cargar_perfil(instrumento)
    señal_float = sintetizar_nota(freq, perfil, CONSTANTES.TASA_MUESTREO, CONSTANTES.DURACION_NOTA)
    
    # Conversión a enteros de 16-bits para Pygame
    señal_int16 = np.int16(señal_float * 32767)
    return señal_int16

def precalentar_cache(instrumento: str) -> dict:
    cache = {}
    for octava in CONSTANTES.OCTAVAS:
        for nota in CONSTANTES.NOTAS:
            nota_str = f"{nota}{octava}"
            cache[nota_str] = nota_a_samples(nota_str, instrumento)
    return cache