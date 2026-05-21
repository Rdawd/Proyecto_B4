# Sintetizador de Señales DASC (FFT-Based)

Proyecto de análisis y síntesis de audio para el para el curso **Matemáticas IV** del Departamento Académico de Sistemas Computacionales (DASC), Universidad Autónoma de Baja California Sur.

Este sistema demuestra experimentalmente que instrumentos distintos (guitarra eléctrica vs. acústica) generan espectros armónicos únicos a pesar de tocar la misma nota (A4 = 440 Hz). El proyecto utiliza la **Transformada Rápida de Fourier (FFT)** para capturar la "huella digital" sonora (timbre) y recrearla con el **temperamento igual**. Además se desarrollo un sintetizador que permite escuchar las demás notas tomando como base la misma nota:.

<img width="1596" height="524" alt="image" src="https://github.com/user-attachments/assets/5e4234ad-d68c-4def-909e-eb7e744e9d0c" />

<img width="1950" height="750" alt="comparacion_armonicos" src="https://github.com/user-attachments/assets/7ce5fda5-d7df-41fe-9e4a-8168a20509d8" />



## Estructura

- **`main.py`**: Punto de entrada principal; gestiona el loop de la aplicación y la lógica de interacción.

- **`analizar_audio_fft.py`**: Pipeline de procesamiento; realiza la carga de `.wav`, aplicación de ventana Hanning y detección de picos espectrales.

- **`comparar_fft_de_cada_audio.py`**: Módulo de visualización científica para comparar frecuencias y amplitudes entre instrumentos.

- **`sintetizador.py`**: Motor de síntesis; genera ondas mediante la suma de senoides basadas en los armónicos detectados y aplica una envolvente **ADSR**.

- **`interfaz.py`**: Sistema visual desarrollado en Pygame con osciloscopio de rastro de fósforo, panel FFT y teclado virtual.

- **`CONSTANTES.py`**: Configuración global del sistema, mapeo de frecuencias y paletas de colores (Temas DASC).

## Requisitos

- Contar con los archivos de audio originales en la ruta `audios/guitarra_electrica.wav` y `audios/guitarra_acustica.wav`.

- Nota de referencia grabada: **A4 (440 Hz)**.

## Instalación

```
pip install pygame numpy soundfile scipy matplotlib
```

## Uso

**Recuerda tener los audios en la carpeta audios.**

Para un flujo de trabajo completo, ejecute los módulos en el siguiente orden:

```
# 1. Analizar los audios originales y extraer tablas de armónicos
python analizar_audio_fft.py

# 2. Generar gráficas comparativas de espectro y barras (se guardan en datos/)
python comparar_fft_de_cada_audio.py

# 3. Iniciar el sintetizador interactivo
python main.py
```

Aunque los pasos 1 y 2 son opcionales si `datos/` ya contiene los JSON. `main.py` los genera automáticamente si no existen. **Sí es necesario tener los audios en la carpeta audios.**

### Controles del Sintetizador

- **Flechas Izquierda / Derecha (`←` `→`)**: Cambiar entre el motor de síntesis de guitarra eléctrica y acústica.

- **Teclas `Z-M` y `Q-U`**: Tocar el teclado musical (Octavas 4 y 5), **semi tonos** `S-J` y `2-7`

---

> Los archivos generados en la carpeta `datos/` (`.json` y `.png`) son producidos dinámicamente por el script de análisis analizar_audio_fft.py y  python comparar_fft_de_cada_audio.py.
