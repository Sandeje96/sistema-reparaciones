from PIL import Image, ImageDraw, ImageFont
import os

# Crear un logo básico si no existe
logo_path = 'app/static/images/logo-artec.png'

if not os.path.exists(logo_path):
    # Crear una imagen simple de 200x200
    img = Image.new('RGB', (200, 200), color='#4A90E2')
    draw = ImageDraw.Draw(img)
    
    # Agregar texto
    try:
        # Intentar usar una fuente del sistema
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        # Si no encuentra la fuente, usar la por defecto
        font = ImageFont.load_default()
    
    # Centrar el texto
    text = "ARTEC"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (200 - text_width) // 2
    y = (200 - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Guardar
    img.save(logo_path)
    print(f"✅ Logo creado en: {logo_path}")
else:
    print("✅ Logo ya existe")