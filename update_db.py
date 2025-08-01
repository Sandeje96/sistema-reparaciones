# update_db.py
"""
Script para actualizar la base de datos con las nuevas tablas de informes técnicos.
"""

import os
from app import create_app, db
from app.models import User, Repair, TechnicalReport

def update_database():
    """Actualizar base de datos con nuevas tablas."""
    
    # Determinar el entorno
    config_name = 'production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'development'
    
    # Crear la aplicación con la configuración apropiada
    app = create_app(config_name)
    
    # Actualizar las tablas dentro del contexto de la aplicación
    with app.app_context():
        print("🔧 Actualizando base de datos...")
        
        try:
            # Crear todas las tablas (las existentes no se modificarán)
            db.create_all()
            print("✅ Tablas actualizadas exitosamente")
            
            # Verificar que la nueva tabla existe
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'technical_reports' in tables:
                print("✅ Tabla 'technical_reports' creada correctamente")
            else:
                print("⚠️ La tabla 'technical_reports' no se encontró")
            
            # Verificar otras tablas
            expected_tables = ['user', 'repair', 'technical_reports']
            for table in expected_tables:
                if table in tables:
                    print(f"✅ Tabla '{table}' encontrada")
                else:
                    print(f"❌ Tabla '{table}' NO encontrada")
            
            print("🚀 Base de datos actualizada y lista para usar")
            
        except Exception as e:
            print(f"❌ Error actualizando base de datos: {e}")
            raise

if __name__ == '__main__':
    update_database()