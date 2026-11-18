

from google import genai
from google.genai import types
import streamlit as st

# 1. Configuración de la página web
st.set_page_config(
    page_title="Editor Profesional con Gemini", page_icon="✍️", layout="centered"
)

# Estilos CSS personalizados para un diseño moderno e innovador
st.markdown(
    """
    <style>
    /* Estilo general del fondo y tipografía */
    .stApp {
        background-color: #0e1117;
        color: #f3f4f6;
    }
    
    /* Personalización de los contenedores de chat */
    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Botón de limpiar historial personalizado */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("✍️ Asistente Editor y Redactor Profesional")
st.markdown(
    "Tu espacio inteligente para perfeccionar textos, corregir estilo y"
    " analizar documentos."
)

# 2. Cargamos la API Key de forma segura desde secrets.toml
try:
  API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception as e:
  st.error(
      "⚠️ No se encontró la API Key en secrets.toml. Asegúrate de configurar"
      " el archivo correctamente."
  )
  st.stop()


# Inicializamos el cliente de forma segura con caché
@st.cache_resource
def get_gemini_client(api_key):
  return genai.Client(api_key=api_key)


client = get_gemini_client(API_KEY)

# 3. Configuramos la personalidad de la IA (Editor y Redactor Profesional)
configuracion = types.GenerateContentConfig(
    system_instruction=(
        "Eres un redactor y editor profesional. Ayudas a mejorar la claridad,"
        " el tono y la ortografía de cualquier texto que te compartan."
    ),
    temperature=0.7,
)

# 4. Barra lateral con el botón mejorado para limpiar el historial y reiniciar sesión
with st.sidebar:
  st.header("⚙️ Controles")
  if st.button("🗑️ Limpiar Historial y Reiniciar"):
    st.session_state.messages = []
    st.session_state.chat_session = client.chats.create(
        model="gemini-3.8-flash", config=configuracion
    )
    st.toast("¡Historial borrado con éxito!", icon="🧹")
    st.rerun()

  st.markdown("---")
  st.write("🔒 Aplicación protegida con `secrets.toml`")
  st.write("🤖 Modelo: `gemini-3.8-flash`")

# Creamos o recuperamos la sesión de chat con gemini-3.8-flash
if "chat_session" not in st.session_state:
  st.session_state.chat_session = client.chats.create(
      model="gemini-3.8-flash", config=configuracion
  )

if "messages" not in st.session_state:
  st.session_state.messages = []

# Mostramos el historial de mensajes en la interfaz
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])
    if "image_preview" in message and message["image_preview"]:
      st.image(message["image_preview"], width=200)

# 5. Widget para subir archivos (imágenes o PDFs)
uploaded_file = st.file_uploader(
    "Sube una imagen o documento PDF para analizar (opcional):",
    type=["png", "jpg", "jpeg", "pdf"],
)

# Vista previa si es una imagen
if uploaded_file is not None and uploaded_file.type.startswith("image/"):
  st.image(uploaded_file, caption="Imagen lista para enviar", width=250)

# 6. Entrada de texto para el usuario
if prompt := st.chat_input("Escribe tu texto o pregunta para editar..."):
  content_to_send = [prompt]
  image_for_history = None

  if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_mime = uploaded_file.type

    file_part = types.Part.from_bytes(data=file_bytes, mime_type=file_mime)
    content_to_send.append(file_part)

    if file_mime.startswith("image/"):
      image_for_history = uploaded_file

  msg_data = {"role": "user", "content": prompt}
  if image_for_history:
    msg_data["image_preview"] = image_for_history

  st.session_state.messages.append(msg_data)
  with st.chat_message("user"):
    st.markdown(prompt)
    if image_for_history:
      st.image(image_for_history, width=200)

  with st.chat_message("assistant"):
    with st.spinner("Analizando y editando contenido..."):
      try:
        response = st.session_state.chat_session.send_message(content_to_send)
        bot_reply = response.text
        st.markdown(bot_reply)
        st.session_state.messages.append(
            {"role": "assistant", "content": bot_reply}
        )
      except Exception as e:
        st.session_state.chat_session = client.chats.create(
            model="gemini-3.8-flash", config=configuracion
        )
        response = st.session_state.chat_session.send_message(content_to_send)
        bot_reply = response.text
        st.markdown(bot_reply)
        st.session_state.messages.append(
            {"role": "assistant", "content": bot_reply}
        )