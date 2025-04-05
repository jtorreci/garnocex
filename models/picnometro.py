import sqlite3
from models.db import obtener_conexion
from models.muestras import actualizar_estado_muestra

def guardar_ensayo_picnometro(codigo_muestra, fecha_ensayo, operario, 
                             densidad_aparente, volumen_hoyo, masa_arena_empleada,
                             masa_arena_cono, densidad_arena, notas=None):
    """
    Guarda un ensayo de picnómetro de arena y sus datos asociados
    
    Args:
        codigo_muestra (str): Código de la muestra
        fecha_ensayo (date): Fecha del ensayo
        operario (str): Nombre del operario
        densidad_aparente (float): Densidad aparente en g/cm³
        volumen_hoyo (float): Volumen del hoyo en cm³
        masa_arena_empleada (float): Masa total de arena empleada en g
        masa_arena_cono (float): Masa de arena en el cono en g
        densidad_arena (float): Densidad de la arena de calibración en g/cm³
        notas (str, optional): Notas adicionales sobre el ensayo
        
    Returns:
        int: ID del ensayo guardado
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    try:
        # Iniciar transacción
        conn.execute("BEGIN")
        
        # Insertar en la tabla general de ensayos
        c.execute("""
        INSERT INTO ensayos (codigo_muestra, tipo_ensayo, fecha_ensayo, operario, notas)
        VALUES (?, ?, ?, ?, ?)
        """, (codigo_muestra, "Picnómetro de Arena", fecha_ensayo, operario, notas))
        
        # Obtener el ID del ensayo insertado
        ensayo_id = c.lastrowid
        
        # Insertar datos específicos del ensayo
        c.execute("""
        INSERT INTO ensayos_picnometro (
            ensayo_id, densidad_aparente, volumen_hoyo, masa_arena_empleada,
            masa_arena_cono, densidad_arena
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ensayo_id, densidad_aparente, volumen_hoyo, masa_arena_empleada,
            masa_arena_cono, densidad_arena
        ))
        
        # Confirmar transacción
        conn.execute("COMMIT")
        
        # Actualizar estado de la muestra
        actualizar_estado_muestra(codigo_muestra, "con ensayo de picnómetro")
        
        return ensayo_id
        
    except Exception as e:
        # Revertir cambios en caso de error
        conn.execute("ROLLBACK")
        raise e
    
    finally:
        conn.close()

def obtener_ensayo_picnometro(codigo_muestra):
    """
    Obtiene el último ensayo de picnómetro de arena de una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
        
    Returns:
        dict: Información del ensayo o None si no existe
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Obtener ensayo
    c.execute("""
    SELECT e.*, p.*
    FROM ensayos e
    JOIN ensayos_picnometro p ON e.id = p.ensayo_id
    WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Picnómetro de Arena'
    ORDER BY e.fecha_ensayo DESC LIMIT 1
    """, (codigo_muestra,))
    
    ensayo = c.fetchone()
    conn.close()
    
    if not ensayo:
        return None
    
    # Convertir a diccionario
    return dict(ensayo)

def obtener_todos_ensayos_picnometro(codigo_muestra=None):
    """
    Obtiene todos los ensayos de picnómetro de arena, opcionalmente filtrados por muestra
    
    Args:
        codigo_muestra (str, optional): Código de la muestra para filtrar
        
    Returns:
        list: Lista de ensayos de picnómetro de arena
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    if codigo_muestra:
        c.execute("""
        SELECT e.*, p.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_picnometro p ON e.id = p.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Picnómetro de Arena'
        ORDER BY e.fecha_ensayo DESC
        """, (codigo_muestra,))
    else:
        c.execute("""
        SELECT e.*, p.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_picnometro p ON e.id = p.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.tipo_ensayo = 'Picnómetro de Arena'
        ORDER BY e.fecha_ensayo DESC
        """)
    
    ensayos = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return ensayos

def calcular_volumen_hoyo(masa_arena_empleada, masa_arena_cono, densidad_arena):
    """
    Calcula el volumen del hoyo
    
    Args:
        masa_arena_empleada (float): Masa total de arena empleada en g
        masa_arena_cono (float): Masa de arena en el cono en g
        densidad_arena (float): Densidad de la arena de calibración en g/cm³
        
    Returns:
        float: Volumen del hoyo en cm³
    """
    # Masa de arena en el hoyo = Masa total - Masa en el cono
    masa_arena_hoyo = masa_arena_empleada - masa_arena_cono
    
    # Volumen = Masa / Densidad
    volumen_hoyo = masa_arena_hoyo / densidad_arena
    
    return volumen_hoyo

def calcular_densidad_aparente(masa_suelo, volumen_hoyo):
    """
    Calcula la densidad aparente del suelo
    
    Args:
        masa_suelo (float): Masa del suelo extraído del hoyo en g
        volumen_hoyo (float): Volumen del hoyo en cm³
        
    Returns:
        float: Densidad aparente en g/cm³
    """
    return masa_suelo / volumen_hoyo

def interpretar_densidad(densidad_aparente, tipo_suelo="suelo"):
    """
    Interpreta la densidad aparente según el tipo de suelo
    
    Args:
        densidad_aparente (float): Densidad aparente en g/cm³
        tipo_suelo (str): Tipo de suelo ("suelo", "arena", "arcilla")
        
    Returns:
        str: Interpretación de la densidad
    """
    if tipo_suelo.lower() == "suelo":
        if densidad_aparente < 1.2:
            return "Muy baja densidad (menos de 1.2 g/cm³)"
        elif densidad_aparente < 1.4:
            return "Baja densidad (1.2 - 1.4 g/cm³)"
        elif densidad_aparente < 1.6:
            return "Densidad media (1.4 - 1.6 g/cm³)"
        elif densidad_aparente < 1.8:
            return "Alta densidad (1.6 - 1.8 g/cm³)"
        else:
            return "Muy alta densidad (más de 1.8 g/cm³)"
    
    elif tipo_suelo.lower() == "arena":
        if densidad_aparente < 1.4:
            return "Baja densidad para arena (menos de 1.4 g/cm³)"
        elif densidad_aparente < 1.6:
            return "Densidad normal para arena (1.4 - 1.6 g/cm³)"
        else:
            return "Alta densidad para arena (más de 1.6 g/cm³)"
    
    elif tipo_suelo.lower() == "arcilla":
        if densidad_aparente < 1.6:
            return "Baja densidad para arcilla (menos de 1.6 g/cm³)"
        elif densidad_aparente < 1.8:
            return "Densidad normal para arcilla (1.6 - 1.8 g/cm³)"
        else:
            return "Alta densidad para arcilla (más de 1.8 g/cm³)"
    
    return "Tipo de suelo no reconocido para interpretación"