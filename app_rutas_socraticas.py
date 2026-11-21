import streamlit as st
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
import textwrap
import requests
import smtplib
from email.message import EmailMessage
from datetime import datetime
import pytz

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Oráculo Rover: Rutas y Cartas Socráticas",
    page_icon="🧭",
    layout="wide"
)

def obtener_hora_cdmx():
    zona_cdmx = pytz.timezone('America/Mexico_City')
    return datetime.now(zona_cdmx)

def limpiar_texto_pdf(texto):
    """Elimina emojis/caracteres no soportados por la fuente estándar de Matplotlib al crear el PDF."""
    if not texto:
        return ""
    return "".join(c for c in str(texto) if ord(c) < 65536 and c not in "🔵🟠🟢🟣🎯🌟🧭🃏📐🔴⚡🔥🏃‍♂️💡🛡️❤️🤝🕊️⚜️🏛️🛠️📏⚙️⏳🔄📋")

# --- 2. CONEXIÓN AL GOOGLE SHEETS ORIGINAL ---
@st.cache_data(ttl=30, show_spinner=False)
def cargar_datos_sheets():
    """Lee los datos guardados por la App 1 en Google Sheets."""
    if "SHEETS_WEBHOOK_URL" in st.secrets:
        try:
            resp = requests.get(st.secrets["SHEETS_WEBHOOK_URL"], timeout=10)
            if resp.status_code == 200:
                datos = resp.json()
                if isinstance(datos, list) and len(datos) > 0:
                    df = pd.DataFrame(datos)
                    return normalizar_columnas(df)
        except Exception:
            pass

    if "SHEETS_CSV_URL" in st.secrets:
        df = pd.read_csv(st.secrets["SHEETS_CSV_URL"])
        return normalizar_columnas(df)

    return pd.DataFrame()

def normalizar_columnas(df):
    """Asegura nombres estándar en las 12 columnas originales de la App 1."""
    if df.empty:
        return df
    columnas_esperadas = [
        "fecha_hora", "nombre", "correo",
        "corporalidad", "creatividad", "caracter",
        "afectividad", "sociabilidad", "espiritualidad",
        "promedio", "superpoder", "area_enfoque"
    ]
    if len(df.columns) >= 12:
        mapeo = {df.columns[i]: columnas_esperadas[i] for i in range(12)}
        df = df.rename(columns=mapeo)
    for col in ["corporalidad", "creatividad", "caracter", "afectividad", "sociabilidad", "espiritualidad", "promedio"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(5)
    return df

# --- 3. MOTOR DE ASOCIACIÓN: 6 ÁREAS -> 4 RUTAS + CARTAS SOCRÁTICAS ---
def analizar_perfil_rover(valores):
    """
    Traduce [corporalidad, creatividad, caracter, afectividad, sociabilidad, espiritualidad]
    a las 4 Rutas (Kikapú, Otomí, Maya, Wixárika), geometría y Cartas Socráticas.
    """
    promedio = float(np.mean(valores))
    desviacion = float(np.std(valores))

    rutas = {
        "🔵 Ruta Kikapú (Salud y Bienestar)": round((valores[0] + valores[3]) / 2, 2),
        "🟠 Ruta Otomí (Habilidades para la Vida)": round((valores[1] + valores[2]) / 2, 2),
        "🟢 Ruta Maya (Medio Ambiente y Sustentabilidad)": round((valores[0] + valores[1] + valores[5]) / 3, 2),
        "🟣 Ruta Wixárika (Paz y Participación Comunitaria)": round((valores[3] + valores[4] + valores[5]) / 3, 2)
    }

    ruta_enfoque = min(rutas, key=rutas.get)
    ruta_fortaleza = max(rutas, key=rutas.get)

    indice_min = int(np.argmin(valores))
    indice_max = int(np.argmax(valores))

    mazo_confrontacion = {
        0: (
            "Carta 1.1 – Corporalidad (Vinculada a Ruta Kikapú)",
            "Mira el número que te pusiste en Corporalidad. Si sigues comiendo, durmiendo y entrenando exactamente igual que en los últimos tres meses, ¿cómo va a estar tu cuerpo en los próximos seis meses? Deja los buenos deseos: ¿qué hábito físico te está saboteando hoy y qué vas a hacer con ese conocimiento para que no se quede solo en entrenar para ti, sino que le sirva también a otros?"
        ),
        1: (
            "Carta 1.2 – Creatividad (Vinculada a Ruta Otomí y Ruta Maya)",
            "¿Cuánto tiempo de tu semana pasas consumiendo lo que otros hacen en redes frente al tiempo que pasas creando soluciones o aprendiendo una habilidad técnica real? Si mañana tuvieras que resolver un problema de tu carrera, trabajo o comunidad sin presupuesto, ¿qué herramienta práctica te urge dominar hoy?"
        ),
        2: (
            "Carta 1.3 – Carácter (Vinculada a Ruta Otomí)",
            "Ser Rover es gobernar tu propia vida. ¿Cuántas cosas dejaste a medias últimamente porque 'no tuviste tiempo' o porque nadie te estuvo presionando? Mira tu puntaje en Carácter: ¿qué compromiso real estás evadiendo ahora mismo en tus estudios, tu casa o el Clan, y qué sistema vas a usar en este ciclo para cumplir tu palabra aunque no tengas ganas?"
        ),
        3: (
            "Carta 1.4 – Afectividad (Vinculada a Ruta Kikapú y Ruta Wixárika)",
            "Cuando estás bajo presión por la escuela, el trabajo o problemas personales, ¿cómo gestionas el estrés y cómo tratas a la gente que te rodea? ¿Qué límite sano necesitas poner en tus relaciones o qué red de apoyo necesitas construir este ciclo para no quemarte?"
        ),
        4: (
            "Carta 1.5 – Sociabilidad y Comunidad (Vinculada a Ruta Wixárika)",
            "El Clan es una hermandad de servicio, no un club social de fin de semana. Fuera de tu círculo de amigos, ¿qué problema real de tu colonia, escuela o municipio estás ignorando aunque sabes que tienes la capacidad de intervenir? ¿Vas a seguir haciendo 'caridad de un día' o vas a liderar una solución que deje un antes y un después medible?"
        ),
        5: (
            "Carta 1.6 – Espiritualidad y Naturaleza (Vinculada a Ruta Maya y Ruta Wixárika)",
            "Tu puntaje en Espiritualidad habla de tu congruencia entre lo que dices que valoras y cómo vives. Mira tu consumo diario (lo que compras, la basura que generas, tu impacto al salir al aire libre): ¿qué comodidad personal estás dispuesto a recortar en este ciclo para reducir tu huella ambiental y enseñar a otros a hacer lo mismo?"
        )
    }

    titulo_carta_debil, texto_carta_debil = mazo_confrontacion[indice_min]

    carta_fortaleza = (
        f"Carta 1.7 – El Espejo de la Fortaleza ({ruta_fortaleza}): "
        f"Obtuviste {valores[indice_max]}/10 en tu área más alta. En el Clan, una habilidad que ya dominas y te guardas para ti no sirve de nada. "
        f"¿En qué Especialidad para la Vida la vas a convertir en este ciclo y a quién se la vas a enseñar o qué problema comunitario vas a resolver con ella?"
    )

    if desviacion >= 2.2:
        geometria = "Polígono Polarizado (Desbalance Crítico)"
        carta_geometria = (
            "Carta 1.8 – El Costo de la Indiferencia: Tu diagrama tiene picos altos pero un hundimiento severo. "
            "Sé brutalmente honesto: ¿esa área está baja porque de verdad no pudiste atenderla o porque decidiste dejarla al final de tus prioridades? "
            "Si no haces nada en los próximos 90 días, ¿qué factura te va a cobrar en tu vida personal o profesional?"
        )
    elif promedio < 5.5:
        geometria = "Polígono Contraído (Etapa de Reconstrucción)"
        carta_geometria = (
            "Carta 2.5 – Filtro [A] Alcanzable: Tu energía general está baja. No intentes subir las 6 áreas de golpe. "
            "Elige una sola trinchera: ¿cuántas horas a la semana le vas a dedicar a tu Ruta prioritaria y de qué día y hora exacta las vas a sacar?"
        )
    else:
        geometria = "Polígono Equilibrado en Expansión"
        carta_geometria = (
            "Carta 3.6 – Alianzas de Fuego: Tienes tracción estable. Voltea a ver las Ruedas de tus hermanos de Malinalli y Tic Temoaya Ochan: "
            "¿quién tiene una debilidad donde tú eres fuerte? ¿Qué proyecto inter-clan o campamento técnico van a armar juntos en el próximo ciclo?"
        )

    return rutas, ruta_enfoque, ruta_fortaleza, geometria, titulo_carta_debil, texto_carta_debil, carta_fortaleza, carta_geometria

def dibujar_radar_rover(valores, nombre, promedio, geometria):
    areas_nombres = ["🏃‍♂️ Corporalidad", "💡 Creatividad", "🛡️ Carácter", "❤️ Afectividad", "🤝 Sociabilidad", "🕊️ Espiritualidad"]
    colores_rebanadas = [
        "rgba(255, 99, 132, 0.45)", "rgba(255, 205, 86, 0.45)", "rgba(153, 102, 255, 0.45)",
        "rgba(255, 159, 64, 0.45)", "rgba(54, 162, 235, 0.45)", "rgba(75, 192, 192, 0.45)"
    ]
    angulos_base = [0, 60, 120, 180, 240, 300]

    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        r=[10]*6, theta=angulos_base, width=[60]*6,
        marker_color=colores_rebanadas, marker_line_color="white", marker_line_width=2,
        hoverinfo="skip", showlegend=False
    ))
    fig.add_trace(go.Scatterpolar(
        r=valores + [valores[0]], theta=angulos_base + [angulos_base[0]],
        fill='toself', fillcolor='rgba(44, 62, 80, 0.38)',
        line=dict(color='#1E293B', width=3), marker=dict(color='#1E293B', size=8),
        name=nombre
    ))
    fig.update_layout(
        template="plotly_white",
        polar=dict(
            angularaxis=dict(tickmode="array", tickvals=angulos_base, ticktext=areas_nombres, direction="clockwise", rotation=90),
            radialaxis=dict(visible=True, range=[0, 10], tickvals=[2, 4, 6, 8, 10])
        ),
        showlegend=False,
        margin=dict(t=60, b=40, l=50, r=50),
        title=dict(text=f"<b>{nombre} — {promedio:.1f}/10</b><br><sup style='color:#64748B;'>{geometria}</sup>", x=0.5)
    )
    return fig

# --- 4. GENERADORES DE ARCHIVOS ADJUNTOS (MARKDOWN + PDF EN RAM) ---
def generar_markdown_ciclo(payload):
    """Genera el contenido del archivo .md listo para Notion y respaldo."""
    return f"""# Ciclo Personal de Programa — {payload['nombre']}
* **Clan:** {payload['clan']}
* **Periodo del Ciclo:** {payload['trimestre']}
* **Fecha de registro / modificación:** {payload['fecha_hora']} (CDMX)
* **Correo del Rover:** {payload['correo']}

---

## 1. Diagnóstico de Rutas de Progresión
* **Ruta Kikapú (Salud y Bienestar):** {payload['pts_kikapu']}/10
* **Ruta Otomí (Habilidades para la Vida):** {payload['pts_otomi']}/10
* **Ruta Maya (Medio Ambiente y Sustentabilidad):** {payload['pts_maya']}/10
* **Ruta Wixárika (Paz y Participación Comunitaria):** {payload['pts_wixarika']}/10

* **Ruta de Enfoque elegida:** {payload['ruta_enfoque']}
* **Ruta de Fortaleza (Especialidad / Servicio):** {payload['ruta_fortaleza']}
* **Geometría de la Rueda:** {payload['geometria']}

---

## 2. Confrontación Socrática
* **Carta trabajada:** {payload['carta_socratica']}
* **Respuesta del Rover:**
> {payload['respuesta_socratica']}

---

## 3. Objetivo SMART del Ciclo Personal

| Criterio SMART | Definición Aprobada | Estado |
| :--- | :--- | :--- |
| **S (Específico)** | {payload['obj_s']} | ✅ |
| **M (Medible)** | {payload['obj_m']} | ✅ |
| **A (Alcanzable)** | {payload['obj_a']} | ✅ |
| **R (Realista / Asesor)** | {payload['obj_r']} | ✅ |
| **T (Tiempo límite)** | {payload['obj_t']} | ✅ |

---

## 4. Acciones Educativas (Metodología PER)
* **1. PLANEA (Conozco):** {payload['per_planea']}
* **2. EJECUTA (Aplico):** {payload['per_ejecuta']}
* **3. REVISA (Comparto):** {payload['per_revisa']}
"""

def generar_pdf_ficha_ram(payload):
    """Genera una ficha oficial en PDF (tamaño carta) en memoria RAM usando Matplotlib."""
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('white')
    ax = fig.add_axes([0.07, 0.05, 0.86, 0.90])
    ax.axis('off')

    y = 0.98
    def escribir_bloque(titulo, texto, espacio_titulo=0.025, espacio_linea=0.020, ancho=92, color_titulo='#0F172A'):
        nonlocal y
        if titulo:
            ax.text(0.0, y, limpiar_texto_pdf(titulo), fontsize=10.5, fontweight='bold', color=color_titulo, va='top')
            y -= espacio_titulo
        if texto:
            for parrafo in limpiar_texto_pdf(texto).split('\n'):
                lineas = textwrap.wrap(parrafo, width=ancho) or [""]
                for linea in lineas:
                    if y < 0.04:
                        break
                    ax.text(0.01, y, linea, fontsize=9.2, color='#1E293B', va='top')
                    y -= espacio_linea
            y -= 0.012

    # Encabezado
    ax.text(0.0, y, "FICHA DE CICLO PERSONAL DE PROGRAMA — CLAN DE ROVERS", fontsize=13.5, fontweight='bold', color='#1E293B', va='top')
    y -= 0.032
    ax.text(0.0, y, f"Rover: {limpiar_texto_pdf(payload['nombre'])}  |  Clan: {limpiar_texto_pdf(payload['clan'])}  |  Periodo: {limpiar_texto_pdf(payload['trimestre'])}", fontsize=10, fontweight='bold', color='#334155', va='top')
    y -= 0.022
    ax.text(0.0, y, f"Fecha de registro/actualizacion: {payload['fecha_hora']} (CDMX)  |  Correo: {payload['correo']}", fontsize=8.5, color='#64748B', va='top')
    y -= 0.022
    ax.plot([0, 1], [y, y], color='#CBD5E1', linewidth=1.2)
    y -= 0.020

    # Sección 1: Rutas
    rutas_resumen = (
        f"Kikapu (Salud): {payload['pts_kikapu']}/10  |  Otomi (Habilidades): {payload['pts_otomi']}/10  |  "
        f"Maya (Ambiente): {payload['pts_maya']}/10  |  Wixarika (Paz/Comunidad): {payload['pts_wixarika']}/10\n"
        f"Ruta de Enfoque elegida: {payload['ruta_enfoque']}\n"
        f"Ruta de Fortaleza (Especialidad): {payload['ruta_fortaleza']}  |  Geometria: {payload['geometria']}"
    )
    escribir_bloque("1. DIAGNOSTICO DE RUTAS DE PROGRESION", rutas_resumen, color_titulo='#0F4C81')

    # Sección 2: Carta Socrática
    escribir_bloque(
        f"2. CONFRONTACION SOCRATICA ({payload['carta_socratica']})",
        f"Reflexion del Rover: {payload['respuesta_socratica']}",
        color_titulo='#9A3412'
    )

    # Sección 3: SMART
    smart_txt = (
        f"[S] Especifico: {payload['obj_s']}\n"
        f"[M] Medible: {payload['obj_m']}\n"
        f"[A] Alcanzable: {payload['obj_a']}\n"
        f"[R] Realista / Asesor: {payload['obj_r']}\n"
        f"[T] Tiempo limite: {payload['obj_t']}"
    )
    escribir_bloque("3. OBJETIVO SMART DEL CICLO PERSONAL", smart_txt, color_titulo='#065F46')

    # Sección 4: PER
    per_txt = (
        f"PLANEA (Conozco): {payload['per_planea']}\n"
        f"EJECUTA (Aplico): {payload['per_ejecuta']}\n"
        f"REVISA (Comparto): {payload['per_revisa']}"
    )
    escribir_bloque("4. PLAN DE ACCIONES EDUCATIVAS (METODOLOGIA PER)", per_txt, color_titulo='#5B21B6')

    buf_pdf = io.BytesIO()
    fig.savefig(buf_pdf, format='pdf', bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return buf_pdf.getvalue()

def guardar_ciclo_fase2(payload):
    """Guarda las Rutas, respuesta socrática y Ciclo SMART+PER en Google Sheets."""
    if "SHEETS_WEBHOOK_URL" not in st.secrets:
        return False, "Falta SHEETS_WEBHOOK_URL en Secrets."
    payload_envio = dict(payload)
    payload_envio["origen"] = "FASE_2_SMART"
    resp = requests.post(st.secrets["SHEETS_WEBHOOK_URL"], json=payload_envio, timeout=10)
    return (resp.status_code == 200), resp.text

def enviar_correo_ciclo(payload, bytes_pdf, texto_md):
    """Envía el Ciclo Personal con archivos adjuntos (.pdf y .md) al Consejero y copia al Rover."""
    remitente = st.secrets["EMAIL_SENDER"]
    correo_responsable = st.secrets.get("ADMIN_EMAIL", remitente)

    nombre_archivo_base = payload["nombre"].replace(" ", "_")
    sello_fecha = obtener_hora_cdmx().strftime("%Y%m%d_%H%M")
    nombre_pdf = f"Ciclo_Personal_{payload['clan']}_{nombre_archivo_base}_{sello_fecha}.pdf"
    nombre_md = f"Ciclo_Personal_{payload['clan']}_{nombre_archivo_base}_{sello_fecha}.md"
    bytes_md = texto_md.encode("utf-8")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(remitente, st.secrets["EMAIL_PASSWORD"])

        # 1. Correo exclusivo para ti (Consejero Responsable) con archivos adjuntos
        msg_admin = EmailMessage()
        msg_admin["Subject"] = f"📋 Ciclo Personal Actualizado: {payload['nombre']} ({payload['clan']} - {payload['trimestre']})"
        msg_admin["From"] = remitente
        msg_admin["To"] = correo_responsable
        msg_admin.set_content(
            f"El Rover {payload['nombre']} (Clan {payload['clan']}) ha registrado o modificado su Ciclo Personal.\n\n"
            f"• Periodo: {payload['trimestre']}\n"
            f"• Ruta de Enfoque: {payload['ruta_enfoque']}\n"
            f"• Ruta de Fortaleza: {payload['ruta_fortaleza']}\n"
            f"• Fecha de actualización: {payload['fecha_hora']} (CDMX)\n\n"
            f"Se adjuntan dos archivos listos para tu seguimiento:\n"
            f"1) {nombre_pdf} (Ficha en PDF para expediente).\n"
            f"2) {nombre_md} (Archivo Markdown listo para importar a Notion)."
        )
        msg_admin.add_attachment(bytes_pdf, maintype="application", subtype="pdf", filename=nombre_pdf)
        msg_admin.add_attachment(bytes_md, maintype="text", subtype="markdown", filename=nombre_md)
        smtp.send_message(msg_admin)

        # 2. Copia para el Rover con sus archivos adjuntos
        if payload["correo"] and "@" in payload["correo"]:
            msg_rover = EmailMessage()
            msg_rover["Subject"] = f"🧭 Tu Ciclo Personal ({payload['trimestre']}): {payload['nombre']} - Clan {payload['clan']}"
            msg_rover["From"] = remitente
            msg_rover["To"] = payload["correo"]
            msg_rover.set_content(
                f"¡Siempre Listo para Servir, {payload['nombre']}!\n\n"
                f"Tu Ciclo Personal ({payload['trimestre']}) ha sido guardado y enviado a tu Consejero Rover.\n"
                f"Adjunto encontrarás tu ficha en PDF y tu archivo Markdown (.md) listo para subir a tu Agenda Rover en Notion.\n\n"
                f"¡Buena caza y largas lunas!"
            )
            msg_rover.add_attachment(bytes_pdf, maintype="application", subtype="pdf", filename=nombre_pdf)
            msg_rover.add_attachment(bytes_md, maintype="text", subtype="markdown", filename=nombre_md)
            smtp.send_message(msg_rover)

    return nombre_pdf, nombre_md

# --- 5. BARRA LATERAL Y NAVEGACIÓN ---
st.sidebar.title("⚜️ Sistema Rover")
modo = st.sidebar.radio(
    "Selecciona la vista:",
    ["🧭 1. Taller Individual (Rutas + Cartas + SMART)", "🏛️ 2. Vista Maestra Consejero (Macrociclo Clanes)"]
)

if st.sidebar.button("🔄 Actualizar datos de Google Sheets"):
    st.cache_data.clear()

df_registros = cargar_datos_sheets()

if df_registros.empty:
    st.warning(
        "⚠️ No se pudieron cargar automáticamente los registros de Google Sheets. "
        "Verifica que hayas agregado la función `doGet(e)` en tu Apps Script o carga aquí el archivo CSV descargado:"
    )
    archivo_csv = st.file_uploader("Subir CSV de Google Sheets (Respaldo manual)", type=["csv"])
    if archivo_csv:
        df_registros = normalizar_columnas(pd.read_csv(archivo_csv))

# ==============================================================================
# MODO 1: TALLER INDIVIDUAL DEL ROVER (RUTAS, CARTAS SOCRÁTICAS Y DISEÑO SMART)
# ==============================================================================
if modo == "🧭 1. Taller Individual (Rutas + Cartas + SMART)":
    st.title("🧭 Fase 2: De tu Rueda de la Vida a tu Ruta y Ciclo Personal")
    st.markdown(
        "Selecciona tu registro guardado en la **Rueda de la Vida**. El sistema analizará la geometría de tu diagrama, "
        "calculará tu afinidad con las **Rutas Kikapú, Otomí, Maya y Wixárika**, y te entregará tus **Cartas Socráticas**."
    )

    if not df_registros.empty:
        nombres_disponibles = df_registros["nombre"].dropna().unique().tolist()
        col_sel1, col_sel2 = st.columns([2, 1])
        with col_sel1:
            rover_seleccionado = st.selectbox("🔍 Busca y selecciona tu nombre:", nombres_disponibles)
        with col_sel2:
            clan_seleccionado = st.selectbox("🏕️ Selecciona tu Clan:", ["Malinalli", "Tic Temoaya Ochan"])

        fila_rover = df_registros[df_registros["nombre"] == rover_seleccionado].iloc[-1]
        valores_rover = [
            int(fila_rover["corporalidad"]), int(fila_rover["creatividad"]), int(fila_rover["caracter"]),
            int(fila_rover["afectividad"]), int(fila_rover["sociabilidad"]), int(fila_rover["espiritualidad"])
        ]
        correo_rover = str(fila_rover["correo"])
        fecha_registro_orig = str(fila_rover["fecha_hora"])

        (
            rutas, ruta_enfoque, ruta_fortaleza, geometria,
            titulo_carta_debil, texto_carta_debil, carta_fortaleza, carta_geometria
        ) = analizar_perfil_rover(valores_rover)

        st.divider()

        col_graf, col_rutas = st.columns([1.1, 1])
        with col_graf:
            fig_radar = dibujar_radar_rover(valores_rover, rover_seleccionado, float(np.mean(valores_rover)), geometria)
            st.plotly_chart(fig_radar, use_container_width=True)
            st.caption(f"Registro original tomado de Google Sheets del: {fecha_registro_orig}")

        with col_rutas:
            st.subheader("🧭 Tus 4 Rutas de Progresión")
            r1, r2 = st.columns(2)
            r1.metric("🔵 Ruta Kikapú", f"{rutas['🔵 Ruta Kikapú (Salud y Bienestar)']}/10", "Salud y Bienestar", delta_color="off")
            r2.metric("🟠 Ruta Otomí", f"{rutas['🟠 Ruta Otomí (Habilidades para la Vida)']}/10", "Habilidades Vida", delta_color="off")
            r3, r4 = st.columns(2)
            r3.metric("🟢 Ruta Maya", f"{rutas['🟢 Ruta Maya (Medio Ambiente y Sustentabilidad)']}/10", "Medio Ambiente", delta_color="off")
            r4.metric("🟣 Ruta Wixárika", f"{rutas['🟣 Ruta Wixárika (Paz y Participación Comunitaria)']}/10", "Paz y Comunidad", delta_color="off")

            st.error(f"🎯 **Ruta de Enfoque (Objetivo de Desarrollo):**\n\n{ruta_enfoque}")
            st.success(f"🌟 **Ruta de Fortaleza (Especialidad y Servicio):**\n\n{ruta_fortaleza}")

        # --- MAZO DE CARTAS SOCRÁTICAS ---
        st.divider()
        st.subheader("🃏 Mazo 1: Tus Cartas Socráticas de Confrontación")
        c_carta1, c_carta2, c_carta3 = st.columns(3)
        with c_carta1:
            st.warning(f"🔴 **1. {titulo_carta_debil}**\n\n*\"{texto_carta_debil}\"*")
        with c_carta2:
            st.info(f"🟢 **2. Fortaleza y Servicio**\n\n*\"{carta_fortaleza}\"*")
        with c_carta3:
            st.success(f"📐 **3. Geometría ({geometria})**\n\n*\"{carta_geometria}\"*")

        respuesta_socratica = st.text_area(
            "✍️ PASO A: Responde sin rodeos a tu Carta Roja de Enfoque (¿Qué hábito te sabotea y cómo lo vas a transformar en acción?):",
            placeholder="Sé directo y concreto..."
        )

        # --- CONSTRUCTOR GUIADO SMART (MAZO 2) Y PER (MAZO 3) ---
        st.divider()
        st.subheader("🛠️ PASO B: Bisturí SMART y Acciones PER (Mazos 2 y 3)")
        st.markdown("Pasa tu meta por las cartas del **Mazo 2 (SMART)** y **Mazo 3 (PER)**. Al guardar, se enviarán tus archivos en **PDF y Markdown** a tu Consejero y a tu correo.")

        col_trim, col_ruta_sel = st.columns(2)
        with col_trim:
            trimestre = st.selectbox(
                "Periodo del Ciclo Personal:",
                [
                    "Trimestre 1 (Ene - Mar)",
                    "Trimestre 2 (Abr - Jun)",
                    "Trimestre 3 (Jul - Sep)",
                    "Trimestre 4 (Oct - Dic)",
                    "Ciclo Cuatrimestral (4 meses)",
                    "Ciclo Semestral (6 meses)"
                ]
            )
        with col_ruta_sel:
            lista_rutas = list(rutas.keys())
            idx_sugerido = lista_rutas.index(ruta_enfoque)
            ruta_elegida = st.selectbox("Ruta que acreditarás en este Ciclo:", lista_rutas, index=idx_sugerido)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            obj_s = st.text_input(
                "🎯 [S] Específico (Carta 2.1 y 2.2 - ¿Qué producto/certificación exacta lograrás y cómo servirá a otros?):",
                placeholder="Prohibido usar 'mejorar' o 'echarle ganas'. Ej: Certificarme en Primeros Auxilios y capacitar a la Tropa."
            )
            obj_m = st.text_input(
                "📏 [M] Medible (Carta 2.3 y 2.4 - ¿Qué número frío demostrará tu éxito ante el Parlamento?):",
                placeholder="Ej: 40 horas de curso, 1 certificado oficial y 25 scouts capacitados."
            )
            obj_a = st.text_input(
                "⚙️ [A] Alcanzable (Carta 2.5 - ¿Qué día y hora exacta de tu agenda semanal le dedicarás y cómo lo costearás?):",
                placeholder="Ej: Sábados de 9:00 a 13:00 h; autofinanciado con $800 MXN de mis ahorros."
            )
        with col_s2:
            obj_r = st.text_input(
                "🤝 [R] Realista (Carta 2.6 y 2.7 - ¿Qué Experto/Institución externa te evaluará y cuál es tu Plan B ante riesgos?):",
                placeholder="Ej: Instructor certificado de Cruz Roja Mexicana / Plan B: Curso Protección Civil municipal."
            )
            obj_t = st.text_input(
                "⏳ [T] Tiempo límite (Carta 2.8 - Fecha de inicio, fecha de ejecución de servicio y fecha de Parlamento):",
                placeholder="Ej: Inicio Semana 1 | Servicio comunitario Semana 10 | Revisión Parlamento Semana 12."
            )

        st.markdown("#### 🔄 Metodología PER (Conozco, Aplico, Comparto)")
        c_p, c_e, c_r = st.columns(3)
        with c_p:
            per_planea = st.text_area("1️⃣ PLANEA / Conozco (Carta 3.1)", placeholder="Investigación teórica, contacto con asesor externo y protocolo A Salvo del Peligro...")
        with c_e:
            per_ejecuta = st.text_area("2️⃣ EJECUTA / Aplico (Carta 3.2)", placeholder="Práctica constante fuera y dentro del Clan, bitácora y pruebas fotográficas en Drive...")
        with c_r:
            per_revisa = st.text_area("3️⃣ REVISA / Comparto (Carta 3.3)", placeholder="Servicio comunitario, evaluación 360° y registro en sdgs.scout.org...")

        verbos_ambiguos = ["mejorar", "intentar", "tratar", "echarle ganas", "apoyar", "fomentar", "concientizar"]
        alerta_ambigua = [v for v in verbos_ambiguos if v in obj_s.lower()]
        if alerta_ambigua:
            st.warning(f"⚠️ **Filtro Socrático activado:** Usaste palabras ambiguas ({', '.join(alerta_ambigua)}) en tu objetivo [S]. Cámbialas por un verbo de acción verificable (ej. *Construir, Certificar, Reducir, Impartir, Diseñar*).")

        if st.button("🚀 Guardar Ciclo Personal y Enviar Archivos (PDF + Markdown) a mi Consejero", type="primary", use_container_width=True):
            if not all([respuesta_socratica.strip(), obj_s.strip(), obj_m.strip(), obj_a.strip(), obj_r.strip(), obj_t.strip()]):
                st.error("⚠️ Debes responder tu Carta Socrática y completar los 5 campos SMART antes de guardar.")
            else:
                ahora_str = obtener_hora_cdmx().strftime("%d/%m/%Y %H:%M")
                payload_f2 = {
                    "fecha_hora": ahora_str,
                    "nombre": rover_seleccionado,
                    "clan": clan_seleccionado,
                    "correo": correo_rover,
                    "pts_kikapu": rutas["🔵 Ruta Kikapú (Salud y Bienestar)"],
                    "pts_otomi": rutas["🟠 Ruta Otomí (Habilidades para la Vida)"],
                    "pts_maya": rutas["🟢 Ruta Maya (Medio Ambiente y Sustentabilidad)"],
                    "pts_wixarika": rutas["🟣 Ruta Wixárika (Paz y Participación Comunitaria)"],
                    "ruta_enfoque": ruta_elegida,
                    "ruta_fortaleza": ruta_fortaleza,
                    "geometria": geometria,
                    "carta_socratica": titulo_carta_debil,
                    "respuesta_socratica": respuesta_socratica.strip(),
                    "trimestre": trimestre,
                    "obj_s": obj_s.strip(),
                    "obj_m": obj_m.strip(),
                    "obj_a": obj_a.strip(),
                    "obj_r": obj_r.strip(),
                    "obj_t": obj_t.strip(),
                    "per_planea": per_planea.strip(),
                    "per_ejecuta": per_ejecuta.strip(),
                    "per_revisa": per_revisa.strip()
                }

                with st.spinner("Generando archivos (PDF y Markdown), guardando en Google Sheets y enviando a tu Consejero..."):
                    markdown_notion = generar_markdown_ciclo(payload_f2)
                    bytes_pdf = generar_pdf_ficha_ram(payload_f2)

                    guardar_ciclo_fase2(payload_f2)
                    try:
                        nombre_pdf, nombre_md = enviar_correo_ciclo(payload_f2, bytes_pdf, markdown_notion)
                        st.success(f"✅ ¡Listo! Se guardó tu registro y se enviaron los archivos **{nombre_pdf}** y **{nombre_md}** al correo de tu Consejero Rover y a tu correo ({correo_rover}).")
                    except Exception as e:
                        nombre_pdf = f"Ciclo_Personal_{rover_seleccionado.replace(' ', '_')}.pdf"
                        nombre_md = f"Ciclo_Personal_{rover_seleccionado.replace(' ', '_')}.md"
                        st.warning(f"Se generaron tus archivos, pero hubo un detalle al enviar el correo: {e}")

                # Botones de descarga inmediata
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="📄 Descargar mi Ficha en PDF",
                        data=bytes_pdf,
                        file_name=nombre_pdf,
                        mime="application/pdf",
                        use_container_width=True
                    )
                with col_dl2:
                    st.download_button(
                        label="📝 Descargar archivo Markdown (.md) para Notion",
                        data=markdown_notion.encode("utf-8"),
                        file_name=nombre_md,
                        mime="text/markdown",
                        use_container_width=True
                    )

                st.subheader("📋 O copia y pega este bloque directamente en tu Agenda Rover de Notion:")
                st.code(markdown_notion, language="markdown")

# ==============================================================================
# MODO 2: VISTA MAESTRA DEL CONSEJERO (CRUCE PARA LOS 4 CICLOS DE CLAN)
# ==============================================================================
else:
    st.title("🏛️ Vista Maestra: Generador de los 4 Ciclos de Clan")
    st.markdown(
        "Esta vista lee todos los registros del Google Sheets original de la **Rueda de la Vida**, calcula las **4 Rutas (Kikapú, Otomí, Maya y Wixárika)** "
        "de todo el Clan y agrupa a los Rovers para diseñar los **4 Ciclos de Programa** de **Malinalli** y **Tic Temoaya Ochan**."
    )

    if not df_registros.empty:
        df_unicos = df_registros.drop_duplicates(subset=["nombre"], keep="last").copy()

        filas_procesadas = []
        for _, row in df_unicos.iterrows():
            vals = [
                int(row["corporalidad"]), int(row["creatividad"]), int(row["caracter"]),
                int(row["afectividad"]), int(row["sociabilidad"]), int(row["espiritualidad"])
            ]
            rutas, r_enf, r_fort, geom, t_carta, _, _, _ = analizar_perfil_rover(vals)
            filas_procesadas.append({
                "Rover": row["nombre"],
                "Balance": round(float(np.mean(vals)), 1),
                "🔵 Kikapú": rutas["🔵 Ruta Kikapú (Salud y Bienestar)"],
                "🟠 Otomí": rutas["🟠 Ruta Otomí (Habilidades para la Vida)"],
                "🟢 Maya": rutas["🟢 Ruta Maya (Medio Ambiente y Sustentabilidad)"],
                "🟣 Wixárika": rutas["🟣 Ruta Wixárika (Paz y Participación Comunitaria)"],
                "🎯 Ruta de Enfoque (Más Baja)": r_enf,
                "🌟 Ruta Fortaleza (Especialidad)": r_fort,
                "🃏 Carta Socrática a debatir": t_carta,
                "Geometría": geom
            })

        df_maestro = pd.DataFrame(filas_procesadas)

        st.subheader("📊 1. Matriz General de Rutas y Cartas Socráticas por Rover")
        st.dataframe(df_maestro, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🤝 2. Agrupación Automática de Equipos por Ruta (Para el Parlamento Rover)")
        st.markdown("Usa estos grupos en el Parlamento para sentar juntos a los Rovers que comparten la misma **Ruta de Enfoque** y conectarlos con quienes tienen esa misma ruta como **Fortaleza**:")

        col_g1, col_g2 = st.columns(2)
        rutas_nombres = [
            "🔵 Ruta Kikapú (Salud y Bienestar)",
            "🟠 Ruta Otomí (Habilidades para la Vida)",
            "🟢 Ruta Maya (Medio Ambiente y Sustentabilidad)",
            "🟣 Ruta Wixárika (Paz y Participación Comunitaria)"
        ]
        for idx, r_nom in enumerate(rutas_nombres):
            with col_g1 if idx % 2 == 0 else col_g2:
                enfoque_rovers = df_maestro[df_maestro["🎯 Ruta de Enfoque (Más Baja)"] == r_nom]["Rover"].tolist()
                fortaleza_rovers = df_maestro[df_maestro["🌟 Ruta Fortaleza (Especialidad)"] == r_nom]["Rover"].tolist()
                with st.expander(f"{r_nom} ({len(enfoque_rovers)} en enfoque)", expanded=True):
                    st.markdown(f"* 🎯 **Deben desarrollar objetivo SMART aquí:** {', '.join(enfoque_rovers) if enfoque_rovers else 'Ninguno'}")
                    st.markdown(f"* 🌟 **Pueden ser mentores / liderar Especialidad aquí:** {', '.join(fortaleza_rovers) if fortaleza_rovers else 'Ninguno'}")
