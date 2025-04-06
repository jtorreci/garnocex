import streamlit as st
import pandas as pd
from datetime import datetime

from models.muestras import obtener_muestras, obtener_muestra
from models.granulometria import guardar_ensayo_granulometrico, obtener_ensayo_granulometrico
from utils.tamices import get_tamices_estandar
from utils.calculo import procesar_datos_tamices, calcular_diametros_caracteristicos, calcular_coeficientes
from utils.graficos import generar_grafico_granulometrico

def mostrar_pagina_granulometria():
    """
    Muestra la página de ensayo granulométrico
    """
    st.header("Ensayo Granulométrico")
    
    try:
        # Seleccionar muestra para el ensayo
        muestras = obtener_muestras()
        
        if not muestras:
            st.warning("No hay muestras registradas. Por favor registre una muestra primero.")
            if st.button("Ir a Registro de Muestras"):
                st.session_state.pagina_actual = "Registro de Muestras"
                st.rerun()
            return
        
        codigos_muestras = [m["codigo_muestra"] for m in muestras]
        
        # Usar la muestra seleccionada desde otra página, si existe
        if "realizar_ensayo" in st.session_state:
            codigo_seleccionado = st.session_state.realizar_ensayo
            # Eliminar para evitar que persista en futuras navegaciones
            del st.session_state.realizar_ensayo
            # Verificar que el código siga existiendo
            if codigo_seleccionado not in codigos_muestras:
                st.error(f"La muestra {codigo_seleccionado} ya no existe.")
                codigo_seleccionado = codigos_muestras[0] if codigos_muestras else None
        else:
            codigo_seleccionado = st.selectbox(
                "Seleccionar Muestra",
                options=codigos_muestras
            )
        
        if not codigo_seleccionado:
            st.warning("No hay muestras disponibles.")
            return
            
        # Obtener datos de la muestra seleccionada
        muestra = obtener_muestra(codigo_seleccionado)
        
        if muestra:
            st.subheader(f"Muestra: {codigo_seleccionado}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Operario:** {muestra['operario']}")
            with col2:
                st.write(f"**Fecha:** {muestra['fecha']}")
            with col3:
                st.write(f"**Tipo Material:** {muestra['tipo_material']}")
            
            # Formulario de ensayo granulométrico
            with st.form("formulario_granulometria"):
                # Datos generales del ensayo
                col1, col2 = st.columns(2)
                
                with col1:
                    operario_ensayo = st.text_input("Operario", value=muestra['operario'])
                
                with col2:
                    fecha_ensayo = st.date_input("Fecha del Ensayo", value=datetime.now().date())
                
                masa_total = st.number_input("Masa Total de Muestra (g)", min_value=0.1, step=0.1)
                
                # Tamices y masas retenidas
                st.subheader("Masas Retenidas por Tamiz")
                
                tamices = get_tamices_estandar()
                masas_retenidas = []
                
                # Crear campos para cada tamiz
                cols_por_fila = 3
                filas = (len(tamices) + cols_por_fila - 1) // cols_por_fila
                
                for fila in range(filas):
                    cols = st.columns(cols_por_fila)
                    
                    for col_idx in range(cols_por_fila):
                        tamiz_idx = fila * cols_por_fila + col_idx
                        
                        if tamiz_idx < len(tamices):
                            tamiz = tamices[tamiz_idx]
                            with cols[col_idx]:
                                masa = st.number_input(
                                    f"Tamiz {tamiz['nombre']} ({tamiz['apertura']} mm)",
                                    min_value=0.0,
                                    step=0.1,
                                    key=f"tamiz_{tamiz_idx}"
                                )
                                masas_retenidas.append(masa)
                
                submit_ensayo = st.form_submit_button("Calcular y Guardar")
            
            if submit_ensayo:
                if masa_total <= 0:
                    st.error("La masa total debe ser mayor que cero")
                else:
                    # Verificar que la suma de masas no exceda la masa total
                    suma_masas = sum(masas_retenidas)
                    if abs(suma_masas - masa_total) > 0.1 * masa_total:
                        st.warning(f"La suma de masas retenidas ({suma_masas:.2f}g) difiere significativamente de la masa total ({masa_total:.2f}g)")
                    
                    # Procesar datos de tamices
                    datos_tamices = procesar_datos_tamices(tamices, masas_retenidas, masa_total)
                    
                    # Calcular parámetros D10, D30, D60
                    d10, d30, d60 = calcular_diametros_caracteristicos(datos_tamices)
                    
                    # Calcular coeficientes de uniformidad y curvatura
                    cu, cc = calcular_coeficientes(d10, d30, d60)
                    
                    # Guardar resultados
                    try:
                        ensayo_id = guardar_ensayo_granulometrico(
                            codigo_seleccionado, fecha_ensayo, operario_ensayo, 
                            masa_total, datos_tamices, d10, d30, d60, cu, cc
                        )
                        
                        st.success(f"Ensayo granulométrico guardado con éxito (ID: {ensayo_id})")
                        
                        # Establecer flag para mostrar resultados
                        st.session_state.mostrar_resultados = codigo_seleccionado
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar el ensayo: {str(e)}")
            
            # Mostrar resultados del ensayo si existe
            if "mostrar_resultados" in st.session_state and st.session_state.mostrar_resultados == codigo_seleccionado:
                ensayo = obtener_ensayo_granulometrico(codigo_seleccionado)
                
                if ensayo:
                    st.subheader("Resultados del Ensayo Granulométrico")
                    
                    # Mostrar parámetros calculados
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("D10", f"{ensayo['d10']:.3f} mm")
                        st.metric("Coef. Uniformidad", f"{ensayo['coef_uniformidad']:.2f}")
                    
                    with col2:
                        st.metric("D30", f"{ensayo['d30']:.3f} mm")
                    
                    with col3:
                        st.metric("D60", f"{ensayo['d60']:.3f} mm")
                        st.metric("Coef. Curvatura", f"{ensayo['coef_curvatura']:.2f}")
                    
                    # Mostrar datos de tamices en tabla
                    st.subheader("Datos de Tamices")
                    df_tamices = pd.DataFrame([
                        {
                            "Tamiz": t["tamiz"],
                            "Apertura (mm)": t["apertura"],
                            "Masa Retenida (g)": t["masa_retenida"],
                            "% Retenido": f"{t['porcentaje_retenido']:.2f}",
                            "% Retenido Acumulado": f"{t['porcentaje_retenido_acumulado']:.2f}",
                            "% Pasa": f"{t['porcentaje_pasa']:.2f}"
                        }
                        for t in ensayo['tamices']
                    ])
                    
                    st.dataframe(df_tamices)
                    
                    # Generar y mostrar gráfico
                    fig = generar_grafico_granulometrico(ensayo['tamices'])
                    st.plotly_chart(fig)
                    
                    # Botón para exportar datos
                    if st.button("Exportar Resultados (CSV)"):
                        csv = df_tamices.to_csv(index=False)
                        st.download_button(
                            label="Descargar CSV",
                            data=csv,
                            file_name=f"granulometria_{codigo_seleccionado}.csv",
                            mime="text/csv"
                        )
        else:
            st.error("No se pudo cargar la información de la muestra seleccionada.")
    
    except Exception as e:
        st.error(f"Ha ocurrido un error: {str(e)}")
        st.exception(e)