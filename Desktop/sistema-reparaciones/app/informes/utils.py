# app/informes/utils.py
"""
Utilidades para generar PDFs de informes técnicos.
"""

import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
import uuid

class TechnicalReportPDF:
    """Generador de PDFs para informes técnicos con formato idéntico al original."""
    
    def __init__(self, report_data):
        self.data = report_data
        self.doc = None
        self.story = []
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configurar estilos personalizados para replicar el formato original."""
        
        # Estilo para el título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#4A90E2'),  # Azul similar al original
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para encabezados de sección (Cliente, Asegurado, etc.)
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=6,
            textColor=white,
            backColor=HexColor('#4A90E2'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leftIndent=8,
            rightIndent=8,
            leading=16
        ))
        
        # Estilo para contenido de secciones
        self.styles.add(ParagraphStyle(
            name='SectionContent',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=3,
            textColor=black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leftIndent=8,
            bulletIndent=8
        ))
        
        # Estilo para el cuadro de informe
        self.styles.add(ParagraphStyle(
            name='ReportBox',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            spaceBefore=6,
            textColor=black,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leftIndent=12,
            rightIndent=12,
            leading=14
        ))
        
        # Estilo para información del técnico
        self.styles.add(ParagraphStyle(
            name='TechnicianInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=HexColor('#4A90E2'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=HexColor('#4A90E2'),
            leftIndent=8,
            rightIndent=8,
            leading=12
        ))
    
    def generate_pdf(self, output_path):
        """Generar el PDF completo."""
        
        # Configurar documento
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=15*mm,
            bottomMargin=20*mm
        )
        
        # Construir contenido
        self._build_header()
        self._build_client_info()
        self._build_device_info()
        self._build_report_section()
        self._build_technician_info()
        
        # Si hay imágenes, agregar páginas adicionales
        if self.data.get('images'):
            self._build_images_pages()
        
        # Generar PDF
        self.doc.build(self.story)
        return output_path
    
    def _build_header(self):
        """Construir encabezado con logo y título."""
        
        # Logo ARTEC (si existe)
        logo_path = os.path.join('app', 'static', 'images', 'logo-artec.png')
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=60*mm, height=60*mm)
                logo.hAlign = 'LEFT'
                self.story.append(logo)
                self.story.append(Spacer(1, 10*mm))
            except:
                pass  # Si hay error con el logo, continuar sin él
        
        # Título principal
        title = Paragraph("Soluciones Tecnológicas", self.styles['CustomTitle'])
        self.story.append(title)
        self.story.append(Spacer(1, 20*mm))
    
    def _build_client_info(self):
        """Construir sección de información del cliente."""
        
        # Cliente
        client_header = Paragraph("Cliente", self.styles['SectionHeader'])
        self.story.append(client_header)
        
        client_content = Paragraph(f"• {self.data.get('insurance_company', '')}", 
                                 self.styles['SectionContent'])
        self.story.append(client_content)
        self.story.append(Spacer(1, 6*mm))
        
        # Asegurado
        insured_header = Paragraph("Asegurado", self.styles['SectionHeader'])
        self.story.append(insured_header)
        
        insured_content = Paragraph(f"• {self.data.get('insured_company', '')}", 
                                  self.styles['SectionContent'])
        self.story.append(insured_content)
        self.story.append(Spacer(1, 6*mm))
        
        # Siniestro
        claim_header = Paragraph("Siniestro", self.styles['SectionHeader'])
        self.story.append(claim_header)
        
        claim_content = Paragraph(f"• {self.data.get('claim_number', '')}", 
                                self.styles['SectionContent'])
        self.story.append(claim_content)
        self.story.append(Spacer(1, 6*mm))
        
        # Fecha
        date_header = Paragraph("Fecha", self.styles['SectionHeader'])
        self.story.append(date_header)
        
        incident_date = self.data.get('incident_date', '')
        if hasattr(incident_date, 'strftime'):
            formatted_date = incident_date.strftime('%d/%m/%Y')
        else:
            formatted_date = str(incident_date)
        
        date_content = Paragraph(f"• {formatted_date}", self.styles['SectionContent'])
        self.story.append(date_content)
        self.story.append(Spacer(1, 15*mm))
    
    def _build_device_info(self):
        """Construir sección de información del equipo."""
        
        # Crear tabla para información del objeto
        device_data = [
            ['Objeto:', 'Marca: ' + self.data.get('brand', '')],
            [self.data.get('device_type', ''), 'Modelo: ' + self.data.get('model', '')],
            ['', 'Serie: ' + self.data.get('serial_number', '')],
            ['', 'Detalles: ' + self.data.get('problem_description', '')]
        ]
        
        device_table = Table(device_data, colWidths=[40*mm, 120*mm])
        device_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        self.story.append(device_table)
        self.story.append(Spacer(1, 15*mm))
    
    def _build_report_section(self):
        """Construir sección del informe técnico."""
        
        # Encabezado del informe
        report_header = Paragraph("Informe:", self.styles['SectionHeader'])
        self.story.append(report_header)
        self.story.append(Spacer(1, 6*mm))
        
        # Contenido del informe técnico
        technical_text = self.data.get('technical_diagnosis', '')
        
        # Dividir el texto en párrafos con bullets
        paragraphs = technical_text.split('\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                if not paragraph.strip().startswith('•'):
                    paragraph = '• ' + paragraph.strip()
                
                report_content = Paragraph(paragraph, self.styles['ReportBox'])
                self.story.append(report_content)
        
        # Precios
        diagnosis_price = self.data.get('diagnosis_price', 0)
        repair_price = self.data.get('repair_price', 0)
        
        price_text = f"• Precio de diagnóstico: ${diagnosis_price:,.0f}"
        price_para = Paragraph(price_text, self.styles['ReportBox'])
        self.story.append(price_para)
        
        if repair_price and repair_price > 0:
            repair_text = f"• Precio de reparación: ${repair_price:,.0f}"
            repair_para = Paragraph(repair_text, self.styles['ReportBox'])
            self.story.append(repair_para)
        
        self.story.append(Spacer(1, 15*mm))
    
    def _build_technician_info(self):
        """Construir información del técnico."""
        
        technician_name = self.data.get('technician_name', 'Leonardo A. Acosta')
        license_number = self.data.get('professional_license', '2200')
        
        tech_info = f"Técnico: {technician_name}    Mat. Prof: {license_number}"
        tech_para = Paragraph(tech_info, self.styles['TechnicianInfo'])
        self.story.append(tech_para)
    
    def _build_images_pages(self):
        """Construir páginas adicionales con imágenes."""
        
        images = self.data.get('images', [])
        if not images:
            return
        
        for image_info in images:
            # Nueva página para cada imagen
            self.story.append(PageBreak())
            
            image_path = os.path.join('app', 'static', image_info['path'])
            
            if os.path.exists(image_path):
                try:
                    # Redimensionar imagen si es necesario
                    max_width = 160*mm
                    max_height = 200*mm
                    
                    # Obtener dimensiones originales
                    with PILImage.open(image_path) as pil_img:
                        orig_width, orig_height = pil_img.size
                        
                        # Calcular escala manteniendo proporción
                        width_scale = max_width / (orig_width * 0.75)  # 0.75 puntos por pixel
                        height_scale = max_height / (orig_height * 0.75)
                        scale = min(width_scale, height_scale, 1.0)  # No agrandar
                        
                        final_width = orig_width * 0.75 * scale
                        final_height = orig_height * 0.75 * scale
                    
                    # Agregar imagen
                    img = Image(image_path, width=final_width, height=final_height)
                    img.hAlign = 'CENTER'
                    self.story.append(img)
                    
                except Exception as e:
                    # Si hay error con la imagen, agregar texto
                    error_para = Paragraph(f"Error cargando imagen {image_info['number']}", 
                                         self.styles['Normal'])
                    self.story.append(error_para)

def generate_report_pdf(report):
    """
    Función principal para generar PDF de informe técnico.
    
    Args:
        report: Instancia del modelo TechnicalReport
        
    Returns:
        str: Ruta del archivo PDF generado
    """
    
    # Preparar datos para el generador
    report_data = {
        'insurance_company': report.insurance_company,
        'insured_company': report.insured_company,
        'claim_number': report.claim_number,
        'incident_date': report.incident_date,
        'device_type': report.device_type,
        'brand': report.brand,
        'model': report.model,
        'serial_number': report.serial_number or '',
        'problem_description': report.problem_description,
        'technical_diagnosis': report.technical_diagnosis,
        'diagnosis_price': report.diagnosis_price,
        'repair_price': report.repair_price,
        'technician_name': report.technician_name,
        'professional_license': report.professional_license,
        'images': report.get_images()
    }
    
    # Crear directorio de salida si no existe
    output_dir = os.path.join('app', 'static', 'reports')
    os.makedirs(output_dir, exist_ok=True)
    
    # Nombre del archivo PDF
    safe_claim = "".join(c for c in report.claim_number if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"informe_{safe_claim}_{report.id}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # Generar PDF
    pdf_generator = TechnicalReportPDF(report_data)
    pdf_generator.generate_pdf(output_path)
    
    return output_path

def save_uploaded_image(file, report_uuid, image_number):
    """
    Guardar imagen subida con nombre único.
    
    Args:
        file: Archivo de imagen subido
        report_uuid: UUID del reporte
        image_number: Número de imagen (1, 2, o 3)
        
    Returns:
        str: Nombre del archivo guardado
    """
    
    if not file or not file.filename:
        return None
    
    # Crear directorio si no existe
    upload_dir = os.path.join('app', 'static', 'uploads', 'informes')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Obtener extensión del archivo
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.jpg', '.jpeg', '.png']:
        return None
    
    # Generar nombre único
    filename = f"{report_uuid}_img{image_number}{file_ext}"
    file_path = os.path.join(upload_dir, filename)
    
    try:
        # Guardar archivo
        file.save(file_path)
        
        # Optimizar imagen si es muy grande
        optimize_image(file_path, max_size=(1920, 1080), quality=85)
        
        return filename
        
    except Exception as e:
        # Si hay error, intentar eliminar archivo parcial
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return None

def optimize_image(image_path, max_size=(1920, 1080), quality=85):
    """
    Optimizar imagen redimensionando y comprimiendo.
    
    Args:
        image_path: Ruta de la imagen
        max_size: Tamaño máximo (width, height)
        quality: Calidad de compresión (1-100)
    """
    
    try:
        with PILImage.open(image_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = PILImage.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Redimensionar si es necesario
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
            
            # Guardar con compresión
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            
    except Exception as e:
        # Si hay error, no hacer nada (mantener imagen original)
        pass

def delete_report_files(report):
    """
    Eliminar archivos asociados a un reporte (imágenes y PDF).
    
    Args:
        report: Instancia del modelo TechnicalReport
    """
    
    # Eliminar imágenes
    report.delete_images()
    
    # Eliminar PDF si existe
    safe_claim = "".join(c for c in report.claim_number if c.isalnum() or c in (' ', '-', '_')).rstrip()
    pdf_filename = f"informe_{safe_claim}_{report.id}.pdf"
    pdf_path = os.path.join('app', 'static', 'reports', pdf_filename)
    
    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except OSError:
            pass  # Error silencioso si no se puede eliminar