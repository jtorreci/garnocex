# Sistema de Gestión de Ensayos Geotécnicos

Este sistema permite la gestión de ensayos geotécnicos, facilitando el registro, procesamiento y consulta de datos de ensayos granulométricos.

## Características

- Registro de muestras con datos básicos (código, operario, fecha, tipo)
- Carga y almacenamiento de imágenes de las muestras
- Registro de ensayos granulométricos
- Cálculo automático de parámetros (D10, D30, D60, Cu, Cc)
- Generación de curvas granulométricas
- Consulta y exportación de resultados

## Requisitos

- Python 3.7 o superior
- Streamlit
- Pandas
- NumPy
- Plotly
- Pillow

## Instalación

1. Clona este repositorio o descarga los archivos
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Estructura del proyecto

```
ensayos_geotecnicos/
│
├── app.py                 # Punto de entrada principal de la aplicación
│
├── pages/                 # Páginas de la aplicación
│   ├── __init__.py
│   ├── registro.py        # Formulario registro de muestras
│   ├── granulometria.py   # Formulario ensayo granulométrico
│   └── consulta.py        # Visualización de resultados
│
├── models/                # Modelos y operaciones de base de datos
│   ├── __init__.py
│   ├── db.py              # Inicialización y conexión a la BD
│   ├── muestras.py        # Operaciones CRUD para muestras
│   └── granulometria.py   # Operaciones CRUD para ensayos granulométricos
│
├── utils/                 # Utilidades y funciones auxiliares
│   ├── __init__.py
│   ├── tamices.py         # Definiciones de tamices estándar
│   ├── calculo.py         # Funciones de cálculo para ensayos
│   └── graficos.py        # Generación de gráficos y visualizaciones
│
└── requirements.txt       # Dependencias del proyecto
```

## Uso

1. Ejecuta la aplicación:

```bash
streamlit run app.py
```

2. Accede a la aplicación en tu navegador (por defecto en http://localhost:8501)

## Flujo de trabajo

1. **Registro de muestras**: Ingresa los datos básicos de la muestra y carga imágenes
2. **Ensayo granulométrico**: Selecciona una muestra y registra los resultados del tamizado
3. **Consulta de resultados**: Visualiza y exporta los resultados de los ensayos

## Despliegue

Para desplegar la aplicación en un servidor local y permitir el acceso desde otras computadoras en la red:

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

Para exponer la aplicación a Internet, puedes usar:

1. Un servicio de túnel como ngrok:
   ```bash
   ngrok http 8501
   ```

2. Un servidor con IP pública y un proxy inverso como Nginx