# app/repairs/routes.py
"""
Rutas para gestión de reparaciones.
"""

from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.repairs import bp
from app.repairs.forms import RepairForm, SearchForm, QuickStatusForm
from app.models import Repair
from app import db

@bp.route('/')
@login_required
def index():
    """Lista principal de reparaciones."""
    
    # Formulario de búsqueda
    search_form = SearchForm()
    
    # Parámetros de búsqueda y filtros
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status_filter', '')
    priority_filter = request.args.get('priority_filter', '')
    
    # Construir query base
    query = Repair.query
    
    # Aplicar filtro de búsqueda
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Repair.client_name.ilike(search_term),
                Repair.device_type.ilike(search_term),
                Repair.brand.ilike(search_term),
                Repair.model.ilike(search_term),
                Repair.problem_description.ilike(search_term)
            )
        )
    
    # Aplicar filtro de estado
    if status_filter:
        if status_filter == 'active':
            query = query.filter(~Repair.status.in_([Repair.DELIVERED, Repair.NO_REPAIR]))
        else:
            query = query.filter(Repair.status == status_filter)
    
    # Aplicar filtro de prioridad
    if priority_filter:
        from datetime import timedelta
        now = datetime.utcnow()
        
        if priority_filter == 'high':
            cutoff_date = now - timedelta(days=15)
            query = query.filter(Repair.entry_date <= cutoff_date)
        elif priority_filter == 'medium':
            start_date = now - timedelta(days=14)
            end_date = now - timedelta(days=7)
            query = query.filter(Repair.entry_date.between(end_date, start_date))
        elif priority_filter == 'low':
            cutoff_date = now - timedelta(days=7)
            query = query.filter(Repair.entry_date >= cutoff_date)
    
    # Ordenar por fecha de ingreso (más antiguos primero)
    query = query.order_by(Repair.entry_date.asc())
    
    # Paginación
    per_page = 20
    repairs = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Prellenar formulario de búsqueda
    if request.method == 'GET':
        search_form.search.data = search
        search_form.status_filter.data = status_filter
        search_form.priority_filter.data = priority_filter
    
    return render_template('repairs/index.html', 
                         repairs=repairs, 
                         search_form=search_form,
                         search=search,
                         status_filter=status_filter,
                         priority_filter=priority_filter)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Agregar nueva reparación."""
    
    form = RepairForm()
    form.status.data = Repair.PENDING_DIAGNOSIS  # Estado por defecto
    
    if form.validate_on_submit():
        repair = Repair(
            client_name=form.client_name.data,
            client_phone=form.client_phone.data,
            device_type=form.device_type.data,
            brand=form.brand.data,
            model=form.model.data,
            serial_number=form.serial_number.data,
            problem_description=form.problem_description.data,
            status=form.status.data,
            diagnosis_notes=form.diagnosis_notes.data,
            repair_cost=form.repair_cost.data,
            parts_needed=form.parts_needed.data,
            created_by=current_user.id
        )
        
        # Establecer fechas según el estado
        if form.status.data == Repair.DIAGNOSED:
            repair.diagnosis_date = datetime.utcnow()
        elif form.status.data in [Repair.READY_FOR_DELIVERY, Repair.DELIVERED]:
            repair.diagnosis_date = datetime.utcnow()
            repair.completion_date = datetime.utcnow()
            if form.status.data == Repair.DELIVERED:
                repair.delivery_date = datetime.utcnow()
        
        try:
            db.session.add(repair)
            db.session.commit()
            flash(f'Reparación agregada: {repair.client_name} - {repair.device_type}', 'success')
            return redirect(url_for('repairs.index'))
        except Exception as e:
            db.session.rollback()
            flash('Error al agregar la reparación. Inténtalo de nuevo.', 'error')
    
    return render_template('repairs/add.html', title='Agregar Reparación', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar reparación existente."""
    
    repair = Repair.query.get_or_404(id)
    form = RepairForm(obj=repair)
    
    if form.validate_on_submit():
        old_status = repair.status
        
        # Actualizar datos
        form.populate_obj(repair)
        repair.updated_at = datetime.utcnow()
        
        # Actualizar fechas según cambios de estado
        if old_status != form.status.data:
            if form.status.data == Repair.DIAGNOSED and not repair.diagnosis_date:
                repair.diagnosis_date = datetime.utcnow()
            elif form.status.data in [Repair.READY_FOR_DELIVERY] and not repair.completion_date:
                repair.completion_date = datetime.utcnow()
            elif form.status.data == Repair.DELIVERED and not repair.delivery_date:
                repair.delivery_date = datetime.utcnow()
        
        try:
            db.session.commit()
            flash(f'Reparación actualizada: {repair.client_name} - {repair.device_type}', 'success')
            return redirect(url_for('repairs.index'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la reparación. Inténtalo de nuevo.', 'error')
    
    return render_template('repairs/edit.html', title='Editar Reparación', form=form, repair=repair)

@bp.route('/view/<int:id>')
@login_required
def view(id):
    """Ver detalles de reparación."""
    
    repair = Repair.query.get_or_404(id)
    return render_template('repairs/view.html', repair=repair)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Eliminar reparación (solo entregadas o sin reparación)."""
    
    repair = Repair.query.get_or_404(id)
    
    # Solo permitir eliminar reparaciones entregadas o sin reparación
    if repair.status not in [Repair.DELIVERED, Repair.NO_REPAIR]:
        flash('Solo se pueden eliminar reparaciones entregadas o sin reparación.', 'error')
        return redirect(url_for('repairs.index'))
    
    try:
        client_name = repair.client_name
        device_type = repair.device_type
        db.session.delete(repair)
        db.session.commit()
        flash(f'Reparación eliminada: {client_name} - {device_type}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la reparación. Inténtalo de nuevo.', 'error')
    
    return redirect(url_for('repairs.index'))

@bp.route('/quick-status/<int:id>', methods=['POST'])
@login_required
def quick_status(id):
    """Cambio rápido de estado via AJAX."""
    
    repair = Repair.query.get_or_404(id)
    new_status = request.form.get('status')
    
    if new_status not in [choice[0] for choice in Repair.STATUS_CHOICES]:
        return jsonify({'success': False, 'message': 'Estado inválido'})
    
    old_status = repair.status
    repair.status = new_status
    repair.updated_at = datetime.utcnow()
    
    # Actualizar fechas según el nuevo estado
    if old_status != new_status:
        if new_status == Repair.DIAGNOSED and not repair.diagnosis_date:
            repair.diagnosis_date = datetime.utcnow()
        elif new_status == Repair.READY_FOR_DELIVERY and not repair.completion_date:
            repair.completion_date = datetime.utcnow()
        elif new_status == Repair.DELIVERED and not repair.delivery_date:
            repair.delivery_date = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Estado actualizado a: {repair.get_status_display()}',
            'new_status': repair.get_status_display(),
            'priority_class': repair.get_priority_class()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al actualizar el estado'})

@bp.route('/stats')
@login_required
def stats():
    """API para estadísticas del dashboard."""
    
    # Reparaciones activas por estado
    stats = {}
    for status_code, status_name in Repair.STATUS_CHOICES:
        if status_code not in [Repair.DELIVERED, Repair.NO_REPAIR]:
            count = Repair.query.filter_by(status=status_code).count()
            stats[status_code] = {
                'name': status_name,
                'count': count
            }
    
    # Prioridades
    from datetime import timedelta
    now = datetime.utcnow()
    
    urgent_date = now - timedelta(days=15)
    medium_start = now - timedelta(days=14)
    medium_end = now - timedelta(days=7)
    
    urgent_count = Repair.query.filter(
        Repair.entry_date <= urgent_date,
        ~Repair.status.in_([Repair.DELIVERED, Repair.NO_REPAIR])
    ).count()
    
    medium_count = Repair.query.filter(
        Repair.entry_date.between(medium_end, medium_start),
        ~Repair.status.in_([Repair.DELIVERED, Repair.NO_REPAIR])
    ).count()
    
    low_count = Repair.query.filter(
        Repair.entry_date >= medium_end,
        ~Repair.status.in_([Repair.DELIVERED, Repair.NO_REPAIR])
    ).count()
    
    priorities = {
        'urgent': urgent_count,
        'medium': medium_count,
        'low': low_count
    }
    
    return jsonify({
        'success': True,
        'stats': stats,
        'priorities': priorities
    })