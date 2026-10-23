# init_taller_db.py
"""
Script de inicialización de la base de datos para Taller Mecánico Don Orlando.
Crea las tablas, el usuario administrador y datos de prueba representativos.
"""

import os
import sys

# Asegurar codificación UTF-8 para consola de Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Repair, RepairItem

def init_database():
    app = create_app('development')
    
    with app.app_context():
        print("🔧 Creando tablas de la base de datos...")
        db.create_all()
        
        # Verificar si falta la columna item_type en repair_items
        inspector = db.inspect(db.engine)
        if 'repair_items' in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns('repair_items')]
            if 'item_type' not in cols:
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE repair_items ADD COLUMN item_type VARCHAR(20) NOT NULL DEFAULT 'mano_obra'"))
                    conn.commit()
                    print("✅ Columna 'item_type' agregada a 'repair_items'.")

        print("✅ Tablas creadas correctamente.")
        
        # 1. Crear usuario administrador
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                is_admin=True,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("👤 Usuario 'admin' creado con contraseña 'admin123'")
        else:
            print("👤 Usuario 'admin' ya existe.")
            
        # 2. Cargar vehículos de ejemplo para verificar patentes XXX111 y XX111XX y conteo de días
        if Repair.query.count() == 0:
            print("🚗 Insertando vehículos de muestra...")
            now = datetime.utcnow()
            
            # Vehículo 1: Formato XX111XX (Mercosur), 5 días en taller, en reparación
            v1 = Repair(
                license_plate='AA123BB',
                brand='Ford',
                model='Ranger 3.2 TDCi',
                year=2020,
                color='Gris Plata',
                mileage=85400,
                client_name='Carlos Benítez',
                client_phone='11-4567-8901',
                client_email='carlos.benitez@ejemplo.com',
                problem_description='Pérdida de fuerza en subidas y silbido agudo en el motor al acelerar.',
                diagnosis='Manguera del intercooler fisurada y válvula EGR con carbonización severa.',
                work_to_do='Reemplazo de manguera de turbo/intercooler, limpieza por ultrasonido de EGR y prueba de banco.',
                parts_needed='1x Manguera intercooler original Ford, 1x Junta EGR.',
                status=Repair.STATUS_EN_REPARACION,
                estimated_cost=185000.0,
                entry_date=now - timedelta(days=5),
                diagnosis_date=now - timedelta(days=4),
                created_by=admin.id
            )
            
            # Vehículo 2: Formato XXX111 (Tradicional), ingresó hoy, sin diagnóstico
            v2 = Repair(
                license_plate='ABC123',
                brand='Volkswagen',
                model='Gol Trend 1.6',
                year=2014,
                color='Blanco',
                mileage=142000,
                client_name='Mariana Gómez',
                client_phone='11-9876-5432',
                problem_description='Pedal de embrague muy duro y crujido metálico al colocar primera o marcha atrás.',
                status=Repair.STATUS_INGRESADO,
                entry_date=now,
                created_by=admin.id
            )
            
            # Vehículo 3: Formato XX111XX, 9 días en taller (Demorado +7 días), esperando repuestos
            v3 = Repair(
                license_plate='AF456CD',
                brand='Chevrolet',
                model='Cruze 1.4T',
                year=2021,
                color='Azul Oscuro',
                mileage=48000,
                client_name='Martín Rossi',
                client_phone='11-3322-1100',
                problem_description='Testigo Check Engine encendido y temperatura de agua sube rápidamente en tráfico.',
                diagnosis='Falla en el termostato electrónico (trabado cerrado) y cuerpo de agua con fuga.',
                work_to_do='Cambio de carcasa completa con termostato, purga de circuito y nuevo refrigerante.',
                parts_needed='Carcasa de termostato GM original (en pedido a fábrica), refrigerante Dexcool.',
                status=Repair.STATUS_ESPERANDO_REPUESTOS,
                estimated_cost=240000.0,
                entry_date=now - timedelta(days=9),
                diagnosis_date=now - timedelta(days=8),
                created_by=admin.id
            )
            
            db.session.add_all([v1, v2, v3])
            db.session.flush()
            
            items_v1 = [
                RepairItem(repair_id=v1.id, item_type=RepairItem.TYPE_REPUESTO, description='Manguera de intercooler original Ford', price=85000.0, order_index=1),
                RepairItem(repair_id=v1.id, item_type=RepairItem.TYPE_MANO_OBRA, description='Limpieza de válvula EGR por ultrasonido y junta nueva', price=55000.0, order_index=2),
                RepairItem(repair_id=v1.id, item_type=RepairItem.TYPE_MANO_OBRA, description='Mano de obra de reemplazo y escaneo computarizado', price=45000.0, order_index=3),
            ]
            db.session.add_all(items_v1)
            db.session.commit()
            print("✅ 3 vehículos de prueba registrados con éxito.")
            print("   - [AA 123 BB] Ford Ranger (5 días - En reparación)")
            print("   - [ABC 123]   VW Gol Trend (Ingresó hoy - Pendiente diagnóstico)")
            print("   - [AF 456 CD] Chevrolet Cruze (9 días - Demorado, esperando repuestos)")
            
        print("\n🚀 Base de datos inicializada correctamente.")

if __name__ == '__main__':
    init_database()
