import streamlit as st
import pandas as pd
from datetime import datetime
import io
import plotly.graph_objects as go
from PIL import Image

from models.muestras import obtener_muestras, obtener_muestra, obtener_imagenes
from models.cbr import (guardar_ensayo_cbr, obtener_ensayo_cbr, 
                      calcular_hinchamiento, calcular_absorcion_agua, interpretar_resultado_cbr)

def mostrar_pagina_cbr():
    """
    Muestra la página de ensayo CBR (California Bearing Ratio)
    """
    st.header("Ensayo CBR (California Bearing Ratio)")
    
    try:
        # Seleccionar muestra para el ensayo
        muestras = obtener_muestras()
        
        if not muestras:
            st.warning("No hay muestras registradas. Por favor registre una muestra primero.")
            if st.button("Ir a Registro de Muestras"):
                st.session_state.pagina_actual = "Registro de Muestras"
                st.experimental_rerun()
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
            ensayo_existente = obtener_ensayo_cbr(codigo_seleccionado)
            
            if ensayo_existente:
                st.info("Esta muestra ya tiene un ensayo CBR registrado. Puede visualizarlo o registrar uno nuevo.")
                if st.button("Ver Ensayo Existente"):
                    st.session_state.mostrar_resultados = codigo_seleccionado
                    st.experimental_rerun()
            
            # Formulario de ensayo
            with st.form("formulario_cbr"):
                st.subheader("Nuevo Ensayo CBR")
                
                # Datos generales del ensayo
                col1, col2 = st.columns(2)
                
                with col1:
                    operario_ensayo = st.text_input("Operario", value=muestra['operario'])
                
                with col2:
                    fecha_ensayo = st.date_input("Fecha del Ensayo", value=datetime.now().date())
                
                # Datos específicos del ensayo
                st.markdown("### Datos del Ensayo")
                
                # Parámetros de compactación
                st.markdown("#### Parámetros de Compactación")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    energia_compactacion = st.number_input("Energía de Compactación (J/m³)", min_value=0.0, step=0.1, value=592.7)
                    densidad_seca = st.number_input("Densidad Seca (g/cm³)", min_value=0.1, step=0.01)
                
                with col2:
                    humedad_inicial = st.number_input("Humedad Inicial (%)", min_value=0.0, step=0.1)
                    humedad_final = st.number_input("Humedad Final (%)", min_value=0.0, step=0.1)
                
                with col3:
                    dias_inmersion = st.number_input("Días de Inmersión", min_value=0, step=1, value=4)
                    sobrecarga = st.number_input("Sobrecarga (kg)", min_value=0.0, step=0.1, value=4.5)
                
                # Resultados del ensayo CBR
                st.markdown("#### Resultados")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    indice_cbr = st.number_input("Índice CBR (%)", min_value=0.0, step=0.1)
                
                with col2:
                    hinchamiento = st.number_input("Hinchamiento (%)", min_value=0.0, step=0.01)
                
                with col3:
                    absorcion_agua = st.number_input("Absorción de Agua (%)", min_value=0.0, step=0.01)
                
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
                if densidad_seca <= 0 or indice_cbr < 0:
                    st.error("La densidad seca debe ser mayor que cero y el índice CBR no puede ser negativo")
                else:
                    try:
                        # Guardar ensayo
                        ensayo_id = guardar_ensayo_cbr(
                            codigo_seleccionado, fecha_ensayo, operario_ensayo,
                            energia_compactacion, densidad_seca, humedad_inicial, humedad_final,
                            hinchamiento, indice_cbr, absorcion_agua, dias_inmersion, sobrecarga,
                            notas
                        )
                        
                        # Interpretar resultado
                        interpretacion = interpretar_resultado_cbr(indice_cbr)
                        
                        # Mostrar resultados guardados
                        st.success(f"Ensayo CBR guardado con éxito (ID: {ensayo_id})")
                        st.info(f"Interpretación: {interpretacion}")
                        
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
                        
                        # Establecer flag para mostrar resultados
                        st.session_state.mostrar_resultados = codigo_seleccionado
                        st.experimental_rerun()
                            
                    except ValueError as e:
                        st.error(f"Error en los cálculos: {str(e)}")
                    except Exception as e:
                        st.error(f"Error al procesar el ensayo: {str(e)}")
            
            # Mostrar resultados del ensayo si existe
            if "mostrar_resultados" in st.session_state and st.session_state.mostrar_resultados == codigo_seleccionado:
                ensayo = obtener_ensayo_cbr(codigo_seleccionado)
                
                if ensayo:
                    st.subheader("Resultados del Ensayo CBR")
                    
                    # Mostrar datos generales
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Fecha del ensayo:** {ensayo['fecha_ensayo']}")
                        st.write(f"**Operario:** {ensayo['operario']}")
                    
                    with col2:
                        st.write(f"**Días de inmersión:** {ensayo['dias_inmersion']}")
                        st.write(f"**Sobrecarga:** {ensayo['sobrecarga']} kg")
                    
                    # Mostrar parámetros de compactación
                    st.markdown("### Parámetros de Compactación")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Energía de Compactación", f"{ensayo['energia_compactacion']:.1f} J/m³")
                        st.metric("Densidad Seca", f"{ensayo['densidad_seca']:.2f} g/cm³")
                    
                    with col2:
                        st.metric("Humedad Inicial", f"{ensayo['humedad_inicial']:.1f}%")
                        st.metric("Humedad Final", f"{ensayo['humedad_final']:.1f}%")
                    
                    with col3:
                        st.metric("Cambio de Humedad", f"{ensayo['humedad_final'] - ensayo['humedad_inicial']:.1f}%")
                    
                    # Mostrar resultados CBR
                    st.markdown("### Resultados del Ensayo")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Índice CBR", f"{ensayo['indice_cbr']:.1f}%")
                    
                    with col2:
                        st.metric("Hinchamiento", f"{ensayo['hinchamiento']:.2f}%")
                    
                    with col3:
                        st.metric("Absorción de Agua", f"{ensayo['absorcion_agua']:.2f}%")
                    
                    # Interpretar resultado
                    interpretacion = interpretar_resultado_cbr(ensayo['indice_cbr'])
                    st.markdown("### Interpretación")
                    st.info(f"**{interpretacion}**")
                    
                    # Criterios de calidad
                    st.markdown("### Evaluación según criterios de calidad")
                    
                    # Evaluar CBR
                    if ensayo['indice_cbr'] >= 20:
                        st.success("✅ CBR adecuado para bases de pavimentos (CBR ≥ 20%)")
                    elif ensayo['indice_cbr'] >= 10:
                        st.success("✅ CBR adecuado para subbases de pavimentos (CBR ≥ 10%)")
                    elif ensayo['indice_cbr'] >= 5:
                        st.warning("⚠️ CBR adecuado solo para subrasante (5% ≤ CBR < 10%)")
                    else:
                        st.error("❌ CBR insuficiente para subrasante (CBR < 5%)")
                    
                    # Evaluar hinchamiento
                    if ensayo['hinchamiento'] <= 1.0:
                        st.success("✅ Hinchamiento dentro de límites aceptables (≤ 1.0%)")
                    elif ensayo['hinchamiento'] <= 2.0:
                        st.warning("⚠️ Hinchamiento elevado (1.0% < Hinchamiento ≤ 2.0%)")
                    else:
                        st.error("❌ Hinchamiento excesivo (> 2.0%), puede causar problemas")
                    
                    # Gráfico comparativo de CBR
                    st.markdown("### Visualización")
                    
                    # Crear gráfico de barras con valores de referencia
                    categorias = ['Subrasante\npobre', 'Subrasante\nregular', 'Subrasante\nbuena', 'Subbase', 'Base']
                    valores_ref = [3, 7, 20, 40, 80]
                    colores_ref = ['rgba(255, 99, 132, 0.5)', 'rgba(255, 159, 64, 0.5)', 
                                'rgba(255, 205, 86, 0.5)', 'rgba(75, 192, 192, 0.5)', 
                                'rgba(54, 162, 235, 0.5)']
                    
                    fig = go.Figure()
                    
                    # Añadir barras de referencia
                    fig.add_trace(go.Bar(
                        x=categorias,
                        y=valores_ref,
                        marker_color=colores_ref,
                        name='Valores de referencia'
                    ))
                    
                    # Añadir línea para el valor de CBR de la muestra
                    fig.add_trace(go.Scatter(
                        x=categorias,
                        y=[ensayo['indice_cbr']] * len(categorias),
                        mode='lines',
                        line=dict(color='red', width=2, dash='dash'),
                        name=f"CBR Muestra ({ensayo['indice_cbr']:.1f}%)"
                    ))
                    
                    # Configurar el diseño del gráfico
                    fig.update_layout(
                        title="Comparación del CBR con valores de referencia",
                        xaxis_title="Categoría",
                        yaxis_title="Índice CBR (%)",
                        yaxis_range=[0, max(max(valores_ref), ensayo['indice_cbr']) * 1.1],
                        height=500
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
                                    "Energía de Compactación (J/m³)", "Densidad Seca (g/cm³)",
                                    "Humedad Inicial (%)", "Humedad Final (%)",
                                    "Hinchamiento (%)", "Índice CBR (%)",
                                    "Absorción de Agua (%)", "Días de Inmersión",
                                    "Sobrecarga (kg)", "Interpretación"
                                ],
                                "Valor": [
                                    codigo_seleccionado, ensayo['fecha_ensayo'], ensayo['operario'],
                                    ensayo['energia_compactacion'], ensayo['densidad_seca'],
                                    ensayo['humedad_inicial'], ensayo['humedad_final'],
                                    ensayo['hinchamiento'], ensayo['indice_cbr'],
                                    ensayo['absorcion_agua'], ensayo['dias_inmersion'],
                                    ensayo['sobrecarga'], interpretacion
                                ]
                            })
                            
                            # Convertir a CSV
                            csv = export_data.to_csv(index=False)
                            
                            # Botón de descarga
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name=f"cbr_{codigo_seleccionado}.csv",
                                mime="text/csv"
                            )
                    
                    with col2:
                        # Botón para realizar otro ensayo
                        if st.button("Realizar Nuevo Ensayo"):
                            # Limpiar el estado para permitir un nuevo registro
                            if "mostrar_resultados" in st.session_state:
                                del st.session_state.mostrar_resultados
                            st.experimental_rerun()
                else:
                    st.error("No se pudo cargar la información del ensayo.")
        else:
            st.error("No se pudo cargar la información de la muestra seleccionada.")
    
    except Exception as e:
        st.error(f"Ha ocurrido un error: {str(e)}")
        st.exception(e)