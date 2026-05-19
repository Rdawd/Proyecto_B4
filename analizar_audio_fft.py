# analizar_audio_fft.py
import os
import json
import numpy as np
import soundfile as sf
import scipy.signal as signal
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import CONSTANTES


# ─────────────────────────────────────────────
#  CARGA Y PREPROCESADO
# ─────────────────────────────────────────────

def cargar_audio(path: str) -> tuple[np.ndarray, int]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Falta {path}")
    señal, sr = sf.read(path)
    if señal.ndim > 1:
        señal = np.mean(señal, axis=1)
    señal = señal.astype(np.float32)
    max_val = np.max(np.abs(señal))
    if max_val > 0:
        señal /= max_val
    return señal, sr


def extraer_fragmento_estable(señal: np.ndarray, sr: int) -> np.ndarray:
    total = len(señal)
    return señal[int(total * 0.20):int(total * 0.80)]


def aplicar_fft(fragmento: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    ventana    = np.hanning(len(fragmento))
    espectro   = np.fft.rfft(fragmento * ventana)
    freqs      = np.fft.rfftfreq(len(fragmento), 1 / sr)
    magnitudes = np.abs(espectro)
    if magnitudes.max() > 0:
        magnitudes /= magnitudes.max()
    return freqs, magnitudes


def detectar_picos(freqs, magnitudes, n=CONSTANTES.NUM_ARMONICOS):
    indices, _ = signal.find_peaks(magnitudes, height=0.01, distance=20)
    picos = sorted([(freqs[i], magnitudes[i]) for i in indices],
                   key=lambda x: x[1], reverse=True)
    return picos[:n]


def guardar_armonicos(picos, instrumento):
    os.makedirs("datos", exist_ok=True)
    if not picos:
        return
    fundamental = min(picos, key=lambda x: x[0])[0]
    with open(f"datos/armonicos_{instrumento}.json", "w") as f:
        json.dump({"picos": picos, "fundamental": fundamental}, f, indent=4)


# ─────────────────────────────────────────────
#  PIPELINE — devuelve tablas
# ─────────────────────────────────────────────

def analizar_instrumento(nombre: str) -> dict:
    """
    Analiza el instrumento y devuelve un dict con:
      - tabla_armonicos: los armónicos ordenados por frecuencia con freq, amp y dB
      - fundamental_hz, sr, duracion_total_s
    Devuelve {} si hay error.
    """
    path = CONSTANTES.INSTRUMENTOS[nombre]
    try:
        señal, sr         = cargar_audio(path)
        fragmento         = extraer_fragmento_estable(señal, sr)
        freqs, magnitudes = aplicar_fft(fragmento, sr)
        picos             = detectar_picos(freqs, magnitudes)
        guardar_armonicos(picos, nombre)

        fundamental    = min(picos, key=lambda x: x[0])[0] if picos else 0.0
        picos_por_freq = sorted(picos, key=lambda x: x[0])

        tabla_armonicos = []
        for i, (freq, amp) in enumerate(picos_por_freq):
            ratio = freq / fundamental if fundamental > 0 else 0.0
            tabla_armonicos.append({
                "armonico": i + 1,
                "freq_hz":  round(float(freq), 2),
                "amp_norm": round(float(amp),  4),
                "amp_db":   round(20 * np.log10(amp) if amp > 0 else -120, 1),
                "ratio_f0": round(float(ratio), 3),
            })

        return {
            "nombre":          nombre,
            "sr":              sr,
            "fundamental_hz":  round(float(fundamental), 2),
            "duracion_total_s": round(len(señal) / sr, 3),
            "tabla_armonicos": tabla_armonicos,
        }

    except Exception as e:
        return {}


# ─────────────────────────────────────────────
#  VISUALIZACIÓN — UNA figura por instrumento
# ─────────────────────────────────────────────

def _estilo_tabla(ax, col_labels, rows, header_color="#1a2633"):
    ax.axis("off")
    t = ax.table(cellText=rows, colLabels=col_labels,
                 loc="center", cellLoc="center")
    t.auto_set_font_size(False)
    t.set_fontsize(9.5)
    t.scale(1, 1.6)
    for j in range(len(col_labels)):
        t[(0, j)].set_facecolor(header_color)
        t[(0, j)].set_text_props(color="white", fontweight="bold")
    for i in range(1, len(rows) + 1):
        bg = "#0d1117" if i % 2 == 0 else "#161b22"
        for j in range(len(col_labels)):
            t[(i, j)].set_facecolor(bg)
            t[(i, j)].set_text_props(color="#c9d1d9")
    return t


def mostrar_tabla_instrumento(res: dict):
    """
    Muestra UNA figura con la tabla de armónicos del instrumento:
    columnas = Armónico | Frecuencia (Hz) | Amplitud (dB) | Ratio F0

    Esto es lo único necesario para demostrar que los armónicos difieren.
    """
    if not res:
        return

    nombre = res["nombre"]
    ta     = res["tabla_armonicos"]

    fig, ax = plt.subplots(figsize=(9, 0.45 * len(ta) + 1.8), facecolor="#0d1117")
    fig.suptitle(
        f"{nombre.upper()}   ·   F0 = {res['fundamental_hz']} Hz   ·   {res['sr']} Hz SR",
        color="#58a6ff", fontsize=12, fontweight="bold"
    )

    cols = ["Armónico", "Frecuencia (Hz)", "Amplitud (dB)", "Ratio F0"]
    rows = [
        [f"A{r['armonico']}", f"{r['freq_hz']:.2f}", f"{r['amp_db']:.1f} dB", f"{r['ratio_f0']:.3f}"]
        for r in ta
    ]
    _estilo_tabla(ax, cols, rows)
    plt.tight_layout()
    plt.show()


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    for inst in CONSTANTES.INSTRUMENTOS.keys():
        res = analizar_instrumento(inst)
        mostrar_tabla_instrumento(res)
    print("Listo")