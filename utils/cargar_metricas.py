import os
import pickle
import pandas as pd

# ✅ Ruta corregida a modelos_guardados (misma carpeta que app.py)
CARPETA_MODELOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modelos_guardados"))

def cargar_metricas_modelos():
    nombres_modelos = {
        "sarima.pkl": "SARIMA",
        "prophet.pkl": "PROPHET",
        "rf.pkl": "RANDOM_FOREST",
        "xgbreg.pkl": "XGBOOST_REG"
    }

    metricas_dict = {}

    for archivo, nombre_legible in nombres_modelos.items():
        ruta = os.path.join(CARPETA_MODELOS, archivo)
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                contenido = pickle.load(f)
                metricas_dict[nombre_legible] = contenido["metricas"].iloc[0].to_dict()
        else:
            print(f"⚠️ No se encontró el archivo: {archivo}")

    df_metricas = pd.DataFrame(metricas_dict).T.round(2)
    df_metricas.index.name = "MODELO"
    return df_metricas
