"""
Interfaz de administración para gestionar trabajos
"""
import streamlit as st
import sys
import os

# Agregar el directorio shared al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import WorksDatabase
from config import APP_CONFIG, WORK_STATUS, CATEGORIES
from utils import generate_work_id, format_date, show_success_message, show_error_message

# Configuración de la página
st.set_page_config(
    page_title="Admin - Data Science Index",
    page_icon="⚙️",
    layout="wide"
)

def check_admin_access():
    """Verificar acceso de administrador"""
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if not st.session_state.admin_logged_in:
        st.title("🔐 Acceso de Administrador")
        
        password = st.text_input("Contraseña:", type="password")
        if st.button("Ingresar"):
            if password == APP_CONFIG["admin_password"]:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        
        st.stop()

def main():
    """Función principal de administración"""
    check_admin_access()
    
    st.title("⚙️ Administración - Data Science Index")
    st.divider()
    
    # Tabs para diferentes funciones
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Ver Trabajos", "➕ Agregar Trabajo", "✏️ Editar Trabajo", "📈 Estadísticas"])
    
    with tab1:
        show_works_list()
    
    with tab2:
        show_add_work_form()
    
    with tab3:
        show_edit_work_form()
    
    with tab4:
        show_statistics()

def show_works_list():
    """Mostrar lista de todos los trabajos"""
    try:
        db = WorksDatabase()
        works_df = db.get_all_works()
        
        if works_df.empty:
            st.info("No hay trabajos registrados.")
            return
        
        st.subheader("📋 Lista de Trabajos")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            category_filter = st.selectbox("Filtrar por categoría:", ["Todas"] + list(CATEGORIES.keys()))
        with col2:
            status_filter = st.selectbox("Filtrar por estado:", ["Todos"] + list(WORK_STATUS.values()))
        
        # Aplicar filtros
        filtered_df = works_df.copy()
        if category_filter != "Todas":
            filtered_df = filtered_df[filtered_df['category'] == category_filter]
        if status_filter != "Todos":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        
        # Mostrar tabla
        st.dataframe(
            filtered_df[['work_name', 'category', 'status', 'version', 'created_date']],
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"Error al cargar trabajos: {str(e)}")

def show_add_work_form():
    """Formulario para agregar nuevo trabajo"""
    st.subheader("➕ Agregar Nuevo Trabajo")
    
    with st.form("add_work_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            work_name = st.text_input("Nombre del trabajo *")
            category = st.selectbox("Categoría *", list(CATEGORIES.keys()))
            subcategory = st.text_input("Subcategoría")
            version = st.text_input("Versión *", value="1.0")
        
        with col2:
            status = st.selectbox("Estado *", list(WORK_STATUS.values()))
            streamlit_page = st.text_input("Archivo Streamlit *", placeholder="categories/calls_analysis/individual_companies.py")
            image_file = st.file_uploader("Imagen preview", type=['jpg', 'jpeg', 'png', 'gif'])
        
        description = st.text_area("Descripción")
        short_description = st.text_area("Descripción corta (para el índice)")
        notes = st.text_area("Notas internas")
        
        submitted = st.form_submit_button("Agregar Trabajo")
        
        if submitted:
            if not work_name or not category or not version or not streamlit_page:
                st.error("Por favor complete todos los campos obligatorios (*)")
            else:
                try:
                    # Generar ID único
                    work_id = generate_work_id(work_name)
                    work_slug = work_id  # Por ahora usar el mismo ID como slug
                    
                    # Preparar datos para inserción
                    work_data = {
                        "work_id": work_id,
                        "work_name": work_name,
                        "work_slug": work_slug,
                        "category": category,
                        "subcategory": subcategory,
                        "status": status,
                        "version": version,
                        "is_latest": True,
                        "description": description,
                        "short_description": short_description,
                        "streamlit_page": streamlit_page,
                        "notes": notes,
                        "tags": []
                    }
                    
                    # Insertar en BigQuery
                    db = WorksDatabase()
                    if db.create_work(work_data):
                        st.success(f"✅ Trabajo '{work_name}' creado exitosamente con ID: {work_id}")
                        st.rerun()
                    else:
                        st.error("❌ Error al crear el trabajo en BigQuery")
                    
                except Exception as e:
                    st.error(f"Error al crear trabajo: {str(e)}")

def show_edit_work_form():
    """Formulario para editar trabajo existente"""
    st.subheader("✏️ Editar Trabajo Existente")
    
    try:
        db = WorksDatabase()
        works_df = db.get_all_works()
        
        if works_df.empty:
            st.info("No hay trabajos para editar.")
            return
        
        # Selector de trabajo
        work_options = {f"{row['work_name']} (v{row['version']})": row['work_id'] 
                       for _, row in works_df.iterrows()}
        
        selected_work_name = st.selectbox("Seleccionar trabajo a editar:", list(work_options.keys()))
        selected_work_id = work_options[selected_work_name]
        
        # Obtener datos del trabajo seleccionado
        work_data = db.get_work_by_id(selected_work_id)
        
        if work_data:
            with st.form("edit_work_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    work_name = st.text_input("Nombre del trabajo *", value=work_data['work_name'])
                    category = st.selectbox("Categoría *", list(CATEGORIES.keys()), 
                                          index=list(CATEGORIES.keys()).index(work_data['category']))
                    subcategory = st.text_input("Subcategoría", value=work_data.get('subcategory', ''))
                    version = st.text_input("Versión *", value=work_data['version'])
                
                with col2:
                    status = st.selectbox("Estado *", list(WORK_STATUS.values()),
                                        index=list(WORK_STATUS.values()).index(work_data['status']))
                    streamlit_page = st.text_input("Archivo Streamlit *", value=work_data['streamlit_page'])
                    image_file = st.file_uploader("Nueva imagen preview", type=['jpg', 'jpeg', 'png', 'gif'])
                
                description = st.text_area("Descripción", value=work_data.get('description', ''))
                short_description = st.text_area("Descripción corta", value=work_data.get('short_description', ''))
                notes = st.text_area("Notas internas", value=work_data.get('notes', ''))
                
                col1, col2 = st.columns(2)
                with col1:
                    update_submitted = st.form_submit_button("💾 Actualizar Trabajo")
                with col2:
                    delete_submitted = st.form_submit_button("🗑️ Archivar Trabajo", type="secondary")
                
                if update_submitted:
                    if not work_name or not category or not version or not streamlit_page:
                        st.error("Por favor complete todos los campos obligatorios (*)")
                    else:
                        try:
                            update_data = {
                                "work_name": work_name,
                                "category": category,
                                "subcategory": subcategory,
                                "status": status,
                                "version": version,
                                "description": description,
                                "short_description": short_description,
                                "streamlit_page": streamlit_page,
                                "notes": notes
                            }
                            
                            if db.update_work(selected_work_id, update_data):
                                st.success(f"✅ Trabajo '{work_name}' actualizado exitosamente")
                                st.rerun()
                            else:
                                st.error("❌ Error al actualizar el trabajo")
                                
                        except Exception as e:
                            st.error(f"Error al actualizar trabajo: {str(e)}")
                
                if delete_submitted:
                    try:
                        if db.delete_work(selected_work_id):
                            st.success(f"✅ Trabajo '{work_name}' archivado exitosamente")
                            st.rerun()
                        else:
                            st.error("❌ Error al archivar el trabajo")
                    except Exception as e:
                        st.error(f"Error al archivar trabajo: {str(e)}")
        
    except Exception as e:
        st.error(f"Error al cargar trabajos: {str(e)}")

def show_statistics():
    """Mostrar estadísticas del sistema"""
    st.subheader("📈 Estadísticas del Sistema")
    st.info("Funcionalidad de estadísticas pendiente de implementar")

if __name__ == "__main__":
    main()
