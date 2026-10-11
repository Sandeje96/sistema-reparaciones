# test_taller.py
"""
Script de verificación y pruebas automatizadas para Taller Mecánico Don Orlando.
"""

import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app, db
from app.models import User, Repair

def run_tests():
    app = create_app('development')
    app.config['WTF_CSRF_ENABLED'] = False  # Para testing rápido
    
    with app.test_client() as client:
        print("🔍 1. Probando inicio de sesión con 'admin'...")
        login_res = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        assert login_res.status_code == 200, f"Fallo login: {login_res.status_code}"
        assert b"DON ORLANDO" in login_res.data, "No se encontró Don Orlando en el navbar"
        print("   ✅ Login exitoso y branding verificado.")
        
        print("\n🔍 2. Verificando panel principal (/repairs/)...")
        panel_res = client.get('/repairs/')
        assert panel_res.status_code == 200
        assert b"AA 123 BB" in panel_res.data, "Patente Mercosur formateada no encontrada"
        assert b"ABC 123" in panel_res.data, "Patente tradicional formateada no encontrada"
        assert b"d\xc3\xadas" in panel_res.data or b"d\xc3\xada" in panel_res.data or b"hoy" in panel_res.data, "Contador de días no encontrado"
        print("   ✅ Panel principal muestra patentes formateadas y conteo de días.")
        
        print("\n🔍 3. Probando ingreso de nuevo vehículo (Formato Tradicional XXX111)...")
        add_res1 = client.post('/repairs/add', data={
            'license_plate': 'kld789',  # minúsculas para probar auto-limpieza
            'brand': 'Peugeot',
            'model': '208 Allure',
            'year': 2017,
            'color': 'Rojo',
            'mileage': 75000,
            'client_name': 'Laura Fernández',
            'client_phone': '11-6677-8899',
            'problem_description': 'Chillido agudo al frenar a baja velocidad.',
            'status': 'ingresado'
        }, follow_redirects=True)
        assert add_res1.status_code == 200
        assert b"KLD 789" in add_res1.data, "Vehículo KLD 789 no se formateó correctamente"
        print("   ✅ Vehículo con patente tradicional XXX111 ingresado con éxito.")
        
        print("\n🔍 4. Probando ingreso de nuevo vehículo (Formato Mercosur XX111XX)...")
        add_res2 = client.post('/repairs/add', data={
            'license_plate': 'ag 321 tx',  # con espacios para probar limpieza
            'brand': 'Toyota',
            'model': 'Corolla XEI',
            'year': 2023,
            'color': 'Blanco',
            'mileage': 22000,
            'client_name': 'Esteban Morales',
            'client_phone': '11-2244-6688',
            'problem_description': 'Service de 20.000 km y revisión general.',
            'status': 'ingresado'
        }, follow_redirects=True)
        assert add_res2.status_code == 200
        assert b"AG 321 TX" in add_res2.data, "Vehículo AG 321 TX no se formateó correctamente"
        print("   ✅ Vehículo con patente Mercosur XX111XX ingresado con éxito.")
        
        print("\n🔍 5. Probando validación de patente inválida (debe rechazar)...")
        invalid_res = client.post('/repairs/add', data={
            'license_plate': '123456',  # Formato no válido
            'brand': 'Fiat',
            'model': 'Palio',
            'client_name': 'Test Inválido',
            'problem_description': 'Falla de prueba para validar error de patente',
            'status': 'ingresado'
        }, follow_redirects=True)
        assert b"Formato de patente no v\xc3\xa1lido" in invalid_res.data, "La validación no rechazó la patente inválida"
        print("   ✅ Validación de patente correcta (rechazó formato erróneo).")
        
        print("\n🔍 6. Probando carga de Diagnóstico y Plan de Trabajo...")
        # Obtener vehículo creado
        v = Repair.query.filter_by(license_plate='KLD789').first()
        assert v is not None
        diag_res = client.post(f'/repairs/{v.id}/diagnosis', data={
            'diagnosis': 'Pastillas de freno delanteras al 10% de vida útil y discos levemente rayados.',
            'work_to_do': 'Reemplazo de pastillas delanteras, rectificado de discos de freno y purga de líquido de frenos.',
            'parts_needed': '1x Juego de pastillas Fras-le, 1L Líquido DOT 4.',
            'estimated_cost': 95000.0,
            'status': 'diagnosticado'
        }, follow_redirects=True)
        assert diag_res.status_code == 200
        assert b"Pastillas de freno" in diag_res.data
        assert b"rectificado de discos" in diag_res.data
        print("   ✅ Diagnóstico y trabajo a realizar guardados y visualizados correctamente.")
        
        print("\n🔍 7. Probando cambio rápido de estado a 'En reparación'...")
        status_res = client.get(f'/repairs/{v.id}/status/en_reparacion', follow_redirects=True)
        assert status_res.status_code == 200
        v_updated = Repair.query.get(v.id)
        assert v_updated.status == 'en_reparacion'
        print(f"   ✅ Estado actualizado a: {v_updated.get_status_display()}")
        
        print("\n🔍 8. Verificando dashboard con estadísticas...")
        dash_res = client.get('/dashboard')
        assert dash_res.status_code == 200
        assert b"Tablero de Control del Taller" in dash_res.data
        print("   ✅ Dashboard de estadísticas funciona correctamente.")
        
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE! 🎉")

if __name__ == '__main__':
    run_tests()
