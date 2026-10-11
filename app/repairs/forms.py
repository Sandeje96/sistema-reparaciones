# app/repairs/forms.py
"""
Formularios para gestión de vehículos y reparaciones en el Taller Mecánico Don Orlando.
"""

import re
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models import Repair


def validate_license_plate(form, field):
    """
    Valida que la patente cumpla con los dos formatos:
    - Formato tradicional: 3 letras y 3 números (XXX111)
    - Formato Mercosur: 2 letras, 3 números y 2 letras (XX111XX)
    """
    raw_plate = field.data or ''
    # Quitar espacios y guiones y pasar a mayúsculas
    clean = re.sub(r'[^A-Za-z0-9]', '', raw_plate).upper()
    
    patron_tradicional = r'^[A-Z]{3}\d{3}$'       # XXX111
    patron_mercosur = r'^[A-Z]{2}\d{3}[A-Z]{2}$'   # XX111XX
    
    if not (re.match(patron_tradicional, clean) or re.match(patron_mercosur, clean)):
        raise ValidationError(
            'Formato de patente no válido. Debe ser XXX111 (ej: ABC123) o XX111XX (ej: AA123BB).'
        )


class RepairForm(FlaskForm):
    """Formulario para registro y edición completa de vehículos en el taller."""
    
    # Identificación del vehículo
    license_plate = StringField('Patente / Dominio', validators=[
        DataRequired(message='La patente es obligatoria'),
        Length(min=6, max=10, message='La patente debe tener entre 6 y 9 caracteres'),
        validate_license_plate
    ], render_kw={"placeholder": "Ej: ABC123 o AA123BB", "style": "text-transform: uppercase;"})
    
    brand = StringField('Marca', validators=[
        DataRequired(message='La marca es obligatoria'),
        Length(min=2, max=50, message='La marca debe tener entre 2 y 50 caracteres')
    ], render_kw={"placeholder": "Ej: Ford, Volkswagen, Toyota"})
    
    model = StringField('Modelo', validators=[
        DataRequired(message='El modelo es obligatorio'),
        Length(min=1, max=50, message='El modelo debe tener entre 1 y 50 caracteres')
    ], render_kw={"placeholder": "Ej: Fiesta, Hilux, Gol Trend"})
    
    year = IntegerField('Año', validators=[
        Optional(),
        NumberRange(min=1950, max=2030, message='Año fuera de rango razonable')
    ], render_kw={"placeholder": "Ej: 2018"})
    
    color = StringField('Color', validators=[
        Optional(),
        Length(max=30, message='Máximo 30 caracteres')
    ], render_kw={"placeholder": "Ej: Gris plata, Blanco, Negro"})
    
    mileage = IntegerField('Kilometraje (Km)', validators=[
        Optional(),
        NumberRange(min=0, message='El kilometraje debe ser mayor o igual a 0')
    ], render_kw={"placeholder": "Ej: 125000"})
    
    # Información del cliente
    client_name = StringField('Nombre del Cliente', validators=[
        DataRequired(message='El nombre del cliente es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ], render_kw={"placeholder": "Nombre y apellido del cliente"})
    
    client_phone = StringField('Teléfono / WhatsApp', validators=[
        Optional(),
        Length(max=30, message='Máximo 30 caracteres')
    ], render_kw={"placeholder": "Ej: 11-5555-5555"})
    
    client_email = StringField('Email del Cliente', validators=[
        Optional(),
        Length(max=100, message='Máximo 100 caracteres')
    ], render_kw={"placeholder": "cliente@email.com"})
    
    # Motivo de ingreso y fallas
    problem_description = TextAreaField('Falla manifestada / Motivo de ingreso', validators=[
        DataRequired(message='Indique el motivo por el cual ingresa el vehículo'),
        Length(min=5, max=2000, message='La descripción debe tener entre 5 y 2000 caracteres')
    ], render_kw={"rows": 3, "placeholder": "Ej: Ruido en tren delantero al doblar a la derecha y pérdida leve de aceite..."})
    
    # Diagnóstico y plan de trabajo
    diagnosis = TextAreaField('Problema detectado / Diagnóstico mecánico', validators=[
        Optional(),
        Length(max=2000, message='Máximo 2000 caracteres')
    ], render_kw={"rows": 3, "placeholder": "Ej: Extremo de dirección derecho con juego excesivo. Fuelle homocinética roto."})
    
    work_to_do = TextAreaField('Trabajo a realizar / Reparaciones', validators=[
        Optional(),
        Length(max=2000, message='Máximo 2000 caracteres')
    ], render_kw={"rows": 3, "placeholder": "Ej: Cambio de extremo de dirección derecho, alineación y balanceo, cambio de fuelle."})
    
    parts_needed = TextAreaField('Repuestos necesarios', validators=[
        Optional(),
        Length(max=1000, message='Máximo 1000 caracteres')
    ], render_kw={"rows": 2, "placeholder": "Ej: 1x Extremo derecho original, 1x Fuelle lado rueda..."})
    
    # Estado y costos
    status = SelectField('Estado del Vehículo', choices=Repair.STATUS_CHOICES, validators=[
        DataRequired(message='El estado es obligatorio')
    ])
    
    estimated_cost = FloatField('Presupuesto Estimado ($)', validators=[
        Optional(),
        NumberRange(min=0, message='El monto debe ser un número positivo')
    ], render_kw={"placeholder": "0.00"})
    
    final_cost = FloatField('Costo Final ($)', validators=[
        Optional(),
        NumberRange(min=0, message='El costo debe ser un número positivo')
    ], render_kw={"placeholder": "0.00"})
    
    submit = SubmitField('Guardar Vehículo')


class DiagnosisWorkForm(FlaskForm):
    """Formulario específico para que el mecánico registre el diagnóstico y trabajo a realizar."""
    
    diagnosis = TextAreaField('Problema detectado (Diagnóstico Mecánico)', validators=[
        DataRequired(message='Debe ingresar el diagnóstico o problema detectado'),
        Length(min=5, max=2000, message='El diagnóstico debe tener al menos 5 caracteres')
    ], render_kw={"rows": 4, "placeholder": "Detalle técnico de la falla encontrada en la revisión..."})
    
    work_to_do = TextAreaField('Trabajo a realizar (Tareas y Reparaciones)', validators=[
        DataRequired(message='Debe especificar qué trabajo o reparaciones se van a efectuar'),
        Length(min=5, max=2000, message='Especifique el trabajo a realizar')
    ], render_kw={"rows": 4, "placeholder": "Detalle de los trabajos, mano de obra y servicios a ejecutar..."})
    
    parts_needed = TextAreaField('Repuestos e Insumos requeridos', validators=[
        Optional(),
        Length(max=1000, message='Máximo 1000 caracteres')
    ], render_kw={"rows": 3, "placeholder": "Repuestos, aceites, filtros o piezas a encargar..."})
    
    estimated_cost = FloatField('Presupuesto Estimado ($)', validators=[
        Optional(),
        NumberRange(min=0, message='Debe ser positivo')
    ], render_kw={"placeholder": "0.00"})
    
    status = SelectField('Actualizar Estado', choices=Repair.STATUS_CHOICES, default=Repair.STATUS_DIAGNOSTICADO)
    
    submit = SubmitField('Registrar Diagnóstico y Plan de Trabajo')


class SearchForm(FlaskForm):
    """Formulario de búsqueda y filtros para el taller."""
    search = StringField('Buscar', render_kw={"placeholder": "Buscar por Patente, Cliente, Marca, Modelo..."})
    status = SelectField('Estado', choices=[('', 'Todos los estados')] + Repair.STATUS_CHOICES)
    filter_active = SelectField('Permanencia', choices=[
        ('in_shop', 'Activos en Taller'),
        ('overdue', 'Demorados (+7 días)'),
        ('delivered', 'Entregados (Historial)'),
        ('all', 'Todos los registros')
    ], default='in_shop')
    submit = SubmitField('Filtrar')