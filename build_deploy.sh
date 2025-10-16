#!/bin/bash

# =============================================================================
# SCRIPT DE BUILD & DEPLOY PARA DATA SCIENCE INDEX
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
    # Parámetro proporcionado explícitamente
    ENVIRONMENT="$1"
    ENVIRONMENT=$(echo "$ENVIRONMENT" | tr '[:upper:]' '[:lower:]')  # Convertir a minúsculas
    
    # Validar ambiente
    if [[ ! "$ENVIRONMENT" =~ ^(dev|qua|pro)$ ]]; then
        echo "❌ Error: Ambiente inválido '$ENVIRONMENT'"
        echo "Uso: ./build_deploy.sh [dev|qua|pro]"
        echo ""
        echo "Ejemplos:"
        echo "  ./build_deploy.sh dev    # Deploy en DEV (platform-partners-des)"
        echo "  ./build_deploy.sh qua    # Deploy en QUA (platform-partners-qua)"
        echo "  ./build_deploy.sh pro    # Deploy en PRO (platform-partners-pro)"
        echo ""
        echo "O ejecuta sin parámetros para usar el proyecto activo de gcloud"
        exit 1
    fi
else
    # Detectar automáticamente según el proyecto activo
    echo "🔍 Detectando ambiente desde proyecto activo de gcloud..."
    
    case "$CURRENT_PROJECT" in
        platform-partners-des)
            ENVIRONMENT="dev"
            echo "✅ Detectado: DEV (platform-partners-des)"
            ;;
        platform-partners-qua)
            ENVIRONMENT="qua"
            echo "✅ Detectado: QUA (platform-partners-qua)"
            ;;
        platform-partners-pro)
            ENVIRONMENT="pro"
            echo "✅ Detectado: PRO (platform-partners-pro)"
            ;;
        *)
            echo "⚠️  Proyecto activo: ${CURRENT_PROJECT}"
            echo "⚠️  No se reconoce el proyecto. Usando DEV por defecto."
            ENVIRONMENT="dev"
            ;;
    esac
fi

# Configuración según ambiente
case "$ENVIRONMENT" in
    dev)
        PROJECT_ID="platform-partners-des"
        SERVICE_NAME="data-science-index-dev"
        SERVICE_ACCOUNT="streamlit-bigquery-sa@platform-partners-des.iam.gserviceaccount.com"
        ;;
    qua)
        PROJECT_ID="platform-partners-qua"
        SERVICE_NAME="data-science-index-qua"
        SERVICE_ACCOUNT="streamlit-bigquery-sa@platform-partners-qua.iam.gserviceaccount.com"
        ;;
    pro)
        PROJECT_ID="platform-partners-pro"
        SERVICE_NAME="data-science-index"
        SERVICE_ACCOUNT="streamlit-bigquery-sa@platform-partners-pro.iam.gserviceaccount.com"
        ;;
esac

REGION="us-east1"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MEMORY="2Gi"
CPU="2"
TIMEOUT="300"
MAX_INSTANCES="10"
MIN_INSTANCES="0"
CONCURRENCY="80"
PORT="8080"

echo "🚀 Iniciando Build & Deploy para Data Science Index"
echo "================================================================"
echo "🌍 AMBIENTE: ${ENVIRONMENT^^}"
echo "📋 Configuración:"
echo "   Proyecto: ${PROJECT_ID}"
echo "   Servicio: ${SERVICE_NAME}"
echo "   Región: ${REGION}"
echo "   Imagen: ${IMAGE_TAG}"
echo "   Memory: ${MEMORY}"
echo "   CPU:    ${CPU}"
echo "   Timeout:       ${TIMEOUT}s"
echo "   Max Instances: ${MAX_INSTANCES}"
echo "   Min Instances: ${MIN_INSTANCES}"
echo "   Concurrency:   ${CONCURRENCY}"
echo "   Port:          ${PORT}"
echo "   Service Account: ${SERVICE_ACCOUNT}"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "index/main_index.py" ]; then
    echo "❌ Error: index/main_index.py no encontrado. Ejecuta este script desde el directorio data_science_index/"
    exit 1
fi

# Verificar que gcloud está configurado
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI no está instalado o no está en el PATH"
    exit 1
fi

# Verificar proyecto activo
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "⚠️  Proyecto actual: ${CURRENT_PROJECT}"
    echo "🔧 Configurando proyecto a: ${PROJECT_ID}"
    gcloud config set project ${PROJECT_ID}
fi

echo ""
echo "📦 PASO 1: VERIFICACIÓN DE ARCHIVOS"
echo "======================================================================="

# Verificar archivos necesarios
if [ -f "index/main_index.py" ]; then
    echo "✅ index/main_index.py encontrado"
else
    echo "❌ index/main_index.py no encontrado"
    exit 1
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt encontrado"
else
    echo "❌ requirements.txt no encontrado"
    exit 1
fi

if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile encontrado"
else
    echo "❌ Dockerfile no encontrado"
    exit 1
fi

# Verificar directorios del proyecto
if [ -d "shared" ]; then
    echo "✅ Directorio shared/ encontrado"
else
    echo "⚠️  Advertencia: No se encontró directorio shared/"
fi

if [ -d "admin" ]; then
    echo "✅ Directorio admin/ encontrado"
else
    echo "⚠️  Advertencia: No se encontró directorio admin/"
fi

if [ -d "categories" ]; then
    echo "✅ Directorio categories/ encontrado"
else
    echo "⚠️  Advertencia: No se encontró directorio categories/"
fi

# Verificar/crear directorio de assets
if [ ! -d "assets" ]; then
    echo "📁 Creando directorio assets/"
    mkdir -p assets/images assets/icons
    echo "✅ Directorio assets creado"
else
    echo "✅ Directorio assets encontrado"
fi

echo ""
echo "🔨 PASO 2: BUILD (Creando imagen Docker)"
echo "=========================================="
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
if gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} &> /dev/null; then
    echo "📝 Servicio existe, actualizando..."
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
        --set-env-vars GCP_PROJECT=${PROJECT_ID}
else
    echo "🆕 Servicio no existe, creando..."
    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_TAG} \
        --platform managed \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --allow-unauthenticated \
        --port ${PORT} \
        --service-account ${SERVICE_ACCOUNT} \
        --memory ${MEMORY} \
        --cpu ${CPU} \
        --timeout ${TIMEOUT} \
        --max-instances ${MAX_INSTANCES} \
        --min-instances ${MIN_INSTANCES} \
        --concurrency ${CONCURRENCY} \
        --set-env-vars GCP_PROJECT=${PROJECT_ID}
fi

if [ $? -eq 0 ]; then
    echo "✅ Servicio creado/actualizado exitosamente!"
else
    echo "❌ Error creando/actualizando servicio"
    exit 1
fi

echo ""
echo "🎉 ¡DEPLOY COMPLETADO EXITOSAMENTE!"
echo "=================================="
echo ""
echo "🌍 AMBIENTE: ${ENVIRONMENT^^}"
echo "📊 Información del servicio:"
echo "   Proyecto: ${PROJECT_ID}"
echo "   Servicio: ${SERVICE_NAME}"
echo "   Región:   ${REGION}"
echo ""
echo "🌐 Para ver tu aplicación:"
echo "   gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)'"
echo ""
echo "   O visita: https://console.cloud.google.com/run?project=${PROJECT_ID}"
echo ""
echo "🔧 Para ver logs en tiempo real:"
echo "   gcloud run services logs read ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --tail"
echo ""
echo "📊 Para ver información del servicio:"
echo "   gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID}"
echo ""
echo "🔄 Para deploy en otros ambientes:"
echo "   ./build_deploy.sh dev    # Deploy en DEV (desarrollo y testing)"
echo "   ./build_deploy.sh qua    # Deploy en QUA (validación y QA)"
echo "   ./build_deploy.sh pro    # Deploy en PRO (producción)"
echo ""
echo "🛑 Para eliminar el servicio:"
echo "   gcloud run services delete ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID}"
echo ""
echo "📝 Notas:"
echo "   - DEV: data-science-index-dev en platform-partners-des"
echo "   - QUA: data-science-index-qua en platform-partners-qua"
echo "   - PRO: data-science-index en platform-partners-pro"
echo "   - El script detecta automáticamente el ambiente según tu proyecto activo"
echo ""

