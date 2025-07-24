# create_db.py - Crear este archivo en la raíz del proyecto

from app import create_app, db
from app.models import User, Repair

# Crear la aplicación
app = create_app()

# Crear las tablas dentro del contexto de la aplicación
with app.app_context():
    print("🔧 Creando todas las tablas...")
    db.create_all()
    print("✅ Tablas creadas exitosamente")
    
    # Crear usuario administrador
    admin_exists = User.query.filter_by(username='admin').first()
    if not admin_exists:
        admin_user = User(
            username='admin',
            is_admin=True
        )
        admin_user.set_password('admin123')  # Cambia esta contraseña
        
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Usuario administrador creado:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
    else:
        print("⚠️ El usuario admin ya existe")
        
    print("🚀 Base de datos lista para usar")