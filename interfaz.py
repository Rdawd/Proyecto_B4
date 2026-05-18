
import pygame
import numpy as np
import math
import CONSTANTES

# ─────────────────────────────────────────────
#  HELPERS DE COLOR
# ─────────────────────────────────────────────
def _tema(instrumento_actual: str) -> dict:
    key = instrumento_actual.lower()
    for k in CONSTANTES.TEMAS:
        if k in key:
            return CONSTANTES.TEMAS[k]
    return CONSTANTES.TEMA_POR_DEFECTO


def _alpha_surf(color: tuple, alpha: int, size: tuple) -> pygame.Surface:
    s = pygame.Surface(size, pygame.SRCALPHA)
    s.fill((*color, alpha))
    return s


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _dim(color, factor):
    return tuple(max(0, int(c * factor)) for c in color)


# ─────────────────────────────────────────────
#  FUENTES
# ─────────────────────────────────────────────
def inicializar_fuentes():
    pygame.font.init()
    font_small = pygame.font.SysFont("couriernew", 11, bold=True)
    font_lcd   = pygame.font.SysFont("couriernew", 15, bold=True)
    font_main  = pygame.font.SysFont("couriernew", 12, bold=True)
    return font_small, font_lcd, font_main


# ─────────────────────────────────────────────
#  ESTADO GLOBAL — decaimiento de teclas
# ─────────────────────────────────────────────
# kid → timestamp (ms) del último KEYDOWN
_decay_timestamps: dict[int, int] = {}

def registrar_keydown(kid: int):
    """Llamar desde main.py en cada KEYDOWN de nota."""
    _decay_timestamps[kid] = pygame.time.get_ticks()

def _decay_factor(kid: int, t_now: int) -> float:
    """Devuelve 1.0 si la tecla sigue activa, 0..1 durante el decaimiento, 0.0 si ya pasó."""
    ts = _decay_timestamps.get(kid, 0)
    elapsed = t_now - ts
    if elapsed >= CONSTANTES.TIEMPO_DECAIMIENTO_MS:
        return 0.0
    return 1.0 - elapsed / CONSTANTES.TIEMPO_DECAIMIENTO_MS


# ─────────────────────────────────────────────
#  LED PULSANTE
# ─────────────────────────────────────────────
def _dibujar_led(screen, cx, cy, color, t):
    pulse = 0.55 + 0.45 * math.sin(t * 0.003)
    rings = [
        (18, int(18  * pulse)),
        (13, int(45  * pulse)),
        (8,  int(110 * pulse)),
        (4,  220),
    ]
    for radius, alpha in rings:
        s = _alpha_surf(color, alpha, (radius * 2, radius * 2))
        screen.blit(s, (cx - radius, cy - radius))
    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 3)


# ─────────────────────────────────────────────
#  OSCILOSCOPIO — phosphor trail
# ─────────────────────────────────────────────
def _dibujar_osciloscopio(screen, rect: pygame.Rect, onda: np.ndarray,
                           lcd_text: tuple, t: int):
    ox, oy, ow, oh = rect.x, rect.y, rect.width, rect.height
    mid_y = oy + oh // 2

    grid_color = _dim(lcd_text, 0.07)
    for row in range(1, 3):
        yg = oy + oh * row // 3
        pygame.draw.line(screen, grid_color, (ox, yg), (ox + ow, yg), 1)
    for col in range(1, 6):
        xg = ox + ow * col // 6
        pygame.draw.line(screen, grid_color, (xg, oy), (xg, oy + oh), 1)

    if len(onda) == 0:
        return

    N = len(onda)
    max_val = np.max(np.abs(onda))
    if max_val == 0:
        max_val = 1.0

    def build_points(offset_frames):
        shifted = np.roll(onda, -int((t * 0.25 + offset_frames) % N))
        pts = []
        for i in range(ow):
            idx = int(i / ow * N)
            val = shifted[idx] / max_val
            y = int(mid_y - val * (oh * 0.42))
            pts.append((ox + i, y))
        return pts

    for offset_f, width, alpha in [(20, 6, 30), (10, 4, 80), (0, 2, 255)]:
        pts = build_points(offset_f)
        if len(pts) > 1:
            surf = pygame.Surface((ow, oh), pygame.SRCALPHA)
            local = [(p[0] - ox, p[1] - oy) for p in pts]
            pygame.draw.lines(surf, (*lcd_text, alpha), False, local, width)
            screen.blit(surf, (ox, oy))

    pts = build_points(0)
    if len(pts) > 1:
        hi = pygame.Surface((ow, oh), pygame.SRCALPHA)
        local = [(p[0] - ox, p[1] - oy) for p in pts]
        pygame.draw.lines(hi, (255, 255, 255, 150), False, local, 1)
        screen.blit(hi, (ox, oy))


# ─────────────────────────────────────────────
#  FFT EN TIEMPO REAL — panel lateral derecho
# ─────────────────────────────────────────────
def _calcular_fft_barras(onda: np.ndarray, n_bars: int = CONSTANTES.NUM_BARRAS_FFT) -> list[float]:
    """Calcula la FFT de la onda y devuelve n_bars amplitudes normalizadas."""
    if len(onda) == 0:
        return [0.0] * n_bars

    # 1. Zero-padding para mejorar la interpolación visual
    N = len(onda)
    ventana = np.hanning(N)
    
    espectro = np.abs(np.fft.rfft(onda * ventana, n=CONSTANTES.BINS_FFT))
    
    if espectro.max() > 0:
        espectro /= espectro.max()

    # 2. Enfocar en el rango musical
    max_bins = min(len(espectro), 250)
    espectro_util = espectro[1:max_bins]
    
    # 3. Dividir el espectro útil en n_bars
    bin_total = len(espectro_util)
    step = max(1, bin_total // n_bars)
    barras = []
    
    for i in range(n_bars): 
        idx_start = i * step
        idx_end = idx_start + step if i < n_bars - 1 else bin_total
        
        chunk = espectro_util[idx_start:idx_end]
        barras.append(float(chunk.max()) if len(chunk) > 0 else 0.0)
        
    return barras

def _dibujar_panel_fft(screen, rect: pygame.Rect, onda: np.ndarray,
                        primary: tuple, lcd_text: tuple, font_small):
    ox, oy, ow, oh = rect.x, rect.y, rect.width, rect.height

    # Fondo del panel
    pygame.draw.rect(screen, (9, 10, 14), rect)
    pygame.draw.line(screen, _dim(primary, 0.22), (ox, oy), (ox, oy + oh), 1)

    label = font_small.render("FFT", True, _dim(primary, 0.35))
    screen.blit(label, (ox + ow // 2 - label.get_width() // 2, oy + 6))

    barras = _calcular_fft_barras(onda, CONSTANTES.NUM_BARRAS_FFT)
    n      = len(barras)
    area_y = oy + 22
    
    area_h = oh - 55 
    bar_w  = (ow - 16 - (n - 1) * 2) // n

    for i, amp in enumerate(barras):
        bh_px  = max(2, int(area_h * amp))
        bx     = ox + 8 + i * (bar_w + 2)
        by     = area_y + area_h - bh_px
        
        bar_c  = _lerp_color(_dim(primary, 0.25), primary, amp)
        pygame.draw.rect(screen, bar_c, (bx, by, bar_w, bh_px), border_radius=2)
        
        cap_c  = _lerp_color(primary, (255, 255, 255), 0.4)
        pygame.draw.rect(screen, cap_c, (bx, by, bar_w, 2))
        
        if bar_w >= 4:
            a_lbl = font_small.render(f"A{i+1}", True, _dim(primary, 0.45))
            offset_y = 2 if i % 2 == 0 else 14
            screen.blit(a_lbl, (bx + bar_w // 2 - a_lbl.get_width() // 2, area_y + area_h + offset_y))


# ─────────────────────────────────────────────
#  TECLADO PIANO
# ─────────────────────────────────────────────
def _calcular_layout_teclado(notas_config: dict):
    blancas   = [(k, v[0]) for k, v in notas_config.items() if "#" not in v[0]]
    negras    = [(k, v[0]) for k, v in notas_config.items() if "#" in  v[0]]
    n_blancas = len(blancas)
    if n_blancas == 0:
        return [], []

    margin, spacing = 12, 2
    kw = (CONSTANTES.ANCHO_VENTANA - margin * 2 - spacing * (n_blancas - 1)) // n_blancas
    kh = CONSTANTES.ALTO_AREA_TECLADO - 6
    bw = int(kw * 0.54)
    bh = int(kh * 0.60)

    white_data = []
    for i, (kid, nota) in enumerate(blancas):
        x = margin + i * (kw + spacing)
        white_data.append((kid, nota, x, kw, kh))

    nota_a_x   = {nota: x for _, nota, x, _, _ in white_data}
    black_data = []
    for kid, nota in negras:
        nota_blanca = nota[0] + nota[-1]
        if nota_blanca in nota_a_x:
            xb = nota_a_x[nota_blanca] + kw - bw // 2
            black_data.append((kid, nota, xb, bw, bh))

    return white_data, black_data


def _dibujar_tecla_blanca(screen, x, y, w, h, presionada, nota_str, decay,
                           color_tema, fuente):
    pygame.draw.rect(screen, (8, 8, 10), (x + 3, y + 5, w, h), border_radius=4)

    if presionada:
        r, g, b   = color_tema
        key_color = (min(255, r // 2 + 140), min(255, g // 2 + 140), min(255, b // 2 + 140))
        border_c  = color_tema
        text_c    = _dim(color_tema, 0.7)
        off_y     = 4
    elif decay > 0.0:
        key_color = _lerp_color((238, 238, 230), color_tema, decay * 0.45)
        border_c  = _lerp_color((80, 80, 80), color_tema, decay)
        text_c    = _lerp_color((130, 130, 130), color_tema, decay * 0.8)
        off_y     = 0
    else:
        key_color = (238, 238, 230)
        border_c  = (80, 80, 80)
        text_c    = (130, 130, 130)
        off_y     = 0

    rect = pygame.Rect(x, y + off_y, w, h - off_y)
    pygame.draw.rect(screen, key_color, rect, border_radius=4)
    hl = (255, 255, 255) if not presionada else _lerp_color(color_tema, (255, 255, 255), 0.5)
    pygame.draw.line(screen, hl, (x + 1, y + off_y + 3), (x + 1, y + h - 8), 1)
    pygame.draw.rect(screen, border_c, rect, 1, border_radius=4)

    lbl = fuente.render(nota_str, True, text_c)
    screen.blit(lbl, (x + w // 2 - lbl.get_width() // 2, y + h - 22 + off_y))


def _dibujar_tecla_negra(screen, x, y, w, h, presionada, nota_str, decay,
                          color_tema, fuente):
    pygame.draw.rect(screen, (4, 4, 6), (x + 3, y + 3, w, h + 3), border_radius=3)

    if presionada:
        key_color = _dim(color_tema, 0.35)
        border_c  = color_tema
        text_c    = color_tema
        off_y     = 4
    elif decay > 0.0:
        key_color = _lerp_color((22, 22, 26), _dim(color_tema, 0.35), decay * 0.6)
        border_c  = _lerp_color((50, 50, 55), color_tema, decay)
        text_c    = _lerp_color((60, 60, 65), color_tema, decay * 0.8)
        off_y     = 0
    else:
        key_color = (22, 22, 26)
        border_c  = (50, 50, 55)
        text_c    = (60, 60, 65)
        off_y     = 0

    rect = pygame.Rect(x, y + off_y, w, h - off_y)
    pygame.draw.rect(screen, key_color, rect, border_radius=3)
    hl_c = (80, 80, 85) if not presionada else _lerp_color(color_tema, (200, 200, 200), 0.3)
    pygame.draw.line(screen, hl_c, (x + 2, y + off_y + 2), (x + w - 3, y + off_y + 2), 1)
    pygame.draw.rect(screen, border_c, rect, 1, border_radius=3)

    lbl = fuente.render(nota_str, True, text_c)
    screen.blit(lbl, (x + w // 2 - lbl.get_width() // 2, y + h - 18 + off_y))


# ─────────────────────────────────────────────
#  BARRA DE MORPH
# ─────────────────────────────────────────────
def _dibujar_morph(screen, mezcla: float, font_small, y_center):
    bx, bw, bh = CONSTANTES.ANCHO_INFO + 10, CONSTANTES.ANCHO_LCD - 20, 4
    by = y_center - bh // 2

    for i in range(bw):
        c = _lerp_color(CONSTANTES.TEMAS["electrica"]["primary"], CONSTANTES.TEMAS["acustica"]["primary"], i / bw)
        pygame.draw.line(screen, _dim(c, 0.3), (bx + i, by), (bx + i, by + bh))

    fill_w = int(bw * mezcla)
    for i in range(fill_w):
        c = _lerp_color(CONSTANTES.TEMAS["electrica"]["primary"], CONSTANTES.TEMAS["acustica"]["primary"], i / bw)
        pygame.draw.line(screen, c, (bx + i, by), (bx + i, by + bh))

    tx = bx + fill_w - 5
    thumb = pygame.Rect(tx, by - 6, 10, 16)
    pygame.draw.rect(screen, (200, 200, 205), thumb, border_radius=3)
    pygame.draw.rect(screen, (100, 100, 105), thumb, 1, border_radius=3)

    el = font_small.render("ELEC", True, _dim(CONSTANTES.TEMAS["electrica"]["primary"], 0.7))
    ac = font_small.render("ACUS", True, _dim(CONSTANTES.TEMAS["acustica"]["primary"],  0.7))
    screen.blit(el, (bx - el.get_width() - 6, by - 4))
    screen.blit(ac, (bx + bw + 6, by - 4))

    pct = font_small.render(f"{int(mezcla * 100):3d}%", True, (70, 85, 95))
    screen.blit(pct, (bx + bw // 2 - pct.get_width() // 2, by - 16))


# ─────────────────────────────────────────────
#  CUADRÍCULA CRT (cacheada)
# ─────────────────────────────────────────────
_grid_surf = None

def _get_grid_surf():
    global _grid_surf
    if _grid_surf is not None:
        return _grid_surf
    _grid_surf = pygame.Surface((CONSTANTES.ANCHO_VENTANA, CONSTANTES.ALTO_VENTANA), pygame.SRCALPHA)
    gc = (255, 255, 255, 5)
    for x in range(0, CONSTANTES.ANCHO_VENTANA, 20):
        pygame.draw.line(_grid_surf, gc, (x, 0), (x, CONSTANTES.ALTO_VENTANA))
    for y in range(0, CONSTANTES.ALTO_VENTANA, 20):
        pygame.draw.line(_grid_surf, gc, (0, y), (CONSTANTES.ANCHO_VENTANA, y))
    return _grid_surf


# ─────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────
def dibujar_interfaz(screen, teclas_activas, datos_notas, notas_config,
                     fuentes, instrumento_actual, mezcla_conversion=None):

    font_small, font_lcd, font_main = fuentes
    tema     = _tema(instrumento_actual)
    primary  = tema["primary"]
    lcd_bg   = tema["lcd_bg"]
    lcd_text = tema["lcd_text"]
    lcd_mid  = tema["lcd_mid"]
    led_c    = tema["led_color"]
    t        = pygame.time.get_ticks()
    pressed  = pygame.key.get_pressed()

    # ── FONDO ────────────────────────────────
    screen.fill((11, 12, 16))
    screen.blit(_get_grid_surf(), (0, 0))

    # ── PANEL SUPERIOR ───────────────────────
    pygame.draw.rect(screen, (13, 14, 18), (0, 0, CONSTANTES.ANCHO_VENTANA, CONSTANTES.ALTO_PANEL))
    pygame.draw.line(screen, primary, (0, CONSTANTES.ALTO_PANEL - 1), (CONSTANTES.ANCHO_VENTANA, CONSTANTES.ALTO_PANEL - 1), 2)

    # ══ PANEL INFO (izquierda) ═══════════════
    pygame.draw.rect(screen, (10, 11, 15), (0, 0, CONSTANTES.ANCHO_INFO, CONSTANTES.ALTO_PANEL))
    pygame.draw.line(screen, _dim(primary, 0.22), (CONSTANTES.ANCHO_INFO - 1, 0), (CONSTANTES.ANCHO_INFO - 1, CONSTANTES.ALTO_PANEL), 1)

    sys_lbl = font_small.render("D A S C", True, (28, 36, 46))
    screen.blit(sys_lbl, (12, 10))

    _dibujar_led(screen, 26, 50, led_c, t)
    screen.blit(font_lcd.render(instrumento_actual.upper(), True, primary), (50, 40))
    screen.blit(font_small.render("DASC SINTETIZADOR", True, _dim(primary, 0.28)), (50, 58))

    pygame.draw.line(screen, _dim(primary, 0.12), (12, 74), (CONSTANTES.ANCHO_INFO - 12, 74), 1)

    # ══ PANEL LCD (centro) ═══════════════════
    lcd_x = CONSTANTES.ANCHO_INFO

    pygame.draw.rect(screen, lcd_bg, (lcd_x, 0, CONSTANTES.ANCHO_LCD, CONSTANTES.ALTO_PANEL))
    pygame.draw.rect(screen, _dim(lcd_text, 0.10), (lcd_x, 0, CONSTANTES.ANCHO_LCD, CONSTANTES.ALTO_PANEL), 1)

    header = font_small.render(
        "── OUTPUT ──────────────────────────────────────────────────────",
        True, _dim(lcd_text, 0.16)
    )
    screen.blit(header, (lcd_x + 8, 8))

    onda_fft = np.zeros(380, dtype=np.float32)

    if teclas_activas:
        nombres = [datos_notas[t_k]["nombre"] for t_k in teclas_activas]
        freqs   = [f"{datos_notas[t_k]['freq']:.1f}" for t_k in teclas_activas]
        s_notas = ", ".join(nombres[:5]) + ("..." if len(nombres) > 5 else "")
        s_freqs = " + ".join(freqs[:5])  + ("..." if len(freqs)   > 5 else "")

        screen.blit(font_lcd.render(f"OUT:  {s_notas}", True, lcd_text), (lcd_x + 8, 22))
        screen.blit(font_lcd.render(f"HZ:   {s_freqs}", True, lcd_mid),  (lcd_x + 8, 40))

        osc_rect = pygame.Rect(lcd_x + 6, 58, CONSTANTES.ANCHO_LCD - 12, CONSTANTES.ALTO_PANEL - 66)
        pygame.draw.rect(screen, (3, 7, 10), osc_rect)
        pygame.draw.rect(screen, _dim(lcd_text, 0.13), osc_rect, 1)

        onda = np.copy(datos_notas[teclas_activas[0]]["onda"])
        for t_k in teclas_activas[1:]:
            onda = onda + datos_notas[t_k]["onda"]
        onda_fft = onda 

        _dibujar_osciloscopio(screen, osc_rect, onda, lcd_text, t)

    else:
        screen.blit(
            font_lcd.render("PULSA UNA TECLA...", True, _dim(lcd_text, 0.20)),
            (lcd_x + 8, 30)
        )
        osc_rect = pygame.Rect(lcd_x + 6, 58, CONSTANTES.ANCHO_LCD - 12, CONSTANTES.ALTO_PANEL - 66)
        pygame.draw.rect(screen, (3, 7, 10), osc_rect)
        pygame.draw.rect(screen, _dim(lcd_text, 0.08), osc_rect, 1)
        mid_y = osc_rect.centery
        pygame.draw.line(screen, _dim(lcd_text, 0.12),
                         (osc_rect.left + 4, mid_y), (osc_rect.right - 4, mid_y), 1)

    if mezcla_conversion is not None:
        _dibujar_morph(screen, mezcla_conversion, font_small, CONSTANTES.ALTO_PANEL - 10)

    # ══ PANEL FFT REAL (derecha) ══════════════
    fft_rect = pygame.Rect(CONSTANTES.ANCHO_VENTANA - CONSTANTES.ANCHO_FFT, 0, CONSTANTES.ANCHO_FFT, CONSTANTES.ALTO_PANEL)
    _dibujar_panel_fft(screen, fft_rect, onda_fft, primary, lcd_text, font_small)

    # ── SEPARADOR ────────────────────────────
    pygame.draw.rect(screen, (8, 9, 12), (0, CONSTANTES.ALTO_PANEL, CONSTANTES.ANCHO_VENTANA, 2))

    # ── FONDO TECLADO ────────────────────────
    pygame.draw.rect(screen, (7, 7, 9), (0, CONSTANTES.Y_AREA_TECLADO, CONSTANTES.ANCHO_VENTANA, CONSTANTES.ALTO_AREA_TECLADO + 2))
    pygame.draw.rect(screen, (100, 6, 12), (8, CONSTANTES.Y_AREA_TECLADO + 2, CONSTANTES.ANCHO_VENTANA - 16, 8), border_radius=2)
    pygame.draw.rect(screen, (50,  3,  6), (8, CONSTANTES.Y_AREA_TECLADO + 8, CONSTANTES.ANCHO_VENTANA - 16, 3))

    # ── TECLADO ───────────────────────────────
    white_data, black_data = _calcular_layout_teclado(notas_config)
    key_y = CONSTANTES.Y_AREA_TECLADO + 12

    for kid, nota, kx, kw, kh in white_data:
        decay = _decay_factor(kid, t)
        _dibujar_tecla_blanca(screen, kx, key_y, kw, kh,
                              bool(pressed[kid]),
                              nota,           
                              decay,
                              primary, font_main)

    for kid, nota, kx, kw, kh in black_data:
        decay = _decay_factor(kid, t)
        _dibujar_tecla_negra(screen, kx, key_y, kw, kh,
                             bool(pressed[kid]),
                             nota,            
                             decay,
                             primary, font_small)

    # ── BARRA INFERIOR ───────────────────────
    pygame.draw.rect(screen, (7, 8, 10), (0, CONSTANTES.ALTO_VENTANA - CONSTANTES.ALTO_BARRA_INFERIOR, CONSTANTES.ANCHO_VENTANA, CONSTANTES.ALTO_BARRA_INFERIOR))
    pygame.draw.line(screen, _dim(primary, 0.16),
                     (0, CONSTANTES.ALTO_VENTANA - CONSTANTES.ALTO_BARRA_INFERIOR), (CONSTANTES.ANCHO_VENTANA, CONSTANTES.ALTO_VENTANA - CONSTANTES.ALTO_BARRA_INFERIOR), 1)

    nav = font_small.render(
        "◄ ►  INSTRUMENTO    |    TECLAS: Z-M / Q-U    |    DASC SINTETIZADOR",
        True, (28, 36, 46)
    )
    screen.blit(nav, (10, CONSTANTES.ALTO_VENTANA - CONSTANTES.ALTO_BARRA_INFERIOR + 5))

    inst_tag = font_small.render(f"[ {instrumento_actual.upper()} ]", True, _dim(primary, 0.65))
    screen.blit(inst_tag, (CONSTANTES.ANCHO_VENTANA - inst_tag.get_width() - 12, CONSTANTES.ALTO_VENTANA - CONSTANTES.ALTO_BARRA_INFERIOR + 5))