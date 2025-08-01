# check_config.py - Verificar configuración de Railway

import os

def check_railway_config():
    """Verificar configuración para Railway."""
    
    print("🔍 VERIFICANDO CONFIGURACIÓN DE RAILWAY")
    print("=" * 50)
    
    # Variables críticas
    critical_vars = {
        'DATABASE_URL': 'URL de conexión a PostgreSQL',
        'SECRET_KEY': 'Clave secreta de Flask',
        'PORT': 'Puerto del servidor'
    }
    
    # Variables opcionales
    optional_vars = {
        'ADMIN_USERNAME': 'Usuario administrador',
        'ADMIN_PASSWORD': 'Contraseña administrador',
        'APP_NAME': 'Nombre de la aplicación',
        'COMPANY_NAME': 'Nombre de la empresa'
    }
    
    print("\n📋 VARIABLES CRÍTICAS:")
    all_critical_ok = True
    
    for var, description in critical_vars.items():
        value = os.environ.get(var)
        if value:
            # Enmascarar valores sensibles
            if 'PASSWORD' in var or 'SECRET' in var or 'DATABASE_URL' in var:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: NO CONFIGURADA - {description}")
            all_critical_ok = False
    
    print("\n📋 VARIABLES OPCIONALES:")
    for var, description in optional_vars.items():
        value = os.environ.get(var)
        if value:
            if 'PASSWORD' in var:
                display_value = "***"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ⚪ {var}: No configurada - {description}")
    
    # Verificar DATABASE_URL específicamente
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"\n🔍 ANÁLISIS DE DATABASE_URL:")
        if database_url.startswith('postgresql://'):
            print("  ✅ Protocolo correcto (postgresql://)")
        elif database_url.startswith('postgres://'):
            print("  ⚠️ Protocolo antiguo - será convertido automáticamente")
        else:
            print("  ❌ Protocolo incorrecto - debe empezar con postgresql://")
            all_critical_ok = False
        
        # Verificar estructura básica
        if '@' in database_url and ':' in database_url:
            print("  ✅ Estructura de URL válida")
        else:
            print("  ❌ Estructura de URL inválida")
            all_critical_ok = False
    
    # Verificar entorno Railway
    railway_vars = ['RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID']
    railway_detected = any(os.environ.get(var) for var in railway_vars)
    
    print(f"\n🚂 ENTORNO RAILWAY:")
    if railway_detected:
        print("  ✅ Entorno Railway detectado")
        for var in railway_vars:
            value = os.environ.get(var)
            if value:
                print(f"    • {var}: {value}")
    else:
        print("  ⚪ Entorno Railway no detectado (ejecutándose localmente)")
    
    print(f"\n📊 RESUMEN:")
    if all_critical_ok:
        print("  ✅ Todas las variables críticas están configuradas")
        print("  🚀 La aplicación debería funcionar correctamente")
    else:
        print("  ❌ Faltan variables críticas")
        print("  🔧 Configura las variables faltantes en Railway")
    
    print("\n" + "=" * 50)
    
    return all_critical_ok

if __name__ == '__main__':
    check_railway_config()