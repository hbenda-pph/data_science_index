# 🔑 Configuración de Service Accounts Multi-Ambiente

Scripts para replicar la service account `streamlit-bigquery-sa` de DEV a QUA y PRO.

## 📋 Scripts Disponibles

### 1. `inspect_service_account.py` - Solo Lectura ✅

Inspecciona la configuración actual en DEV sin hacer cambios.

```bash
python inspect_service_account.py
```

**Output**:
- ✅ Información básica de la service account
- ✅ Roles IAM a nivel proyecto
- ✅ Permisos en dataset BigQuery
- ✅ Permisos en tablas específicas
- ✅ Comandos sugeridos para replicación manual

### 2. `setup_service_accounts.py` - Replicación Automática 🚀

Replica automáticamente la configuración de DEV a QUA y PRO.

```bash
python setup_service_accounts.py
```

**Qué hace**:
1. Describe la service account en DEV
2. Obtiene todos los roles y permisos
3. Crea service accounts en QUA y PRO (si no existen)
4. Replica roles IAM
5. Replica permisos de BigQuery
6. Otorga permisos a tablas específicas

## 🚀 Uso Recomendado

### Paso 1: Inspeccionar (Opcional)

```bash
python inspect_service_account.py
```

Esto te muestra qué se va a replicar sin hacer cambios.

### Paso 2: Replicar

```bash
python setup_service_accounts.py
```

El script te pedirá confirmación antes de hacer cambios.

### Paso 3: Verificar

```bash
# DEV
gcloud iam service-accounts describe streamlit-bigquery-sa@platform-partners-des.iam.gserviceaccount.com --project=platform-partners-des

# QUA
gcloud iam service-accounts describe streamlit-bigquery-sa@platform-partners-qua.iam.gserviceaccount.com --project=platform-partners-qua

# PRO
gcloud iam service-accounts describe streamlit-bigquery-sa@platform-partners-pro.iam.gserviceaccount.com --project=platform-partners-pro
```

## 📊 Permisos Replicados

### Roles IAM (Proyecto)
- Se copian todos los roles asignados a nivel proyecto en DEV

### Permisos BigQuery
- ✅ Acceso al dataset `settings`
- ✅ Permisos en tabla `works_index`
- ✅ Permisos en tabla `works_categories`
- ✅ Role: BigQuery Data Viewer

## 🔧 Configuración

Los scripts usan la siguiente configuración:

```python
ENVIRONMENTS = {
    'dev': {
        'project_id': 'platform-partners-des',
        'service_account': 'streamlit-bigquery-sa@platform-partners-des.iam.gserviceaccount.com'
    },
    'qua': {
        'project_id': 'platform-partners-qua',
        'service_account': 'streamlit-bigquery-sa@platform-partners-qua.iam.gserviceaccount.com'
    },
    'pro': {
        'project_id': 'platform-partners-pro',
        'service_account': 'streamlit-bigquery-sa@platform-partners-pro.iam.gserviceaccount.com'
    }
}

DATASET_ID = 'settings'
TABLES = ['works_index', 'works_categories']
```

## 🔑 Prerequisitos

1. **gcloud CLI** instalado y configurado
2. **bq CLI** (incluido con gcloud)
3. **Permisos** para crear service accounts y otorgar roles en QUA y PRO:
   - `iam.serviceAccounts.create`
   - `iam.serviceAccounts.setIamPolicy`
   - `resourcemanager.projects.setIamPolicy`
   - `bigquery.datasets.update`

4. **Autenticación**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

## ⚠️ Notas Importantes

- Los scripts verifican si las service accounts ya existen antes de crearlas
- Si una service account ya existe, solo actualizan los permisos
- Los permisos existentes no se eliminan, solo se agregan nuevos
- El script pide confirmación antes de hacer cambios

## 🐛 Troubleshooting

### Error: "Permission denied"
```bash
# Verifica que tienes los permisos necesarios
gcloud projects get-iam-policy platform-partners-qua
gcloud projects get-iam-policy platform-partners-pro
```

### Error: "Service account already exists"
Es normal. El script detecta esto y solo actualiza permisos.

### Error: "Dataset not found"
Verifica que las tablas `works_index` y `works_categories` existan en QUA y PRO:
```bash
bq ls platform-partners-qua:settings
bq ls platform-partners-pro:settings
```

## 📝 Después de Ejecutar

Después de ejecutar `setup_service_accounts.py`:

1. ✅ Verifica que las service accounts fueron creadas
2. ✅ Haz un deploy en cada ambiente:
   ```bash
   ./build_deploy.sh qua
   ./build_deploy.sh pro
   ```
3. ✅ Prueba que la app funciona en cada ambiente

## 🔄 Actualizar Permisos

Si necesitas agregar nuevos permisos después:

1. Agrégalos manualmente a DEV
2. Ejecuta `python setup_service_accounts.py` nuevamente
3. Los nuevos permisos se replicarán a QUA y PRO

## 💡 Comandos Útiles

```bash
# Ver todos los roles de una service account
gcloud projects get-iam-policy platform-partners-des \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:streamlit-bigquery-sa@platform-partners-des.iam.gserviceaccount.com"

# Ver permisos del dataset
bq show --format=prettyjson platform-partners-des:settings

# Ver permisos de una tabla
bq show --format=prettyjson platform-partners-des:settings.works_categories
```


