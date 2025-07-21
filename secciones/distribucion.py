import io
import streamlit as st
from utils.visual_utils import style_tabla_distribucion
from utils.transformaciones import distributivo
import pandas as pd
import plotly.express as px

def distribuir(df,distri):
 #DISTRIBUCION_GRAFI
    df_distri = df.copy()
    df_distribucion= distributivo(df_distri,distri)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.subheader(":point_right: Análisis de Distribución de Costos Mensuales por Concepto")
   
    # Variable selector
    col1, col2 = st.columns(2)
    with col1:
        seleccion_conceptos = st.multiselect(
            'Selecciona el concepto para analizar',
            options=df_distribucion['CONCEPTO'].unique(),
            key="custom-selector-conceptos"
        )    

    with col2:
        seleccion_analisis = st.multiselect(
            'Selecciona el tipo de análisis para analizar',
            options=df_distribucion['ANALISIS'].unique(),
            key="custom-selector-analisis"
        ) 

    df_filtrado = df_distribucion[
        (df_distribucion['CONCEPTO'].isin(seleccion_conceptos)) &
        (df_distribucion['ANALISIS'].isin(seleccion_analisis))
    ].copy()

    if not df_filtrado.empty:
        df_filtrado['FECHA'] = pd.to_datetime(df_filtrado['FECHA'])
        df_filtrado['Mes'] = df_filtrado['FECHA'].dt.strftime('%B')
        df_filtrado['PESO PONDERADO PROMEDIO'] = df_filtrado['PESO PONDERADO PROMEDIO'].round(2)

        # Definir el orden de los meses en inglés
        meses_ordenados = ['January', 'February', 'March', 'April', 'May', 'June', 
                        'July', 'August', 'September', 'October', 'November', 'December']
        df_filtrado['Mes'] = pd.Categorical(df_filtrado['Mes'], categories=meses_ordenados, ordered=True)
        
        # Crear una columna combinada para concepto y análisis
        df_filtrado['CONCEPTO_ANALISIS'] = df_filtrado['CONCEPTO'] + ' - ' + df_filtrado['ANALISIS']

        fig = px.line(
            df_filtrado,
            x='Mes',
            y='PESO PONDERADO PROMEDIO',
            color='CONCEPTO_ANALISIS',
            title="DISTRIBUCIÓN MENSUAL DE COSTOS",
            labels={'PESO PONDERADO PROMEDIO': 'DISTRIBUCIÓN PORCENTUAL %', 'CONCEPTO_ANALISIS': 'Concepto - Tipo de Análisis'},
            markers=True
        )

        for trace in fig.data:
            trace.update(name=trace.name.split(',')[0])
            trace.update(line=dict(dash=None))

        unique_colors = px.colors.qualitative.Plotly
        color_mapping = {name: unique_colors[i % len(unique_colors)] for i, name in enumerate(df_filtrado['CONCEPTO_ANALISIS'].unique())}
        for trace in fig.data:
            trace.update(line=dict(color=color_mapping[trace.name]))

        for trace in fig.data:
            trace.update(
                hovertemplate='<b>Mes</b>: %{x}<br>' +
                '<b>Distribución Porcentual</b>: %{y:.2f}%<br>' +
                '<b>Concepto - Análisis</b>: ' + trace.name + '<br>'
            )

        fig.update_layout(
            width=1280,
            height=730,
            title={
                'text': "DISTRIBUCIÓN MENSUAL DE COSTOS",
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24)
            },
            xaxis=dict(showgrid=False, categoryorder='array', categoryarray=meses_ordenados),
            yaxis=dict(
                tickformat=".0f",  
                showgrid=True,
                gridwidth=0.5,
                gridcolor='rgba(255, 255, 255, 0.1)',
            ),
            plot_bgcolor='rgba(0, 0, 0, 0)'
        )

        st.plotly_chart(fig)
        def descargar_excel_d(dataframe):
            dataframe['FECHA'] = pd.to_datetime(dataframe['FECHA'])
            dataframe['FECHA'] = dataframe['FECHA'].dt.strftime('%Y-%m-%d')
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                dataframe.to_excel(writer, index=False, sheet_name='Sheet1')
            processed_data = output.getvalue()
            return processed_data


        excel_data = descargar_excel_d(df_distribucion)
        st.download_button(
            label="Descargar Datos",
            data=excel_data,
            file_name="Distribución.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        with st.expander("TABLA DINÁMICA: DISTRIBUCIÓN MENSUAL DE COSTOS POR ESCENARIO"):
            col1, col2 = st.columns(2)
                
            with col1:
                filtro_conceptos = st.multiselect(
                'Selecciona el concepto para analizar',
                options=df_distribucion['CONCEPTO'].unique(),
                key="conceptos_tabla"
            )   
            with col2:
                filtro_analisis = st.multiselect(
                'Selecciona el tipo de análisis para analizar',
                options=df_distribucion['ANALISIS'].unique(),
                key="tabla_analisis"
                ) 
            
            df_tabla=df_distribucion.copy()
            df_tabla['FECHA'] = pd.to_datetime(df_tabla['FECHA'])
            df_tabla['NOMBRE_MES'] = df_tabla['FECHA'].dt.strftime('%b')

            df_filtrado_t = df_tabla[(df_tabla['CONCEPTO'].isin(filtro_conceptos)) & (df_tabla['ANALISIS'].isin(filtro_analisis))].copy()
            if not df_filtrado_t.empty:
                del df_filtrado_t["FECHA"]
                pivot_df = df_filtrado_t.pivot_table(
                    index=['ANALISIS', 'CONCEPTO'],
                    columns='NOMBRE_MES',
                    values='PESO PONDERADO PROMEDIO',
                    aggfunc='mean'
                ).reset_index()

                
                all_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                
                for month in all_months:
                    if month not in pivot_df.columns:
                        pivot_df[month] = None

                
                pivot_df = pivot_df[['ANALISIS', 'CONCEPTO'] + all_months]
                pivot_df = pivot_df.sort_values(by=['CONCEPTO'])
                styled_distribuido = style_tabla_distribucion(pivot_df)
                st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
                st.write(styled_distribuido.set_table_attributes('class="styled-table"').hide(axis="index").to_html(), unsafe_allow_html=True)

            else:
                st.markdown('<p style="font-size:24px; color:orange;">Por favor, selecciona al menos un concepto y un tipo de análisis para visualizar la tabla.</p>', unsafe_allow_html=True)



    else:
        st.markdown('<p style="font-size:24px; color:orange;">Por favor, selecciona al menos un concepto y un tipo de análisis para visualizar la gráfica.</p>', unsafe_allow_html=True)