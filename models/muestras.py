import io
import sqlite3
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

def guardar_imagen(codigo_muestra, imagen, nombre_archivo):
    """
    Guarda una imagen asociada a una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
        imagen (PIL.Image): Objeto de imagen
        nombre_archivo (str): Nombre original del archivo
    
    Returns:
        int: ID de la imagen guardada
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Convertir imagen a bytes para almacenar en SQLite
    img_byte_arr = io.BytesIO()
    imagen.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    c.execute("INSERT INTO imagenes (codigo_muestra, imagen, nombre_archivo) VALUES (?, ?, ?)",
              (codigo_muestra, img_byte_arr, nombre_archivo))
    
    # Obtener el ID de la imagen insertada
    imagen_id = c.lastrowid
    
    conn.commit()
    conn.close()
    
    return imagen_id

def obtener_imagenes(codigo_muestra):
    """
    Recupera las imágenes asociadas a una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
    
    Returns:
        list: Lista de tuplas (id, imagen, nombre) de imágenes
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    c.execute("SELECT id, imagen, nombre_archivo FROM imagenes WHERE codigo_muestra = ?", (codigo_muestra,))
    resultados = c.fetchall()
    
    imagenes = []
    for img_id, img_data, nombre in resultados:
        img = Image.open(io.BytesIO(img_data))
        imagenes.append((img_id, img, nombre))
    
    conn.close()
    return imagenes

def obtener_muestras():
    """
    Obtiene todas las muestras de la base de datos
    
    Returns:
        list: Lista de diccionarios con información de muestras
    """
    conn = obtener_conexion()
    # No sobrescribir row_factory si ya está configurado en obtener_conexion
    c = conn.cursor()
    
    c.execute("SELECT * FROM muestras ORDER BY fecha DESC")
    muestras_raw = c.fetchall()
    
    # Convertir a diccionarios manualmente si es necesario
    muestras = []
    for row in muestras_raw:
        if isinstance(row, sqlite3.Row):
            muestras.append(dict(row))
        else:
            # Si no es Row, crear diccionario manualmente 
            # (esto depende de cómo está configurado tu cursor)
            # Suponiendo que conocemos el orden de las columnas
            columns = ["codigo_muestra", "operario", "fecha", "tipo_material", "estado", "notas"]
            muestras.append(dict(zip(columns, row)))
    
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
    
    # Si muestra no es None, convertir a diccionario
    result = None
    if muestra:
        if isinstance(muestra, sqlite3.Row):
            result = dict(muestra)
        else:
            # Si no es Row, crear diccionario manualmente
            columns = ["codigo_muestra", "operario", "fecha", "tipo_material", "estado", "notas"]
            result = dict(zip(columns, muestra))
    
    conn.close()
    return result

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