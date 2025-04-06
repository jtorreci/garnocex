import streamlit as st
import pandas as pd
from datetime import datetime
import io
import plotly.graph_objects as go
from PIL import Image

from models.muestras import obtener_muestras, obtener_muestra, obtener_imagenes
from models.lajas_agujas import (guardar_ensayo_lajas_agujas, obtener_ensayo_lajas_agujas,
                               calcular_indices_lajas_agujas, interpretar_indices)

def mostrar_pagina_lajas_agujas():
    """
    Muestra la página de ensayo de índice de lajas y agujas
    """
    st.header("Ensayo de Índice de Lajas y Agujas")
    
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
            ensayo_existente = obtener_ensayo_lajas_agujas(codigo_seleccionado)
            
            if ensayo_existente:
                st.info("Esta muestra ya tiene un ensayo de índice de lajas y agujas registrado. Puede visualizarlo o registrar uno nuevo.")
                if st.button("Ver Ensayo Existente"):
                    st.session_state.mostrar_resultados = codigo_seleccionado
                    st.rerun()
            
            # Formulario de ensayo
            with st.form("formulario_lajas_agujas"):
                st.subheader("Nuevo Ensayo de Índice de Lajas y Agujas")
                
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
                    masa_total = st.number_input("Masa total de la muestra (g)", min_value=0.1, step=0.1)
                    masa_lajas = st.number_input("Masa de partículas con forma de laja (g)", min_value=0.0, step=0.1)
                
                with col2:
                    masa_agujas = st.number_input("Masa de partículas con forma de aguja (g)", min_value=0.0, step=0.1)
                    st.metric("Masa total de lajas y agujas (g)", f"{masa_lajas + masa_agujas:.1f}")
                
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
                if masa_total <= 0:
                    st.error("La masa total debe ser mayor que cero")
                elif masa_lajas < 0 or masa_agujas < 0:
                    st.error("Las masas de lajas y agujas no pueden ser negativas")
                elif masa_lajas + masa_agujas > masa_total:
                    st.error("La suma de masa de lajas y agujas no puede superar la masa total")
                else:
                    try:
                        # Calcular índices
                        indice_lajas, indice_agujas = calcular_indices_lajas_agujas(
                            masa_total, masa_lajas, masa_agujas
                        )
                        
                        # Interpretar índices
                        interpretacion_lajas, interpretacion_agujas = interpretar_indices(
                            indice_lajas, indice_agujas
                        )
                        
                        # Mostrar resultados calculados
                        st.subheader("Resultados calculados:")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Índice de Lajas", f"{indice_lajas:.1f}%")
                            st.info(interpretacion_lajas)
                        
                        with col2:
                            st.metric("Índice de Agujas", f"{indice_agujas:.1f}%")
                            st.info(interpretacion_agujas)
                        
                        # Confirmar guardar
                        if st.button("Confirmar y Guardar Resultados"):
                            # Guardar resultados en la base de datos
                            ensayo_id = guardar_ensayo_lajas_agujas(
                                codigo_seleccionado, fecha_ensayo, operario_ensayo,
                                masa_total, masa_lajas, masa_agujas,
                                indice_lajas, indice_agujas, notas
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
                            
                            st.success(f"Ensayo de índice de lajas y agujas guardado con éxito (ID: {ensayo_id})")
                            
                            # Establecer flag para mostrar resultados
                            st.session_state.mostrar_resultados = codigo_seleccionado
                            st.rerun()
                            
                    except ValueError as e:
                        st.error(f"Error en los cálculos: {str(e)}")
                    except Exception as e:
                        st.error(f"Error al procesar el ensayo: {str(e)}")
            
            # Mostrar resultados del ensayo si existe
            if "mostrar_resultados" in st.session_state and st.session_state.mostrar_resultados == codigo_seleccionado:
                ensayo = obtener_ensayo_lajas_agujas(codigo_seleccionado)
                
                if ensayo:
                    st.subheader("Resultados del Ensayo de Índice de Lajas y Agujas")
                    
                    # Mostrar datos generales
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Fecha del ensayo:** {ensayo['fecha_ensayo']}")
                        st.write(f"**Operario:** {ensayo['operario']}")
                    
                    # Mostrar masas
                    st.markdown("### Datos de Masas")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Masa Total", f"{ensayo['masa_total']:.1f} g")
                    
                    with col2:
                        st.metric("Masa de Lajas", f"{ensayo['masa_lajas']:.1f} g")
                        st.metric("% Lajas", f"{(ensayo['masa_lajas']/ensayo['masa_total']*100):.1f}%")
                    
                    with col3:
                        st.metric("Masa de Agujas", f"{ensayo['masa_agujas']:.1f} g")
                        st.metric("% Agujas", f"{(ensayo['masa_agujas']/ensayo['masa_total']*100):.1f}%")
                    
                    # Mostrar índices
                    st.markdown("### Índices Calculados")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Índice de Lajas", f"{ensayo['indice_lajas']:.1f}%")
                    
                    with col2:
                        st.metric("Índice de Agujas", f"{ensayo['indice_agujas']:.1f}%")
                    
                    # Interpretar resultados
                    interpretacion_lajas, interpretacion_agujas = interpretar_indices(
                        ensayo['indice_lajas'], ensayo['indice_agujas']
                    )
                    
                    st.markdown("### Interpretación")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Índice de Lajas:** {interpretacion_lajas}")
                    
                    with col2:
                        st.info(f"**Índice de Agujas:** {interpretacion_agujas}")
                    
                    # Evaluación según normativa
                    st.markdown("### Evaluación según Normativa UNE-EN 933-3 y 933-4")
                    
                    # Índice de lajas
                    if ensayo['indice_lajas'] <= 20:
                        st.success("✅ Índice de lajas apto para capas de rodadura (IL ≤ 20%)")
                    elif ensayo['indice_lajas'] <= 35:
                        st.success("✅ Índice de lajas apto para capas de base e intermedias (IL ≤ 35%)")
                    else:
                        st.error("❌ Índice de lajas no cumple requisitos para uso en capas de firmes (IL > 35%)")
                    
                    # Índice de agujas
                    if ensayo['indice_agujas'] <= 20:
                        st.success("✅ Índice de agujas apto para capas de rodadura (IA ≤ 20%)")
                    elif ensayo['indice_agujas'] <= 35:
                        st.success("✅ Índice de agujas apto para capas de base e intermedias (IA ≤ 35%)")
                    else:
                        st.error("❌ Índice de agujas no cumple requisitos para uso en capas de firmes (IA > 35%)")
                    
                    # Gráfico comparativo
                    st.markdown("### Visualización")
                    
                    # Crear gráfico de barras para comparar índices
                    fig = go.Figure()
                    
                    # Definir categorías y valores límite según normativa
                    categorias = ['Muy buena\nforma', 'Buena\nforma', 'Forma\naceptable', 'Mala\nforma']
                    valores_limite = [10, 20, 35, 50]
                    
                    # Añadir barras con valores límite
                    fig.add_trace(go.Bar(
                        x=categorias,
                        y=valores_limite,
                        marker_color='rgba(158, 202, 225, 0.6)',
                        name='Valores de referencia'
                    ))
                    
                    # Añadir valores de la muestra
                    fig.add_trace(go.Scatter(
                        x=categorias,
                        y=[ensayo['indice_lajas']] * len(categorias),
                        mode='lines',
                        line=dict(color='red', width=2, dash='dash'),
                        name=f"Índice de Lajas ({ensayo['indice_lajas']:.1f}%)"
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=categorias,
                        y=[ensayo['indice_agujas']] * len(categorias),
                        mode='lines',
                        line=dict(color='blue', width=2, dash='dot'),
                        name=f"Índice de Agujas ({ensayo['indice_agujas']:.1f}%)"
                    ))
                    
                    # Configurar el diseño del gráfico
                    fig.update_layout(
                        title="Comparación con valores de referencia",
                        xaxis_title="Categoría de forma",
                        yaxis_title="Índice (%)",
                        yaxis_range=[0, max(50, ensayo['indice_lajas'], ensayo['indice_agujas']) * 1.1],
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
                                    "Masa Total (g)", "Masa de Lajas (g)", "Masa de Agujas (g)",
                                    "Índice de Lajas (%)", "Índice de Agujas (%)",
                                    "Interpretación Lajas", "Interpretación Agujas"
                                ],
                                "Valor": [
                                    codigo_seleccionado, ensayo['fecha_ensayo'], ensayo['operario'],
                                    ensayo['masa_total'], ensayo['masa_lajas'], ensayo['masa_agujas'],
                                    ensayo['indice_lajas'], ensayo['indice_agujas'],
                                    interpretacion_lajas, interpretacion_agujas
                                ]
                            })
                            
                            # Convertir a CSV
                            csv = export_data.to_csv(index=False)
                            
                            # Botón de descarga
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name=f"lajas_agujas_{codigo_seleccionado}.csv",
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