# run.py
"""
Punto de entrada principal para el Sistema de Gestión de Reparaciones.

Este archivo es responsable de:
- Cargar las variables de entorno
- Crear la instancia de la aplicación Flask
- Ejecutar la aplicación en modo desarrollo
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

from app import create_app

# Crear la instancia de la aplicación Flask
app = create_app()

# Comandos CLI personalizados
@app.cli.command()
def init_db():
    """Inicializar la base de datos con tablas vacías."""
    from app import db
    
    print("🔧 Creando tablas de la base de datos...")
    db.create_all()
    print("✅ Base de datos inicializada correctamente.")

@app.cli.command()
def create_admin():
    """Crear un usuario administrador."""
    from app import db
    from app.models import User
    from werkzeug.security import generate_password_hash
    import getpass
    
    print("👤 Creando usuario administrador...")
    
    username = input("Nombre de usuario: ").strip()
    if not username:
        print("❌ El nombre de usuario es obligatorio.")
        return
    
    if User.query.filter_by(username=username).first():
        print(f"❌ El usuario '{username}' ya existe.")
        return
    
    password = getpass.getpass("Contraseña: ")
    if len(password) < 6:
        print("❌ La contraseña debe tener al menos 6 caracteres.")
        return
    
    try:
        admin_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"✅ Usuario administrador '{username}' creado correctamente.")
        
    except Exception as e:
        print(f"❌ Error creando usuario: {e}")
        db.session.rollback()

if __name__ == '__main__':
    app.run(debug=True)