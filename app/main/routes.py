# app/main/routes.py
"""
Rutas principales del sistema Taller Mecánico Don Orlando.
"""

from datetime import datetime, timedelta
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import bp
from app.models import Repair
from app import db


@bp.route('/')
def index():
    """Página principal - redirige al panel de vehículos si está logueado, o al login."""
    if current_user.is_authenticated:
        return redirect(url_for('repairs.index'))
    else:
        return redirect(url_for('auth.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard con estadísticas generales del taller."""
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    
    # Vehículos en taller (no entregados)
    in_shop_query = Repair.query.filter(Repair.status != Repair.STATUS_ENTREGADO)
    total_in_shop = in_shop_query.count()
    
    pending_diagnosis = Repair.query.filter_by(status=Repair.STATUS_INGRESADO).count()
    diagnosed = Repair.query.filter_by(status=Repair.STATUS_DIAGNOSTICADO).count()
    in_repair = Repair.query.filter_by(status=Repair.STATUS_EN_REPARACION).count()
    waiting_parts = Repair.query.filter_by(status=Repair.STATUS_ESPERANDO_REPUESTOS).count()
    ready_for_delivery = Repair.query.filter_by(status=Repair.STATUS_LISTO).count()
    delivered_total = Repair.query.filter_by(status=Repair.STATUS_ENTREGADO).count()
    
    # Vehículos con más de 7 días en el taller
    overdue_vehicles = in_shop_query.filter(Repair.entry_date <= seven_days_ago).all()
    overdue_count = len(overdue_vehicles)
    
    # Vehículos con mayor tiempo de estadía
    longest_stay = in_shop_query.order_by(Repair.entry_date.asc()).limit(8).all()
    
    stats = {
        'total_in_shop': total_in_shop,
        'pending_diagnosis': pending_diagnosis,
        'diagnosed': diagnosed,
        'in_repair': in_repair,
        'waiting_parts': waiting_parts,
        'ready_for_delivery': ready_for_delivery,
        'delivered_total': delivered_total,
        'overdue_count': overdue_count,
        'overdue_vehicles': overdue_vehicles,
        'longest_stay': longest_stay
    }
    
    return render_template('dashboard.html', stats=stats)