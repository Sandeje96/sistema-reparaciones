# app/informes/forms.py
"""
Formularios para gestión de informes técnicos.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, FloatField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import date

class TechnicalReportForm(FlaskForm):
    """Formulario para crear/editar informes técnicos."""
    
    # Información del seguro
    insurance_company = StringField('Cliente (Compañía de Seguros)', validators=[
        DataRequired(message='La compañía de seguros es obligatoria'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ], default='SANCOR COOP. LIMITADA DE SEGUROS')
    
    insured_company = StringField('Asegurado', validators=[
        DataRequired(message='El asegurado es obligatorio'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ])
    
    claim_number = StringField('Número de Siniestro', validators=[
        DataRequired(message='El número de siniestro es obligatorio'),
        Length(min=1, max=50, message='Debe tener entre 1 y 50 caracteres')
    ])
    
    incident_date = DateField('Fecha del Siniestro', validators=[
        DataRequired(message='La fecha del siniestro es obligatoria')
    ], default=date.today)
    
    # Información del equipo
    device_type = StringField('Objeto', validators=[
        DataRequired(message='El tipo de equipo es obligatorio'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ], description='Ej: Tv 43", Heladera, etc.')
    
    brand = StringField('Marca', validators=[
        DataRequired(message='La marca es obligatoria'),
        Length(min=1, max=50, message='Debe tener entre 1 y 50 caracteres')
    ])
    
    model = StringField('Modelo', validators=[
        DataRequired(message='El modelo es obligatorio'),
        Length(min=1, max=100, message='Debe tener entre 1 y 100 caracteres')
    ])
    
    serial_number = StringField('Número de Serie', validators=[
        Optional(),
        Length(max=100, message='No puede tener más de 100 caracteres')
    ])
    
    problem_description = TextAreaField('Detalles del Problema', validators=[
        DataRequired(message='La descripción del problema es obligatoria'),
        Length(min=10, max=500, message='Debe tener entre 10 y 500 caracteres')
    ], description='Descripción breve del problema reportado')
    
    # Diagnóstico técnico
    technical_diagnosis = TextAreaField('Informe Técnico', validators=[
        DataRequired(message='El informe técnico es obligatorio'),
        Length(min=50, max=2000, message='Debe tener entre 50 y 2000 caracteres')
    ], description='Diagnóstico técnico detallado del problema')
    
    diagnosis_price = FloatField('Precio de Diagnóstico', validators=[
        DataRequired(message='El precio de diagnóstico es obligatorio'),
        NumberRange(min=0, message='El precio debe ser un número positivo')
    ], default=25000.0)
    
    repair_price = FloatField('Precio de Reparación', validators=[
        Optional(),
        NumberRange(min=0, message='El precio debe ser un número positivo')
    ])
    
    # Información del técnico (pre-llenado pero editable)
    technician_name = StringField('Nombre del Técnico', validators=[
        DataRequired(message='El nombre del técnico es obligatorio'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ], default='Leonardo A. Acosta')
    
    professional_license = StringField('Matrícula Profesional', validators=[
        DataRequired(message='La matrícula profesional es obligatoria'),
        Length(min=1, max=20, message='Debe tener entre 1 y 20 caracteres')
    ], default='2200')
    
    # Archivos de imágenes
    image1 = FileField('Imagen 1', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten archivos JPG, JPEG y PNG')
    ])
    
    image2 = FileField('Imagen 2 (Opcional)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten archivos JPG, JPEG y PNG')
    ])
    
    image3 = FileField('Imagen 3 (Opcional)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten archivos JPG, JPEG y PNG')
    ])
    
    submit = SubmitField('Generar Informe')

class SearchReportForm(FlaskForm):
    """Formulario de búsqueda de informes."""
    
    search = StringField('Buscar', validators=[
        Optional(),
        Length(max=100, message='La búsqueda no puede tener más de 100 caracteres')
    ], description='Buscar por asegurado, siniestro, marca, modelo...')
    
    submit = SubmitField('Buscar')