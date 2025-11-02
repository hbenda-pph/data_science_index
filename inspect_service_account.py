#!/usr/bin/env python3
"""
Script para inspeccionar la configuración actual de la service account en DEV
Sin hacer ningún cambio - solo lectura
"""

import subprocess
import json

PROJECT_ID = 'platform-partners-des'
SA_EMAIL = 'streamlit-bigquery-sa@platform-partners-des.iam.gserviceaccount.com'
DATASET_ID = 'settings'

def run_command(cmd):
    """Ejecutar comando y retornar output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

def main():
    print("=" * 80)
    print(f"🔍 INSPECCIÓN DE SERVICE ACCOUNT EN {PROJECT_ID}")
    print("=" * 80)
    
    # 1. Información básica de la service account
    print(f"\n1️⃣ INFORMACIÓN BÁSICA")
    print("-" * 80)
    cmd = f"gcloud iam service-accounts describe {SA_EMAIL} --project={PROJECT_ID} --format=json"
    stdout, returncode = run_command(cmd)
    
    if returncode == 0:
        sa_info = json.loads(stdout)
        print(f"✅ Email: {sa_info.get('email')}")
        print(f"✅ Display Name: {sa_info.get('displayName')}")
        print(f"✅ Description: {sa_info.get('description', 'N/A')}")
        print(f"✅ Unique ID: {sa_info.get('uniqueId')}")
    else:
        print("❌ Service Account no encontrada")
        return
    
    # 2. Roles IAM a nivel proyecto
    print(f"\n2️⃣ ROLES IAM A NIVEL PROYECTO")
    print("-" * 80)
    cmd = f"gcloud projects get-iam-policy {PROJECT_ID} --format=json"
    stdout, returncode = run_command(cmd)
    
    if returncode == 0:
        policy = json.loads(stdout)
        sa_roles = []
        
        for binding in policy.get('bindings', []):
            members = binding.get('members', [])
            for member in members:
                if SA_EMAIL in member:
                    sa_roles.append(binding['role'])
        
        if sa_roles:
            print(f"✅ Roles encontrados ({len(sa_roles)}):")
            for role in sa_roles:
                print(f"   • {role}")
        else:
            print("⚠️  No se encontraron roles a nivel proyecto")
    
    # 3. Permisos en dataset BigQuery
    print(f"\n3️⃣ PERMISOS EN DATASET BIGQUERY: {DATASET_ID}")
    print("-" * 80)
    cmd = f"bq show --format=prettyjson {PROJECT_ID}:{DATASET_ID}"
    stdout, returncode = run_command(cmd)
    
    if returncode == 0:
        dataset_info = json.loads(stdout)
        access_entries = dataset_info.get('access', [])
        
        sa_permissions = []
        for entry in access_entries:
            if 'userByEmail' in entry and SA_EMAIL in entry['userByEmail']:
                sa_permissions.append({
                    'role': entry.get('role'),
                    'email': entry.get('userByEmail')
                })
        
        if sa_permissions:
            print(f"✅ Permisos encontrados ({len(sa_permissions)}):")
            for perm in sa_permissions:
                print(f"   • Role: {perm['role']}")
        else:
            print("⚠️  No se encontraron permisos directos en el dataset")
    else:
        print(f"❌ Error obteniendo dataset: {returncode}")
    
    # 4. Permisos específicos en tablas
    print(f"\n4️⃣ PERMISOS EN TABLAS ESPECÍFICAS")
    print("-" * 80)
    
    tables = ['works_index', 'works_categories']
    for table in tables:
        print(f"\n   Tabla: {table}")
        cmd = f"bq show --format=prettyjson {PROJECT_ID}:{DATASET_ID}.{table}"
        stdout, returncode = run_command(cmd)
        
        if returncode == 0:
            try:
                table_info = json.loads(stdout)
                # Las tablas heredan permisos del dataset normalmente
                print(f"   ✅ Tabla existe (permisos heredados del dataset)")
            except:
                print(f"   ⚠️  Error parseando información de tabla")
        else:
            print(f"   ❌ Tabla no encontrada o sin acceso")
    
    # 5. Comandos de replicación sugeridos
    print(f"\n5️⃣ COMANDOS PARA REPLICAR EN QUA Y PRO")
    print("-" * 80)
    
    print("\n📋 Para QUA:")
    print(f"""
# Crear service account
gcloud iam service-accounts create streamlit-bigquery-sa \\
    --display-name="Streamlit BigQuery Service Account" \\
    --project=platform-partners-qua

# Otorgar roles (ajusta según los roles encontrados arriba)
gcloud projects add-iam-policy-binding platform-partners-qua \\
    --member="serviceAccount:streamlit-bigquery-sa@platform-partners-qua.iam.gserviceaccount.com" \\
    --role="roles/bigquery.dataViewer"

# Otorgar acceso al dataset
bq update --dataset \\
    --add_access_entry="serviceAccount:streamlit-bigquery-sa@platform-partners-qua.iam.gserviceaccount.com:role:READER" \\
    platform-partners-qua:settings
""")
    
    print("\n📋 Para PRO:")
    print(f"""
# Crear service account
gcloud iam service-accounts create streamlit-bigquery-sa \\
    --display-name="Streamlit BigQuery Service Account" \\
    --project=platform-partners-pro

# Otorgar roles (ajusta según los roles encontrados arriba)
gcloud projects add-iam-policy-binding platform-partners-pro \\
    --member="serviceAccount:streamlit-bigquery-sa@platform-partners-pro.iam.gserviceaccount.com" \\
    --role="roles/bigquery.dataViewer"

# Otorgar acceso al dataset
bq update --dataset \\
    --add_access_entry="serviceAccount:streamlit-bigquery-sa@platform-partners-pro.iam.gserviceaccount.com:role:READER" \\
    platform-partners-pro:settings
""")
    
    print("\n" + "=" * 80)
    print("✅ Inspección completada")
    print("=" * 80)
    print("\n💡 TIP: Ejecuta 'python setup_service_accounts.py' para replicar automáticamente")

if __name__ == "__main__":
    main()


