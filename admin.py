"""
Punto de entrada para la interfaz de administración
"""
import sys
import os

# Agregar el directorio admin al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'admin'))

# Importar y ejecutar el admin principal
from admin_main import main

if __name__ == "__main__":
    main()
