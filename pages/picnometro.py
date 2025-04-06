import streamlit as st
import pandas as pd
from datetime import datetime
import io
import plotly.graph_objects as go
from PIL import Image

from models.muestras import obtener_muestras, obtener_muestra, obtener_imagenes
from models.picnometro import (guardar_ensayo_picnometro, obtener_ensayo_picnometro,
                             calcular_volumen_hoyo, calcular_densidad_aparente,
                             interpretar_densidad)

def mostrar_pagina_picnometro():
    """
    Muestra la página de ensayo de picnómetro de arena
    """
    st.header("Ensayo de Picnómetro de Arena")
    
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
            ensayo_existente = obtener_ensayo_picnometro(codigo_seleccionado)
            
            if ensayo_existente:
                st.info("Esta muestra ya tiene un ensayo de picnómetro de arena registrado. Puede visualizarlo o registrar uno nuevo.")
                if st.button("Ver Ensayo Existente"):
                    st.session_state.mostrar_resultados = codigo_seleccionado
                    st.rerun()
            
            # Formulario de ensayo
            with st.form("formulario_picnometro"):
                st.subheader("Nuevo Ensayo de Picnómetro de Arena")
                
                # Datos generales del ensayo
                col1, col2 = st.columns(2)
                
                with col1:
                    operario_ensayo = st.text_input("Operario", value=muestra['operario'])
                
                with col2:
                    fecha_ensayo = st.date_input("Fecha del Ensayo", value=datetime.now().date())
                
                # Datos específicos del ensayo
                st.markdown("### Datos del Ensayo")
                
                st.markdown("#### Datos de Calibración y Medición")
                col1, col2 = st.columns(2)
                
                with col1:
                    masa_arena_empleada = st.number_input("Masa total de arena empleada (g)", min_value=0.1, step=0.1)
                    masa_arena_cono = st.number_input("Masa de arena en el cono (g)", min_value=0.0, step=0.1)
                    densidad_arena = st.number_input("Densidad de la arena de calibración (g/cm³)", min_value=0.1, step=0.01, value=1.5)
                
                with col2:
                    st.markdown("#### Cálculos Automáticos")
                    
                    # Calcular volumen del hoyo
                    if masa_arena_empleada > 0 and densidad_arena > 0:
                        masa_arena_hoyo = max(0, masa_arena_empleada - masa_arena_cono)
                        volumen_hoyo = calcular_volumen_hoyo(masa_arena_empleada, masa_arena_cono, densidad_arena)
                        
                        st.metric("Masa de arena en el hoyo (g)", f"{masa_arena_hoyo:.1f}")
                        st.metric("Volumen del hoyo (cm³)", f"{volumen_hoyo:.1f}")
                        
                        # Input para masa del suelo
                        masa_suelo = st.number_input("Masa del suelo extraído (g)", min_value=0.0, step=0.1)
                        
                        if masa_suelo > 0 and volumen_hoyo > 0:
                            densidad_aparente = calcular_densidad_aparente(masa_suelo, volumen_hoyo)
                            st.metric("Densidad aparente (g/cm³)", f"{densidad_aparente:.2f}")
                            
                            # Interpretar la densidad
                            interpretacion = interpretar_densidad(densidad_aparente, muestra['tipo_material'].lower())
                            st.info(interpretacion)
                        else:
                            densidad_aparente = 0.0
                    else:
                        volumen_hoyo = 0.0
                        densidad_aparente = 0.0
                
                # Campo para notas adicionales
                notas = st.text_area("Notas y Observaciones")
                
                # Imágenes del ensayo
                archivos_imagenes = st.file_uploader(
                    "Cargar imágenes del ensayo",
                    accept_multiple_files=True,
                    type=["png", "jpg", "jpeg"]
                )
                
                submitted = st.form_submit_button("Guardar Ensayo")
            
            # Procesar el formulario
            if submitted:
                if masa_arena_empleada <= 0 or densidad_arena <= 0:
                    st.error("La masa de arena empleada y la densidad de la arena deben ser mayores que cero")
                elif masa_arena_cono >= masa_arena_empleada:
                    st.error("La masa de arena en el cono no puede ser mayor o igual a la masa total de arena empleada")
                else:
                    try:
                        # Calcular valores
                        volumen_hoyo = calcular_volumen_hoyo(masa_arena_empleada, masa_arena_cono, densidad_arena)
                        
                        if 'masa_suelo' in locals() and masa_suelo > 0:
                            densidad_aparente = calcular_densidad_aparente(masa_suelo, volumen_hoyo)
                        else:
                            densidad_aparente = 0.0
                            st.warning("No se ingresó la masa del suelo, se guardará densidad aparente como 0.")
                        
                        # Guardar ensayo
                        ensayo_id = guardar_ensayo_picnometro(
                            codigo_seleccionado, fecha_ensayo, operario_ensayo,
                            densidad_aparente, volumen_hoyo, masa_arena_empleada,
                            masa_arena_cono, densidad_arena, notas
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
                        
                        st.success(f"Ensayo de picnómetro de arena guardado con éxito (ID: {ensayo_id})")
                        
                        # Establecer flag para mostrar resultados
                        st.session_state.mostrar_resultados = codigo_seleccionado
                        st.rerun()
                            
                    except ValueError as e:
                        st.error(f"Error en los cálculos: {str(e)}")
                    except Exception as e:
                        st.error(f"Error al procesar el ensayo: {str(e)}")
            
            # Mostrar resultados del ensayo si existe
            if "mostrar_resultados" in st.session_state and st.session_state.mostrar_resultados == codigo_seleccionado:
                ensayo = obtener_ensayo_picnometro(codigo_seleccionado)
                
                if ensayo:
                    st.subheader("Resultados del Ensayo de Picnómetro de Arena")
                    
                    # Mostrar datos generales
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Fecha del ensayo:** {ensayo['fecha_ensayo']}")
                        st.write(f"**Operario:** {ensayo['operario']}")
                    
                    # Mostrar datos de la arena
                    st.markdown("### Datos de Arena y Calibración")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Masa de Arena Empleada", f"{ensayo['masa_arena_empleada']:.1f} g")
                    
                    with col2:
                        st.metric("Masa de Arena en Cono", f"{ensayo['masa_arena_cono']:.1f} g")
                        st.metric("Masa de Arena en Hoyo", f"{ensayo['masa_arena_empleada'] - ensayo['masa_arena_cono']:.1f} g")
                    
                    with col3:
                        st.metric("Densidad de Arena", f"{ensayo['densidad_arena']:.2f} g/cm³")
                    
                    # Mostrar resultados
                    st.markdown("### Resultados del Ensayo")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Volumen del Hoyo", f"{ensayo['volumen_hoyo']:.1f} cm³")
                    
                    with col2:
                        st.metric("Densidad Aparente", f"{ensayo['densidad_aparente']:.2f} g/cm³")
                    
                    # Interpretación
                    if ensayo['densidad_aparente'] > 0:
                        interpretacion = interpretar_densidad(ensayo['densidad_aparente'], muestra['tipo_material'].lower())
                        st.markdown("### Interpretación")
                        st.info(interpretacion)
                        
                        # Evaluación según rango típico
                        st.markdown("### Evaluación")
                        
                        if muestra['tipo_material'].lower() in ['suelo', 'arena', 'arcilla']:
                            tipo_suelo = muestra['tipo_material'].lower()
                        else:
                            tipo_suelo = 'suelo'
                        
                        if tipo_suelo == 'arena':
                            if ensayo['densidad_aparente'] < 1.4:
                                st.warning("⚠️ Densidad baja para arena (< 1.4 g/cm³)")
                            elif ensayo['densidad_aparente'] < 1.6:
                                st.success("✅ Densidad normal para arena (1.4 - 1.6 g/cm³)")
                            else:
                                st.success("✅ Densidad alta para arena (> 1.6 g/cm³)")
                        elif tipo_suelo == 'arcilla':
                            if ensayo['densidad_aparente'] < 1.6:
                                st.warning("⚠️ Densidad baja para arcilla (< 1.6 g/cm³)")
                            elif ensayo['densidad_aparente'] < 1.8:
                                st.success("✅ Densidad normal para arcilla (1.6 - 1.8 g/cm³)")
                            else:
                                st.success("✅ Densidad alta para arcilla (> 1.8 g/cm³)")
                        else:  # suelo genérico
                            if ensayo['densidad_aparente'] < 1.2:
                                st.error("❌ Densidad muy baja (< 1.2 g/cm³)")
                            elif ensayo['densidad_aparente'] < 1.4:
                                st.warning("⚠️ Densidad baja (1.2 - 1.4 g/cm³)")
                            elif ensayo['densidad_aparente'] < 1.6:
                                st.success("✅ Densidad media (1.4 - 1.6 g/cm³)")
                            elif ensayo['densidad_aparente'] < 1.8:
                                st.success("✅ Densidad alta (1.6 - 1.8 g/cm³)")
                            else:
                                st.success("✅ Densidad muy alta (> 1.8 g/cm³)")
                    
                    # Gráfico comparativo
                    st.markdown("### Visualización")
                    
                    # Crear gráfico comparativo de densidades típicas
                    fig = go.Figure()
                    
                    # Definir rangos de densidad típicos para diferentes materiales
                    materiales = ['Arena suelta', 'Arena compacta', 'Arcilla blanda', 'Arcilla firme', 'Muestra actual']
                    densidad_min = [1.3, 1.6, 1.5, 1.7, ensayo['densidad_aparente']]
                    densidad_max = [1.6, 2.0, 1.7, 2.2, ensayo['densidad_aparente']]
                    
                    # Añadir rangos para cada material
                    for i, material in enumerate(materiales):
                        if i < len(materiales) - 1:  # Todos excepto la muestra actual
                            fig.add_trace(go.Bar(
                                x=[material],
                                y=[(densidad_max[i] + densidad_min[i]) / 2],
                                error_y=dict(
                                    type='data',
                                    symmetric=False,
                                    array=[(densidad_max[i] - densidad_min[i]) / 2],
                                    arrayminus=[(densidad_max[i] - densidad_min[i]) / 2]
                                ),
                                width=0.6,
                                marker_color='rgba(55, 83, 109, 0.7)',
                                name=material
                            ))
                        else:  # Muestra actual
                            fig.add_trace(go.Bar(
                                x=[material],
                                y=[densidad_min[i]],
                                width=0.6,
                                marker_color='red',
                                name=material
                            ))
                    
                    # Configurar el diseño del gráfico
                    fig.update_layout(
                        title="Comparación con densidades típicas",
                        xaxis_title="Material",
                        yaxis_title="Densidad aparente (g/cm³)",
                        yaxis_range=[1.0, 2.5],
                        height=500,
                        showlegend=False
                    )
                    
                    # Mostrar el gráfico
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar notas
                    if ensayo['notas']:
                        st.markdown("### Notas del Ensayo")
                        st.info(ensayo['notas'])
                    
                    # Opciones adicionales
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Botón para exportar resultados
                        if st.button("Exportar Resultados (CSV)"):
                            # Crear DataFrame para exportar
                            export_data = pd.DataFrame({
                                "Parámetro": [
                                    "Código Muestra", "Fecha Ensayo", "Operario",
                                    "Masa Arena Empleada (g)", "Masa Arena Cono (g)",
                                    "Densidad Arena (g/cm³)", "Volumen Hoyo (cm³)",
                                    "Densidad Aparente (g/cm³)"
                                ],
                                "Valor": [
                                    codigo_seleccionado, ensayo['fecha_ensayo'], ensayo['operario'],
                                    ensayo['masa_arena_empleada'], ensayo['masa_arena_cono'],
                                    ensayo['densidad_arena'], ensayo['volumen_hoyo'],
                                    ensayo['densidad_aparente']
                                ]
                            })
                            
                            # Convertir a CSV
                            csv = export_data.to_csv(index=False)
                            
                            # Botón de descarga
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name=f"picnometro_{codigo_seleccionado}.csv",
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