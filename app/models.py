# app/models.py
"""
Modelos de base de datos para el Taller Mecánico Don Orlando.
"""

from datetime import datetime
import re
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import uuid
import os


class User(UserMixin, db.Model):
    """Modelo de usuario del sistema."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
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
    """
    Modelo de Reparación y Gestión de Vehículos en Taller Mecánico Don Orlando.
    """
    __tablename__ = 'repairs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 🚗 Identificación del Vehículo
    license_plate = db.Column(db.String(10), nullable=False, index=True)  # Patente: XXX111 o XX111XX
    brand = db.Column(db.String(50), nullable=False)                      # Marca: Ford, Chevrolet, Toyota, etc.
    model = db.Column(db.String(50), nullable=False)                      # Modelo: Focus, Hilux, Gol, etc.
    year = db.Column(db.Integer, nullable=True)                           # Año
    color = db.Column(db.String(30), nullable=True)                       # Color
    mileage = db.Column(db.Integer, nullable=True)                        # Kilometraje actual
    
    # 👤 Datos del Cliente
    client_name = db.Column(db.String(100), nullable=False, index=True)
    client_phone = db.Column(db.String(30), nullable=True)
    client_email = db.Column(db.String(100), nullable=True)
    
    # 🔧 Motivo de Ingreso, Diagnóstico y Tareas
    problem_description = db.Column(db.Text, nullable=False)  # Motivo de ingreso / Falla manifestada
    diagnosis = db.Column(db.Text, nullable=True)             # Problema detectado por el mecánico
    work_to_do = db.Column(db.Text, nullable=True)            # Trabajo a realizar / Reparaciones presupuestadas
    parts_needed = db.Column(db.Text, nullable=True)          # Repuestos e insumos necesarios
    
    # 💰 Costos
    estimated_cost = db.Column(db.Float, nullable=True)       # Presupuesto estimado
    final_cost = db.Column(db.Float, nullable=True)           # Costo final cobrado
    
    # 🚦 Estados de permanencia en taller
    STATUS_INGRESADO = 'ingresado'
    STATUS_DIAGNOSTICADO = 'diagnosticado'
    STATUS_EN_REPARACION = 'en_reparacion'
    STATUS_ESPERANDO_REPUESTOS = 'esperando_repuestos'
    STATUS_LISTO = 'listo'
    STATUS_ENTREGADO = 'entregado'
    
    STATUS_CHOICES = [
        (STATUS_INGRESADO, 'Ingresado (Pendiente revisión)'),
        (STATUS_DIAGNOSTICADO, 'Diagnóstico realizado'),
        (STATUS_EN_REPARACION, 'En reparación'),
        (STATUS_ESPERANDO_REPUESTOS, 'Esperando repuestos'),
        (STATUS_LISTO, 'Listo para entregar'),
        (STATUS_ENTREGADO, 'Entregado')
    ]
    
    status = db.Column(db.String(30), nullable=False, default=STATUS_INGRESADO, index=True)
    
    # ⏱️ Fechas para seguimiento del tiempo
    entry_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    diagnosis_date = db.Column(db.DateTime, nullable=True)
    completion_date = db.Column(db.DateTime, nullable=True)
    delivery_date = db.Column(db.DateTime, nullable=True)
    
    # Auditoría
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con usuario
    creator = db.relationship('User', backref=db.backref('repairs', lazy=True))
    
    @staticmethod
    def clean_plate(plate):
        """Limpia y normaliza la patente (mayúsculas, sin espacios ni guiones)."""
        if not plate:
            return ''
        return re.sub(r'[^A-Za-z0-9]', '', plate).upper()
    
    @property
    def formatted_plate(self):
        """Devuelve la patente con formato legible (ej: AA 123 BB o ABC 123)."""
        plate = self.clean_plate(self.license_plate)
        if len(plate) == 6:  # Formato tradicional: XXX111 -> XXX 111
            return f"{plate[:3]} {plate[3:]}"
        elif len(plate) == 7:  # Formato Mercosur: XX111XX -> XX 111 XX
            return f"{plate[:2]} {plate[2:5]} {plate[5:]}"
        return plate
    
    def days_in_shop(self):
        """Calcula los días transcurridos desde el ingreso del vehículo."""
        if not self.entry_date:
            return 0
        ref_date = self.delivery_date if (self.status == self.STATUS_ENTREGADO and self.delivery_date) else datetime.utcnow()
        delta = ref_date - self.entry_date
        return max(0, delta.days)
    
    def days_since_entry(self):
        """Compatibilidad con métodos anteriores."""
        return self.days_in_shop()
    
    def get_days_badge_class(self):
        """Retorna la clase CSS para el badge de días transcurridos."""
        if self.status == self.STATUS_ENTREGADO:
            return 'days-counter days-delivered'
        days = self.days_in_shop()
        if days >= 7:
            return 'days-counter days-delayed'     # Demorado (+7 días)
        elif days >= 3:
            return 'days-counter days-attention'   # En atención (3-6 días)
        else:
            return 'days-counter days-recent'      # Reciente (0-2 días)
            
    def get_days_badge_label(self):
        """Texto claro para el badge de días en celular."""
        if self.status == self.STATUS_ENTREGADO:
            return f'Estuvo {self.days_in_shop()} días'
        days = self.days_in_shop()
        if days == 0:
            return 'Ingresó hoy'
        elif days == 1:
            return '1 día en taller'
        else:
            return f'{days} días en taller'
    
    def get_status_badge_class(self):
        """Clase CSS para el badge de estado."""
        return f'status-pill status-{self.status}'
    
    def get_status_display(self):
        """Obtener el nombre amigable del estado."""
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict.get(self.status, 'Desconocido')
    
    def is_active(self):
        """Verificar si el vehículo sigue en el taller."""
        return self.status != self.STATUS_ENTREGADO
        
    @property
    def vehicle_title(self):
        """Título amigable: Marca Modelo (Año)."""
        year_str = f" ({self.year})" if self.year else ""
        return f"{self.brand} {self.model}{year_str}"
        
    @property
    def items_total(self):
        """Suma total de todos los ítems de la proforma/presupuesto."""
        return sum((item.price or 0.0) for item in self.items)

    @property
    def labor_revenue(self):
        """
        Suma total de Mano de Obra (sobre la cual se reparte 70% Daniel y 30% Titular).
        Si no hay ítems en la proforma, toma el monto total estimado/final como mano de obra.
        """
        if self.items:
            return float(sum((item.price or 0.0) for item in self.items if getattr(item, 'item_type', 'mano_obra') != 'repuesto'))
        if self.final_cost is not None and self.final_cost > 0:
            return float(self.final_cost)
        return float(self.estimated_cost or 0.0)

    @property
    def parts_revenue(self):
        """Suma total de Repuestos (columna informativa separada, no entra en el reparto 70/30)."""
        if self.items:
            return float(sum((item.price or 0.0) for item in self.items if getattr(item, 'item_type', 'mano_obra') == 'repuesto'))
        return 0.0

    @property
    def effective_revenue(self):
        """Monto total efectivo del arreglo (Mano de Obra + Repuestos)."""
        if self.items:
            return float(self.items_total)
        if self.final_cost is not None and self.final_cost > 0:
            return float(self.final_cost)
        return float(self.estimated_cost or 0.0)

    @property
    def daniel_share(self):
        """70% de la Mano de Obra correspondiente al mecánico Daniel."""
        return round(self.labor_revenue * 0.70, 2)

    @property
    def owner_labor_share(self):
        """30% de la Mano de Obra correspondiente al titular del taller."""
        return round(self.labor_revenue * 0.30, 2)

    @property
    def owner_share(self):
        """30% de la Mano de Obra correspondiente al titular del taller (los repuestos van en columna separada)."""
        return self.owner_labor_share

    @property
    def revenue_reference_date(self):
        """Fecha de referencia para imputar el ingreso en el mes."""
        if self.status == self.STATUS_ENTREGADO and self.delivery_date:
            return self.delivery_date
        if self.status in (self.STATUS_LISTO, self.STATUS_ENTREGADO) and self.completion_date:
            return self.completion_date
        return self.entry_date or self.created_at
        
    @property
    def clean_whatsapp_phone(self):
        """Normaliza el teléfono para enlaces de WhatsApp (wa.me)."""
        if not self.client_phone:
            return ''
        digits = re.sub(r'\D', '', self.client_phone)
        if not digits:
            return ''
        # Si es un celular argentino de 10 dígitos sin código de país (ej: 1145678901), anteponer 549
        if len(digits) == 10 and not digits.startswith('54'):
            return f"549{digits}"
        return digits

    def __repr__(self):
        return f'<Vehículo {self.license_plate}: {self.brand} {self.model}>'


class RepairItem(db.Model):
    """
    Ítem individual de presupuesto / proforma para una reparación.
    Cada fila tiene:
    - description: nombre del trabajo o repuesto
    - item_type: 'mano_obra' (se reparte 70% Daniel / 30% Titular) o 'repuesto' (columna informativa separada)
    - price: importe del ítem
    """
    __tablename__ = 'repair_items'
    
    TYPE_MANO_OBRA = 'mano_obra'
    TYPE_REPUESTO = 'repuesto'
    
    id = db.Column(db.Integer, primary_key=True)
    repair_id = db.Column(db.Integer, db.ForeignKey('repairs.id', ondelete='CASCADE'), nullable=False, index=True)
    item_type = db.Column(db.String(20), nullable=False, default=TYPE_MANO_OBRA)  # 'mano_obra' o 'repuesto'
    description = db.Column(db.String(300), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    repair = db.relationship(
        'Repair',
        backref=db.backref('items', lazy=True, order_by='RepairItem.order_index, RepairItem.id', cascade='all, delete-orphan')
    )
    
    @property
    def type_label(self):
        """Etiqueta legible del tipo de ítem."""
        return 'Repuesto' if self.item_type == self.TYPE_REPUESTO else 'Mano de Obra'
    
    def __repr__(self):
        return f'<RepairItem {self.id} [{self.item_type}]: {self.description} (${self.price})>'


# Alias para mayor claridad semántica
VehicleRepair = Repair


class TechnicalReport(db.Model):
    """Modelo opcional para informes técnicos detallados."""
    __tablename__ = 'technical_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    insurance_company = db.Column(db.String(100), nullable=True)
    insured_company = db.Column(db.String(100), nullable=True)
    claim_number = db.Column(db.String(50), nullable=True)
    incident_date = db.Column(db.Date, nullable=True)
    
    license_plate = db.Column(db.String(20), nullable=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    problem_description = db.Column(db.Text, nullable=False)
    technical_diagnosis = db.Column(db.Text, nullable=False)
    diagnosis_price = db.Column(db.Float, nullable=False, default=0.0)
    repair_price = db.Column(db.Float, nullable=True)
    
    technician_name = db.Column(db.String(100), nullable=False, default='Don Orlando')
    
    image1_filename = db.Column(db.String(255), nullable=True)
    image2_filename = db.Column(db.String(255), nullable=True)
    image3_filename = db.Column(db.String(255), nullable=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref=db.backref('technical_reports', lazy=True))
    
    def __repr__(self):
        return f'<TechnicalReport {self.id}: {self.brand} {self.model}>'
