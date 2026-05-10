# Plan de Proyecto — B4 · Síntesis de Instrumentos por Suma de Parciales

**Serie de Fourier aplicada al análisis y síntesis de guitarras**

---

## Idea Central

Un instrumento no produce una sola frecuencia, sino una suma de sinusoides:

```
sonido = A₁·sin(2π·f·t) + A₂·sin(2π·2f·t) + A₃·sin(2π·3f·t) + ...
```

Las amplitudes `Aₙ` de cada armónico definen el **timbre**. Este proyecto mide esas amplitudes desde grabaciones reales de tres tipos de guitarra y las usa para sintetizar y comparar sus timbres.

---

## Objetivo General

Analizar mediante la Transformada de Fourier (FFT) tres señales reales de guitarra, sintetizar sus timbres por suma de parciales con las amplitudes medidas, y permitir la conversión entre timbres en tiempo real mediante una interfaz interactiva de piano.

---

## Cambios Técnicos Incorporados

Esta sección documenta las mejoras aplicadas al diseño original de `analizar_audio.py`, explicando qué se tenía pensado hacer y cómo se hará.

---

### Cambio 1 — Ventana Hann antes de la FFT

**Cómo se tenía pensado hacer:**

```python
fft = np.fft.rfft(audio)
magnitud = np.abs(fft)
```

La FFT se aplicaba directamente sobre el audio crudo. Esto asume que la señal se repite periódicamente en los bordes del fragmento analizado. Como eso no ocurre en un audio real, aparece **spectral leakage**: energía que se derrama de un armónico hacia sus frecuencias vecinas, contaminando los picos y produciendo amplitudes inexactas.

**Cómo se hará ahora:**

```python
ventana = np.hanning(len(audio))
factor_correccion = len(ventana) / np.sum(ventana)  # ≈ 2.0 para Hann
audio_ventaneado = audio * ventana
fft = np.fft.rfft(audio_ventaneado)
magnitud = np.abs(fft) * factor_correccion
```

La ventana Hann multiplica la señal por una curva que vale 0 en los bordes y 1 en el centro, eliminando las discontinuidades. El factor de corrección compensa la reducción de amplitud que introduce la ventana — sin él los valores medidos quedan aproximadamente a la mitad.

**Resultado:** picos más limpios, armónicos más precisos, amplitudes más fieles al instrumento real.

---

### Cambio 2 — Análisis de sección estable, no del audio completo

**Cómo se tenía pensado hacer:**

```python
audio, sr = sf.read(ruta_audio)
fft = np.fft.rfft(audio)  # se analizaba todo el audio
```

Al analizar el audio completo, el **transitorio de ataque** (el golpe de la púa) domina la FFT. Ese transitorio contiene frecuencias de impacto que no pertenecen al timbre sostenido, inflando artificialmente los armónicos bajos.

**Cómo se hará ahora:**

```python
inicio = int(0.2 * sr)   # saltar los primeros 200ms (transitorio de ataque)
fin    = int(1.0 * sr)   # hasta el segundo 1.0 (sustain estable)
audio  = audio[inicio:fin]
```

Se analiza únicamente la región de **sustain estacionario**, donde el espectro es representativo del timbre real del instrumento.

**Resultado:** amplitudes que reflejan el timbre sostenido, no el ruido de la púa.

---

### Cambio 3 — Comparación visual: espectro medido vs sintetizado

**Cómo se tenía pensado hacer:**
El plan generaba solo el espectro del audio real con los picos marcados. La validación de que la síntesis era correcta dependía únicamente de la inspección visual en la interfaz de pygame.

**Cómo se hará ahora:**
`analizar_audio.py` genera adicionalmente una figura comparativa con ambos espectros superpuestos:

```
FFT del audio real        (azul)
FFT del audio sintetizado (naranja)
────────────────────────────────
mismos ejes, misma escala
```

Esto demuestra directamente que la síntesis reconstruye el espectro principal del instrumento. Si los picos coinciden, la síntesis es fiel. Si hay diferencias menores, se explican en el reporte (la síntesis aditiva captura el estado estacionario pero no los transitorios ni el ruido de la caja acústica).

**Resultado:** cierra el ciclo completo del proyecto con validación científica:

```
Audio real → FFT → amplitudes → síntesis → FFT → comparar con original
```

**Archivos adicionales en `salida/`:**

```
salida/
├── comparacion_medido_vs_sintetizado_electrica.png
├── comparacion_medido_vs_sintetizado_acustica.png
└── comparacion_medido_vs_sintetizado_midi.png
```

---

## Estructura de Archivos

```
proyecto_b4/
├── main.py                    ← Bucle principal de pygame
├── CONSTANTES.py              ← Parámetros globales y catálogo de instrumentos
├── generar_nota_instrumento.py← Motor de síntesis aditiva (Serie de Fourier)
├── dibujar_interfaz.py        ← Renderizado visual del piano y osciloscopio
├── analizar_audio.py          ← Medición de amplitudes por FFT (con ventana Hann)
├── convertidor_timbre.py      ← Conversión entre timbres (eléctrica ↔ acústica)
├── audio/
│   ├── guitarra_electrica.wav ← Grabación real (La4, 440 Hz, nota limpia)
│   ├── guitarra_acustica.wav  ← Grabación real (La4, 440 Hz, nota limpia)
│   └── guitarra_midi.wav      ← Audio exportado de MIDI (La4, 440 Hz)
├── salida/
│   ├── espectro_electrica.png
│   ├── espectro_acustica.png
│   ├── espectro_midi.png
│   ├── comparacion_espectros.png
│   ├── comparacion_medido_vs_sintetizado_electrica.png
│   ├── comparacion_medido_vs_sintetizado_acustica.png
│   └── comparacion_medido_vs_sintetizado_midi.png
└── PLAN_PROYECTO_B4.md        ← Este archivo
```

---

## Descripción de Cada Archivo

### `CONSTANTES.py`

Centraliza todos los parámetros globales y el catálogo de instrumentos con sus amplitudes medidas.

**Contiene:**

- `SAMPLE_RATE`, `DURACION`, `WIDTH`, `HEIGHT`
- Colores de la interfaz
- `AMPS_GUITARRA_ELECTRICA`, `AMPS_GUITARRA_ACUSTICA`, `AMPS_GUITARRA_MIDI` — listas de amplitudes medidas por `analizar_audio.py`
- `CATALOGO_INSTRUMENTOS` — diccionario `nombre → (amplitudes, params_adsr)`

**ADSR por instrumento:**

| Instrumento        | Attack | Decay | Sustain Level | Release | Justificación                                            |
| ------------------ | ------ | ----- | ------------- | ------- | -------------------------------------------------------- |
| Guitarra Eléctrica | 0.003s | 0.15s | 0.35          | 0.50s   | Ataque de púa muy rápido, decae rápido sin caja acústica |
| Guitarra Acústica  | 0.005s | 0.30s | 0.20          | 0.60s   | Púa con resonancia de caja, sustain bajo natural         |
| Guitarra MIDI      | 0.008s | 0.25s | 0.40          | 0.70s   | Librería de samples, más sustain artificial              |

**No tiene pruebas propias** — es solo configuración.

---

### `analizar_audio.py`

Carga cada grabación real, calcula su FFT con ventana Hann sobre la sección estable, identifica los picos armónicos y devuelve las amplitudes normalizadas. Es la fuente de verdad de las amplitudes.

**Función principal:**

```python
def medir_amplitudes(ruta_audio, f0=440.0, n_armonicos=10, ventana_hz=20,
                     inicio_s=0.2, fin_s=1.0):
    """
    Carga el audio, recorta al sustain, aplica ventana Hann,
    calcula FFT, busca el pico más cercano a cada armónico
    (f0, 2f0, 3f0...) dentro de una ventana de ±ventana_hz Hz,
    y devuelve las amplitudes normalizadas al primer armónico.
    """
```

**Salida:** lista de amplitudes `[1.000, 0.XXX, 0.XXX, ...]`

**Proceso interno — antes vs ahora:**

| Paso              | Diseño original            | Diseño actualizado                          |
| ----------------- | -------------------------- | ------------------------------------------- |
| Segmento de audio | Audio completo             | Solo `[0.2s, 1.0s]` (sustain)               |
| Preprocesado      | Ninguno                    | Ventana Hann + factor de corrección         |
| FFT               | `np.fft.rfft(audio)`       | `np.fft.rfft(audio * ventana)`              |
| Validación        | Solo espectro del original | Espectro medido vs sintetizado superpuestos |

**Tiene prueba propia:** Al ejecutarse directamente analiza los tres audios, genera todas las gráficas incluidas las comparaciones medido vs sintetizado.

```bash
python analizar_audio.py
```

---

### `generar_nota_instrumento.py`

Motor de síntesis aditiva. Recibe una frecuencia, una lista de amplitudes medidas y parámetros ADSR, y devuelve el audio PCM listo para pygame.

**Función principal:**

```python
def generar_nota_instrumento(freq, amplitudes, adsr_params):
    """
    SERIE DE FOURIER:
    onda = Σ amplitudes[n] · sin(2π · n · freq · t)  para n = 1..N

    Aplica envolvente ADSR y devuelve (audio_stereo_int16, onda_dibujo).
    """
```

**Sin prueba propia** — su validación es la comparación medido vs sintetizado generada en `analizar_audio.py`.

---

### `convertidor_timbre.py`

Implementa la conversión de timbre entre guitarra eléctrica y acústica (y viceversa) usando morfado espectral: interpola linealmente entre los dos conjuntos de amplitudes medidas.

**Función principal:**

```python
def convertir_timbre(amplitudes_origen, amplitudes_destino, mezcla=0.5):
    """
    Interpola entre dos espectros:
    amps_resultado[n] = (1 - mezcla) · origen[n] + mezcla · destino[n]
    mezcla = 0.0 → 100% origen
    mezcla = 1.0 → 100% destino
    """
```

**Tiene prueba propia:** Genera una secuencia de audios con `mezcla` variando de 0.0 a 1.0 en pasos de 0.25, los guarda como `.wav` y muestra la gráfica de cómo cambia el espectro.

```bash
python convertidor_timbre.py
```

---

### `dibujar_interfaz.py`

Renderiza la interfaz completa: panel HUD con osciloscopio, teclado de piano con teclas blancas y negras, selector de instrumento, y panel de conversión de timbre.

**Función principal:**

```python
def dibujar_interfaz(screen, teclas_activas, datos_notas, notas_config,
                     fuentes, instrumento_actual, mezcla_conversion=None):
```

**Panel de conversión:**

- Barra deslizante visual (←→) que indica el nivel de mezcla entre eléctrica y acústica
- Se controla con teclas `Z` (más eléctrica) y `X` (más acústica)
- Solo visible cuando el instrumento seleccionado es una de las dos guitarras

**Sin prueba propia** — depende de pygame para renderizarse.

---

### `main.py`

Bucle principal. Inicializa pygame, pre-genera el banco de sonidos para todos los instrumentos y todas las notas, y gestiona los eventos. El banco de sonidos será llenado con la guitarra acústica, guitarra eléctrica y guitarra de midi post analizados.

**Flujo:**

1. Inicializar pygame y mixer
2. Pre-calcular `banco_sonidos[instrumento][tecla]` para todas las combinaciones
3. Escuchar eventos: teclas de nota, flechas para cambiar instrumento, `Z`/`X` para conversión de timbre
4. En tiempo real, si el usuario está en modo conversión, recalcular la nota con `convertir_timbre` antes de reproducirla

**Controles:**

| Tecla                                               | Acción                           |
| --------------------------------------------------- | -------------------------------- |
| `A` `W` `S` `E` `D` `F` `T` `G` `Y` `H` `U` `J` `K` | Tocar notas Do a Do+             |
| `←` `→`                                             | Cambiar instrumento              |
| `Z`                                                 | Desplazar mezcla hacia eléctrica |
| `X`                                                 | Desplazar mezcla hacia acústica  |
| `ESC` / cerrar ventana                              | Salir                            |

**Sin prueba propia** — es el punto de entrada del programa.

---

## Plan de Trabajo por Fases

### Fase 1 — Recopilación de audios

**Qué hacer:** Grabar o descargar tres archivos `.wav` de La4 (440 Hz):

- `guitarra_electrica.wav` — nota limpia, sin efectos, sin distorsión
- `guitarra_acustica.wav` — nota limpia en sala silenciosa
- `guitarra_midi.wav` — exportado desde DAW o librería MIDI

**Requisitos del audio:**

- Formato `.wav`, mono o estéreo (se convierte a mono automáticamente)
- Duración mínima: **1.5 segundos** de nota sostenida (necesario para tener sustain en `[0.2s, 1.0s]`)
- Sin reverberación excesiva ni ruido de fondo

**Tiempo estimado:** 1–2 horas

---

### Fase 2 — Medición de amplitudes (`analizar_audio.py`)

**Qué hacer:** Implementar y ejecutar `analizar_audio.py` con los tres cambios incorporados.

**Antes:** FFT directa sobre el audio completo → amplitudes contaminadas por el transitorio de ataque.

**Ahora:**

1. Recortar a `[0.2s, 1.0s]` para excluir el transitorio
2. Aplicar ventana Hann con factor de corrección
3. Calcular FFT y buscar picos armónicos
4. Generar comparación medido vs sintetizado por cada instrumento

**Resultado:** Tres listas de amplitudes reales para `CONSTANTES.py` y gráficas de validación.

**Tiempo estimado:** 2–3 horas

---

### Fase 3 — Motor de síntesis (`generar_nota_instrumento.py`)

**Qué hacer:** Implementar la síntesis aditiva con las amplitudes medidas.

**Validación:** La comparación medido vs sintetizado generada en la Fase 2 confirma que la síntesis es correcta — ya no depende solo de la inspección visual en pygame.

**Tiempo estimado:** 1–2 horas

---

### Fase 4 — Interfaz y banco de sonidos (`dibujar_interfaz.py` + `main.py`)

**Qué hacer:** Integrar los tres instrumentos al catálogo, verificar que el cambio de instrumento con flechas funciona, y que el osciloscopio muestra la onda correcta.

**Tiempo estimado:** 1–2 horas

---

### Fase 5 — Convertidor de timbre (`convertidor_timbre.py`)

**Qué hacer:** Implementar el morfado espectral entre eléctrica y acústica. Integrar el control `Z`/`X` en `main.py` y la barra de conversión en `dibujar_interfaz.py`.

**Tiempo estimado:** 2–3 horas

---

### Fase 6 — Comparación y reporte

**Qué hacer:** Compilar gráficas y redactar las conclusiones.

**Gráficas disponibles al llegar a esta fase:**

- Espectro de cada instrumento con picos armónicos marcados
- Comparación de los tres espectros superpuestos
- Comparación medido vs sintetizado por instrumento
- Secuencia de morfado espectral eléctrica → acústica

**Conclusiones a incluir:**

- Diferencias espectrales entre eléctrica, acústica y MIDI (¿qué armónicos dominan en cada una?)
- Por qué el timbre cambia aunque la nota (440 Hz) es la misma
- Por qué se usó ventana Hann y qué problema resuelve (spectral leakage)
- Por qué se analizó solo el sustain y no el transitorio de ataque
- Relación entre Serie de Fourier (síntesis) y Transformada de Fourier (análisis)
- Qué muestra el osciloscopio al tocar varias teclas simultáneamente (superposición)
- Interpretación de la gráfica medido vs sintetizado

**Tiempo estimado:** 1–2 horas

---

## Relación con la Teoría

| Concepto                          | Dónde aparece en el proyecto                                                   |
| --------------------------------- | ------------------------------------------------------------------------------ |
| Serie de Fourier                  | `generar_nota_instrumento.py` — suma de sinusoides con amplitudes medidas      |
| Transformada de Fourier           | `analizar_audio.py` — `np.fft.rfft` para medir amplitudes del espectro real    |
| Spectral leakage                  | `analizar_audio.py` — problema que resuelve la ventana Hann                    |
| Señal estacionaria vs transitorio | `analizar_audio.py` — justificación del recorte `[0.2s, 1.0s]`                 |
| Superposición de señales          | Osciloscopio en `dibujar_interfaz.py` — mezcla de ondas al tocar varias teclas |
| Morfado espectral                 | `convertidor_timbre.py` — interpolación lineal entre espectros                 |
| Timbre                            | La diferencia perceptible entre los tres instrumentos con la misma nota        |

---

## Entregables

| Archivo                                          | Descripción                                      |
| ------------------------------------------------ | ------------------------------------------------ |
| `main.py`                                        | Programa ejecutable completo                     |
| `CONSTANTES.py`                                  | Amplitudes medidas de los tres instrumentos      |
| `analizar_audio.py`                              | Script de análisis FFT con ventana Hann y prueba |
| `generar_nota_instrumento.py`                    | Motor de síntesis                                |
| `dibujar_interfaz.py`                            | Interfaz visual                                  |
| `convertidor_timbre.py`                          | Conversión eléctrica ↔ acústica con prueba       |
| `salida/comparacion_espectros.png`               | Gráfica comparativa de los tres espectros        |
| `salida/comparacion_medido_vs_sintetizado_*.png` | Validación científica por instrumento            |
| `PLAN_PROYECTO_B4.md`                            | Este documento                                   |

---

## Dependencias

```bash
pip install numpy soundfile matplotlib pygame
```

---

## Cómo Ejecutar

```bash
# 1. Medir amplitudes y generar gráficas de validación
python analizar_audio.py

# 2. Probar el convertidor de timbre
python convertidor_timbre.py

# 3. Lanzar el sintetizador completo
python main.py
```
