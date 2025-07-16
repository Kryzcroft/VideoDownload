import streamlit as st
import yt_dlp
import time
import re
from io import BytesIO

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


def descargar_y_retornar(url, modo, calidad, barra_progreso):
    buffer = BytesIO()

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
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [hook],
        'noplaylist': True,
        'outtmpl': '-',  # stdout
    }

    if modo == "Solo audio (.mp3)":
        opciones.update({
            'format': 'best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        opciones['format'] = 'best' if calidad == 'Alta' else 'worst[height<=360]'

    opciones['outtmpl'] = '%(title)s.%(ext)s'

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'video')
            extension = 'mp3' if modo == "Solo audio (.mp3)" else 'mp4'
            nombre_archivo = f"{titulo}.{extension}"

            ruta_archivo = f"{nombre_archivo}"
            with open(ruta_archivo, "rb") as f:
                buffer.write(f.read())
            buffer.seek(0)
            return buffer, nombre_archivo, None
    except Exception as e:
        return None, None, str(e)


# === INTERFAZ DE USUARIO ===
st.set_page_config(page_title="Kryzcroft Downloader", layout="centered")
st.title("📥 Hola! aqui podras descargar tus videos favoritos o el audio.")
st.markdown(
    "Compatible con: **YouTube, TikTok, Instagram, Facebook y X (Twitter)**")

if st.session_state.get("limpiar_input"):
    st.session_state.input_url = ""
    st.session_state.limpiar_input = False

st.text_input("🔗 Pega el enlace del video", key="input_url")
url = st.session_state.input_url.strip()

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

modo = st.radio("🎵 ¿Qué deseas descargar?", ["Video", "Solo audio (.mp3)"])

if modo == "Video":
    calidad = st.selectbox("🎚️ Calidad del video", ["Alta", "Media (360p)"])
else:
    calidad = None

if st.button("Descargar"):
    if not url:
        st.warning("⚠️ Debes ingresar un enlace.")
    else:
        barra = st.progress(0)
        buffer, nombre_archivo, error = descargar_y_retornar(
            url, modo, calidad, barra)
        if buffer:
            st.toast("✅ Descarga completada", icon="📥")
            st.session_state.limpiar_input = True
            st.download_button(
                label=f"📄 Descargar {nombre_archivo}",
                data=buffer,
                file_name=nombre_archivo,
                mime="application/octet-stream"
            )
        else:
            st.error(f"❌ Error: {error}")
