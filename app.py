import streamlit as st
import sqlite3
import os
import traceback
import sys
from models.usuarios_db import verificar_credenciales, crear_usuario, verificar_nickname_disponible, init_users_table

# Evitar que se muestren las rutas en la barra lateral
hide_streamlit_elements = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
/* Ocultar selectbox de rutas */
[data-testid="stSidebarNav"] {display: none !important;}
</style>
"""

# Función para cambiar de página
def cambiar_pagina(opcion):
    nueva_pagina = opcion
    
    # Si selecciona ensayos pero no hay subpágina seleccionada,
    # establecer la primera opción como predeterminada
    if nueva_pagina == "Ensayos" and not st.session_state.subpagina_ensayos:
        st.session_state.subpagina_ensayos = opciones_ensayos[0]
        
    st.session_state.pagina_actual = nueva_pagina

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Ensayos Geotécnicos",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilos personalizados
st.markdown(hide_streamlit_elements, unsafe_allow_html=True)
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar variables de sesión relacionadas con la autenticación
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

if 'vista_login' not in st.session_state:
    st.session_state.vista_login = "login"  # puede ser "login" o "signup"

# Inicialización de la base de datos y carga de módulos
@st.cache_resource
def inicializar_sistema():
    """
    Inicializa el sistema, asegurando que la base de datos existe
    y cargando los módulos necesarios.
    """
    try:
        # Primero aseguramos que el módulo de base de datos está disponible
        from models.db import inicializar_bd, obtener_conexion
        
        # Inicializar la base de datos
        inicializar_bd()
        
        # Inicializar la tabla de usuarios
        init_users_table()
        
        # Cargar los módulos necesarios
        from pages.inicio import mostrar_pagina_inicio
        from pages.registro import mostrar_pagina_registro
        from pages.granulometria import mostrar_pagina_granulometria
        from pages.consulta import mostrar_pagina_consulta
        from pages.densidad_arido import mostrar_pagina_densidad_arido
        from pages.limites import mostrar_pagina_limites
        from pages.cbr import mostrar_pagina_cbr
        from pages.lajas_agujas import mostrar_pagina_lajas_agujas
        from pages.picnometro import mostrar_pagina_picnometro
        from pages.equivalente_arena import mostrar_pagina_equivalente_arena
        from pages.proctor import mostrar_pagina_proctor
        
        return {
            "inicializado": True,
            "modulos": {
                "inicio": mostrar_pagina_inicio,
                "registro": mostrar_pagina_registro,
                "granulometria": mostrar_pagina_granulometria,
                "consulta": mostrar_pagina_consulta,
                "densidad_arido": mostrar_pagina_densidad_arido,
                "limites": mostrar_pagina_limites,
                "cbr": mostrar_pagina_cbr,
                "lajas_agujas": mostrar_pagina_lajas_agujas,
                "picnometro": mostrar_pagina_picnometro,
                "equivalente_arena": mostrar_pagina_equivalente_arena,
                "proctor": mostrar_pagina_proctor
            }
        }
    except Exception as e:
        return {
            "inicializado": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Función para mostrar la página de inicio de sesión
def mostrar_login():
    st.title("🔐 Inicio de Sesión")
    
    with st.form("login_form"):
        nickname = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Iniciar Sesión")
        with col2:
            signup_button = st.form_submit_button("Crear Cuenta")
    
    if submit_button:
        if nickname and password:
            usuario = verificar_credenciales(nickname, password)
            if usuario:
                st.session_state.autenticado = True
                st.session_state.usuario_actual = usuario
                st.success("¡Inicio de sesión exitoso!")
                st.rerun()
            else:
                st.error("Nombre de usuario o contraseña incorrectos")
        else:
            st.warning("Por favor, complete todos los campos")
    
    if signup_button:
        st.session_state.vista_login = "signup"
        st.rerun()

# Función para mostrar la página de registro
def mostrar_signup():
    st.title("📝 Registro de Usuario")
    
    with st.form("signup_form"):
        nombre = st.text_input("Nombre completo")
        nickname = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        confirm_password = st.text_input("Confirmar contraseña", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Registrarse")
        with col2:
            back_button = st.form_submit_button("Volver al inicio de sesión")
    
    if back_button:
        st.session_state.vista_login = "login"
        st.rerun()
        
    if submit_button:
        if not nombre or not nickname or not password:
            st.warning("Todos los campos son obligatorios")
        elif password != confirm_password:
            st.error("Las contraseñas no coinciden")
        elif len(password) < 6:
            st.warning("La contraseña debe tener al menos 6 caracteres")
        else:
            # Verificar si el nickname está disponible
            if verificar_nickname_disponible(nickname):
                if crear_usuario(nombre, nickname, password):
                    st.success("Usuario creado con éxito. Ahora puede iniciar sesión.")
                    st.session_state.vista_login = "login"
                    st.rerun()
                else:
                    st.error("Error al crear el usuario")
            else:
                st.error("El nombre de usuario ya está en uso")

# Función para cerrar sesión
def cerrar_sesion():
    st.session_state.autenticado = False
    st.session_state.usuario_actual = None
    st.session_state.pagina_actual = "Inicio"
    st.session_state.vista_login = "login"
    st.rerun()

# Función principal
def main():
    # Inicializar sistema
    sistema = inicializar_sistema()
    
    if not sistema["inicializado"]:
        st.error("Error al inicializar el sistema")
        st.error(sistema["error"])
        st.code(sistema["traceback"], language="python")
        return
    
    # Inicializar estado si no existe
    if "pagina_actual" not in st.session_state:
        st.session_state.pagina_actual = "Inicio"
    
    if 'subpagina_ensayos' not in st.session_state:
        st.session_state.subpagina_ensayos = None

    # Opciones principales del menú
    opciones_principales = ["Inicio", "Registro de Muestras", "Ensayos", "Consulta de Resultados"]

    # Opciones del submenú de ensayos
    opciones_ensayos = [
        "Ensayos Granulométricos", 
        "Límites de Atterberg", 
        "Densidad de Árido Grueso", 
        "CBR",
        "Índice de Lajas y Agujas",
        "Picnómetro de Arena",
        "Equivalente de Arena",
        "Próctor"
    ]

    # Barra lateral
    with st.sidebar:
        # Título de la aplicación
        st.title("Sistema de Ensayos Geotécnicos")
        
        # Si el usuario está autenticado, mostrar el menú completo
        if st.session_state.autenticado:
            st.write(f"👤 **Usuario:** {st.session_state.usuario_actual['nombre']}")
            
            # Botón de cerrar sesión
            if st.button("Cerrar Sesión"):
                cerrar_sesion()
            
            st.markdown("---")
            
            # Navegación
            st.header("Navegación")
            opcion = st.radio(
                "Seleccione una opción:",
                opciones_principales,
                index=opciones_principales.index(
                    "Ensayos" if st.session_state.pagina_actual == "Ensayos" or st.session_state.pagina_actual in opciones_ensayos 
                    else st.session_state.pagina_actual
                ),
            )

            if opcion == "Ensayos" and not st.session_state.subpagina_ensayos:
                st.session_state.subpagina_ensayos = opciones_ensayos[0]
            
            st.session_state.pagina_actual = opcion

            # Si se selecciona "Ensayos", mostrar el submenú
            if opcion == "Ensayos":
                subopcion = st.selectbox(
                    "Tipo de ensayo:",
                    opciones_ensayos,
                    index=opciones_ensayos.index(st.session_state.subpagina_ensayos) if st.session_state.subpagina_ensayos in opciones_ensayos else 0
                )
                
                # Actualizar la subpágina actual de ensayos
                st.session_state.subpagina_ensayos = subopcion
                st.session_state.pagina_actual = subopcion
        else:
            # Si no está autenticado, mostrar opciones de login/registro
            st.write("👤 **Acceso al Sistema**")
            
            if st.button("Iniciar Sesión", key="btn_login", disabled=st.session_state.vista_login == "login"):
                st.session_state.vista_login = "login"
                st.rerun()
                
            if st.button("Crear Cuenta", key="btn_signup", disabled=st.session_state.vista_login == "signup"):
                st.session_state.vista_login = "signup"
                st.rerun()
        
        # Información adicional en la barra lateral
        st.markdown("---")
        st.info(
            "Este sistema permite gestionar ensayos geotécnicos, "
            "facilitando el registro, procesamiento y consulta de datos."
        )
        
        # Mostrar versión y otros detalles
        st.markdown("---")
        st.caption("© 2025 - GARNOCEX")
        st.caption("v1.0.0")
    
    # Contenido principal
    if st.session_state.autenticado:
        # Enrutar a la página correspondiente basado en la selección
        try:
            pagina_actual = st.session_state.pagina_actual
            
            if pagina_actual == "Inicio":
                sistema["modulos"]["inicio"]()
            elif pagina_actual == "Registro de Muestras":
                sistema["modulos"]["registro"]()
            elif pagina_actual == "Consulta de Resultados":
                sistema["modulos"]["consulta"]()
            elif pagina_actual in opciones_ensayos:
                # Manejar los distintos tipos de ensayos
                if pagina_actual == "Ensayos Granulométricos":
                    sistema["modulos"]["granulometria"]()
                elif pagina_actual == "Límites de Atterberg":
                    sistema["modulos"]["limites"]()
                elif pagina_actual == "Densidad de Árido Grueso":
                    sistema["modulos"]["densidad_arido"]()
                elif pagina_actual == "CBR":
                    sistema["modulos"]["cbr"]()
                elif pagina_actual == "Índice de Lajas y Agujas":
                    sistema["modulos"]["lajas_agujas"]()
                elif pagina_actual == "Picnómetro de Arena":
                    sistema["modulos"]["picnometro"]()
                elif pagina_actual == "Equivalente de Arena":
                    sistema["modulos"]["equivalente_arena"]()
                elif pagina_actual == "Próctor":
                    sistema["modulos"]["proctor"]()
                else:
                    st.error(f"Página de ensayo no implementada: {pagina_actual}")
            else:
                st.error(f"Página no encontrada: {pagina_actual}")
        except Exception as e:
            st.error(f"Ha ocurrido un error: {str(e)}")
            st.exception(e)
    else:
        # Mostrar pantalla de login o registro
        if st.session_state.vista_login == "login":
            mostrar_login()
        else:
            mostrar_signup()

# Punto de entrada de la aplicación
if __name__ == "__main__":
    main()