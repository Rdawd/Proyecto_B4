**Departamento de Ingeniería en Sistemas Computacionales (DASC)** **Universidad Autónoma de Baja California Sur (UABCS)** 

Este documento técnico describe los fundamentos físicos, matemáticos y de software detrás de un sintetizador de audio que funciona gracias a la FFT. El sistema se divide ,  en dos etapas: 

1. **Ingeniería Inversa (Análisis Espectral):** Extracción automatizada de los armónicos de instrumentos reales utilizando la Transformada Rápida de Fourier (FFT) y algoritmos de detección de picos en muestras `.wav`. 

2. 2. **Síntesis Aditiva (Reconstrucción):** Recreación digital interactiva de los timbres analizados mediante osciladores senoidales gobernados por el modelo de Temperamento Igual y controlados dinámicamente por envolventes temporales ADSR.

## 1. Teoría musical...

Para entender como funciona el proyecto hay que saber varias cosas de teoría musical como;octavas, tonos, semitonos,coma pitagórica, temperamento igual, entre otras.

Una **octava** se define matemáticamente como una duplicación exacta de la frecuencia de origen. Si una nota base vibra a una frecuencia $f$, su octava superior vibrará exactamente a $2f$. Nuestro cerebro percibe esta relación de duplicación como el mismo tono musical, pero situado en un registro más agudo. 

### 1.2 El Problema Pitagórico y la Coma Musical

Durante siglos, la afinación se basó en el sistema de Pitágoras, el cual construía la escala musical utilizando intervalos basados en fracciones de números enteros perfectos, principalmente la relación $3:2$ (conocida como la *Quinta Perfecta*). 
Sin embargo, la física y las matemáticas presentan una incompatibilidad fundamental conocida como la **Coma Pitagórica**: si apilas 12 quintas perfectas calculadas mediante fracciones puras ($(3/2)^{12}$), deberías llegar exactamente a la misma frecuencia que si apilas 7 octavas puras ($2^7$). En la realidad, existe una pequeña discrepancia:
                                 $(1.5)^{12} \approx 129.746 \neq 2^7 = 128$
Esta imperfección provocaba que un instrumento afinado perfectamente para tocar en una tonalidad (por ejemplo, Do mayor) sonara extremadamente desafinado y disonante al intentar tocar en otra tonalidad (como Fa sostenido). A estos intervalos inservibles se les conocía históricamente como el "acorde del lobo".

### 1.3 La Solución Moderna: El Temperamento Igual

Para solucionar este problema de raíz y permitir la modulación entre tonalidades sin reafinar el instrumento, los matemáticos y músicos del siglo XVII desarrollaron el **Temperamento Igual**. 
Este sistema consiste en dividir las notas de manera uniforme: el espacio de la octava se divide en **12 escalones idénticos** llamados **semitonos**. Como el oído humano no percibe la frecuencia de manera lineal (sumando), sino de manera logarítmica (multiplicando), cada escalón debe calcularse multiplicando la nota anterior por un factor geométrico constante. Este factor es la **raíz doceava de 2**:
                                                 $\sqrt[12]{2} \approx 1.059463094$
Si multiplicamos una frecuencia base por este "número mágico" 12 veces consecutivas, habremos duplicado la frecuencia con precisión matemática absoluta:
$f \times (\sqrt[12]{2})^{12} = f \times 2 = 2f \text{ (Una octava completa)}$


La fórmula general para calcular la frecuencia de cualquier nota musical $f_n$ a una distancia de $n$ semitonos de una nota de referencia $f_0$ es:
$f_n = f_0 \times 2^{\frac{n}{12}}$

### 1.4 El Estándar Internacional ISO 16

La elección de la frecuencia de inicio es NO es arbitraria. En la antigüedad, cada ciudad u orquesta afinaba bajo sus propios criterios (oscilando entre 392 Hz y 480 Hz).  En **1939**, una conferencia internacional en Londres fijó la nota **La de la cuarta octava (A4)** a un valor estándar de **440 Hz**, lo cual fue posteriormente ratificado por la Organización Internacional de Normalización bajo la norma **ISO 16**. 

## 2. Procesamiento Digital de Señales: La Transformada de Fourier (FFT)

### 2.1 El Límite Físico del Audio Digital (Teorema de Nyquist)

Un sistema informático no puede almacenar ondas continuas del mundo real; debe digitalizarlas tomando muestras periódicas de la amplitud. La velocidad a la que se toman estas capturas se denomina **Tasa de Muestreo (Sample Rate)**. El estándar de alta fidelidad utilizado en este proyecto es `TASA_MUESTREO = 44100` (44.1 kHz, o 44,100 muestras de audio por segundo).
De acuerdo con el **Teorema de Muestreo de Nyquist-Shannon** que nos recomendo la IA, para reconstruir o analizar digitalmente una onda de manera perfecta, se necesita tomar, como mínimo, dos muestras por cada ciclo completo (una muestra en el punto más alto de la ola y otra en el punto más bajo). Por lo tanto, la frecuencia máxima que nuestro software puede procesar de forma segura es la mitad exacta de la tasa de muestreo:
$\text{Frecuencia de Nyquist} = \frac{\text{TASA\_MUESTREO}}{2} = \frac{44100}{2} = 22,050 \text{ Hz}$
Cualquier frecuencia del mundo real superior a los 22,050 Hz que intente ingresar al sistema sufrirá un fenómeno de distorsión destructiva llamado **Aliasing**, donde la computadora "alucina" frecuencias falsas e inexistentes en el espectro grave.

### 2.2 Análisis Espectral y Detección de Picos mediante SciPy

Cuando una cuerda de guitarra vibra, no produce una onda senoidal pura de 440 Hz. La cuerda vibra en toda su longitud, pero también genera ondas secundarias simultáneas al vibrar en mitades, tercios y cuartos. Estas vibraciones se denominan **Armónicos** y constituyen múltiplos enteros de la frecuencia fundamental ($1 \times f_0, 2 \times f_0, 3 \times f_0 \dots$). La suma de todos estos armónicos define el **Timbre** único del instrumento.
Para extraer esta información de los archivos de audio reales, el archivo `analizar_audio_fft.py` calcula la Transformada Rápida de Fourier (FFT). La FFT toma una señal desordenada en el dominio del tiempo y la descompone en un abanico que muestra la amplitud de cada frecuencia individual presente en el rango de 0 a 22,050 Hz.
Para aislar los armónicos verdaderos del siseo analógico y el ruido de fondo del micrófono, el script ejecuta un filtrado matemático avanzado que hizo la IA mediante la función `find_peaks` de la librería `scipy.signal`:

`indices, _ = signal.find_peaks(magnitudes, height=0.01, distance=20)`

- **`height=0.01` (Umbral de Amplitud Mínima):** Dado que las magnitudes del espectro están normalizadas (donde el pico más alto vale 1.0), este parámetro instruye al sistema a descartar de forma fulminante cualquier componente frecuencial cuya energía sea inferior al 1% de la señal principal. Esto elimina eficazmente el ruido base.

- **`distance=20` (Separación Inter-Espectral):** En una FFT real, los picos de frecuencia no ocupan un solo píxel; son montañitas con cierta anchura. Sin este parámetro, el algoritmo contaría la cima de la montaña y los bachecitos de sus laderas como múltiples armónicos diferentes. Al exigir una distancia mínima de 20 muestras físicas dentro del arreglo, el sistema garantiza saltar a la siguiente zona espectral limpia, capturando armónicos independientes bien diferenciados.

### 2.3 El Concepto de Ratios: Independencia de Notas

Un aspecto crítico de ingeniería en este software es que no almacena las frecuencias absolutas en Hertz descubiertas por la FFT. Si el software guardara textualmente que la guitarra tiene un pico en 440 Hz y otro en 880 Hz, esa firma acústica quedaría congelada y solo serviría para reproducir la nota La4.

Para poder conseguir las demás notas, el analizador convierte las frecuencias en **Ratios (Proporciones Relativas)** dividiendo cada frecuencia armónica detectada entre la frecuencia fundamental ($f_0$):

$\text{Ratio} = \frac{\text{Frecuencia del Armónico}}{\text{Frecuencia Fundamental}}$

- Para el primer armónico (fundamental): $440 / 440 = 1.0$

- Para el segundo armónico: $880 / 440 = 2.0$

Este se almacena en archivos JSON en el directorio `datos/`. De esta forma, si el músico presiona la nota Do5 ($f_0 = 523.25\text{ Hz}$), el sintetizador recupera el molde y calcula los osciladores multiplicando la nueva base por los ratios guardados ($523.25 \times 1.0, 523.25 \times 2.0 \dots$), preservando el timbre idéntico de la guitarra en cualquier registro de altura.

---

## 3. Síntesis Aditiva y Modulación Temporal (ADSR)

### 3.1 Reconstrucción por Síntesis Aditiva

En el archivo `sintetizador.py`, el proceso se invierte. El software lee el archivo JSON del instrumento seleccionado y recrea el sonido mediante **Síntesis Aditiva**, la cual establece que cualquier sonido complejo puede recrearse sumando ondas senoidales puras escaladas adecuadamente en frecuencia y volumen.

Por cada armónico en el perfil, el software calcula su frecuencia de destino y genera matemáticamente la onda mediante la función trigonométrica seno (`np.sin`):

Python

```
señal += amp * np.sin(2 * np.pi * freq_armonico * t)
```

### 3.2 La Envolvente Dinámica ADSR

Si se reproducen las ondas senoidales puras calculadas, el sintetizador generaría un sonido estéril, estático y artificial. Esto ocurre porque en los instrumentos reales, el volumen no aparece y desaparece instantáneamente; el sonido evoluciona con el tiempo.

Para emular el comportamiento físico de los instrumentos mecánicos, la función `aplicar_adsr` aplica una envolvente de volumen segmentada en cuatro etapas clave sobre la señal digitalizada:

Python

```
i_attack = int(0.05 * N)
i_decay = int(0.15 * N)   # 5% attack + 10% decay
i_sustain = int(0.85 * N) # Restan 15% para release
```

1. **Attack (Ataque - Primer 5% de la nota):** Modula el volumen de forma lineal desde 0.0 hasta su nivel máximo (1.0). Imita el impacto inicial de la púa sobre la cuerda.

2. **Decay (Decaimiento - Siguiente 10% de la nota):** Disminuye paulatinamente el volumen desde el pico máximo de excitación hasta el nivel de estabilización de la nota.

3. **Sustain (Sostenimiento - Del 15% al 85% de la nota):** Mantiene el volumen en un nivel constante y controlado (fijado en 0.7 en el código) mientras la tecla permanezca idealmente presionada.

4. **Release (Relajación - Último 15% de la nota):** Provoca una rampa descendente suave de volumen desde el nivel de sustain hasta el silencio absoluto (0.0), emulando cómo la vibración de la cuerda se apaga debido a la fricción natural del aire y la madera.

---

## 4.Implementación Explícita de la Transformada de Fourier (FFT)







---



## 5. Cartografía del Código: Líneas Exactas por Archivo

A continuación, se presentan los fragmentos de código exactos de la arquitectura del proyecto que sustentan científicamente los puntos anteriores.

### 5.1 Archivo: `CONSTANTES.py`

Establece los parámetros globales de la arquitectura, la configuración del hardware de audio simulado y los temas estéticos de la interfaz gráfica DASC.

Python

```
TASA_MUESTREO = 44100  # Frecuencia de muestreo (Nyquist = 22050 Hz)
DURACION_NOTA = 1.5
NOTA_BASE = "A4"
FREQ_BASE = 440.0      # Estándar ISO 16
NUM_ARMONICOS = 20     # Cantidad máxima de picos a procesar
```

### 5.2 Archivo: `analizar_audio_fft.py`

Contiene la lógica de ingeniería inversa para procesar las ondas `.wav`, aplicar la FFT y filtrar los componentes espectrales mediante SciPy.

Python

```
def aplicar_fft(fragmento: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    ventana    = np.hanning(len(fragmento)) # Ventana para evitar artefactos en bordes
    espectro   = np.fft.rfft(fragmento * ventana)
    freqs      = np.fft.rfftfreq(len(fragmento), 1 / sr)
    magnitudes = np.abs(espectro)
    if magnitudes.max() > 0:
        magnitudes /= magnitudes.max()      # Normalización a escala 0.0 - 1.0
    return freqs, magnitudes

def detectar_picos(freqs, magnitudes, n=CONSTANTES.NUM_ARMONICOS):
    # Detección y filtrado de ruido mediante parámetros numéricos de altura y distancia
    indices, _ = signal.find_peaks(magnitudes, height=0.01, distance=20)
    picos = sorted([(freqs[i], magnitudes[i]) for i in indices],
                   key=lambda x: x[1], reverse=True)
    return picos[:n]
```

### 5.3 Archivo: `sintetizador.py`

Contiene el motor de cálculo matemático del sintetizador, la fórmula del temperamento igual y la modulación aditiva de la señal.

Python

```
def freq_de_nota(nota_str: str) -> float:
    nombre = nota_str[:-1]
    octava = int(nota_str[-1])
    indice_nota = CONSTANTES.NOTAS.index(nombre)
    indice_a4 = 9 
    octava_base = 4
    # Cálculo algebraico del número de semitonos de distancia respecto a A4
    semitonos = (octava - octava_base) * 12 + (indice_nota - indice_a4)
    # Aplicación estricta de la fórmula logarítmica de Temperamento Igual
    return CONSTANTES.FREQ_BASE * (2 ** (semitonos / 12))

def sintetizar_nota(freq: float, perfil: list, sr: int, duracion: float) -> np.ndarray:
    t = np.linspace(0, duracion, int(sr * duracion), False)
    señal = np.zeros_like(t)

    for ratio, amp in perfil:
        freq_armonico = freq * ratio
        # Aplicación directa del Teorema de Nyquist para evitar Aliasing
        if freq_armonico < sr / 2:
            señal += amp * np.sin(2 * np.pi * freq_armonico * t)

    max_val = np.max(np.abs(señal))
    if max_val > 0:
        señal /= max_val # Evita la saturación digital (Clipping)

    return aplicar_adsr(señal, sr)
```

### 5.4 Archivo: `interfaz.py`

Se encarga del renderizado gráfico de la señal sintetizada, dibujando un osciloscopio virtual y una gráfica FFT en tiempo real en el panel superior de la ventana.

Python

```
def _calcular_fft_barras(onda: np.ndarray, n_bars: int = CONSTANTES.NUM_BARRAS_FFT) -> list[float]:
    if len(onda) == 0:
        return [0.0] * n_bars
    N = len(onda)
    ventana = np.hanning(N)
    espectro = np.abs(np.fft.rfft(onda * ventana, n=CONSTANTES.BINS_FFT))
    if espectro.max() > 0:
        espectro /= espectro.max()
    max_bins = min(len(espectro), 250)
    espectro_util = espectro[1:max_bins]
    bin_total = len(espectro_util)
    step = max(1, bin_total // n_bars)
    barras = []
    for i in range(n_bars): 
        idx_start = i * step
        idx_end = idx_start + step if i < n_bars - 1 else bin_total
        chunk = espectro_util[idx_start:idx_end]
        barras.append(float(chunk.max()) if len(chunk) > 0 else 0.0)
    return barras
```

### 5.5 Archivo: `main.py`

Orquestador del sistema. Vincula los eventos físicos del teclado numérico/alfabético QWERTY de la computadora con el disparador de muestras de Pygame Mixer.

Python

```
elif e.key in CONSTANTES.MAPEO_TECLAS:
    nota = CONSTANTES.MAPEO_TECLAS[e.key]
    if nota not in nota_activa_str:
        nota_activa_str.add(nota)
        if nota in cache_notas:
            # Conversión de la matriz matemática de Numpy a un búfer binario de audio crudo
            buffer = np.ascontiguousarray(cache_notas[nota]).tobytes()
            sonido = pygame.mixer.Sound(buffer=buffer)
            sonido.set_volume(0.5)
            sonido.play()
```

---

## 6. Conclusiones del Proyecto

1. **Equivalencia Matemática:** El software demuestra que es posible decodificar la señal acústica analógica a través de herramientas discretas de Fourier, preservando los criterios de fidelidad mediante el control de la tasa de Nyquist.

2. **Modularidad y Escalabilidad:** Al desacoplar la frecuencia absoluta a través del cálculo de ratios y mapas JSON, el sistema se transforma en un verdadero instrumento polifónico ágil, demostrando buenas prácticas de arquitectura de software para ingeniería en sistemas computacionales.

3. **Realismo de Audio:** El algoritmo comprueba que la síntesis aditiva puramente matemática requiere de modulaciones dinámicas en el tiempo (envolvente ADSR) para engañar al cerebro humano y recrear sensaciones auditivas orgánicas y musicales realistas.


