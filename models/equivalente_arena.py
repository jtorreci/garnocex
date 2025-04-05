import sqlite3
from models.db import obtener_conexion
from models.muestras import actualizar_estado_muestra

def guardar_ensayo_equivalente_arena(codigo_muestra, fecha_ensayo, operario, 
                                   altura_sedimento, altura_floculos, equivalente_arena,
                                   temperatura, notas=None):
    """
    Guarda un ensayo de equivalente de arena y sus datos asociados
    
    Args:
        codigo_muestra (str): Código de la muestra
        fecha_ensayo (date): Fecha del ensayo
        operario (str): Nombre del operario
        altura_sedimento (float): Altura del sedimento en mm
        altura_floculos (float): Altura de los flóculos en mm
        equivalente_arena (float): Valor del equivalente de arena en porcentaje
        temperatura (float): Temperatura durante el ensayo en °C
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
        """, (codigo_muestra, "Equivalente de Arena", fecha_ensayo, operario, notas))
        
        # Obtener el ID del ensayo insertado
        ensayo_id = c.lastrowid
        
        # Insertar datos específicos del ensayo
        c.execute("""
        INSERT INTO ensayos_equivalente_arena (
            ensayo_id, altura_sedimento, altura_floculos, equivalente_arena, temperatura
        )
        VALUES (?, ?, ?, ?, ?)
        """, (ensayo_id, altura_sedimento, altura_floculos, equivalente_arena, temperatura))
        
        # Confirmar transacción
        conn.execute("COMMIT")
        
        # Actualizar estado de la muestra
        actualizar_estado_muestra(codigo_muestra, "con ensayo de equivalente de arena")
        
        return ensayo_id
        
    except Exception as e:
        # Revertir cambios en caso de error
        conn.execute("ROLLBACK")
        raise e
    
    finally:
        conn.close()

def obtener_ensayo_equivalente_arena(codigo_muestra):
    """
    Obtiene el último ensayo de equivalente de arena de una muestra
    
    Args:
        codigo_muestra (str): Código de la muestra
        
    Returns:
        dict: Información del ensayo o None si no existe
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Obtener ensayo
    c.execute("""
    SELECT e.*, ea.*
    FROM ensayos e
    JOIN ensayos_equivalente_arena ea ON e.id = ea.ensayo_id
    WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Equivalente de Arena'
    ORDER BY e.fecha_ensayo DESC LIMIT 1
    """, (codigo_muestra,))
    
    ensayo = c.fetchone()
    conn.close()
    
    if not ensayo:
        return None
    
    # Convertir a diccionario
    return dict(ensayo)

def obtener_todos_ensayos_equivalente_arena(codigo_muestra=None):
    """
    Obtiene todos los ensayos de equivalente de arena, opcionalmente filtrados por muestra
    
    Args:
        codigo_muestra (str, optional): Código de la muestra para filtrar
        
    Returns:
        list: Lista de ensayos de equivalente de arena
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    if codigo_muestra:
        c.execute("""
        SELECT e.*, ea.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_equivalente_arena ea ON e.id = ea.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Equivalente de Arena'
        ORDER BY e.fecha_ensayo DESC
        """, (codigo_muestra,))
    else:
        c.execute("""
        SELECT e.*, ea.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_equivalente_arena ea ON e.id = ea.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.tipo_ensayo = 'Equivalente de Arena'
        ORDER BY e.fecha_ensayo DESC
        """)
    
    ensayos = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return ensayos

def calcular_equivalente_arena(altura_sedimento, altura_floculos):
    """
    Calcula el equivalente de arena
    
    Args:
        altura_sedimento (float): Altura del sedimento en mm
        altura_floculos (float): Altura de los flóculos en mm
        
    Returns:
        float: Equivalente de arena en porcentaje
    """
    # Validar datos
    if altura_sedimento <= 0 or altura_floculos <= 0:
        raise ValueError("Las alturas deben ser mayores que cero")
    
    if altura_sedimento > altura_floculos:
        raise ValueError("La altura del sedimento no puede ser mayor que la altura de los flóculos")
    
    # Calcular equivalente de arena
    ea = (altura_sedimento / altura_floculos) * 100
    
    # Redondear según norma UNE-EN 933-8
    ea_redondeado = round(ea)
    
    return ea_redondeado

def interpretar_equivalente_arena(ea_valor):
    """
    Interpreta el resultado del ensayo de equivalente de arena según normativas
    
    Args:
        ea_valor (float): Valor del equivalente de arena en porcentaje
        
    Returns:
        tuple: (clasificacion, recomendacion)
    """
    # Clasificación según PG-3 (España)
    if ea_valor >= 50:
        clasificacion = "Árido limpio (EA ≥ 50)"
        recomendacion = "Apto para la mayoría de usos en obra civil"
    elif ea_valor >= 40:
        clasificacion = "Árido con contenido limitado de finos arcillosos (40 ≤ EA < 50)"
        recomendacion = "Apto para algunas capas de firmes y ciertas aplicaciones"
    elif ea_valor >= 30:
        clasificacion = "Árido con contenido significativo de finos arcillosos (30 ≤ EA < 40)"
        recomendacion = "Uso limitado, verificar requisitos específicos de la aplicación"
    else:
        clasificacion = "Árido con alto contenido de finos arcillosos (EA < 30)"
        recomendacion = "No recomendado para capas de firmes, posible uso en aplicaciones no estructurales"
    
    return clasificacion, recomendacion