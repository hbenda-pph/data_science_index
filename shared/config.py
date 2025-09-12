"""
Configuraciones del proyecto
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de BigQuery
BIGQUERY_PROJECT = "platform-partners-des"
BIGQUERY_DATASET = "settings"
BIGQUERY_TABLE = "works_index"

# Configuración de Streamlit
STREAMLIT_CONFIG = {
    "page_title": "Data Science Index",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Configuración de la aplicación
APP_CONFIG = {
    "title": "Data Science Index",
    "subtitle": "Portafolio de Análisis Predictivo y Ciencia de Datos",
    "page_icon": "📊",
    "admin_password": os.getenv("ADMIN_PASSWORD", "admin123"),  # Cambiar en producción
    "max_image_size": 5 * 1024 * 1024,  # 5MB
    "allowed_image_types": ["jpg", "jpeg", "png", "gif"]
}

# Estados de trabajos
WORK_STATUS = {
    "ACTIVE": "active",
    "PAUSED": "paused", 
    "ARCHIVED": "archived",
    "MAINTENANCE": "maintenance"
}

# Categorías principales
CATEGORIES = {
    "calls_analysis": "Análisis de Llamadas",
    "marketing_analysis": "Análisis de Marketing", 
    "climate_analysis": "Análisis Climáticos",
    "accounting_analysis": "Análisis de Contabilidad",
    "workforce_analysis": "Análisis de Fuerza Laboral"
}
