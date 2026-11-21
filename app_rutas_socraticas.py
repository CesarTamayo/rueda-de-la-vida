import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
import smtplib
from email.message import EmailMessage
from datetime import datetime
import pytz

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Oráculo Rover 2027: Rutas y Cartas Socráticas",
    page_icon="🧭",
    layout="wide"
)

def obtener_hora_cdmx():
    zona_cdmx = pytz.timezone('America/Mexico_City')
    return datetime.now(zona_cdmx)

# --- 2. CONEXIÓN AL GOOGLE SHEETS ORIGINAL ---
@st.cache_data(ttl=30, show_spinner=False)
def cargar_datos_sheets():
    """
    Lee los datos guardados por la App 1 en Google Sheets.
    Soporta lectura vía SHEETS_WEBHOOK_URL (doGet) o vía SHEETS_CSV_URL.
    """
    # Opción A: Usar el mismo Webhook si ya tiene habilitado doGet(e)
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

    # Opción B: Lectura directa por URL de Google Sheets publicado como CSV
    if "SHEETS_CSV_URL" in st.secrets:
        df = pd.read_csv(st.secrets["SHEETS_CSV_URL"])
        return normalizar_columnas(df)

    return pd.DataFrame()

def normalizar_columnas(df):
    """Asegura que las 12 columnas originales de la App 1 tengan nombres estándar por posición."""
    if df.empty:
        return df
    # Si la hoja no tenía encabezados exactos, mapeamos por las 12 posiciones del payload de la App 1
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
    Recibe la lista [corporalidad, creatividad, caracter, afectividad, sociabilidad, espiritualidad]
    y devuelve las 4 Rutas (Kikapú, Otomí, Maya, Wixárika), la lectura geométrica y las Cartas Socráticas.
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
            "Mira el número que te pusiste en Corporalidad. Si sigues comiendo, durmiendo y entrenando exactamente igual que en los últimos tres meses, ¿cómo va a estar tu cuerpo a mitad de 2027? Deja los buenos deseos: ¿qué hábito físico te está saboteando hoy y qué vas a hacer con ese conocimiento para que no se quede solo en entrenar para ti, sino que le sirva también a otros?"
        ),
        1: (
            "Carta 1.2 – Creatividad (Vinculada a Ruta Otomí y Ruta Maya)",
            "¿Cuánto tiempo de tu semana pasas consumiendo lo que otros hacen en redes frente al tiempo que pasas creando soluciones o aprendiendo una habilidad técnica real? Si mañana tuvieras que resolver un problema de tu carrera, trabajo o comunidad sin presupuesto, ¿qué herramienta práctica te urge dominar hoy?"
        ),
        2: (
            "Carta 1.3 – Carácter (Vinculada a Ruta Otomí)",
            "Ser Rover es gobernar tu propia vida. ¿Cuántas cosas dejaste a medias este año porque 'no tuviste tiempo' o porque nadie te estuvo presionando? Mira tu puntaje en Carácter: ¿qué compromiso real estás evadiendo ahora mismo en tus estudios, tu casa o el Clan, y qué sistema vas a usar en 2027 para cumplir tu palabra aunque no tengas ganas?"
        ),
        3: (
            "Carta 1.4 – Afectividad (Vinculada a Ruta Kikapú y Ruta Wixárika)",
            "Cuando estás bajo presión por la escuela, el trabajo o problemas personales, ¿cómo gestionas el estrés y cómo tratas a la gente que te rodea? ¿Qué límite sano necesitas poner en tus relaciones o qué red de apoyo necesitas construir este trimestre para no quemarte?"
        ),
        4: (
            "Carta 1.5 – Sociabilidad y Comunidad (Vinculada a Ruta Wixárika)",
            "El Clan es una hermandad de servicio, no un club social de fin de semana. Fuera de tu círculo de amigos, ¿qué problema real de tu colonia, escuela o municipio estás ignorando aunque sabes que tienes la capacidad de intervenir? ¿Vas a seguir haciendo 'caridad de un día' o vas a liderar una solución que deje un antes y un después medible?"
        ),
        5: (
            "Carta 1.6 – Espiritualidad y Naturaleza (Vinculada a Ruta Maya y Ruta Wixárika)",
            "Tu puntaje en Espiritualidad habla de tu congruencia entre lo que dices que valoras y cómo vives. Mira tu consumo diario (lo que compras, la basura que generas, tu impacto al salir al aire libre): ¿qué comodidad personal estás dispuesto a recortar en 2027 para reducir tu huella ambiental y enseñar a otros a hacer lo mismo?"
        )
    }

    titulo_carta_debil, texto_carta_debil = mazo_confrontacion[indice_min]

    carta_fortaleza = (
        f"Carta 1.7 – El Espejo de la Fortaleza ({ruta_fortaleza}): "
        f"Obtuviste {valores[indice_max]}/10 en tu área más alta. En el Clan, una habilidad que ya dominas y te guardas para ti no sirve de nada. "
        f"¿En qué Especialidad para la Vida la vas a convertir este trimestre y a quién se la vas a enseñar o qué problema comunitario vas a resolver con ella?"
    )

    # Evaluación geométrica de la Rueda
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
            "¿quién tiene una debilidad donde tú eres fuerte? ¿Qué proyecto inter-clan o campamento técnico van a armar juntos en el Trimestre 1?"
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

def guardar_ciclo_fase2(payload):
    """Guarda las Rutas, respuesta socrática y Ciclo SMART+PER en la pestaña Ciclos_2027 de Google Sheets."""
    if "SHEETS_WEBHOOK_URL" not in st.secrets:
        return False, "Falta SHEETS_WEBHOOK_URL en Secrets."
    payload["origen"] = "FASE_2_SMART"
    resp = requests.post(st.secrets["SHEETS_WEBHOOK_URL"], json=payload, timeout=10)
    return (resp.status_code == 200), resp.text

def enviar_correo_ciclo_2027(payload):
    """Envía el Ciclo Personal SMART y PER al Rover y al Consejero Responsable."""
    remitente = st.secrets["EMAIL_SENDER"]
    correo_responsable = st.secrets.get("ADMIN_EMAIL", remitente)
    destinatarios = [payload["correo"]]
    if correo_responsable not in destinatarios:
        destinatarios.append(correo_responsable)

    msg = EmailMessage()
    msg["Subject"] = f"🧭 Ciclo Personal 2027 ({payload['trimestre']}): {payload['nombre']} - Clan {payload['clan']}"
    msg["From"] = remitente
    msg["To"] = ", ".join(destinatarios)

    cuerpo = (
        f"¡Siempre Listo para Servir, {payload['nombre']} (Clan {payload['clan']})!\n\n"
        f"Se ha generado tu Ruta y Ciclo Personal de Programa 2027 a partir de tu Rueda de la Vida:\n\n"
        f"=== 1. ASOCIACIÓN CON LAS 4 RUTAS ===\n"
        f"• Ruta Kikapú (Salud y Bienestar): {payload['pts_kikapu']}/10\n"
        f"• Ruta Otomí (Habilidades para la Vida): {payload['pts_otomi']}/10\n"
        f"• Ruta Maya (Medio Ambiente y Sustentabilidad): {payload['pts_maya']}/10\n"
        f"• Ruta Wixárika (Paz y Participación Comunitaria): {payload['pts_wixarika']}/10\n"
        f"-> Ruta de Enfoque elegida: {payload['ruta_enfoque']}\n"
        f"-> Ruta de Fortaleza (Especialidad): {payload['ruta_fortaleza']}\n\n"
        f"=== 2. CONFRONTACIÓN SOCRÁTICA ===\n"
        f"Carta: {payload['carta_socratica']}\n"
        f"Tu Respuesta: \"{payload['respuesta_socratica']}\"\n\n"
        f"=== 3. OBJETIVO SMART ({payload['trimestre']}) ===\n"
        f"• [S] Específico (Qué y Para qué): {payload['obj_s']}\n"
        f"• [M] Medible (Indicador numérico): {payload['obj_m']}\n"
        f"• [A] Alcanzable (Horario y recursos): {payload['obj_a']}\n"
        f"• [R] Realista (Asesor externo y Plan B): {payload['obj_r']}\n"
        f"• [T] Tiempo límite (Fechas de corte): {payload['obj_t']}\n\n"
        f"=== 4. ACCIONES EDUCATIVAS (METODOLOGÍA PER) ===\n"
        f"• PLANEA (Conozco): {payload['per_planea']}\n"
        f"• EJECUTA (Aplico): {payload['per_ejecuta']}\n"
        f"• REVISA (Comparto en servicio): {payload['per_revisa']}\n\n"
        f"Copia estos bloques directamente en tu Agenda Rover 2027 en Notion."
    )
    msg.set_content(cuerpo)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(remitente, st.secrets["EMAIL_PASSWORD"])
        smtp.send_message(msg)

# --- 4. BARRA LATERAL Y NAVEGACIÓN ---
st.sidebar.title("⚜️ Sistema Rover 2027")
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
        "Verifica que hayas agregado la función `doGet(e)` en tu Apps Script o carga aquí el archivo CSV descargado de tu Google Sheets:"
    )
    archivo_csv = st.file_uploader("Subir CSV de Google Sheets (Respaldo manual)", type=["csv"])
    if archivo_csv:
        df_registros = normalizar_columnas(pd.read_csv(archivo_csv))

# ==============================================================================
# MODO 1: TALLER INDIVIDUAL DEL ROVER (RUTAS, CARTAS SOCRÁTICAS Y DISEÑO SMART)
# ==============================================================================
if modo == "🧭 1. Taller Individual (Rutas + Cartas + SMART)":
    st.title("🧭 Fase 2: De tu Rueda de la Vida a tu Ruta y Ciclo 2027")
    st.markdown(
        "Selecciona tu registro guardado en la **Rueda de la Vida**. El sistema analizará la geometría de tu diagrama, "
        "calculará tu afinidad con las **Rutas Kikapú, Otomí, Maya y Wixárika**, y te entregará tus **Cartas Socráticas**."
    )

    if not df_registros.empty:
        # Si un Rover se registró más de una vez, tomamos su registro más reciente
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

        # Visualización del Diagrama + Puntajes de las 4 Rutas
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
        st.markdown("Pasa tu meta por las cartas del **Mazo 2 (SMART)** y **Mazo 3 (PER)**. Al guardar, obtendrás el bloque listo para pegar en tu **Notion**.")

        col_trim, col_ruta_sel = st.columns(2)
        with col_trim:
            trimestre = st.selectbox("Trimestre del Ciclo Personal 2027:", ["T1 (Ene - Mar 2027)", "T2 (Abr - Jun 2027)", "T3 (Jul - Sep 2027)", "T4 (Oct - Dic 2027)"])
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
                placeholder="Ej: Inicio 15/Ene/2027 | Servicio 13/Mar/2027 | Revisión Parlamento 27/Mar/2027."
            )

        st.markdown("#### 🔄 Metodología PER (Conozco, Aplico, Comparto)")
        c_p, c_e, c_r = st.columns(3)
        with c_p:
            per_planea = st.text_area("1️⃣ PLANEA / Conozco (Carta 3.1)", placeholder="Investigación teórica, contacto con asesor externo y protocolo A Salvo del Peligro (SfH)...")
        with c_e:
            per_ejecuta = st.text_area("2️⃣ EJECUTA / Aplico (Carta 3.2)", placeholder="Práctica constante fuera y dentro del Clan, bitácora y pruebas fotográficas en Drive...")
        with c_r:
            per_revisa = st.text_area("3️⃣ REVISA / Comparto (Carta 3.3)", placeholder="Servicio comunitario, evaluación 360° y registro en sdgs.scout.org / ExplorApp...")

        # Validador automático de verbos ambiguos
        verbos_ambiguos = ["mejorar", "intentar", "tratar", "echarle ganas", "apoyar", "fomentar", "concientizar"]
        alerta_ambigua = [v for v in verbos_ambiguos if v in obj_s.lower()]
        if alerta_ambigua:
            st.warning(f"⚠️ **Filtro Socrático activado:** Usaste palabras ambiguas ({', '.join(alerta_ambigua)}) en tu objetivo [S]. cámbialas por un verbo de acción verificable (ej. *Construir, Certificar, Reducir, Impartir, Diseñar*).")

        if st.button("🚀 Guardar Mi Ciclo 2027 en Google Sheets, Enviar a mi Correo y Generar Código para Notion", type="primary", use_container_width=True):
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
                with st.spinner("Registrando tu Ciclo Personal 2027 y enviando copia a tu Consejero..."):
                    ok_s, msg_s = guardar_ciclo_fase2(payload_f2)
                    try:
                        enviar_correo_ciclo_2027(payload_f2)
                        st.success(f"✅ ¡Ciclo Personal 2027 guardado y enviado por correo a {correo_rover} y a tu Consejero!")
                    except Exception as e:
                        st.warning(f"Se procesó tu ficha, pero hubo un detalle con el correo: {e}")

                st.subheader("📋 Copia y pega este bloque directamente en tu Agenda Rover de Notion:")
                markdown_notion = f"""### 🧭 Ciclo Personal: {trimestre} — {rover_seleccionado} (Clan {clan_seleccionado})
* **Ruta de Enfoque:** {ruta_elegida} | **Ruta de Fortaleza (Especialidad):** {ruta_fortaleza}
* **Carta Socrática Trabajada ({titulo_carta_debil}):** *"{respuesta_socratica.strip()}"*

| Criterio SMART | Definición Aprobada | Estado |
| :--- | :--- | :--- |
| **S (Específico)** | {obj_s.strip()} | ✅ |
| **M (Medible)** | {obj_m.strip()} | ✅ |
| **A (Alcanzable)** | {obj_a.strip()} | ✅ |
| **R (Realista / Asesor)** | {obj_r.strip()} | ✅ |
| **T (Tiempo límite)** | {obj_t.strip()} | ✅ |

* **1. PLANEA (Conozco):** {per_planea.strip()}
* **2. EJECUTA (Aplico):** {per_ejecuta.strip()}
* **3. REVISA (Comparto):** {per_revisa.strip()}
"""
                st.code(markdown_notion, language="markdown")

# ==============================================================================
# MODO 2: VISTA MAESTRA DEL CONSEJERO (CRUCE PARA LOS 4 CICLOS DE CLAN 2027)
# ==============================================================================
else:
    st.title("🏛️ Vista Maestra: Generador de los 4 Ciclos de Clan 2027")
    st.markdown(
        "Esta vista lee todos los registros del Google Sheets original de la **Rueda de la Vida**, calcula las **4 Rutas (Kikapú, Otomí, Maya y Wixárika)** "
        "de todo el Clan y agrupa a los Rovers para diseñar los **4 Ciclos de Programa 2027** de **Malinalli** y **Tic Temoaya Ochan**."
    )

    if not df_registros.empty:
        # Tomar el último registro único por cada Rover
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
        st.markdown("Usa estos grupos en la sesión de diciembre/enero para sentar juntos a los Rovers que comparten la misma **Ruta de Enfoque** y conectarlos con quienes tienen esa misma ruta como **Fortaleza**:")

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
