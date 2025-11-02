#!/usr/bin/env python3
"""
Script para replicar la service account de DEV a QUA y PRO
con todos los permisos necesarios para data_science_index
"""

import subprocess
import json
import sys

# Configuración de proyectos y ambientes
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

def run_command(cmd, check=True):
    """Ejecutar comando y retornar output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def describe_service_account(project_id, sa_email):
    """Obtener información de la service account"""
    print(f"\n📋 Describiendo service account en {project_id}...")
    
    cmd = f"gcloud iam service-accounts describe {sa_email} --project={project_id} --format=json"
    stdout, stderr, returncode = run_command(cmd, check=False)
    
    if returncode == 0:
        sa_info = json.loads(stdout)
        print(f"✅ Service Account encontrada:")
        print(f"   Email: {sa_info.get('email')}")
        print(f"   Display Name: {sa_info.get('displayName')}")
        print(f"   Description: {sa_info.get('description', 'N/A')}")
        return sa_info
    else:
        print(f"❌ Service Account no encontrada")
        print(f"   Error: {stderr}")
        return None

def get_project_iam_policy(project_id, sa_email):
    """Obtener roles IAM de la service account a nivel proyecto"""
    print(f"\n🔍 Obteniendo roles IAM del proyecto {project_id}...")
    
    cmd = f"gcloud projects get-iam-policy {project_id} --format=json"
    stdout, stderr, returncode = run_command(cmd)
    
    if returncode != 0:
        print(f"❌ Error obteniendo IAM policy: {stderr}")
        return []
    
    policy = json.loads(stdout)
    sa_roles = []
    
    for binding in policy.get('bindings', []):
        members = binding.get('members', [])
        for member in members:
            if sa_email in member:
                sa_roles.append(binding['role'])
    
    print(f"✅ Roles encontrados ({len(sa_roles)}):")
    for role in sa_roles:
        print(f"   - {role}")
    
    return sa_roles

def get_bigquery_dataset_permissions(project_id, dataset_id, sa_email):
    """Obtener permisos del dataset BigQuery"""
    print(f"\n🔍 Obteniendo permisos del dataset {project_id}:{dataset_id}...")
    
    cmd = f"bq show --format=prettyjson {project_id}:{dataset_id}"
    stdout, stderr, returncode = run_command(cmd, check=False)
    
    if returncode != 0:
        print(f"❌ Error obteniendo dataset: {stderr}")
        return []
    
    dataset_info = json.loads(stdout)
    access_entries = dataset_info.get('access', [])
    
    sa_permissions = []
    for entry in access_entries:
        if 'userByEmail' in entry and sa_email in entry['userByEmail']:
            sa_permissions.append(entry.get('role'))
    
    print(f"✅ Permisos en dataset encontrados ({len(sa_permissions)}):")
    for perm in sa_permissions:
        print(f"   - {perm}")
    
    return sa_permissions

def create_service_account(project_id, sa_name, display_name, description=""):
    """Crear service account"""
    print(f"\n🆕 Creando service account en {project_id}...")
    
    # Verificar si ya existe
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
    cmd = f"gcloud iam service-accounts describe {sa_email} --project={project_id}"
    _, _, returncode = run_command(cmd, check=False)
    
    if returncode == 0:
        print(f"⚠️  Service Account ya existe: {sa_email}")
        return True
    
    # Crear nueva service account
    cmd = f'gcloud iam service-accounts create {sa_name} \
        --display-name="{display_name}" \
        --description="{description}" \
        --project={project_id}'
    
    stdout, stderr, returncode = run_command(cmd, check=False)
    
    if returncode == 0:
        print(f"✅ Service Account creada: {sa_email}")
        return True
    else:
        print(f"❌ Error creando service account: {stderr}")
        return False

def grant_project_roles(project_id, sa_email, roles):
    """Otorgar roles a nivel proyecto"""
    print(f"\n🔑 Otorgando roles de proyecto en {project_id}...")
    
    for role in roles:
        cmd = f'gcloud projects add-iam-policy-binding {project_id} \
            --member="serviceAccount:{sa_email}" \
            --role="{role}" \
            --condition=None'
        
        _, stderr, returncode = run_command(cmd, check=False)
        
        if returncode == 0:
            print(f"   ✅ {role}")
        else:
            print(f"   ❌ {role}: {stderr}")

def grant_bigquery_dataset_access(project_id, dataset_id, sa_email, role='READER'):
    """Otorgar acceso al dataset BigQuery"""
    print(f"\n📊 Otorgando acceso a dataset {project_id}:{dataset_id}...")
    
    # Usar bq update para agregar acceso
    cmd = f'bq update --dataset \
        --add_access_entry="serviceAccount:{sa_email}:role:{role}" \
        {project_id}:{dataset_id}'
    
    stdout, stderr, returncode = run_command(cmd, check=False)
    
    if returncode == 0:
        print(f"✅ Acceso otorgado al dataset")
    else:
        print(f"⚠️  Error otorgando acceso al dataset: {stderr}")

def grant_bigquery_table_permissions(project_id, dataset_id, table_id, sa_email):
    """Otorgar permisos a tabla específica BigQuery"""
    print(f"\n📋 Otorgando permisos a tabla {project_id}:{dataset_id}.{table_id}...")
    
    # BigQuery Data Viewer a nivel de tabla
    cmd = f'bq add-iam-policy-binding \
        --member="serviceAccount:{sa_email}" \
        --role="roles/bigquery.dataViewer" \
        {project_id}:{dataset_id}.{table_id}'
    
    stdout, stderr, returncode = run_command(cmd, check=False)
    
    if returncode == 0:
        print(f"✅ Permisos otorgados a tabla {table_id}")
    else:
        print(f"⚠️  Error: {stderr}")

def main():
    print("=" * 80)
    print("🚀 REPLICACIÓN DE SERVICE ACCOUNT: DEV → QUA, PRO")
    print("=" * 80)
    
    # Paso 1: Describir service account en DEV
    dev_config = ENVIRONMENTS['dev']
    dev_sa_info = describe_service_account(dev_config['project_id'], dev_config['service_account'])
    
    if not dev_sa_info:
        print("\n❌ No se pudo obtener información de DEV. Abortando.")
        sys.exit(1)
    
    # Paso 2: Obtener roles y permisos en DEV
    dev_roles = get_project_iam_policy(dev_config['project_id'], dev_config['service_account'])
    dev_dataset_perms = get_bigquery_dataset_permissions(
        dev_config['project_id'], 
        DATASET_ID, 
        dev_config['service_account']
    )
    
    print("\n" + "=" * 80)
    print("📋 RESUMEN DE CONFIGURACIÓN EN DEV:")
    print("=" * 80)
    print(f"Service Account: {dev_config['service_account']}")
    print(f"Display Name: {dev_sa_info.get('displayName')}")
    print(f"Roles IAM ({len(dev_roles)}):")
    for role in dev_roles:
        print(f"  - {role}")
    print(f"Permisos BigQuery Dataset ({len(dev_dataset_perms)}):")
    for perm in dev_dataset_perms:
        print(f"  - {perm}")
    
    # Confirmar antes de continuar
    print("\n" + "=" * 80)
    response = input("¿Deseas replicar esta configuración a QUA y PRO? (s/n): ")
    if response.lower() != 's':
        print("❌ Operación cancelada.")
        sys.exit(0)
    
    # Paso 3: Replicar en QUA y PRO
    for env in ['qua', 'pro']:
        print("\n" + "=" * 80)
        print(f"🔄 REPLICANDO EN {env.upper()}")
        print("=" * 80)
        
        env_config = ENVIRONMENTS[env]
        sa_name = dev_config['service_account'].split('@')[0]  # streamlit-bigquery-sa
        
        # Crear service account
        if create_service_account(
            env_config['project_id'],
            sa_name,
            dev_sa_info.get('displayName', 'Streamlit BigQuery Service Account'),
            dev_sa_info.get('description', '')
        ):
            # Otorgar roles de proyecto
            grant_project_roles(env_config['project_id'], env_config['service_account'], dev_roles)
            
            # Otorgar acceso a dataset
            grant_bigquery_dataset_access(
                env_config['project_id'],
                DATASET_ID,
                env_config['service_account']
            )
            
            # Otorgar permisos a tablas específicas
            for table in TABLES:
                grant_bigquery_table_permissions(
                    env_config['project_id'],
                    DATASET_ID,
                    table,
                    env_config['service_account']
                )
    
    print("\n" + "=" * 80)
    print("🎉 ¡REPLICACIÓN COMPLETADA!")
    print("=" * 80)
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Verificar que las service accounts fueron creadas correctamente")
    print("2. Actualizar Cloud Run en cada ambiente si es necesario")
    print("\nComandos de verificación:")
    for env, config in ENVIRONMENTS.items():
        print(f"\n{env.upper()}:")
        print(f"  gcloud iam service-accounts describe {config['service_account']} --project={config['project_id']}")

if __name__ == "__main__":
    main()


