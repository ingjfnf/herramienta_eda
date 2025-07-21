import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
from statsmodels.tsa.seasonal import seasonal_decompose
from utils.transformaciones import temporalidad
from utils.visual_utils import style_modelos
from utils.cargar_metricas import cargar_metricas_modelos


def descomposicion(df):
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.subheader(":point_right: Análisis Gráfico de Descomposición de la Serie de Tiempo para HORAS EXTRA - COLOMBIA")

    # Transformación de la serie temporal
    data_agrupada_ok = temporalidad(df)
    descomposicion = seasonal_decompose(data_agrupada_ok["Cost (lc)"], model='additive')

    # Crear figura compacta (no gigante ni aplastada)
    fig, axs = plt.subplots(4, 1, figsize=(8, 4), sharex=True)
    componentes = ['observed', 'trend', 'seasonal', 'resid']
    titulos = ['Serie Observada', 'Tendencia', 'Estacionalidad', 'Residuo']

    for i, componente in enumerate(componentes):
        serie = getattr(descomposicion, componente)
        axs[i].plot(serie, linewidth=2)
        axs[i].set_ylabel(titulos[i], fontsize=7)
        axs[i].tick_params(axis='y', labelsize=8)
        axs[i].xaxis.set_major_formatter(mdates.DateFormatter('%b-%Y'))
        axs[i].tick_params(axis='x', labelrotation=30, labelsize=7)

    if componente == 'resid':
        axs[i].axhline(y=0, color='gray', linestyle='--', linewidth=1)

    plt.subplots_adjust(hspace=0.5)

    # CENTRAR la gráfica en una columna ancha real
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        st.pyplot(fig)
    
    st.markdown("<h3 style='color:white;'>🧠 Explicación del Análisis de los Componentes</h3>", unsafe_allow_html=True)

    with st.expander("Despliega para ver el análisis detallado", expanded=False):

        st.markdown("### 1. **Serie Observada (Cost (lc)**")
        st.markdown("""
        * 📈 Se ve claramente una **tendencia ascendente** con fluctuaciones mensuales.  
        * Las oscilaciones tienen una **amplitud moderada**, pero hay cierta repetición → posible estacionalidad.
        """)

        st.markdown("### 2. **Tendencia (Trend)**")
        st.markdown("""
        * La curva muestra un **crecimiento constante hasta mediados de 2024**, luego parece **estabilizarse**.  
        * Esto indica que la serie **no es estacionaria**, ya que la media cambia con el tiempo.  
        🔎 *Confirma que debemos aplicar modelos que incluyan tendencia.*
        """)

        st.markdown("### 3. **Estacionalidad (Seasonal)**")
        st.markdown("""
        * Se observa un **patrón repetitivo anual** con picos entre **agosto y diciembre**, y valles en **enero/febrero**.  
        📌 *Esto sugiere aplicar modelos como SARIMA o Prophet.*
        """)

        st.markdown("### 4. **Residuo (Resid)**")
        st.markdown("""
        * Los residuos están **centrados en cero** sin patrones claros.  
        ✅ *Esto indica que la tendencia y estacionalidad explican bien la variabilidad de la serie.*
        """)

        st.markdown("### ✅ Conclusión General:")
        st.markdown("""
        * **No es estacionaria**  
        * **Tiene estacionalidad anual**  
        * **El ruido está controlado y no hay patrones residuales relevantes**
        """)



def tabla():
    st.subheader(":point_right: 📊 Métricas de Evaluación por Modelo")

    df_resultados = cargar_metricas_modelos()
    styled_df_model = style_modelos(df_resultados.reset_index())

    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    st.write(
        styled_df_model.set_table_attributes('class=\"styled-table\"').hide(axis="index").to_html(),
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)



    with st.expander("Despliega para ver el análisis detallado", expanded=False):
        st.markdown("""
    ### 📊 Comparación de modelos para las proyecciones

    Se probaron cuatro modelos para predecir el comportamiento futuro de los datos. Para saber cuál funciona mejor, los comparamos usando tres métricas claves, tanto con los datos de **entrenamiento** (los datos que el modelo ya conocía), como con los de **prueba** (datos nuevos que no había visto antes).

    ---

    ### 📐 ¿Qué miden las métricas?

    - **MAE (Error Absoluto Medio)**: indica **cuánto se equivoca el modelo en promedio**. Si el MAE es de 5 millones, significa que en promedio, el modelo se equivoca por +/- 5 millones con respecto al valor real.
    
    - **RMSE (Raíz del Error Cuadrático Medio)**: Mide qué tan grandes son, en promedio, los errores del modelo, **pero da más peso a los errores muy grandes.** Es decir, si el modelo a veces se equivoca por mucho, esta métrica lo refleja con más fuerza.
        Sirve para identificar si el modelo tiene picos de error que podrían afectar decisiones importantes, aunque en promedio no se equivoque tanto.
    
    - **MAPE (Error Porcentual Absoluto Medio)**: expresa el error **como un porcentaje respecto al valor real**, lo que permite compararlo en distintas escalas. Por ejemplo, un MAPE de 6% significa que el modelo, en promedio, se desvía un 6% del valor correcto.

    Lo ideal es que **todas estas métricas sean lo más bajas posible**, tanto en entrenamiento como en prueba.

    ---

    ### ✅ ¿Por qué recomendamos el modelo **PROPHET**?

    Después de analizar los resultados, **PROPHET** es el modelo que mejor predice datos nuevos y lo hace con la menor cantidad de errores, por las siguientes razones:

    1. 🟢 **Es el más preciso con datos reales**:
    - Prophet tuvo el **menor error porcentual en prueba (MAPE: 6.17%)**.
    - También fue el que menos se equivocó en términos absolutos (MAE y RMSE en prueba más bajos que los otros modelos).

    2. 🧠 **Aprendió bien sin memorizar**:
    - Prophet mostró **muy poca diferencia entre los errores en entrenamiento y prueba**, lo cual indica que **generaliza bien**, es decir, **no memoriza los datos viejos, sino que entiende el comportamiento general de la serie**.

    3. ⚖️ **Balance entre precisión y estabilidad**:
    - A diferencia de otros modelos, Prophet logra un equilibrio ideal entre buenos resultados y consistencia, sin ser ni muy optimista ni muy conservador.

    ---

    ### 🔎 ¿Qué pasó con los otros modelos?

    - 🔴 **XGBOOST_REG**:
    - Durante el entrenamiento, parecía el modelo perfecto (casi sin errores).
    - Pero al enfrentarse a datos nuevos, **su error subió bruscamente**, lo que indica que **memorizó el pasado y no supo adaptarse al futuro**. Esto es un clásico caso de **sobreajuste**.

    - 🟠 **SARIMA**:
    - Tuvo **los peores resultados en todos los indicadores**.
    - Ni siquiera fue preciso con los datos de entrenamiento, lo que sugiere que **no entendió bien el patrón de la serie**.

    - 🟡 **RANDOM_FOREST**:
    - Es un buen modelo, con errores moderadamente bajos.
    - Sin embargo, **tuvo errores un poco mayores que Prophet en todas las métricas**, por lo que no fue la opción óptima.

    ---

    ### 🟢 Conclusión

    > El modelo **PROPHET** es el más recomendable para las proyecciones porque combina:
    > - Alta precisión.
    > - Estabilidad.
    > - Buena capacidad para adaptarse a datos nuevos.

    Esto lo convierte en la mejor herramienta para tomar decisiones informadas y confiables basadas en las predicciones del sistema.
    """)
    