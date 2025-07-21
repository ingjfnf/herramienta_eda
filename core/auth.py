import streamlit as st

def credenciales(username, password):
    try:
        users = st.secrets["users"]
        return username in users and users[username] == password
    except Exception as e:
        st.error("No se pudieron cargar las credenciales.")
        return False

def login_interface():
    st.markdown(
        """
        <style>
        .customizado-container {
            max-width: 30px;
            margin: auto;
            padding: 10px;
        }
        .stTextInput {
            width: 50%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="customizado-container">', unsafe_allow_html=True)
    username = st.text_input("Nombre de usuario")
    password = st.text_input("Contraseña", type="password")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Iniciar sesión"):
        if credenciales(username, password):
            st.session_state['authenticated'] = True
            st.experimental_rerun()
        else:
            st.error("Nombre de usuario o contraseña incorrectos")
