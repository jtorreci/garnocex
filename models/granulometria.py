import sqlite3
from models.db import obtener_conexion
from models.muestras import actualizar_estado_muestra

def guardar_ensayo_granulometrico(codigo_muestra, fecha_ensayo, operario, masa_total, datos_tamices, d10, d30, d60, cu, cc):
    """
    Guarda un ensayo granulométrico y sus datos asociados
    
    Args:
        codigo_muestra (str): Código de la muestra
        fecha_ensayo (date): Fecha del ensayo
        operario (str): Nombre del operario
        masa_total (float): Masa total de la muestra
        datos_tamices (list): Lista de diccionarios con datos de tamices
        d10 (float): Diámetro D10
        d30 (float): Diámetro D30
        d60 (float): Diámetro D60
        cu (float): Coeficiente de uniformidad
        cc (float): Coeficiente de curvatura
        
    Returns:
        int: ID del ensayo guardado
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    try:
        # Iniciar transacción
        conn.execute("BEGIN")
        
        # Insertar datos del ensayo
        c.execute("""
        INSERT INTO ensayos_granulometricos 
        (codigo_muestra, fecha_ensayo, operario, masa_total, d10, d30, d60, coef_uniformidad, coef_curvatura)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (codigo_muestra, fecha_ensayo, operario, masa_total, d10, d30, d60, cu, cc))
        
        # Obtener el ID del ensayo insertado
        ensayo_id = c.lastrowid
        
        # Insertar datos de los tamices
        for dato in datos_tamices:
            c.execute("""
            INSERT INTO datos_tamices 
            (ensayo_id, tamiz, apertura, masa_retenida, porcentaje_retenido, 
             porcentaje_retenido_acumulado, porcentaje_pasa)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ensayo_id,
                dato["tamiz"],
                dato["apertura"],
                dato["masa_retenida"],
                dato["porcentaje_retenido"],
                dato["porcentaje_retenido_acumulado"],
                dato["porcentaje_pasa"]
            ))
        
        # Confirmar transacción
        conn.execute("COMMIT")
        
        # Actualizar estado de la muestra
        actualizar_estado_muestra(codigo_muestra, "con ensayo granulométrico")
        
        return ensayo_id
        
    except Exception as e:
        # Revertir cambios en caso de error
        conn.execute("ROLLBACK")
        raise e
    
    finally:
        conn.close()

def obtener_ensayo_granulometrico(codigo_muestra):
    """
    Obtiene el último ensayo granulométrico de una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
        
    Returns:
        dict: Información del ensayo o None si no existe
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Obtener ensayo
    c.execute("""
    SELECT * FROM ensayos_granulometricos 
    WHERE codigo_muestra = ? 
    ORDER BY id DESC LIMIT 1
    """, (codigo_muestra,))
    
    ensayo = c.fetchone()
    
    if not ensayo:
        conn.close()
        return None
    
    # Convertir a diccionario
    ensayo_dict = dict(ensayo)
    
    # Obtener datos de tamices
    c.execute("""
    SELECT * FROM datos_tamices 
    WHERE ensayo_id = ? 
    ORDER BY apertura DESC
    """, (ensayo['id'],))
    
    tamices = [dict(row) for row in c.fetchall()]
    ensayo_dict['tamices'] = tamices
    
    conn.close()
    return ensayo_dict

def obtener_todos_ensayos_granulometricos(codigo_muestra=None):
    """
    Obtiene todos los ensayos granulométricos, opcionalmente filtrados por muestra
    
    Args:
        codigo_muestra (str, optional): Código de la muestra para filtrar
        
    Returns:
        list: Lista de ensayos granulométricos
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    if codigo_muestra:
        c.execute("""
        SELECT eg.*, m.codigo_muestra 
        FROM ensayos_granulometricos eg
        JOIN muestras m ON eg.codigo_muestra = m.codigo_muestra
        WHERE eg.codigo_muestra = ?
        ORDER BY eg.fecha_ensayo DESC
        """, (codigo_muestra,))
    else:
        c.execute("""
        SELECT eg.*, m.codigo_muestra 
        FROM ensayos_granulometricos eg
        JOIN muestras m ON eg.codigo_muestra = m.codigo_muestra
        ORDER BY eg.fecha_ensayo DESC
        """)
    
    ensayos = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return ensayos