import io
import sqlite3
from datetime import datetime
from PIL import Image
from models.db import obtener_conexion

def guardar_muestra(codigo_muestra, operario, fecha, tipo_material, notas, estado="registrado"):
    """
    Guarda o actualiza una muestra en la base de datos
    
    Args:
        codigo_muestra (str): Código único de la muestra
        operario (str): Nombre del operario
        fecha (date): Fecha de la muestra
        tipo_material (str): Tipo de material
        notas (str): Notas adicionales
        estado (str, optional): Estado de la muestra. Por defecto "registrado"
    
    Returns:
        bool: True si la operación fue exitosa
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Verificar si la muestra ya existe
    c.execute("SELECT codigo_muestra FROM muestras WHERE codigo_muestra = ?", (codigo_muestra,))
    resultado = c.fetchone()
    
    if resultado:
        # Actualizar muestra existente
        c.execute("""
        UPDATE muestras 
        SET operario = ?, fecha = ?, tipo_material = ?, estado = ?, notas = ?
        WHERE codigo_muestra = ?
        """, (operario, fecha, tipo_material, estado, notas, codigo_muestra))
    else:
        # Insertar nueva muestra
        c.execute("""
        INSERT INTO muestras (codigo_muestra, operario, fecha, tipo_material, estado, notas)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (codigo_muestra, operario, fecha, tipo_material, estado, notas))
    
    conn.commit()
    conn.close()
    return True

def guardar_imagen(codigo_muestra, imagen, nombre_archivo, descripcion=None):
    """
    Guarda una imagen asociada a una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
        imagen (PIL.Image): Objeto de imagen
        nombre_archivo (str): Nombre original del archivo
        descripcion (str, optional): Descripción de la imagen
    
    Returns:
        int: ID de la imagen guardada
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Convertir imagen a bytes para almacenar en SQLite
    img_byte_arr = io.BytesIO()
    imagen.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Fecha actual para la subida
    fecha_subida = datetime.now().strftime('%Y-%m-%d')
    
    c.execute("""
    INSERT INTO imagenes (codigo_muestra, imagen, nombre_archivo, fecha_subida, descripcion)
    VALUES (?, ?, ?, ?, ?)
    """, (codigo_muestra, img_byte_arr, nombre_archivo, fecha_subida, descripcion))
    
    # Obtener el ID de la imagen insertada
    imagen_id = c.lastrowid
    
    conn.commit()
    conn.close()
    
    return imagen_id

def guardar_imagen_ensayo(codigo_muestra, ensayo_id, imagen, nombre_archivo, descripcion=None):
    """
    Guarda una imagen asociada a un ensayo específico
    
    Args:
        codigo_muestra (str): Código de la muestra
        ensayo_id (int): ID del ensayo
        imagen (PIL.Image): Objeto de imagen
        nombre_archivo (str): Nombre original del archivo
        descripcion (str, optional): Descripción de la imagen
    
    Returns:
        int: ID de la imagen guardada
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Verificar que el ensayo existe y corresponde a la muestra
    c.execute("""
    SELECT id FROM ensayos 
    WHERE id = ? AND codigo_muestra = ?
    """, (ensayo_id, codigo_muestra))
    
    if not c.fetchone():
        conn.close()
        raise ValueError(f"El ensayo ID {ensayo_id} no existe o no corresponde a la muestra {codigo_muestra}")
    
    # Convertir imagen a bytes para almacenar en SQLite
    img_byte_arr = io.BytesIO()
    imagen.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Fecha actual para la subida
    fecha_subida = datetime.now().strftime('%Y-%m-%d')
    
    c.execute("""
    INSERT INTO imagenes (codigo_muestra, ensayo_id, imagen, nombre_archivo, fecha_subida, descripcion)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (codigo_muestra, ensayo_id, img_byte_arr, nombre_archivo, fecha_subida, descripcion))
    
    # Obtener el ID de la imagen insertada
    imagen_id = c.lastrowid
    
    conn.commit()
    conn.close()
    
    return imagen_id

def obtener_imagenes(codigo_muestra, ensayo_id=None):
    """
    Recupera las imágenes asociadas a una muestra o a un ensayo específico
    
    Args:
        codigo_muestra (str): Código de la muestra
        ensayo_id (int, optional): ID del ensayo. Si se proporciona, se devuelven solo las imágenes del ensayo.
    
    Returns:
        list: Lista de tuplas (id, imagen, nombre) de imágenes
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    if ensayo_id is not None:
        # Imágenes específicas del ensayo
        c.execute("""
        SELECT id, imagen, nombre_archivo, fecha_subida, descripcion 
        FROM imagenes 
        WHERE codigo_muestra = ? AND ensayo_id = ?
        """, (codigo_muestra, ensayo_id))
    else:
        # Imágenes de la muestra (sin asociación a ensayo específico)
        c.execute("""
        SELECT id, imagen, nombre_archivo, fecha_subida, descripcion 
        FROM imagenes 
        WHERE codigo_muestra = ? AND ensayo_id IS NULL
        """, (codigo_muestra,))
    
    resultados = c.fetchall()
    
    imagenes = []
    for img_id, img_data, nombre, fecha, descripcion in resultados:
        try:
            img = Image.open(io.BytesIO(img_data))
            imagenes.append((img_id, img, nombre, fecha, descripcion))
        except Exception as e:
            print(f"Error al cargar imagen {img_id}: {str(e)}")
    
    conn.close()
    return imagenes

def obtener_imagen_por_id(imagen_id):
    """
    Recupera una imagen específica por su ID
    
    Args:
        imagen_id (int): ID de la imagen
    
    Returns:
        tuple: (imagen, nombre, fecha, descripcion) o None si no existe
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    c.execute("""
    SELECT imagen, nombre_archivo, fecha_subida, descripcion, codigo_muestra, ensayo_id
    FROM imagenes 
    WHERE id = ?
    """, (imagen_id,))
    
    resultado = c.fetchone()
    conn.close()
    
    if resultado:
        img_data, nombre, fecha, descripcion, codigo_muestra, ensayo_id = resultado
        try:
            img = Image.open(io.BytesIO(img_data))
            return (img, nombre, fecha, descripcion, codigo_muestra, ensayo_id)
        except Exception as e:
            print(f"Error al cargar imagen {imagen_id}: {str(e)}")
            return None
    else:
        return None

def obtener_muestras(filtros=None):
    """
    Obtiene todas las muestras de la base de datos, opcionalmente filtradas
    
    Args:
        filtros (dict, optional): Diccionario con filtros a aplicar
            Claves posibles: codigo, operario, fecha_inicio, fecha_fin, tipo_material, estado
    
    Returns:
        list: Lista de diccionarios con información de muestras
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Construir consulta base
    query = """
    SELECT m.*, COUNT(DISTINCT e.id) as num_ensayos
    FROM muestras m
    LEFT JOIN ensayos e ON m.codigo_muestra = e.codigo_muestra
    """
    
    where_clauses = []
    params = []
    
    # Aplicar filtros si existen
    if filtros:
        if 'codigo' in filtros and filtros['codigo']:
            where_clauses.append("m.codigo_muestra LIKE ?")
            params.append(f"%{filtros['codigo']}%")
            
        if 'operario' in filtros and filtros['operario']:
            where_clauses.append("m.operario LIKE ?")
            params.append(f"%{filtros['operario']}%")
            
        if 'fecha_inicio' in filtros and filtros['fecha_inicio']:
            where_clauses.append("m.fecha >= ?")
            params.append(filtros['fecha_inicio'])
            
        if 'fecha_fin' in filtros and filtros['fecha_fin']:
            where_clauses.append("m.fecha <= ?")
            params.append(filtros['fecha_fin'])
            
        if 'tipo_material' in filtros and filtros['tipo_material']:
            where_clauses.append("m.tipo_material = ?")
            params.append(filtros['tipo_material'])
            
        if 'estado' in filtros and filtros['estado']:
            where_clauses.append("m.estado = ?")
            params.append(filtros['estado'])
    
    # Añadir cláusulas WHERE si hay filtros
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    # Agrupar por muestra y ordenar por fecha descendente
    query += " GROUP BY m.codigo_muestra ORDER BY m.fecha DESC"
    
    c.execute(query, params)
    muestras_raw = c.fetchall()
    
    # Convertir a lista de diccionarios
    muestras = [dict(m) for m in muestras_raw]
    
    conn.close()
    return muestras

def obtener_muestra(codigo_muestra):
    """
    Obtiene información de una muestra específica
    
    Args:
        codigo_muestra (str): Código de la muestra
    
    Returns:
        dict: Información de la muestra o None si no existe
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    c.execute("SELECT * FROM muestras WHERE codigo_muestra = ?", (codigo_muestra,))
    muestra = c.fetchone()
    
    if not muestra:
        conn.close()
        return None
    
    # Convertir a diccionario
    muestra_dict = dict(muestra)
    
    # Obtener ensayos asociados
    c.execute("""
    SELECT id, tipo_ensayo, fecha_ensayo, operario, notas
    FROM ensayos
    WHERE codigo_muestra = ?
    ORDER BY fecha_ensayo DESC
    """, (codigo_muestra,))
    
    ensayos = c.fetchall()
    muestra_dict['ensayos'] = [dict(e) for e in ensayos]
    
    # Contar imágenes asociadas a la muestra
    c.execute("""
    SELECT COUNT(*) as num_imagenes
    FROM imagenes
    WHERE codigo_muestra = ? AND ensayo_id IS NULL
    """, (codigo_muestra,))
    
    resultado = c.fetchone()
    muestra_dict['num_imagenes'] = resultado[0] if resultado else 0
    
    conn.close()
    return muestra_dict

def actualizar_estado_muestra(codigo_muestra, nuevo_estado):
    """
    Actualiza el estado de una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
        nuevo_estado (str): Nuevo estado
    
    Returns:
        bool: True si la operación fue exitosa
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    c.execute("UPDATE muestras SET estado = ? WHERE codigo_muestra = ?", 
              (nuevo_estado, codigo_muestra))
    
    conn.commit()
    conn.close()
    
    return True

def eliminar_muestra(codigo_muestra):
    """
    Elimina una muestra y todos sus datos asociados
    
    Args:
        codigo_muestra (str): Código de la muestra a eliminar
    
    Returns:
        bool: True si la eliminación fue exitosa
    """
    conn = obtener_conexion()
    try:
        c = conn.cursor()
        
        # Verificar que la muestra existe
        c.execute("SELECT codigo_muestra FROM muestras WHERE codigo_muestra = ?", (codigo_muestra,))
        if not c.fetchone():
            conn.close()
            return False
        
        # Iniciar transacción
        conn.execute("BEGIN")
        
        # Obtener IDs de ensayos asociados
        c.execute("SELECT id FROM ensayos WHERE codigo_muestra = ?", (codigo_muestra,))
        ensayos_ids = [row[0] for row in c.fetchall()]
        
        # Eliminar datos de los ensayos específicos
        for ensayo_id in ensayos_ids:
            # Eliminar datos de tamices (granulometría)
            c.execute("DELETE FROM datos_tamices WHERE ensayo_id = ?", (ensayo_id,))
            
            # Eliminar datos de ensayos granulométricos
            c.execute("DELETE FROM ensayos_granulometricos WHERE ensayo_id = ?", (ensayo_id,))
            
            # Eliminar datos de otros tipos de ensayos
            c.execute("DELETE FROM ensayos_limites WHERE ensayo_id = ?", (ensayo_id,))
            c.execute("DELETE FROM ensayos_densidad_arido WHERE ensayo_id = ?", (ensayo_id,))
            c.execute("DELETE FROM ensayos_cbr WHERE ensayo_id = ?", (ensayo_id,))
            c.execute("DELETE FROM ensayos_lajas_agujas WHERE ensayo_id = ?", (ensayo_id,))
            c.execute("DELETE FROM ensayos_picnometro WHERE ensayo_id = ?", (ensayo_id,))
            c.execute("DELETE FROM ensayos_equivalente_arena WHERE ensayo_id = ?", (ensayo_id,))
            c.execute("DELETE FROM ensayos_proctor WHERE ensayo_id = ?", (ensayo_id,))
            c.execute("DELETE FROM puntos_proctor WHERE ensayo_id = ?", (ensayo_id,))
        
        # Eliminar imágenes asociadas
        c.execute("DELETE FROM imagenes WHERE codigo_muestra = ?", (codigo_muestra,))
        
        # Eliminar ensayos
        c.execute("DELETE FROM ensayos WHERE codigo_muestra = ?", (codigo_muestra,))
        
        # Eliminar la muestra
        c.execute("DELETE FROM muestras WHERE codigo_muestra = ?", (codigo_muestra,))
        
        # Confirmar transacción
        conn.execute("COMMIT")
        return True
        
    except sqlite3.Error as e:
        # Revertir cambios en caso de error
        conn.execute("ROLLBACK")
        print(f"Error al eliminar muestra: {str(e)}")
        return False
    finally:
        conn.close()

def obtener_tipos_materiales():
    """
    Obtiene la lista de tipos de materiales registrados
    
    Returns:
        list: Lista de tipos de materiales únicos
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    c.execute("SELECT DISTINCT tipo_material FROM muestras ORDER BY tipo_material")
    tipos = [row[0] for row in c.fetchall()]
    
    conn.close()
    return tipos

def obtener_estados_muestras():
    """
    Obtiene la lista de estados de muestras registrados
    
    Returns:
        list: Lista de estados únicos
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    c.execute("SELECT DISTINCT estado FROM muestras ORDER BY estado")
    estados = [row[0] for row in c.fetchall()]
    
    conn.close()
    return estados

def obtener_operarios():
    """
    Obtiene la lista de operarios registrados
    
    Returns:
        list: Lista de operarios únicos
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    c.execute("SELECT DISTINCT operario FROM muestras ORDER BY operario")
    operarios = [row[0] for row in c.fetchall()]
    
    conn.close()
    return operarios

def obtener_estadisticas_muestras():
    """
    Obtiene estadísticas básicas sobre las muestras y ensayos
    
    Returns:
        dict: Diccionario con estadísticas
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Total de muestras
    c.execute("SELECT COUNT(*) FROM muestras")
    total_muestras = c.fetchone()[0]
    
    # Total de ensayos
    c.execute("SELECT COUNT(*) FROM ensayos")
    total_ensayos = c.fetchone()[0]
    
    # Ensayos por tipo
    c.execute("SELECT tipo_ensayo, COUNT(*) FROM ensayos GROUP BY tipo_ensayo")
    ensayos_por_tipo = {row[0]: row[1] for row in c.fetchall()}
    
    # Muestras por tipo de material
    c.execute("SELECT tipo_material, COUNT(*) FROM muestras GROUP BY tipo_material")
    muestras_por_tipo = {row[0]: row[1] for row in c.fetchall()}
    
    # Muestras por estado
    c.execute("SELECT estado, COUNT(*) FROM muestras GROUP BY estado")
    muestras_por_estado = {row[0]: row[1] for row in c.fetchall()}
    
    # Ensayos recientes (último mes)
    c.execute("""
    SELECT COUNT(*) FROM ensayos 
    WHERE fecha_ensayo >= date('now', '-30 days')
    """)
    ensayos_recientes = c.fetchone()[0]
    
    conn.close()
    
    return {
        "total_muestras": total_muestras,
        "total_ensayos": total_ensayos,
        "ensayos_por_tipo": ensayos_por_tipo,
        "muestras_por_tipo": muestras_por_tipo,
        "muestras_por_estado": muestras_por_estado,
        "ensayos_recientes": ensayos_recientes
    }