# core/secciones/pareto_actual.py

import streamlit as st
from utils.visual_utils import style_dataframe
from utils.transformaciones import pareto_auto
from babel.dates import format_date

def mostrar_pareto_actual(actual_df):
    # Obtener fecha actual
    from datetime import datetime
    from babel.dates import format_date

    fecha_hoy = datetime.now()
    fecha_formateada = format_date(fecha_hoy, format='d', locale='es_ES')
    fecha_mes = format_date(fecha_hoy, format='MMMM', locale='es_ES')
    fecha_año = format_date(fecha_hoy, format='y', locale='es_ES')

    st.subheader(f":point_right: Análisis de Pareto de la Ejecución Actual al: {fecha_formateada} de {fecha_mes} de {fecha_año}")
    
    df = actual_df.copy()
    resultado = pareto_auto(df)
    styled_df = style_dataframe(resultado)
    styled_df = styled_df.hide(axis="index")
    html_table = styled_df.set_table_attributes('class="styled-table"').to_html()

    # Mostrar tabla centrada
    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    st.write(html_table, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)


