import streamlit as st
import pandas as pd
from datetime import datetime
import io
import plotly.graph_objects as go
import numpy as np
from PIL import Image

from models.muestras import obtener_muestras, obtener_muestra, obtener_imagenes
from models.limites import (guardar_ensayo_limites, obtener_ensayo_limites,
                          calcular_indice_plasticidad, obtener_clasificacion_sucs)

def mostrar_pagina_limites():
    """
    Muestra la página de ensayo de límites de Atterberg
    """
    st.header("Ensayo de Límites de Atterberg")
    
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
            ensayo_existente = obtener_ensayo_limites(codigo_seleccionado)
            
            if ensayo_existente:
                st.info("Esta muestra ya tiene un ensayo de límites de Atterberg registrado. Puede visualizarlo o registrar uno nuevo.")
                if st.button("Ver Ensayo Existente"):
                    st.session_state.mostrar_resultados = codigo_seleccionado
                    st.rerun()
            
            # Formulario de ensayo
            with st.form("formulario_limites"):
                st.subheader("Nuevo Ensayo de Límites de Atterberg")
                
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
                    limite_liquido = st.number_input("Límite Líquido (%)", min_value=0.0, max_value=100.0, step=0.1)
                
                with col2:
                    limite_plastico = st.number_input("Límite Plástico (%)", min_value=0.0, max_value=100.0, step=0.1)
                
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
                if limite_liquido <= 0 or limite_plastico <= 0:
                    st.error("Los valores de límite líquido y límite plástico deben ser mayores que cero")
                elif limite_liquido < limite_plastico:
                    st.error("El límite líquido debe ser mayor o igual al límite plástico")
                else:
                    try:
                        # Calcular índice de plasticidad
                        indice_plasticidad = calcular_indice_plasticidad(limite_liquido, limite_plastico)
                        
                        # Obtener clasificación SUCS
                        clasificacion_sucs = obtener_clasificacion_sucs(limite_liquido, indice_plasticidad)
                        
                        # Mostrar resultados calculados
                        st.subheader("Resultados calculados:")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Límite Líquido (LL)", f"{limite_liquido:.1f}%")
                            st.metric("Límite Plástico (LP)", f"{limite_plastico:.1f}%")
                        with col2:
                            st.metric("Índice de Plasticidad (IP)", f"{indice_plasticidad:.1f}%")
                            st.info(f"Clasificación SUCS: {clasificacion_sucs}")
                        
                        # Gráfico de Carta de Plasticidad
                        st.subheader("Carta de Plasticidad de Casagrande")
                        figura_carta = crear_carta_plasticidad(limite_liquido, indice_plasticidad)
                        st.plotly_chart(figura_carta, use_container_width=True)
                        
                        # Confirmar guardar
                        if st.button("Confirmar y Guardar Resultados"):
                            # Guardar resultados en la base de datos
                            ensayo_id = guardar_ensayo_limites(
                                codigo_seleccionado, fecha_ensayo, operario_ensayo,
                                limite_liquido, limite_plastico, indice_plasticidad,
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
                            
                            st.success(f"Ensayo de límites de Atterberg guardado con éxito (ID: {ensayo_id})")
                            
                            # Establecer flag para mostrar resultados
                            st.session_state.mostrar_resultados = codigo_seleccionado
                            st.rerun()
                            
                    except ValueError as e:
                        st.error(f"Error en los cálculos: {str(e)}")
                    except Exception as e:
                        st.error(f"Error al procesar el ensayo: {str(e)}")
            
            # Mostrar resultados del ensayo si existe
            if "mostrar_resultados" in st.session_state and st.session_state.mostrar_resultados == codigo_seleccionado:
                ensayo = obtener_ensayo_limites(codigo_seleccionado)
                
                if ensayo:
                    st.subheader("Resultados del Ensayo de Límites de Atterberg")
                    
                    # Mostrar datos generales
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Fecha del ensayo:** {ensayo['fecha_ensayo']}")
                        st.write(f"**Operario:** {ensayo['operario']}")
                    
                    # Mostrar parámetros calculados
                    st.markdown("### Resultados")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Límite Líquido (LL)", f"{ensayo['limite_liquido']:.1f}%")
                    
                    with col2:
                        st.metric("Límite Plástico (LP)", f"{ensayo['limite_plastico']:.1f}%")
                    
                    with col3:
                        st.metric("Índice de Plasticidad (IP)", f"{ensayo['indice_plasticidad']:.1f}%")
                    
                    # Obtener y mostrar clasificación SUCS
                    clasificacion_sucs = obtener_clasificacion_sucs(
                        ensayo['limite_liquido'], 
                        ensayo['indice_plasticidad']
                    )
                    
                    st.info(f"**Clasificación SUCS:** {clasificacion_sucs}")
                    
                    # Gráfico de Carta de Plasticidad
                    st.markdown("### Carta de Plasticidad de Casagrande")
                    figura_carta = crear_carta_plasticidad(
                        ensayo['limite_liquido'], 
                        ensayo['indice_plasticidad']
                    )
                    st.plotly_chart(figura_carta, use_container_width=True)
                    
                    # Interpretación del resultado
                    st.markdown("### Interpretación")
                    
                    if ensayo['indice_plasticidad'] < 4:
                        st.write("**Suelo no plástico o de baja plasticidad**")
                        st.write("Este suelo se comporta principalmente como un limo, con poca o ninguna cohesión.")
                    elif ensayo['indice_plasticidad'] < 7:
                        st.write("**Suelo de baja plasticidad**")
                        st.write("Este suelo tiene una cohesión limitada y se comporta de manera similar a un limo arcilloso.")
                    elif ensayo['indice_plasticidad'] < 15:
                        st.write("**Suelo de plasticidad media**")
                        st.write("Este suelo tiene propiedades intermedias, con cohesión moderada.")
                    else:
                        st.write("**Suelo de alta plasticidad**")
                        st.write("Este suelo tiene una alta cohesión y presenta comportamiento arcilloso significativo.")
                    
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
                                    "Límite Líquido (%)", "Límite Plástico (%)",
                                    "Índice de Plasticidad (%)", "Clasificación SUCS"
                                ],
                                "Valor": [
                                    codigo_seleccionado, ensayo['fecha_ensayo'], ensayo['operario'],
                                    ensayo['limite_liquido'], ensayo['limite_plastico'],
                                    ensayo['indice_plasticidad'], clasificacion_sucs
                                ]
                            })
                            
                            # Convertir a CSV
                            csv = export_data.to_csv(index=False)
                            
                            # Botón de descarga
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name=f"limites_atterberg_{codigo_seleccionado}.csv",
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

def crear_carta_plasticidad(ll, ip):
    """
    Crea un gráfico de la Carta de Plasticidad de Casagrande con el punto de la muestra
    
    Args:
        ll (float): Límite líquido
        ip (float): Índice de plasticidad
        
    Returns:
        plotly.graph_objects.Figure: Figura con la carta de plasticidad
    """
    # Crear figura
    fig = go.Figure()
    
    # Datos para las líneas de la carta
    ll_valores = np.linspace(0, 100, 100)
    
    # Línea A: IP = 0.73 * (LL - 20)
    ip_linea_a = 0.73 * (ll_valores - 20)
    ip_linea_a[ip_linea_a < 0] = 0
    
    # Línea U: IP = 0.9 * (LL - 8)
    ip_linea_u = 0.9 * (ll_valores - 8)
    ip_linea_u[ip_linea_u < 0] = 0
    
    # Añadir líneas
    fig.add_trace(go.Scatter(
        x=ll_valores, y=ip_linea_a,
        mode='lines', name='Línea A: IP = 0.73(LL-20)',
        line=dict(color='black', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=ll_valores, y=ip_linea_u,
        mode='lines', name='Línea U: IP = 0.9(LL-8)',
        line=dict(color='black', width=2, dash='dash')
    ))
    
    # Línea vertical en LL = 50
    fig.add_trace(go.Scatter(
        x=[50, 50], y=[0, 60],
        mode='lines', name='LL = 50',
        line=dict(color='black', width=1.5, dash='dot')
    ))
    
    # Añadir áreas para los diferentes tipos de suelo
    # CL - Arcilla de baja plasticidad
    x_cl = ll_valores[ll_valores <= 50]
    y1_cl = np.zeros_like(x_cl)
    y2_cl = ip_linea_a[ll_valores <= 50]
    fig.add_trace(go.Scatter(
        x=list(x_cl) + list(x_cl)[::-1],
        y=list(y2_cl) + list(y1_cl)[::-1],
        fill='toself',
        fillcolor='rgba(144, 238, 144, 0.5)',
        line=dict(color='rgba(144, 238, 144, 0)'),
        name='CL - Arcilla de baja plasticidad',
        hoverinfo='name'
    ))
    
    # ML - Limo de baja plasticidad
    fig.add_trace(go.Scatter(
        x=[0, 20, 50, 50, 0],
        y=[0, 0, 0, 7, 7],
        fill='toself',
        fillcolor='rgba(255, 235, 205, 0.5)',
        line=dict(color='rgba(255, 235, 205, 0)'),
        name='ML - Limo de baja plasticidad',
        hoverinfo='name'
    ))
    
    # CL-ML - Arcilla limosa de baja plasticidad
    x_cl_ml = ll_valores[(ll_valores >= 20) & (ll_valores <= 50)]
    y1_cl_ml = np.zeros_like(x_cl_ml) + 7
    y2_cl_ml = ip_linea_a[(ll_valores >= 20) & (ll_valores <= 50)]
    fig.add_trace(go.Scatter(
        x=list(x_cl_ml) + list(x_cl_ml)[::-1],
        y=list(y2_cl_ml) + list(y1_cl_ml)[::-1],
        fill='toself',
        fillcolor='rgba(152, 251, 152, 0.5)',
        line=dict(color='rgba(152, 251, 152, 0)'),
        name='CL-ML - Arcilla limosa de baja plasticidad',
        hoverinfo='name'
    ))
    
    # CH - Arcilla de alta plasticidad
    x_ch = ll_valores[ll_valores >= 50]
    y1_ch = np.zeros_like(x_ch)
    y2_ch = ip_linea_a[ll_valores >= 50]
    fig.add_trace(go.Scatter(
        x=list(x_ch) + list(x_ch)[::-1],
        y=list(y2_ch) + list(y1_ch)[::-1],
        fill='toself',
        fillcolor='rgba(255, 160, 122, 0.5)',
        line=dict(color='rgba(255, 160, 122, 0)'),
        name='CH - Arcilla de alta plasticidad',
        hoverinfo='name'
    ))
    
    # MH - Limo de alta plasticidad
    fig.add_trace(go.Scatter(
        x=[50, 100, 100, 50],
        y=[0, 0, 60, 60],
        fill='toself',
        fillcolor='rgba(222, 184, 135, 0.5)',
        line=dict(color='rgba(222, 184, 135, 0)'),
        name='MH - Limo de alta plasticidad',
        hoverinfo='name'
    ))
    
    # Punto de la muestra
    fig.add_trace(go.Scatter(
        x=[ll], y=[ip],
        mode='markers',
        marker=dict(size=12, color='red', symbol='circle'),
        name=f'Muestra (LL={ll:.1f}, IP={ip:.1f})'
    ))
    
    # Configurar ejes y título
    fig.update_layout(
        title='Carta de Plasticidad de Casagrande',
        xaxis_title='Límite Líquido (LL)',
        yaxis_title='Índice de Plasticidad (IP)',
        xaxis=dict(range=[0, 100]),
        yaxis=dict(range=[0, 60]),
        legend=dict(x=0.01, y=0.99),
        width=800,
        height=600
    )
    
    return fig