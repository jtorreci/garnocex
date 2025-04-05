import streamlit as st
import time
import sys
import os

# Añadir el directorio raíz al path para poder importar desde models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar funciones del modelo de usuarios
from models.usuarios_db import (
    crear_usuario, 
    obtener_todos_usuarios, 
    obtener_usuario_por_id,
    actualizar_usuario, 
    eliminar_usuario, 
    verificar_credenciales,
    verificar_nickname_disponible
)

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Usuarios - Ensayos Geotécnicos",
    page_icon="👤",
    layout="wide"
)

# Inicializar variables de sesión
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None
    
if 'es_admin' not in st.session_state:
    st.session_state.es_admin = False
    
if 'vista_actual' not in st.session_state:
    st.session_state.vista_actual = "login"

def login_usuario(nickname, password):
    """Inicia sesión de usuario."""
    usuario = verificar_credenciales(nickname, password)
    if usuario:
        st.session_state.autenticado = True
        st.session_state.usuario_actual = usuario
        
        # Por simplicidad, consideramos admin al usuario con ID 1
        # En un sistema real, deberías tener un campo específico
        st.session_state.es_admin = (usuario['id'] == 1)
        
        st.session_state.vista_actual = "perfil"
        return True
    return False

def cerrar_sesion():
    """Cierra la sesión actual."""
    st.session_state.autenticado = False
    st.session_state.usuario_actual = None
    st.session_state.es_admin = False
    st.session_state.vista_actual = "login"

def cambiar_vista(vista):
    """Cambia la vista actual."""
    st.session_state.vista_actual = vista

def mostrar_login():
    """Muestra el formulario de inicio de sesión."""
    st.title("🔐 Inicio de Sesión")
    
    with st.form("login_form"):
        nickname = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Iniciar Sesión")
        with col2:
            register_button = st.form_submit_button("Crear Cuenta")
            
    if submit_button:
        if nickname and password:
            if login_usuario(nickname, password):
                st.success("¡Inicio de sesión exitoso!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Nombre de usuario o contraseña incorrectos")
        else:
            st.warning("Por favor, ingrese nombre de usuario y contraseña")
            
    if register_button:
        cambiar_vista("registro")
        st.rerun()
        
    st.markdown("---")
    st.write("¿No tiene una cuenta? Haga clic en 'Crear Cuenta'")

def mostrar_registro():
    """Muestra el formulario de registro de usuarios."""
    st.title("📝 Registro de Usuario")
    
    with st.form("registro_form"):
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
        cambiar_vista("login")
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
                    st.success("Usuario creado con éxito")
                    time.sleep(1)
                    cambiar_vista("login")
                    st.rerun()
                else:
                    st.error("Error al crear el usuario")
            else:
                st.error("El nombre de usuario ya está en uso")
                
    st.markdown("---")
    st.write("¿Ya tiene una cuenta? Haga clic en 'Volver al inicio de sesión'")

def mostrar_perfil():
    """Muestra la información del perfil del usuario."""
    st.title("👤 Perfil de Usuario")
    
    if not st.session_state.usuario_actual:
        st.error("No hay usuario autenticado")
        cambiar_vista("login")
        return
    
    usuario = st.session_state.usuario_actual
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Información del Usuario")
        st.write(f"**Nombre:** {usuario['nombre']}")
        st.write(f"**Usuario:** {usuario['nickname']}")
        st.write(f"**Fecha de registro:** {usuario['fecha_creacion']}")
        
    with col2:
        st.subheader("Opciones")
        if st.button("Editar Perfil"):
            cambiar_vista("editar_perfil")
            st.rerun()
        
        if st.session_state.es_admin:
            if st.button("Gestionar Usuarios"):
                cambiar_vista("admin_usuarios")
                st.rerun()
        
        if st.button("Cerrar Sesión"):
            cerrar_sesion()
            st.success("Sesión cerrada con éxito")
            time.sleep(1)
            st.rerun()

def mostrar_editar_perfil():
    """Muestra el formulario para editar el perfil."""
    st.title("✏️ Editar Perfil")
    
    if not st.session_state.usuario_actual:
        st.error("No hay usuario autenticado")
        cambiar_vista("login")
        return
    
    usuario = st.session_state.usuario_actual
    
    with st.form("editar_perfil_form"):
        nombre = st.text_input("Nombre completo", value=usuario['nombre'])
        nickname = st.text_input("Nombre de usuario", value=usuario['nickname'])
        
        st.subheader("Cambiar contraseña (opcional)")
        nueva_password = st.text_input("Nueva contraseña", type="password")
        confirm_password = st.text_input("Confirmar nueva contraseña", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Guardar Cambios")
        with col2:
            back_button = st.form_submit_button("Volver al Perfil")
            
    if back_button:
        cambiar_vista("perfil")
        st.rerun()
        
    if submit_button:
        # Validar datos
        if not nombre or not nickname:
            st.warning("El nombre y el nombre de usuario son obligatorios")
        elif nueva_password and nueva_password != confirm_password:
            st.error("Las contraseñas no coinciden")
        elif nueva_password and len(nueva_password) < 6:
            st.warning("La contraseña debe tener al menos 6 caracteres")
        else:
            # Verificar si el nickname está disponible (si ha cambiado)
            nickname_cambiado = nickname != usuario['nickname']
            
            if nickname_cambiado and not verificar_nickname_disponible(nickname):
                st.error("El nombre de usuario ya está en uso")
            else:
                # Actualizar usuario
                actualizar_params = {
                    'usuario_id': usuario['id'],
                    'nombre': nombre,
                    'nickname': nickname if nickname_cambiado else None,
                    'password': nueva_password if nueva_password else None
                }
                
                if actualizar_usuario(**actualizar_params):
                    # Actualizar datos en sesión
                    usuario_actualizado = obtener_usuario_por_id(usuario['id'])
                    st.session_state.usuario_actual = usuario_actualizado
                    
                    st.success("Perfil actualizado con éxito")
                    time.sleep(1)
                    cambiar_vista("perfil")
                    st.rerun()
                else:
                    st.error("Error al actualizar el perfil")

def mostrar_admin_usuarios():
    """Muestra la interfaz de administración de usuarios."""
    st.title("👥 Gestión de Usuarios")
    
    if not st.session_state.es_admin:
        st.error("No tiene permisos de administrador")
        cambiar_vista("perfil")
        return
    
    # Opciones de navegación
    if st.button("Volver al Perfil"):
        cambiar_vista("perfil")
        st.rerun()
    
    # Mostrar lista de usuarios
    st.subheader("Lista de Usuarios")
    usuarios = obtener_todos_usuarios()
    
    if not usuarios:
        st.info("No hay usuarios registrados")
    else:
        # Crear una tabla para mostrar los usuarios
        data = []
        for usuario in usuarios:
            data.append({
                "ID": usuario['id'],
                "Nombre": usuario['nombre'],
                "Usuario": usuario['nickname'],
                "Fecha de registro": usuario['fecha_creacion']
            })
        
        st.dataframe(data)
        
        # Formulario para editar o eliminar usuario
        st.subheader("Editar o Eliminar Usuario")
        
        with st.form("admin_form"):
            usuario_id = st.number_input("ID del usuario", min_value=1, step=1)
            accion = st.radio("Acción", ["Editar", "Eliminar"])
            
            if accion == "Editar":
                nombre = st.text_input("Nuevo nombre (dejar en blanco para no cambiar)")
                nickname = st.text_input("Nuevo nombre de usuario (dejar en blanco para no cambiar)")
                nueva_password = st.text_input("Nueva contraseña (dejar en blanco para no cambiar)", type="password")
            
            submit_button = st.form_submit_button("Realizar Acción")
        
        if submit_button:
            # Verificar que el usuario existe
            usuario = obtener_usuario_por_id(usuario_id)
            
            if not usuario:
                st.error(f"No existe un usuario con ID {usuario_id}")
            else:
                if accion == "Eliminar":
                    # Proteger al usuario admin (ID 1)
                    if usuario_id == 1:
                        st.error("No se puede eliminar al usuario administrador")
                    else:
                        if eliminar_usuario(usuario_id):
                            st.success(f"Usuario {usuario['nickname']} eliminado con éxito")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Error al eliminar el usuario")
                else:  # Editar
                    # Preparar parámetros para actualización
                    actualizar_params = {
                        'usuario_id': usuario_id,
                        'nombre': nombre if nombre else None,
                        'nickname': nickname if nickname else None,
                        'password': nueva_password if nueva_password else None
                    }
                    
                    # Verificar disponibilidad del nickname si se va a cambiar
                    if nickname and nickname != usuario['nickname'] and not verificar_nickname_disponible(nickname):
                        st.error("El nombre de usuario ya está en uso")
                    else:
                        if actualizar_usuario(**actualizar_params):
                            st.success(f"Usuario {usuario['nickname']} actualizado con éxito")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Error al actualizar el usuario")

# Principal: Selector de vistas
def main():
    # Barra lateral con navegación si el usuario está autenticado
    if st.session_state.autenticado:
        with st.sidebar:
            st.write(f"👤 **{st.session_state.usuario_actual['nombre']}**")
            st.markdown("---")
            
            if st.button("Ver Perfil"):
                cambiar_vista("perfil")
                st.rerun()
                
            if st.button("Editar Perfil"):
                cambiar_vista("editar_perfil")
                st.rerun()
                
            if st.session_state.es_admin:
                if st.button("Gestionar Usuarios"):
                    cambiar_vista("admin_usuarios")
                    st.rerun()
                    
            if st.button("Cerrar Sesión"):
                cerrar_sesion()
                st.success("Sesión cerrada con éxito")
                time.sleep(1)
                st.rerun()
    
    # Mostrar la vista actual
    if st.session_state.vista_actual == "login":
        mostrar_login()
    elif st.session_state.vista_actual == "registro":
        mostrar_registro()
    elif st.session_state.vista_actual == "perfil":
        mostrar_perfil()
    elif st.session_state.vista_actual == "editar_perfil":
        mostrar_editar_perfil()
    elif st.session_state.vista_actual == "admin_usuarios":
        mostrar_admin_usuarios()
    else:
        st.error("Vista no válida")
        cambiar_vista("login")

if __name__ == "__main__":
    main()