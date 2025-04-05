import sqlite3
from models.db import obtener_conexion
from models.muestras import actualizar_estado_muestra

def guardar_ensayo_limites(codigo_muestra, fecha_ensayo, operario, 
                         limite_liquido, limite_plastico, indice_plasticidad,
                         notas=None):
    """
    Guarda un ensayo de límites de Atterberg y sus datos asociados
    
    Args:
        codigo_muestra (str): Código de la muestra
        fecha_ensayo (date): Fecha del ensayo
        operario (str): Nombre del operario
        limite_liquido (float): Límite líquido en porcentaje
        limite_plastico (float): Límite plástico en porcentaje
        indice_plasticidad (float): Índice de plasticidad en porcentaje
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
        """, (codigo_muestra, "Límites de Atterberg", fecha_ensayo, operario, notas))
        
        # Obtener el ID del ensayo insertado
        ensayo_id = c.lastrowid
        
        # Insertar datos específicos del ensayo
        c.execute("""
        INSERT INTO ensayos_limites (ensayo_id, limite_liquido, limite_plastico, indice_plasticidad)
        VALUES (?, ?, ?, ?)
        """, (ensayo_id, limite_liquido, limite_plastico, indice_plasticidad))
        
        # Confirmar transacción
        conn.execute("COMMIT")
        
        # Actualizar estado de la muestra
        actualizar_estado_muestra(codigo_muestra, "con ensayo de límites")
        
        return ensayo_id
        
    except Exception as e:
        # Revertir cambios en caso de error
        conn.execute("ROLLBACK")
        raise e
    
    finally:
        conn.close()

def obtener_ensayo_limites(codigo_muestra):
    """
    Obtiene el último ensayo de límites de Atterberg de una muestra
    
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
    JOIN ensayos_limites l ON e.id = l.ensayo_id
    WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Límites de Atterberg'
    ORDER BY e.fecha_ensayo DESC LIMIT 1
    """, (codigo_muestra,))
    
    ensayo = c.fetchone()
    conn.close()
    
    if not ensayo:
        return None
    
    # Convertir a diccionario
    return dict(ensayo)

def obtener_todos_ensayos_limites(codigo_muestra=None):
    """
    Obtiene todos los ensayos de límites de Atterberg, opcionalmente filtrados por muestra
    
    Args:
        codigo_muestra (str, optional): Código de la muestra para filtrar
        
    Returns:
        list: Lista de ensayos de límites
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    if codigo_muestra:
        c.execute("""
        SELECT e.*, l.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_limites l ON e.id = l.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Límites de Atterberg'
        ORDER BY e.fecha_ensayo DESC
        """, (codigo_muestra,))
    else:
        c.execute("""
        SELECT e.*, l.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_limites l ON e.id = l.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.tipo_ensayo = 'Límites de Atterberg'
        ORDER BY e.fecha_ensayo DESC
        """)
    
    ensayos = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return ensayos

def calcular_indice_plasticidad(limite_liquido, limite_plastico):
    """
    Calcula el índice de plasticidad a partir del límite líquido y plástico
    
    Args:
        limite_liquido (float): Límite líquido en porcentaje
        limite_plastico (float): Límite plástico en porcentaje
        
    Returns:
        float: Índice de plasticidad
    """
    # Validar datos
    if limite_liquido < limite_plastico:
        raise ValueError("El límite líquido debe ser mayor o igual al límite plástico")
    
    return limite_liquido - limite_plastico

def obtener_clasificacion_sucs(limite_liquido, indice_plasticidad):
    """
    Obtiene la clasificación SUCS según Carta de Plasticidad de Casagrande
    
    Args:
        limite_liquido (float): Límite líquido en porcentaje
        indice_plasticidad (float): Índice de plasticidad en porcentaje
        
    Returns:
        str: Clasificación SUCS
    """
    # No plástico
    if indice_plasticidad < 4:
        if limite_liquido < 50:
            return "ML - Limo de baja plasticidad"
        else:
            return "MH - Limo de alta plasticidad"
    
    # Línea A: IP = 0.73 * (LL - 20)
    valor_linea_a = 0.73 * (limite_liquido - 20)
    
    if limite_liquido < 50:  # Baja plasticidad
        if indice_plasticidad > valor_linea_a:
            return "CL - Arcilla de baja plasticidad"
        else:
            return "CI - Arcilla-Limo de baja plasticidad"
    else:  # Alta plasticidad
        if indice_plasticidad > valor_linea_a:
            return "CH - Arcilla de alta plasticidad"
        else:
            return "MH - Limo de alta plasticidad"