#!/bin/bash

# Script para configurar las ramas de Git para el proyecto data_science_index
# Ramas: main (Productivo), develop (Desarrollo), qa (Calidad)

echo "🌿 Configurando ramas de Git para data_science_index..."

# Crear rama de desarrollo
git checkout -b develop
echo "✅ Rama 'develop' creada para Desarrollo"

# Crear rama de calidad
git checkout -b qa
echo "✅ Rama 'qa' creada para Calidad"

# Volver a main (Productivo)
git checkout main
echo "✅ Rama 'main' configurada para Productivo"

# Mostrar ramas creadas
echo ""
echo "📋 Ramas configuradas:"
git branch -a

echo ""
echo "🎯 Flujo de trabajo recomendado:"
echo "   main    → Productivo (Cloud Run)"
echo "   qa      → Calidad (Testing)"
echo "   develop → Desarrollo (Local/Dev)"
echo ""
echo "✅ Configuración de ramas completada!"
