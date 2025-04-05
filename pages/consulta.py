import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

from models.muestras import obtener_muestras, obtener_muestra, obtener_imagenes
from models.granulometria import obtener_ensayo_granulometrico
from utils.graficos import generar_grafico_granulometrico

def mostrar_pagina_consulta():
    """
    Muestra la página de consulta de resultados
    """
    st.header("Consulta de Resultados")
    
    try:
        # Obtener lista de muestras
        muestras = obtener_muestras()
        
        if not muestras:
            st.warning("No hay muestras registradas en el sistema.")
            if st.button("Ir a Registro de Muestras"):
                st.session_state.pagina_actual = "Registro de Muestras"
                st.experimental_rerun()
            return
        
        # Convertir a DataFrame para facilitar el filtrado
        df_muestras = pd.DataFrame([
            {
                "codigo_muestra": m.get("codigo_muestra", ""),
                "operario": m.get("operario", ""),
                "fecha": m.get("fecha", ""),
                "tipo_material": m.get("tipo_material", ""),
                "estado": m.get("estado", "")
            }
            for m in muestras
        ])
        
        # Convertir fecha a datetime para filtrado
        try:
            df_muestras['fecha'] = pd.to_datetime(df_muestras['fecha'])
        except:
            # Si hay error en la conversión, intentamos con un formato específico
            pass
            
        # --- SECCIÓN DE FILTROS ---
        st.subheader("Filtros")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por operario
            operarios = ["Todos"] + sorted(df_muestras['operario'].unique().tolist())
            operario_filtro = st.selectbox(
                "Filtrar por Operario:",
                options=operarios
            )
        
        with col2:
            # Filtro por fecha inicio
            try:
                fecha_min = df_muestras['fecha'].min().date()
                fecha_max = df_muestras['fecha'].max().date()
            except:
                # Si hay error, usamos fechas por defecto
                fecha_min = datetime.now().date()
                fecha_max = datetime.now().date()
                
            fecha_inicio = st.date_input(
                "Fecha Inicio:",
                value=fecha_min
            )
        
        with col3:
            # Filtro por fecha fin
            fecha_fin = st.date_input(
                "Fecha Fin:",
                value=fecha_max
            )
            
        # Filtro por texto/código
        filtro_codigo = st.text_input("Filtrar por código:", "")
        
        # Aplicar filtros
        df_filtrado = df_muestras.copy()
        
        # Filtro por operario
        if operario_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['operario'] == operario_filtro]
        
        # Filtro por fecha
        try:
            df_filtrado = df_filtrado[
                (df_filtrado['fecha'].dt.date >= fecha_inicio) & 
                (df_filtrado['fecha'].dt.date <= fecha_fin)
            ]
        except:
            # Si hay error en el filtrado por fecha, lo ignoramos
            pass
            
        # Filtro por código
        if filtro_codigo:
            df_filtrado = df_filtrado[df_filtrado['codigo_muestra'].str.contains(filtro_codigo, case=False)]
        
        # Crear DataFrame para mostrar muestras (con formato adecuado)
        df_mostrar = pd.DataFrame({
            "Código": df_filtrado["codigo_muestra"],
            "Operario": df_filtrado["operario"],
            "Fecha": df_filtrado["fecha"].dt.strftime('%Y-%m-%d') if 'fecha' in df_filtrado.columns and pd.api.types.is_datetime64_any_dtype(df_filtrado['fecha']) else df_filtrado["fecha"],
            "Tipo Material": df_filtrado["tipo_material"],
            "Estado": df_filtrado["estado"]
        })
        
        # Mostrar tabla de muestras
        st.subheader(f"Muestras Registradas ({len(df_filtrado)} resultados)")
        st.dataframe(df_mostrar, use_container_width=True)
        
        # Si no hay muestras después del filtrado
        if df_filtrado.empty:
            st.warning("No hay muestras que coincidan con los filtros aplicados.")
            return
        
        # --- SELECCIÓN MÚLTIPLE DE MUESTRAS ---
        st.subheader("Selección de Muestras para Comparación")
        
        codigos_filtrados = df_filtrado["codigo_muestra"].tolist()
        
        codigos_seleccionados = st.multiselect(
            "Seleccionar Muestras para Ver Detalles",
            options=codigos_filtrados,
            default=codigos_filtrados[0] if codigos_filtrados else None
        )
        
        if not codigos_seleccionados:
            st.info("Seleccione al menos una muestra para ver sus detalles.")
            return
        
        # --- TABLA COMPARATIVA DE PARÁMETROS ---
        st.subheader("Comparativa de Muestras Seleccionadas")
        
        # Recopilar datos de todas las muestras seleccionadas
        datos_comparativos = []
        ensayos_validos = []
        
        for codigo in codigos_seleccionados:
            muestra = obtener_muestra(codigo)
            ensayo = obtener_ensayo_granulometrico(codigo)
            
            if muestra and ensayo:
                datos_comparativos.append({
                    "Código Muestra": codigo,
                    "Fecha Ensayo": ensayo.get('fecha_ensayo', 'No disponible'),
                    "Operario": ensayo.get('operario', muestra.get('operario', 'No disponible')),
                    "Masa Total (g)": ensayo.get('masa_total', 0),
                    "D10 (mm)": round(ensayo.get('d10', 0), 3),
                    "D30 (mm)": round(ensayo.get('d30', 0), 3),
                    "D60 (mm)": round(ensayo.get('d60', 0), 3),
                    "Coef. Uniformidad": round(ensayo.get('coef_uniformidad', 0), 2),
                    "Coef. Curvatura": round(ensayo.get('coef_curvatura', 0), 2)
                })
                
                # Guardar ensayos válidos para el gráfico comparativo
                if ensayo.get('tamices'):
                    ensayos_validos.append((codigo, ensayo))
        
        if datos_comparativos:
            # Mostrar tabla comparativa
            df_comparativa = pd.DataFrame(datos_comparativos)
            st.dataframe(df_comparativa, use_container_width=True)
            
            # Opción para exportar comparativa
            csv_comparativa = df_comparativa.to_csv(index=False)
            st.download_button(
                label="Descargar Comparativa (CSV)",
                data=csv_comparativa,
                file_name=f"comparativa_granulometria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No hay datos de ensayos disponibles para las muestras seleccionadas.")
            return
            
        # --- GRÁFICO COMPARATIVO ---
        if ensayos_validos:
            st.subheader("Gráfico Comparativo de Curvas Granulométricas")
            
            # Crear un gráfico combinado
            fig = go.Figure()
            
            for codigo, ensayo in ensayos_validos:
                if 'tamices' in ensayo and ensayo['tamices']:
                    # Extraer datos para la curva
                    x_data = [t.get('apertura', 0) for t in ensayo['tamices']]
                    y_data = [t.get('porcentaje_pasa', 0) for t in ensayo['tamices']]
                    
                    # Añadir curva al gráfico
                    fig.add_trace(go.Scatter(
                        x=x_data, 
                        y=y_data,
                        mode='lines+markers',
                        name=codigo
                    ))
            
            # Configurar el gráfico
            fig.update_layout(
                title="Curvas Granulométricas",
                xaxis_title="Tamaño de partícula (mm)",
                yaxis_title="Porcentaje que pasa (%)",
                xaxis_type="log",
                xaxis_range=[np.log10(0.01), np.log10(100)],
                yaxis_range=[0, 100],
                height=600
            )
            
            # Mostrar el gráfico
            st.plotly_chart(fig, use_container_width=True)
            
        # --- DETALLES INDIVIDUALES DE CADA MUESTRA ---
        st.markdown("---")
        st.subheader("Detalles Individuales de Muestras")
        
        for codigo in codigos_seleccionados:
            with st.expander(f"Muestra: {codigo}", expanded=False):
                muestra = obtener_muestra(codigo)
                ensayo = obtener_ensayo_granulometrico(codigo)
                
                if muestra:
                    tab1, tab2 = st.tabs(["Información General", "Ensayo Granulométrico"])
                    
                    with tab1:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Operario:** {muestra.get('operario', 'No disponible')}")
                            st.write(f"**Fecha:** {muestra.get('fecha', 'No disponible')}")
                            st.write(f"**Tipo Material:** {muestra.get('tipo_material', 'No disponible')}")
                        
                        with col2:
                            st.write(f"**Estado:** {muestra.get('estado', 'No disponible')}")
                            st.write(f"**Notas:** {muestra.get('notas', '') if muestra.get('notas') else 'Sin notas'}")
                        
                        # Mostrar imágenes
                        try:
                            imagenes = obtener_imagenes(codigo)
                            if imagenes:
                                st.subheader("Imágenes")
                                img_cols = st.columns(min(3, len(imagenes)))
                                
                                for idx, (img_id, img, nombre) in enumerate(imagenes):
                                    col_idx = idx % 3
                                    with img_cols[col_idx]:
                                        st.image(img, caption=nombre, use_column_width=True)
                            else:
                                st.info("Esta muestra no tiene imágenes adjuntas.")
                        except Exception as e:
                            st.error(f"Error al cargar imágenes: {str(e)}")
                    
                    with tab2:
                        if ensayo:
                            # Mostrar datos básicos del ensayo
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Fecha Ensayo:** {ensayo.get('fecha_ensayo', 'No disponible')}")
                            with col2:
                                st.write(f"**Operario:** {ensayo.get('operario', 'No disponible')}")
                            with col3:
                                st.write(f"**Masa Total:** {ensayo.get('masa_total', 'No disponible')} g")
                            
                            # Mostrar datos de tamices en tabla
                            if 'tamices' in ensayo and ensayo['tamices']:
                                st.subheader("Datos de Tamices")
                                try:
                                    df_tamices = pd.DataFrame([
                                        {
                                            "Tamiz": t.get("tamiz", ""),
                                            "Apertura (mm)": t.get("apertura", 0),
                                            "Masa Retenida (g)": t.get("masa_retenida", 0),
                                            "% Retenido": f"{t.get('porcentaje_retenido', 0):.2f}",
                                            "% Retenido Acumulado": f"{t.get('porcentaje_retenido_acumulado', 0):.2f}",
                                            "% Pasa": f"{t.get('porcentaje_pasa', 0):.2f}"
                                        }
                                        for t in ensayo['tamices']
                                    ])
                                    
                                    st.dataframe(df_tamices)
                                    
                                    # Generar y mostrar gráfico individual
                                    try:
                                        fig_individual = generar_grafico_granulometrico(ensayo['tamices'])
                                        st.plotly_chart(fig_individual)
                                    except Exception as e:
                                        st.error(f"Error al generar el gráfico individual: {str(e)}")
                                    
                                    # Opción para exportar resultados
                                    csv = df_tamices.to_csv(index=False)
                                    st.download_button(
                                        label="Descargar CSV",
                                        data=csv,
                                        file_name=f"granulometria_{codigo}.csv",
                                        mime="text/csv",
                                        key=f"download_{codigo}"
                                    )
                                except Exception as e:
                                    st.error(f"Error al procesar datos de tamices: {str(e)}")
                            else:
                                st.warning("No hay datos de tamices disponibles para este ensayo.")
                        else:
                            st.info("Esta muestra no tiene ensayos granulométricos registrados.")
                            if st.button("Realizar Ensayo Granulométrico", key=f"btn_ensayo_{codigo}"):
                                st.session_state.realizar_ensayo = codigo
                                st.session_state.pagina_actual = "Ensayos Granulométricos"
                                st.experimental_rerun()
                else:
                    st.error(f"No se pudo cargar la información de la muestra {codigo}.")
    
    except Exception as e:
        st.error(f"Ha ocurrido un error: {str(e)}")
        st.exception(e)