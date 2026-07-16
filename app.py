import streamlit as st
import plotly.graph_objects as go
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime  # <-- NUEVA LIBRERÍA PARA LA FECHA Y HORA

def enviar_correo(email_destino, nombre_usuario, figura):
    """Genera el PDF y lo envía por correo electrónico usando SMTP"""
    
    # Formato de fecha para el nombre del archivo (Ej: 20260716_153025)
    fecha_hora_archivo = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"Rueda_Vida_{nombre_usuario.replace(' ', '_')}_{fecha_hora_archivo}.pdf"
    
    # 1. Guardar el gráfico como PDF temporalmente en el servidor
    figura.write_image(nombre_archivo, format="pdf", engine="kaleido")
    
    # 2. Construir el mensaje de correo
    msg = EmailMessage()
    msg['Subject'] = 'Tus Resultados: Rueda de la Vida 🎡'
    msg['From'] = st.secrets["EMAIL_SENDER"]
    msg['To'] = email_destino
    
    cuerpo_mensaje = (
        f"¡Hola, {nombre_usuario}!\n\n"
        f"Gracias por participar. Adjunto a este correo encontrarás el PDF "
        f"con tu Rueda de la Vida generada el día de hoy.\n\n"
        f"¡Mucho éxito en tu crecimiento personal!"
    )
    msg.set_content(cuerpo_mensaje)
    
    # 3. Leer el PDF y adjuntarlo al correo
    with open(nombre_archivo, 'rb') as f:
        datos_pdf = f.read()
        
    msg.add_attachment(datos_pdf, maintype='application', subtype='pdf', filename=nombre_archivo)
    
    # 4. Conectarse al servidor de Gmail y enviar
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"])
        smtp.send_message(msg)
        
    # 5. Limpieza: borrar el archivo temporal del servidor
    if os.path.exists(nombre_archivo):
        os.remove(nombre_archivo)

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Rueda de la Vida", page_icon="🎡", layout="centered")

st.title("🎡 Tu Rueda de la Vida")
st.write("Ajusta tus niveles, ingresa tus datos y recibe tu PDF por correo.")

# Captura de datos del usuario
nombre = st.text_input("Nombre completo:", "")
nombre_display = nombre if nombre else "Usuario"
correo = st.text_input("Correo electrónico para recibir tus resultados:", "")

# Categorías
categorias = [
    '✚ Corporalidad', '★ Creatividad', '⛨ Carácter', 
    '♥ Afectividad', '✿ Sociabilidad', '☀ Espiritualidad'
]

# Deslizadores
st.subheader("Tus Puntuaciones")
valores = []
for cat in categorias:
    val = st.slider(cat, min_value=1, max_value=10, value=5, step=1)
    valores.append(val)

# --- GENERACIÓN DEL GRÁFICO ---
categorias_grafico = categorias + [categorias[0]]
valores_grafico = valores + [valores[0]]

# Obtener fecha y hora actual con formato legible (Ej: 16/07/2026 a las 15:30)
fecha_hora_visible = datetime.now().strftime("%d/%m/%Y a las %H:%M")

fig = go.Figure()
fig.add_trace(go.Scatterpolar(
    r=valores_grafico,
    theta=categorias_grafico,
    fill='toself',
    name=nombre_display,
    line_color='#2C3E50',
    fillcolor='rgba(44, 62, 80, 0.4)'
))

# Configuramos el diseño y agregamos la fecha como un subtítulo (usando HTML en el título)
fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
    showlegend=False,
    title=dict(
        text=f"Rueda de la Vida de {nombre_display}<br><sup style='color:gray;'>Generado el: {fecha_hora_visible}</sup>", 
        font=dict(size=20),
        y=0.95 # Subimos un poco el título para que quepa bien el subtítulo
    )
)

st.plotly_chart(fig, use_container_width=True)

# --- BOTÓN DE ENVÍO ---
if st.button("Generar PDF y Enviar a mi Correo", type="primary"):
    if not correo:
        st.warning("⚠️ Por favor, ingresa un correo electrónico válido antes de enviar.")
    elif "@" not in correo or "." not in correo:
        st.error("⚠️ El formato del correo parece ser incorrecto.")
    else:
        with st.spinner("Generando PDF y enviando correo..."):
            try:
                enviar_correo(correo, nombre_display, fig)
                st.success(f"✅ ¡Éxito! Tu Rueda de la Vida ha sido enviada a {correo}.")
            except Exception as e:
                st.error("❌ Ocurrió un error al enviar el correo. Por favor contacta al administrador.")
