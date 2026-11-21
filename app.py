import streamlit as st
import plotly.graph_objects as go
import smtplib
from email.message import EmailMessage
from datetime import datetime
import pytz

def obtener_hora_cdmx():
    """Función auxiliar para obtener la hora exacta de la CDMX"""
    zona_cdmx = pytz.timezone('America/Mexico_City')
    return datetime.now(zona_cdmx)

def enviar_correo(email_rover, nombre_usuario, clan, cum, bytes_pdf, nombre_archivo, ruta_prioritaria, ruta_fortaleza, reflexion):
    """Envía el PDF generado en memoria al Rover y al Consejero Rover vía SMTP"""
    
    remitente = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"]
    # Si tienes un correo específico de consejero en secrets lo usa; si no, envía copia al mismo EMAIL_SENDER
    correo_consejero = st.secrets.get("EMAIL_CONSEJERO", remitente)
    
    # Lista de destinatarios (Rover + Consejero)
    destinatarios = [ email_rover ]
    if correo_consejero not in destinatarios:
        destinatarios.append(correo_consejero)
    
    msg = EmailMessage()
    msg['Subject'] = f'🧭 Autodiagnóstico Rueda de la Vida 2027: {nombre_usuario} (Clan {clan})'
    msg['From'] = remitente
    msg['To'] = ", ".join(destinatarios)
    
    cuerpo_mensaje = (
        f"¡Hola, {nombre_usuario}! ¡Siempre Listo para Servir!\n\n"
        f"Se ha registrado con éxito tu Autodiagnóstico (Paso 1: Descubrimiento) para diseñar "
        f"tu Ciclo Personal de Programa 2027.\n\n"
        f"--- DATOS DEL ROVER ---\n"
        f"• Nombre: {nombre_usuario}\n"
        f"• Clan: {clan}\n"
        f"• CUM: {cum if cum else 'No especificado'}\n\n"
        f"--- VINCULACIÓN CON RUTAS DE PROGRESIÓN (PJ.OS) ---\n"
        f"• 🎯 Eje / Ruta sugerida para fortalecer (Objetivo SMART): {ruta_prioritaria}\n"
        f"• 🌟 Eje / Ruta de mayor fortaleza (Para Especialidad / Servicio): {ruta_fortaleza}\n\n"
        f"--- COMPROMISO Y REFLEXIÓN INICIAL 2027 ---\n"
        f"\"{reflexion if reflexion else 'Sin reflexión registrada.'}\"\n\n"
        f"Adjunto a este correo encontrarás el PDF oficial con tu Rueda de la Vida. "
        f"Recuerda subir tu gráfico a tu Agenda Rover en Notion y a tu carpeta de evidencias.\n\n"
        f"¡Mucho éxito remando tu propia canoa este 2027!"
    )
    msg.set_content(cuerpo_mensaje)
    
    # Adjuntar el PDF directamente desde los bytes en memoria
    msg.add_attachment(bytes_pdf, maintype='application', subtype='pdf', filename=nombre_archivo)
    
    # Conectarse al servidor de Gmail y enviar
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(remitente, password)
        smtp.send_message(msg)

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Rueda de la Vida Rover 2027", page_icon="🧭", layout="centered")

st.title("🧭 Tu Rueda de la Vida: Clan de Rovers 2027")
st.write(
    "**Paso 1: Autodiagnóstico.** Ajusta tus niveles del 1 al 10, identifica la Ruta de Progresión "
    "que impulsarás en tu Ciclo Personal 2027, recibe tu PDF por correo y descarga tu imagen para **Notion**."
)

# 1. Captura de datos del Rover
col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre completo del Rover: *", "")
    clan = st.selectbox("Selecciona tu Clan: *", ["Malinalli", "Tic Temoaya Ochan"])
with col2:
    correo = st.text_input("Tu correo electrónico (para recibir resultados): *", "")
    cum = st.text_input("CUM (Clave Única de Membresía):", "")

nombre_display = nombre.strip() if nombre.strip() else "Rover Scout"

st.divider()

# 2. Categorías (Áreas de Crecimiento + Enfoque de Sustentabilidad)
categorias = [
    '✚ Corporalidad', 
    '★ Creatividad', 
    '⛨ Carácter', 
    '♥ Afectividad', 
    '✿ Sociabilidad', 
    '☀ Espiritualidad'
]

st.subheader("📊 Evalúa tus Dimensiones Personales")
st.caption("1 = Necesito desarrollar urgentemente | 5 = En equilibrio | 10 = Domino y comparto con los demás")

col_izq, col_der = st.columns(2)
valores = []
for i, cat in enumerate(categorias):
    with col_izq if i % 2 == 0 else col_der:
        val = st.slider(cat, min_value=1, max_value=10, value=5, step=1)
        valores.append(val)

# Mapeo de las 6 dimensiones hacia los 4 Ejes Temáticos / Rutas del PJ.OS
# Índices: 0=Corporalidad, 1=Creatividad, 2=Carácter, 3=Afectividad, 4=Sociabilidad, 5=Espiritualidad
rutas_pjos = {
    "🔵 Salud y Bienestar (Ruta Kikapú)": (valores[0] + valores[3]) / 2,
    "🟠 Habilidades para la Vida (Ruta Otomí)": (valores[1] + valores[2]) / 2,
    "🟢 Medio Ambiente y Sustentabilidad (Ruta Maya)": (valores[0] + valores[1] + valores[5]) / 3,
    "🟣 Paz y Participación Comunitaria (Ruta Wixárika)": (valores[4] + valores[5]) / 2
}

ruta_prioritaria = min(rutas_pjos, key=rutas_pjos.get)
ruta_fortaleza = max(rutas_pjos, key=rutas_pjos.get)

# --- GENERACIÓN DEL GRÁFICO ---
categorias_grafico = categorias + [categorias[0]]
valores_grafico = valores + [valores[0]]

ahora_cdmx = obtener_hora_cdmx()
fecha_hora_visible = ahora_cdmx.strftime("%d/%m/%Y a las %H:%M")
fecha_hora_archivo = ahora_cdmx.strftime("%Y%m%d_%H%M%S")

fig = go.Figure()
fig.add_trace(go.Scatterpolar(
    r=valores_grafico,
    theta=categorias_grafico,
    fill='toself',
    name=nombre_display,
    line_color='#D9232E',
    fillcolor='rgba(217, 35, 46, 0.35)'
))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
    showlegend=False,
    title=dict(
        text=f"Rueda de la Vida: {nombre_display} (Clan {clan})<br><sup style='color:gray;'>Generado el: {fecha_hora_visible} (CDMX)</sup>", 
        font=dict(size=18),
        y=0.95
    )
)

st.plotly_chart(fig, use_container_width=True)

# --- ORIENTACIÓN AUTOMÁTICA PARA EL CICLO PERSONAL 2027 ---
st.info(
    f"🧭 **Brújula para tu Ciclo Personal 2027:**\n"
    f"- **Ruta sugerida para fortalecer (Objetivo SMART):** {ruta_prioritaria}\n"
    f"- **Ruta de mayor fortaleza (Especialidad / Servicio):** {ruta_fortaleza}"
)

reflexion = st.text_area(
    "📝 Mi compromiso inicial para 2027 (¿Qué acción o especialidad trabajaré en mi primer ciclo?):",
    placeholder="Ejemplo: En el trimestre Enero-Marzo trabajaré la Ruta Kikapú mejorando mi condición física y certificándome en primeros auxilios..."
)

# --- BOTÓN DE ENVÍO Y DESCARGA PARA NOTION ---
if st.button("🚀 Enviar Resultados a mi Consejero y Habilitar Descarga para Notion", type="primary"):
    if not nombre.strip():
        st.warning("⚠️ Por favor, ingresa tu nombre completo antes de continuar.")
    elif not correo or "@" not in correo or "." not in correo:
        st.error("⚠️ Por favor, ingresa un correo electrónico válido.")
    else:
        with st.spinner("Generando archivos (PDF y PNG) y enviando copia a tu Consejero Rover..."):
            try:
                nombre_limpio = nombre_display.replace(' ', '_')
                nombre_pdf = f"Rueda_Vida_{clan}_{nombre_limpio}_{fecha_hora_archivo}.pdf"
                nombre_png = f"Rueda_Vida_{clan}_{nombre_limpio}_{fecha_hora_archivo}.png"
                
                # Generar PDF y PNG directamente en memoria RAM con Kaleido
                bytes_pdf = fig.to_image(format="pdf")
                bytes_png = fig.to_image(format="png", width=900, height=750, scale=2)
                
                # Enviar correo al Rover y al Consejero
                enviar_correo(
                    correo, nombre_display, clan, cum, 
                    bytes_pdf, nombre_pdf, 
                    ruta_prioritaria, ruta_fortaleza, reflexion
                )
                
                st.success(f"✅ ¡Éxito! Tu diagnóstico fue enviado a **{correo}** y al correo de tu Consejero Rover.")
                
                # Botones de descarga inmediata para Notion y Google Drive
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.download_button(
                        label="📥 Descargar Imagen (PNG) para pegar en Notion",
                        data=bytes_png,
                        file_name=nombre_png,
                        mime="image/png"
                    )
                with col_btn2:
                    st.download_button(
                        label="📄 Descargar Reporte (PDF) para Google Drive",
                        data=bytes_pdf,
                        file_name=nombre_pdf,
                        mime="application/pdf"
                    )
                    
            except Exception as e:
                st.error(f"❌ Ocurrió un error al procesar el envío: {e}")
