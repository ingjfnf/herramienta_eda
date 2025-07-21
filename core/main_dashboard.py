import streamlit as st
import pandas as pd
from datetime import datetime
from babel.dates import format_date

from utils.transformaciones import arreglos
from utils.visual_utils import generate_scroller_html, maquillaje
from secciones.pareto_actual import mostrar_pareto_actual
from secciones.pareto_dinamico import mostrar_pareto_dinamico
from secciones.tendencias import grafica_ten
from secciones.outliers import mostrar_outliers
from secciones.distribucion import distribuir
from secciones.series import descomposicion
from secciones.series import tabla
from modelaje.grafica_modelos import total
from modelaje.pronosticos import pronosticador


logo_url = "https://raw.githubusercontent.com/ingjfnf/dash_presu/main/log_red.jpg"
def ejecutar_dashboard():
    # Cargar los archivos desde el session_state
    preclosing_df = pd.read_excel(st.session_state.preclosing)
    simulacion_df = pd.read_excel(st.session_state.simulacion)
    historico_df = pd.read_excel(st.session_state.historico, sheet_name="base_historica")
    actual = pd.read_excel(st.session_state.traza, sheet_name="SEGUIMIENTO")
    distribucion = pd.read_excel(st.session_state.traza, sheet_name="DISTRIBUCION")
    serial = pd.read_excel(st.session_state.historico, sheet_name="series_t")

    # Unir y transformar los datos
    df_final = arreglos(preclosing_df, simulacion_df, actual, historico_df)
    st.session_state.df_final = df_final

    # Fecha actual formateada
    fecha_hoy = datetime.now()
    fecha_formateada = format_date(fecha_hoy, format='d', locale='es_ES')
    fecha_mes = format_date(fecha_hoy, format='MMMM', locale='es_ES')
    fecha_año = format_date(fecha_hoy, format='y', locale='es_ES')


    scrolll=maquillaje(actual)
    html_content = generate_scroller_html(scrolll)
    st.markdown(html_content, unsafe_allow_html=True)   
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="width: 100%; display: flex; justify-content: center; align-items: center; gap: 2rem; margin-bottom: 2rem;">
    <img src="{logo_url}" alt="Logo de la empresa" style="width: 180px; height: auto;"/>
    <h1 style="margin: 0; font-size: 2.5rem;">E.D.A. PLANNING & REPORTING !!!</h1>
    <span style="font-size: 3rem;">📊</span>
    </div>
    <style>
        div.block-container {{
            padding-top: 3rem;
        }}
        .styled-table {{
            width: 70% !important;  /* Ajusta el ancho aquí */
            margin: auto;
        }}
        th {{
            background-color: #1F77B4 !important;
            color: white !important;
            text-align: center !important;
            font-size: 14px !important;  /* Reduce el tamaño de la letra del encabezado */
        }}
        td {{
            text-align: center !important;
            font-size: 13px !important;  /* Reduce el tamaño de la letra de las celdas */
            white-space: nowrap;
        }}
        .concepto-col {{
            font-weight: bold !important;
        }}
        hr.divider {{
            border: 0;
            height: 1px;
            background: #444;
            margin: 2rem 0;
        }}
        .custom-select-container {{
            display: flex; justify-content: center;
            font-size: 1.2rem;
        }}
        .custom-select {{
            width: 150px !important;
        }}
        .small-font {{
            font-size: 12px !important;  /* Reduce el tamaño de la letra */
        }}
    </style>
    
    """, unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)
    # TABLA PARETO 2
    mostrar_pareto_actual(actual)
    mostrar_pareto_dinamico(actual)
    grafica_ten(df_final)
    mostrar_outliers(df_final)
    distribuir(df_final,distribucion)
    descomposicion(serial)
    tabla()
    total(serial)
    pronosticador(serial)