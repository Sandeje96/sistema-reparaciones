# app/repairs/forms.py
"""
Formularios para gestión de reparaciones.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, SubmitField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from app.models import Repair

class RepairForm(FlaskForm):
    """Formulario para agregar/editar reparaciones."""
    
    # Información del cliente
    client_name = StringField('Nombre del Cliente', validators=[
        DataRequired(message='El nombre del cliente es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    
    client_phone = StringField('Teléfono del Cliente', validators=[
        Optional(),
        Length(max=20, message='El teléfono no puede tener más de 20 caracteres')
    ])
    
    # Información del equipo
    device_type = StringField('Tipo de Equipo', validators=[
        DataRequired(message='El tipo de equipo es obligatorio'),
        Length(min=2, max=50, message='El tipo debe tener entre 2 y 50 caracteres')
    ])
    
    brand = StringField('Marca', validators=[
        DataRequired(message='La marca es obligatoria'),
        Length(min=1, max=50, message='La marca debe tener entre 1 y 50 caracteres')
    ])
    
    model = StringField('Modelo', validators=[
        DataRequired(message='El modelo es obligatorio'),
        Length(min=1, max=50, message='El modelo debe tener entre 1 y 50 caracteres')
    ])
    
    serial_number = StringField('Número de Serie', validators=[
        Optional(),
        Length(max=100, message='El número de serie no puede tener más de 100 caracteres')
    ])
    
    # Descripción del problema
    problem_description = TextAreaField('Descripción del Problema', validators=[
        DataRequired(message='La descripción del problema es obligatoria'),
        Length(min=10, max=1000, message='La descripción debe tener entre 10 y 1000 caracteres')
    ])
    
    # Estado
    status = SelectField('Estado', choices=Repair.STATUS_CHOICES, validators=[
        DataRequired(message='El estado es obligatorio')
    ])
    
    # Información adicional
    diagnosis_notes = TextAreaField('Notas de Diagnóstico', validators=[
        Optional(),
        Length(max=1000, message='Las notas no pueden tener más de 1000 caracteres')
    ])
    
    repair_cost = FloatField('Costo de Reparación', validators=[
        Optional(),
        NumberRange(min=0, message='El costo debe ser un número positivo')
    ])
    
    # Después de estas líneas:
    parts_needed = TextAreaField('Repuestos Necesarios', validators=[
        Optional(),
        Length(max=500, message='Los repuestos no pueden tener más de 500 caracteres')
    ])

    # AGREGAR ESTOS NUEVOS CAMPOS:
    # Información adicional para informes técnicos (opcional)
    insurance_company = StringField('Compañía de Seguros', validators=[
        Optional(),
        Length(max=100, message='No puede tener más de 100 caracteres')
    ])

    insured_company = StringField('Empresa Asegurada', validators=[
        Optional(),
        Length(max=100, message='No puede tener más de 100 caracteres')
    ])

    claim_number = StringField('Número de Siniestro', validators=[
        Optional(),
        Length(max=50, message='No puede tener más de 50 caracteres')
    ])

    
    incident_date = StringField('Fecha del Siniestro', validators=[
        Optional()
    ], render_kw={"type": "date"})
    
    submit = SubmitField('Guardar')

class SearchForm(FlaskForm):
    """Formulario de búsqueda y filtros."""
    
    search = StringField('Buscar', validators=[
        Optional(),
        Length(max=100, message='La búsqueda no puede tener más de 100 caracteres')
    ])
    
    status_filter = SelectField('Filtrar por Estado', choices=[
        ('', 'Todos los estados'),
        ('active', 'Solo activos'),
        (Repair.PENDING_DIAGNOSIS, 'Falta diagnóstico'),
        (Repair.DIAGNOSED, 'Diagnóstico hecho'),
        (Repair.WAITING_PARTS, 'Esperando repuestos'),
        (Repair.READY_FOR_DELIVERY, 'Pendiente de entrega'),
        (Repair.DELIVERED, 'Entregado'),
        (Repair.NO_REPAIR, 'Sin reparación')
    ])
    
    priority_filter = SelectField('Filtrar por Prioridad', choices=[
        ('', 'Todas las prioridades'),
        ('high', 'Urgente (15+ días)'),
        ('medium', 'Media (7-14 días)'),
        ('low', 'Baja (menos de 7 días)')
    ])
    
    submit = SubmitField('Buscar')

class QuickStatusForm(FlaskForm):
    """Formulario rápido para cambio de estado."""
    
    status = SelectField('Nuevo Estado', choices=Repair.STATUS_CHOICES, validators=[
        DataRequired(message='El estado es obligatorio')
    ])
    
    submit = SubmitField('Actualizar')