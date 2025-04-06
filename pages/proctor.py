import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import plotly.graph_objects as go
from PIL import Image

from models.muestras import obtener_muestras, obtener_muestra, obtener_imagenes, guardar_imagen_ensayo
from models.proctor import (guardar_ensayo_proctor, obtener_ensayo_proctor, 
                          ajustar_curva_proctor, obtener_parametros_proctor)

def mostrar_pagina_proctor():
    """
    Muestra la página de ensayo Próctor
    """
    st.header("Ensayo Próctor")
    
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
            ensayo_existente = obtener_ensayo_proctor(codigo_seleccionado)
            
            if ensayo_existente:
                st.info("Esta muestra ya tiene un ensayo Próctor registrado. Puede visualizarlo o registrar uno nuevo.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Ver Ensayo Existente", use_container_width=True):
                        st.session_state.mostrar_resultados = codigo_seleccionado
                        st.rerun()
                with col2:
                    if st.button("Nuevo Ensayo", use_container_width=True):
                        st.session_state.mostrar_formulario = True
                        st.rerun()
            else:
                st.session_state.mostrar_formulario = True
            
            # Mostrar formulario de ensayo
            if st.session_state.get('mostrar_formulario', False):
                with st.form("formulario_proctor"):
                    st.subheader("Nuevo Ensayo Próctor")
                    
                    # Datos generales del ensayo
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        operario_ensayo = st.text_input("Operario", value=muestra['operario'])
                    
                    with col2:
                        fecha_ensayo = st.date_input("Fecha del Ensayo", value=datetime.now().date())
                    
                    # Tipo de Próctor
                    tipo_proctor = st.selectbox(
                        "Tipo de Próctor",
                        options=["Normal", "Modificado"]
                    )
                    
                    # Cargar parámetros estándar según el tipo
                    parametros_proctor = obtener_parametros_proctor(tipo_proctor)
                    
                    # Datos específicos del ensayo
                    st.markdown("### Parámetros del Ensayo")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        energia_compactacion = st.number_input(
                            "Energía de Compactación (J/m³)", 
                            min_value=0.1, 
                            step=0.1, 
                            value=parametros_proctor["energia_compactacion"]
                        )
                    
                    with col2:
                        numero_capas = st.number_input(
                            "Número de Capas", 
                            min_value=1, 
                            step=1, 
                            value=parametros_proctor["numero_capas"]
                        )
                    
                    with col3:
                        golpes_capa = st.number_input(
                            "Golpes por Capa", 
                            min_value=1, 
                            step=1, 
                            value=parametros_proctor["golpes_capa"]
                        )
                    
                    # Datos de puntos de la curva
                    st.markdown("### Puntos de la Curva Próctor")
                    st.info("Ingrese los datos de humedad y densidad seca para cada punto de la curva.")
                    
                    num_puntos = st.number_input("Número de Puntos", min_value=3, max_value=10, value=5, step=1)
                    
                    # Crear tabla editable para los puntos
                    puntos_data = []
                    
                    for i in range(int(num_puntos)):
                        col1, col2 = st.columns(2)
                        with col1:
                            humedad = st.number_input(
                                f"Humedad Punto {i+1} (%)", 
                                min_value=0.0, 
                                max_value=100.0, 
                                step=0.1,
                                key=f"humedad_{i}"
                            )
                        
                        with col2:
                            densidad_seca = st.number_input(
                                f"Densidad Seca Punto {i+1} (g/cm³)", 
                                min_value=0.1, 
                                max_value=3.0, 
                                step=0.01,
                                key=f"densidad_{i}"
                            )
                        
                        puntos_data.append({
                            "numero_punto": i+1,
                            "humedad": humedad,
                            "densidad_seca": densidad_seca
                        })
                    
                    # Campo para notas adicionales
                    notas = st.text_area("Notas y Observaciones")
                    
                    # Imágenes del ensayo
                    st.markdown("### Imágenes del Ensayo (opcional)")
                    archivos_imagenes = st.file_uploader(
                        "Cargar imágenes del ensayo",
                        accept_multiple_files=True,
                        type=["png", "jpg", "jpeg"]
                    )
                    
                    submitted = st.form_submit_button("Calcular y Guardar")
                
                # Procesar el formulario
                if submitted:
                    if len(puntos_data) < 3:
                        st.error("Se requieren al menos 3 puntos para ajustar la curva Próctor")
                    else:
                        # Verificar que los puntos tienen valores válidos
                        datos_validos = True
                        for punto in puntos_data:
                            if punto["humedad"] <= 0 or punto["densidad_seca"] <= 0:
                                st.error("Todos los valores de humedad y densidad deben ser mayores que cero")
                                datos_validos = False
                                break
                        
                        if datos_validos:
                            try:
                                # Ajustar curva para determinar densidad máxima y humedad óptima
                                try:
                                    densidad_maxima, humedad_optima = ajustar_curva_proctor(puntos_data)
                                    
                                    if densidad_maxima <= 0 or humedad_optima <= 0:
                                        st.error("No se pudo determinar correctamente la densidad máxima y humedad óptima. Revisando puntos...")
                                        # Usar el punto con mayor densidad como aproximación
                                        densidad_maxima = max(punto["densidad_seca"] for punto in puntos_data)
                                        idx_max = next(i for i, p in enumerate(puntos_data) if p["densidad_seca"] == densidad_maxima)
                                        humedad_optima = puntos_data[idx_max]["humedad"]
                                        st.warning(f"Se usó el punto con mayor densidad como aproximación (punto {idx_max+1}).")
                                    
                                    # Mostrar resultados calculados
                                    st.subheader("Resultados calculados:")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Densidad Seca Máxima", f"{densidad_maxima:.3f} g/cm³")
                                    
                                    with col2:
                                        st.metric("Humedad Óptima", f"{humedad_optima:.1f}%")
                                    
                                    # Gráfica de la curva
                                    fig = generar_grafica_proctor(puntos_data, densidad_maxima, humedad_optima)
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Confirmar guardar
                                    if st.button("Confirmar y Guardar Resultados"):
                                        # Guardar resultados en la base de datos
                                        ensayo_id = guardar_ensayo_proctor(
                                            codigo_seleccionado, fecha_ensayo, operario_ensayo,
                                            tipo_proctor, densidad_maxima, humedad_optima,
                                            energia_compactacion, numero_capas, golpes_capa,
                                            puntos_data, notas
                                        )
                                        
                                        # Guardar imágenes si hay
                                        imagenes_guardadas = 0
                                        for archivo in archivos_imagenes:
                                            try:
                                                img = Image.open(archivo)
                                                guardar_imagen_ensayo(
                                                    codigo_seleccionado, 
                                                    ensayo_id, 
                                                    img, 
                                                    archivo.name,
                                                    f"Imagen de ensayo Próctor - {archivo.name}"
                                                )
                                                imagenes_guardadas += 1
                                            except Exception as e:
                                                st.error(f"Error al guardar imagen {archivo.name}: {str(e)}")
                                        
                                        if imagenes_guardadas > 0:
                                            st.success(f"Se guardaron {imagenes_guardadas} imágenes")
                                        
                                        st.success(f"Ensayo Próctor guardado con éxito (ID: {ensayo_id})")
                                        
                                        # Establecer flag para mostrar resultados
                                        st.session_state.mostrar_resultados = codigo_seleccionado
                                        st.session_state.mostrar_formulario = False
                                        st.rerun()
                                
                                except Exception as e:
                                    st.error(f"Error al ajustar la curva Próctor: {str(e)}")
                                
                            except ValueError as e:
                                st.error(f"Error en los cálculos: {str(e)}")
                            except Exception as e:
                                st.error(f"Error al procesar el ensayo: {str(e)}")
            
            # Mostrar resultados del ensayo si existe
            if "mostrar_resultados" in st.session_state and st.session_state.mostrar_resultados == codigo_seleccionado:
                ensayo = obtener_ensayo_proctor(codigo_seleccionado)
                
                if ensayo:
                    st.subheader("Resultados del Ensayo Próctor")
                    
                    # Mostrar datos generales
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Fecha del ensayo:** {ensayo['fecha_ensayo']}")
                        st.write(f"**Operario:** {ensayo['operario']}")
                    
                    with col2:
                        st.write(f"**Tipo Próctor:** {ensayo['tipo_proctor']}")
                        st.write(f"**Capas:** {ensayo['numero_capas']}")
                    
                    with col3:
                        st.write(f"**Golpes por capa:** {ensayo['golpes_capa']}")
                        st.write(f"**Energía de compactación:** {ensayo['energia_compactacion']:.2f} J/cm³")
                    
                    # Mostrar resultados principales
                    st.markdown("### Resultados Principales")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Densidad Seca Máxima", f"{ensayo['densidad_maxima']:.3f} g/cm³")
                    
                    with col2:
                        st.metric("Humedad Óptima", f"{ensayo['humedad_optima']:.1f}%")
                    
                    # Mostrar datos de los puntos
                    st.markdown("### Puntos de la Curva")
                    
                    # Crear DataFrame con los puntos
                    df_puntos = pd.DataFrame([
                        {
                            "Punto": p["numero_punto"],
                            "Humedad (%)": p["humedad"],
                            "Densidad Seca (g/cm³)": p["densidad_seca"]
                        }
                        for p in ensayo['puntos']
                    ])
                    
                    st.dataframe(df_puntos, use_container_width=True)
                    
                    # Gráfica de la curva
                    fig = generar_grafica_proctor(ensayo['puntos'], ensayo['densidad_maxima'], ensayo['humedad_optima'])
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Evaluación según tipo de suelo
                    st.markdown("### Evaluación")
                    
                    # Evaluación de la densidad máxima según el tipo de material
                    if muestra['tipo_material'].lower() in ['suelo', 'arena', 'arcilla']:
                        tipo_suelo = muestra['tipo_material'].lower()
                    else:
                        tipo_suelo = 'suelo'
                    
                    if tipo_suelo == 'arena':
                        if ensayo['densidad_maxima'] < 1.6:
                            st.warning("⚠️ Densidad máxima baja para arena (< 1.6 g/cm³)")
                        elif ensayo['densidad_maxima'] < 1.9:
                            st.success("✅ Densidad máxima normal para arena (1.6 - 1.9 g/cm³)")
                        else:
                            st.success("✅ Densidad máxima alta para arena (> 1.9 g/cm³)")
                    elif tipo_suelo == 'arcilla':
                        if ensayo['densidad_maxima'] < 1.5:
                            st.warning("⚠️ Densidad máxima baja para arcilla (< 1.5 g/cm³)")
                        elif ensayo['densidad_maxima'] < 1.8:
                            st.success("✅ Densidad máxima normal para arcilla (1.5 - 1.8 g/cm³)")
                        else:
                            st.success("✅ Densidad máxima alta para arcilla (> 1.8 g/cm³)")
                    else:  # suelo genérico
                        if ensayo['densidad_maxima'] < 1.5:
                            st.warning("⚠️ Densidad máxima baja (< 1.5 g/cm³)")
                        elif ensayo['densidad_maxima'] < 1.8:
                            st.success("✅ Densidad máxima normal (1.5 - 1.8 g/cm³)")
                        else:
                            st.success("✅ Densidad máxima alta (> 1.8 g/cm³)")
                    
                    # Evaluación de la humedad óptima
                    if ensayo['humedad_optima'] < 5:
                        st.info("Humedad óptima muy baja (< 5%), típica de suelos granulares")
                    elif ensayo['humedad_optima'] < 15:
                        st.info("Humedad óptima normal (5% - 15%)")
                    else:
                        st.info("Humedad óptima alta (> 15%), típica de suelos arcillosos")
                    
                    # Verificar grado de compactación para diferentes aplicaciones
                    st.markdown("### Grado de Compactación Recomendado")
                    
                    st.markdown("""
                    | Aplicación | Grado de Compactación (% Próctor) |
                    |------------|----------------------------------|
                    | Rellenos no estructurales | 90% - 95% |
                    | Terraplenes | 95% - 98% |
                    | Bases de pavimentos | 98% - 100% |
                    | Núcleos de presas | 98% - 100% |
                    """)
                    
                    # Mostrar imágenes asociadas al ensayo
                    try:
                        imagenes = obtener_imagenes(codigo_seleccionado, ensayo['id'])
                        if imagenes:
                            st.markdown("### Imágenes del Ensayo")
                            cols = st.columns(min(3, len(imagenes)))
                            for i, (img_id, img, nombre, fecha, desc) in enumerate(imagenes):
                                with cols[i % 3]:
                                    st.image(img, caption=nombre)
                    except Exception as e:
                        st.error(f"Error al cargar imágenes: {str(e)}")
                    
                    # Mostrar notas
                    if ensayo['notas']:
                        st.markdown("### Notas del Ensayo")
                        st.info(ensayo['notas'])
                    
                    # Opciones adicionales
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Botón para exportar resultados
                        if st.button("Exportar Resultados (CSV)", use_container_width=True):
                            # Crear DataFrame para exportar
                            export_data = pd.DataFrame({
                                "Parámetro": [
                                    "Código Muestra", "Fecha Ensayo", "Operario",
                                    "Tipo Próctor", "Densidad Máxima (g/cm³)", "Humedad Óptima (%)",
                                    "Energía Compactación (J/cm³)", "Número Capas", "Golpes por Capa"
                                ],
                                "Valor": [
                                    codigo_seleccionado, ensayo['fecha_ensayo'], ensayo['operario'],
                                    ensayo['tipo_proctor'], ensayo['densidad_maxima'], ensayo['humedad_optima'],
                                    ensayo['energia_compactacion'], ensayo['numero_capas'], ensayo['golpes_capa']
                                ]
                            })
                            
                            # Convertir a CSV
                            csv = export_data.to_csv(index=False)
                            
                            # Botón de descarga
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name=f"proctor_{codigo_seleccionado}.csv",
                                mime="text/csv"
                            )
                    
                    with col2:
                        # Botón para realizar otro ensayo
                        if st.button("Realizar Nuevo Ensayo", use_container_width=True):
                            # Limpiar el estado para permitir un nuevo registro
                            if "mostrar_resultados" in st.session_state:
                                del st.session_state.mostrar_resultados
                            st.session_state.mostrar_formulario = True
                            st.rerun()
                else:
                    st.error("No se pudo cargar la información del ensayo.")
        else:
            st.error("No se pudo cargar la información de la muestra seleccionada.")
    
    except Exception as e:
        st.error(f"Ha ocurrido un error: {str(e)}")
        st.exception(e)

def generar_grafica_proctor(puntos_data, densidad_maxima, humedad_optima):
    """
    Genera un gráfico de la curva Próctor
    
    Args:
        puntos_data (list): Lista de diccionarios con los puntos (humedad, densidad_seca)
        densidad_maxima (float): Densidad seca máxima calculada
        humedad_optima (float): Humedad óptima calculada
        
    Returns:
        plotly.graph_objects.Figure: Figura con la curva Próctor
    """
    # Extraer datos de los puntos
    humedades = [p["humedad"] for p in puntos_data]
    densidades = [p["densidad_seca"] for p in puntos_data]
    
    # Ordenar por humedad creciente
    puntos_ordenados = sorted(zip(humedades, densidades), key=lambda p: p[0])
    humedades_ord = [p[0] for p in puntos_ordenados]
    densidades_ord = [p[1] for p in puntos_ordenados]
    
    # Crear figura
    fig = go.Figure()
    
    # Añadir puntos experimentales
    fig.add_trace(go.Scatter(
        x=humedades,
        y=densidades,
        mode='markers',
        name='Puntos experimentales',
        marker=dict(
            size=10,
            color='blue',
            symbol='circle'
        )
    ))
    
    # Ajustar curva suave (parábola)
    if len(puntos_data) >= 3:
        try:
            # Crear un rango de humedades para la curva ajustada
            humidity_range = np.linspace(min(humedades) - 1, max(humedades) + 1, 100)
            
            # Ajustar coeficientes del polinomio (parábola)
            coeffs = np.polyfit(humedades, densidades, 2)
            poly = np.poly1d(coeffs)
            
            # Añadir curva ajustada
            fig.add_trace(go.Scatter(
                x=humidity_range,
                y=poly(humidity_range),
                mode='lines',
                name='Curva ajustada',
                line=dict(color='rgba(0, 0, 255, 0.5)', width=2)
            ))
        except:
            # Si hay error en el ajuste, conectar puntos con líneas rectas
            fig.add_trace(go.Scatter(
                x=humedades_ord,
                y=densidades_ord,
                mode='lines',
                name='Línea unión puntos',
                line=dict(color='rgba(0, 0, 255, 0.5)', width=2)
            ))
    
    # Añadir punto de densidad máxima
    fig.add_trace(go.Scatter(
        x=[humedad_optima],
        y=[densidad_maxima],
        mode='markers',
        name=f'Punto óptimo ({humedad_optima:.1f}%, {densidad_maxima:.3f} g/cm³)',
        marker=dict(
            size=12,
            color='red',
            symbol='star'
        )
    ))
    
    # Añadir líneas de referencia al punto óptimo
    fig.add_shape(
        type="line",
        x0=humedad_optima,
        y0=0,
        x1=humedad_optima,
        y1=densidad_maxima,
        line=dict(
            color="red",
            width=1,
            dash="dash",
        )
    )
    
    fig.add_shape(
        type="line",
        x0=min(humedades) - 1,
        y0=densidad_maxima,
        x1=humedad_optima,
        y1=densidad_maxima,
        line=dict(
            color="red",
            width=1,
            dash="dash",
        )
    )
    
    # Configurar el diseño del gráfico
    fig.update_layout(
        title="Curva Próctor",
        xaxis_title="Humedad (%)",
        yaxis_title="Densidad Seca (g/cm³)",
        xaxis=dict(
            range=[min(humedades) - 1, max(humedades) + 1],
            zeroline=True
        ),
        yaxis=dict(
            range=[min(densidades) * 0.95, max(densidades) * 1.05],
            zeroline=True
        ),
        height=600,
        showlegend=True
    )
    
    return fig