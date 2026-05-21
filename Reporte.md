**Departamento de Ingeniería en Sistemas Computacionales (DASC)** **Universidad Autónoma de Baja California Sur (UABCS)** 

Este documento técnico describe los fundamentos físicos, matemáticos y de software detrás de un sintetizador de audio que funciona gracias a la FFT: 

#### 1. Teoría Musical

Para entender cómo funciona el proyecto hay que saber varias cosas de teoría musical: octavas, tonos, semitonos, coma pitagórica, temperamento igual, entre otras.

Una **octava** se define matemáticamente como una duplicación exacta de la frecuencia de origen. Si una nota base vibra a una frecuencia *f*, su octava superior vibrará exactamente a *2f*. Nuestro cerebro percibe esta relación de duplicación como el mismo tono musical, pero situado en un registro más agudo.

### 1.2 El Problema Pitagórico y la Coma Musical

Durante siglos, la afinación se basó en el sistema de Pitágoras, el cual construía la escala musical utilizando intervalos basados en fracciones de números enteros perfectos, principalmente la relación 3:2 (conocida como la *Quinta Perfecta*).

Sin embargo, la física y las matemáticas presentan una incompatibilidad fundamental conocida como la **Coma Pitagórica**: si apilas 12 quintas perfectas calculadas mediante fracciones puras `(3/2)^12`, deberías llegar exactamente a la misma frecuencia que si apilas 7 octavas puras `2^7`. En la realidad, existe una pequeña discrepancia:

(1.5)¹² ≈ 129.746  ≠  2⁷ = 128

Esta imperfección provocaba que un instrumento afinado perfectamente para tocar en una tonalidad sonara disonante al intentar tocar en otra. A estos intervalos inservibles se les conocía históricamente como el "acorde del lobo".

### 1.3 La Solución Moderna: El Temperamento Igual

Para solucionar este problema y permitir la modulación entre tonalidades sin reafinar el instrumento, los matemáticos y músicos del siglo XVII desarrollaron el **Temperamento Igual**.

Este sistema divide la octava en **12 escalones idénticos** llamados **semitonos**. Como el oído humano percibe la frecuencia de manera logarítmica (multiplicando), cada escalón se calcula multiplicando la nota anterior por un factor geométrico constante: la **raíz doceava de 2**: $\sqrt[12]{2} \approx 1.059463094$

Si multiplicamos una frecuencia base por este factor 12 veces consecutivas, duplicamos la frecuencia con precisión matemática absoluta:

$f \times (\sqrt[12]{2})^{12} = f \times 2 = 2f$ (Una octava completa)

La fórmula general para calcular la frecuencia de cualquier nota `fn` a una distancia de `n` semitonos de una nota de referencia `f0` es: $f_n = f_0 \times 2^{\frac{n}{12}}$

### 1.4 El Estándar Internacional ISO 16

La elección de la frecuencia de inicio no es arbitraria. En **1939**, una conferencia internacional en Londres fijó la nota **La de la cuarta octava (A4)** en **440 Hz**, posteriormente ratificado bajo la norma **ISO 16**.

---

## 2. Procesamiento Digital de Señales: La Transformada de Fourier (FFT)

### 2.1 El Límite Físico del Audio Digital (Teorema de Nyquist)

Un sistema informático no puede almacenar ondas continuas del mundo real; debe digitalizarlas tomando muestras periódicas de la amplitud. La velocidad a la que se toman estas capturas se denomina **Tasa de Muestreo**. El estándar utilizado en este proyecto es `TASA_MUESTREO = 44100` (44,100 muestras por segundo).

De acuerdo con el **Teorema de Muestreo de Nyquist-Shannon**, para reconstruir una onda de manera perfecta se necesitan como mínimo dos muestras por cada ciclo completo. Por lo tanto, la frecuencia máxima que el software puede procesar de forma segura es:

```
Frecuencia de Nyquist = TASA_MUESTREO / 2 = 44100 / 2 = 22,050 Hz
```

Cualquier frecuencia superior a 22,050 Hz sufrirá un fenómeno de distorsión llamado **Aliasing**, donde la computadora genera frecuencias falsas en el espectro grave.

### 2.2 Análisis Espectral y Detección de Picos mediante SciPy

Cuando una cuerda de guitarra vibra, no produce una onda senoidal pura de 440 Hz. La cuerda vibra en toda su longitud y genera ondas secundarias simultáneas al vibrar en mitades, tercios y cuartos. Estas vibraciones se denominan **Armónicos** y constituyen múltiplos enteros de la frecuencia fundamental $1 \times f_0, 2 \times f_0, 3 \times f_0 \dots$. La suma de todos estos armónicos define el **Timbre** único del instrumento.

Para aislar los armónicos verdaderos del ruido de fondo, el script ejecuta la función `find_peaks` de `scipy.signal`:

```python
indices, _ = signal.find_peaks(magnitudes, height=0.01, distance=20)
```

- **`height=0.01` (Umbral de Amplitud Mínima):** Dado que las magnitudes están normalizadas (pico máximo = 1.0), descarta cualquier componente cuya energía sea inferior al 1% de la señal principal. Elimina el ruido base.
- **`distance=20` (Separación Inter-Espectral):** En una FFT real, los picos de frecuencia tienen cierta anchura. Sin este parámetro, el algoritmo contaría las laderas de cada pico como armónicos distintos. Exigir una separación mínima de 20 bins garantiza capturar armónicos bien diferenciados.

### 2.3 El Concepto de Ratios: Independencia de Notas

El analizador no almacena las frecuencias absolutas en Hz. Si guardara que la guitarra tiene un pico en 440 Hz, esa firma acústica solo serviría para reproducir La4.

En cambio, convierte las frecuencias en **Ratios (Proporciones Relativas)** dividiendo cada frecuencia armónica entre la frecuencia fundamental $f_0$:

$\text{Ratio} = \frac{\text{Frecuencia del Armónico}}{\text{Frecuencia Fundamental}}$

- Primer armónico (fundamental): `440 / 440 = 1.0`
- Segundo armónico: `880 / 440 = 2.0`

Estos ratios se almacenan en archivos JSON en `datos/`. Si el músico presiona Do5 $f_0 = 523.25\text{ Hz}$, el sintetizador multiplica la nueva base por los ratios guardados (`523.25 × 1.0`, `523.25 × 2.0` ...), preservando el timbre idéntico en cualquier registro.

---

## 3. Síntesis Aditiva y Modulación Temporal (ADSR)

### 3.1 Reconstrucción por Síntesis Aditiva

En `sintetizador.py`, el proceso se invierte. El software lee el JSON del instrumento seleccionado y recrea el sonido mediante **Síntesis Aditiva**: cualquier sonido complejo puede recrearse sumando ondas senoidales puras escaladas adecuadamente en frecuencia y volumen.

Por cada armónico en el perfil, el software genera matemáticamente la onda mediante la función trigonométrica seno:

```python
señal += amp * np.sin(2 * np.pi * freq_armonico * t)
```

### 3.2 La Envolvente Dinámica ADSR

Las ondas senoidales puras producen un sonido estéril y artificial porque en los instrumentos reales el volumen no aparece y desaparece instantáneamente. Para emular el comportamiento físico, la función `aplicar_adsr` aplica una envolvente de volumen en cuatro etapas:

```python
i_attack  = int(0.05 * N)
i_decay   = int(0.15 * N)   # 5% attack + 10% decay
i_sustain = int(0.85 * N)   # Restan 15% para release
```

1. **Attack (primer 5%):** Sube el volumen de 0.0 a 1.0. Imita el impacto inicial de la púa sobre la cuerda.
2. **Decay (siguiente 10%):** Baja desde el pico máximo hasta el nivel de estabilización.
3. **Sustain (del 15% al 85%):** Mantiene el volumen constante en 0.7 mientras la nota está activa.
4. **Release (último 15%):** Rampa descendente de 0.7 a 0.0, emulando el apagado natural de la cuerda.

---

## 4. Implementación Explícita de la Transformada de Fourier (FFT)

### 4.1 Propósito FFT

En este proyecto la FFT cumple dos propósitos distintos en dos archivos distintos:

| Archivo                 | Uso de la FFT                                                                   | Momento                                     |
| ----------------------- | ------------------------------------------------------------------------------- | ------------------------------------------- |
| `analizar_audio_fft.py` | Extraer el perfil armónico del instrumento real grabado en `.wav`               | Una sola vez, antes de usar el sintetizador |
| `interfaz.py`           | Calcular el espectro de la señal sintetizada que se está tocando en tiempo real | Cada frame, a 60 FPS                        |

### 4.2 La FFT en el análisis del audio real

El archivo `analizar_audio_fft.py` aplica la FFT al fragmento estable del audio grabado (el 60% central de la señal, descartando el ataque y el release). Antes de aplicar la transformada, se multiplica la señal por una **ventana de Hanning**:

```python
ventana  = np.hanning(len(fragmento))
espectro = np.fft.rfft(fragmento * ventana)
freqs    = np.fft.rfftfreq(len(fragmento), 1 / sr)
```

**Por qué se aplica la ventana de Hanning:** La FFT asume matemáticamente que la señal que analiza es periódica y se repite de forma infinita. Un fragmento de audio real casi nunca comienza y termina exactamente en cero, por lo que al "pegar" el final con el principio se genera una discontinuidad brusca. Esa discontinuidad produce un fenómeno llamado **spectral leakage** (fuga espectral): energía falsa que se "derrama" desde las frecuencias reales hacia frecuencias vecinas, ensuciando el espectro y dificultando la detección de picos. La ventana de Hanning atenúa suavemente los extremos del fragmento hacia cero, eliminando la discontinuidad y produciendo un espectro limpio.

**`np.fft.rfft` vs `np.fft.fft`:** Se utiliza `rfft` (real FFT) en lugar de la FFT compleja general porque la señal de audio es un array de números reales. La FFT de una señal real es simétricamente redundante: la segunda mitad del resultado es el espejo conjugado de la primera. `rfft` aprovecha esta propiedad y devuelve únicamente la primera mitad, reduciendo el tamaño del espectro a `N/2 + 1` bins y ahorrando memoria y cómputo.

**Lo que devuelve la FFT:**

- `espectro`: array de números complejos. Cada posición representa una frecuencia. La magnitud (`np.abs`) de cada número indica cuánta energía hay a esa frecuencia.
- `freqs`: array de frecuencias en Hz correspondientes a cada bin del espectro, calculadas a partir del número de muestras y la tasa de muestreo.

Luego se normalizan las magnitudes dividiendo entre el valor máximo, dejando la escala en el rango `[0.0, 1.0]`:

```python
magnitudes = np.abs(espectro)
if magnitudes.max() > 0:
    magnitudes /= magnitudes.max()
```

### 4.3 La FFT en tiempo real dentro de la interfaz

La función `_calcular_fft_barras` en `interfaz.py` aplica la FFT a la onda sintetizada mezclada de todas las teclas activas, en cada frame del loop de Pygame:

```python
ventana  = np.hanning(N)
espectro = np.abs(np.fft.rfft(onda * ventana, n=CONSTANTES.BINS_FFT))
if espectro.max() > 0:
    espectro /= espectro.max()
```

El parámetro `n=CONSTANTES.BINS_FFT` (valor: 2048) le indica a la FFT que use exactamente 2048 puntos de análisis, independientemente del tamaño real de la onda de entrada. Esto garantiza una resolución espectral consistente en el panel visual.

Después de obtener el espectro, se recortan los primeros 250 bins (correspondientes a las frecuencias graves y medias donde viven los armónicos de guitarra) y se agrupan en 12 barras visuales:

```python
max_bins      = min(len(espectro), 250)
espectro_util = espectro[1:max_bins]        # se descarta la frecuencia 0
step          = max(1, bin_total // n_bars)
```

Cada barra representa el pico máximo de su banda de frecuencias, produciendo una visualización que responde en tiempo real a las notas tocadas y refleja fielmente los armónicos de cada instrumento.

### 4.4 Del espectro al timbre: el ciclo completo

El ciclo completo que conecta la FFT del análisis con la síntesis y la visualización es el siguiente:

```
Audio .wav real
      │
      ▼
np.fft.rfft(fragmento × ventana_hanning)
      │  extrae frecuencias y amplitudes
      ▼
Picos detectados → convertidos a ratios (freq / f0)
      │  guardados en datos/armonicos_{instrumento}.json
      ▼
sintetizar_nota(): suma de senoides amp × sin(2π × f0 × ratio × t)
      │  genera la onda de la nota presionada
      ▼
np.fft.rfft(onda_sintetizada × ventana_hanning)
      │  calcula el espectro de lo que se está tocando
      ▼
Panel FFT de la interfaz: 12 barras en tiempo real
```

---

## 5. Cartografía del Código: Líneas Exactas por Archivo

A continuación, se presentan los fragmentos de código exactos de la arquitectura del proyecto que sustentan científicamente los puntos anteriores.

###### 5.1 Archivo: `CONSTANTES.py`

Centraliza toda la configuración del proyecto en un único punto. No contiene lógica ejecutable.

**`TASA_MUESTREO = 44100`** Define cuántas muestras de amplitud se capturan y reproducen por segundo. 44,100 Hz es el estándar de audio de alta fidelidad. Este valor lo usa `sintetizador.py` para construir el eje temporal de cada nota y también determina la frecuencia de Nyquist que limita qué armónicos se sintetizan.

**`FREQ_BASE = 440.0` y `NOTA_BASE = "A4"`** Son el ancla de todo el sistema de temperamento igual. Cualquier nota se calcula como una distancia en semitonos respecto a A4 = 440 Hz. Si algún día se quisiera afinar el sistema a un estándar diferente (como 432 Hz), solo habría que cambiar este valor.

**`NUM_ARMONICOS = 20`** Límite máximo de picos espectrales que el analizador guarda por instrumento. Controla directamente cuántos osciladores senoidales se sumarán en `sintetizar_nota`: más armónicos significa mayor fidelidad tímbrica pero más cómputo por nota.

**`ANCHO_VENTANA = 1600` y `ALTO_VENTANA = 500`** Dimensiones de la ventana Pygame. A partir de estos valores se calculan en cascada todos los demás parámetros de layout: `ANCHO_LCD`, `Y_AREA_TECLADO`, `ALTO_AREA_TECLADO`, etc. Cambiar estas dos constantes reescala toda la interfaz.

**`TIEMPO_DECAIMIENTO_MS = 200`** Duración en milisegundos del efecto visual de glow que queda en las teclas después de soltarlas. Lo consulta `_decay_factor` en `interfaz.py` para calcular qué tan brillante debe estar cada tecla en el frame actual.

**`TEMAS`** Diccionario de diccionarios con las paletas de color por instrumento: `primary`, `lcd_bg`, `lcd_text`, `lcd_mid` y `led_color`. La función `_tema()` en `interfaz.py` lo consulta al inicio de cada frame. Todos los elementos visuales (LED, borde del panel, texto LCD, barras FFT, teclas activas) derivan su color de este único diccionario.

**`MAPEO_TECLAS`** Diccionario que traduce cada constante de tecla de Pygame (`pygame.K_z`, `pygame.K_s`, etc.) a la nota musical correspondiente (`"C4"`, `"C#4"`, etc.). Es el puente entre el evento físico del teclado y el motor de síntesis. Cubre dos octavas completas: la fila inferior del teclado (Z–M) mapea C4–B4 y la fila superior (Q–U) mapea C5–B5, con C6 en la tecla I.

---

### 5.2 Archivo: `analizar_audio_fft.py`

Es el único archivo del proyecto que lee audio del disco. Realiza la ingeniería inversa del instrumento: toma el `.wav` grabado, lo procesa por FFT y extrae los armónicos que definen su timbre. Su salida (los archivos JSON en `datos/`) es lo que alimenta al sintetizador.

**`cargar_audio(path)`** Abre el `.wav` con `soundfile.read`. Si el archivo es estéreo (dos canales), lo colapsa a mono promediando ambos canales con `np.mean(señal, axis=1)`. Luego normaliza dividiendo entre el máximo absoluto, dejando la señal en `[-1.0, 1.0]`. Esta normalización es crítica: sin ella, el umbral `height=0.01` en `detectar_picos` se comportaría de forma distinta dependiendo del volumen con que se grabó el `.wav`.

**`extraer_fragmento_estable(señal, sr)`** Devuelve el 60% central de la señal: desde el 20% hasta el 80% del total de muestras.

```python
return señal[int(total * 0.20):int(total * 0.80)]
```

El objetivo es descartar el ataque inicial (donde la energía de la púa domina y el timbre aún no es estable) y el release final (donde la cuerda se está apagando y el espectro se degrada). El fragmento central representa el timbre en estado estacionario, que es lo que se quiere capturar como firma del instrumento.

**`aplicar_fft(fragmento, sr)`** Es el núcleo matemático del análisis. Multiplica el fragmento por una ventana de Hanning para eliminar artefactos de borde, luego aplica la FFT real:

```python
ventana    = np.hanning(len(fragmento))
espectro   = np.fft.rfft(fragmento * ventana)
freqs      = np.fft.rfftfreq(len(fragmento), 1 / sr)
magnitudes = np.abs(espectro)
```

`rfftfreq` calcula a qué frecuencia en Hz corresponde cada bin del espectro, usando el número de muestras y la tasa de muestreo. Al final normaliza las magnitudes dividiendo entre el máximo, dejando la escala en `[0.0, 1.0]`. Devuelve los dos arrays: `freqs` y `magnitudes`.

**`detectar_picos(freqs, magnitudes, n)`** Recibe el espectro normalizado y localiza los armónicos reales filtrando el ruido:

```python
indices, _ = signal.find_peaks(magnitudes, height=0.01, distance=20)
picos = sorted([(freqs[i], magnitudes[i]) for i in indices],
               key=lambda x: x[1], reverse=True)
return picos[:n]
```

Ordena los picos de mayor a menor amplitud y devuelve los `n` más fuertes (máximo `NUM_ARMONICOS = 20`). El resultado es una lista de tuplas `(frecuencia_hz, amplitud_normalizada)` que representan los armónicos del instrumento.

**`guardar_armonicos(picos, instrumento)`** Toma la lista de picos, identifica la frecuencia fundamental como el pico de menor frecuencia, y serializa todo en un JSON:

```python
fundamental = min(picos, key=lambda x: x[0])[0]
json.dump({"picos": picos, "fundamental": fundamental}, f, indent=4)
```

Este JSON es la interfaz entre el análisis y la síntesis. Una vez generado, el sintetizador puede funcionar completamente sin los archivos `.wav` originales.

**`analizar_instrumento(nombre)`** Orquesta el pipeline completo llamando en secuencia a las cuatro funciones anteriores. Adicionalmente calcula los ratios `freq / fundamental` y los valores en dB para cada armónico, empaquetando todo en un diccionario con la clave `tabla_armonicos`. Este diccionario es el que `mostrar_tabla_instrumento` usa para generar la tabla visual en Spyder, y también es lo que devuelve cuando `main.py` lo llama para regenerar los JSON si no existen.

**`mostrar_tabla_instrumento(res)`** Recibe el diccionario devuelto por `analizar_instrumento` y genera una figura de matplotlib con cuatro columnas: Armónico, Frecuencia (Hz), Amplitud (dB) y Ratio F0. El tamaño de la figura se calcula dinámicamente según el número de armónicos detectados (`figsize=(9, 0.45 * len(ta) + 1.8)`). Es la herramienta de verificación visual del análisis.

---

### 5.3 Archivo: `sintetizador.py`

Motor matemático del proyecto. Toma los ratios almacenados en los JSON y los convierte en ondas de audio reproducibles. No lee archivos `.wav` ni interactúa con Pygame directamente: opera exclusivamente sobre datos numéricos.

**`freq_de_nota(nota_str)`** Convierte una cadena como `"C#5"` a su frecuencia en Hz. Primero separa el nombre de la nota y la octava, luego calcula cuántos semitonos la separan de A4:

```python
semitonos = (octava - octava_base) * 12 + (indice_nota - indice_a4)
return CONSTANTES.FREQ_BASE * (2 ** (semitonos / 12))
```

`indice_a4 = 9` porque La ocupa la posición 9 en la lista cromática `["C","C#","D"...]`. `(octava - 4) * 12` escala por octavas completas y `(indice_nota - 9)` ajusta los semitonos dentro de la octava. El resultado es la aplicación directa de la fórmula de temperamento igual.

**`cargar_perfil(instrumento)`** Lee el JSON del instrumento y convierte cada pico en una tupla `(ratio, amplitud)`, donde `ratio = freq / fundamental`:

```python
for freq, amp in picos:
    ratio = freq / fundamental
    perfil.append((ratio, amp))
```

Normalizar a ratios es lo que hace al perfil independiente de la nota. El mismo molde tímbrico capturado de A4 se puede aplicar a cualquier nota multiplicando su `f0` por cada ratio.

**`aplicar_adsr(señal, sr)`** Construye una envolvente de volumen de cuatro segmentos usando `np.linspace` y la multiplica elemento a elemento por la señal:

```python
env[:i_attack]        = np.linspace(0.0, 1.0, i_attack)      # ataque
env[i_attack:i_decay] = np.linspace(1.0, 0.7, i_decay - i_attack)  # decay
env[i_sustain:]       = np.linspace(0.7, 0.0, N - i_sustain)  # release
```

El segmento de sustain no se escribe explícitamente porque el array se inicializa en `0.7` con `np.ones * 0.7`. La multiplicación final `señal * env` aplica la dinámica temporal que hace que el sonido se comporte como un instrumento real.

**`sintetizar_nota(freq, perfil, sr, duracion)`** Genera la onda completa de una nota. Crea el eje temporal con `np.linspace(0, duracion, int(sr * duracion), False)` y suma las senoides de todos los armónicos del perfil:

```python
for ratio, amp in perfil:
    freq_armonico = freq * ratio
    if freq_armonico < sr / 2:
        señal += amp * np.sin(2 * np.pi * freq_armonico * t)
```

El filtro `freq_armonico < sr / 2` descarta armónicos por encima de la frecuencia de Nyquist antes de sintetizarlos, previniendo aliasing. Al terminar normaliza la suma y llama a `aplicar_adsr`.

**`nota_a_samples(nota_str, instrumento)`** Wrapper que une las tres funciones anteriores y convierte el resultado float a enteros de 16 bits:

```python
señal_int16 = np.int16(señal_float * 32767)
```

El factor 32767 es el máximo valor positivo de un entero de 16 bits con signo. Este formato es exactamente el que `pygame.mixer.Sound` espera recibir como buffer de audio crudo.

**`precalentar_cache(instrumento)`** Itera sobre todas las combinaciones de `OCTAVAS × NOTAS` (2 × 12 = 24 notas) y llama a `nota_a_samples` para cada una, almacenando el resultado en un diccionario `{"C4": array, "C#4": array, ...}`. Al ejecutarse al inicio, todo el cómputo de síntesis ocurre antes de que el usuario toque una tecla. Durante el juego, reproducir una nota es solo leer una entrada del diccionario.

---

### 5.4 Archivo: `interfaz.py`

Responsable de todo el renderizado visual. No produce ni reproduce audio; recibe las ondas ya calculadas y el estado actual del sintetizador, y los traduce a píxeles en cada frame.

**`inicializar_fuentes()`** Carga las tres fuentes `couriernew` (tamaños 11, 15 y 12) una sola vez al arrancar el programa y las devuelve como tupla. Se pasan como argumento a `dibujar_interfaz` en cada frame para evitar el costo de cargarlas 60 veces por segundo.

**`_tema(instrumento_actual)`** Busca en `CONSTANTES.TEMAS` la paleta del instrumento activo haciendo `if k in key` para tolerancia de variantes del nombre. Si no encuentra coincidencia devuelve `CONSTANTES.TEMA_POR_DEFECTO`. Es el punto de entrada de toda la lógica de color: el resultado de esta función determina el color de cada elemento visible en el frame.

**`registrar_keydown(kid)` y `_decay_factor(kid, t_now)`** Trabajan juntas para el efecto de decaimiento visual. `registrar_keydown` guarda el timestamp actual en el diccionario global `_decay_timestamps` cuando se presiona una tecla. `_decay_factor` calcula cuánto tiempo ha pasado desde ese timestamp y devuelve un valor entre 1.0 (acaba de soltarse) y 0.0 (ya pasaron los 200 ms):

```python
elapsed = t_now - ts
return 1.0 - elapsed / CONSTANTES.TIEMPO_DECAIMIENTO_MS
```

Este valor se pasa a las funciones de dibujo de teclas para interpolar el color entre el estado activo y el reposo.

**`_dibujar_led(screen, cx, cy, color, t)`** Dibuja el LED pulsante del panel izquierdo como cuatro círculos concéntricos con radios 18, 13, 8 y 4, cada uno con un valor de alpha diferente. El alpha de los tres exteriores se modula con `math.sin(t * 0.003)`, donde `t` es el tiempo de Pygame en milisegundos. El factor `0.003` produce un ciclo completo cada ~2 segundos, simulando una luz que respira lentamente.

**`_dibujar_osciloscopio(screen, rect, onda, lcd_text, t)`** Primero dibuja una cuadrícula sutil dividiendo el área en 3 filas y 6 columnas. Luego renderiza la onda en tres pasadas con `np.roll` para crear el efecto phosphor trail:

```python
for offset_f, width, alpha in [(20, 6, 30), (10, 4, 80), (0, 2, 255)]:
    pts = build_points(offset_f)
    pygame.draw.lines(surf, (*lcd_text, alpha), False, local, width)
```

Cada pasada dibuja la onda desplazada en el tiempo (20, 10 y 0 frames atrás) con menor opacidad y mayor grosor, simulando la persistencia del fósforo en un osciloscopio CRT. Encima de las tres capas se dibuja una línea blanca de 1px que aporta el brillo del haz principal.

**`_calcular_fft_barras(onda, n_bars)`** Aplica la FFT a la onda sintetizada activa para generar el panel derecho en tiempo real. Aplica ventana de Hanning, calcula `np.fft.rfft` con `BINS_FFT = 2048` puntos, normaliza, descarta el bin DC (frecuencia 0) y recorta a los primeros 250 bins útiles. Luego agrupa esos bins en `n_bars = 12` bandas tomando el máximo de cada banda. Devuelve una lista de 12 floats.

**`_dibujar_panel_fft(screen, rect, onda, primary, lcd_text, font_small)`** Llama a `_calcular_fft_barras` y renderiza cada valor como una barra vertical. El color de cada barra se interpola entre el color primario oscurecido y el color primario saturado según su amplitud:

```python
bar_c = _lerp_color(_dim(primary, 0.25), primary, amp)
```

Encima de cada barra dibuja un cap de 2px con el color primario aclarado hacia blanco. Las etiquetas A1–A12 se alternan en dos alturas para evitar solapamiento cuando las barras son estrechas.

**`_calcular_layout_teclado(notas_config)`** Separa las notas del mapa en blancas (sin `#`) y negras (con `#`). Calcula el ancho de cada tecla blanca dividiendo el ancho disponible entre el número de blancas. Para las negras, localiza la posición X de la tecla blanca base (ej. `"C4"` para `"C#4"`) y la desplaza hacia la derecha:

```python
nota_blanca = nota[0] + nota[-1]   # "C#4" → "C4"
xb = nota_a_x[nota_blanca] + kw - bw // 2
```

Devuelve dos listas separadas porque el teclado se dibuja en dos pasadas: primero todas las blancas, luego todas las negras encima.

**`_dibujar_tecla_blanca` y `_dibujar_tecla_negra`** Cada función maneja tres estados visuales: presionada, en decaimiento y reposo. En el estado presionado la tecla se desplaza 4 píxeles hacia abajo (`off_y = 4`) para simular hundimiento físico. En el estado de decaimiento se interpola el color usando `_lerp_color` con el factor de `_decay_factor`. Ambas muestran la nota musical (`"C4"`, `"C#4"`) en lugar de la tecla QWERTY.

**`_get_grid_surf()`** Genera la superficie de cuadrícula CRT una única vez con `pygame.SRCALPHA` y la almacena en la variable global `_grid_surf`. En los frames siguientes simplemente devuelve la superficie ya creada. Dibujar líneas individuales 60 veces por segundo sería costoso; el cacheo convierte esa operación en un solo `screen.blit`.

**`dibujar_interfaz(screen, teclas_activas, datos_notas, notas_config, fuentes, instrumento_actual, mezcla_conversion)`** Es la función pública del archivo, llamada desde `main.py` exactamente una vez por frame. Orquesta el renderizado completo en este orden: fondo con cuadrícula CRT → panel info izquierdo (LED + nombre de instrumento) → panel LCD central (texto OUT/HZ + osciloscopio) → panel FFT derecho → barra de morph opcional → separador → fondo del teclado con rail rojo → teclas blancas → teclas negras → barra inferior de navegación. Si no hay teclas activas, el osciloscopio muestra una línea plana y el panel FFT muestra barras en cero.

---

### 5.5 Archivo: `main.py`

Punto de entrada del sistema. No contiene lógica de audio ni de renderizado; su rol es inicializar todos los subsistemas, conectar los eventos del teclado con el motor de síntesis y mantener el loop principal a 60 FPS.

**`verificar_archivos()`** Antes de inicializar Pygame, comprueba que cada ruta en `CONSTANTES.INSTRUMENTOS` existe en disco. Si falta algún `.wav`, llama a `exit(1)` inmediatamente. También verifica los JSON de armónicos en `datos/`: si no existen, llama silenciosamente a `analizar_instrumento` para generarlos, de modo que el sintetizador siempre arranque con los datos necesarios.

**`preparar_datos_interfaz(cache_notas, instrumento_actual)`** Construye los dos diccionarios que `dibujar_interfaz` necesita en cada frame. Para cada entrada en `CONSTANTES.MAPEO_TECLAS`, crea una entrada en `notas_config` con la nota string y una entrada en `datos_notas` con el nombre, la frecuencia y los primeros 380 samples de la onda convertidos a float:

```python
onda_float = onda_int.astype(np.float32) / 32768.0
```

La división por 32768 (no 32767) invierte la conversión de `nota_a_samples` de forma aproximada, devolviendo la señal al rango `[-1.0, 1.0]` que el osciloscopio espera. Si alguna nota del mapeo (como C6) no está en el caché porque está fuera de `OCTAVAS`, la genera al vuelo con `nota_a_samples`.

**Loop principal (`while corriendo`)** Procesa los eventos de Pygame en cada iteración:

- **Flechas izquierda/derecha:** Cambia `instrumento_actual`, recarga el caché completo con `precalentar_cache` para el nuevo instrumento y limpia `nota_activa_str`. El recalentado toma un momento perceptible porque sintetiza las 24 notas.
- **`KEYDOWN` de nota:** Agrega la nota a `nota_activa_str` y la reproduce inmediatamente:

```python
buffer = np.ascontiguousarray(cache_notas[nota]).tobytes()
sonido = pygame.mixer.Sound(buffer=buffer)
sonido.set_volume(0.5)
sonido.play()
```

`np.ascontiguousarray` garantiza que el array esté en memoria contigua antes de `tobytes()`, lo que Pygame exige para construir el `Sound` desde un buffer crudo.

- **`KEYUP` de nota:** Elimina la nota de `nota_activa_str`. El audio continúa sonando hasta que el ADSR lo apague naturalmente porque Pygame ya está reproduciendo la muestra en su propio buffer.

Al final de cada iteración construye `teclas_activas_ids` filtrando `MAPEO_TECLAS` por las notas activas y llama a `dibujar_interfaz`. Luego `clock.tick(60)` bloquea el proceso el tiempo necesario para mantener exactamente 60 frames por segundo.
##6. Consideraciones

## 6. Consideraciones
Los audios fueron grabados utilizando una herramienta llamada bandlab, sin embargo las dos guitarras no fueron grabadas en el mismo ambiente. La guitarra acústica fue grabada usando un micrófono dinámico FIFINE K688, mientras que la guitarra eléctrica usando un micrófono de celular. Lo cual debe ser una consideración importante a tener en cuenta.

Los audios fueron grabados siguiendo las siguientes consideraciones:

- **Nota grabada:** A4 (440 Hz)
- **Grabaciones** `.wav`
- **Formato:** mono (1 canal), cualquier bit depth que soporte `soundfile`
- **Duración recomendada:** mínimo 2 segundos para que el fragmento estable
  (60% central) tenga suficientes muestras
- **Sin efectos:** grabación limpia, sin reverb ni distorsión extrema
- **Ubicación exacta:** `audios/guitarra_electrica.wav` y `audios/guitarra_acustica.wav`

Los controles mas comodos fueron:

**Controles:**

| Tecla | Acción |
| --- | --- |
| `← →` | Cambiar instrumento |
| `Z–M`, `Q–U` | Notas C4–B5 |
| `S–J`, `2–7` | Semitonos |
| Cierre de ventana | Salir |

---
## 7. El mayor error

El mayor error radico en el dibujo del teclado, el cual fue un error muy simple pero que arruino completamente el sentido del proyecto

En `CONSTANTES.py` tenemos el mapeo de todas las teclas:

```python
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
```

La primera parte contiene todas las notas de la primer octava, la segunda todas las notas de la segunda octava, aparentemente todo iba bien. Sin embargo, el problema fue que justamente se esta dibujando dos veces el C5, una para el final de la primera octava y otra para el comienzo de la segunda octava.

<img width="1597" height="523" alt="image" src="https://github.com/user-attachments/assets/eb78a00d-87ac-45d9-924a-8650ecd51629" />

Se solucionó muy fácilmente corrigiendo esa parte del código de tal manera que eliminamos esas notas:**pygame.K_COMMA: "C5", pygame.K_l: "C#5", pygame.K_PERIOD: "D5"**

```python
MAPEO_TECLAS = {
    pygame.K_z: "C4",  pygame.K_s: "C#4", pygame.K_x: "D4",
    pygame.K_d: "D#4", pygame.K_c: "E4",  pygame.K_v: "F4",
    pygame.K_g: "F#4", pygame.K_b: "G4",  pygame.K_h: "G#4",
    pygame.K_n: "A4",  pygame.K_j: "A#4", pygame.K_m: "B4",
    
    
    pygame.K_q: "C5",  pygame.K_2: "C#5", pygame.K_w: "D5",
    pygame.K_3: "D#5", pygame.K_e: "E5",  pygame.K_r: "F5",
    pygame.K_5: "F#5", pygame.K_t: "G5",  pygame.K_6: "G#5",
    pygame.K_y: "A5",  pygame.K_7: "A#5", pygame.K_u: "B5",
    pygame.K_i: "C6"
}
```

<img width="1597" height="524" alt="image" src="https://github.com/user-attachments/assets/3bec4788-3350-4ffd-a650-abd4027b669b" />

Se dibuja perfectamente ahora, gracias a **dios**.

## 8. Conclusiones del Proyecto

1. **Equivalencia Matemática:** El software demuestra que es posible decodificar la señal acústica analógica a través de FFT, preservando los criterios de fidelidad mediante el control de la tasa de Nyquist.

2. **Diferencia de frecuencias:** Se observa la diferencia entre la frecuencia de dos instrumentos que aparentemente son iguales y deberían de tener la misma frecuencia, pero no es así.
   <img width="1950" height="750" alt="comparacion_armonicos" src="https://github.com/user-attachments/assets/80aee526-a11d-48de-b092-1fe0fe8fa21a" />


3. **Realismo de Audio:** El algoritmo comprueba que la síntesis aditiva puramente matemática requiere de modulaciones dinámicas en el tiempo (envolvente ADSR) para engañar al cerebro humano y recrear sensaciones auditivas orgánicas y musicales realistas.

   
