# create_db.py - Inicialización y migración para Railway / Producción y Desarrollo

import os
import sys

# Asegurar codificación UTF-8 para evitar errores de consola
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Repair, TechnicalReport

def create_database():
    """Crear base de datos y tablas para Taller Mecánico Don Orlando."""
    
    is_railway = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID')
    config_name = 'production' if is_railway else 'development'
    
    print(f"🌍 Entorno detectado: {'Railway (Producción)' if is_railway else 'Desarrollo'}")
    
    try:
        app = create_app(config_name)
        
        with app.app_context():
            print("🔍 Verificando conexión a la base de datos...")
            
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
            
            print("🔧 Creando tablas...")
            db.create_all()
            print("✅ Tablas creadas exitosamente")
            
            # Verificar tablas creadas
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Tablas en la base de datos: {tables}")
            
            # Crear usuario administrador si no existe
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_exists = User.query.filter_by(username=admin_username).first()
            
            if not admin_exists:
                if is_railway:
                    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
                else:
                    admin_password = 'admin123'
                
                admin_user = User(
                    username=admin_username,
                    is_admin=True,
                    is_active=True
                )
                admin_user.set_password(admin_password)
                
                db.session.add(admin_user)
                db.session.commit()
                print(f"✅ Usuario administrador '{admin_username}' creado")
            else:
                print(f"ℹ️ Usuario administrador '{admin_username}' ya existe")
            
            # Si la tabla repairs está vacía, agregar vehículos de prueba
            if 'repairs' in tables and Repair.query.count() == 0:
                print("🚗 Agregando vehículos iniciales de muestra...")
                admin = User.query.filter_by(username=admin_username).first()
                now = datetime.utcnow()
                
                v1 = Repair(
                    license_plate='AA123BB',
                    brand='Ford',
                    model='Ranger 3.2 TDCi',
                    year=2020,
                    color='Gris Plata',
                    mileage=85400,
                    client_name='Carlos Benítez',
                    client_phone='11-4567-8901',
                    problem_description='Pérdida de fuerza en subidas y silbido en el motor.',
                    diagnosis='Manguera de intercooler fisurada y válvula EGR carbonizada.',
                    work_to_do='Reemplazo de manguera de turbo/intercooler y limpieza de EGR.',
                    status=Repair.STATUS_EN_REPARACION,
                    estimated_cost=185000.0,
                    entry_date=now - timedelta(days=5),
                    diagnosis_date=now - timedelta(days=4),
                    created_by=admin.id
                )
                
                v2 = Repair(
                    license_plate='ABC123',
                    brand='Volkswagen',
                    model='Gol Trend 1.6',
                    year=2014,
                    color='Blanco',
                    mileage=142000,
                    client_name='Mariana Gómez',
                    client_phone='11-9876-5432',
                    problem_description='Pedal de embrague muy duro y crujido metálico al colocar primera.',
                    status=Repair.STATUS_INGRESADO,
                    entry_date=now,
                    created_by=admin.id
                )
                
                db.session.add_all([v1, v2])
                db.session.commit()
                print("✅ Vehículos de muestra registrados correctamente.")
            
            print("\n🚀 ¡Base de datos de Taller Mecánico Don Orlando configurada correctamente!")
            return True
            
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)