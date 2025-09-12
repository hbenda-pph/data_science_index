"""
Índice principal de trabajos de ciencia de datos
"""
import streamlit as st
import sys
import os

# Agregar el directorio shared al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import WorksDatabase
from config import APP_CONFIG, CATEGORIES
from utils import format_date, get_status_badge, get_category_icon

# Configuración de la página
st.set_page_config(
    page_title=APP_CONFIG["title"],
    page_icon=APP_CONFIG["page_icon"],
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Función principal del índice"""
    
    # Header
    st.title(APP_CONFIG["title"])
    st.markdown(f"*{APP_CONFIG['subtitle']}*")
    st.divider()
    
    # Inicializar base de datos
    try:
        db = WorksDatabase()
        
        # Sidebar con filtros
        with st.sidebar:
            st.header("🔍 Filtros")
            
            # Filtro por categoría
            categories = db.get_categories()
            selected_category = st.selectbox(
                "Categoría:",
                ["Todas"] + categories
            )
            
            # Filtro por estado
            status_filter = st.selectbox(
                "Estado:",
                ["Todos", "Activos", "Pausados", "En Mantenimiento"]
            )
        
        # Obtener trabajos según filtros
        if selected_category == "Todas":
            works_df = db.get_all_works()
        else:
            works_df = db.get_works_by_category(selected_category)
        
        # Aplicar filtro de estado
        if status_filter != "Todos":
            status_map = {
                "Activos": "active",
                "Pausados": "paused", 
                "En Mantenimiento": "maintenance"
            }
            works_df = works_df[works_df['status'] == status_map[status_filter]]
        
        # Mostrar trabajos
        if works_df.empty:
            st.info("No se encontraron trabajos con los filtros seleccionados.")
        else:
            st.subheader(f"📊 Trabajos encontrados: {len(works_df)}")
            
            # Mostrar trabajos en grid
            cols = st.columns(3)
            for idx, (_, work) in enumerate(works_df.iterrows()):
                with cols[idx % 3]:
                    show_work_card(work)
    
    except Exception as e:
        st.error(f"Error al cargar los trabajos: {str(e)}")
        st.info("Verifique la conexión a BigQuery y las credenciales.")

def show_work_card(work):
    """Mostrar tarjeta de trabajo"""
    with st.container():
        # Header de la tarjeta
        col1, col2 = st.columns([3, 1])
        
        with col1:
            category_name = CATEGORIES.get(work['category'], work['category'])
            st.markdown(f"**{work['work_name']}**")
            st.caption(f"{get_category_icon(work['category'])} {category_name}")
        
        with col2:
            st.markdown(f"{get_status_badge(work['status'])}")
        
        # Descripción
        if work['short_description']:
            st.markdown(f"*{work['short_description']}*")
        
        # Metadatos
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"Versión: {work['version']}")
        with col2:
            st.caption(f"Creado: {format_date(work['created_date'])}")
        
        # Botón para ver trabajo
        if st.button(f"Ver Trabajo", key=f"view_{work['work_id']}"):
            st.session_state['selected_work'] = work['work_id']
            st.rerun()
        
        st.divider()

if __name__ == "__main__":
    main()
