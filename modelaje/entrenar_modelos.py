import pandas as pd
import numpy as np
import pickle
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from prophet import Prophet
import statsmodels.api as sm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELOS_DIR = os.path.join(BASE_DIR, "..", "modelos_guardados")
os.makedirs(MODELOS_DIR, exist_ok=True)

def temporalidad(df):
    data = df.copy()
    data["Calendar Year/Month - Key"] = data["Calendar Year/Month - Key"].astype(str)
    data[["mes", "anio"]] = data["Calendar Year/Month - Key"].str.split(".", expand=True)
    data["mes"] = data["mes"].str.zfill(2)
    data["fecha_formateada"] = data["mes"] + "." + data["anio"]
    data["fecha_formateada"] = pd.to_datetime(data["fecha_formateada"], format='%m.%Y')
    data_agrupada = pd.pivot_table(data, values="Cost (lc)", index="fecha_formateada", aggfunc="sum", sort=True).reset_index()
    data_agrupada["fecha_formateada"] = pd.to_datetime(data_agrupada["fecha_formateada"])
    data_agrupada.set_index("fecha_formateada", inplace=True)
    return data_agrupada.asfreq('MS')

def calcular_metricas(y_true_train, y_pred_train, y_true_test, y_pred_test):
    return {
        "MAE Train": mean_absolute_error(y_true_train, y_pred_train),
        "RMSE Train": np.sqrt(mean_squared_error(y_true_train, y_pred_train)),
        "MAPE Train": np.mean(np.abs((y_true_train - y_pred_train) / y_true_train)) * 100,
        "MAE Test": mean_absolute_error(y_true_test, y_pred_test),
        "RMSE Test": np.sqrt(mean_squared_error(y_true_test, y_pred_test)),
        "MAPE Test": np.mean(np.abs((y_true_test - y_pred_test) / y_true_test)) * 100,
    }

def entrenar_guardar_sarima(df, n_test=6):
    df = df.copy()
    train, test = df[:-n_test], df[-n_test:]
    fechas_test = test.index

    modelo = sm.tsa.statespace.SARIMAX(train['Cost (lc)'], order=(1, 1, 2), seasonal_order=(0, 1, 0, 12),
                                        enforce_stationarity=False, enforce_invertibility=False)
    resultado = modelo.fit()
    pred_train = resultado.fittedvalues
    pred_test = resultado.forecast(steps=n_test)
    metricas = pd.DataFrame([calcular_metricas(train['Cost (lc)'], pred_train, test['Cost (lc)'], pred_test)], index=["SARIMA"])

    with open(os.path.join(MODELOS_DIR, "sarima.pkl"), "wb") as f:
        pickle.dump({
            "modelo": resultado,
            "pred_train": pred_train,
            "pred_test": pred_test,
            "fechas_test": fechas_test,
            "metricas": metricas
        }, f)

    # PRONÓSTICO A FUTURO + INTERVALOS DE CONFIANZA
    full_model = sm.tsa.statespace.SARIMAX(df['Cost (lc)'], order=(1, 1, 2), seasonal_order=(0, 1, 0, 12)).fit()
    pred_full = full_model.get_forecast(steps=49)
    forecast_futuro = pred_full.predicted_mean
    conf_int = pred_full.conf_int()

    with open(os.path.join(MODELOS_DIR, "sarima_full.pkl"), "wb") as f:
        pickle.dump({
            "modelo": full_model,
            "forecast_futuro": forecast_futuro,
            "conf_int": conf_int
        }, f)

def entrenar_guardar_prophet(df, n_test=6):
    df_prophet = df.reset_index()[["fecha_formateada", "Cost (lc)"]].rename(columns={"fecha_formateada": "ds", "Cost (lc)": "y"})
    train, test = df_prophet[:-n_test], df_prophet[-n_test:]

    modelo = Prophet()
    modelo.fit(train)

    pred_train_df = modelo.predict(train)
    future_df = modelo.make_future_dataframe(periods=n_test, freq='MS')
    pred_test_df = modelo.predict(future_df).tail(n_test)

    y_pred_train = pred_train_df['yhat']
    y_pred_test = pred_test_df['yhat']
    fechas_test = pred_test_df['ds']

    metricas = pd.DataFrame([calcular_metricas(train['y'], y_pred_train, test['y'], y_pred_test)], index=["PROPHET"])

    with open(os.path.join(MODELOS_DIR, "prophet.pkl"), "wb") as f:
        pickle.dump({
            "modelo": modelo,
            "pred_train": y_pred_train,
            "pred_test": y_pred_test,
            "fechas_test": fechas_test,
            "metricas": metricas
        }, f)

    modelo_full = Prophet()
    modelo_full.fit(df_prophet)
    future = modelo_full.make_future_dataframe(periods=49, freq='MS')
    forecast_futuro = modelo_full.predict(future).tail(49)

    with open(os.path.join(MODELOS_DIR, "prophet_full.pkl"), "wb") as f:
        pickle.dump({"modelo": modelo_full, "forecast_futuro": forecast_futuro}, f)

def generar_features(df):
    df = df.copy().reset_index()
    df["mes"] = df["fecha_formateada"].dt.month
    df["año"] = df["fecha_formateada"].dt.year
    for i in range(1, 13):
        df[f"lag_{i}"] = df["Cost (lc)"].shift(i)
    df["media_3m"] = df["Cost (lc)"].rolling(window=3).mean().shift(1)
    df["var_pct_mensual"] = df["Cost (lc)"].pct_change().shift(1)
    return df.dropna().reset_index(drop=True)

def entrenar_guardar_modelo_arbol(df, modelo, nombre, n_test=6):
    df_feats = generar_features(df)
    X = df_feats.drop(columns=["fecha_formateada", "Cost (lc)"])
    y = df_feats["Cost (lc)"]
    columnas_entrenamiento = X.columns.tolist()

    X_train, X_test = X[:-n_test], X[-n_test:]
    y_train, y_test = y[:-n_test], y[-n_test:]
    fechas_test = df_feats.loc[y_test.index, "fecha_formateada"]

    modelo.fit(X_train, y_train)
    y_pred_train = modelo.predict(X_train)
    y_pred_test = modelo.predict(X_test)

    metricas = pd.DataFrame([calcular_metricas(y_train, y_pred_train, y_test, y_pred_test)], index=[nombre.upper()])

    with open(os.path.join(MODELOS_DIR, f"{nombre}.pkl"), "wb") as f:
        pickle.dump({
            "modelo": modelo,
            "pred_train": y_pred_train,
            "pred_test": y_pred_test,
            "fechas_test": fechas_test,
            "metricas": metricas
        }, f)

    df_future = df.copy()
    for i in range(1, 13):
        df_future[f"lag_{i}"] = df_future["Cost (lc)"].shift(i)
    df_future["media_3m"] = df_future["Cost (lc)"].rolling(window=3).mean().shift(1)
    df_future["var_pct_mensual"] = df_future["Cost (lc)"].pct_change().shift(1)
    df_future = df_future.dropna().reset_index()

    ultimos_datos = df_future.iloc[-1:].copy()
    predicciones = []
    fechas_pred = pd.date_range(start=pd.Timestamp("2025-06-01"), periods=49, freq="MS")

    for fecha in fechas_pred:
        nuevo_row = {
            "fecha_formateada": fecha,
            "Cost (lc)": predicciones[-1] if predicciones else ultimos_datos["Cost (lc)"].values[0],
            "mes": fecha.month,
            "año": fecha.year,
        }

        for i in range(1, 13):
            if i == 1:
                nuevo_row[f"lag_{i}"] = ultimos_datos["Cost (lc)"].values[0]
            else:
                nuevo_row[f"lag_{i}"] = ultimos_datos[f"lag_{i-1}"].values[0]

        nuevo_row["media_3m"] = np.mean([nuevo_row.get("lag_1", 0), nuevo_row.get("lag_2", 0), nuevo_row.get("lag_3", 0)])
        nuevo_row["var_pct_mensual"] = (nuevo_row["Cost (lc)"] - nuevo_row["lag_1"]) / nuevo_row["lag_1"] if nuevo_row["lag_1"] != 0 else 0

        ultimos_datos = pd.DataFrame([nuevo_row])
        for col in columnas_entrenamiento:
            if col not in ultimos_datos.columns:
                ultimos_datos[col] = np.nan
        ultimos_datos = ultimos_datos[columnas_entrenamiento]

        pred = modelo.predict(ultimos_datos)[0]
        predicciones.append(pred)
        nuevo_row["Cost (lc)"] = pred
        ultimos_datos["Cost (lc)"] = pred

    forecast_futuro = pd.Series(predicciones, index=fechas_pred)

    with open(os.path.join(MODELOS_DIR, f"{nombre}_full.pkl"), "wb") as f:
        pickle.dump({"modelo": modelo, "forecast_futuro": forecast_futuro}, f)

if __name__ == "__main__":
    df = pd.read_excel(r"C:\\Users\\CO1013629717\\Enel Spa\\Planificación, O&M, Reporting y Analytics - General\\Reporting\\ANALISIS_ESCENARIOS_PRESUPUESTALES\\ARCHIVOS FINALES\\historico_22_23.xlsx", sheet_name="series_t")
    data = temporalidad(df)
    entrenar_guardar_sarima(data)
    entrenar_guardar_prophet(data)
    entrenar_guardar_modelo_arbol(data, RandomForestRegressor(n_estimators=100, max_depth=None, random_state=42), "rf")
    entrenar_guardar_modelo_arbol(data, XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, subsample=0.8, colsample_bytree=0.8, reg_alpha=1, reg_lambda=1, random_state=42), "xgbreg")
    print("Modelos generados correctamente")
