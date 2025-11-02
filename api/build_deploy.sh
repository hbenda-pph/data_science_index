#!/bin/bash

# =============================================================================
# SCRIPT DE BUILD & DEPLOY PARA DATA SCIENCE INDEX API
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
        echo "Uso: ./api/build_deploy.sh [dev|qua|pro]"
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
        SERVICE_NAME="data-science-index-api-dev"
        SERVICE_ACCOUNT="streamlit-bigquery-sa@platform-partners-des.iam.gserviceaccount.com"
        ;;
    qua)
        PROJECT_ID="platform-partners-qua"
        SERVICE_NAME="data-science-index-api-qua"
        SERVICE_ACCOUNT="streamlit-bigquery-sa@platform-partners-qua.iam.gserviceaccount.com"
        ;;
    pro)
        PROJECT_ID="platform-partners-pro"
        SERVICE_NAME="data-science-index-api"
        SERVICE_ACCOUNT="streamlit-bigquery-sa@platform-partners-pro.iam.gserviceaccount.com"
        ;;
esac

REGION="us-east1"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MEMORY="1Gi"
CPU="1"
TIMEOUT="300"
MAX_INSTANCES="10"
MIN_INSTANCES="0"
CONCURRENCY="80"
PORT="8080"

echo "🚀 Iniciando Build & Deploy para Data Science Index API"
echo "================================================================"
echo "🌍 AMBIENTE: ${ENVIRONMENT^^}"
echo "📋 Configuración:"
echo "   Proyecto: ${PROJECT_ID}"
echo "   Servicio: ${SERVICE_NAME}"
echo "   Región: ${REGION}"
echo "   Imagen: ${IMAGE_TAG}"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "api/main.py" ]; then
    echo "❌ Error: api/main.py no encontrado. Ejecuta desde el directorio data_science_index/"
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

echo ""
echo "📦 PASO 1: VERIFICACIÓN DE ARCHIVOS"
echo "======================================================================="

# Verificar archivos necesarios
if [ -f "api/main.py" ]; then
    echo "✅ api/main.py encontrado"
else
    echo "❌ api/main.py no encontrado"
    exit 1
fi

if [ -f "api/requirements.txt" ]; then
    echo "✅ api/requirements.txt encontrado"
else
    echo "❌ api/requirements.txt no encontrado"
    exit 1
fi

if [ -f "api/Dockerfile" ]; then
    echo "✅ api/Dockerfile encontrado"
else
    echo "❌ api/Dockerfile no encontrado"
    exit 1
fi

if [ -d "shared" ]; then
    echo "✅ Directorio shared/ encontrado"
else
    echo "❌ Directorio shared/ no encontrado"
    exit 1
fi

echo ""
echo "🔨 PASO 2: BUILD (Creando imagen Docker)"
echo "=========================================="
# El build debe hacerse desde el directorio raíz para tener acceso a shared/
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
        --port ${PORT} \
        --service-account ${SERVICE_ACCOUNT} \
        --allow-unauthenticated
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
        --service-account ${SERVICE_ACCOUNT} \
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
echo "🌐 URL del servicio:"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')
echo "   ${SERVICE_URL}"
echo ""
echo "📊 Comandos útiles:"
echo "   Ver logs: gcloud run services logs read ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --tail"
echo "   Ver info: gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID}"
echo ""

