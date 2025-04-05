import sqlite3
from models.db import obtener_conexion
from models.muestras import actualizar_estado_muestra

def guardar_ensayo_proctor(codigo_muestra, fecha_ensayo, operario, 
                          tipo_proctor, densidad_maxima, humedad_optima, 
                          energia_compactacion, numero_capas, golpes_capa,
                          puntos_curva, notas=None):
    """
    Guarda un ensayo Próctor y sus datos asociados
    
    Args:
        codigo_muestra (str): Código de la muestra
        fecha_ensayo (date): Fecha del ensayo
        operario (str): Nombre del operario
        tipo_proctor (str): Tipo de ensayo Próctor ("Normal" o "Modificado")
        densidad_maxima (float): Densidad seca máxima en g/cm³
        humedad_optima (float): Humedad óptima en porcentaje
        energia_compactacion (float): Energía de compactación en J/cm³
        numero_capas (int): Número de capas utilizadas
        golpes_capa (int): Número de golpes por capa
        puntos_curva (list): Lista de diccionarios con los puntos de la curva Próctor
                           Cada diccionario debe contener: humedad, densidad_seca, numero_punto
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
        """, (codigo_muestra, "Próctor", fecha_ensayo, operario, notas))
        
        # Obtener el ID del ensayo insertado
        ensayo_id = c.lastrowid
        
        # Insertar datos específicos del ensayo
        c.execute("""
        INSERT INTO ensayos_proctor (
            ensayo_id, tipo_proctor, densidad_maxima, humedad_optima,
            energia_compactacion, numero_capas, golpes_capa
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ensayo_id, tipo_proctor, densidad_maxima, humedad_optima,
            energia_compactacion, numero_capas, golpes_capa
        ))
        
        # Insertar puntos de la curva
        for punto in puntos_curva:
            c.execute("""
            INSERT INTO puntos_proctor (
                ensayo_id, humedad, densidad_seca, numero_punto
            )
            VALUES (?, ?, ?, ?)
            """, (
                ensayo_id, 
                punto["humedad"], 
                punto["densidad_seca"],
                punto["numero_punto"]
            ))
        
        # Confirmar transacción
        conn.execute("COMMIT")
        
        # Actualizar estado de la muestra
        actualizar_estado_muestra(codigo_muestra, "con ensayo próctor")
        
        return ensayo_id
        
    except Exception as e:
        # Revertir cambios en caso de error
        conn.execute("ROLLBACK")
        raise e
    
    finally:
        conn.close()

def obtener_ensayo_proctor(codigo_muestra):
    """
    Obtiene el último ensayo Próctor de una muestra
    
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
    JOIN ensayos_proctor p ON e.id = p.ensayo_id
    WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Próctor'
    ORDER BY e.fecha_ensayo DESC LIMIT 1
    """, (codigo_muestra,))
    
    ensayo = c.fetchone()
    if not ensayo:
        conn.close()
        return None
    
    ensayo_dict = dict(ensayo)
    
    # Obtener puntos de la curva
    c.execute("""
    SELECT * FROM puntos_proctor
    WHERE ensayo_id = ?
    ORDER BY numero_punto
    """, (ensayo['id'],))
    
    puntos = [dict(row) for row in c.fetchall()]
    ensayo_dict['puntos'] = puntos
    
    conn.close()
    return ensayo_dict

def obtener_todos_ensayos_proctor(codigo_muestra=None):
    """
    Obtiene todos los ensayos Próctor, opcionalmente filtrados por muestra
    
    Args:
        codigo_muestra (str, optional): Código de la muestra para filtrar
        
    Returns:
        list: Lista de ensayos Próctor
    """
    conn = obtener_conexion()
    c = conn.cursor()
    
    if codigo_muestra:
        c.execute("""
        SELECT e.*, p.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_proctor p ON e.id = p.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.codigo_muestra = ? AND e.tipo_ensayo = 'Próctor'
        ORDER BY e.fecha_ensayo DESC
        """, (codigo_muestra,))
    else:
        c.execute("""
        SELECT e.*, p.*, m.codigo_muestra 
        FROM ensayos e
        JOIN ensayos_proctor p ON e.id = p.ensayo_id
        JOIN muestras m ON e.codigo_muestra = m.codigo_muestra
        WHERE e.tipo_ensayo = 'Próctor'
        ORDER BY e.fecha_ensayo DESC
        """)
    
    ensayos = []
    for row in c.fetchall():
        ensayo_dict = dict(row)
        
        # Obtener puntos de la curva para cada ensayo
        c.execute("""
        SELECT * FROM puntos_proctor
        WHERE ensayo_id = ?
        ORDER BY numero_punto
        """, (ensayo_dict['id'],))
        
        puntos = [dict(p) for p in c.fetchall()]
        ensayo_dict['puntos'] = puntos
        
        ensayos.append(ensayo_dict)
    
    conn.close()
    return ensayos

def ajustar_curva_proctor(puntos):
    """
    Ajusta una curva polinómica a los puntos del ensayo Próctor para determinar
    la densidad máxima y humedad óptima
    
    Args:
        puntos (list): Lista de diccionarios con los puntos (humedad, densidad_seca)
        
    Returns:
        tuple: (densidad_maxima, humedad_optima)
    """
    try:
        import numpy as np
        from scipy.optimize import curve_fit
        
        # Extracción de datos
        humedades = np.array([p['humedad'] for p in puntos])
        densidades = np.array([p['densidad_seca'] for p in puntos])
        
        # Función para ajustar (parábola)
        def parabola(x, a, b, c):
            return a * x**2 + b * x + c
        
        # Ajuste de la curva
        params, _ = curve_fit(parabola, humedades, densidades)
        a, b, c = params
        
        # La humedad óptima es el punto donde la derivada es cero
        humedad_optima = -b / (2 * a)
        
        # La densidad máxima es el valor de la función en ese punto
        densidad_maxima = parabola(humedad_optima, a, b, c)
        
        return densidad_maxima, humedad_optima
    
    except (ImportError, Exception) as e:
        # Si no se puede hacer el ajuste matemático, se usa la aproximación por el punto más alto
        max_punto = max(puntos, key=lambda p: p['densidad_seca'])
        return max_punto['densidad_seca'], max_punto['humedad']

def calcular_energia_compactacion(tipo_proctor, peso_maza, altura_caida, numero_capas, golpes_capa, volumen_molde):
    """
    Calcula la energía de compactación del ensayo Próctor
    
    Args:
        tipo_proctor (str): Tipo de ensayo Próctor ("Normal" o "Modificado")
        peso_maza (float): Peso de la maza en kg
        altura_caida (float): Altura de caída de la maza en m
        numero_capas (int): Número de capas
        golpes_capa (int): Número de golpes por capa
        volumen_molde (float): Volumen del molde en cm³
        
    Returns:
        float: Energía de compactación en J/cm³
    """
    # Convertir peso a newtons (1 kg = 9.81 N)
    fuerza_maza = peso_maza * 9.81
    
    # Trabajo por golpe (J) = Fuerza (N) * Altura (m)
    trabajo_golpe = fuerza_maza * altura_caida
    
    # Trabajo total (J) = Trabajo por golpe (J) * Número de golpes * Número de capas
    trabajo_total = trabajo_golpe * golpes_capa * numero_capas
    
    # Energía de compactación (J/cm³) = Trabajo total (J) / Volumen del molde (cm³)
    energia_compactacion = trabajo_total / volumen_molde
    
    return energia_compactacion

def obtener_parametros_proctor(tipo_proctor):
    """
    Obtiene los parámetros estándar para el ensayo Próctor según su tipo
    
    Args:
        tipo_proctor (str): Tipo de ensayo Próctor ("Normal" o "Modificado")
        
    Returns:
        dict: Parámetros del ensayo
    """
    if tipo_proctor.lower() == "normal":
        return {
            "peso_maza": 2.5,  # kg
            "altura_caida": 0.305,  # m
            "numero_capas": 3,
            "golpes_capa": 25,
            "volumen_molde": 944,  # cm³
            "energia_compactacion": 0.583  # J/cm³
        }
    elif tipo_proctor.lower() == "modificado":
        return {
            "peso_maza": 4.54,  # kg
            "altura_caida": 0.457,  # m
            "numero_capas": 5,
            "golpes_capa": 25,
            "volumen_molde": 944,  # cm³
            "energia_compactacion": 2.632  # J/cm³
        }
    else:
        raise ValueError("Tipo de Próctor no reconocido. Debe ser 'Normal' o 'Modificado'")