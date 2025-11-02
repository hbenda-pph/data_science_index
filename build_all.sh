#!/bin/bash

# =============================================================================
# SCRIPT DE BUILD & DEPLOY COMPLETO
# Despliega: API, Frontend y Streamlit Index
# Multi-Environment: DEV, QUA, PRO
# =============================================================================

set -e  # Salir si hay algún error

# =============================================================================
# CONFIGURACIÓN DE AMBIENTES
# =============================================================================

# Detectar proyecto activo de gcloud
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)

# Si se proporciona parámetro, usarlo; si no, detectar automáticamente
if [ -n "$1" ]; then
    ENVIRONMENT="$1"
    ENVIRONMENT=$(echo "$ENVIRONMENT" | tr '[:upper:]' '[:lower:]')
    
    if [[ ! "$ENVIRONMENT" =~ ^(dev|qua|pro)$ ]]; then
        echo "❌ Error: Ambiente inválido '$ENVIRONMENT'"
        echo "Uso: ./build_all.sh [dev|qua|pro]"
        echo ""
        echo "Ejemplos:"
        echo "  ./build_all.sh dev    # Deploy en DEV"
        echo "  ./build_all.sh qua    # Deploy en QUA"
        echo "  ./build_all.sh pro    # Deploy en PRO"
        exit 1
    fi
else
    case "$CURRENT_PROJECT" in
        platform-partners-des)
            ENVIRONMENT="dev"
            ;;
        platform-partners-qua)
            ENVIRONMENT="qua"
            ;;
        platform-partners-pro)
            ENVIRONMENT="pro"
            ;;
        *)
            echo "⚠️  Proyecto activo: ${CURRENT_PROJECT}"
            echo "⚠️  No se reconoce el proyecto. Usando DEV por defecto."
            ENVIRONMENT="dev"
            ;;
    esac
fi

echo "🚀 DEPLOY COMPLETO - Data Science Index"
echo "================================================================"
echo "🌍 AMBIENTE: ${ENVIRONMENT^^}"
echo ""
echo "Este script desplegará:"
echo "  1. API FastAPI (data-science-index-api-*)"
echo "  2. Frontend HTML/JS (data-science-index-frontend-*)"
echo "  3. Streamlit Index (data-science-index-*)"
echo ""
read -p "¿Continuar? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado"
    exit 1
fi

# PASO 1: Deploy API
echo ""
echo "════════════════════════════════════════════════════════════"
echo "📡 PASO 1: DEPLOY API"
echo "════════════════════════════════════════════════════════════"
./api/build_deploy.sh ${ENVIRONMENT}

if [ $? -ne 0 ]; then
    echo "❌ Error en deploy de API"
    exit 1
fi

# PASO 2: Deploy Frontend
echo ""
echo "════════════════════════════════════════════════════════════"
echo "🎨 PASO 2: DEPLOY FRONTEND"
echo "════════════════════════════════════════════════════════════"
./frontend/build_deploy.sh ${ENVIRONMENT}

if [ $? -ne 0 ]; then
    echo "❌ Error en deploy de Frontend"
    exit 1
fi

# PASO 3: Deploy Streamlit Index (opcional, mantener compatibilidad)
echo ""
echo "════════════════════════════════════════════════════════════"
echo "📊 PASO 3: DEPLOY STREAMLIT INDEX (Opcional)"
echo "════════════════════════════════════════════════════════════"
read -p "¿Desplegar también el Streamlit Index? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./build_deploy.sh ${ENVIRONMENT}
else
    echo "⏭️  Omitiendo deploy de Streamlit Index"
fi

echo ""
echo "✅ DEPLOY COMPLETO FINALIZADO!"
echo "================================================================"
echo ""
echo "📋 Resumen de servicios desplegados:"
echo ""
case "$ENVIRONMENT" in
    dev)
        echo "   API:      data-science-index-api-dev"
        echo "   Frontend: data-science-index-frontend-dev"
        echo "   Streamlit: data-science-index-dev (si se desplegó)"
        ;;
    qua)
        echo "   API:      data-science-index-api-qua"
        echo "   Frontend: data-science-index-frontend-qua"
        echo "   Streamlit: data-science-index-qua (si se desplegó)"
        ;;
    pro)
        echo "   API:      data-science-index-api"
        echo "   Frontend: data-science-index-frontend"
        echo "   Streamlit: data-science-index (si se desplegó)"
        ;;
esac
echo ""

