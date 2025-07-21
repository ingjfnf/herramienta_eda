import io
import streamlit as st
from utils.visual_utils import style_tabla_filtro
import pandas as pd
import plotly.express as px

def grafica_ten(df):


#GRÁFICA DE TENDENCIAS
    

    st.subheader(":point_right: Análisis Gráfico de Tendencias para Escenarios Presupuestales")
  
    # Utilizamos el DataFrame final guardado en el estado de sesión
    
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    
    
    df['Mes'] = df['FECHA'].dt.strftime('%b')
    df['Año'] = df['FECHA'].dt.year
    
    
    meses_ingles = {'ene.': 'Jan', 'feb.': 'Feb', 'mar.': 'Mar', 'abr.': 'Apr', 'may.': 'May', 'jun.': 'Jun',
                    'jul.': 'Jul', 'ago.': 'Aug', 'sep.': 'Sep', 'oct.': 'Oct', 'nov.': 'Nov', 'dic.': 'Dec'}
    df['Mes'] = df['Mes'].replace(meses_ingles)
    
    df['EJECUCIÓN_MIL_MILLONES'] = df['VALOR'] / 1e9
    
    
    df['Mes'] = pd.Categorical(df['Mes'], categories=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], ordered=True)

    conceptos_unicos = df['CONCEPTO'].unique().tolist()
    conceptos_opciones = ['TODAS'] + conceptos_unicos

    
    col1, col2 = st.columns(2)
    with col1:
        conceptos_seleccionados = st.multiselect('Selecciona los conceptos', options=conceptos_opciones, default=[])
    with col2:
        analisis = st.multiselect('Selecciona el tipo de análisis', options=df['ANALISIS'].unique(), default=[])

    
    if 'TODAS' in conceptos_seleccionados:
        conceptos_seleccionados = conceptos_unicos

    if conceptos_seleccionados and analisis:
        
        df_filtered = df[(df['CONCEPTO'].isin(conceptos_seleccionados)) & (df['ANALISIS'].isin(analisis))]

        
        if not df_filtered.empty:
            df_grouped = df_filtered.groupby(['Mes', 'Año', 'ANALISIS'], as_index=False)['EJECUCIÓN_MIL_MILLONES'].sum()

            
            df_grouped = df_grouped[df_grouped['EJECUCIÓN_MIL_MILLONES'] != 0]

            
            fig = px.line(
                df_grouped,
                x='Mes',
                y='EJECUCIÓN_MIL_MILLONES',
                color='ANALISIS',  #
                title="COMPARACIÓN DE ESCENARIOS PRESUPUESTALES",
                labels={'EJECUCIÓN_MIL_MILLONES': 'Ejecución (Mil Millones de COP)', 'ANALISIS': 'Tipo de Análisis'},
                markers=True
            )

            
            for trace in fig.data:
                trace.update(name=trace.name.split(',')[0])  
                trace.update(line=dict(dash=None))  

            
            unique_colors = px.colors.qualitative.Plotly
            color_mapping = {name: unique_colors[i % len(unique_colors)] for i, name in enumerate(df['ANALISIS'].unique())}
            for trace in fig.data:
                trace.update(line=dict(color=color_mapping[trace.name]))

            
            for trace in fig.data:
                trace.update(
                    hovertemplate='<b>Mes</b>: %{x}<br>' +
                    '<b>Ejecución</b>: $%{y:.2f} Mil Millones<br>' +
                    '<b>Análisis</b>: ' + trace.name + '<br>'
                )

            
            fig.update_layout(
                width=1250,
                height=730,
                title={
                    'text': "COMPARACIÓN DE ESCENARIOS PRESUPUESTALES",
                    'y':0.9,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=24)
                },
                xaxis=dict(showgrid=False), 
                   yaxis=dict(
                    showgrid=True,
                    gridwidth=0.5,
                    gridcolor='rgba(255, 255, 255, 0.1)'),  
                    
                plot_bgcolor='rgba(0, 0, 0, 0)'  

            )

            st.plotly_chart(fig)
       
            def descargar_excel(dataframe):
                if 'FECHA' in dataframe.columns:
                    dataframe['FECHA'] = dataframe['FECHA'].dt.date
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dataframe.to_excel(writer, index=False, sheet_name='Sheet1')
                processed_data = output.getvalue()
                return processed_data
                                
            
            excel_data = descargar_excel(df)
            st.download_button(
                label="Descargar Datos",
                data=excel_data,
                file_name="tendencias.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            #TABLA EXPANSORA
            
            expansor = df.copy()

            expansor['FECHA'] = pd.to_datetime(expansor['FECHA'], errors='coerce')
            expansor['MES'] = expansor['FECHA'].dt.strftime('%B')
            analisis_options = ['Seleccione una opción'] + list(expansor['ANALISIS'].unique())

            with st.expander("TABLA DINÁMICA: CÁLCULO DE DIFERENCIAS POR ESCENARIO"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    escenario_1 = st.selectbox("Escenario 1", options=analisis_options, key="escenario_1")
                with col2:
                    escenario_2 = st.selectbox("Escenario 2", options=analisis_options, key="escenario_2")
                with col3:
                    conceptos_seleccionados = st.multiselect("Conceptos", options=expansor['CONCEPTO'].unique(), key="conceptos_seleccionados")
                with col4:
                    fechas_seleccionadas = st.multiselect("Meses", options=expansor['MES'].unique(), key="fechas_seleccionadas")

                
                total_escenario = [escenario_1, escenario_2]
                if 'Seleccione una opción' in total_escenario:
                    st.warning("Por favor, seleccione opciones válidas para los escenarios.")
                else:
                    
                    filtro = expansor[
                        (expansor['ANALISIS'].isin(total_escenario)) & 
                        (expansor['CONCEPTO'].isin(conceptos_seleccionados)) & 
                        (expansor['MES'].isin(fechas_seleccionadas))
                    ]

                    if filtro.empty:
                        st.warning("No hay datos que coincidan con los filtros seleccionados.")
                    else:
                        df_pivot = filtro.pivot_table(index=['CONCEPTO', 'MES'], columns='ANALISIS', values='VALOR').reset_index()
                        meses_ls = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        df_pivot['MES'] = pd.Categorical(df_pivot['MES'], categories=meses_ls, ordered=True)
                        dfsalida = df_pivot.sort_values(by=['CONCEPTO', 'MES'])
                        nombre_columna_diferencia = f"{escenario_2} - {escenario_1}"
                        dfsalida[nombre_columna_diferencia] = dfsalida.apply(lambda x: x[escenario_2] - x[escenario_1], axis=1)
                        if escenario_1==escenario_2:
                            dfsalida=dfsalida[['CONCEPTO', 'MES',escenario_1,nombre_columna_diferencia]]
                        else:
                            dfsalida=dfsalida[['CONCEPTO', 'MES',escenario_1,escenario_2,nombre_columna_diferencia]]
                        styled_filtrado = style_tabla_filtro(dfsalida,nombre_columna_diferencia)
                        st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
                        st.write(styled_filtrado.set_table_attributes('class="styled-table"').hide(axis="index").to_html(), unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown('<p style="font-size:24px; color:orange;">No hay datos disponibles para los filtros seleccionados.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="font-size:24px; color:orange;">Por favor, selecciona al menos un concepto y un tipo de análisis para visualizar la gráfica.</p>', unsafe_allow_html=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)