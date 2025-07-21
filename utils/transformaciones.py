import streamlit as st
from prophet import Prophet
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import pandas as pd
import statsmodels.api as sm

def detectar_outliers(df, columna_valor):
    Q1 = df[columna_valor].quantile(0.25)
    Q3 = df[columna_valor].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df[columna_valor] < (Q1 - 1.5 * IQR)) | (df[columna_valor] > (Q3 + 1.5 * IQR))]
    return outliers

def arreglos(preclosing_df, simulacion_df, actual, historico_df):
    preclosing_df['PRESUPUESTO'] = preclosing_df['PRESUPUESTO'].fillna(0).round().astype('int64')
    preclosing_df = preclosing_df.rename(columns={"PRESUPUESTO": "VALOR"})
    preclosing_df["ANALISIS"] = "BUDGET"

    simulacion_df['VALOR'] = simulacion_df['VALOR'].fillna(0).round().astype('int64')
    simulacion_df["ANALISIS"] = "FORECAST"

    actual_tendencia = actual[["FECHA", "CONCEPTO", "EJECUCIÓN"]].rename(columns={"EJECUCIÓN": "VALOR"})
    actual_tendencia["ANALISIS"] = "ACTUAL"

    historico_df = historico_df.rename(columns={"EJECUCIÓN": "VALOR"})
    historico_df['FECHA'] = pd.to_datetime(historico_df['FECHA'], dayfirst=True)
    historico_df['AÑO'] = historico_df['FECHA'].dt.year
    dataframes_por_año = {año: historico_df[historico_df['AÑO'] == año].reset_index(drop=True) for año in historico_df['AÑO'].unique()}

    for año, df in dataframes_por_año.items():
        df["ANALISIS"] = f"Historico_{año}"
        df.drop(columns="AÑO", inplace=True)

    preclosing_df['FECHA'] = pd.to_datetime(preclosing_df['FECHA'], dayfirst=True)
    simulacion_df['FECHA'] = pd.to_datetime(simulacion_df['FECHA'], dayfirst=True)
    actual_tendencia['FECHA'] = pd.to_datetime(actual_tendencia['FECHA'], dayfirst=True)

    conjunto_total = pd.concat([preclosing_df, simulacion_df, actual_tendencia] + list(dataframes_por_año.values()))
    return conjunto_total




def pareto_auto(traza_df):
    traza_df['PRESUPUESTO'] = traza_df['PRESUPUESTO'].fillna(0)
    traza_df['PRESUPUESTO'] = traza_df['PRESUPUESTO'].round().astype('int64')
    traza_df['EJECUCIÓN'] = traza_df['EJECUCIÓN'].fillna(0)
    traza_df['EJECUCIÓN'] = traza_df['EJECUCIÓN'].round().astype('int64')
    traza_original = traza_df.copy()

    traza_original['DIFERENCIA'] = traza_original.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    traza_original['DIFERENCIA_ABS'] = traza_original['DIFERENCIA'].abs()

    traza_df = traza_df.groupby(["CONCEPTO"]).agg({"PRESUPUESTO": "sum", "EJECUCIÓN": "sum"}).reset_index()
    traza_df['DIFERENCIA'] = traza_df.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    traza_df['DIFERENCIA_ABS'] = traza_df['DIFERENCIA'].abs()
    traza_df_ordenado = traza_df.sort_values(by='DIFERENCIA_ABS', ascending=False)
    traza_df_ordenado = traza_df_ordenado[traza_df_ordenado["DIFERENCIA_ABS"] > 0]
    traza_df_ordenado = traza_df_ordenado.copy()
    traza_df_ordenado['SUMA_ACUMULADA'] = traza_df_ordenado['DIFERENCIA_ABS'].cumsum()
    traza_df_ordenado['PORCENTAJE_ACUMULADO'] = traza_df_ordenado['SUMA_ACUMULADA'] / traza_df_ordenado['DIFERENCIA_ABS'].sum() * 100

    pareto = traza_df_ordenado['PORCENTAJE_ACUMULADO'].searchsorted(80) + 1
    pareto_valores = traza_df_ordenado.iloc[:pareto]
    paretofinal = pareto_valores[['CONCEPTO', 'PRESUPUESTO', 'EJECUCIÓN', 'DIFERENCIA_ABS', 'PORCENTAJE_ACUMULADO']]
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "DIFERENCIA_ABSOLUTO"})

    traza_df_media = traza_original.groupby(["CONCEPTO"]).agg({"DIFERENCIA_ABS": "mean"}).reset_index()
    traza_df_max = traza_original.groupby(["CONCEPTO"]).agg({"DIFERENCIA_ABS": "max"}).reset_index()

    paretofinal = paretofinal.copy()
    paretofinal = pd.merge(paretofinal, traza_df_media, how="left", on="CONCEPTO")

    paretofinal['DIFERENCIA_ABS'] = paretofinal['DIFERENCIA_ABS'].fillna(0)
    paretofinal['DIFERENCIA_ABS'] = paretofinal['DIFERENCIA_ABS'].round().astype('int64')
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "MEDIA_DIFERENCIA_ABS"})

    paretofinal = pd.merge(paretofinal, traza_df_max, how="left", on="CONCEPTO")
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "MAX_DIFERENCIA_ABS"})

    paretofinal["LLAVE"] = paretofinal["CONCEPTO"] + paretofinal["MAX_DIFERENCIA_ABS"].astype(str)
    traza_original["llav"] = traza_original["CONCEPTO"] + traza_original["DIFERENCIA_ABS"].astype(str)
    paretofinal["FECHA_MAX_DIFF"] = pd.merge(paretofinal, traza_original, how="left", left_on="LLAVE", right_on="llav")["FECHA"]

    del paretofinal["LLAVE"]

    return paretofinal


def pareto_filtro(traza_df):
    traza_df['PRESUPUESTO'] = traza_df['PRESUPUESTO'].fillna(0)
    traza_df['PRESUPUESTO'] = traza_df['PRESUPUESTO'].round().astype('int64')
    traza_df['EJECUCIÓN'] = traza_df['EJECUCIÓN'].fillna(0)
    traza_df['EJECUCIÓN'] = traza_df['EJECUCIÓN'].round().astype('int64')
    traza_original = traza_df.copy()

    traza_original['DIFERENCIA'] = traza_original.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    traza_original['DIFERENCIA_ABS'] = traza_original['DIFERENCIA'].abs()

    traza_df = traza_df.groupby(["CONCEPTO"]).agg({"PRESUPUESTO": "sum", "EJECUCIÓN": "sum"}).reset_index()
    traza_df['DIFERENCIA'] = traza_df.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    traza_df['DIFERENCIA_ABS'] = traza_df['DIFERENCIA'].abs()
    traza_df_ordenado = traza_df.sort_values(by='DIFERENCIA_ABS', ascending=False)
    traza_df_ordenado = traza_df_ordenado[traza_df_ordenado["DIFERENCIA_ABS"] > 0]
    traza_df_ordenado = traza_df_ordenado.copy()
    traza_df_ordenado['SUMA_ACUMULADA'] = traza_df_ordenado['DIFERENCIA_ABS'].cumsum()
    traza_df_ordenado['PORCENTAJE_ACUMULADO'] = traza_df_ordenado['SUMA_ACUMULADA'] / traza_df_ordenado['DIFERENCIA_ABS'].sum() * 100

    pareto = traza_df_ordenado['PORCENTAJE_ACUMULADO'].searchsorted(80) + 1
    pareto_valores = traza_df_ordenado.iloc[:pareto]
    paretofinal = pareto_valores[['CONCEPTO', 'PRESUPUESTO', 'EJECUCIÓN', 'DIFERENCIA_ABS', 'PORCENTAJE_ACUMULADO']]
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "DIFERENCIA_ABSOLUTO"})

    traza_df_media = traza_original.groupby(["CONCEPTO"]).agg({"DIFERENCIA_ABS": "mean"}).reset_index()
    traza_df_max = traza_original.groupby(["CONCEPTO"]).agg({"DIFERENCIA_ABS": "max"}).reset_index()

    paretofinal = paretofinal.copy()
    paretofinal = pd.merge(paretofinal, traza_df_media, how="left", on="CONCEPTO")

    paretofinal['DIFERENCIA_ABS'] = paretofinal['DIFERENCIA_ABS'].fillna(0)
    paretofinal['DIFERENCIA_ABS'] = paretofinal['DIFERENCIA_ABS'].round().astype('int64')
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "MEDIA_DIFERENCIA_ABS"})

    paretofinal = pd.merge(paretofinal, traza_df_max, how="left", on="CONCEPTO")
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "MAX_DIFERENCIA_ABS"})

    paretofinal["LLAVE"] = paretofinal["CONCEPTO"] + paretofinal["MAX_DIFERENCIA_ABS"].astype(str)
    traza_original["llav"] = traza_original["CONCEPTO"] + traza_original["DIFERENCIA_ABS"].astype(str)
    paretofinal["FECHA_MAX_DIFF"] = pd.merge(paretofinal, traza_original, how="left", left_on="LLAVE", right_on="llav")["FECHA"]

    del paretofinal["LLAVE"]

    return paretofinal

def salida_out(df):  
    outliers_df = pd.DataFrame()
    for concepto in df['CONCEPTO'].unique():
        for analisis in df['ANALISIS'].unique():
            subset = df[(df['CONCEPTO'] == concepto) & (df['ANALISIS'] == analisis)]
            if not subset.empty:
                outliers = detectar_outliers(subset, 'VALOR')
                outliers_df = pd.concat([outliers_df, outliers])
    return outliers_df


def distributivo(df,modelo):
    distri = df[(df["ANALISIS"] == "Historico_2022") | (df["ANALISIS"] == "Historico_2023") | (df["ANALISIS"] == "ACTUAL")]
    distri = distri.copy()
    distri["absoluto"] = distri["VALOR"].abs()
    actual = distri[distri["ANALISIS"] == "ACTUAL"]
    promedio_por_concepto = actual.groupby('CONCEPTO')['absoluto'].mean()
    promedio_por_concepto_anual = promedio_por_concepto * 12
    actual = actual.copy()
    actual['TOTAL CONCEPTO PROMEDIO'] = actual['CONCEPTO'].map(promedio_por_concepto_anual)
    actual['TOTAL CONCEPTO PROMEDIO'] = actual['TOTAL CONCEPTO PROMEDIO'].astype("int64")
    actual['PESO PONDERADO PROMEDIO'] = actual.apply(
        lambda x: round((x["absoluto"] / x['TOTAL CONCEPTO PROMEDIO']) * 100, 2) if x['TOTAL CONCEPTO PROMEDIO'] != 0 else 0,
        axis=1
    )
    historia_22 = distri[distri["ANALISIS"] == "Historico_2022"]
    suma_por_concepto = historia_22.groupby('CONCEPTO')['absoluto'].sum()
    historia_22 = historia_22.copy()
    historia_22['TOTAL CONCEPTO'] = historia_22['CONCEPTO'].map(suma_por_concepto)
    historia_22['TOTAL CONCEPTO'] = historia_22['TOTAL CONCEPTO'].astype("int64")
    historia_22['PESO PONDERADO PROMEDIO'] = historia_22.apply(
        lambda x: round((x["absoluto"] / x['TOTAL CONCEPTO']) * 100, 2) if x['TOTAL CONCEPTO'] != 0 else 0,
        axis=1
    )
    historia_23 = distri[distri["ANALISIS"] == "Historico_2023"]
    suma_por_concepto = historia_23.groupby('CONCEPTO')['absoluto'].sum()
    historia_23 = historia_23.copy()
    historia_23['TOTAL CONCEPTO'] = historia_23['CONCEPTO'].map(suma_por_concepto)
    historia_23['TOTAL CONCEPTO'] = historia_23['TOTAL CONCEPTO'].astype("int64")
    historia_23['PESO PONDERADO PROMEDIO'] = historia_23.apply(
        lambda x: round((x["absoluto"] / x['TOTAL CONCEPTO']) * 100, 2) if x['TOTAL CONCEPTO'] != 0 else 0,
        axis=1
    )
    Distribucion_23 = historia_23[["FECHA", "CONCEPTO", "PESO PONDERADO PROMEDIO", "ANALISIS"]]
    Distribucion_22 = historia_22[["FECHA", "CONCEPTO", "PESO PONDERADO PROMEDIO", "ANALISIS"]]
    Distribucion_actual = actual[["FECHA", "CONCEPTO", "PESO PONDERADO PROMEDIO", "ANALISIS"]]
    salida_total = pd.concat([Distribucion_23, Distribucion_22, Distribucion_actual], ignore_index=True)

    df_transpuesto = modelo.melt(id_vars=['CONCEPTO COSTO', 'CONCEPTO COSTO HOMOLOGADO'], var_name='mensualidad', value_name='Valor')
    del df_transpuesto["CONCEPTO COSTO"]
    def convertir_fecha(fecha):
        meses = {
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 
            'may': '05', 'jun': '06', 'jul': '07', 'ago': '08', 
            'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
        }
        mes, año = fecha.split('-')
        año = '20' + año  
        mes = meses[mes.lower()]  
        return f'{año}-{mes}-01'

    df_transpuesto['FECHA'] = df_transpuesto['mensualidad'].apply(convertir_fecha)
    del df_transpuesto['mensualidad']
    df_transpuesto = df_transpuesto.rename(columns={"CONCEPTO COSTO HOMOLOGADO": "CONCEPTO", "Valor": "PESO"})
    df_transpuesto = df_transpuesto[["FECHA", "CONCEPTO", "PESO"]]
    df_transpuesto["PESO PONDERADO PROMEDIO"] = df_transpuesto.apply(lambda x: round(x["PESO"] * 100, 2), axis=1)
    del df_transpuesto["PESO"]
    df_transpuesto["ANALISIS"] = "MODELO"
    df_transpuesto['FECHA'] = pd.to_datetime(df_transpuesto['FECHA'])
    distribucion_final = pd.concat([salida_total, df_transpuesto], ignore_index=True)

    return distribucion_final

def temporalidad(df):
    data=df.copy()
    data["Calendar Year/Month - Key"] = data["Calendar Year/Month - Key"].astype(str)
    data[["mes", "anio"]] = data["Calendar Year/Month - Key"].str.split(".", expand=True)
    data["mes"] = data["mes"].str.zfill(2)
    data["fecha_formateada"] = data["mes"] + "." + data["anio"]
    data["fecha_formateada"] = pd.to_datetime(data["fecha_formateada"], format='%m.%Y')
    data_agrupada=pd.pivot_table(data,values="Cost (lc)",index="fecha_formateada",aggfunc="sum",sort=True).reset_index()
    data_agrupada["fecha_formateada"] = pd.to_datetime(data_agrupada["fecha_formateada"])
    data_agrupada.set_index("fecha_formateada", inplace=True)
    data_agrupada_ok = data_agrupada.asfreq('MS') 
    return data_agrupada_ok




    