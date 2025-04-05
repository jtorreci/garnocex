import sqlite3
from models.db import obtener_conexion
from models.muestras import actualizar_estado_muestra

def guardar_ensayo_lajas_agujas(codigo_muestra, fecha_ensayo, operario, 
                               masa_total, masa_lajas, masa_agujas,
                               indice_lajas, indice_agujas, notas=None):
    """
    Guarda un ensayo de índice de lajas y agujas y sus datos asociados
    
    Args:
        codigo_muestra (str): Código de la muestra
        fecha_ensayo (date): Fecha del ensayo
        operario (str): Nombre del operario
        masa_total (float): Masa total de la muestra en gramos
        masa_lajas (float): Masa de las partículas con forma de laja en gramos
        masa_agujas (float): Masa de las partículas con forma de aguja en gramos
        indice_lajas (float): Índice de lajas en porcentaje
        indice_agujas (float): Índice de agujas en porcentaje
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
        """, (codigo_muestra, "Índice de Lajas y Agujas", fecha_ensayo, operario, notas))
        
        # Obtener el ID del ensayo insertado
        ensayo_id = c.lastrowid
        
        # Insertar datos específicos del ensayo
        c.execute("""
        INSERT INTO ensayos_lajas_agujas (
            ensayo_id, indice_lajas, indice_agujas, masa_total, masa_lajas, masa_agujas
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (ensayo_id, indice_lajas, indice_agujas, masa_total, masa_lajas, masa_agujas))
        
        # Confirmar transacción
        conn.execute("COMMIT")
        
        # Actualizar estado de la muestra
        actualizar_estado_muestra(codigo_muestra, "con ensayo de lajas y agujas")
        
        return ensayo_id
        
    except Exception as e:
        # Revertir cambios en caso de error
        conn.execute("ROLLBACK")
        raise e
    
    finally:
        conn.close()

def obtener_ensayo_lajas_agujas(codigo_muestra):
    """
    Obtiene el último ensayo de índice de lajas y agujas de una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
        
    Returns:
        dict: Información del ensayo o None si no existe
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Obtener ensayo
    c.execute("""
    SELECT e.*, l.*
    FROM ensayos e
    JOIN ensayos_lajas_agujas l ON e.id = l.ensayo_id
    WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Índice de Lajas y Agujas'
    ORDER BY e.fecha_ensayo DESC LIMIT 1
    """, (codigo_muestra,))
    
    ensayo = c.fetchone()
    conn.close()
    
    if not ensayo:
        return None
    
    # Convertir a diccionario
    return dict(ensayo)

def obtener_todos_ensayos_lajas_agujas(codigo_muestra=None):
    """
    Obtiene todos los ensayos de índice de lajas y agujas, opcionalmente filtrados por muestra
    
    Args:
        codigo_muestra (str, optional): Código de la muestra para filtrar
        
    Returns:
        list: Lista de ensayos de índice de lajas y agujas
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    if codigo_muestra:
        c.execute("""
        SELECT e.*, l.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_lajas_agujas l ON e.id = l.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Índice de Lajas y Agujas'
        ORDER BY e.fecha_ensayo DESC
        """, (codigo_muestra,))
    else:
        c.execute("""
        SELECT e.*, l.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_lajas_agujas l ON e.id = l.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.tipo_ensayo = 'Índice de Lajas y Agujas'
        ORDER BY e.fecha_ensayo DESC
        """)
    
    ensayos = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return ensayos

def calcular_indices_lajas_agujas(masa_total, masa_lajas, masa_agujas):
    """
    Calcula los índices de lajas y agujas
    
    Args:
        masa_total (float): Masa total de la muestra en gramos
        masa_lajas (float): Masa de las partículas con forma de laja en gramos
        masa_agujas (float): Masa de las partículas con forma de aguja en gramos
        
    Returns:
        tuple: (indice_lajas, indice_agujas) en porcentaje
    """
    # Validar datos
    if masa_total <= 0:
        raise ValueError("La masa total debe ser mayor que cero")
    
    if masa_lajas < 0 or masa_agujas < 0:
        raise ValueError("Las masas de lajas y agujas no pueden ser negativas")
    
    if masa_lajas + masa_agujas > masa_total:
        raise ValueError("La suma de masa de lajas y agujas no puede superar la masa total")
    
    # Calcular índices
    indice_lajas = (masa_lajas / masa_total) * 100
    indice_agujas = (masa_agujas / masa_total) * 100
    
    return indice_lajas, indice_agujas

def interpretar_indices(indice_lajas, indice_agujas):
    """
    Interpreta los índices de lajas y agujas según normativas (UNE-EN 933-3 y UNE-EN 933-4)
    
    Args:
        indice_lajas (float): Índice de lajas en porcentaje
        indice_agujas (float): Índice de agujas en porcentaje
        
    Returns:
        tuple: (interpretacion_lajas, interpretacion_agujas)
    """
    # Interpretación índice de lajas
    if indice_lajas <= 10:
        interpretacion_lajas = "Muy buena forma (IL ≤ 10%)"
    elif indice_lajas <= 20:
        interpretacion_lajas = "Buena forma (10% < IL ≤ 20%)"
    elif indice_lajas <= 35:
        interpretacion_lajas = "Forma aceptable (20% < IL ≤ 35%)"
    else:
        interpretacion_lajas = "Mala forma (IL > 35%)"
    
    # Interpretación índice de agujas
    if indice_agujas <= 10:
        interpretacion_agujas = "Muy buena forma (IA ≤ 10%)"
    elif indice_agujas <= 20:
        interpretacion_agujas = "Buena forma (10% < IA ≤ 20%)"
    elif indice_agujas <= 35:
        interpretacion_agujas = "Forma aceptable (20% < IA ≤ 35%)"
    else:
        interpretacion_agujas = "Mala forma (IA > 35%)"
    
    return interpretacion_lajas, interpretacion_agujas