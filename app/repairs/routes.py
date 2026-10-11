# app/repairs/routes.py
"""
Rutas para la gestión de vehículos y reparaciones en el Taller Mecánico Don Orlando.
"""

from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.repairs import bp
from app.repairs.forms import RepairForm, DiagnosisWorkForm, SearchForm
from app.models import Repair
from app import db


@bp.route('/')
@login_required
def index():
    """Panel principal de vehículos en taller."""
    search_form = SearchForm()
    
    # Parámetros de consulta
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    filter_active = request.args.get('filter_active', 'in_shop').strip()
    sort_by = request.args.get('sort_by', 'entry_asc')  # entry_asc = más tiempo en taller primero
    
    query = Repair.query
    
    # Búsqueda por texto (patente, cliente, marca, modelo, problema)
    if search:
        clean_search = Repair.clean_plate(search)
        search_like = f"%{search}%"
        filters = [
            Repair.client_name.ilike(search_like),
            Repair.brand.ilike(search_like),
            Repair.model.ilike(search_like),
            Repair.problem_description.ilike(search_like),
            Repair.diagnosis.ilike(search_like)
        ]
        if clean_search:
            filters.append(Repair.license_plate.ilike(f"%{clean_search}%"))
        query = query.filter(db.or_(*filters))
    
    # Filtro de permanencia
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    
    if filter_active == 'in_shop':
        query = query.filter(Repair.status != Repair.STATUS_ENTREGADO)
    elif filter_active == 'overdue':
        query = query.filter(
            Repair.status != Repair.STATUS_ENTREGADO,
            Repair.entry_date <= seven_days_ago
        )
    elif filter_active == 'delivered':
        query = query.filter(Repair.status == Repair.STATUS_ENTREGADO)
    
    # Filtro por estado puntual
    if status_filter:
        query = query.filter(Repair.status == status_filter)
        
    # Ordenamiento
    if sort_by == 'entry_asc':
        # Más días en taller primero (fecha de entrada más antigua)
        query = query.order_by(Repair.entry_date.asc())
    elif sort_by == 'entry_desc':
        # Recientes primero
        query = query.order_by(Repair.entry_date.desc())
    elif sort_by == 'plate':
        query = query.order_by(Repair.license_plate.asc())
    else:
        query = query.order_by(Repair.entry_date.asc())
        
    per_page = 15
    repairs = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Métricas rápidas de taller para la cabecera
    total_in_shop = Repair.query.filter(Repair.status != Repair.STATUS_ENTREGADO).count()
    pending_diagnosis = Repair.query.filter(Repair.status == Repair.STATUS_INGRESADO).count()
    in_repair = Repair.query.filter(Repair.status == Repair.STATUS_EN_REPARACION).count()
    ready_count = Repair.query.filter(Repair.status == Repair.STATUS_LISTO).count()
    overdue_count = Repair.query.filter(
        Repair.status != Repair.STATUS_ENTREGADO,
        Repair.entry_date <= seven_days_ago
    ).count()
    
    # Prellenar formulario
    search_form.search.data = search
    search_form.status.data = status_filter
    search_form.filter_active.data = filter_active
    
    return render_template(
        'repairs/index.html',
        repairs=repairs,
        search_form=search_form,
        search=search,
        status_filter=status_filter,
        filter_active=filter_active,
        sort_by=sort_by,
        stats={
            'total_in_shop': total_in_shop,
            'pending_diagnosis': pending_diagnosis,
            'in_repair': in_repair,
            'ready': ready_count,
            'overdue': overdue_count
        }
    )


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Registrar un nuevo vehículo que ingresa al taller."""
    form = RepairForm()
    
    if form.validate_on_submit():
        clean_plate = Repair.clean_plate(form.license_plate.data)
        
        vehicle = Repair(
            license_plate=clean_plate,
            brand=form.brand.data.strip(),
            model=form.model.data.strip(),
            year=form.year.data,
            color=form.color.data.strip() if form.color.data else None,
            mileage=form.mileage.data,
            client_name=form.client_name.data.strip(),
            client_phone=form.client_phone.data.strip() if form.client_phone.data else None,
            client_email=form.client_email.data.strip() if form.client_email.data else None,
            problem_description=form.problem_description.data.strip(),
            diagnosis=form.diagnosis.data.strip() if form.diagnosis.data else None,
            work_to_do=form.work_to_do.data.strip() if form.work_to_do.data else None,
            parts_needed=form.parts_needed.data.strip() if form.parts_needed.data else None,
            status=form.status.data,
            estimated_cost=form.estimated_cost.data,
            final_cost=form.final_cost.data,
            entry_date=datetime.utcnow(),
            created_by=current_user.id
        )
        
        if vehicle.diagnosis:
            vehicle.diagnosis_date = datetime.utcnow()
            
        db.session.add(vehicle)
        db.session.commit()
        
        flash(f'¡Vehículo [{vehicle.formatted_plate}] {vehicle.brand} {vehicle.model} ingresado al taller con éxito!', 'success')
        return redirect(url_for('repairs.view', id=vehicle.id))
        
    return render_template('repairs/add.html', form=form)


@bp.route('/<int:id>')
@login_required
def view(id):
    """Ficha detallada del vehículo, días en taller y trabajos."""
    vehicle = Repair.query.get_or_404(id)
    return render_template('repairs/view.html', vehicle=vehicle)


@bp.route('/<int:id>/diagnosis', methods=['GET', 'POST'])
@login_required
def diagnosis(id):
    """Cargar o actualizar el diagnóstico mecánico y las tareas a realizar."""
    vehicle = Repair.query.get_or_404(id)
    form = DiagnosisWorkForm()
    
    if form.validate_on_submit():
        vehicle.diagnosis = form.diagnosis.data.strip()
        vehicle.work_to_do = form.work_to_do.data.strip()
        vehicle.parts_needed = form.parts_needed.data.strip() if form.parts_needed.data else None
        vehicle.estimated_cost = form.estimated_cost.data
        vehicle.status = form.status.data
        
        if not vehicle.diagnosis_date:
            vehicle.diagnosis_date = datetime.utcnow()
            
        db.session.commit()
        flash(f'Diagnóstico y plan de trabajo actualizado para el vehículo [{vehicle.formatted_plate}].', 'success')
        return redirect(url_for('repairs.view', id=vehicle.id))
        
    elif request.method == 'GET':
        form.diagnosis.data = vehicle.diagnosis or ''
        form.work_to_do.data = vehicle.work_to_do or ''
        form.parts_needed.data = vehicle.parts_needed or ''
        form.estimated_cost.data = vehicle.estimated_cost
        form.status.data = vehicle.status if vehicle.status != Repair.STATUS_INGRESADO else Repair.STATUS_DIAGNOSTICADO
        
    return render_template('repairs/diagnosis.html', vehicle=vehicle, form=form)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edición integral de los datos del vehículo y cliente."""
    vehicle = Repair.query.get_or_404(id)
    form = RepairForm()
    
    if form.validate_on_submit():
        vehicle.license_plate = Repair.clean_plate(form.license_plate.data)
        vehicle.brand = form.brand.data.strip()
        vehicle.model = form.model.data.strip()
        vehicle.year = form.year.data
        vehicle.color = form.color.data.strip() if form.color.data else None
        vehicle.mileage = form.mileage.data
        vehicle.client_name = form.client_name.data.strip()
        vehicle.client_phone = form.client_phone.data.strip() if form.client_phone.data else None
        vehicle.client_email = form.client_email.data.strip() if form.client_email.data else None
        vehicle.problem_description = form.problem_description.data.strip()
        vehicle.diagnosis = form.diagnosis.data.strip() if form.diagnosis.data else None
        vehicle.work_to_do = form.work_to_do.data.strip() if form.work_to_do.data else None
        vehicle.parts_needed = form.parts_needed.data.strip() if form.parts_needed.data else None
        vehicle.status = form.status.data
        vehicle.estimated_cost = form.estimated_cost.data
        vehicle.final_cost = form.final_cost.data
        
        if vehicle.status == Repair.STATUS_ENTREGADO and not vehicle.delivery_date:
            vehicle.delivery_date = datetime.utcnow()
        elif vehicle.status == Repair.STATUS_LISTO and not vehicle.completion_date:
            vehicle.completion_date = datetime.utcnow()
            
        db.session.commit()
        flash(f'Datos del vehículo [{vehicle.formatted_plate}] actualizados.', 'success')
        return redirect(url_for('repairs.view', id=vehicle.id))
        
    elif request.method == 'GET':
        form.license_plate.data = vehicle.license_plate
        form.brand.data = vehicle.brand
        form.model.data = vehicle.model
        form.year.data = vehicle.year
        form.color.data = vehicle.color
        form.mileage.data = vehicle.mileage
        form.client_name.data = vehicle.client_name
        form.client_phone.data = vehicle.client_phone
        form.client_email.data = vehicle.client_email
        form.problem_description.data = vehicle.problem_description
        form.diagnosis.data = vehicle.diagnosis
        form.work_to_do.data = vehicle.work_to_do
        form.parts_needed.data = vehicle.parts_needed
        form.status.data = vehicle.status
        form.estimated_cost.data = vehicle.estimated_cost
        form.final_cost.data = vehicle.final_cost
        
    return render_template('repairs/edit.html', form=form, vehicle=vehicle)


@bp.route('/<int:id>/status/<new_status>', methods=['POST', 'GET'])
@login_required
def change_status(id, new_status):
    """Cambio rápido de estado con un clic."""
    vehicle = Repair.query.get_or_404(id)
    valid_statuses = [choice[0] for choice in Repair.STATUS_CHOICES]
    
    if new_status in valid_statuses:
        vehicle.status = new_status
        if new_status == Repair.STATUS_ENTREGADO:
            vehicle.delivery_date = datetime.utcnow()
        elif new_status == Repair.STATUS_LISTO:
            vehicle.completion_date = datetime.utcnow()
            
        db.session.commit()
        flash(f'Estado del vehículo [{vehicle.formatted_plate}] cambiado a: {vehicle.get_status_display()}', 'info')
    else:
        flash('Estado no válido.', 'danger')
        
    # Redirigir según el referer o a la ficha
    next_page = request.referrer or url_for('repairs.view', id=vehicle.id)
    return redirect(next_page)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Eliminar registro de vehículo."""
    vehicle = Repair.query.get_or_404(id)
    plate = vehicle.formatted_plate
    db.session.delete(vehicle)
    db.session.commit()
    flash(f'Vehículo [{plate}] eliminado del registro.', 'warning')
    return redirect(url_for('repairs.index'))