import streamlit as st
import pandas as pd
from datetime import datetime
import io
import plotly.graph_objects as go
from PIL import Image

from models.muestras import obtener_muestras, obtener_muestra, obtener_imagenes
from models.equivalente_arena import (guardar_ensayo_equivalente_arena, obtener_ensayo_equivalente_arena, 
                                    calcular_equivalente_arena, interpretar_equivalente_arena)

def mostrar_pagina_equivalente_arena():
    """
    Muestra la página de ensayo de equivalente de arena
    """
    st.header("Ensayo de Equivalente de Arena")
    
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
            ensayo_existente = obtener_ensayo_equivalente_arena(codigo_seleccionado)
            
            if ensayo_existente:
                st.info("Esta muestra ya tiene un ensayo de equivalente de arena registrado. Puede visualizarlo o registrar uno nuevo.")
                if st.button("Ver Ensayo Existente"):
                    st.session_state.mostrar_resultados = codigo_seleccionado
                    st.rerun()
            
            # Formulario de ensayo
            with st.form("formulario_equivalente_arena"):
                st.subheader("Nuevo Ensayo de Equivalente de Arena")
                
                # Datos generales del ensayo
                col1, col2 = st.columns(2)
                
                with col1:
                    operario_ensayo = st.text_input("Operario", value=muestra['operario'])
                
                with col2:
                    fecha_ensayo = st.date_input("Fecha del Ensayo", value=datetime.now().date())
                
                # Datos específicos del ensayo
                st.markdown("### Datos del Ensayo")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    altura_sedimento = st.number_input("Altura del sedimento (mm)", min_value=0.1, step=0.1)
                
                with col2:
                    altura_floculos = st.number_input("Altura de los flóculos (mm)", min_value=0.1, step=0.1)
                
                with col3:
                    temperatura = st.number_input("Temperatura (°C)", min_value=0.0, step=0.1, value=20.0)
                
                # Cálculo automático del equivalente de arena
                if altura_sedimento > 0 and altura_floculos > 0:
                    if altura_sedimento > altura_floculos:
                        st.error("La altura del sedimento no puede ser mayor que la altura de los flóculos")
                        equivalente_arena_valor = 0
                    else:
                        equivalente_arena_valor = calcular_equivalente_arena(altura_sedimento, altura_floculos)
                        st.metric("Equivalente de Arena (EA)", f"{equivalente_arena_valor}%")
                        
                        # Interpretación del resultado
                        clasificacion, recomendacion = interpretar_equivalente_arena(equivalente_arena_valor)
                        st.info(f"**Clasificación:** {clasificacion}\n\n**Recomendación:** {recomendacion}")
                else:
                    equivalente_arena_valor = 0
                
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
                if altura_sedimento <= 0 or altura_floculos <= 0:
                    st.error("Las alturas deben ser mayores que cero")
                elif altura_sedimento > altura_floculos:
                    st.error("La altura del sedimento no puede ser mayor que la altura de los flóculos")
                else:
                    try:
                        # Calcular equivalente de arena
                        equivalente_arena_valor = calcular_equivalente_arena(altura_sedimento, altura_floculos)
                        
                        # Guardar ensayo
                        ensayo_id = guardar_ensayo_equivalente_arena(
                            codigo_seleccionado, fecha_ensayo, operario_ensayo,
                            altura_sedimento, altura_floculos, equivalente_arena_valor,
                            temperatura, notas
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
                        
                        st.success(f"Ensayo de equivalente de arena guardado con éxito (ID: {ensayo_id})")
                        
                        # Establecer flag para mostrar resultados
                        st.session_state.mostrar_resultados = codigo_seleccionado
                        st.rerun()
                            
                    except ValueError as e:
                        st.error(f"Error en los cálculos: {str(e)}")
                    except Exception as e:
                        st.error(f"Error al procesar el ensayo: {str(e)}")
            
            # Mostrar resultados del ensayo si existe
            if "mostrar_resultados" in st.session_state and st.session_state.mostrar_resultados == codigo_seleccionado:
                ensayo = obtener_ensayo_equivalente_arena(codigo_seleccionado)
                
                if ensayo:
                    st.subheader("Resultados del Ensayo de Equivalente de Arena")
                    
                    # Mostrar datos generales
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Fecha del ensayo:** {ensayo['fecha_ensayo']}")
                        st.write(f"**Operario:** {ensayo['operario']}")
                    
                    with col2:
                        st.write(f"**Temperatura:** {ensayo['temperatura']}°C")
                    
                    # Mostrar resultados
                    st.markdown("### Resultados del Ensayo")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Altura de Sedimento", f"{ensayo['altura_sedimento']:.1f} mm")
                    
                    with col2:
                        st.metric("Altura de Flóculos", f"{ensayo['altura_floculos']:.1f} mm")
                    
                    with col3:
                        st.metric("Equivalente de Arena (EA)", f"{ensayo['equivalente_arena']}%")
                    
                    # Interpretar resultados
                    clasificacion, recomendacion = interpretar_equivalente_arena(ensayo['equivalente_arena'])
                    
                    st.markdown("### Interpretación")
                    st.info(f"**Clasificación:** {clasificacion}\n\n**Recomendación:** {recomendacion}")
                    
                    # Evaluación según norma PG-3
                    st.markdown("### Evaluación según Norma PG-3")
                    
                    # Criterios según capas
                    if ensayo['equivalente_arena'] >= 50:
                        st.success("✅ EA ≥ 50: Apto para la mayoría de usos en obra civil")
                        
                        if ensayo['equivalente_arena'] >= 70:
                            st.success("✅ EA ≥ 70: Cumple requisitos para capas de rodadura")
                        else:
                            st.info("ℹ️ 50 ≤ EA < 70: Cumple para capas intermedias pero no para rodadura")
                    
                    elif ensayo['equivalente_arena'] >= 40:
                        st.warning("⚠️ 40 ≤ EA < 50: Limitado a algunas capas de firmes y ciertas aplicaciones")
                    
                    elif ensayo['equivalente_arena'] >= 30:
                        st.warning("⚠️ 30 ≤ EA < 40: Uso muy limitado, verificar requisitos específicos")
                    
                    else:
                        st.error("❌ EA < 30: No recomendado para capas de firmes")
                    
                    # Gráfico comparativo
                    st.markdown("### Visualización")
                    
                    # Crear gráfico de barras con valores de referencia
                    fig = go.Figure()
                    
                    # Definir categorías y valores de referencia
                    categorias = ['No apto', 'Uso limitado', 'Apto para\ncapas intermedias', 'Apto para\ncapas de rodadura']
                    valores_ref = [15, 35, 50, 70]
                    colores_ref = ['rgba(255, 99, 132, 0.6)', 'rgba(255, 159, 64, 0.6)', 
                                'rgba(75, 192, 192, 0.6)', 'rgba(54, 162, 235, 0.6)']
                    
                    # Añadir barras de referencia
                    fig.add_trace(go.Bar(
                        x=categorias,
                        y=valores_ref,
                        marker_color=colores_ref,
                        name='Valores de referencia'
                    ))
                    
                    # Añadir línea para el valor de la muestra
                    fig.add_trace(go.Scatter(
                        x=categorias,
                        y=[ensayo['equivalente_arena']] * len(categorias),
                        mode='lines',
                        line=dict(color='red', width=2, dash='dash'),
                        name=f"Muestra EA = {ensayo['equivalente_arena']}%"
                    ))
                    
                    # Configurar el diseño del gráfico
                    fig.update_layout(
                        title="Comparación con valores de referencia PG-3",
                        xaxis_title="Categoría",
                        yaxis_title="Equivalente de Arena (%)",
                        yaxis_range=[0, 100],
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
                                    "Altura Sedimento (mm)", "Altura Flóculos (mm)",
                                    "Equivalente de Arena (%)", "Temperatura (°C)",
                                    "Clasificación", "Recomendación"
                                ],
                                "Valor": [
                                    codigo_seleccionado, ensayo['fecha_ensayo'], ensayo['operario'],
                                    ensayo['altura_sedimento'], ensayo['altura_floculos'],
                                    ensayo['equivalente_arena'], ensayo['temperatura'],
                                    clasificacion, recomendacion
                                ]
                            })
                            
                            # Convertir a CSV
                            csv = export_data.to_csv(index=False)
                            
                            # Botón de descarga
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name=f"equivalente_arena_{codigo_seleccionado}.csv",
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