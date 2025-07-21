import pandas as  pd
import numpy as np
def generate_scroller_html(df):
    items = []
    for index, row in df.iterrows():
        icon = "&#9660;" if row['VARIACION'] < 0 else "&#9650;"
        color = "red" if row['VARIACION'] < 0 else "green"
        items.append(
            f"<span>{row['CONCEPTO']} <span style='color:{color};'>{icon}</span> {row['VARIACION']}% &nbsp;&nbsp;&nbsp;&nbsp;</span>"
        )
    items_html = ''.join(items)
    items_html_double = items_html + items_html  # Para loop infinito

    html_content = f"""
    <div id="scroller" style="white-space: nowrap; overflow: hidden; width: 92.5%; height: 37px; position: fixed;
    left: 50%; transform: translateX(-50%);
    background-color: white; color: black; z-index: 2000; display: flex; align-items: center;">
        <div id="scrolling-text" style="display: inline-block;">
            {items_html_double}
        </div>
    </div>
    <hr class="scroller-divider">
    <style>
    #scroller {{
        overflow: hidden;
        position: relative;
        margin-bottom: 0px;
        display: flex;
        align-items: center;
    }}
    #scrolling-text {{
        display: inline-block;
        white-space: nowrap;
        position: relative;
        animation: scroll 110s linear infinite;
        font-weight: bold;
        padding: 0 10px;
    }}
    @keyframes scroll {{
        0% {{ transform: translateX(0); }}
        100% {{ transform: translateX(-50%); }}
    }}
    .scroller-divider {{
        border: 0;
        height: 1px;
        background: #444;
        margin-top: 0;
        margin-bottom: 2rem;
    }}
    #scroller:hover #scrolling-text {{
        animation-play-state: paused;
    }}
    </style>
    """
    return html_content



def maquillaje(df):
    df['PRESUPUESTO'] = df['PRESUPUESTO'].fillna(0).round().astype('int64')
    df['EJECUCIÓN'] = df['EJECUCIÓN'].fillna(0).round().astype('int64')
    df = df.groupby(["CONCEPTO"]).agg({"PRESUPUESTO": "sum", "EJECUCIÓN": "sum"}).reset_index()
    df['DIFERENCIA'] = df.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    df = df[df['PRESUPUESTO'] > 0]
    df['VARIACION'] = df.apply(lambda x: round((((x["DIFERENCIA"] / x['PRESUPUESTO']) * 100) * -1), 2), axis=1)
    return df

def format_currency_with_semaforo(value):
    
    if isinstance(value, (int, float)):
        formatted_value = f"{abs(value):,.0f}".replace(",", ".")
        if value < 0:
            return f"- $ {formatted_value} 🟢"  
        elif value > 0:
            return f"$ {formatted_value} 🔴"   
        else:
            return f"$ {formatted_value} 🟡"   
    return value 

def format_percentage(value):
    return f"{value:.2f}%"

def format_currency(value):
    if isinstance(value, (int, float)):
 
        if value < 0:
            return f"- $ {abs(value):,.0f}".replace(",", ".")
        else:
            return f"$ {value:,.0f}".replace(",", ".")
    return value

def style_dataframe(df):
    df_formatted = df.copy()
    for col in df.columns:
        if col not in ['PORCENTAJE_ACUMULADO', 'FECHA_MAX_DIFF']:
            df_formatted[col] = df_formatted[col].apply(format_currency)
        elif col == 'PORCENTAJE_ACUMULADO':
            df_formatted[col] = df_formatted[col].apply(format_percentage)
    
    styled_df = df_formatted.style.set_table_styles(
        [
            {
                'selector': 'th',
                'props': [('background-color', '#1F77B4'), ('color', 'white'), ('font-size', "14px"), ('text-align', 'center')]
            },
            {
                'selector': 'td',
                'props': [('font-size', "12px"), ('text-align', 'center'), ('white-space', 'nowrap')]
            },
            {
                'selector': 'td.col0',
                'props': [('font-weight', 'bold')]
            }
        ]
    ).set_properties(**{'border': '1px solid white','width': '70px'})
    
    return styled_df


def style_tabla_filtro(df,nombre):
    df_formatted = df.copy()

    df_formatted[nombre] = df[nombre].apply(format_currency_with_semaforo)

    for col in df.columns:
        if col != 'CONCEPTO' or col != 'MES' or col != nombre:
            df_formatted[col] = df_formatted[col].apply(format_currency)

    styled_df = df_formatted.style.set_table_styles(
        [
            {
                'selector': 'th',
                'props': [('background-color', '#1F77B4'), 
                          ('color', 'white'), 
                          ('font-size', '14px'), 
                          ('text-align', 'center'),
                          ('white-space', 'nowrap')]  
            },
            {
                'selector': 'td',
                'props': [('font-size', '12px'), ('text-align', 'center'), ('white-space', 'nowrap')]
            },
            {
                'selector': 'td.col0',
                'props': [('font-weight', 'bold')]
            }
        ]
    ).set_properties(**{'border': '1px solid white', 'width': '70px'})
    
    return styled_df

def style_dataframe_filtered(df):
    df_formatted = df.copy()
    for col in df.columns:
        if col == 'VALOR':
            df_formatted[col] = df_formatted[col].apply(format_currency)
    
    styled_df = df_formatted.style.set_table_styles(
        [
            {
                'selector': 'th',
                'props': [('background-color', '#1F77B4'), ('color', 'white'), ('font-size', '14px'), ('text-align', 'center')]
            },
            {
                'selector': 'td',
                'props': [('font-size', '12px'), ('text-align', 'center'), ('white-space', 'nowrap')]
            },
            {
                'selector': 'td.col0',
                'props': [('font-weight', 'bold')]
            }
        ]
    ).set_properties(**{'border': '1px solid white', 'width': '70px'})
    
    return styled_df


def style_tabla_distribucion(df):
    df_formatted = df.copy()
    
    def format_percentage(value):
        if pd.isnull(value):
            return 'None'
        return f'{value:.2f} %'

    for col in df.columns:
        if col not in ['CONCEPTO', 'ANALISIS']:
            df_formatted[col] = df_formatted[col].apply(format_percentage)
    
    styled_df = df_formatted.style.set_table_styles(
        [
            {
                'selector': 'th',
                'props': [('background-color', '#1F77B4'), ('color', 'white'), ('font-size', '14px'), ('text-align', 'center')]
            },
            {
                'selector': 'td',
                'props': [('font-size', '12px'), ('text-align', 'center'), ('white-space', 'nowrap')]
            },
            {
                'selector': 'td.col0',
                'props': [('font-weight', 'bold')]
            }
        ]
    ).set_properties(**{'border': '1px solid white', 'width': '70px'})
    
    return styled_df


def style_modelos(df):
    df_formatted = df.copy()

    # 🧹 Aseguramos que todo esté en formato numérico para cálculo
    for col in df.columns:
        if col != "MODELO":
            df_formatted[col] = pd.to_numeric(df_formatted[col], errors="coerce")

    # 📊 Calculamos diferencias absolutas entre métricas de train y test
    df_formatted["DIF_MAE"] = abs(df_formatted["MAE Test"] - df_formatted["MAE Train"])
    df_formatted["DIF_RMSE"] = abs(df_formatted["RMSE Test"] - df_formatted["RMSE Train"])
    df_formatted["DIF_MAPE"] = abs(df_formatted["MAPE Test"] - df_formatted["MAPE Train"])
    df_formatted["DIF_PROMEDIO"] = df_formatted[["DIF_MAE", "DIF_RMSE", "DIF_MAPE"]].mean(axis=1)

    # 📌 Ordenamos del mejor al peor modelo (menor diferencia promedio)
    df_ordenado = df_formatted.sort_values("DIF_PROMEDIO").drop(columns=["DIF_MAE", "DIF_RMSE", "DIF_MAPE", "DIF_PROMEDIO"])

    # 🚦 Agregamos semáforos
    semaforos = ['🟢', '🟡', '🟠', '🔴']
    df_ordenado["MODELO"] = [f"{semaforos[i]} {modelo}" for i, modelo in enumerate(df_ordenado["MODELO"])]

    # 💄 Aplicamos formato visual
    for col in df_ordenado.columns:
        if "MAPE" in col:
            df_ordenado[col] = df_ordenado[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "")
        elif col != "MODELO":
            df_ordenado[col] = df_ordenado[col].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "")

    # 🎨 Aplicamos estilo como en tu tablero
    styled_df = df_ordenado.style.set_table_styles(
        [
            {
                'selector': 'th',
                'props': [
                    ('background-color', '#1F77B4'),
                    ('color', 'white'),
                    ('font-size', '14px'),
                    ('text-align', 'center'),
                    ('white-space', 'nowrap')
                ]
            },
            {
                'selector': 'td',
                'props': [
                    ('font-size', '12px'),
                    ('text-align', 'center'),
                    ('white-space', 'nowrap')
                ]
            },
            {
                'selector': 'td.col0',
                'props': [('font-weight', 'bold')]
            }
        ]
    ).set_properties(**{'border': '1px solid white', 'width': '70px'})

    return styled_df
