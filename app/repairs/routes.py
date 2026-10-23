# app/repairs/routes.py
"""
Rutas para la gestión de vehículos y reparaciones en el Taller Mecánico Don Orlando.
"""

import os
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.repairs import bp
from app.repairs.forms import RepairForm, DiagnosisWorkForm, SearchForm
from app.repairs.utils import generate_proforma_pdf
from app.models import Repair, RepairItem
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


@bp.route('/<int:id>/proforma', methods=['GET', 'POST'])
@login_required
def proforma(id):
    """Cargar o editar los ítems a reparar (Mano de Obra o Repuesto) para la Proforma / Presupuesto."""
    vehicle = Repair.query.get_or_404(id)
    
    if request.method == 'POST':
        descriptions = request.form.getlist('item_description[]')
        prices = request.form.getlist('item_price[]')
        types = request.form.getlist('item_type[]')
        diagnosis_text = request.form.get('diagnosis', '').strip()
        notes_text = request.form.get('parts_needed', '').strip()
        
        # Si types viene vacío o con menos elementos, rellenar con 'mano_obra'
        while len(types) < len(descriptions):
            types.append(RepairItem.TYPE_MANO_OBRA)
            
        # Actualizar diagnóstico y observaciones si se modificaron desde esta pantalla
        if diagnosis_text:
            vehicle.diagnosis = diagnosis_text
            if not vehicle.diagnosis_date:
                vehicle.diagnosis_date = datetime.utcnow()
        if 'parts_needed' in request.form:
            vehicle.parts_needed = notes_text if notes_text else None
            
        # Reemplazar los ítems actuales por las nuevas filas válidas
        RepairItem.query.filter_by(repair_id=vehicle.id).delete()
        
        total_cost = 0.0
        work_lines = []
        valid_idx = 0
        
        for desc, raw_price, raw_type in zip(descriptions, prices, types):
            clean_desc = (desc or '').strip()
            if not clean_desc:
                continue
            try:
                clean_price = float(str(raw_price).replace(',', '.').strip() or 0.0)
            except ValueError:
                clean_price = 0.0
                
            item_type = raw_type if raw_type in (RepairItem.TYPE_MANO_OBRA, RepairItem.TYPE_REPUESTO) else RepairItem.TYPE_MANO_OBRA
            
            valid_idx += 1
            item = RepairItem(
                repair_id=vehicle.id,
                item_type=item_type,
                description=clean_desc,
                price=max(0.0, clean_price),
                order_index=valid_idx
            )
            db.session.add(item)
            total_cost += max(0.0, clean_price)
            type_prefix = "[Repuesto]" if item_type == RepairItem.TYPE_REPUESTO else "[Mano de Obra]"
            work_lines.append(f"• {type_prefix} {clean_desc}")
            
        # Sincronizar presupuesto estimado y resumen de trabajo a realizar
        vehicle.estimated_cost = total_cost
        if work_lines:
            vehicle.work_to_do = "\n".join(work_lines)
        if vehicle.status == Repair.STATUS_INGRESADO and valid_idx > 0:
            vehicle.status = Repair.STATUS_DIAGNOSTICADO
            
        db.session.commit()
        
        # Generar el PDF actualizado inmediatamente para tenerlo listo
        try:
            generate_proforma_pdf(vehicle)
        except Exception as e:
            print(f"Aviso generando PDF tras guardar proforma: {e}")
            
        action = request.form.get('action', 'save')
        if action == 'save_and_download':
            return redirect(url_for('repairs.proforma_pdf', id=vehicle.id, download=1))
            
        flash(f'¡Proforma / Presupuesto de [{vehicle.formatted_plate}] guardado con éxito! ({valid_idx} ítems - Total: ${total_cost:,.0f})', 'success')
        return redirect(url_for('repairs.proforma', id=vehicle.id))
        
    return render_template('repairs/proforma.html', vehicle=vehicle)


@bp.route('/<int:id>/proforma/pdf')
@login_required
def proforma_pdf(id):
    """Genera y sirve el archivo PDF de la Proforma (para descargar o compartir por WhatsApp)."""
    vehicle = Repair.query.get_or_404(id)
    download = request.args.get('download', '1') == '1'
    
    try:
        pdf_path = generate_proforma_pdf(vehicle)
        safe_plate = vehicle.clean_plate(vehicle.license_plate) or f"Auto_{vehicle.id}"
        download_name = f"Proforma_{safe_plate}_{vehicle.brand}_{vehicle.model}.pdf".replace(' ', '_')
        
        return send_file(
            pdf_path,
            as_attachment=download,
            download_name=download_name,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error al generar el PDF de la proforma: {str(e)}', 'danger')
        return redirect(url_for('repairs.proforma', id=vehicle.id))


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
