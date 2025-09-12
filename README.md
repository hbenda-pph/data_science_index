# Data Science Index

Plataforma de gestión de trabajos de ciencia de datos y análisis predictivo.

## Estructura del Proyecto

- `index/` - Índice principal de trabajos
- `admin/` - Interfaz de administración
- `shared/` - Código común y utilidades
- `categories/` - Trabajos organizados por categoría
- `assets/` - Recursos estáticos (imágenes, iconos)

## Configuración

1. Instalar dependencias: `pip install -r requirements.txt`
2. Configurar variables de entorno para BigQuery
3. Ejecutar: `streamlit run index/main_index.py`

## Base de Datos

Tabla principal: `platform-partners-des.settings.works_index`
