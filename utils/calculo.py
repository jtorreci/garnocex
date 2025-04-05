def procesar_datos_tamices(tamices, masas_retenidas, masa_total):
    """
    Procesa los datos de los tamices y calcula porcentajes
    
    Args:
        tamices (list): Lista de diccionarios con información de tamices
        masas_retenidas (list): Lista de masas retenidas en cada tamiz
        masa_total (float): Masa total de la muestra
        
    Returns:
        list: Lista de diccionarios con información procesada de cada tamiz
    """
    datos_tamices = []
    masa_acumulada = 0
    
    for i, tamiz in enumerate(tamices):
        masa_retenida = masas_retenidas[i] if i < len(masas_retenidas) else 0
        porcentaje_retenido = (masa_retenida / masa_total) * 100 if masa_total > 0 else 0
        masa_acumulada += masa_retenida
        porcentaje_retenido_acumulado = (masa_acumulada / masa_total) * 100 if masa_total > 0 else 0
        porcentaje_pasa = 100 - porcentaje_retenido_acumulado
        
        datos_tamices.append({
            "tamiz": tamiz["nombre"],
            "apertura": tamiz["apertura"],
            "masa_retenida": masa_retenida,
            "porcentaje_retenido": porcentaje_retenido,
            "porcentaje_retenido_acumulado": porcentaje_retenido_acumulado,
            "porcentaje_pasa": porcentaje_pasa
        })
    
    return datos_tamices

def interpolar(x, y, valor_y):
    """
    Realiza interpolación lineal para encontrar un valor x para un y dado
    
    Args:
        x (list): Lista de valores x
        y (list): Lista de valores y
        valor_y (float): Valor de y para el que se busca x
        
    Returns:
        float: Valor interpolado de x
    """
    # Buscar los puntos de interpolación
    for i in range(len(y) - 1):
        if y[i] >= valor_y and y[i + 1] <= valor_y:
            # Interpolación lineal
            if y[i] == y[i + 1]:
                return x[i]
            return x[i] + (x[i + 1] - x[i]) * (valor_y - y[i]) / (y[i + 1] - y[i])
    
    # Si no se puede interpolar, devolver 0
    return 0

def calcular_diametros_caracteristicos(datos_tamices):
    """
    Calcula los diámetros D10, D30 y D60 interpolando la curva granulométrica
    
    Args:
        datos_tamices (list): Lista de diccionarios con información procesada de tamices
        
    Returns:
        tuple: (d10, d30, d60) Diámetros característicos
    """
    # Extraer datos para interpolación
    aperturas = [dato["apertura"] for dato in datos_tamices if dato["apertura"] > 0]
    porcentajes = [dato["porcentaje_pasa"] for dato in datos_tamices if dato["apertura"] > 0]
    
    # Invertir listas para que aperturas estén en orden ascendente
    aperturas.reverse()
    porcentajes.reverse()
    
    # Interpolación lineal para D10, D30, D60
    d10 = interpolar(aperturas, porcentajes, 10)
    d30 = interpolar(aperturas, porcentajes, 30)
    d60 = interpolar(aperturas, porcentajes, 60)
    
    return d10, d30, d60

def calcular_coeficientes(d10, d30, d60):
    """
    Calcula coeficientes de uniformidad y curvatura
    
    Args:
        d10 (float): Diámetro D10
        d30 (float): Diámetro D30
        d60 (float): Diámetro D60
        
    Returns:
        tuple: (cu, cc) Coeficientes de uniformidad y curvatura
    """
    cu, cc = 0, 0
    
    if d10 > 0:
        if d60 > 0:
            cu = d60 / d10
        if d30 > 0 and d60 > 0:
            cc = (d30 * d30) / (d10 * d60)
    
    return cu, cc