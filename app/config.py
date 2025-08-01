# create_db.py - Mejorado para Railway

import os
import sys
from app import create_app, db
from app.models import User, Repair, TechnicalReport

def create_database():
    """Crear base de datos y tablas."""
    
    # Determinar entorno (más robusto)
    is_railway = (
        os.environ.get('RAILWAY_ENVIRONMENT') or 
        os.environ.get('RAILWAY_PROJECT_ID') or
        os.environ.get('RAILWAY_SERVICE_ID') or
        'railway.app' in os.environ.get('DATABASE_URL', '')
    )
    config_name = 'production' if is_railway else 'development'
    
    print(f"🌍 Entorno detectado: {'Railway (Producción)' if is_railway else 'Desarrollo'}")
    
    try:
        # Crear aplicación
        app = create_app(config_name)
        
        with app.app_context():
            # Verificar conexión a la base de datos
            print("🔍 Verificando conexión a la base de datos...")
            
            # Intentar conectar
            try:
                db.engine.connect()
                print("✅ Conexión a la base de datos exitosa")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
                print("\n🔧 SOLUCIONES:")
                print("1. Verificar que tengas PostgreSQL en Railway")
                print("2. Verificar variable DATABASE_URL")
                print("3. URL debe ser: postgresql://user:pass@host:port/db")
                return False
            
            # Crear todas las tablas
            print("🔧 Creando tablas...")
            db.create_all()
            print("✅ Tablas creadas exitosamente")
            
            # Verificar tablas creadas
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Tablas en la base de datos: {tables}")
            
            # Crear usuario administrador solo si no existe
            admin_exists = User.query.filter_by(username='admin').first()
            
            if not admin_exists:
                # Credenciales del admin
                if is_railway:
                    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
                    admin_password = os.environ.get('ADMIN_PASSWORD', 'artec2024!')
                else:
                    admin_username = 'admin'
                    admin_password = 'admin123'
                
                admin_user = User(
                    username=admin_username,
                    is_admin=True
                )
                admin_user.set_password(admin_password)
                
                db.session.add(admin_user)
                db.session.commit()
                
                print(f"✅ Usuario administrador '{admin_username}' creado")
                
                if not is_railway:
                    print(f"   👤 Usuario: {admin_username}")
                    print(f"   🔑 Contraseña: {admin_password}")
                else:
                    print("   🔐 Credenciales configuradas desde variables de entorno")
            else:
                print("ℹ️ Usuario administrador ya existe")
            
            # Verificar estructura de la tabla repairs
            if 'repair' in tables:
                columns = [col['name'] for col in inspector.get_columns('repair')]
                required_columns = ['insurance_company', 'insured_company', 'claim_number', 'incident_date']
                
                missing_columns = [col for col in required_columns if col not in columns]
                if missing_columns:
                    print(f"⚠️ Columnas faltantes en 'repair': {missing_columns}")
                    print("🔧 Ejecuta update_repairs_table.py para agregar las columnas")
                else:
                    print("✅ Tabla 'repair' tiene todas las columnas necesarias")
            
            # Verificar tabla de informes técnicos
            if 'technical_reports' in tables:
                print("✅ Tabla 'technical_reports' existe")
            else:
                print("⚠️ Tabla 'technical_reports' no encontrada")
            
            print("\n🚀 ¡Base de datos configurada correctamente!")
            print(f"🌐 Puedes acceder en: https://tu-app.railway.app")
            
            return True
            
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)