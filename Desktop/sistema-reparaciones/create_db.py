# create_db.py - Crear este archivo en la raíz del proyecto

import os
from app import create_app, db
from app.models import User, Repair

# Determinar el entorno
config_name = 'production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'development'

# Crear la aplicación con la configuración apropiada
app = create_app(config_name)

# Crear las tablas dentro del contexto de la aplicación
with app.app_context():
    print("🔧 Creando todas las tablas...")
    
    try:
        db.create_all()
        print("✅ Tablas creadas exitosamente")
        
        # Crear usuario administrador solo si no existe
        admin_exists = User.query.filter_by(username='admin').first()
        if not admin_exists:
            # En producción, usar variables de entorno para credenciales
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            admin_user = User(
                username=admin_username,
                is_admin=True
            )
            admin_user.set_password(admin_password)
            
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Usuario administrador '{admin_username}' creado")
            
            if not os.environ.get('RAILWAY_ENVIRONMENT'):
                print(f"   Usuario: {admin_username}")
                print(f"   Contraseña: {admin_password}")
        else:
            print("⚠️ El usuario admin ya existe")
            
        print("🚀 Base de datos lista para usar")
        
    except Exception as e:
        print(f"❌ Error configurando base de datos: {e}")
        raise