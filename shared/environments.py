"""
Configuración de entornos para el proyecto
"""
import os
from typing import Dict

class EnvironmentConfig:
    """Configuración específica por entorno"""
    
    def __init__(self, environment: str = "dev"):
        self.environment = environment
        self.config = self._get_environment_config()
    
    def _get_environment_config(self) -> Dict:
        """Obtener configuración específica del entorno"""
        
        base_config = {
            "app_name": "Data Science Index",
            "debug": True,
            "log_level": "INFO"
        }
        
        if self.environment == "dev":
            return {
                **base_config,
                "debug": True,
                "log_level": "DEBUG",
                "bigquery_project": "platform-partners-des",
                "bigquery_dataset": "settings",
                "bigquery_table": "works_index",
                "streamlit_port": 8501,
                "streamlit_host": "localhost"
            }
        
        elif self.environment == "qua":
            return {
                **base_config,
                "debug": False,
                "log_level": "INFO",
                "bigquery_project": "platform-partners-qua",
                "bigquery_dataset": "settings",
                "bigquery_table": "works_index", 
                "streamlit_port": 8502,
                "streamlit_host": "0.0.0.0"
            }
        
        elif self.environment == "pro":
            return {
                **base_config,
                "debug": False,
                "log_level": "WARNING",
                "bigquery_project": "platform-partners-pro",
                "bigquery_dataset": "settings",
                "bigquery_table": "works_index",
                "streamlit_port": 8080,
                "streamlit_host": "0.0.0.0"
            }
        
        else:
            raise ValueError(f"Entorno no válido: {self.environment}")
    
    def get_bigquery_table_ref(self) -> str:
        """Obtener referencia completa de la tabla BigQuery"""
        return f"{self.config['bigquery_project']}.{self.config['bigquery_dataset']}.{self.config['bigquery_table']}"
    
    def get_streamlit_config(self) -> Dict:
        """Obtener configuración de Streamlit"""
        return {
            "server.port": self.config["streamlit_port"],
            "server.address": self.config["streamlit_host"],
            "server.headless": True,
            "browser.gatherUsageStats": False
        }

# Instancia global de configuración
def get_config(environment: str = None) -> EnvironmentConfig:
    """Obtener configuración del entorno actual"""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "dev")
    
    return EnvironmentConfig(environment)
