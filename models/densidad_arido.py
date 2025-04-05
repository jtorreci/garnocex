import sqlite3
from models.db import obtener_conexion
from models.muestras import actualizar_estado_muestra

def guardar_ensayo_densidad_arido(codigo_muestra, fecha_ensayo, operario, 
                                 masa_seca, masa_sss, masa_sumergida,
                                 densidad_aparente, densidad_tras_secado, densidad_sss, absorcion_agua,
                                 notas=None):
    """
    Guarda un ensayo de densidad de árido grueso y sus datos asociados
    
    Args:
        codigo_muestra (str): Código de la muestra
        fecha_ensayo (date): Fecha del ensayo
        operario (str): Nombre del operario
        masa_seca (float): Masa seca de la muestra en gramos
        masa_sss (float): Masa saturada superficie seca en gramos
        masa_sumergida (float): Masa sumergida en gramos
        densidad_aparente (float): Densidad aparente en g/cm³
        densidad_tras_secado (float): Densidad tras secado en g/cm³
        densidad_sss (float): Densidad SSS en g/cm³
        absorcion_agua (float): Absorción de agua en porcentaje
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
        """, (codigo_muestra, "Densidad de Árido Grueso", fecha_ensayo, operario, notas))
        
        # Obtener el ID del ensayo insertado
        ensayo_id = c.lastrowid
        
        # Insertar datos específicos del ensayo
        c.execute("""
        INSERT INTO ensayos_densidad_arido (
            ensayo_id, densidad_aparente, densidad_tras_secado, densidad_sss, 
            absorcion_agua, masa_sumergida, masa_sss, masa_seca
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ensayo_id, 
            densidad_aparente, 
            densidad_tras_secado, 
            densidad_sss, 
            absorcion_agua, 
            masa_sumergida, 
            masa_sss, 
            masa_seca
        ))
        
        # Confirmar transacción
        conn.execute("COMMIT")
        
        # Actualizar estado de la muestra
        actualizar_estado_muestra(codigo_muestra, "con ensayo de densidad de árido")
        
        return ensayo_id
        
    except Exception as e:
        # Revertir cambios en caso de error
        conn.execute("ROLLBACK")
        raise e
    
    finally:
        conn.close()

def obtener_ensayo_densidad_arido(codigo_muestra):
    """
    Obtiene el último ensayo de densidad de árido de una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
        
    Returns:
        dict: Información del ensayo o None si no existe
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Obtener ensayo
    c.execute("""
    SELECT e.*, d.*
    FROM ensayos e
    JOIN ensayos_densidad_arido d ON e.id = d.ensayo_id
    WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Densidad de Árido Grueso'
    ORDER BY e.fecha_ensayo DESC LIMIT 1
    """, (codigo_muestra,))
    
    ensayo = c.fetchone()
    conn.close()
    
    if not ensayo:
        return None
    
    # Convertir a diccionario
    return dict(ensayo)

def obtener_todos_ensayos_densidad_arido(codigo_muestra=None):
    """
    Obtiene todos los ensayos de densidad de árido grueso, opcionalmente filtrados por muestra
    
    Args:
        codigo_muestra (str, optional): Código de la muestra para filtrar
        
    Returns:
        list: Lista de ensayos de densidad de árido
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    if codigo_muestra:
        c.execute("""
        SELECT e.*, d.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_densidad_arido d ON e.id = d.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Densidad de Árido Grueso'
        ORDER BY e.fecha_ensayo DESC
        """, (codigo_muestra,))
    else:
        c.execute("""
        SELECT e.*, d.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_densidad_arido d ON e.id = d.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.tipo_ensayo = 'Densidad de Árido Grueso'
        ORDER BY e.fecha_ensayo DESC
        """)
    
    ensayos = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return ensayos

def calcular_parametros_densidad(masa_seca, masa_sss, masa_sumergida):
    """
    Calcula los parámetros del ensayo de densidad de árido grueso
    
    Args:
        masa_seca (float): Masa seca en gramos
        masa_sss (float): Masa saturada superficie seca en gramos
        masa_sumergida (float): Masa sumergida en gramos
        
    Returns:
        tuple: (densidad_aparente, densidad_tras_secado, densidad_sss, absorcion_agua)
    """
    # Validar datos
    if masa_sumergida >= masa_sss or masa_sumergida >= masa_seca:
        raise ValueError("La masa sumergida debe ser menor que la masa seca y SSS")
    
    if masa_sss < masa_seca:
        raise ValueError("La masa SSS debe ser mayor o igual a la masa seca")
    
    # Calcular densidades
    densidad_aparente = masa_seca / (masa_sss - masa_sumergida)
    densidad_tras_secado = masa_seca / (masa_seca - masa_sumergida)
    densidad_sss = masa_sss / (masa_sss - masa_sumergida)
    
    # Calcular absorción de agua
    absorcion_agua = ((masa_sss - masa_seca) / masa_seca) * 100
    
    return (densidad_aparente, densidad_tras_secado, densidad_sss, absorcion_agua)