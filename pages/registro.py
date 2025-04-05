import streamlit as st
from datetime import datetime
from PIL import Image
import traceback
from models.muestras import guardar_muestra, guardar_imagen, obtener_muestra, obtener_imagenes

def mostrar_pagina_registro():
    """
    Muestra la página de registro de muestras
    """
    st.header("Registro de Muestras")
    
    # Verificar que el usuario esté autenticado
    if not st.session_state.get('autenticado', False) or not st.session_state.get('usuario_actual'):
        st.warning("Debe iniciar sesión para registrar muestras")
        return
    
    # Obtener el nombre del usuario actual
    usuario_actual = st.session_state.usuario_actual['nombre']
    
    try:
        # Formulario para registrar nueva muestra
        with st.form("formulario_muestra"):
            col1, col2 = st.columns(2)
            
            with col1:
                codigo_muestra = st.text_input("Código de Muestra", key="codigo")
                # Mostrar el operario como texto no editable (usuario actual)
                st.write(f"**Operario:** {usuario_actual}")
                # Agregar un campo oculto para mantener el valor del operario
                operario = usuario_actual
                fecha = st.date_input("Fecha", value=datetime.now().date())
            
            with col2:
                tipo_material = st.selectbox(
                    "Tipo de Material",
                    options=["Suelo", "Roca", "Otro"],
                    key="tipo_material"
                )
                notas = st.text_area("Notas", key="notas")
            
            # Carga de imágenes
            archivos_imagenes = st.file_uploader(
                "Cargar imágenes de la muestra", 
                accept_multiple_files=True,
                type=["png", "jpg", "jpeg"]
            )
            
            submitted = st.form_submit_button("Guardar Muestra")
            
            if submitted:
                if not codigo_muestra:
                    st.error("Debe ingresar un código de muestra")
                else:
                    # Guardar información de la muestra
                    try:
                        guardar_muestra(codigo_muestra, operario, fecha, tipo_material, notas)
                        
                        # Guardar imágenes si se han cargado
                        imagenes_guardadas = 0
                        for archivo in archivos_imagenes:
                            try:
                                img = Image.open(archivo)
                                guardar_imagen(codigo_muestra, img, archivo.name)
                                imagenes_guardadas += 1
                            except Exception as e:
                                st.error(f"Error al guardar imagen {archivo.name}: {str(e)}")
                        
                        if archivos_imagenes and imagenes_guardadas == 0:
                            st.warning("No se pudieron guardar las imágenes, pero la información de la muestra se guardó correctamente.")
                        elif archivos_imagenes and imagenes_guardadas < len(archivos_imagenes):
                            st.warning(f"Se guardaron {imagenes_guardadas} de {len(archivos_imagenes)} imágenes.")
                        
                        st.success(f"Muestra {codigo_muestra} guardada correctamente")
                        st.session_state.mostrar_muestra = codigo_muestra
                    except Exception as e:
                        st.error(f"Error al guardar la muestra: {str(e)}")
                        st.exception(e)

        # Mostrar muestra recién guardada
        if "mostrar_muestra" in st.session_state:
            codigo = st.session_state.mostrar_muestra
            
            try:
                muestra = obtener_muestra(codigo)
                
                if muestra:
                    st.subheader(f"Muestra: {codigo}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Operario:** {muestra.get('operario', 'No disponible')}")
                        st.write(f"**Fecha:** {muestra.get('fecha', 'No disponible')}")
                        st.write(f"**Tipo Material:** {muestra.get('tipo_material', 'No disponible')}")
                    
                    with col2:
                        st.write(f"**Estado:** {muestra.get('estado', 'No disponible')}")
                        st.write(f"**Notas:** {muestra.get('notas', 'Sin notas') or 'Sin notas'}")
                    
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
                            st.info("No hay imágenes adjuntas a esta muestra.")
                    except Exception as e:
                        st.error(f"Error al cargar las imágenes: {str(e)}")
                    
                    # Opciones adicionales
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Botón para ir a ensayo granulométrico
                        if st.button("Realizar Ensayo Granulométrico", use_container_width=True):
                            st.session_state.realizar_ensayo = codigo
                            st.session_state.pagina_actual = "Ensayos Granulométricos"
                            st.experimental_rerun()
                    
                    with col2:
                        # Botón para registrar nueva muestra
                        if st.button("Registrar Otra Muestra", use_container_width=True):
                            # Limpiar el estado para permitir un nuevo registro
                            del st.session_state.mostrar_muestra
                            st.experimental_rerun()
                else:
                    st.error(f"No se pudo recuperar la información de la muestra {codigo}.")
                    if st.button("Intentar de nuevo"):
                        st.experimental_rerun()
            except Exception as e:
                st.error(f"Error al mostrar la muestra: {str(e)}")
                st.code(traceback.format_exc())
    except Exception as e:
        st.error(f"Ha ocurrido un error: {str(e)}")
        st.exception(e)