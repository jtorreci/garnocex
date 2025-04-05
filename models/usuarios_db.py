import sqlite3
import hashlib
import os
import secrets
from typing import Optional, Tuple, List, Dict

# Ruta de la base de datos
DB_PATH = "ensayos_geotecnicos.db"

def get_db_connection():
    """Establece conexión con la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_users_table():
    """Inicializa la tabla de usuarios si no existe."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tabla de usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        nickname TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Genera un hash seguro de la contraseña usando PBKDF2 con SHA-256.
    
    Args:
        password: Contraseña en texto plano
        salt: Valor salt opcional. Si no se proporciona, se genera uno nuevo.
        
    Returns:
        Tupla con (password_hash, salt)
    """
    if salt is None:
        # Generar un salt aleatorio de 32 bytes
        salt = secrets.token_hex(32)
        
    # Aplicar PBKDF2 usando SHA-256 con 100,000 iteraciones
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=100000
    )
    
    password_hash = key.hex()
    return password_hash, salt

def crear_usuario(nombre: str, nickname: str, password: str) -> bool:
    """
    Crea un nuevo usuario en la base de datos.
    
    Args:
        nombre: Nombre completo del usuario
        nickname: Nombre de usuario único
        password: Contraseña en texto plano
        
    Returns:
        True si el usuario se creó con éxito, False si hay error (ej: nickname duplicado)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generar hash y salt de la contraseña
        password_hash, salt = hash_password(password)
        
        # Insertar el nuevo usuario
        cursor.execute('''
        INSERT INTO usuarios (nombre, nickname, password_hash, salt)
        VALUES (?, ?, ?, ?)
        ''', (nombre, nickname, password_hash, salt))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Error de integridad (nickname duplicado)
        conn.close()
        return False
    except Exception as e:
        print(f"Error al crear usuario: {e}")
        conn.close()
        return False

def verificar_credenciales(nickname: str, password: str) -> Optional[Dict]:
    """
    Verifica las credenciales de un usuario.
    
    Args:
        nickname: Nombre de usuario
        password: Contraseña en texto plano
        
    Returns:
        Diccionario con datos del usuario si las credenciales son correctas, None en caso contrario
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buscar usuario por nickname
    cursor.execute('SELECT * FROM usuarios WHERE nickname = ?', (nickname,))
    usuario = cursor.fetchone()
    
    if not usuario:
        conn.close()
        return None
    
    # Verificar contraseña
    stored_hash = usuario['password_hash']
    salt = usuario['salt']
    
    # Calcular hash de la contraseña proporcionada
    calculated_hash, _ = hash_password(password, salt)
    
    if calculated_hash == stored_hash:
        # Convertir el objeto Row a diccionario
        usuario_dict = dict(usuario)
        
        # Eliminar datos sensibles
        del usuario_dict['password_hash']
        del usuario_dict['salt']
        
        conn.close()
        return usuario_dict
    
    conn.close()
    return None

def obtener_usuario_por_id(usuario_id: int) -> Optional[Dict]:
    """
    Obtiene información de un usuario por su ID.
    
    Args:
        usuario_id: ID del usuario
        
    Returns:
        Diccionario con datos del usuario o None si no existe
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,))
    usuario = cursor.fetchone()
    
    conn.close()
    
    if usuario:
        usuario_dict = dict(usuario)
        del usuario_dict['password_hash']
        del usuario_dict['salt']
        return usuario_dict
    
    return None

def obtener_todos_usuarios() -> List[Dict]:
    """
    Obtiene la lista de todos los usuarios.
    
    Returns:
        Lista de diccionarios con datos de usuarios (sin info sensible)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, nombre, nickname, fecha_creacion, fecha_modificacion FROM usuarios')
    usuarios = cursor.fetchall()
    
    conn.close()
    
    return [dict(usuario) for usuario in usuarios]

def actualizar_usuario(usuario_id: int, nombre: Optional[str] = None, 
                      nickname: Optional[str] = None, password: Optional[str] = None) -> bool:
    """
    Actualiza los datos de un usuario.
    
    Args:
        usuario_id: ID del usuario a actualizar
        nombre: Nuevo nombre (opcional)
        nickname: Nuevo nickname (opcional)
        password: Nueva contraseña (opcional)
        
    Returns:
        True si la actualización fue exitosa, False en caso contrario
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si el usuario existe
        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            conn.close()
            return False
        
        # Construir consulta dinámica para actualizar solo los campos proporcionados
        update_parts = []
        params = []
        
        if nombre is not None:
            update_parts.append("nombre = ?")
            params.append(nombre)
            
        if nickname is not None:
            update_parts.append("nickname = ?")
            params.append(nickname)
            
        if password is not None:
            password_hash, salt = hash_password(password)
            update_parts.append("password_hash = ?")
            params.append(password_hash)
            update_parts.append("salt = ?")
            params.append(salt)
        
        # Actualizar la fecha de modificación
        update_parts.append("fecha_modificacion = CURRENT_TIMESTAMP")
        
        if not update_parts:
            # No hay nada que actualizar
            conn.close()
            return True
            
        # Construir y ejecutar la consulta
        query = f"UPDATE usuarios SET {', '.join(update_parts)} WHERE id = ?"
        params.append(usuario_id)
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return True
    except sqlite3.IntegrityError:
        # Error de integridad (nickname duplicado)
        conn.close()
        return False
    except Exception as e:
        print(f"Error al actualizar usuario: {e}")
        conn.close()
        return False

def eliminar_usuario(usuario_id: int) -> bool:
    """
    Elimina un usuario de la base de datos.
    
    Args:
        usuario_id: ID del usuario a eliminar
        
    Returns:
        True si la eliminación fue exitosa, False en caso contrario
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM usuarios WHERE id = ?', (usuario_id,))
        
        if cursor.rowcount == 0:
            # No se encontró el usuario
            conn.close()
            return False
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al eliminar usuario: {e}")
        conn.close()
        return False

def verificar_nickname_disponible(nickname: str) -> bool:
    """
    Verifica si un nickname está disponible.
    
    Args:
        nickname: Nickname a verificar
        
    Returns:
        True si el nickname está disponible, False si ya existe
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM usuarios WHERE nickname = ?', (nickname,))
    resultado = cursor.fetchone()
    
    conn.close()
    
    return resultado['count'] == 0

# Inicializar la tabla de usuarios al importar el módulo
init_users_table()