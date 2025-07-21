import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import pickle
import os
import numpy as np
import io
from utils.transformaciones import temporalidad

def unir_con_valores_reales(df_modelos, df_real):
    df_real = df_real.reset_index().rename(columns={"fecha_formateada": "Fecha", "Cost (lc)": "Costo real"})
    df_real = df_real[["Fecha", "Costo real"]]
    modelos = df_modelos["Modelo"].unique()
    df_real_expandido = pd.concat([df_real.assign(Modelo=modelo) for modelo in modelos], ignore_index=True)
    df_unido = pd.merge(df_modelos, df_real_expandido, on=["Fecha", "Modelo"], how="outer")
    return df_unido

def pronosticador(df):
    CARPETA_MODELOS = "modelos_guardados"

    archivos_modelos = {
        "SARIMA": "sarima_full.pkl",
        "PROPHET": "prophet_full.pkl",
        "RANDOM_FOREST": "rf_full.pkl",
        "XGBOOST_REG": "xgbreg_full.pkl"
    }

    df_modelos = []

    for nombre_modelo, archivo in archivos_modelos.items():
        ruta = os.path.join(CARPETA_MODELOS, archivo)
        with open(ruta, "rb") as f:
            contenido = pickle.load(f)

        if nombre_modelo == "PROPHET":
            forecast_df = contenido["forecast_futuro"]["ds yhat yhat_lower yhat_upper".split()].copy()
            forecast_df.columns = ["Fecha", "Pronostico", "Lower", "Upper"]

        elif nombre_modelo == "SARIMA":
            forecast = contenido["forecast_futuro"]
            fechas_futuras = pd.date_range(start=pd.Timestamp("2025-06-01"), periods=len(forecast), freq='MS')
            forecast_df = pd.DataFrame({
                "Fecha": fechas_futuras,
                "Pronostico": forecast,
                "Lower": np.nan,
                "Upper": np.nan
            })

        else:
            forecast = np.array(contenido["forecast_futuro"])
            fechas_futuras = pd.date_range(start=pd.Timestamp("2025-06-01"), periods=len(forecast), freq='MS')
            forecast_df = pd.DataFrame({
                "Fecha": fechas_futuras,
                "Pronostico": forecast,
                "Lower": np.nan,
                "Upper": np.nan
            })

        # FILTRAR RANGO DE FECHAS HASTA DIC 2028
        forecast_df = forecast_df[forecast_df['Fecha'] <= pd.Timestamp("2028-12-01")]

        forecast_df["Modelo"] = nombre_modelo
        df_modelos.append(forecast_df)

    df_pronosticos = pd.concat(df_modelos, ignore_index=True)
    df_pronosticos = df_pronosticos[["Modelo", "Fecha", "Pronostico", "Lower", "Upper"]]

    def obtener_factor(fecha):
        if fecha < pd.Timestamp('2024-07-15'):
            return 48 / 47
        elif fecha < pd.Timestamp('2025-07-15'):
            return 48 / 46
        elif fecha < pd.Timestamp('2026-07-15'):
            return 48 / 44
        else:
            return 48 / 42

    df_pronosticos["Factor_ley"] = df_pronosticos["Fecha"].apply(obtener_factor)
    df_pronosticos["Pronostico_ajustado"] = df_pronosticos["Pronostico"] * df_pronosticos["Factor_ley"]
    df_pronosticos["Lower_ajustada"] = df_pronosticos["Lower"] * df_pronosticos["Factor_ley"]
    df_pronosticos["Upper_ajustada"] = df_pronosticos["Upper"] * df_pronosticos["Factor_ley"]

    serie_real = temporalidad(df)
    df_unido = unir_con_valores_reales(df_pronosticos, serie_real)

    st.subheader("📊 Selecciona el modelo para graficar:")

    modelos_disponibles = df_unido["Modelo"].unique().tolist()
    modelo_seleccionado = st.radio(
        label="",
        options=modelos_disponibles,
        horizontal=True
    )

    df_modelo = df_unido[df_unido["Modelo"] == modelo_seleccionado].copy()
    df_modelo = df_modelo[df_modelo['Fecha'] <= pd.Timestamp("2028-12-01")]

    fig = go.Figure()

    if df_modelo["Costo real"].notna().any():
        fig.add_trace(go.Scatter(
            x=df_modelo["Fecha"],
            y=df_modelo["Costo real"] / 1e9,
            mode="lines",
            name="Valor real",
            line=dict(color="#0cc6f5"),
            hovertemplate="%{x|%b %Y}, %{y:.2f}<extra></extra>"
        ))

    fig.add_trace(go.Scatter(
        x=df_modelo["Fecha"],
        y=df_modelo["Pronostico"] / 1e9,
        mode="lines",
        name=f"Proyección original ({modelo_seleccionado})",
        line=dict(color="#0fe40f", dash="dot"),
        hovertemplate="%{x|%b %Y}, %{y:.2f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df_modelo["Fecha"],
        y=df_modelo["Pronostico_ajustado"] / 1e9,
        mode="lines",
        name="Proyección ajustada (Ley 2101)",
        line=dict(color="#FA390E"),
        hovertemplate="%{x|%b %Y}, %{y:.2f}<extra></extra>"
    ))

    if modelo_seleccionado != "SARIMA" and df_modelo["Lower_ajustada"].notna().any() and df_modelo["Upper_ajustada"].notna().any():
        fig.add_trace(go.Scatter(
            x=pd.concat([df_modelo["Fecha"], df_modelo["Fecha"][::-1]]),
            y=pd.concat([df_modelo["Upper_ajustada"] / 1e9, df_modelo["Lower_ajustada"][::-1] / 1e9]),
            fill="toself",
            fillcolor="rgba(255,0,0,0.2)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=True,
            name="IC 95% ajustada"
        ))

    fig.update_layout(
        title=f"Proyección de costos de horas extras en ENEL (2025–2028) – Modelo: {modelo_seleccionado}<br><sup>Con y sin ajuste por reducción de jornada laboral</sup>",
        xaxis_title="Fecha",
        yaxis_title="Costo mensual (Miles de Millones COP)",
        yaxis=dict(tickformat=".2f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # BOTÓN DE DESCARGA FILTRADO Y ACOTADO
    def descargar_excel(dataframe):
        if 'Fecha' in dataframe.columns:
            dataframe['Fecha'] = dataframe['Fecha'].dt.date
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Pronosticos Ajustados')
        return output.getvalue()

    columnas_comunes = ["Modelo", "Fecha", "Pronostico", "Factor_ley", "Pronostico_ajustado"]
    columnas_profeta = columnas_comunes + ["Lower", "Upper", "Lower_ajustada", "Upper_ajustada"]

    df_exportar = df_modelo[df_modelo['Fecha'].between("2025-06-01", "2028-12-01")]

    if modelo_seleccionado == "PROPHET":
        df_exportar = df_exportar[columnas_profeta]
    else:
        df_exportar = df_exportar[columnas_comunes]

    excel_data = descargar_excel(df_exportar)
    st.download_button(
        label="📥 Descargar Datos de Pronóstico",
        data=excel_data,
        file_name=f"pronosticos_{modelo_seleccionado.lower()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
