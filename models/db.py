import sqlite3
import os

# Ruta de la base de datos
DB_PATH = 'ensayos_geotecnicos.db'

def obtener_conexion():
    """
    Crea y devuelve una conexión a la base de datos SQLite.
    Si la base de datos no existe, la crea y inicializa las tablas.
    
    Returns:
        sqlite3.Connection: Objeto de conexión a la base de datos
    """
    # Comprobar si la base de datos existe
    db_existe = os.path.exists(DB_PATH)
    
    # Crear conexión
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Si la base de datos no existía, inicializar las tablas
    if not db_existe:
        inicializar_tablas(conn)
    
    return conn

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
    
    # Crear tabla para otros tipos de ensayos (por ejemplo, límites de Atterberg)
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_limites (
        ensayo_id INTEGER PRIMARY KEY,
        limite_liquido REAL,
        limite_plastico REAL,
        indice_plasticidad REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    # Crear tabla para ensayos de densidad
    c.execute('''
    CREATE TABLE IF NOT EXISTS ensayos_densidad (
        ensayo_id INTEGER PRIMARY KEY,
        densidad_seca REAL,
        densidad_humeda REAL,
        humedad REAL,
        volumen REAL,
        masa REAL,
        FOREIGN KEY (ensayo_id) REFERENCES ensayos (id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()

def inicializar_bd():
    """
    Inicializa la base de datos creando las tablas necesarias si no existen.
    Esta función es redundante pero se mantiene por compatibilidad.
    """
    conn = obtener_conexion()
    inicializar_tablas(conn)
    conn.close()

def migrar_datos_estructura_antigua(conn):
    """
    Migra datos desde la estructura antigua a la nueva estructura con múltiples ensayos.
    
    Args:
        conn (sqlite3.Connection): Conexión a la base de datos
    """
    cursor = conn.cursor()
    
    # Comprobar si existen datos en la tabla antigua de ensayos granulométricos
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ensayos_granulometricos_old'")
    if cursor.fetchone() is None:
        # Verificar si hay datos en la tabla actual de ensayos granulométricos
        cursor.execute("SELECT COUNT(*) FROM ensayos_granulometricos")
        if cursor.fetchone()[0] > 0:
            # Renombrar la tabla actual
            cursor.execute("ALTER TABLE ensayos_granulometricos RENAME TO ensayos_granulometricos_old")
            
            # Crear la nueva estructura
            inicializar_tablas(conn)
            
            # Migrar los datos
            cursor.execute("""
                INSERT INTO ensayos (codigo_muestra, tipo_ensayo, fecha_ensayo, operario)
                SELECT codigo_muestra, 'Granulométrico', fecha_ensayo, operario
                FROM ensayos_granulometricos_old
            """)
            
            # Obtener los ID de los nuevos ensayos
            cursor.execute("""
                SELECT e.id, eg.id as old_id
                FROM ensayos e
                JOIN ensayos_granulometricos_old eg ON e.codigo_muestra = eg.codigo_muestra
                    AND e.fecha_ensayo = eg.fecha_ensayo
                    AND e.operario = eg.operario
            """)
            
            id_mapping = {old_id: new_id for new_id, old_id in cursor.fetchall()}
            
            # Migrar datos granulométricos
            for old_id, new_id in id_mapping.items():
                cursor.execute("""
                    INSERT INTO ensayos_granulometricos 
                    (ensayo_id, masa_total, d10, d30, d60, coef_uniformidad, coef_curvatura)
                    SELECT ?, masa_total, d10, d30, d60, coef_uniformidad, coef_curvatura
                    FROM ensayos_granulometricos_old
                    WHERE id = ?
                """, (new_id, old_id))
                
                # Migrar datos de tamices
                cursor.execute("""
                    INSERT INTO datos_tamices
                    (ensayo_id, tamiz, apertura, masa_retenida, porcentaje_retenido, 
                     porcentaje_retenido_acumulado, porcentaje_pasa)
                    SELECT ?, tamiz, apertura, masa_retenida, porcentaje_retenido, 
                           porcentaje_retenido_acumulado, porcentaje_pasa
                    FROM datos_tamices
                    WHERE ensayo_id = ?
                """, (new_id, old_id))
            
            # Actualizar las imágenes (todas apuntan a muestras en la estructura antigua)
            cursor.execute("UPDATE imagenes SET ensayo_id = NULL")
            
            conn.commit()