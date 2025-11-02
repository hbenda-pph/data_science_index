#!/bin/bash

# =============================================================================
# SCRIPT DE BUILD & DEPLOY PARA DATA SCIENCE INDEX FRONTEND
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
        echo "Uso: ./frontend/build_deploy.sh [dev|qua|pro]"
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
            ENVIRONMENT="dev"
            ;;
    esac
fi

# Configuración según ambiente
case "$ENVIRONMENT" in
    dev)
        PROJECT_ID="platform-partners-des"
        SERVICE_NAME="data-science-index-frontend-dev"
        API_SERVICE_NAME="data-science-index-api-dev"
        ;;
    qua)
        PROJECT_ID="platform-partners-qua"
        SERVICE_NAME="data-science-index-frontend-qua"
        API_SERVICE_NAME="data-science-index-api-qua"
        ;;
    pro)
        PROJECT_ID="platform-partners-pro"
        SERVICE_NAME="data-science-index-frontend"
        API_SERVICE_NAME="data-science-index-api"
        ;;
esac

REGION="us-east1"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MEMORY="512Mi"
CPU="1"
TIMEOUT="300"
MAX_INSTANCES="10"
MIN_INSTANCES="0"
CONCURRENCY="80"
PORT="8080"

echo "🚀 Iniciando Build & Deploy para Data Science Index Frontend"
echo "================================================================"
echo "🌍 AMBIENTE: ${ENVIRONMENT^^}"
echo "📋 Configuración:"
echo "   Proyecto: ${PROJECT_ID}"
echo "   Servicio: ${SERVICE_NAME}"
echo "   API Service: ${API_SERVICE_NAME}"
echo "   Región: ${REGION}"
echo ""

# Detectar directorio del script y directorio raíz del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_DIR="$(pwd)"

# Determinar directorio raíz del proyecto
# Caso 1: Script ejecutado desde frontend/build_deploy.sh (estamos en frontend/)
if [ -f "${SCRIPT_DIR}/index.html" ]; then
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# Caso 2: Script ejecutado desde raíz como ./frontend/build_deploy.sh
elif [ -f "${SCRIPT_DIR}/../frontend/index.html" ]; then
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# Caso 3: Estamos ya en el raíz
elif [ -f "${CURRENT_DIR}/frontend/index.html" ]; then
    PROJECT_ROOT="$CURRENT_DIR"
else
    echo "❌ Error: No se encontró directorio raíz del proyecto"
    echo "   Ejecuta desde: data_science_index/ o frontend/"
    exit 1
fi

# Navegar al directorio raíz para el build (Docker necesita contexto desde raíz)
cd "$PROJECT_ROOT"

# Verificar archivos necesarios
if [ ! -f "frontend/index.html" ]; then
    echo "❌ Error: frontend/index.html no encontrado"
    exit 1
fi

# Verificar que gcloud está configurado
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI no está instalado"
    exit 1
fi

# Configurar proyecto
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "🔧 Configurando proyecto a: ${PROJECT_ID}"
    gcloud config set project ${PROJECT_ID}
fi

# Obtener URL de la API (para información)
echo ""
echo "🔍 Obteniendo URL de la API..."
API_URL=$(gcloud run services describe ${API_SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)' 2>/dev/null)

if [ -z "$API_URL" ]; then
    echo "⚠️  Advertencia: No se pudo obtener URL de la API."
    echo "   El frontend detectará automáticamente la URL de la API."
    echo "   Asegúrate de desplegar la API primero."
else
    echo "✅ API URL detectada: ${API_URL}"
    echo "   El frontend usará detección automática para encontrar esta URL."
fi

echo ""
echo "📦 PASO 1: VERIFICACIÓN DE ARCHIVOS"
echo "======================================================================="

if [ -f "frontend/index.html" ]; then
    echo "✅ frontend/index.html encontrado"
else
    echo "❌ frontend/index.html no encontrado"
    exit 1
fi

if [ -f "frontend/Dockerfile" ]; then
    echo "✅ frontend/Dockerfile encontrado"
else
    echo "❌ frontend/Dockerfile no encontrado"
    exit 1
fi

echo ""
echo "🔨 PASO 2: BUILD (Creando imagen Docker)"
echo "=========================================="
# El build debe hacerse desde el directorio raíz para tener acceso a frontend/
gcloud builds submit --tag ${IMAGE_TAG}

if [ $? -eq 0 ]; then
    echo "✅ Build exitoso!"
else
    echo "❌ Error en el build"
    exit 1
fi

echo ""
echo "🚀 PASO 3: CREATE/UPDATE SERVICE"
echo "================================="

# Verificar si el servicio ya existe
if gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} &>/dev/null; then
    echo "📝 Actualizando servicio existente..."
    gcloud run services update ${SERVICE_NAME} \
        --image ${IMAGE_TAG} \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --memory ${MEMORY} \
        --cpu ${CPU} \
        --timeout ${TIMEOUT} \
        --max-instances ${MAX_INSTANCES} \
        --min-instances ${MIN_INSTANCES} \
        --concurrency ${CONCURRENCY} \
        --port ${PORT}
else
    echo "🆕 Creando nuevo servicio..."
    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_TAG} \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --platform managed \
        --memory ${MEMORY} \
        --cpu ${CPU} \
        --timeout ${TIMEOUT} \
        --max-instances ${MAX_INSTANCES} \
        --min-instances ${MIN_INSTANCES} \
        --concurrency ${CONCURRENCY} \
        --port ${PORT} \
        --allow-unauthenticated
fi

if [ $? -eq 0 ]; then
    echo "✅ Deploy exitoso!"
else
    echo "❌ Error en el deploy"
    exit 1
fi

echo ""
echo "✅ DEPLOY COMPLETADO!"
echo "================================================================"
echo "🌐 URL del Frontend:"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "   ${SERVICE_URL}"
echo ""
echo "📊 Comandos útiles:"
echo "   Ver logs: gcloud run services logs read ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --tail"
echo "   Ver info: gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID}"
echo ""

