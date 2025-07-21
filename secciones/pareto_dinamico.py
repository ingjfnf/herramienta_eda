import streamlit as st
from utils.visual_utils import style_dataframe
from utils.transformaciones import pareto_filtro


def mostrar_pareto_dinamico(df):

    st.subheader(":point_right: Análisis de Pareto Dinámico")
    st.markdown('<div class="custom-select-container">', unsafe_allow_html=True)
    st.markdown('<span style="font-size: 1.3rem;">Selecciona las fechas de corte</span>', unsafe_allow_html=True)
    selected_conceptos = st.multiselect(
        '',
        options=df['FECHA'].unique(),
        key="custom-select"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    
    filtered_df = df[df['FECHA'].isin(selected_conceptos)]

    grafica_2 = pareto_filtro(filtered_df)
    styled_df_2 = style_dataframe(grafica_2)

    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    st.write(styled_df_2.set_table_attributes('class="styled-table small-font"').hide(axis="index").to_html(), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)