# Data Science Index

Plataforma de gestión de trabajos de ciencia de datos y análisis predictivo.

## Estructura del Proyecto

- `index/` - Índice principal de trabajos
- `admin/` - Interfaz de administración
- `shared/` - Código común y utilidades
- `categories/` - Trabajos organizados por categoría
- `assets/` - Recursos estáticos (imágenes, iconos)

## Desarrollo Local

1. Instalar dependencias: `pip install -r requirements.txt`
2. Configurar variables de entorno para BigQuery
3. Ejecutar: `streamlit run index/main_index.py`

## Despliegue a Cloud Run

### Despliegue Multi-Ambiente Inteligente

El proyecto incluye un script `build_deploy.sh` que facilita el despliegue en múltiples ambientes:

```bash
# Deploy automático (detecta el proyecto activo de gcloud)
./build_deploy.sh

# Deploy explícito por ambiente
./build_deploy.sh dev    # Desarrollo (platform-partners-des)
./build_deploy.sh qua    # QA/Testing (platform-partners-qua)
./build_deploy.sh pro    # Producción (platform-partners-pro)
```

### Características del Script

✅ **Detección Automática**: Identifica el ambiente según tu proyecto de gcloud activo  
✅ **Validación Completa**: Verifica todos los archivos necesarios antes del build  
✅ **Multi-Ambiente**: Soporta DEV, QUA y PRO con configuraciones específicas  
✅ **Configuración Automática**: Establece el proyecto correcto en gcloud automáticamente  
✅ **Manejo de Errores**: Sale inmediatamente si detecta algún problema  
✅ **Información Detallada**: Muestra comandos útiles al finalizar  

### Configuración por Ambiente

| Ambiente | Proyecto | Servicio | BigQuery Dataset | Región |
|----------|----------|----------|------------------|--------|
| **DEV** | platform-partners-des | data-science-index-dev | settings | us-east1 |
| **QUA** | platform-partners-qua | data-science-index-qua | settings | us-east1 |
| **PRO** | platform-partners-pro | data-science-index | settings | us-east1 |

**Nota**: El script configura automáticamente el proyecto correcto en gcloud, y BigQuery usa ese proyecto activo. No se requiere configuración adicional.

### Comandos Útiles Post-Deploy

```bash
# Ver la URL del servicio (PRO)
gcloud run services describe data-science-index --region=us-east1 --project=platform-partners-pro --format='value(status.url)'

# Ver logs en tiempo real (DEV)
gcloud run services logs read data-science-index-dev --region=us-east1 --project=platform-partners-des --tail

# Ver información del servicio (QUA)
gcloud run services describe data-science-index-qua --region=us-east1 --project=platform-partners-qua
```

## Base de Datos

Tabla principal: `platform-partners-des.settings.works_index`

## Arquitectura del Proyecto

### Archivos Core
- `index/main_index.py` - Aplicación principal Streamlit
- `admin/admin_main.py` - Panel de administración

### Módulos Compartidos (`shared/`)
- `config.py` - Configuraciones generales y constantes
- `database.py` - Conexión y operaciones BigQuery (usa proyecto activo de gcloud)
- `utils.py` - Funciones utilitarias

### Trabajos por Categoría (`categories/`)
- `calls_analysis/individual_companies.py` - Análisis por compañía
- `calls_analysis/total_analysis.py` - Análisis consolidado

### Deploy
- `build_deploy.sh` - Script de despliegue multi-ambiente
- `Dockerfile` - Configuración Docker para Cloud Run
- `requirements.txt` - Dependencias Python

## Configuración Multi-Ambiente

El proyecto usa una arquitectura simple donde:

1. **`build_deploy.sh`** configura automáticamente el proyecto correcto en gcloud
2. **BigQuery** usa el proyecto activo de gcloud (sin configuración adicional)
3. **No se requieren** archivos de configuración por ambiente

```bash
# El script hace esto internamente:
gcloud config set project platform-partners-des  # DEV
gcloud config set project platform-partners-qua  # QUA
gcloud config set project platform-partners-pro  # PRO

# Y BigQuery automáticamente usa ese proyecto
```

**Ventajas de esta arquitectura**:
- ✅ Menos archivos = Menos complejidad
- ✅ Una sola fuente de verdad (build_deploy.sh)
- ✅ No hay riesgo de configuraciones desalineadas
- ✅ Consistente con otros proyectos
