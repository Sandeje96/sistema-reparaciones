# app/main/routes.py
"""
Rutas principales del sistema.
"""

from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import bp
from app.models import Repair
from app import db

@bp.route('/')
def index():
    """Página principal - redirige al dashboard de reparaciones."""
    if current_user.is_authenticated:
        return redirect(url_for('repairs.index'))
    else:
        return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard con estadísticas rápidas."""
    
    # Obtener estadísticas
    total_repairs = Repair.query.filter(Repair.status.in_([
        Repair.PENDING_DIAGNOSIS, 
        Repair.DIAGNOSED, 
        Repair.WAITING_PARTS, 
        Repair.READY_FOR_DELIVERY
    ])).count()
    
    pending_diagnosis = Repair.query.filter_by(status=Repair.PENDING_DIAGNOSIS).count()
    waiting_parts = Repair.query.filter_by(status=Repair.WAITING_PARTS).count()
    ready_for_delivery = Repair.query.filter_by(status=Repair.READY_FOR_DELIVERY).count()
    
    # Reparaciones urgentes (más de 15 días)
    from datetime import datetime, timedelta
    urgent_date = datetime.utcnow() - timedelta(days=15)
    urgent_repairs = Repair.query.filter(
        Repair.entry_date <= urgent_date,
        Repair.status.in_([
            Repair.PENDING_DIAGNOSIS, 
            Repair.DIAGNOSED, 
            Repair.WAITING_PARTS, 
            Repair.READY_FOR_DELIVERY
        ])
    ).count()
    
    # Reparaciones recientes
    recent_repairs = Repair.query.filter(
        Repair.status.in_([
            Repair.PENDING_DIAGNOSIS, 
            Repair.DIAGNOSED, 
            Repair.WAITING_PARTS, 
            Repair.READY_FOR_DELIVERY
        ])
    ).order_by(Repair.entry_date.asc()).limit(5).all()
    
    stats = {
        'total_repairs': total_repairs,
        'pending_diagnosis': pending_diagnosis,
        'waiting_parts': waiting_parts,
        'ready_for_delivery': ready_for_delivery,
        'urgent_repairs': urgent_repairs,
        'recent_repairs': recent_repairs
    }
    
    return render_template('dashboard.html', stats=stats)