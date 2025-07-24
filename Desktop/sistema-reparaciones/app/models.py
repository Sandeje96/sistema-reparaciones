# app/models.py
"""
Modelos de base de datos para el Sistema de Gestión de Reparaciones.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """Modelo de usuario del sistema."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Establecer contraseña hasheada."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Repair(db.Model):
    """Modelo para reparaciones de equipos."""
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Información del cliente
    client_name = db.Column(db.String(100), nullable=False, index=True)
    client_phone = db.Column(db.String(20), nullable=True)
    
    # Información del equipo
    device_type = db.Column(db.String(50), nullable=False)  # TV, Radio, etc.
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(100), nullable=True)
    
    # Descripción del problema
    problem_description = db.Column(db.Text, nullable=False)
    
    # Estados de la reparación
    PENDING_DIAGNOSIS = 'pending_diagnosis'
    DIAGNOSED = 'diagnosed'
    WAITING_PARTS = 'waiting_parts'
    READY_FOR_DELIVERY = 'ready_for_delivery'
    DELIVERED = 'delivered'
    NO_REPAIR = 'no_repair'
    
    STATUS_CHOICES = [
        (PENDING_DIAGNOSIS, 'Falta diagnóstico'),
        (DIAGNOSED, 'Diagnóstico hecho'),
        (WAITING_PARTS, 'Esperando repuestos'),
        (READY_FOR_DELIVERY, 'Pendiente de entrega'),
        (DELIVERED, 'Entregado'),
        (NO_REPAIR, 'Sin reparación')
    ]
    
    status = db.Column(db.String(20), nullable=False, default=PENDING_DIAGNOSIS, index=True)
    
    # Información adicional
    diagnosis_notes = db.Column(db.Text, nullable=True)
    repair_cost = db.Column(db.Float, nullable=True)
    parts_needed = db.Column(db.Text, nullable=True)
    
    # Fechas
    entry_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    diagnosis_date = db.Column(db.DateTime, nullable=True)
    completion_date = db.Column(db.DateTime, nullable=True)
    delivery_date = db.Column(db.DateTime, nullable=True)
    
    # Usuario que creó el registro
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con usuario
    creator = db.relationship('User', backref=db.backref('repairs', lazy=True))
    
    def get_status_display(self):
        """Obtener el nombre amigable del estado."""
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict.get(self.status, 'Desconocido')
    
    def days_since_entry(self):
        """Calcular días desde el ingreso."""
        delta = datetime.utcnow() - self.entry_date
        return delta.days
    
    def get_priority_class(self):
        """Obtener clase CSS basada en la antigüedad."""
        days = self.days_since_entry()
        if days >= 15:
            return 'priority-high'
        elif days >= 7:
            return 'priority-medium'
        else:
            return 'priority-low'
    
    def get_priority_label(self):
        """Obtener etiqueta de prioridad."""
        days = self.days_since_entry()
        if days >= 15:
            return 'Urgente'
        elif days >= 7:
            return 'Media'
        else:
            return 'Baja'
    
    def is_active(self):
        """Verificar si la reparación está activa (no entregada ni sin reparación)."""
        return self.status not in [self.DELIVERED, self.NO_REPAIR]
    
    def __repr__(self):
        return f'<Repair {self.id}: {self.client_name} - {self.device_type}>'
