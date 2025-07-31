import os

# Carpetas necesarias
folders = [
    'app/static/uploads/informes',
    'app/static/reports',
    'app/static/images'
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"Carpeta creada: {folder}")
    
    # Crear archivo .gitkeep para que Git mantenga las carpetas
    gitkeep_path = os.path.join(folder, '.gitkeep')
    with open(gitkeep_path, 'w') as f:
        f.write('')
    print(f"Archivo .gitkeep creado en: {folder}")

print("✅ Todas las carpetas creadas correctamente")