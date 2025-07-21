import streamlit as st
import pandas as pd
from utils.visual_utils import style_dataframe_filtered
from utils.transformaciones import salida_out

def mostrar_outliers(df):
    st.subheader(":point_right: Análisis dinámico de Outliers por Escenarios Presupuestales")

    df_outlier = df.copy()
    df_out = salida_out(df_outlier)

    df_out['FECHA'] = pd.to_datetime(df_out['FECHA'])
    df_out['FECHA'] = df_out['FECHA'].dt.date

    df_out = df_out.reset_index(drop=True)
    df_out.columns = pd.Index([
        f"{col}_{i}" if list(df_out.columns).count(col) > 1 else col
        for i, col in enumerate(df_out.columns)
    ])

    col1, col2 = st.columns([1, 3])

    with col1:
        conceptos = df_out['CONCEPTO'].unique()
        selected_conceptos = st.multiselect('Selecciona los conceptos', conceptos)

    with col2:
        df_filtered = df_out[df_out['CONCEPTO'].isin(selected_conceptos)]
        styled_df_3 = style_dataframe_filtered(df_filtered)

        st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
        st.write(
            styled_df_3.set_table_attributes('class="styled-table"').hide(axis="index").to_html(),
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
