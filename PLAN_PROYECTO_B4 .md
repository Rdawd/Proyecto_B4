**# Plan del Proyecto — DASC Sintetizador FFT

## Objetivo

Demostrar que dos guitarras tocando la misma nota (A4 = 440 Hz) producen
espectros armónicos diferentes, capturar esa diferencia con FFT, y usarla
para sintetizar el sonido de cada instrumento en tiempo real mediante un
teclado virtual.

---

## Estructura de archivos

```
proyecto/
│
├── audios/                        ← REQUERIDO — archivos .wav pregrabados
│   ├── guitarra_electrica.wav     ← Nota A4 grabada en guitarra eléctrica
│   └── guitarra_acustica.wav      ← Nota A4 grabada en guitarra acústica
│
├── datos/                         ← Generado automáticamente al analizar
│   ├── armonicos_electrica.json   ← Picos FFT de la eléctrica
│   ├── armonicos_acustica.json    ← Picos FFT de la acústica
│   ├── comparacion_fft.png        ← Gráfico espectro armónico superpuesto
│   └── comparacion_armonicos.png  ← Gráfico barras amplitud por armónico
│
├── CONSTANTES.py                  ← Toda la configuración del proyecto
├── analizar_audio_fft.py          ← Análisis FFT + tabla por instrumento
├── comparar_fft_de_cada_audio.py  ← Gráficos comparativos entre instrumentos
├── sintetizador.py                ← Síntesis aditiva por armónicos
├── interfaz.py                    ← Teclado, osciloscopio, FFT
└── main.py                        ← Punto de entrada principal
```

---

## Requisitos de audio

Los archivos `.wav` deben cumplir:

- **Nota grabada:** A4 (440 Hz)
- **Formato:** mono (1 canal), cualquier bit depth que soporte `soundfile`
- **Duración recomendada:** mínimo 2 segundos para que el fragmento estable
  (60% central) tenga suficientes muestras
- **Sin efectos:** grabación limpia, sin reverb ni distorsión extrema
- **Ubicación exacta:** `audios/guitarra_electrica.wav` y `audios/guitarra_acustica.wav`

> Si los `.wav` no existen, `main.py` termina con `[ERROR] Falta ...` antes de abrir la ventana. Es decir, SON NECESARIOS

---

## Flujo de ejecución

### 1. Análisis — `analizar_audio_fft.py`

```
.wav → carga y normalización
     → extracción del fragmento estable (20%–80% de la señal)
     → ventana Hanning + FFT real
     → detección de picos (height > 0.01, distance > 20 bins)
     → guardado en datos/armonicos_{instrumento}.json
     → tabla: Armónico | Frecuencia (Hz) | Amplitud (dB) | Ratio F0
```

Se genera **una tabla por instrumento** que abre en Spyder con `plt.show()`.
Al terminar imprime `Listo`.

### 2. Comparación — `comparar_fft_de_cada_audio.py`

Lee los JSON de `datos/` y genera dos figuras:

| Figura                             | Contenido                                   |
| ---------------------------------- | ------------------------------------------- |
| **Amplitud por armónico (A1–A10)** | Barras agrupadas por instrumento            |
| **Espectro Armónico**              | Stem plot superpuesto de ambos instrumentos |

Ambas figuras se guardan en `datos/` y abren en Spyder.
Al terminar imprime `Archivos guardados en datos/`.

### 3. Síntesis — `sintetizador.py`

```
JSON de armónicos → perfil de ratios (freq/F0, amplitud)
                 → para cada nota: F0 calculada por temperamento igual
                 → suma de senoides: señal = Σ amp·sin(2π·freq_arm·t)
                 → envolvente ADSR (5% A, 10% D, 70% S, 15% R)
                 → conversión a int16 para Pygame
```

`precalentar_cache()` pre-genera todas las notas de las octavas 4 y 5
al arrancar, para que la reproducción sea instantánea.

### 4. Interfaz — `interfaz.py`

Ventana Pygame de 1600 × 500 px dividida en tres zonas:

| Zona                       | Contenido                                                   |
| -------------------------- | ----------------------------------------------------------- |
| **Panel info** (izquierda) | LED pulsante, nombre del instrumento                        |
| **Panel LCD** (centro)     | Notas activas, frecuencias, osciloscopio con phosphor trail |
| **Panel FFT** (derecha)    | FFT en tiempo real de la onda tocada, 12 barras             |
| **Teclado** (inferior)     | Piano QWERTY con notas musicales, decaimiento 200 ms        |
| **Barra inferior**         | Navegación e instrumento activo                             |

Cada instrumento tiene su paleta de color:

- Eléctrica → cian `(0, 200, 255)`
- Acústica → ámbar `(255, 140, 0)`

### 5. Punto de entrada — `main.py`

1. Verifica que los `.wav` existen
2. Si no existe el JSON de un instrumento, lo genera automáticamente
3. Inicializa Pygame (mixer 44100 Hz, mono, buffer 512)
4. 
5. Entra al loop a 60 FPS
6. Imprime `Listo` cuando la ventana está lista

**Controles:**

| Tecla | Acción |
| --- | --- |
| `← →` | Cambiar instrumento |
| `Z–M`, `Q–U` | Notas C4–B5 |
| `S–J`, `2–7` | Semitonos |
| Cierre de ventana | Salir |

---

## Dependencias

```
pygame
numpy
soundfile
scipy
matplotlib
```

Instalar con:

```bash
pip install pygame numpy soundfile scipy matplotlib
```

---

## Orden de uso recomendado

Los pasos 2 y 3 son opcionales si `datos/` ya contiene los JSON. `main.py` los genera automáticamente si no existen. **Sí es necesario tener los audios en la carpeta audios.**

```
1. Colocar los .wav en audios/
2. Ejecutar analizar_audio_fft.py   → revisa tablas por instrumento
3. Ejecutar comparar_fft_de_cada_audio.py → revisa gráficos comparativos
4. Ejecutar main.py                 → sintetizador interactivo
```
