import streamlit as st
import requests

# --- GESTIÓN DE SECRETOS (MODO NUBE) ---
# En lugar de escribir la clave aquí, le decimos:
# "Busca la variable NOTION_TOKEN dentro de los secretos del sistema"

try:
    NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
    DB_NOTAS_ID = st.secrets["DB_NOTAS_ID"]
    DB_MENSAJES_ID = st.secrets["DB_MENSAJES_ID"]
except FileNotFoundError:
    st.error("⚠️ No se encontraron los secretos. Asegúrate de configurarlos en Streamlit Cloud.")
    st.stop()

# --- CONFIGURACIÓN GLOBAL ---
headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


st.set_page_config(page_title="Portal Académico", page_icon="🏫")
st.title("🏫 Portal de Estudiantes")

# --- LOGIN (Barra lateral) ---
with st.sidebar:
    st.header("🔐 Acceso")
    usuario_input = st.text_input("Estudiante:", placeholder="Ej: María García")
    clave_input = st.text_input("Contraseña:", type="password")
    boton_ingresar = st.button("Consultar")

# Inicializar estado de sesión
if "usuario_validado" not in st.session_state:
    st.session_state.usuario_validado = None

# Lógica del botón Ingresar
if boton_ingresar:
    url = f"https://api.notion.com/v1/databases/{DB_NOTAS_ID}/query"
    
    # Filtramos por nombre
    payload = {"filter": {"property": "Estudiante", "title": {"equals": usuario_input}}}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            if len(data["results"]) > 0:
                props = data["results"][0]["properties"]
                
                # Verificamos la clave
                try:
                    clave_lista = props["Clave"]["rich_text"]
                    clave_real = clave_lista[0]["text"]["content"] if clave_lista else ""
                    
                    if clave_input == clave_real:
                        st.session_state.usuario_validado = data["results"][0]
                        st.session_state.nombre_usuario = usuario_input
                        st.success("¡Bienvenido!") # Feedback visual
                    else:
                        st.error("Contraseña incorrecta")
                except KeyError:
                    st.error("Error: No encuentro la columna 'Clave' en Notion.")
            else:
                st.error("Usuario no encontrado")
        else:
            st.error("Error de conexión con Notion")
    except Exception as e:
        st.error(f"Error técnico: {e}")

# --- SI EL USUARIO YA ENTRÓ ---
if st.session_state.usuario_validado:
    
    # 1. MOSTRAR DATOS
    props = st.session_state.usuario_validado["properties"]
    try:
        resultado_lista = props["Resultado"]["rich_text"]
        resultado = resultado_lista[0]["text"]["content"] if resultado_lista else "Sin info"
        
        st.subheader(f"Hola, {st.session_state.nombre_usuario}")
        st.metric("Tu Estado Actual", resultado)
    except:
        st.warning("No se pudo leer el estado.")

    st.divider()

    # 2. ENVIAR MENSAJE
    st.subheader("📬 ¿Tienes dudas? Envía un mensaje al profesor")
    
    with st.form("form_mensaje"):
        texto_mensaje = st.text_area("Escribe tu consulta aquí:")
        enviar_btn = st.form_submit_button("Enviar Mensaje a Notion")
        
        if enviar_btn and texto_mensaje:
            url_crear = "https://api.notion.com/v1/pages"
            
            nuevo_mensaje = {
                "parent": {"database_id": DB_MENSAJES_ID},
                "properties": {
                    "Remitente": {
                        "title": [{"text": {"content": st.session_state.nombre_usuario}}]
                    },
                    "Mensaje": {
                        "rich_text": [{"text": {"content": texto_mensaje}}]
                    }
                }
            }
            
            # Ahora 'headers' ya está definido arriba y no fallará
            res_crear = requests.post(url_crear, headers=headers, json=nuevo_mensaje)
            
            if res_crear.status_code == 200:
                st.balloons()
                st.success("✅ ¡Mensaje enviado exitosamente!")
            else:
                st.error(f"Error al enviar: {res_crear.status_code} - {res_crear.text}")