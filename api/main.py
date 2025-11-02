"""
API FastAPI para Data Science Index
Provee endpoints para obtener trabajos y categorías desde BigQuery
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from typing import List, Dict, Optional
import json
import pandas as pd
from datetime import datetime

# Agregar shared al path para importar módulos
# Desde /app/api/main.py -> /app/shared
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import WorksDatabase
from config import CATEGORIES

# Funciones de utilidad (sin dependencia de Streamlit)
def format_date(date_input) -> str:
    """Formatear fecha para mostrar en la interfaz"""
    if not date_input:
        return "N/A"
    
    try:
        # Si es un Timestamp de pandas
        if hasattr(date_input, 'strftime'):
            return date_input.strftime("%d/%m/%Y %H:%M")
        
        # Si es un string
        if isinstance(date_input, str):
            date_obj = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            return date_obj.strftime("%d/%m/%Y %H:%M")
        
        # Si es otro tipo, convertir a string
        return str(date_input)
    except:
        return str(date_input) if date_input else "N/A"

def get_status_badge(status: str) -> str:
    """Obtener emoji para el estado del trabajo"""
    status_emojis = {
        "active": "🟢",
        "paused": "⏸️", 
        "archived": "📁",
        "maintenance": "🔧"
    }
    return status_emojis.get(status, "❓")

def get_category_icon(category: str) -> str:
    """Obtener emoji para la categoría del trabajo"""
    category_icons = {
        "calls_analysis": "📞",
        "marketing_analysis": "📈",
        "climate_analysis": "🌡️",
        "accounting_analysis": "💰",
        "workforce_analysis": "👥"
    }
    return category_icons.get(category, "📊")

app = FastAPI(title="Data Science Index API", version="1.0.0")

# CORS para permitir llamadas desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia global de la base de datos
db = WorksDatabase()


@app.get("/")
def root():
    """Endpoint raíz"""
    return {
        "service": "Data Science Index API",
        "version": "1.0.0",
        "endpoints": {
            "/works": "Obtener todos los trabajos",
            "/works/{category}": "Obtener trabajos por categoría",
            "/categories": "Obtener todas las categorías"
        }
    }


@app.get("/works")
def get_all_works():
    """Obtener todos los trabajos activos"""
    try:
        df = db.get_all_works()
        
        if df.empty:
            return {"works": [], "count": 0}
        
        # Obtener mapeo de categorías desde works_categories (si está disponible)
        category_map = {}
        try:
            from google.cloud import bigquery
            categories_table_ref = f"{db.project_id}.{db.dataset_id}.works_categories"
            category_query = f"""
            SELECT category_id, category_name, category_icon
            FROM `{categories_table_ref}`
            WHERE is_active = true
            """
            cat_result = db.client.query(category_query).to_dataframe()
            if not cat_result.empty:
                for _, cat_row in cat_result.iterrows():
                    category_map[str(cat_row.get("category_id", ""))] = {
                        "name": str(cat_row.get("category_name", "")),
                        "icon": str(cat_row.get("category_icon", "📊"))
                    }
        except Exception as e:
            print(f"⚠️  No se pudieron cargar categorías desde BigQuery: {e}")
        
        # Convertir DataFrame a lista de diccionarios
        works = []
        for _, row in df.iterrows():
            category_id = str(row.get("category", ""))
            
            # Obtener nombre e icono de categoría
            if category_id in category_map:
                category_name = category_map[category_id]["name"]
                category_icon = category_map[category_id]["icon"]
            else:
                # Fallback a config.py
                category_name = CATEGORIES.get(category_id, category_id)
                category_icon = get_category_icon(category_id)
            
            work = {
                "work_id": str(row.get("work_id", "")),
                "title": str(row.get("work_name", "")),  # Usar work_name de BigQuery
                "work_name": str(row.get("work_name", "")),  # Mantener ambos para compatibilidad
                "description": str(row.get("description", "")),
                "short_description": str(row.get("short_description", "")),
                "category": category_id,
                "category_name": category_name,
                "url": str(row.get("work_url", "")),  # Usar work_url de BigQuery
                "work_url": str(row.get("work_url", "")),  # Mantener ambos para compatibilidad
                "version": str(row.get("version", "")),
                "created_date": format_date(row.get("created_date")) if pd.notna(row.get("created_date", pd.NaT)) else "",
                "status": str(row.get("status", "active")),
                "status_badge": get_status_badge(str(row.get("status", "active"))),
                "category_icon": category_icon,
                "notes": str(row.get("notes", "")),
            }
            works.append(work)
        
        return {"works": works, "count": len(works)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener trabajos: {str(e)}")


@app.get("/works/{category}")
def get_works_by_category(category: str):
    """Obtener trabajos por categoría"""
    try:
        df = db.get_works_by_category(category)
        
        if df.empty:
            return {"works": [], "count": 0, "category": category}
        
        # Obtener mapeo de categorías desde works_categories (si está disponible)
        category_map = {}
        try:
            from google.cloud import bigquery
            categories_table_ref = f"{db.project_id}.{db.dataset_id}.works_categories"
            category_query = f"""
            SELECT category_id, category_name, category_icon
            FROM `{categories_table_ref}`
            WHERE is_active = true
            """
            cat_result = db.client.query(category_query).to_dataframe()
            if not cat_result.empty:
                for _, cat_row in cat_result.iterrows():
                    category_map[str(cat_row.get("category_id", ""))] = {
                        "name": str(cat_row.get("category_name", "")),
                        "icon": str(cat_row.get("category_icon", "📊"))
                    }
        except Exception as e:
            print(f"⚠️  No se pudieron cargar categorías desde BigQuery: {e}")
        
        # Convertir DataFrame a lista de diccionarios
        works = []
        for _, row in df.iterrows():
            category_id = str(row.get("category", ""))
            
            # Obtener nombre e icono de categoría
            if category_id in category_map:
                category_name = category_map[category_id]["name"]
                category_icon = category_map[category_id]["icon"]
            else:
                # Fallback a config.py
                category_name = CATEGORIES.get(category_id, category_id)
                category_icon = get_category_icon(category_id)
            
            work = {
                "work_id": str(row.get("work_id", "")),
                "title": str(row.get("work_name", "")),  # Usar work_name de BigQuery
                "work_name": str(row.get("work_name", "")),  # Mantener ambos para compatibilidad
                "description": str(row.get("description", "")),
                "short_description": str(row.get("short_description", "")),
                "category": category_id,
                "category_name": category_name,
                "url": str(row.get("work_url", "")),  # Usar work_url de BigQuery
                "work_url": str(row.get("work_url", "")),  # Mantener ambos para compatibilidad
                "version": str(row.get("version", "")),
                "created_date": format_date(row.get("created_date")) if pd.notna(row.get("created_date", pd.NaT)) else "",
                "status": str(row.get("status", "active")),
                "status_badge": get_status_badge(str(row.get("status", "active"))),
                "category_icon": category_icon,
                "notes": str(row.get("notes", "")),
            }
            works.append(work)
        
        return {"works": works, "count": len(works), "category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener trabajos: {str(e)}")


@app.get("/categories")
def get_categories():
    """Obtener todas las categorías disponibles desde works_categories"""
    try:
        # Intentar obtener categorías desde BigQuery
        try:
            from google.cloud import bigquery
            
            categories_table_ref = f"{db.project_id}.{db.dataset_id}.works_categories"
            query = f"""
            SELECT category_id, category_name, category_icon, description, display_order
            FROM `{categories_table_ref}`
            WHERE is_active = true
            ORDER BY display_order, category_name
            """
            result = db.client.query(query).to_dataframe()
            
            if not result.empty:
                categories_list = []
                for _, row in result.iterrows():
                    categories_list.append({
                        "id": str(row.get("category_id", "")),
                        "name": str(row.get("category_name", "")),
                        "icon": str(row.get("category_icon", "📊")),
                        "description": str(row.get("description", "")),
                        "display_order": int(row.get("display_order", 0)) if pd.notna(row.get("display_order")) else 0
                    })
                return {"categories": categories_list, "count": len(categories_list)}
        except Exception as bq_error:
            # Fallback: usar CATEGORIES de config.py
            print(f"⚠️  No se pudo acceder a works_categories, usando fallback: {bq_error}")
        
        # Fallback a config.py
        categories_list = []
        for cat_id, cat_name in CATEGORIES.items():
            categories_list.append({
                "id": cat_id,
                "name": cat_name,
                "icon": get_category_icon(cat_id),
                "description": "",
                "display_order": 0
            })
        
        return {"categories": categories_list, "count": len(categories_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener categorías: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-science-index-api"}

