import streamlit as st
import plotly.graph_objects as go
import numpy as np
import smtplib
from email.message import EmailMessage
from datetime import datetime
import pytz
import requests

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mi Rueda de la Vida", page_icon="🎡", layout="centered")

# Estado de sesión para evitar registros duplicados del mismo participante
if "ultima_firma_guardada" not in st.session_state:
    st.session_state.ultima_firma_guardada = ""

def obtener_hora_cdmx():
    """Obtiene la fecha y hora exacta de la Ciudad de México."""
    zona_cdmx = pytz.timezone('America/Mexico_City')
    return datetime.now(zona_cdmx)

@st.cache_data(show_spinner=False)
def exportar_en_memoria(_figura, formato, _firma_datos):
    """Convierte el gráfico a PNG o PDF directamente en la memoria RAM."""
    return _figura.to_image(format=formato, width=850, height=850, scale=2)

def guardar_en_google_sheets(fecha_hora, nombre, correo, valores, promedio, superpoder, area_enfoque):
    """Envía los resultados del participante a Google Sheets vía Webhook."""
    if "SHEETS_WEBHOOK_URL" not in st.secrets:
        return False, "Falta configurar SHEETS_WEBHOOK_URL en los Secrets de Streamlit."
    
    payload = {
        "fecha_hora": fecha_hora,
        "nombre": nombre,
        "correo": correo if correo else "No proporcionado",
        "corporalidad": int(valores[0]),
        "creatividad": int(valores[1]),
        "caracter": int(valores[2]),
        "afectividad": int(valores[3]),
        "sociabilidad": int(valores[4]),
        "espiritualidad": int(valores[5]),
        "promedio": round(float(promedio), 2),
        "superpoder": superpoder,
        "area_enfoque": area_enfoque
    }
    
    respuesta = requests.post(st.secrets["SHEETS_WEBHOOK_URL"], json=payload, timeout=10)
    return (respuesta.status_code == 200), respuesta.text

def enviar_correo_ram(email_destino, nombre_usuario, bytes_pdf, nombre_archivo, promedio, area_fuerte):
    """Envía el PDF adjunto leyendo los bytes directamente desde la RAM."""
    msg = EmailMessage()
    msg['Subject'] = f'🎡 Tu Rueda de la Vida - {nombre_usuario}'
    msg['From'] = st.secrets["EMAIL_SENDER"]
    msg['To'] = email_destino
    
    cuerpo = (
        f"¡Hola, {nombre_usuario}!\n\n"
        f"Aquí tienes el resultado de tu Rueda de la Vida generada hoy.\n\n"
        f"📊 Tu Resumen Rápido:\n"
        f"• Balance General: {promedio:.1f} / 10\n"
        f"• Tu Superpoder actual: {area_fuerte}\n\n"
        f"Adjunto encontrarás tu gráfico en formato PDF listo para imprimir o guardar.\n"
        f"¡Mucho éxito en tu camino de crecimiento!"
    )
    msg.set_content(cuerpo)
    msg.add_attachment(bytes_pdf, maintype='application', subtype='pdf', filename=nombre_archivo)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"])
        smtp.send_message(msg)

# --- 2. DEFINICIÓN DE LAS 6 ÁREAS ---
areas = [
    {
        "nombre": "🏃‍♂️ Corporalidad",
        "color": "rgba(255, 99, 132, 0.45)",
        "pregunta": "¿Qué tal andas de energía, sueño, alimentación y ejercicio?"
    },
    {
        "nombre": "💡 Creatividad",
        "color": "rgba(255, 205, 86, 0.45)",
        "pregunta": "¿Dedicas tiempo a tus hobbies, aprender cosas nuevas y resolver retos?"
    },
    {
        "nombre": "🛡️ Carácter",
        "color": "rgba(153, 102, 255, 0.45)",
        "pregunta": "¿Cómo sientes tu autocontrol, disciplina, resiliencia y metas?"
    },
    {
        "nombre": "❤️ Afectividad",
        "color": "rgba(255, 159, 64, 0.45)",
        "pregunta": "¿Cómo va la gestión de tus emociones, familia y relaciones cercanas?"
    },
    {
        "nombre": "🤝 Sociabilidad",
        "color": "rgba(54, 162, 235, 0.45)",
        "pregunta": "¿Qué tan conectado te sientes con tus amigos, comunidad y servicio?"
    },
    {
        "nombre": "🕊️ Espiritualidad",
        "color": "rgba(75, 192, 192, 0.45)",
        "pregunta": "¿Sientes paz interior, propósito de vida y conexión con tus creencias?"
    }
]

# --- 3. ENCABEZADO Y CAPTURA INTERACTIVA ---
st.title("🎡 Tu Rueda de la Vida")
st.markdown("Mueve los controles del **1** *(total descuido)* al **10** *(plenitud total)* y descubre qué tan equilibrada rueda tu vida hoy.")

st.subheader("1️⃣ Evalúa tu momento actual")

valores = []
col1, col2 = st.columns(2)

for i, area in enumerate(areas):
    columna_actual = col1 if i % 2 == 0 else col2
    with columna_actual:
        val = st.slider(
            label=f"**{area['nombre']}**",
            min_value=1,
            max_value=10,
            value=6,
            step=1,
            help=area["pregunta"]
        )
        st.caption(area["pregunta"])
        valores.append(val)

# --- 4. DIAGNÓSTICO AUTOMÁTICO EN VIVO ---
st.divider()
st.subheader("2️⃣ Tu Diagnóstico en Vivo")

promedio = np.mean(valores)
desviacion = np.std(valores)
indice_max = int(np.argmax(valores))
indice_min = int(np.argmin(valores))

area_fuerte = areas[indice_max]["nombre"]
area_debil = areas[indice_min]["nombre"]

m1, m2, m3 = st.columns(3)
m1.metric("⚡ Balance General", f"{int(promedio * 10)}%", f"{promedio:.1f} / 10 pts")
m2.metric("🔥 Tu Superpoder", area_fuerte, f"Nivel {valores[indice_max]}")
m3.metric("🎯 Área de Enfoque", area_debil, f"Nivel {valores[indice_min]}", delta_color="off")

if promedio >= 8 and desviacion < 1.5:
    st.success("🌟 **¡Rueda Todo Terreno!** Tienes un nivel de plenitud alto y muy parejo. Tu vida gira con muchísima fluidez. ¡Sigue manteniendo esos hábitos!")
elif desviacion >= 2.2:
    st.warning(f"🎢 **¡Alerta de Bache!** Destacas muchísimo en **{area_fuerte}**, pero la diferencia con **{area_debil}** hace que tu rueda dé saltos al girar. Pequeñas mejoras en {area_debil} te darán mucha paz.")
elif promedio < 5.5:
    st.info(f"🌱 **Etapa de Reconstrucción:** Es totalmente válido pasar por momentos de baja energía. No intentes subir todo de golpe; elige una acción pequeña hoy para impulsar **{area_debil}**.")
else:
    st.info(f"⚖️ **Rueda en Crecimiento:** Llevas un ritmo estable y equilibrado. Para pasar al siguiente nivel, apóyate en tu fortaleza (**{area_fuerte}**) para impulsar **{area_debil}**.")

# --- 5. PERSONALIZACIÓN Y GRÁFICO ---
st.divider()
st.subheader("3️⃣ Tu Mapa Visual")

nombre_input = st.text_input("Escribe tu nombre o apodo (obligatorio para registrar y descargar):", placeholder="Ej. Alex Rivera")
nombre_display = nombre_input.strip() if nombre_input.strip() else "Explorador(a)"

ahora_cdmx = obtener_hora_cdmx()
fecha_hora_visible = ahora_cdmx.strftime("%d/%m/%Y • %H:%M")

angulos_base = [0, 60, 120, 180, 240, 300]
nombres_categorias = [a["nombre"] for a in areas]
colores_rebanadas = [a["color"] for a in areas]

fig = go.Figure()

fig.add_trace(go.Barpolar(
    r=[10] * 6,
    theta=angulos_base,
    width=[60] * 6,
    marker_color=colores_rebanadas,
    marker_line_color="white",
    marker_line_width=2,
    hoverinfo="skip",
    showlegend=False
))

angulos_cerrados = angulos_base + [angulos_base[0]]
valores_cerrados = valores + [valores[0]]
textos_hover = nombres_categorias + [nombres_categorias[0]]

fig.add_trace(go.Scatterpolar(
    r=valores_cerrados,
    theta=angulos_cerrados,
    fill='toself',
    fillcolor='rgba(44, 62, 80, 0.38)',
    line=dict(color='#1E293B', width=3),
    marker=dict(color='#1E293B', size=9),
    text=textos_hover,
    hovertemplate="<b>%{text}</b><br>Nivel: %{r}/10<extra></extra>",
    name=nombre_display
))

fig.update_layout(
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    polar=dict(
        bgcolor="white",
        angularaxis=dict(
            tickmode="array",
            tickvals=angulos_base,
            ticktext=nombres_categorias,
            direction="clockwise",
            rotation=90,
            tickfont=dict(size=13, color="#1E293B"),
            gridcolor="rgba(0,0,0,0.12)"
        ),
        radialaxis=dict(
            visible=True,
            range=[0, 10],
            tickvals=[2, 4, 6, 8, 10],
            ticktext=["2", "4", "6", "8", "10"],
            tickfont=dict(size=10, color="#475569"),
            gridcolor="rgba(0,0,0,0.18)",
            angle=90
        )
    ),
    showlegend=False,
    margin=dict(t=100, b=50, l=65, r=65),
    title=dict(
        text=f"<b>Rueda de la Vida de {nombre_display}</b><br><sup style='color:#64748B;'>Balance: {promedio:.1f}/10  |  {fecha_hora_visible} (CDMX)</sup>",
        font=dict(size=20, color="#0F172A"),
        x=0.5,
        xanchor="center",
        y=0.95
    )
)

st.plotly_chart(fig, use_container_width=True)

# --- 6. REGISTRO EN GOOGLE SHEETS, DESCARGA Y CORREO ---
st.divider()
st.subheader("4️⃣ Registra y Guarda tu Resultado")

nombre_limpio = nombre_display.replace(" ", "_")
fecha_archivo = ahora_cdmx.strftime("%Y%m%d_%H%M")
firma_actual = f"{nombre_display}_{valores}"

# A. Botón de registro directo en el taller (Google Sheets)
if st.button("✅ Registrar mi Rueda en el Taller", use_container_width=True, type="primary"):
    if not nombre_input.strip():
        st.warning("⚠️ Por favor escribe tu nombre o apodo arriba (en el paso 3) antes de registrar.")
    elif st.session_state.ultima_firma_guardada == firma_actual:
        st.info("ℹ️ Tus resultados actuales ya están registrados en el taller.")
    else:
        with st.spinner("Registrando tu participación..."):
            try:
                ok, detalle = guardar_en_google_sheets(
                    fecha_hora_visible, nombre_display, "", valores, promedio, area_fuerte, area_debil
                )
                if ok:
                    st.session_state.ultima_firma_guardada = firma_actual
                    st.success("🎉 ¡Participación registrada con éxito! Ahora puedes descargar tu imagen abajo.")
                else:
                    st.error(f"⚠️ No se pudo registrar en la hoja: {detalle}")
            except Exception as e:
                st.error(f"❌ Error de conexión al registrar: {e}")

# B. Preparación de archivos en RAM para descarga directa
try:
    bytes_png = exportar_en_memoria(fig, "png", firma_actual)
    bytes_pdf = exportar_en_memoria(fig, "pdf", firma_actual)
    exportacion_lista = True
except Exception as e:
    exportacion_lista = False
    st.error(f"⚠️ No se pudo preparar la descarga: {e}")

if exportacion_lista:
    col_png, col_pdf = st.columns(2)
    
    with col_png:
        st.download_button(
            label="📸 Descargar Imagen (PNG)",
            data=bytes_png,
            file_name=f"Rueda_{nombre_limpio}_{fecha_archivo}.png",
            mime="image/png",
            use_container_width=True
        )
        
    with col_pdf:
        st.download_button(
            label="📄 Descargar Documento (PDF)",
            data=bytes_pdf,
            file_name=f"Rueda_{nombre_limpio}_{fecha_archivo}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # C. Opción de correo (también registra en Google Sheets si no lo había hecho antes)
    with st.expander("📩 ¿Prefieres recibir el PDF en tu correo electrónico?"):
        correo_input = st.text_input("Tu correo electrónico:", placeholder="ejemplo@correo.com")
        if st.button("Enviar a mi correo y registrar", use_container_width=True):
            if not correo_input or "@" not in correo_input or "." not in correo_input:
                st.warning("⚠️ Por favor escribe un correo electrónico válido.")
            else:
                with st.spinner("Guardando registro y enviando correo..."):
                    # 1. Guardar en Google Sheets (si aún no se ha guardado esta combinación)
                    firma_con_correo = f"{firma_actual}_{correo_input.strip()}"
                    if st.session_state.ultima_firma_guardada != firma_con_correo:
                        try:
                            ok, _ = guardar_en_google_sheets(
                                fecha_hora_visible, nombre_display, correo_input.strip(),
                                valores, promedio, area_fuerte, area_debil
                            )
                            if ok:
                                st.session_state.ultima_firma_guardada = firma_con_correo
                        except Exception:
                            pass # No bloqueamos el envío de correo si falla Sheets

                    # 2. Enviar el correo con el PDF desde la RAM
                    try:
                        nombre_pdf = f"Rueda_{nombre_limpio}_{fecha_archivo}.pdf"
                        enviar_correo_ram(correo_input.strip(), nombre_display, bytes_pdf, nombre_pdf, promedio, area_fuerte)
                        st.success(f"✅ ¡Listo! Resultado registrado y enviado a {correo_input}.")
                    except Exception as e:
                        st.error(f"❌ No se pudo enviar el correo. Usa los botones de descarga directa de arriba. ({e})")
