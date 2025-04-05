def get_tamices_estandar():
    """
    Devuelve una lista de tamices estándar utilizados en ensayos granulométricos
    
    Returns:
        list: Lista de diccionarios con nombre y apertura de cada tamiz
    """
    return [
        {"nombre": "3\"", "apertura": 75.0},
        {"nombre": "2\"", "apertura": 50.0},
        {"nombre": "1 1/2\"", "apertura": 37.5},
        {"nombre": "1\"", "apertura": 25.0},
        {"nombre": "3/4\"", "apertura": 19.0},
        {"nombre": "1/2\"", "apertura": 12.5},
        {"nombre": "3/8\"", "apertura": 9.5},
        {"nombre": "No. 4", "apertura": 4.75},
        {"nombre": "No. 10", "apertura": 2.00},
        {"nombre": "No. 20", "apertura": 0.85},
        {"nombre": "No. 40", "apertura": 0.425},
        {"nombre": "No. 60", "apertura": 0.250},
        {"nombre": "No. 100", "apertura": 0.150},
        {"nombre": "No. 200", "apertura": 0.075},
        {"nombre": "Fondo", "apertura": 0}
    ]

# Alias para la misma función (por compatibilidad)
get_tamices = get_tamices_estandar