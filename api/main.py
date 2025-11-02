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
        
        # Convertir DataFrame a lista de diccionarios
        works = []
        for _, row in df.iterrows():
            work = {
                "work_id": str(row.get("work_id", "")),
                "title": str(row.get("title", "")),
                "description": str(row.get("description", "")),
                "category": str(row.get("category", "")),
                "category_name": CATEGORIES.get(str(row.get("category", "")), str(row.get("category", ""))),
                "url": str(row.get("url", "")),
                "created_date": format_date(row.get("created_date")) if pd.notna(row.get("created_date", pd.NaT)) else "",
                "status": str(row.get("status", "active")),
                "status_badge": get_status_badge(str(row.get("status", "active"))),
                "category_icon": get_category_icon(str(row.get("category", ""))),
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
        
        # Convertir DataFrame a lista de diccionarios
        works = []
        for _, row in df.iterrows():
            work = {
                "work_id": str(row.get("work_id", "")),
                "title": str(row.get("title", "")),
                "description": str(row.get("description", "")),
                "category": str(row.get("category", "")),
                "category_name": CATEGORIES.get(str(row.get("category", "")), str(row.get("category", ""))),
                "url": str(row.get("url", "")),
                "created_date": format_date(row.get("created_date")) if pd.notna(row.get("created_date", pd.NaT)) else "",
                "status": str(row.get("status", "active")),
                "status_badge": get_status_badge(str(row.get("status", "active"))),
                "category_icon": get_category_icon(str(row.get("category", ""))),
            }
            works.append(work)
        
        return {"works": works, "count": len(works), "category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener trabajos: {str(e)}")


@app.get("/categories")
def get_categories():
    """Obtener todas las categorías disponibles"""
    try:
        categories_list = []
        for cat_id, cat_name in CATEGORIES.items():
            categories_list.append({
                "id": cat_id,
                "name": cat_name,
                "icon": get_category_icon(cat_id)
            })
        
        return {"categories": categories_list, "count": len(categories_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener categorías: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-science-index-api"}

