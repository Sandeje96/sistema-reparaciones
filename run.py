# run.py
"""
Punto de entrada principal para Taller Mecánico Don Orlando.
"""

import os
import sys
from dotenv import load_dotenv

# Asegurar codificación UTF-8 si está disponible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

from app import create_app, db

# Determinar configuración según entorno
config_name = 'production' if os.environ.get('RAILWAY_ENVIRONMENT') else os.environ.get('FLASK_CONFIG', 'default')
app = create_app(config_name)

# Asegurar tablas, migraciones ligeras y usuario inicial al arrancar el contenedor
with app.app_context():
    try:
        from app.models import User
        db.create_all()
        
        # Verificar si falta la columna item_type en repair_items (migración automática)
        inspector = db.inspect(db.engine)
        if 'repair_items' in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns('repair_items')]
            if 'item_type' not in cols:
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE repair_items ADD COLUMN item_type VARCHAR(20) NOT NULL DEFAULT 'mano_obra'"))
                    conn.commit()
                    print("[OK] Columna 'item_type' agregada a 'repair_items'.")

        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin = User.query.filter_by(username=admin_username).first()
        if not admin:
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin_user = User(
                username=admin_username,
                is_admin=True,
                is_active=True
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"[OK] Usuario administrador '{admin_username}' creado.")
        else:
            print(f"[INFO] Usuario '{admin_username}' verificado y listo.")
    except Exception as e:
        print(f"[WARN] Inicialización automática de DB: {e}")

# Comandos CLI
@app.cli.command()
def init_db():
    """Inicializar la base de datos."""
    with app.app_context():
        db.create_all()
        print("[OK] Base de datos inicializada.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
