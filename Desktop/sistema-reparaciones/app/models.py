# app/models.py
"""
Modelos de base de datos para el Sistema de Gestión de Reparaciones.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import uuid
import os

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

# 🆕 NUEVO MODELO PARA INFORMES TÉCNICOS
class TechnicalReport(db.Model):
    """Modelo para informes técnicos de seguros."""
    
    __tablename__ = 'technical_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificador único para archivos
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Información del seguro
    insurance_company = db.Column(db.String(100), nullable=False)  # Cliente (ej: SANCOR COOP.)
    insured_company = db.Column(db.String(100), nullable=False)    # Asegurado (ej: OSOL S.R.L)
    claim_number = db.Column(db.String(50), nullable=False)        # Siniestro
    incident_date = db.Column(db.Date, nullable=False)             # Fecha del siniestro
    
    # Información del equipo
    device_type = db.Column(db.String(100), nullable=False)        # Objeto (ej: Tv 43'')
    brand = db.Column(db.String(50), nullable=False)               # Marca
    model = db.Column(db.String(100), nullable=False)              # Modelo
    serial_number = db.Column(db.String(100), nullable=True)       # Serie
    problem_description = db.Column(db.Text, nullable=False)       # Detalles del problema
    
    # Diagnóstico técnico
    technical_diagnosis = db.Column(db.Text, nullable=False)       # Informe técnico detallado
    diagnosis_price = db.Column(db.Float, nullable=False)          # Precio de diagnóstico
    repair_price = db.Column(db.Float, nullable=True)              # Precio de reparación
    
    # Información del técnico
    technician_name = db.Column(db.String(100), nullable=False, default='Leonardo A. Acosta')
    professional_license = db.Column(db.String(20), nullable=False, default='2200')
    
    # Archivos de imágenes (máximo 3)
    image1_filename = db.Column(db.String(255), nullable=True)
    image2_filename = db.Column(db.String(255), nullable=True)
    image3_filename = db.Column(db.String(255), nullable=True)
    
    # Metadatos
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    creator = db.relationship('User', backref=db.backref('technical_reports', lazy=True))
    
    def get_images(self):
        """Obtener lista de imágenes no vacías."""
        images = []
        for i in range(1, 4):
            filename = getattr(self, f'image{i}_filename')
            if filename:
                images.append({
                    'number': i,
                    'filename': filename,
                    'path': f'uploads/informes/{filename}'
                })
        return images
    
    def get_upload_folder(self):
        """Obtener carpeta de subida para este informe."""
        return os.path.join('app', 'static', 'uploads', 'informes')
    
    def delete_images(self):
        """Eliminar archivos de imágenes asociados."""
        upload_folder = self.get_upload_folder()
        for i in range(1, 4):
            filename = getattr(self, f'image{i}_filename')
            if filename:
                file_path = os.path.join(upload_folder, filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass  # Error silencioso si no se puede eliminar
    
    def __repr__(self):
        return f'<TechnicalReport {self.id}: {self.claim_number} - {self.device_type}>'