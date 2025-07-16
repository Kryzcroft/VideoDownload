import streamlit as st
import os
import yt_dlp
import time
import re

# === CONFIGURACIÓN DE CARPETAS ===
CARPETAS = {
    'YouTube': 'downloads/youtube',
    'TikTok': 'downloads/tiktok',
    'Instagram': 'downloads/instagram',
    'Facebook': 'downloads/facebook',
    'X (Twitter)': 'downloads/x'
}

for carpeta in CARPETAS.values():
    os.makedirs(carpeta, exist_ok=True)

# === FUNCIONES DE VALIDACIÓN ===


def es_enlace_valido(url):
    patrones = [
        r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/",
        r"(https?://)?(www\.)?tiktok\.com/",
        r"(https?://)?(www\.)?instagram\.com/",
        r"(https?://)?(www\.)?facebook\.com/",
        r"(https?://)?(www\.)?x\.com/",
        r"(https?://)?(www\.)?twitter\.com/"
    ]
    return any(re.search(p, url) for p in patrones)


def es_playlist(url):
    patrones_playlist = [r"[?&]list=", r"/playlist"]
    return any(re.search(p, url) for p in patrones_playlist)


def detectar_plataforma(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "tiktok.com" in url:
        return "TikTok"
    elif "instagram.com" in url:
        return "Instagram"
    elif "facebook.com" in url:
        return "Facebook"
    elif "x.com" in url or "twitter.com" in url:
        return "X (Twitter)"
    return None

# === FUNCIÓN: OBTENER INFO DEL VIDEO ===


def obtener_info_video(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration")
            }
    except Exception:
        return None

# === FUNCIÓN: DESCARGAR VIDEO O AUDIO CON PROGRESO Y VERIFICACIÓN ===


def descargar_video(url, plataforma, modo, calidad, barra_progreso):
    carpeta_destino = CARPETAS[plataforma]

    # Intentar obtener info para verificar existencia previa
    try:
        info_pre = yt_dlp.YoutubeDL(
            {'quiet': True}).extract_info(url, download=False)
        titulo = info_pre.get("title", "video").strip().replace(
            "/", "_").replace("\\", "_")
        extension = "mp3" if modo == "Solo audio (.mp3)" else "mp4"
        nombre_final = f"{titulo}.{extension}"
        ruta_archivo = os.path.join(carpeta_destino, nombre_final)
        if os.path.exists(ruta_archivo):
            return False, "⚠️ El video ya fue descargado anteriormente."
    except Exception:
        pass

    # Barra de progreso
    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            descargado = d.get('downloaded_bytes', 0)
            if total:
                porcentaje = int(descargado / total * 100)
                barra_progreso.progress(min(porcentaje, 100))
        elif d['status'] == 'finished':
            barra_progreso.progress(100)
            time.sleep(0.3)
            barra_progreso.empty()

    opciones = {
        'progress_hooks': [hook],
        'outtmpl': os.path.join(carpeta_destino, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True
    }

    if modo == "Solo audio (.mp3)":
        opciones.update({
            'format': 'best',  # 👈 Cambiado de 'bestaudio' a 'best' para compatibilidad
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        opciones['format'] = 'best' if calidad == 'Alta' else 'worst[height<=360]'

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])
        return True, f"✅ Archivo guardado en: `{carpeta_destino}`"
    except Exception as e:
        return False, f"❌ Error al descargar: {e}"

# === FUNCIÓN: MOSTRAR DESCARGAS EXISTENTES ===


def mostrar_descargas(plataforma):
    carpeta = os.path.abspath(CARPETAS[plataforma])
    archivos = os.listdir(carpeta)
    archivos = [f for f in archivos if not f.startswith(".")]

    if archivos:
        st.markdown(f"### 📂 Archivos descargados en *{plataforma}*:")
        for archivo in sorted(archivos, reverse=True):
            ruta = os.path.join(carpeta, archivo)
            link = f"file://{ruta}"
            st.markdown(
                f'<a href="{link}" target="_blank">📄 {archivo}</a>',
                unsafe_allow_html=True
            )
    else:
        st.info("🕸️ Aún no hay descargas registradas en esta red social.")


# === INTERFAZ DE USUARIO ===
st.set_page_config(page_title="Kryzcroft Downloader", layout="centered")
st.title("📥 Descarga tus Videos o Extrae el Audio")
st.markdown(
    "Compatible con: **YouTube, TikTok, Instagram, Facebook y X (Twitter)**")

# LIMPIEZA CONTROLADA
if st.session_state.get("limpiar_input"):
    st.session_state.input_url = ""
    st.session_state.limpiar_input = False

st.text_input("🔗 Pega el enlace del video", key="input_url")
url = st.session_state.input_url.strip()

# === VALIDACIONES ===
if url and not es_enlace_valido(url):
    st.warning("⚠️ El enlace no pertenece a una red social válida.")
    st.stop()

if url and es_playlist(url):
    st.error("⛔ No se permiten descargas de playlists completas.")
    st.stop()

plataforma = detectar_plataforma(url)
if not plataforma:
    st.warning("❓ No se pudo detectar la plataforma del video.")
    st.stop()
else:
    st.markdown(f"🌐 Plataforma detectada: **{plataforma}**")

# === VISTA PREVIA DEL VIDEO ===
if url:
    info = obtener_info_video(url)
    if info:
        st.markdown("### 📺 Vista previa del video")
        st.markdown(
            f'<a href="{url}" target="_blank">'
            f'<img src="{info["thumbnail"]}" width="400"></a>',
            unsafe_allow_html=True
        )
        st.markdown(f"**🎬 Título:** {info['title']}")
        duracion = info.get("duration")
        if duracion:
            minutos = duracion // 60
            segundos = duracion % 60
            st.markdown(f"**⏱️ Duración:** {minutos} min {segundos} seg")
        else:
            st.markdown("**⏱️ Duración:** No disponible")

# === OPCIONES DE DESCARGA ===
modo = st.radio("🎵 ¿Qué deseas descargar?", ["Video", "Solo audio (.mp3)"])

if modo == "Video":
    calidad = st.selectbox("🎚️ Calidad del video", ["Alta", "Media (360p)"])
else:
    calidad = None

# === DESCARGA ===
if st.button("Descargar"):
    if not url:
        st.warning("⚠️ Debes ingresar un enlace.")
    else:
        barra = st.progress(0)
        exito, mensaje = descargar_video(url, plataforma, modo, calidad, barra)
        if exito:
            st.toast("✅ Descarga completada.", icon="📥")
            st.session_state.limpiar_input = True
        else:
            st.warning(mensaje)

# === HISTORIAL ===
mostrar_descargas(plataforma)
