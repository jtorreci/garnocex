import streamlit as st
import os

def mostrar_pagina_inicio():
    """
    Muestra la página de inicio del sistema
    """
    st.header("Bienvenido al Sistema de Gestión de Ensayos Geotécnicos. Proyecto GARNOCEX")
    
    # Información general del sistema
    st.markdown("""
    ## Descripción del Sistema
    
    Este sistema le permite gestionar ensayos geotécnicos de manera eficiente y organizada, 
    facilitando el registro, procesamiento y consulta de datos experimentales.
    
    ### Características principales:
    
    - Registro de muestras con datos completos
    - Almacenamiento de imágenes de las muestras
    - Procesamiento de ensayos granulométricos
    - Generación automática de curvas granulométricas
    - Cálculo de parámetros característicos (D10, D30, D60)
    - Cálculo de coeficientes de uniformidad y curvatura
    - Consulta y exportación de resultados
    """)
    
    # Instrucciones de uso
    with st.expander("¿Cómo usar el sistema?"):
        st.markdown("""
        ### Pasos para utilizar el sistema:
        
        1. **Registro de Muestras**: 
           - Seleccione "Registro de Muestras" en el menú lateral
           - Complete los datos requeridos de la muestra
           - Suba imágenes si es necesario
           - Guarde la información
        
        2. **Ensayos Granulométricos**:
           - Seleccione "Ensayos Granulométricos" en el menú lateral
           - Elija la muestra a la que desea asociar el ensayo
           - Ingrese la masa total y las masas retenidas en cada tamiz
           - El sistema calculará automáticamente la curva granulométrica y los parámetros
        
        3. **Consulta de Resultados**:
           - Seleccione "Consulta de Resultados" en el menú lateral
           - Explore las muestras registradas
           - Visualice los datos, gráficos y resultados de los ensayos
           - Exporte la información según sea necesario
        """)
    
    # Estadísticas del sistema
    st.subheader("Estadísticas del Sistema")
    
    # Mostrar algunas estadísticas básicas
    col1, col2, col3 = st.columns(3)
    
    try:
        # Intentar obtener estadísticas reales de la base de datos
        from models.db import obtener_conexion
        
        # Comprobar si la base de datos existe
        db_exists = os.path.exists('ensayos_geotecnicos.db')
        
        if db_exists:
            conn = obtener_conexion()
            c = conn.cursor()
            
            # Contar muestras
            c.execute("SELECT COUNT(*) FROM muestras")
            num_muestras = c.fetchone()[0]
            
            # Contar ensayos
            c.execute("SELECT COUNT(*) FROM ensayos_granulometricos")
            num_ensayos = c.fetchone()[0]
            
            # Contar imágenes
            c.execute("SELECT COUNT(*) FROM imagenes")
            num_imagenes = c.fetchone()[0]
            
            conn.close()
        else:
            num_muestras = 0
            num_ensayos = 0
            num_imagenes = 0
        
    except Exception:
        # Valores por defecto si hay error
        num_muestras = 0
        num_ensayos = 0
        num_imagenes = 0
    
    with col1:
        st.metric("Muestras Registradas", num_muestras)
    
    with col2:
        st.metric("Ensayos Granulométricos", num_ensayos)
    
    with col3:
        st.metric("Imágenes Almacenadas", num_imagenes)
    
    # Call to action
    st.markdown("---")
    st.markdown("### ¿Listo para comenzar?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Registrar Nueva Muestra", use_container_width=True):
            st.session_state.pagina_actual = "Registro de Muestras"
            st.rerun()
    
    with col2:
        if st.button("Realizar Ensayo", use_container_width=True):
            st.session_state.pagina_actual = "Ensayos Granulométricos"
            st.rerun()
    
    with col3:
        if st.button("Consultar Resultados", use_container_width=True):
            st.session_state.pagina_actual = "Consulta de Resultados"
            st.rerun()