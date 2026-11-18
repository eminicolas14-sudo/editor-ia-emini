
import os
import streamlit as st
from google import genai
from PIL import Image

# Configuración de la página
st.set_page_config(
    page_title="Redactor y Editor IA",
    page_icon="📝",
    layout="centered"
)

st.title("📝 Redactor y Editor Multimodal con Gemini")
st.write("Pega tu texto, o adjunta una imagen o PDF en la barra lateral para que la IA lo analice, corrija y mejore.")

# 1. Configurar la API Key desde los Secrets de Streamlit o variables de entorno
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ Falta configurar la GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

# Inicializar el cliente oficial de Google GenAI
client = genai.Client(api_key=api_key)

# Definir el modelo a utilizar
MODEL_NAME = "gemini-2.5-flash"

# 2. Inicializar la sesión de chat y el historial en st.session_state
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(model=MODEL_NAME)

if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Barra lateral (Sidebar) para cargar archivos y reiniciar
with st.sidebar:
    st.header("⚙️ Configuración y Archivos")
    
    # Cargador de archivos (imágenes y PDFs)
    uploaded_file = st.file_uploader(
        "Sube una imagen o un PDF:",
        type=["png", "jpg", "jpeg", "pdf"]
    )
    
    st.markdown("---")
    if st.button("🗑️ Limpiar Historial y Reiniciar"):
        st.session_state.messages = []
        st.session_state.chat_session = client.chats.create(model=MODEL_NAME)
        st.rerun()

# 4. Mostrar el historial de mensajes en la interfaz
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Entrada del usuario y lógica de envío
if prompt := st.chat_input("Escribe tu instrucción o pega tu texto aquí..."):
    
    # Mostrar mensaje del usuario en pantalla
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file is not None:
            if uploaded_file.type.startswith("image/"):
                st.image(uploaded_file, width=250, caption="Imagen adjunta")
            else:
                st.info(f"📄 PDF adjunto: {uploaded_file.name}")

    # 6. Preparar el contenido multimodal para Gemini
    content_to_send = [prompt]
    
    if uploaded_file is not None:
        if uploaded_file.type.startswith("image/"):
            # Procesar imagen con Pillow
            img = Image.open(uploaded_file)
            content_to_send.append(img)
        elif uploaded_file.type == "application/pdf":
            # Procesar PDF leyéndolo como bytes
            pdf_bytes = uploaded_file.getvalue()
            content_to_send.append({
                "mime_type": "application/pdf",
                "data": pdf_bytes
            })

    # 7. Enviar la consulta al modelo con manejo de errores (ej. Error 503)
    with st.chat_message("assistant"):
        with st.spinner("Analizando contenido..."):
            try:
                response = st.session_state.chat_session.send_message(content_to_send)
                st.markdown(response.text)
                # Guardar respuesta en el historial
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error("⚠️ El servidor de IA está experimentando alta demanda en este momento. Por favor, espera unos segundos y vuelve a intentarlo.")