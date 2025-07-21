import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.transformaciones import temporalidad
import os
import pickle
import numpy as np

# ---------- Cargar la base ----------
def total(df_base):
    df_serie = temporalidad(df_base)
    df_serie = df_serie.reset_index().rename(columns={"fecha_formateada": "Fecha", "Cost (lc)": "Valor real"})
    y_test = df_serie.tail(6).copy()
    y_test.set_index("Fecha", inplace=True)

    # ---------- Cargar predicciones de los modelos ----------
    CARPETA_MODELOS = "modelos_guardados"
    NOMBRE_ARCHIVOS = {
        "SARIMA": "sarima.pkl",
        "PROPHET": "prophet.pkl",
        "XGBOOST_REG": "xgbreg.pkl",
        "RANDOM_FOREST": "rf.pkl"
    }

    # Construir el DataFrame completo con valores reales
    df_comparativo = pd.DataFrame({
        "Fecha": df_serie["Fecha"],
        "Valor real": df_serie["Valor real"]
    })

    for nombre, archivo in NOMBRE_ARCHIVOS.items():
        ruta = os.path.join(CARPETA_MODELOS, archivo)
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                contenido = pickle.load(f)
                pred = contenido["pred_test"]
                if isinstance(pred, pd.DataFrame):
                    pred = pred.iloc[:, 0]
                elif isinstance(pred, (np.ndarray, list)):
                    pred = pd.Series(pred)
                pred.index = y_test.index
                serie_pred = pd.Series([None] * (len(df_serie) - 6) + list(pred.values), index=df_serie.index)
                df_comparativo[nombre] = serie_pred
        else:
            st.warning(f"No se encontró el archivo: {archivo}")

    # ---------- Selección de modelos con CHECKBOX ----------
    st.markdown("### 📉 Selecciona los modelos para graficar:")
    col1, col2, col3, col4 = st.columns(4)
    modelos_seleccionados = []

    if col1.checkbox("SARIMA"):
        modelos_seleccionados.append("SARIMA")
    if col2.checkbox("PROPHET"):
        modelos_seleccionados.append("PROPHET")
    if col3.checkbox("XGBOOST_REG"):
        modelos_seleccionados.append("XGBOOST_REG")
    if col4.checkbox("RANDOM_FOREST"):
        modelos_seleccionados.append("RANDOM_FOREST")

    # ---------- Graficar ----------
    def graficar_modelos(df_comparativo, modelos_seleccionados):
        fig = go.Figure()
        df_comparativo_scaled = df_comparativo.copy()
        df_comparativo_scaled["Valor real"] = df_comparativo_scaled["Valor real"] / 1e9

        for modelo in modelos_seleccionados:
            if modelo in df_comparativo_scaled.columns:
                df_comparativo_scaled[modelo] = df_comparativo_scaled[modelo] / 1e9

        fig.add_trace(go.Scatter(
            x=df_comparativo_scaled["Fecha"],
            y=df_comparativo_scaled["Valor real"],
            mode="lines+markers",
            name="Valor real",
            line=dict(color="#0cc6f5", width=3),
            opacity=1
        ))

        colores = {
            "SARIMA": "#FA390E",
            "PROPHET": "#f30ae0",
            "XGBOOST_REG": "#E48007",
            "RANDOM_FOREST": "#0fe40f"
        }

        for modelo in modelos_seleccionados:
            if modelo in df_comparativo_scaled.columns:
                fig.add_trace(go.Scatter(
                    x=df_comparativo_scaled["Fecha"],
                    y=df_comparativo_scaled[modelo],
                    mode="lines+markers",
                    name=modelo,
                    line=dict(color=colores.get(modelo, "gray"), dash="dash", width=2),
                    opacity=1
                ))

        fig.update_layout(
            width=1250,
            height=700,
            title=dict(
                text="Predicción de Costos en Conjunto de Prueba",
                x=0.5,
                xanchor='center',
                font=dict(size=22)
            ),
            xaxis_title="Fecha",
            yaxis_title="Costo mensual (Miles de Millones COP)",
            legend_title="Modelo",
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                tickformat=",.2f"
            )
        )

        return fig

    # ---------- Mostrar gráfico ----------
    if modelos_seleccionados:
        fig = graficar_modelos(df_comparativo, modelos_seleccionados)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Selecciona al menos un modelo para comparar contra el valor real.")

    with st.expander("Despliega para ver el análisis detallado", expanded=False):
        st.markdown("""
        ### 🧠 Análisis de la Predicción de Costos en Conjunto de Prueba

        La gráfica compara la serie real de costos mensuales con las predicciones generadas por cuatro modelos de machine learning: SARIMA, Prophet, XGBoost y Random Forest. Se observa cómo cada modelo intenta capturar el comportamiento del costo en los últimos seis meses, permitiendo evaluar visualmente el grado de ajuste y precisión de cada uno.

        - **SARIMA** presenta un patrón suavizado, pero con mayor subestimación en los meses con repunte. Su estructura estadística tiende a generar valores más conservadores, lo cual puede ser útil en contextos donde se prefieren estimaciones prudentes.
        - **Prophet**, en cambio, logra capturar con mayor amplitud los picos y caídas, lo que sugiere que es sensible a variaciones recientes en la tendencia. Sin embargo, podría ser más volátil en contextos con ruido.
        - **XGBoost Regresor** muestra una predicción intermedia, adaptándose de forma razonable al comportamiento real pero sin sobresalir en los extremos.
        - **Random Forest** también mantiene una trayectoria estable, aunque tiende a suavizar los valores, lo cual podría limitar su capacidad de anticipar cambios abruptos.

        En conjunto, esta visualización permite al usuario contrastar la precisión y robustez de los modelos frente a los datos reales, facilitando la toma de decisiones sobre cuál modelo utilizar para futuras proyecciones o escenarios presupuestales.
        """)
