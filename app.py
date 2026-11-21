import streamlit as st
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import io
import smtplib
from email.message import EmailMessage
from datetime import datetime
import pytz
import requests

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Rueda de la Vida Rover", page_icon="⚜️", layout="centered")

if "firma_registrada" not in st.session_state:
    st.session_state.firma_registrada = ""

def obtener_hora_cdmx():
    """Obtiene la fecha y hora exacta de la Ciudad de México."""
    zona_cdmx = pytz.timezone('America/Mexico_City')
    return datetime.now(zona_cdmx)

@st.cache_data(show_spinner=False)
def generar_archivos_ram(nombre_usuario, valores, promedio, fecha_hora_visible):
    """Genera la imagen PNG y el documento PDF directamente en la memoria RAM."""
    categorias_pdf = [
        'Corporalidad', 'Creatividad', 'Carácter',
        'Afectividad', 'Sociabilidad', 'Espiritualidad'
    ]
    colores_hex = ['#FF9999', '#FFE082', '#D1B3FF', '#FFB366', '#99CCFF', '#80CBC4']
    N = len(categorias_pdf)
    angulos = [n / float(N) * 2 * np.pi for n in range(N)]

    valores_cerrados = list(valores) + [valores[0]]
    angulos_cerrados = angulos + [angulos[0]]

    fig, ax = plt.subplots(figsize=(8.5, 8.5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ancho_rebanada = 2 * np.pi / N
    for i in range(N):
        ax.bar(
            angulos[i], 10, width=ancho_rebanada, bottom=0,
            color=colores_hex[i], alpha=0.55, edgecolor='white', linewidth=2
        )

    ax.set_rlabel_position(0)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], color="#475569", size=9, fontweight='bold')
    ax.set_ylim(0, 10)

    ax.set_xticks(angulos)
    ax.set_xticklabels(categorias_pdf, color='#0F172A', size=12, fontweight='bold')
    ax.tick_params(axis='x', which='major', pad=28)

    ax.plot(angulos_cerrados, valores_cerrados, linewidth=3, linestyle='solid', color='#1E293B')
    ax.fill(angulos_cerrados, valores_cerrados, color='#1E293B', alpha=0.30)
    ax.scatter(angulos, valores, color='#1E293B', s=65, zorder=5)

    plt.suptitle(
        f"Rueda de la Vida — {nombre_usuario}",
        fontsize=18, fontweight='bold', color='#0F172A', y=0.97
    )
    ax.set_title(
        f"Balance General: {promedio:.1f}/10   |   {fecha_hora_visible} (CDMX)",
        fontsize=11, color='#64748B', pad=38
    )

    plt.tight_layout()

    buf_png = io.BytesIO()
    fig.savefig(buf_png, format='png', dpi=200, bbox_inches='tight', facecolor='white')
    bytes_png = buf_png.getvalue()

    buf_pdf = io.BytesIO()
    fig.savefig(buf_pdf, format='pdf', bbox_inches='tight', facecolor='white')
    bytes_pdf = buf_pdf.getvalue()

    plt.close(fig)
    return bytes_png, bytes_pdf

def guardar_en_google_sheets(fecha_hora, nombre, correo, valores, promedio, superpoder, area_enfoque):
    """Envía los resultados del Rover a Google Sheets vía Webhook."""
    if "SHEETS_WEBHOOK_URL" not in st.secrets:
        return False, "Falta configurar SHEETS_WEBHOOK_URL en los Secrets."

    payload = {
        "fecha_hora": fecha_hora,
        "nombre": nombre,
        "correo": correo,
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

def enviar_correos_ram(email_rover, nombre_usuario, bytes_pdf, nombre_archivo, promedio, area_fuerte, area_debil, valores):
    """Envía el PDF al Rover y una copia de respaldo al correo del responsable del Clan."""
    remitente = st.secrets["EMAIL_SENDER"]
    # Si defines ADMIN_EMAIL en Secrets lo usará; si no, lo enviará al mismo EMAIL_SENDER
    correo_responsable = st.secrets.get("ADMIN_EMAIL", remitente)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(remitente, st.secrets["EMAIL_PASSWORD"])

        # 1. Correo para el Rover
        msg_rover = EmailMessage()
        msg_rover['Subject'] = f'⚜️ Tu Rueda de la Vida Rover — {nombre_usuario}'
        msg_rover['From'] = remitente
        msg_rover['To'] = email_rover

        cuerpo_rover = (
            f"¡Hola, {nombre_usuario}! ¡Siempre Listo para Servir!\n\n"
            f"Aquí tienes el resultado de tu Rueda de la Vida:\n\n"
            f"📊 Resumen de tu evaluación:\n"
            f"• Balance General: {promedio:.1f} / 10\n"
            f"• Fortaleza principal: {area_fuerte}\n"
            f"• Área de oportunidad: {area_debil}\n\n"
            f"Adjunto encontrarás tu mapa visual en formato PDF para tu seguimiento personal en el Clan.\n"
            f"¡Mucho éxito remando tu propia canoa!"
        )
        msg_rover.set_content(cuerpo_rover)
        msg_rover.add_attachment(bytes_pdf, maintype='application', subtype='pdf', filename=nombre_archivo)
        smtp.send_message(msg_rover)

        # 2. Copia de respaldo para ti (Responsable / Scouter)
        msg_admin = EmailMessage()
        msg_admin['Subject'] = f'📋 Nuevo Registro Rover: {nombre_usuario} ({promedio:.1f}/10)'
        msg_admin['From'] = remitente
        msg_admin['To'] = correo_responsable

        cuerpo_admin = (
            f"Se ha registrado una nueva Rueda de la Vida en el Clan:\n\n"
            f"• Rover: {nombre_usuario}\n"
            f"• Correo: {email_rover}\n"
            f"• Balance General: {promedio:.1f} / 10\n"
            f"• Fortaleza: {area_fuerte} | Enfoque: {area_debil}\n\n"
            f"Desglose por áreas:\n"
            f"- Corporalidad: {valores[0]}/10\n"
            f"- Creatividad: {valores[1]}/10\n"
            f"- Carácter: {valores[2]}/10\n"
            f"- Afectividad: {valores[3]}/10\n"
            f"- Sociabilidad: {valores[4]}/10\n"
            f"- Espiritualidad: {valores[5]}/10\n\n"
            f"Se adjunta el PDF generado."
        )
        msg_admin.set_content(cuerpo_admin)
        msg_admin.add_attachment(bytes_pdf, maintype='application', subtype='pdf', filename=nombre_archivo)
        smtp.send_message(msg_admin)

# --- 2. DEFINICIÓN DE LAS 6 ÁREAS ---
areas = [
    {
        "nombre": "🏃‍♂️ Corporalidad",
        "color": "rgba(255, 99, 132, 0.45)",
        "pregunta": "¿Qué tal andas de energía, sueño, alimentación y actividad física?"
    },
    {
        "nombre": "💡 Creatividad",
        "color": "rgba(255, 205, 86, 0.45)",
        "pregunta": "¿Dedicas tiempo a tus hobbies, aprender cosas nuevas y resolver retos?"
    },
    {
        "nombre": "🛡️ Carácter",
        "color": "rgba(153, 102, 255, 0.45)",
        "pregunta": "¿Cómo sientes tu autocontrol, disciplina, resiliencia y metas personales?"
    },
    {
        "nombre": "❤️ Afectividad",
        "color": "rgba(255, 159, 64, 0.45)",
        "pregunta": "¿Cómo va la gestión de tus emociones, familia y relaciones cercanas?"
    },
    {
        "nombre": "🤝 Sociabilidad",
        "color": "rgba(54, 162, 235, 0.45)",
        "pregunta": "¿Qué tan conectado te sientes con el Clan, tus amigos y el servicio?"
    },
    {
        "nombre": "🕊️ Espiritualidad",
        "color": "rgba(75, 192, 192, 0.45)",
        "pregunta": "¿Sientes paz interior, propósito de vida y conexión con tus creencias?"
    }
]

# --- 3. ENCABEZADO Y CAPTURA INTERACTIVA ---
st.title("⚜️ Rueda de la Vida Rover")
st.markdown("Evalúa tu momento actual del **1** *(descuido)* al **10** *(plenitud)* en cada una de las 6 áreas de desarrollo personal.")

st.subheader("1️⃣ Evalúa tus 6 áreas")

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
m2.metric("🔥 Tu Fortaleza", area_fuerte, f"Nivel {valores[indice_max]}")
m3.metric("🎯 Área de Enfoque", area_debil, f"Nivel {valores[indice_min]}", delta_color="off")

if promedio >= 8 and desviacion < 1.5:
    st.success("🌟 **¡Rueda Equilibrada!** Tienes un nivel de plenitud alto y parejo en tus áreas de desarrollo. ¡Sigue manteniendo ese ritmo en tu ruta!")
elif desviacion >= 2.2:
    st.warning(f"🎢 **¡Alerta de Desbalance!** Destacas mucho en **{area_fuerte}**, pero la diferencia con **{area_debil}** frena tu avance. Pequeñas acciones en {area_debil} te darán mayor equilibrio.")
elif promedio < 5.5:
    st.info(f"🌱 **Etapa de Reconstrucción:** Es válido pasar por momentos de baja energía. No intentes subir todo de golpe; elige un reto pequeño hoy para impulsar **{area_debil}**.")
else:
    st.info(f"⚖️ **Rueda en Movimiento:** Llevas un ritmo estable. Apóyate en tu fortaleza (**{area_fuerte}**) para impulsar **{area_debil}** en tu plan personal.")

# --- 5. VISTA PREVIA DEL GRÁFICO ---
st.divider()
st.subheader("3️⃣ Vista Previa de tu Mapa")

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
    name="Vista Previa"
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
    margin=dict(t=80, b=50, l=65, r=65),
    title=dict(
        text=f"<b>Balance General: {promedio:.1f}/10</b><br><sup style='color:#64748B;'>{fecha_hora_visible} (CDMX)</sup>",
        font=dict(size=18, color="#0F172A"),
        x=0.5,
        xanchor="center",
        y=0.95
    )
)

st.plotly_chart(fig, use_container_width=True)

# --- 6. REGISTRO OBLIGATORIO ANTES DE DESCARGAR ---
st.divider()
st.subheader("4️⃣ Registra tus Datos para Descargar")
st.info("🔒 Para desbloquear la descarga de tu **Imagen (PNG)** y **Documento (PDF)**, ingresa tu nombre y correo electrónico. Se enviará una copia en PDF a tu correo y al registro del Clan.")

col_nom, col_mail = st.columns(2)
with col_nom:
    nombre_input = st.text_input("Nombre completo:", placeholder="Ej. Alex Rivera")
with col_mail:
    correo_input = st.text_input("Correo electrónico:", placeholder="alex@correo.com")

nombre_limpio = nombre_input.strip()
correo_limpio = correo_input.strip()
firma_actual = f"{nombre_limpio}_{correo_limpio}_{valores}"

if st.button("📩 Registrar y Desbloquear Descargas", use_container_width=True, type="primary"):
    if not nombre_limpio:
        st.warning("⚠️ Por favor escribe tu nombre completo.")
    elif not correo_limpio or "@" not in correo_limpio or "." not in correo_limpio:
        st.warning("⚠️ Por favor escribe un correo electrónico válido.")
    elif st.session_state.firma_registrada == firma_actual:
        st.info("ℹ️ Estos resultados ya fueron registrados y enviados. Puedes descargar tus archivos abajo.")
    else:
        with st.spinner("Registrando en el Clan y enviando PDF por correo..."):
            try:
                bytes_png, bytes_pdf = generar_archivos_ram(
                    nombre_limpio, tuple(valores), promedio, fecha_hora_visible
                )
                nombre_archivo_base = nombre_limpio.replace(" ", "_")
                fecha_archivo = ahora_cdmx.strftime("%Y%m%d_%H%M")
                nombre_pdf = f"Rueda_Rover_{nombre_archivo_base}_{fecha_archivo}.pdf"

                # 1. Guardar en Google Sheets
                ok_sheets, detalle_sheets = guardar_en_google_sheets(
                    fecha_hora_visible, nombre_limpio, correo_limpio,
                    valores, promedio, area_fuerte, area_debil
                )
                if not ok_sheets:
                    st.error(f"⚠️ Error al guardar en la hoja de registro: {detalle_sheets}")
                    st.stop()

                # 2. Enviar PDF al Rover y a tu correo
                enviar_correos_ram(
                    correo_limpio, nombre_limpio, bytes_pdf, nombre_pdf,
                    promedio, area_fuerte, area_debil, valores
                )

                # 3. Desbloquear botones de descarga
                st.session_state.firma_registrada = firma_actual
                st.success(f"✅ ¡Registro completado! Se envió el PDF a **{correo_limpio}** y al registro del Clan. Ya puedes descargar tus archivos:")

            except Exception as e:
                st.error(f"❌ Ocurrió un error al procesar el registro o envío de correo: {e}")

# --- 7. BOTONES DE DESCARGA (SOLO VISIBLES TRAS REGISTRAR) ---
if st.session_state.firma_registrada == firma_actual and nombre_limpio and correo_limpio:
    bytes_png, bytes_pdf = generar_archivos_ram(
        nombre_limpio, tuple(valores), promedio, fecha_hora_visible
    )
    nombre_archivo_base = nombre_limpio.replace(" ", "_")
    fecha_archivo = ahora_cdmx.strftime("%Y%m%d_%H%M")

    col_png, col_pdf = st.columns(2)
    with col_png:
        st.download_button(
            label="📸 Descargar Imagen (PNG)",
            data=bytes_png,
            file_name=f"Rueda_Rover_{nombre_archivo_base}_{fecha_archivo}.png",
            mime="image/png",
            use_container_width=True
        )
    with col_pdf:
        st.download_button(
            label="📄 Descargar Documento (PDF)",
            data=bytes_pdf,
            file_name=f"Rueda_Rover_{nombre_archivo_base}_{fecha_archivo}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
elif st.session_state.firma_registrada != "" and st.session_state.firma_registrada != firma_actual:
    st.caption("🔄 *Modificaste algún valor, nombre o correo. Vuelve a presionar **Registrar y Desbloquear Descargas** para actualizar tu archivo.*")
