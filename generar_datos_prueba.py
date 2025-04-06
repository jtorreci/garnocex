import os
import sqlite3
import random
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import io

# Ruta de la base de datos
DB_PATH = 'ensayos_geotecnicos.db'

def generar_db_prueba():
    """
    Genera una base de datos de prueba con muestras aleatorias y sus ensayos
    """
    # Eliminar la base de datos anterior si existe
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Base de datos anterior eliminada: {DB_PATH}")
    
    # Conectar a la nueva base de datos
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Inicializar las tablas
    inicializar_tablas(conn)
    
    # Crear datos de prueba
    generar_muestras_aleatorias(conn, 6)
    
    # Crear usuarios de prueba
    crear_usuarios_prueba(conn)
    
    # Cerrar conexión
    conn.close()
    
    print(f"Base de datos de prueba creada correctamente: {DB_PATH}")

def inicializar_tablas(conn):
    """
    Inicializa las tablas necesarias en la base de datos.
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
    """
    c = conn.cursor()
    
    # Crear tabla de muestras
    c.execute('''
    CREATE TABLE IF NOT EXISTS muestras (
        codigo_muestra TEXT PRIMARY KEY,
        operario TEXT,
        fecha DATE,
        tipo_material TEXT,
        estado TEXT,
        notas TEXT
    )
    ''')
    
    # Crear tabla de ensayos (genérica)
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_muestra TEXT,
        tipo_ensayo TEXT,
        fecha_ensayo DATE,
        operario TEXT,
        notas TEXT,
        FOREIGN KEY (codigo_muestra) REFERENCES muestras (codigo_muestra)
    )
    ''')
    
    # Crear tabla de ensayos granulométricos
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_granulometricos (
        ensayo_id INTEGER PRIMARY KEY,
        masa_total REAL,
        d10 REAL,
        d30 REAL,
        d60 REAL,
        coef_uniformidad REAL,
        coef_curvatura REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla para los datos de tamices
    c.execute('''
    CREATE TABLE IF NOT EXISTS datos_tamices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ensayo_id INTEGER,
        tamiz TEXT,
        apertura REAL,
        masa_retenida REAL,
        porcentaje_retenido REAL,
        porcentaje_retenido_acumulado REAL,
        porcentaje_pasa REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla de imágenes con referencia opcional a ensayos
    c.execute('''
    CREATE TABLE IF NOT EXISTS imagenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_muestra TEXT,
        ensayo_id INTEGER NULL,
        imagen BLOB,
        nombre_archivo TEXT,
        fecha_subida DATE,
        descripcion TEXT,
        FOREIGN KEY (codigo_muestra) REFERENCES muestras (codigo_muestra),
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE SET NULL
    )
    ''')
    
    # Crear tabla para ensayos de límites de Atterberg
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_limites (
        ensayo_id INTEGER PRIMARY KEY,
        limite_liquido REAL,
        limite_plastico REAL,
        indice_plasticidad REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla para ensayos de densidad de árido grueso
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_densidad_arido (
        ensayo_id INTEGER PRIMARY KEY,
        densidad_aparente REAL,
        densidad_tras_secado REAL,
        densidad_sss REAL, /* Saturada con superficie seca */
        absorcion_agua REAL,
        masa_sumergida REAL,
        masa_sss REAL,
        masa_seca REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla para ensayos CBR
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_cbr (
        ensayo_id INTEGER PRIMARY KEY,
        energia_compactacion REAL,
        densidad_seca REAL,
        humedad_inicial REAL,
        humedad_final REAL,
        hinchamiento REAL,
        indice_cbr REAL,
        absorcion_agua REAL,
        dias_inmersion INTEGER,
        sobrecarga REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla para ensayos de índice de lajas y agujas
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_lajas_agujas (
        ensayo_id INTEGER PRIMARY KEY,
        indice_lajas REAL,
        indice_agujas REAL,
        masa_total REAL,
        masa_lajas REAL,
        masa_agujas REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla para ensayos de picnómetro de arena
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_picnometro (
        ensayo_id INTEGER PRIMARY KEY,
        densidad_aparente REAL,
        volumen_hoyo REAL,
        masa_arena_empleada REAL,
        masa_arena_cono REAL,
        densidad_arena REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla para ensayos de equivalente de arena
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_equivalente_arena (
        ensayo_id INTEGER PRIMARY KEY,
        altura_sedimento REAL,
        altura_floculos REAL,
        equivalente_arena REAL,
        temperatura REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla para ensayos Próctor
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_proctor (
        ensayo_id INTEGER PRIMARY KEY,
        tipo_proctor TEXT,
        densidad_maxima REAL,
        humedad_optima REAL,
        energia_compactacion REAL,
        numero_capas INTEGER,
        golpes_capa INTEGER,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla para los puntos de la curva Próctor
    c.execute('''
    CREATE TABLE IF NOT EXISTS puntos_proctor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ensayo_id INTEGER,
        humedad REAL,
        densidad_seca REAL,
        numero_punto INTEGER,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos_proctor (ensayo_id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla de usuarios
    c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        nickname TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()

def generar_muestras_aleatorias(conn, num_muestras=6):
    """
    Genera muestras aleatorias y sus ensayos
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        num_muestras (int): Número de muestras a generar
    """
    c = conn.cursor()
    
    # Definir operarios
    operarios = ["Juan Pérez", "María Gómez", "Carlos Rodríguez", "Ana Martínez"]
    
    # Definir tipos de materiales
    tipos_materiales = ["Suelo", "Arena", "Arcilla", "Grava", "Roca"]
    
    # Definir estados
    estados = ["Registrado", "En análisis", "Analizado", "Archivado"]
    
    # Fecha base (hace 3 meses)
    fecha_base = datetime.now() - timedelta(days=90)
    
    # Generar muestras
    for i in range(1, num_muestras + 1):
        # Generar datos aleatorios
        codigo_muestra = f"M-{2023}-{i:03d}"
        operario = random.choice(operarios)
        dias_aleatorios = random.randint(0, 90)
        fecha = (fecha_base + timedelta(days=dias_aleatorios)).strftime('%Y-%m-%d')
        tipo_material = random.choice(tipos_materiales)
        estado = random.choice(estados)
        notas = f"Muestra de prueba {i}. Material obtenido de la zona de prueba."
        
        # Insertar muestra
        c.execute('''
        INSERT INTO muestras (codigo_muestra, operario, fecha, tipo_material, estado, notas)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (codigo_muestra, operario, fecha, tipo_material, estado, notas))
        
        # Crear imagen de prueba para la muestra
        generar_imagen_prueba(conn, codigo_muestra)
        
        # Decidir qué ensayos generar
        ensayos_a_generar = random.sample([
            "Granulométrico", 
            "Límites de Atterberg", 
            "Densidad de Árido Grueso",
            "CBR",
            "Índice de Lajas y Agujas",
            "Picnómetro de Arena",
            "Equivalente de Arena",
            "Próctor"
        ], k=random.randint(1, 4))  # Entre 1 y 4 ensayos por muestra
        
        for tipo_ensayo in ensayos_a_generar:
            dias_desde_muestra = random.randint(1, 15)
            fecha_ensayo = (datetime.strptime(fecha, '%Y-%m-%d') + timedelta(days=dias_desde_muestra)).strftime('%Y-%m-%d')
            
            # Insertar en la tabla general de ensayos
            c.execute('''
            INSERT INTO ensayos (codigo_muestra, tipo_ensayo, fecha_ensayo, operario, notas)
            VALUES (?, ?, ?, ?, ?)
            ''', (codigo_muestra, tipo_ensayo, fecha_ensayo, operario, f"Ensayo de prueba de {tipo_ensayo}"))
            
            ensayo_id = c.lastrowid
            
            # Generar datos específicos del ensayo
            if tipo_ensayo == "Granulométrico":
                generar_ensayo_granulometrico(conn, ensayo_id)
            elif tipo_ensayo == "Límites de Atterberg":
                generar_ensayo_limites(conn, ensayo_id)
            elif tipo_ensayo == "Densidad de Árido Grueso":
                generar_ensayo_densidad_arido(conn, ensayo_id)
            elif tipo_ensayo == "CBR":
                generar_ensayo_cbr(conn, ensayo_id)
            elif tipo_ensayo == "Índice de Lajas y Agujas":
                generar_ensayo_lajas_agujas(conn, ensayo_id)
            elif tipo_ensayo == "Picnómetro de Arena":
                generar_ensayo_picnometro(conn, ensayo_id)
            elif tipo_ensayo == "Equivalente de Arena":
                generar_ensayo_equivalente_arena(conn, ensayo_id)
            elif tipo_ensayo == "Próctor":
                generar_ensayo_proctor(conn, ensayo_id)
            
    conn.commit()

def generar_imagen_prueba(conn, codigo_muestra):
    """
    Genera una imagen de prueba para una muestra
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        codigo_muestra (str): Código de la muestra
    """
    c = conn.cursor()
    
    # Crear una imagen simple
    width, height = 300, 200
    img = Image.new('RGB', (width, height), color=(random.randint(200, 255), random.randint(200, 255), random.randint(200, 255)))
    
    # Convertir a bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Insertar en la base de datos
    c.execute('''
    INSERT INTO imagenes (codigo_muestra, imagen, nombre_archivo, fecha_subida, descripcion)
    VALUES (?, ?, ?, ?, ?)
    ''', (codigo_muestra, img_byte_arr, f'muestra_{codigo_muestra}.png', datetime.now().strftime('%Y-%m-%d'), f'Imagen de prueba para muestra {codigo_muestra}'))
    
    conn.commit()

def generar_ensayo_granulometrico(conn, ensayo_id):
    """
    Genera datos aleatorios para un ensayo granulométrico
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        ensayo_id (int): ID del ensayo
    """
    c = conn.cursor()
    
    # Datos aleatorios
    masa_total = round(random.uniform(1000, 3000), 1)
    d10 = round(random.uniform(0.1, 0.5), 3)
    d30 = round(random.uniform(0.5, 1.5), 3)
    d60 = round(random.uniform(2.0, 5.0), 3)
    coef_uniformidad = round(d60 / d10, 2)
    coef_curvatura = round((d30**2) / (d10 * d60), 2)
    
    # Insertar ensayo granulométrico
    c.execute('''
    INSERT INTO ensayos_granulometricos (ensayo_id, masa_total, d10, d30, d60, coef_uniformidad, coef_curvatura)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ensayo_id, masa_total, d10, d30, d60, coef_uniformidad, coef_curvatura))
    
    # Tamices estándar
    tamices = [
        {"nombre": "4\"", "apertura": 101.6},
        {"nombre": "3\"", "apertura": 76.2},
        {"nombre": "2\"", "apertura": 50.8},
        {"nombre": "1 1/2\"", "apertura": 38.1},
        {"nombre": "1\"", "apertura": 25.4},
        {"nombre": "3/4\"", "apertura": 19.1},
        {"nombre": "1/2\"", "apertura": 12.7},
        {"nombre": "3/8\"", "apertura": 9.52},
        {"nombre": "N°4", "apertura": 4.76},
        {"nombre": "N°10", "apertura": 2.0},
        {"nombre": "N°20", "apertura": 0.84},
        {"nombre": "N°40", "apertura": 0.42},
        {"nombre": "N°60", "apertura": 0.25},
        {"nombre": "N°140", "apertura": 0.105},
        {"nombre": "N°200", "apertura": 0.074}
    ]
    
    # Generar datos para tamices
    masa_acumulada = 0
    for tamiz in tamices:
        # Calcular masa retenida aleatoria (decreciente para tamices más pequeños)
        masa_retenida = round(masa_total * random.uniform(0.02, 0.25) * (tamiz["apertura"]/100), 1)
        
        # Asegurar que no excedemos la masa total
        if masa_acumulada + masa_retenida > masa_total:
            masa_retenida = round(masa_total - masa_acumulada, 1)
            if masa_retenida <= 0:
                break
        
        masa_acumulada += masa_retenida
        
        # Calcular porcentajes
        porcentaje_retenido = round((masa_retenida / masa_total) * 100, 2)
        porcentaje_retenido_acumulado = round((masa_acumulada / masa_total) * 100, 2)
        porcentaje_pasa = round(100 - porcentaje_retenido_acumulado, 2)
        
        # Insertar datos tamiz
        c.execute('''
        INSERT INTO datos_tamices (ensayo_id, tamiz, apertura, masa_retenida, porcentaje_retenido, porcentaje_retenido_acumulado, porcentaje_pasa)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ensayo_id, tamiz["nombre"], tamiz["apertura"], masa_retenida, porcentaje_retenido, porcentaje_retenido_acumulado, porcentaje_pasa))
    
    conn.commit()

def generar_ensayo_limites(conn, ensayo_id):
    """
    Genera datos aleatorios para un ensayo de límites de Atterberg
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        ensayo_id (int): ID del ensayo
    """
    c = conn.cursor()
    
    # Datos aleatorios
    limite_liquido = round(random.uniform(25, 60), 1)
    limite_plastico = round(random.uniform(15, limite_liquido - 5), 1)
    indice_plasticidad = round(limite_liquido - limite_plastico, 1)
    
    # Insertar ensayo limites
    c.execute('''
    INSERT INTO ensayos_limites (ensayo_id, limite_liquido, limite_plastico, indice_plasticidad)
    VALUES (?, ?, ?, ?)
    ''', (ensayo_id, limite_liquido, limite_plastico, indice_plasticidad))
    
    conn.commit()

def generar_ensayo_densidad_arido(conn, ensayo_id):
    """
    Genera datos aleatorios para un ensayo de densidad de árido grueso
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        ensayo_id (int): ID del ensayo
    """
    c = conn.cursor()
    
    # Datos aleatorios
    masa_seca = round(random.uniform(500, 2000), 1)
    masa_sss = round(masa_seca * random.uniform(1.01, 1.05), 1)
    masa_sumergida = round(masa_seca * random.uniform(0.5, 0.7), 1)
    
    # Cálculos
    densidad_aparente = round(masa_seca / (masa_sss - masa_sumergida), 3)
    densidad_tras_secado = round(masa_seca / (masa_seca - masa_sumergida), 3)
    densidad_sss = round(masa_sss / (masa_sss - masa_sumergida), 3)
    absorcion_agua = round(((masa_sss - masa_seca) / masa_seca) * 100, 2)
    
    # Insertar ensayo
    c.execute('''
    INSERT INTO ensayos_densidad_arido (
        ensayo_id, densidad_aparente, densidad_tras_secado, densidad_sss, 
        absorcion_agua, masa_sumergida, masa_sss, masa_seca
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ensayo_id, densidad_aparente, densidad_tras_secado, densidad_sss, 
         absorcion_agua, masa_sumergida, masa_sss, masa_seca))
    
    conn.commit()

def generar_ensayo_cbr(conn, ensayo_id):
    """
    Genera datos aleatorios para un ensayo CBR
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        ensayo_id (int): ID del ensayo
    """
    c = conn.cursor()
    
    # Datos aleatorios
    energia_compactacion = round(random.uniform(500, 3000), 1)
    densidad_seca = round(random.uniform(1.5, 2.2), 2)
    humedad_inicial = round(random.uniform(5, 15), 1)
    humedad_final = round(humedad_inicial + random.uniform(1, 5), 1)
    hinchamiento = round(random.uniform(0, 3), 2)
    indice_cbr = round(random.uniform(2, 40), 1)
    absorcion_agua = round(random.uniform(0.5, 5), 2)
    dias_inmersion = random.randint(1, 7)
    sobrecarga = round(random.uniform(2, 10), 1)
    
    # Insertar ensayo
    c.execute('''
    INSERT INTO ensayos_cbr (
        ensayo_id, energia_compactacion, densidad_seca, humedad_inicial, humedad_final,
        hinchamiento, indice_cbr, absorcion_agua, dias_inmersion, sobrecarga
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ensayo_id, energia_compactacion, densidad_seca, humedad_inicial, humedad_final,
         hinchamiento, indice_cbr, absorcion_agua, dias_inmersion, sobrecarga))
    
    conn.commit()

def generar_ensayo_lajas_agujas(conn, ensayo_id):
    """
    Genera datos aleatorios para un ensayo de índice de lajas y agujas
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        ensayo_id (int): ID del ensayo
    """
    c = conn.cursor()
    
    # Datos aleatorios
    masa_total = round(random.uniform(1000, 5000), 1)
    masa_lajas = round(masa_total * random.uniform(0.05, 0.3), 1)
    masa_agujas = round(masa_total * random.uniform(0.05, 0.2), 1)
    
    # Cálculos
    indice_lajas = round((masa_lajas / masa_total) * 100, 1)
    indice_agujas = round((masa_agujas / masa_total) * 100, 1)
    
    # Insertar ensayo
    c.execute('''
    INSERT INTO ensayos_lajas_agujas (
        ensayo_id, indice_lajas, indice_agujas, masa_total, masa_lajas, masa_agujas
    )
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (ensayo_id, indice_lajas, indice_agujas, masa_total, masa_lajas, masa_agujas))
    
    conn.commit()

def generar_ensayo_picnometro(conn, ensayo_id):
    """
    Genera datos aleatorios para un ensayo de picnómetro de arena
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        ensayo_id (int): ID del ensayo
    """
    c = conn.cursor()
    
    # Datos aleatorios
    masa_arena_empleada = round(random.uniform(2000, 5000), 1)
    masa_arena_cono = round(random.uniform(500, 1000), 1)
    densidad_arena = round(random.uniform(1.4, 1.7), 2)
    
    # Cálculos
    volumen_hoyo = round((masa_arena_empleada - masa_arena_cono) / densidad_arena, 1)
    densidad_aparente = round(random.uniform(1.5, 2.0), 2)  # Este valor normalmente se calcula con la masa del suelo extraído
    
    # Insertar ensayo
    c.execute('''
    INSERT INTO ensayos_picnometro (
        ensayo_id, densidad_aparente, volumen_hoyo, masa_arena_empleada,
        masa_arena_cono, densidad_arena
    )
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (ensayo_id, densidad_aparente, volumen_hoyo, masa_arena_empleada,
         masa_arena_cono, densidad_arena))
    
    conn.commit()

def generar_ensayo_equivalente_arena(conn, ensayo_id):
    """
    Genera datos aleatorios para un ensayo de equivalente de arena
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        ensayo_id (int): ID del ensayo
    """
    c = conn.cursor()
    
    # Datos aleatorios
    altura_sedimento = round(random.uniform(2, 10), 1)
    altura_floculos = round(altura_sedimento + random.uniform(2, 10), 1)
    temperatura = round(random.uniform(18, 25), 1)
    
    # Cálculos
    equivalente_arena = round((altura_sedimento / altura_floculos) * 100)
    
    # Insertar ensayo
    c.execute('''
    INSERT INTO ensayos_equivalente_arena (
        ensayo_id, altura_sedimento, altura_floculos, equivalente_arena, temperatura
    )
    VALUES (?, ?, ?, ?, ?)
    ''', (ensayo_id, altura_sedimento, altura_floculos, equivalente_arena, temperatura))
    
    conn.commit()

def generar_ensayo_proctor(conn, ensayo_id):
    """
    Genera datos aleatorios para un ensayo Próctor
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
        ensayo_id (int): ID del ensayo
    """
    c = conn.cursor()
    
    # Datos aleatorios
    tipo_proctor = random.choice(["Normal", "Modificado"])
    energia_compactacion = 592.7 if tipo_proctor == "Normal" else 2632.0
    numero_capas = 3 if tipo_proctor == "Normal" else 5
    golpes_capa = 25
    
    # Humedad óptima y densidad máxima
    humedad_optima = round(random.uniform(8, 15), 1)
    densidad_maxima = round(random.uniform(1.7, 2.1), 3)
    
    # Insertar ensayo Próctor
    c.execute('''
    INSERT INTO ensayos_proctor (
        ensayo_id, tipo_proctor, densidad_maxima, humedad_optima,
        energia_compactacion, numero_capas, golpes_capa
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ensayo_id, tipo_proctor, densidad_maxima, humedad_optima,
         energia_compactacion, numero_capas, golpes_capa))
    
    # Generar puntos de la curva
    num_puntos = 5
    humedades = [round(humedad_optima + (i - 2) * 2, 1) for i in range(num_puntos)]
    
    for i, h in enumerate(humedades):
        # La densidad sigue una curva parabólica con máximo en humedad_optima
        desviacion = abs(h - humedad_optima)
        factor = 1 - (desviacion / 10) ** 2
        densidad_seca = round(densidad_maxima * factor, 3)
        
        c.execute('''
        INSERT INTO puntos_proctor (
            ensayo_id, humedad, densidad_seca, numero_punto
        )
        VALUES (?, ?, ?, ?)
        ''', (ensayo_id, h, densidad_seca, i+1))
    
    conn.commit()

def crear_usuarios_prueba(conn):
    """
    Crea usuarios de prueba para el sistema
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
    """
    c = conn.cursor()
    
    # Crear usuario admin (password: admin123)
    c.execute('''
    INSERT INTO usuarios (nombre, nickname, password_hash, salt)
    VALUES (?, ?, ?, ?)
    ''', ("Administrador", "admin", "9c900c863c7a35874cf305ed2e40b75a67ead86e87ac52eea80eb9962a416575", "1234567890abcdef"))
    
    # Crear usuario técnico (password: tecnico123)
    c.execute('''
    INSERT INTO usuarios (nombre, nickname, password_hash, salt)
    VALUES (?, ?, ?, ?)
    ''', ("Técnico de Laboratorio", "tecnico", "9c900c863c7a35874cf305ed2e40b75a67ead86e87ac52eea80eb9962a416575", "1234567890abcdef"))
    
    conn.commit()

if __name__ == "__main__":
    generar_db_prueba()