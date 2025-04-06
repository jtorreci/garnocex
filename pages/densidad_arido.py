import streamlit as st
import pandas as pd
from datetime import datetime
import io
import plotly.graph_objects as go
from PIL import Image

from models.muestras import obtener_muestras, obtener_muestra, obtener_imagenes
from models.densidad_arido import (guardar_ensayo_densidad_arido, obtener_ensayo_densidad_arido,
                                 calcular_parametros_densidad)

def mostrar_pagina_densidad_arido():
    """
    Muestra la página de ensayo de densidad de árido grueso
    """
    st.header("Ensayo de Densidad de Árido Grueso")
    
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
            
            # Comprobar si ya existe un ensayo para esta muestra
            ensayo_existente = obtener_ensayo_densidad_arido(codigo_seleccionado)
            
            if ensayo_existente:
                st.info("Esta muestra ya tiene un ensayo de densidad de árido grueso registrado. Puede visualizarlo o registrar uno nuevo.")
                if st.button("Ver Ensayo Existente"):
                    st.session_state.mostrar_resultados = codigo_seleccionado
                    st.rerun()
            
            # Formulario de ensayo
            with st.form("formulario_densidad_arido"):
                st.subheader("Nuevo Ensayo de Densidad de Árido Grueso")
                
                # Datos generales del ensayo
                col1, col2 = st.columns(2)
                
                with col1:
                    operario_ensayo = st.text_input("Operario", value=muestra['operario'])
                
                with col2:
                    fecha_ensayo = st.date_input("Fecha del Ensayo", value=datetime.now().date())
                
                # Datos específicos del ensayo
                st.markdown("### Datos del Ensayo")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Masas")
                    masa_seca = st.number_input("Masa seca (g)", min_value=0.1, step=0.1)
                    masa_sss = st.number_input("Masa saturada superficie seca (g)", min_value=0.1, step=0.1)
                    masa_sumergida = st.number_input("Masa sumergida (g)", min_value=0.1, step=0.1)
                
                # Campo para notas adicionales
                notas = st.text_area("Notas y Observaciones")
                
                # Imágenes del ensayo
                archivos_imagenes = st.file_uploader(
                    "Cargar imágenes del ensayo",
                    accept_multiple_files=True,
                    type=["png", "jpg", "jpeg"]
                )
                
                submitted = st.form_submit_button("Calcular y Guardar")
            
            # Procesar el formulario
            if submitted:
                if masa_seca <= 0 or masa_sss <= 0 or masa_sumergida <= 0:
                    st.error("Todos los valores de masa deben ser mayores que cero")
                else:
                    try:
                        # Calcular parámetros
                        densidad_aparente, densidad_tras_secado, densidad_sss, absorcion_agua = calcular_parametros_densidad(
                            masa_seca, masa_sss, masa_sumergida
                        )
                        
                        # Mostrar resultados calculados
                        st.subheader("Resultados calculados:")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Densidad aparente", f"{densidad_aparente:.2f} g/cm³")
                            st.metric("Densidad tras secado", f"{densidad_tras_secado:.2f} g/cm³")
                        with col2:
                            st.metric("Densidad SSS", f"{densidad_sss:.2f} g/cm³")
                            st.metric("Absorción de agua", f"{absorcion_agua:.2f} %")
                        
                        # Confirmar guardar
                        if st.button("Confirmar y Guardar Resultados"):
                            # Guardar resultados en la base de datos
                            ensayo_id = guardar_ensayo_densidad_arido(
                                codigo_seleccionado, fecha_ensayo, operario_ensayo,
                                masa_seca, masa_sss, masa_sumergida,
                                densidad_aparente, densidad_tras_secado, densidad_sss, absorcion_agua,
                                notas
                            )
                            
                            # Guardar imágenes si hay
                            imagenes_guardadas = 0
                            for archivo in archivos_imagenes:
                                try:
                                    img = Image.open(archivo)
                                    # Aquí faltaría implementar una función para guardar la imagen con el ensayo_id
                                    # guardar_imagen_ensayo(codigo_seleccionado, ensayo_id, img, archivo.name)
                                    imagenes_guardadas += 1
                                except Exception as e:
                                    st.error(f"Error al guardar imagen {archivo.name}: {str(e)}")
                            
                            st.success(f"Ensayo de densidad de árido grueso guardado con éxito (ID: {ensayo_id})")
                            
                            # Establecer flag para mostrar resultados
                            st.session_state.mostrar_resultados = codigo_seleccionado
                            st.rerun()
                            
                    except ValueError as e:
                        st.error(f"Error en los cálculos: {str(e)}")
                    except Exception as e:
                        st.error(f"Error al procesar el ensayo: {str(e)}")
            
            # Mostrar resultados del ensayo si existe
            if "mostrar_resultados" in st.session_state and st.session_state.mostrar_resultados == codigo_seleccionado:
                ensayo = obtener_ensayo_densidad_arido(codigo_seleccionado)
                
                if ensayo:
                    st.subheader("Resultados del Ensayo de Densidad de Árido Grueso")
                    
                    # Mostrar datos generales
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Fecha del ensayo:** {ensayo['fecha_ensayo']}")
                        st.write(f"**Operario:** {ensayo['operario']}")
                    
                    # Mostrar parámetros calculados
                    st.markdown("### Densidades y Absorción")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Densidad aparente", f"{ensayo['densidad_aparente']:.2f} g/cm³")
                        st.metric("Absorción de agua", f"{ensayo['absorcion_agua']:.2f} %")
                    
                    with col2:
                        st.metric("Densidad tras secado", f"{ensayo['densidad_tras_secado']:.2f} g/cm³")
                    
                    with col3:
                        st.metric("Densidad SSS", f"{ensayo['densidad_sss']:.2f} g/cm³")
                    
                    # Mostrar datos de masas
                    st.markdown("### Datos de Masas")
                    
                    masas_df = pd.DataFrame({
                        "Parámetro": ["Masa seca", "Masa SSS", "Masa sumergida"],
                        "Valor (g)": [
                            ensayo['masa_seca'],
                            ensayo['masa_sss'],
                            ensayo['masa_sumergida']
                        ]
                    })
                    
                    st.dataframe(masas_df, use_container_width=True)
                    
                    # Evaluación según normativa UNE-EN 1097-6
                    st.markdown("### Evaluación según Normativa")
                    
                    # Criterios de evaluación
                    if ensayo['densidad_aparente'] >= 2.0 and ensayo['densidad_aparente'] <= 3.0:
                        st.success("✅ La densidad aparente está dentro del rango típico para áridos (2.0 - 3.0 g/cm³)")
                    else:
                        st.warning("⚠️ La densidad aparente está fuera del rango típico para áridos (2.0 - 3.0 g/cm³)")
                    
                    if ensayo['absorcion_agua'] <= 5.0:
                        st.success("✅ La absorción de agua es aceptable (≤ 5%)")
                    else:
                        st.warning("⚠️ La absorción de agua es superior al valor recomendado (> 5%)")
                    
                    # Mostrar notas
                    if ensayo['notas']:
                        st.markdown("### Notas del Ensayo")
                        st.info(ensayo['notas'])
                    
                    # Gráfico comparativo
                    st.markdown("### Visualización")
                    
                    # Crear un gráfico de barras sencillo con los resultados
                    fig = go.Figure()
                    
                    # Añadir barras para cada densidad
                    fig.add_trace(go.Bar(
                        x=['Densidad aparente', 'Densidad tras secado', 'Densidad SSS'],
                        y=[
                            ensayo['densidad_aparente'],
                            ensayo['densidad_tras_secado'],
                            ensayo['densidad_sss']
                        ],
                        text=[
                            f"{ensayo['densidad_aparente']:.2f} g/cm³",
                            f"{ensayo['densidad_tras_secado']:.2f} g/cm³",
                            f"{ensayo['densidad_sss']:.2f} g/cm³"
                        ],
                        textposition='auto',
                        marker_color=['rgba(55, 83, 109, 0.7)', 'rgba(26, 118, 255, 0.7)', 'rgba(55, 128, 191, 0.7)']
                    ))
                    
                    # Configurar el diseño del gráfico
                    fig.update_layout(
                        title="Comparación de Densidades",
                        yaxis_title="Densidad (g/cm³)",
                        height=400,
                        showlegend=False
                    )
                    
                    # Mostrar el gráfico
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Opciones adicionales
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Botón para exportar resultados
                        if st.button("Exportar Resultados (CSV)"):
                            # Crear DataFrame para exportar
                            export_data = pd.DataFrame({
                                "Parámetro": [
                                    "Código Muestra", "Fecha Ensayo", "Operario",
                                    "Masa seca (g)", "Masa SSS (g)", "Masa sumergida (g)",
                                    "Densidad aparente (g/cm³)", "Densidad tras secado (g/cm³)",
                                    "Densidad SSS (g/cm³)", "Absorción de agua (%)"
                                ],
                                "Valor": [
                                    codigo_seleccionado, ensayo['fecha_ensayo'], ensayo['operario'],
                                    ensayo['masa_seca'], ensayo['masa_sss'], ensayo['masa_sumergida'],
                                    ensayo['densidad_aparente'], ensayo['densidad_tras_secado'],
                                    ensayo['densidad_sss'], ensayo['absorcion_agua']
                                ]
                            })
                            
                            # Convertir a CSV
                            csv = export_data.to_csv(index=False)
                            
                            # Botón de descarga
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name=f"densidad_arido_{codigo_seleccionado}.csv",
                                mime="text/csv"
                            )
                    
                    with col2:
                        # Botón para realizar otro ensayo
                        if st.button("Realizar Nuevo Ensayo"):
                            # Limpiar el estado para permitir un nuevo registro
                            if "mostrar_resultados" in st.session_state:
                                del st.session_state.mostrar_resultados
                            st.rerun()
                else:
                    st.error("No se pudo cargar la información del ensayo.")
        else:
            st.error("No se pudo cargar la información de la muestra seleccionada.")
    
    except Exception as e:
        st.error(f"Ha ocurrido un error: {str(e)}")
        st.exception(e)