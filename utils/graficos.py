import plotly.graph_objects as go

def generar_grafico_granulometrico(datos_tamices):
    """
    Genera un gráfico de curva granulométrica
    
    Args:
        datos_tamices (list): Lista de diccionarios con información procesada de tamices
        
    Returns:
        plotly.graph_objects.Figure: Objeto de figura de Plotly
    """
    # Extraer datos para el gráfico
    aperturas = [dato["apertura"] for dato in datos_tamices if dato["apertura"] > 0]
    porcentajes = [dato["porcentaje_pasa"] for dato in datos_tamices if dato["apertura"] > 0]
    
    # Crear gráfico logarítmico
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=aperturas,
        y=porcentajes,
        mode='lines+markers',
        name='Curva granulométrica'
    ))
    
    # Configurar escala logarítmica en eje X
    fig.update_xaxes(
        title='Tamaño de partículas (mm)',
        type='log',
        autorange='reversed'
    )
    
    # Configurar eje Y
    fig.update_yaxes(
        title='Porcentaje que pasa (%)',
        range=[0, 100]
    )
    
    # Añadir cuadrícula
    fig.update_layout(
        title='Curva Granulométrica',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray'
        ),
        plot_bgcolor='white',
        height=600,
        width=800
    )
    
    return fig