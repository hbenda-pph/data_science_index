"""
Índice principal de trabajos de ciencia de datos
"""
import streamlit as st
import sys
import os
from google.cloud import bigquery

# Agregar el directorio shared al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import WorksDatabase
from config import APP_CONFIG, CATEGORIES
from utils import format_date, get_status_badge, get_category_icon

# Importar estilos compartidos externos (desde módulo compartido)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'analysis_predictive_shared'))
from streamlit_config import apply_standard_styles

# Configuración de la página
st.set_page_config(
    page_title=APP_CONFIG["title"],
    page_icon=APP_CONFIG["page_icon"],
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilos centralizados INMEDIATAMENTE después de set_page_config
apply_standard_styles()

def main():
    """Función principal del índice"""
    
    # Verificar si se quiere ver un trabajo específico
    query_params = st.query_params
    if "work_url" in query_params:
        show_external_work(query_params["work_url"])
        return
    
    if "work" in query_params:
        work_id = query_params["work"]
        show_work(work_id)
        return
    
    # Header mejorado
    st.markdown("""
    <div class="scientific-header">
        <h1>📊 Data Science Index</h1>
        <p>Portafolio de Análisis Predictivo y Ciencia de Datos</p>
    </div>
    """, unsafe_allow_html=True)
    
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
            
            # Opción de vista: Tabla o Cards
            view_option = st.radio("Vista:", ["📋 Tabla", "🎴 Cards"], horizontal=True)
            
            if view_option == "📋 Tabla":
                show_works_table(works_df)
            else:
                # Mostrar trabajos en tabla horizontal (estilo Kaggle)
                for idx, (_, work) in enumerate(works_df.iterrows()):
                    show_work_card_horizontal(work)
    
    except Exception as e:
        st.error(f"Error al cargar los trabajos: {str(e)}")
        st.info("Verifique la conexión a BigQuery y las credenciales.")

def show_works_table(works_df):
    """Mostrar trabajos en formato tabla científica"""
    
    # Preparar datos para la tabla
    table_data = []
    
    for _, work in works_df.iterrows():
        # Obtener información de categoría
        try:
            db = WorksDatabase()
            categories_table_ref = f"{db.project_id}.{db.dataset_id}.works_categories"
            category_query = f"""
            SELECT category_name, category_icon
            FROM `{categories_table_ref}`
            WHERE category_id = @category_id AND is_active = true
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("category_id", "STRING", work['category'])
                ]
            )
            
            category_result = db.client.query(category_query, job_config=job_config).to_dataframe()
            
            if not category_result.empty:
                category_name = category_result['category_name'].iloc[0]
                category_icon = category_result['category_icon'].iloc[0]
            else:
                category_name = work['category']
                category_icon = "📊"
                
        except Exception as e:
            # Fallback: usar config.py (para ejecución local sin permisos)
            category_id = work['category']
            category_name = CATEGORIES.get(category_id, category_id)
            category_icon = get_category_icon(category_id)
        
        # Estado con color
        status_display = {
            "active": "🟢 Activo",
            "paused": "⏸️ Pausado",
            "archived": "📁 Archivado",
            "maintenance": "🔧 Mantenimiento"
        }.get(work['status'], "❓ Desconocido")
        
        table_data.append({
            "Trabajo": work['work_name'],
            "Categoría": f"{category_icon} {category_name}",
            "Estado": status_display,
            "Versión": work['version'],
            "Creado": format_date(work['created_date']),
            "Acción": f"work_{work['work_id']}"
        })
    
    # Mostrar tabla con st.dataframe personalizada
    if table_data:
        # Convertir a DataFrame para st.dataframe
        import pandas as pd
        df_table = pd.DataFrame(table_data)
        
        # Configurar la tabla
        st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Trabajo": st.column_config.TextColumn(
                    "Trabajo",
                    width="large",
                    help="Nombre del trabajo de ciencia de datos"
                ),
                "Categoría": st.column_config.TextColumn(
                    "Categoría",
                    width="medium",
                    help="Categoría científica del trabajo"
                ),
                "Estado": st.column_config.TextColumn(
                    "Estado",
                    width="small",
                    help="Estado actual del trabajo"
                ),
                "Versión": st.column_config.TextColumn(
                    "Versión",
                    width="small",
                    help="Versión del trabajo"
                ),
                "Creado": st.column_config.TextColumn(
                    "Creado",
                    width="medium",
                    help="Fecha de creación"
                ),
                "Acción": st.column_config.TextColumn(
                    "Acción",
                    width="small",
                    help="Acciones disponibles"
                )
            }
        )
        
        # Botones de acción (debajo de la tabla)
        st.markdown("### 🚀 Acciones")
        cols = st.columns(min(len(table_data), 4))  # Máximo 4 columnas
        
        for i, work_data in enumerate(table_data):
            with cols[i % 4]:
                work_id = work_data["Acción"].replace("work_", "")
                work_name = work_data["Trabajo"]
                
                if st.button(f"Ver {work_name[:20]}...", key=f"table_view_{work_id}"):
                    # Obtener work_url de la base de datos
                    try:
                        db = WorksDatabase()
                        work_info = db.get_work_by_id(work_id)
                        if work_info and work_info.get('work_url'):
                            st.query_params.work_url = work_info['work_url']
                            st.rerun()
                        else:
                            st.error("❌ No se especificó URL para este trabajo")
                    except Exception as e:
                        st.error(f"❌ Error al cargar trabajo: {str(e)}")

def show_work_card_horizontal(work):
    """Mostrar tarjeta de trabajo en formato horizontal estilo Kaggle"""
    
    # Obtener información de categoría
    try:
        db = WorksDatabase()
        categories_table_ref = f"{db.project_id}.{db.dataset_id}.works_categories"
        category_query = f"""
        SELECT category_name, category_icon, description as category_description
        FROM `{categories_table_ref}`
        WHERE category_id = @category_id AND is_active = true
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("category_id", "STRING", work['category'])
            ]
        )
        
        category_result = db.client.query(category_query, job_config=job_config).to_dataframe()
        
        if not category_result.empty:
            category_name = category_result['category_name'].iloc[0]
            category_icon = category_result['category_icon'].iloc[0]
            category_description = category_result['category_description'].iloc[0]
        else:
            category_name = work['category']
            category_icon = "📊"
            category_description = ""
            
    except Exception as e:
        # Fallback: usar config.py (para ejecución local sin permisos)
        category_id = work['category']
        category_name = CATEGORIES.get(category_id, category_id)
        category_icon = get_category_icon(category_id)
        category_description = ""
    
    # Contenedor principal con borde y padding usando clase CSS centralizada
    with st.container():
        st.markdown("""
        <div class="work-card">
        """, unsafe_allow_html=True)
        
        # Header del trabajo
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            # Título principal
            st.markdown(f"### {work['work_name']}")
            
            # Categoría con icono
            st.markdown(f"**{category_icon} {category_name}**")
            
            # Descripción corta
            if work['short_description']:
                st.markdown(f"*{work['short_description']}*")
        
        with col2:
            # Estado
            status_color = {
                "active": "🟢",
                "paused": "⏸️",
                "archived": "📁",
                "maintenance": "🔧"
            }.get(work['status'], "❓")
            
            st.markdown(f"**Estado:** {status_color} {work['status'].title()}")
            st.markdown(f"**Versión:** {work['version']}")
        
        with col3:
            # Metadatos
            st.markdown(f"**Creado:** {format_date(work['created_date'])}")
            
        # Botón para ver trabajo
        if st.button(f"🚀 Ver Trabajo", key=f"view_{work['work_id']}", type="primary"):
            work_url = work.get('work_url')
            if work_url:
                st.query_params.work_url = work_url
                st.rerun()
            else:
                st.error("❌ No se especificó URL para este trabajo")
        
        # Descripción completa del trabajo (si existe)
        if work.get('description'):
            st.markdown("---")
            st.markdown("**📝 Descripción:**")
            st.markdown(work['description'])
        
        # Descripción de la categoría (si existe)
        if category_description:
            st.markdown("---")
            st.markdown("**📂 Sobre esta categoría:**")
            st.markdown(category_description)
        
        # Tags o notas (si existen)
        if work.get('notes'):
            st.markdown("---")
            st.markdown("**📌 Notas:**")
            st.markdown(f"*{work['notes']}*")
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_external_work(work_url: str):
    """Mostrar trabajo externo embebido"""
    
    # Header con botón de regreso
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        <div class="external-work-header">
            <h1>📊 Trabajo Externo</h1>
            <p>Cargando trabajo desde URL externa...</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔙 Volver al Índice", type="secondary"):
            st.query_params.clear()
            st.rerun()
    
    # Mostrar trabajo en iframe
    try:
        st.components.v1.iframe(work_url, height=800)
    except Exception as e:
        st.error(f"❌ Error al cargar el trabajo: {str(e)}")
        st.info(f"URL: {work_url}")
        
        # Botón alternativo para abrir en nueva ventana
        st.markdown(f"""
        <div class="external-link">
            <a href="{work_url}" target="_blank">
                🚀 Abrir trabajo en nueva ventana
            </a>
        </div>
        """, unsafe_allow_html=True)

def show_work(work_id: str):
    """Mostrar y ejecutar un trabajo específico"""
    try:
        db = WorksDatabase()
        work_data = db.get_work_by_id(work_id)
        
        if not work_data:
            st.error(f"❌ Trabajo con ID '{work_id}' no encontrado")
            st.info("🔙 [Volver al Índice](?)")
            return
        
        # Header del trabajo mejorado
        st.markdown(f"""
        <div class="external-work-header">
            <h1>📊 {work_data['work_name']}</h1>
            <p>Versión {work_data['version']} • {get_status_badge(work_data['status'])} {work_data['status'].title()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Información del trabajo en cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"📅 **Creado:** {format_date(work_data['created_date'])}")
        
        with col2:
            st.success(f"📊 **Versión:** {work_data['version']}")
        
        with col3:
            status_color = "🟢" if work_data['status'] == 'active' else "⏸️" if work_data['status'] == 'paused' else "🔧"
            st.warning(f"{status_color} **Estado:** {work_data['status'].title()}")
        
        # Descripción
        if work_data.get('description'):
            st.markdown("### 📝 Descripción")
            st.write(work_data['description'])
        
        # Botón para volver al índice
        if st.button("🔙 Volver al Índice"):
            st.query_params.clear()
            st.rerun()
        
        st.divider()
        
        # Ejecutar el archivo Streamlit del trabajo
        streamlit_page = work_data.get('streamlit_page')
        if streamlit_page:
            st.markdown("### 🚀 Ejecutando Trabajo")
            
            try:
                # SOLUCIÓN ROBUSTA: Buscar el archivo en todas las ubicaciones posibles
                st.info(f"📁 Ejecutando: `{streamlit_page}`")
                
                # Generar todas las rutas posibles
                possible_paths = []
                
                if streamlit_page.startswith('../'):
                    # Para rutas que empiezan con ../
                    relative_path = streamlit_page[3:]  # Remover '../'
                    
                    # Rutas desde diferentes puntos de partida
                    possible_paths = [
                        os.path.join('/', relative_path),  # Desde raíz
                        os.path.join('/app', relative_path),  # Desde /app
                        os.path.join(os.getcwd(), relative_path),  # Desde directorio actual
                        os.path.join(os.path.dirname(__file__), '..', '..', relative_path),  # Desde index/../../
                        os.path.join(os.path.dirname(__file__), '..', '..', '..', relative_path),  # Desde index/../../../
                    ]
                else:
                    # Para rutas normales
                    possible_paths = [
                        os.path.join(os.path.dirname(__file__), '..', streamlit_page),
                        os.path.join('/', streamlit_page),
                        os.path.join('/app', streamlit_page),
                        os.path.join(os.getcwd(), streamlit_page),
                    ]
                
                # Buscar el archivo
                file_found = False
                file_path = None
                
                for path in possible_paths:
                    if os.path.exists(path):
                        file_path = path
                        file_found = True
                        break
                
                if file_found:
                    st.success(f"✅ Archivo encontrado en: `{file_path}`")
                    
                    # Mostrar información del archivo
                    file_size = os.path.getsize(file_path)
                    st.info(f"📊 Tamaño del archivo: {file_size} bytes")
                    
                    # Mostrar contenido del archivo
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            st.markdown("**📄 Contenido del archivo:**")
                            st.code(content[:1000] + "..." if len(content) > 1000 else content, language='python')
                    except Exception as e:
                        st.error(f"❌ Error al leer el archivo: {str(e)}")
                        
                else:
                    st.error("❌ Archivo no encontrado en ninguna ubicación posible")
                    st.info("**🔍 Rutas probadas:**")
                    for i, path in enumerate(possible_paths):
                        st.info(f"  {i+1}. `{path}`")
                    
                    # Búsqueda exhaustiva como último recurso
                    st.info("**🔍 Búsqueda exhaustiva:**")
                    try:
                        # Buscar archivos dashboard.py en todo el sistema
                        found_files = []
                        st.info("🔍 Buscando archivos 'dashboard.py'...")
                        
                        # Buscar en directorios comunes
                        search_dirs = ['/', '/app', '/tmp', '/home', '/usr', '/opt']
                        
                        for search_dir in search_dirs:
                            if os.path.exists(search_dir):
                                try:
                                    for root, dirs, files in os.walk(search_dir):
                                        for file in files:
                                            if file == 'dashboard.py':
                                                found_files.append(os.path.join(root, file))
                                                if len(found_files) >= 10:  # Limitar resultados
                                                    break
                                        if len(found_files) >= 10:
                                            break
                                except PermissionError:
                                    continue  # Saltar directorios sin permisos
                                except Exception:
                                    continue
                        
                        if found_files:
                            st.success(f"✅ Encontrados {len(found_files)} archivos 'dashboard.py':")
                            for i, file in enumerate(found_files):
                                st.info(f"  {i+1}. `{file}`")
                                
                            # Buscar específicamente calls_analysis_dashboard
                            st.info("🔍 Buscando directorios 'calls_analysis_dashboard'...")
                            dashboard_dirs = []
                            for search_dir in search_dirs:
                                if os.path.exists(search_dir):
                                    try:
                                        for root, dirs, files in os.walk(search_dir):
                                            if 'calls_analysis_dashboard' in dirs:
                                                dashboard_dirs.append(os.path.join(root, 'calls_analysis_dashboard'))
                                    except:
                                        continue
                            
                            if dashboard_dirs:
                                st.success(f"✅ Encontrados {len(dashboard_dirs)} directorios 'calls_analysis_dashboard':")
                                for i, dir_path in enumerate(dashboard_dirs):
                                    st.info(f"  {i+1}. `{dir_path}`")
                                    # Verificar si tiene dashboard.py
                                    dashboard_file = os.path.join(dir_path, 'dashboard.py')
                                    if os.path.exists(dashboard_file):
                                        st.success(f"    ✅ Contiene dashboard.py: `{dashboard_file}`")
                                    else:
                                        st.info(f"    ❌ No contiene dashboard.py")
                        else:
                            st.warning("⚠️ No se encontró ningún archivo 'dashboard.py'")
                            
                    except Exception as e:
                        st.error(f"Error en búsqueda exhaustiva: {e}")
                    
            except Exception as e:
                st.error(f"❌ Error al ejecutar el trabajo: {str(e)}")
        else:
            st.warning("⚠️ No se especificó archivo Streamlit para este trabajo.")
    
    except Exception as e:
        st.error(f"❌ Error al cargar el trabajo: {str(e)}")
        st.info("🔙 [Volver al Índice](?)")

if __name__ == "__main__":
    main()
