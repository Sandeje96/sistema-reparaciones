# check_database.py
import os
from app import create_app, db

def check_database():
    config_name = 'production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'development'
    app = create_app(config_name)
    
    with app.app_context():
        print("🔍 Verificando estructura de la base de datos...")
        
        # Inspeccionar la tabla repairs
        inspector = db.inspect(db.engine)
        
        if 'repair' in inspector.get_table_names():
            columns = inspector.get_columns('repair')
            print("📋 Columnas en la tabla 'repair':")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # Verificar si las nuevas columnas existen
            column_names = [col['name'] for col in columns]
            new_columns = ['insurance_company', 'insured_company', 'claim_number', 'incident_date']
            
            print("\n🔍 Verificando nuevas columnas:")
            for col in new_columns:
                if col in column_names:
                    print(f"  ✅ {col}: EXISTE")
                else:
                    print(f"  ❌ {col}: NO EXISTE")
        else:
            print("❌ Tabla 'repair' no encontrada")

if __name__ == '__main__':
    check_database()