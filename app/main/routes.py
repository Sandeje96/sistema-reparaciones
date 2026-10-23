# app/main/routes.py
"""
Rutas principales del sistema Taller Mecánico Don Orlando.
"""

from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, send_file, flash
from flask_login import login_required, current_user
from app.main import bp
from app.models import Repair
from app.repairs.utils import generate_liquidacion_pdf
from app import db


MESES_ES = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre'
}


def _calculate_monthly_income(selected_year, selected_month):
    """Función auxiliar que calcula las reparaciones confirmadas, pendientes y totales del mes."""
    now = datetime.utcnow()
    all_repairs = Repair.query.order_by(Repair.entry_date.desc()).all()
    
    confirmed_repairs = []
    pending_repairs = []
    years_set = {now.year}
    
    for r in all_repairs:
        ref_date = r.revenue_reference_date
        if ref_date:
            years_set.add(ref_date.year)
            
        if r.status in (Repair.STATUS_LISTO, Repair.STATUS_ENTREGADO):
            if ref_date and ref_date.year == selected_year and ref_date.month == selected_month:
                confirmed_repairs.append(r)
        else:
            if r.effective_revenue > 0 or (ref_date and ref_date.year == selected_year and ref_date.month == selected_month):
                pending_repairs.append(r)
                
    total_confirmed = sum(r.effective_revenue for r in confirmed_repairs)
    labor_confirmed = sum(r.labor_revenue for r in confirmed_repairs)
    parts_confirmed = sum(r.parts_revenue for r in confirmed_repairs)
    daniel_confirmed = round(sum(r.daniel_share for r in confirmed_repairs), 2)
    owner_labor_confirmed = round(sum(r.owner_labor_share for r in confirmed_repairs), 2)
    
    total_pending = sum(r.effective_revenue for r in pending_repairs)
    labor_pending = sum(r.labor_revenue for r in pending_repairs)
    parts_pending = sum(r.parts_revenue for r in pending_repairs)
    daniel_pending = round(sum(r.daniel_share for r in pending_repairs), 2)
    owner_labor_pending = round(sum(r.owner_labor_share for r in pending_repairs), 2)
    
    summary = {
        'total_confirmed': total_confirmed,
        'labor_confirmed': labor_confirmed,
        'parts_confirmed': parts_confirmed,
        'daniel_confirmed': daniel_confirmed,
        'owner_labor_confirmed': owner_labor_confirmed,
        'owner_confirmed': owner_labor_confirmed,
        'count_confirmed': len(confirmed_repairs),
        'total_pending': total_pending,
        'labor_pending': labor_pending,
        'parts_pending': parts_pending,
        'daniel_pending': daniel_pending,
        'owner_labor_pending': owner_labor_pending,
        'owner_pending': owner_labor_pending,
        'count_pending': len(pending_repairs)
    }
    return confirmed_repairs, pending_repairs, sorted(years_set, reverse=True), summary


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


@bp.route('/ingresos')
@login_required
def ingresos():
    """
    Sección de ingresos mensuales y liquidación de Mano de Obra:
    - Daniel (Mecánico): 70% de la Mano de Obra
    - Titular (Vos): 30% de la Mano de Obra
    - Repuestos: Columna aparte informativa (no entra en el reparto 70/30)
    """
    now = datetime.utcnow()
    selected_year = request.args.get('year', now.year, type=int)
    selected_month = request.args.get('month', now.month, type=int)
    
    if selected_month < 1 or selected_month > 12:
        selected_month = now.month
        
    confirmed_repairs, pending_repairs, available_years, summary = _calculate_monthly_income(selected_year, selected_month)
    month_name = MESES_ES.get(selected_month, '')
    
    return render_template(
        'ingresos.html',
        selected_year=selected_year,
        selected_month=selected_month,
        month_name=month_name,
        months_list=MESES_ES,
        available_years=available_years,
        confirmed_repairs=confirmed_repairs,
        pending_repairs=pending_repairs,
        summary=summary
    )


@bp.route('/ingresos/pdf')
@login_required
def ingresos_pdf():
    """
    Genera y descarga (o previsualiza) el PDF de Rendición / Liquidación de Dinero del mes
    con espacios de firma para Daniel y el Titular.
    """
    now = datetime.utcnow()
    selected_year = request.args.get('year', now.year, type=int)
    selected_month = request.args.get('month', now.month, type=int)
    download = request.args.get('download', '1') == '1'
    
    if selected_month < 1 or selected_month > 12:
        selected_month = now.month
        
    month_name = MESES_ES.get(selected_month, '')
    confirmed_repairs, _, _, summary = _calculate_monthly_income(selected_year, selected_month)
    
    try:
        pdf_path = generate_liquidacion_pdf(selected_year, month_name, confirmed_repairs, summary)
        download_name = f"Rendicion_Liquidacion_{month_name}_{selected_year}.pdf".replace(' ', '_')
        return send_file(
            pdf_path,
            as_attachment=download,
            download_name=download_name,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error al generar el PDF de liquidación: {str(e)}', 'danger')
        return redirect(url_for('main.ingresos', year=selected_year, month=selected_month))
