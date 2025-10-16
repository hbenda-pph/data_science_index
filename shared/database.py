"""
Conexión y operaciones con BigQuery para el índice de trabajos
"""
import os
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from typing import List, Dict, Optional

class WorksDatabase:
    def __init__(self):
        """Inicializar conexión a BigQuery
        
        Usa el proyecto activo de gcloud configurado por build_deploy.sh
        No requiere configuración manual de proyecto
        """
        # Dataset y tabla son iguales en todos los ambientes
        self.dataset_id = "settings"
        self.table_id = "works_index"
        
        # Inicializar cliente BigQuery (usa proyecto activo de gcloud)
        self.client = bigquery.Client()
        
        # Obtener project_id del cliente (para referencias)
        self.project_id = self.client.project
        self.table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
    
    def get_all_works(self) -> pd.DataFrame:
        """Obtener todos los trabajos activos"""
        query = f"""
        SELECT *
        FROM `{self.table_ref}`
        WHERE status = 'active'
        ORDER BY category, created_date DESC
        """
        return self.client.query(query).to_dataframe()
    
    def get_works_by_category(self, category_name: str) -> pd.DataFrame:
        """Obtener trabajos por categoría"""
        # Primero obtener el category_id desde works_categories
        categories_table_ref = f"{self.project_id}.{self.dataset_id}.works_categories"
        category_query = f"""
        SELECT category_id
        FROM `{categories_table_ref}`
        WHERE category_name = @category_name AND is_active = true
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("category_name", "STRING", category_name)
            ]
        )
        
        category_result = self.client.query(category_query, job_config=job_config).to_dataframe()
        
        if category_result.empty:
            return pd.DataFrame()  # No hay categoría con ese nombre
        
        category_id = category_result['category_id'].iloc[0]
        
        # Ahora obtener trabajos por category_id
        works_query = f"""
        SELECT *
        FROM `{self.table_ref}`
        WHERE category = @category_id AND status = 'active'
        ORDER BY created_date DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("category_id", "STRING", category_id)
            ]
        )
        
        return self.client.query(works_query, job_config=job_config).to_dataframe()
    
    def get_work_by_id(self, work_id: str) -> Optional[Dict]:
        """Obtener un trabajo específico por ID"""
        query = f"""
        SELECT *
        FROM `{self.table_ref}`
        WHERE work_id = @work_id
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("work_id", "STRING", work_id)
            ]
        )
        result = self.client.query(query, job_config=job_config).to_dataframe()
        return result.to_dict('records')[0] if not result.empty else None
    
    def get_categories(self) -> List[str]:
        """Obtener lista de categorías únicas desde works_categories"""
        categories_table_ref = f"{self.project_id}.{self.dataset_id}.works_categories"
        query = f"""
        SELECT category_name
        FROM `{categories_table_ref}`
        WHERE is_active = true
        ORDER BY display_order, category_name
        """
        result = self.client.query(query).to_dataframe()
        return result['category_name'].tolist()
    
    def create_work(self, work_data: Dict) -> bool:
        """Crear nuevo trabajo"""
        try:
            # Preparar datos para inserción
            row_to_insert = {
                "work_id": work_data["work_id"],
                "work_name": work_data["work_name"],
                "work_slug": work_data.get("work_slug", work_data["work_id"]),
                "category": work_data["category"],
                "subcategory": work_data.get("subcategory", ""),
                "status": work_data["status"],
                "version": work_data["version"],
                "is_latest": work_data.get("is_latest", True),
                "description": work_data.get("description", ""),
                "short_description": work_data.get("short_description", ""),
                "image_preview_url": work_data.get("image_preview_url", ""),
                "created_date": work_data.get("created_date", "CURRENT_TIMESTAMP()"),
                "updated_date": "CURRENT_TIMESTAMP()",
                "activated_date": work_data.get("activated_date"),
                "archived_date": work_data.get("archived_date"),
                "streamlit_page": work_data["streamlit_page"],
                "config_json": work_data.get("config_json", "{}"),
                "notes": work_data.get("notes", ""),
                "tags": work_data.get("tags", [])
            }
            
            # Insertar en BigQuery
            errors = self.client.insert_rows_json(self.table_ref, [row_to_insert])
            return len(errors) == 0
            
        except Exception as e:
            print(f"Error creating work: {e}")
            return False
    
    def update_work(self, work_id: str, update_data: Dict) -> bool:
        """Actualizar trabajo existente"""
        try:
            # Construir query de actualización
            set_clauses = []
            for key, value in update_data.items():
                if key != "work_id":  # No actualizar el ID
                    if isinstance(value, str):
                        set_clauses.append(f"{key} = '{value}'")
                    elif isinstance(value, list):
                        # Para arrays como tags
                        tags_str = "', '".join(value)
                        set_clauses.append(f"{key} = ['{tags_str}']")
                    else:
                        set_clauses.append(f"{key} = {value}")
            
            if not set_clauses:
                return True
            
            query = f"""
            UPDATE `{self.table_ref}`
            SET {', '.join(set_clauses)}, updated_date = CURRENT_TIMESTAMP()
            WHERE work_id = '{work_id}'
            """
            
            job = self.client.query(query)
            job.result()  # Esperar a que termine
            return True
            
        except Exception as e:
            print(f"Error updating work: {e}")
            return False
    
    def delete_work(self, work_id: str) -> bool:
        """Eliminar trabajo (soft delete - cambiar status a archived)"""
        try:
            query = f"""
            UPDATE `{self.table_ref}`
            SET status = 'archived', 
                archived_date = CURRENT_TIMESTAMP(),
                updated_date = CURRENT_TIMESTAMP()
            WHERE work_id = '{work_id}'
            """
            
            job = self.client.query(query)
            job.result()
            return True
            
        except Exception as e:
            print(f"Error deleting work: {e}")
            return False
    
    def get_work_by_slug(self, work_slug: str) -> Optional[Dict]:
        """Obtener trabajo por slug (para URLs amigables)"""
        query = f"""
        SELECT *
        FROM `{self.table_ref}`
        WHERE work_slug = @work_slug AND status = 'active'
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("work_slug", "STRING", work_slug)
            ]
        )
        result = self.client.query(query, job_config=job_config).to_dataframe()
        return result.to_dict('records')[0] if not result.empty else None
