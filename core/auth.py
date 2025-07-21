import streamlit as st

def credenciales(username, password):
    users = {
        "CO1088260844": "MB0844",
        "CO1088282417": "DP2417",
        "CO1013629717": "JN9717"
    }
    return username in users and users[username] == password

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
