import numpy as np
from CONSTANTES import SAMPLE_RATE, DURACION

def generar_nota_instrumento(freq, amplitudes, adsr_params):
    num_samples = int(SAMPLE_RATE * DURACION)
    t = np.linspace(0, DURACION, num_samples, endpoint=False)

    onda = np.zeros_like(t)
    for n, amp in enumerate(amplitudes, start=1):
        onda += amp * np.sin(2 * np.pi * n * freq * t)

    # Desempaquetar los parámetros dinámicos
    a_sec, d_sec, s_lvl, r_sec = adsr_params
    
    # SEGURIDAD MATEMÁTICA: geomspace no permite bajar exactamente a 0.0
    s_lvl = max(s_lvl, 0.001)
    
    n_attack  = int(a_sec * SAMPLE_RATE)
    n_decay   = int(d_sec * SAMPLE_RATE)
    n_release = int(r_sec * SAMPLE_RATE)
    n_sustain = max(0, num_samples - (n_attack + n_decay + n_release))

    # Construir la envolvente
    env = np.concatenate([
        np.linspace(0, 1.0, n_attack),
        np.geomspace(1.0, s_lvl, n_decay),
        np.ones(n_sustain) * s_lvl,
        np.geomspace(s_lvl, 0.001, n_release)
    ])

    longitud   = min(len(onda), len(env))
    onda_final = onda[:longitud] * env[:longitud]

    onda_dibujo = onda_final[100:700].copy()
    max_val = np.max(np.abs(onda_final))
    
    # Normalización con headroom de 0.3
    if max_val > 0:
        onda_final = (onda_final / max_val) * 0.3

    audio_int16  = (onda_final * 32767).astype(np.int16)
    audio_stereo = np.column_stack((audio_int16, audio_int16))
    
    return np.ascontiguousarray(audio_stereo), onda_dibujo