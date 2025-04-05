import sqlite3
from models.db import obtener_conexion
from models.muestras import actualizar_estado_muestra

def guardar_ensayo_cbr(codigo_muestra, fecha_ensayo, operario, 
                      energia_compactacion, densidad_seca, humedad_inicial, humedad_final,
                      hinchamiento, indice_cbr, absorcion_agua, dias_inmersion, sobrecarga,
                      notas=None):
    """
    Guarda un ensayo CBR y sus datos asociados
    
    Args:
        codigo_muestra (str): Código de la muestra
        fecha_ensayo (date): Fecha del ensayo
        operario (str): Nombre del operario
        energia_compactacion (float): Energía de compactación en J/m³
        densidad_seca (float): Densidad seca en g/cm³
        humedad_inicial (float): Humedad inicial en porcentaje
        humedad_final (float): Humedad final en porcentaje
        hinchamiento (float): Hinchamiento en porcentaje
        indice_cbr (float): Índice CBR
        absorcion_agua (float): Absorción de agua en porcentaje
        dias_inmersion (int): Días de inmersión
        sobrecarga (float): Sobrecarga en kg
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
        """, (codigo_muestra, "CBR", fecha_ensayo, operario, notas))
        
        # Obtener el ID del ensayo insertado
        ensayo_id = c.lastrowid
        
        # Insertar datos específicos del ensayo
        c.execute("""
        INSERT INTO ensayos_cbr (
            ensayo_id, energia_compactacion, densidad_seca, humedad_inicial, humedad_final,
            hinchamiento, indice_cbr, absorcion_agua, dias_inmersion, sobrecarga
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ensayo_id, energia_compactacion, densidad_seca, humedad_inicial, humedad_final,
            hinchamiento, indice_cbr, absorcion_agua, dias_inmersion, sobrecarga
        ))
        
        # Confirmar transacción
        conn.execute("COMMIT")
        
        # Actualizar estado de la muestra
        actualizar_estado_muestra(codigo_muestra, "con ensayo CBR")
        
        return ensayo_id
        
    except Exception as e:
        # Revertir cambios en caso de error
        conn.execute("ROLLBACK")
        raise e
    
    finally:
        conn.close()

def obtener_ensayo_cbr(codigo_muestra):
    """
    Obtiene el último ensayo CBR de una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
        
    Returns:
        dict: Información del ensayo o None si no existe
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Obtener ensayo
    c.execute("""
    SELECT e.*, c.*
    FROM ensayos e
    JOIN ensayos_cbr c ON e.id = c.ensayo_id
    WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'CBR'
    ORDER BY e.fecha_ensayo DESC LIMIT 1
    """, (codigo_muestra,))
    
    ensayo = c.fetchone()
    conn.close()
    
    if not ensayo:
        return None
    
    # Convertir a diccionario
    return dict(ensayo)

def obtener_todos_ensayos_cbr(codigo_muestra=None):
    """
    Obtiene todos los ensayos CBR, opcionalmente filtrados por muestra
    
    Args:
        codigo_muestra (str, optional): Código de la muestra para filtrar
        
    Returns:
        list: Lista de ensayos CBR
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    if codigo_muestra:
        c.execute("""
        SELECT e.*, c.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_cbr c ON e.id = c.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'CBR'
        ORDER BY e.fecha_ensayo DESC
        """, (codigo_muestra,))
    else:
        c.execute("""
        SELECT e.*, c.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_cbr c ON e.id = c.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.tipo_ensayo = 'CBR'
        ORDER BY e.fecha_ensayo DESC
        """)
    
    ensayos = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return ensayos

def calcular_hinchamiento(altura_inicial, altura_final):
    """
    Calcula el hinchamiento en porcentaje
    
    Args:
        altura_inicial (float): Altura inicial de la muestra en mm
        altura_final (float): Altura final de la muestra después de la inmersión en mm
        
    Returns:
        float: Hinchamiento en porcentaje
    """
    return ((altura_final - altura_inicial) / altura_inicial) * 100

def calcular_absorcion_agua(masa_inicial, masa_final):
    """
    Calcula la absorción de agua en porcentaje
    
    Args:
        masa_inicial (float): Masa inicial de la muestra en g
        masa_final (float): Masa final de la muestra después de la inmersión en g
        
    Returns:
        float: Absorción de agua en porcentaje
    """
    return ((masa_final - masa_inicial) / masa_inicial) * 100

def interpretar_resultado_cbr(indice_cbr):
    """
    Interpreta el resultado del ensayo CBR según valores típicos
    
    Args:
        indice_cbr (float): Índice CBR
        
    Returns:
        str: Interpretación del resultado
    """
    if indice_cbr < 3:
        return "Muy pobre (subrasante)"
    elif indice_cbr < 7:
        return "Pobre a regular (subrasante)"
    elif indice_cbr < 20:
        return "Regular (subbase)"
    elif indice_cbr < 50:
        return "Bueno (base)"
    else:
        return "Excelente (base)"