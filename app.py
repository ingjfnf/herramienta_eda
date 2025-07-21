import streamlit as st
st.set_page_config(page_title="PLANNING & REPORTING", page_icon="📊", layout="wide")


# 🔁 Importación de módulos organizados
from core.auth import login_interface
from core.layout import mostrar_encabezado
from core.file_uploader import mostrar_uploader
from core.main_dashboard import ejecutar_dashboard

# 🔒 Estado de control inicial
if 'show_dataframe' not in st.session_state:
    st.session_state.show_dataframe = False

# 👇 CONTROL DE FLUJO
if not st.session_state.get('authenticated', False):
    mostrar_encabezado()         # Solo antes de autenticarse
    login_interface()
else:
    if not st.session_state.get('show_dataframe', False):
        mostrar_encabezado()     # Solo en pantalla de carga de archivos
        st.markdown("<br><br>", unsafe_allow_html=True)
        mostrar_uploader()
    else:
        ejecutar_dashboard()     # Aquí NO debe mostrarse encabezado otra vez
