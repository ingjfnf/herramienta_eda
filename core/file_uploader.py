import streamlit as st
import emoji

def mostrar_uploader():
    folder_emoji = emoji.emojize(':file_folder:')
    col1, col2 = st.columns(2)

    with col1:
        st.file_uploader(f"{folder_emoji} CARGUE DE ARCHIVO PRECLOSING", type=["csv", "txt", "xlsx", "xls"], key="preclosing_upload")
        st.file_uploader(f"{folder_emoji} CARGUE DE ARCHIVO SIMULACIÓN ESCENARIOS", type=["csv", "txt", "xlsx", "xls"], key="simulacion_upload")

    with col2:
        st.file_uploader(f"{folder_emoji} CARGUE DE ARCHIVO HISTÓRICO DE EJECUCIONES", type=["csv", "txt", "xlsx", "xls"], key="historico_upload")
        st.file_uploader(f"{folder_emoji} CARGUE DE ARCHIVO DE EJECUCIÓN ACTUAL", type=["csv", "txt", "xlsx", "xls"], key="traza_upload")

    for archivo in ['preclosing_upload', 'simulacion_upload', 'historico_upload', 'traza_upload']:
        if st.session_state.get(archivo) is not None:
            st.session_state[archivo.split("_")[0]] = st.session_state[archivo]

    if all(k in st.session_state for k in ['preclosing', 'simulacion', 'historico', 'traza']):
        col1, col2 = st.columns([4, 1])  # 👈 Centra texto y pone botón a la derecha
        with col1:
            st.markdown(
                '<p style="font-size:24px; color:green;">Todos los archivos han sido cargados correctamente.</p>',
                unsafe_allow_html=True
            )
        with col2:
            if st.button("Siguiente", key="next_button"):
                st.session_state.show_dataframe = True
                st.experimental_rerun()
    else:
        st.markdown(
            '<p style="font-size:24px; color:red;">DEBEN SER CARGADOS LOS 4 ARCHIVOS PARA EL TABLERO, DE LO CONTRARIO NO ES POSIBLE CONTINUAR.</p>',
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <style>
            .block-container {
                padding: 1rem 2rem;
                max-width: 100% !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
