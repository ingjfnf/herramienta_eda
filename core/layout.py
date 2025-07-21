import streamlit as st

def mostrar_encabezado():
    logo_url = "https://raw.githubusercontent.com/ingjfnf/dash_presu/main/log_red.jpg"

    st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 1.5rem;">
            <img src="{logo_url}" alt="Logo de la empresa" style="width: 150px; height: auto;"/>
            <h1 style="margin: 0; white-space: nowrap;">E.D.A. PLANNING & REPORTING !!!</h1>
            <span style="font-size: 3rem;">📊</span>
        </div>

        <style>
            div.block-container {{
                padding-top: 3rem;
            }}
            .styled-table {{
                width: 70% !important;
                margin: auto;
            }}
            th {{
                background-color: #1F77B4 !important;
                color: white !important;
                text-align: center !important;
                font-size: 14px !important;
            }}
            td {{
                text-align: center !important;
                font-size: 13px !important;
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
                font-size: 12px !important;
            }}
        </style>
    """, unsafe_allow_html=True)
