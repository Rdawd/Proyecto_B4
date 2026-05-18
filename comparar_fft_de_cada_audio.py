# comparar_fft_de_cada_audio.py
import json
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import CONSTANTES

N_ARM = 10   # armónicos a mostrar en todas las tablas


# ─────────────────────────────────────────────
#  CARGA
# ─────────────────────────────────────────────

def cargar_todos_los_armonicos() -> dict:
    datos = {}
    for inst in CONSTANTES.INSTRUMENTOS.keys():
        ruta = f"datos/armonicos_{inst}.json"
        if os.path.exists(ruta):
            with open(ruta) as f:
                datos[inst] = json.load(f)
        else:
            datos[inst] = {"picos": [], "fundamental": 0.0}
    return datos


# ─────────────────────────────────────────────
#  HELPER ESTILO TABLA
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


# ─────────────────────────────────────────────
#  TABLA 1 — Comparación directa de frecuencias
#  Filas = A1..A10, columnas = instrumentos
#  Esto muestra DIRECTAMENTE que las frecuencias difieren
# ─────────────────────────────────────────────

def tabla_frecuencias_comparativa():
    """
    Tabla principal de demostración:
    Para cada armónico A1–A10 muestra la frecuencia (Hz)
    de cada instrumento lado a lado.
    Si la guitarra eléctrica y acústica fueran idénticas,
    todas las filas serían iguales. No lo son.
    """
    datos  = cargar_todos_los_armonicos()
    insts  = list(datos.keys())
    colores_header = {
        "electrica": "#003f5c",
        "acustica":  "#7a2800",
    }

    col_labels = ["Armónico"] + [i.upper() + "\nFrecuencia (Hz)" for i in insts] \
                              + [i.upper() + "\nAmplitud (dB)" for i in insts]

    rows = []
    for i in range(N_ARM):
        fila = [f"A{i+1}"]
        # Frecuencias
        for inst in insts:
            picos = sorted(datos[inst].get("picos", []), key=lambda v: v[0])
            if i < len(picos):
                fila.append(f"{picos[i][0]:.1f}")
            else:
                fila.append("—")
        # Amplitudes en dB
        for inst in insts:
            picos = sorted(datos[inst].get("picos", []), key=lambda v: v[0])
            if i < len(picos):
                amp = picos[i][1]
                db  = 20 * np.log10(amp) if amp > 0 else -120
                fila.append(f"{db:.1f} dB")
            else:
                fila.append("—")
        rows.append(fila)

    fig, ax = plt.subplots(figsize=(12, 0.5 * N_ARM + 2.2), facecolor="#0d1117")
    fig.suptitle(
        "Frecuencia y Amplitud por Armónico — misma nota A4, distinto instrumento",
        color="#58a6ff", fontsize=13, fontweight="bold"
    )
    _estilo_tabla(ax, col_labels, rows)
    plt.tight_layout()
    os.makedirs("datos", exist_ok=True)
    plt.savefig("datos/tabla_comparativa_frecuencias.png", dpi=150,
                facecolor="#0d1117", bbox_inches="tight")
    plt.show()


# ─────────────────────────────────────────────
#  TABLA 2 — Diferencia absoluta entre instrumentos
#  Cuantifica cuánto difieren armónico a armónico
# ─────────────────────────────────────────────

def tabla_diferencia_entre_instrumentos():
    """
    Para cada armónico A1–A10 calcula:
      - Δ Frecuencia (Hz) entre eléctrica y acústica
      - Δ Amplitud (dB) entre eléctrica y acústica
    Si fueran idénticos, todas las diferencias serían 0.
    """
    datos = cargar_todos_los_armonicos()
    insts = list(datos.keys())

    if len(insts) < 2:
        print("Se necesitan al menos 2 instrumentos para calcular diferencias.")
        return

    inst_a, inst_b = insts[0], insts[1]
    picos_a = sorted(datos[inst_a].get("picos", []), key=lambda v: v[0])
    picos_b = sorted(datos[inst_b].get("picos", []), key=lambda v: v[0])

    col_labels = [
        "Armónico",
        f"{inst_a.upper()} Hz",
        f"{inst_b.upper()} Hz",
        "Δ Hz",
        f"{inst_a.upper()} dB",
        f"{inst_b.upper()} dB",
        "Δ dB",
    ]

    rows = []
    for i in range(N_ARM):
        fa   = picos_a[i][0] if i < len(picos_a) else None
        fb   = picos_b[i][0] if i < len(picos_b) else None
        ampa = picos_a[i][1] if i < len(picos_a) else None
        ampb = picos_b[i][1] if i < len(picos_b) else None

        dba  = round(20 * np.log10(ampa), 1) if ampa else "—"
        dbb  = round(20 * np.log10(ampb), 1) if ampb else "—"

        delta_hz = f"{abs(fa - fb):.1f}" if fa and fb else "—"
        delta_db = f"{abs(dba - dbb):.1f}" if isinstance(dba, float) and isinstance(dbb, float) else "—"

        rows.append([
            f"A{i+1}",
            f"{fa:.1f}" if fa else "—",
            f"{fb:.1f}" if fb else "—",
            delta_hz,
            f"{dba} dB" if isinstance(dba, float) else "—",
            f"{dbb} dB" if isinstance(dbb, float) else "—",
            f"{delta_db} dB" if delta_db != "—" else "—",
        ])

    fig, ax = plt.subplots(figsize=(13, 0.5 * N_ARM + 2.2), facecolor="#0d1117")
    fig.suptitle(
        f"Diferencia armónico a armónico: {inst_a.upper()} vs {inst_b.upper()} — misma nota A4",
        color="#58a6ff", fontsize=13, fontweight="bold"
    )
    _estilo_tabla(ax, col_labels, rows, header_color="#1e3a1e")
    plt.tight_layout()
    os.makedirs("datos", exist_ok=True)
    plt.savefig("datos/tabla_diferencias.png", dpi=150,
                facecolor="#0d1117", bbox_inches="tight")
    plt.show()


# ─────────────────────────────────────────────
#  GRÁFICO — Espectro superpuesto (stem)
# ─────────────────────────────────────────────

def graficar_fft_superpuesta():
    datos      = cargar_todos_los_armonicos()
    colores    = {"electrica": "#00c8ff", "acustica": "#ff8c00"}
    markerfmts = {"electrica": "co",      "acustica": "yo"}

    fig, ax = plt.subplots(figsize=(13, 5), facecolor="#0d1117")
    ax.set_facecolor("#0d1117")
    ax.tick_params(colors="#8b949e")
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

    for inst, info in datos.items():
        picos = info["picos"]
        if not picos:
            continue
        freqs = [p[0] for p in picos]
        amps  = [p[1] for p in picos]
        c  = colores.get(inst, "white")
        mf = markerfmts.get(inst, "wo")
        ml, sl, _ = ax.stem(freqs, amps, linefmt=c, markerfmt=mf,
                            basefmt=" ", label=inst)
        plt.setp(sl, alpha=0.65, linewidth=1.5)
        plt.setp(ml, alpha=0.9, markersize=6)

    ax.set_title("Espectro Armónico",
                 color="#58a6ff", fontsize=13, fontweight="bold")
    ax.set_xlabel("Frecuencia (Hz)", color="#8b949e")
    ax.set_ylabel("Amplitud normalizada", color="#8b949e")
    ax.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9", fontsize=10)
    ax.grid(True, color="#21262d", linewidth=0.5)

    os.makedirs("datos", exist_ok=True)
    plt.tight_layout()
    plt.savefig("datos/comparacion_fft.png", dpi=150, facecolor="#0d1117")
    plt.show()


# ─────────────────────────────────────────────
#  GRÁFICO — Barras de amplitud por armónico
# ─────────────────────────────────────────────

def graficar_armonicos_barras():
    datos   = cargar_todos_los_armonicos()
    labels  = [f"A{i+1}" for i in range(N_ARM)]
    x       = np.arange(N_ARM)
    width   = 0.35
    insts   = list(datos.keys())
    colores = ["#00c8ff", "#ff8c00"]
    offsets = [-width / 2, width / 2]

    fig, ax = plt.subplots(figsize=(13, 5), facecolor="#0d1117")
    ax.set_facecolor("#0d1117")
    ax.tick_params(colors="#8b949e")
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

    for idx, inst in enumerate(insts):
        picos = sorted(datos[inst].get("picos", []), key=lambda v: v[0])
        amps  = [picos[i][1] if i < len(picos) else 0 for i in range(N_ARM)]
        ax.bar(x + offsets[idx], amps, width, label=inst,
               color=colores[idx % len(colores)], alpha=0.85,
               edgecolor="#0d1117", linewidth=0.5)

    ax.set_xlabel("Armónico", color="#8b949e")
    ax.set_ylabel("Amplitud normalizada", color="#8b949e")
    ax.set_title("Amplitud por armónico (A1–A10) — misma nota A4",
                 color="#58a6ff", fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color="#8b949e")
    ax.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9", fontsize=10)
    ax.grid(axis="y", color="#21262d", linewidth=0.5)

    os.makedirs("datos", exist_ok=True)
    plt.tight_layout()
    plt.savefig("datos/comparacion_armonicos.png", dpi=150, facecolor="#0d1117")
    plt.show()


# ─────────────────────────────────────────────
#  REPORTE CONSOLA
# ─────────────────────────────────────────────

def reporte_consola():
    datos = cargar_todos_los_armonicos()
    print("\n" + "═" * 50)
    print("   REPORTE ESPECTRAL — DASC")
    print("═" * 50)
    for inst, info in datos.items():
        f0    = info.get("fundamental", 0.0)
        picos = sorted(info.get("picos", []), key=lambda v: v[0])
        print(f"\n  {inst.upper()}  |  F0 = {f0:.2f} Hz")
        print(f"  {'Arm.':<6} {'Freq (Hz)':>12} {'Amp (dB)':>10}")
        print(f"  {'-'*30}")
        for i, (freq, amp) in enumerate(picos[:N_ARM]):
            db = 20 * np.log10(amp) if amp > 0 else -120
            print(f"  A{i+1:<5} {freq:>12.2f} {db:>9.1f} dB")
    print("\n" + "═" * 50)


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    graficar_armonicos_barras()
    graficar_fft_superpuesta()
    print("Archivos guardados en datos/")