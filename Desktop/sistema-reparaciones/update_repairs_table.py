# update_repairs_table.py
"""
Script para agregar los nuevos campos de seguros a la tabla de reparaciones.
"""

import os
from app import create_app, db

def update_repairs_table():
    """Agregar nuevos campos a la tabla repairs."""
    
    # Determinar el entorno
    config_name = 'production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'development'
    
    # Crear la aplicación
    app = create_app(config_name)
    
    with app.app_context():
        print("🔧 Actualizando tabla de reparaciones...")
        
        try:
            # Usar SQL directo para agregar las columnas
            with db.engine.connect() as conn:
                # Verificar si las columnas ya existen
                inspector = db.inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('repair')]
                
                new_columns = [
                    ('insurance_company', 'VARCHAR(100)'),
                    ('insured_company', 'VARCHAR(100)'),
                    ('claim_number', 'VARCHAR(50)'),
                    ('incident_date', 'DATE')
                ]
                
                for col_name, col_type in new_columns:
                    if col_name not in columns:
                        sql = f"ALTER TABLE repair ADD COLUMN {col_name} {col_type}"
                        conn.execute(db.text(sql))
                        print(f"✅ Columna '{col_name}' agregada")
                    else:
                        print(f"⚠️ Columna '{col_name}' ya existe")
                
                conn.commit()
            
            print("✅ Tabla de reparaciones actualizada correctamente")
            
        except Exception as e:
            print(f"❌ Error actualizando tabla: {e}")
            raise

if __name__ == '__main__':
    update_repairs_table()