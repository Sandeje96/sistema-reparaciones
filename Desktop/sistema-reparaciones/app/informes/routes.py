# app/informes/routes.py
"""
Rutas para gestión de informes técnicos.
"""

import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.informes import bp
from app.informes.forms import TechnicalReportForm, SearchReportForm
from app.informes.utils import generate_report_pdf, save_uploaded_image, delete_report_files
from app.models import TechnicalReport
from app import db

@bp.route('/')
@login_required
def index():
    """Lista de informes técnicos."""
    
    # Formulario de búsqueda
    search_form = SearchReportForm()
    
    # Parámetros de búsqueda
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Construir query base
    query = TechnicalReport.query
    
    # Aplicar filtro de búsqueda
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                TechnicalReport.insured_company.ilike(search_term),
                TechnicalReport.claim_number.ilike(search_term),
                TechnicalReport.brand.ilike(search_term),
                TechnicalReport.model.ilike(search_term),
                TechnicalReport.device_type.ilike(search_term),
                TechnicalReport.insurance_company.ilike(search_term)
            )
        )
    
    # Ordenar por fecha de creación (más recientes primero)
    query = query.order_by(TechnicalReport.created_at.desc())
    
    # Paginación
    per_page = 15
    reports = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Prellenar formulario de búsqueda
    if request.method == 'GET':
        search_form.search.data = search
    
    return render_template('informes/index.html', 
                         reports=reports, 
                         search_form=search_form,
                         search=search)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Crear nuevo informe técnico."""
    
    form = TechnicalReportForm()
    
    if form.validate_on_submit():
        try:
            # Crear nuevo informe
            report = TechnicalReport(
                insurance_company=form.insurance_company.data,
                insured_company=form.insured_company.data,
                claim_number=form.claim_number.data,
                incident_date=form.incident_date.data,
                device_type=form.device_type.data,
                brand=form.brand.data,
                model=form.model.data,
                serial_number=form.serial_number.data,
                problem_description=form.problem_description.data,
                technical_diagnosis=form.technical_diagnosis.data,
                diagnosis_price=form.diagnosis_price.data,
                repair_price=form.repair_price.data,
                technician_name=form.technician_name.data,
                professional_license=form.professional_license.data,
                created_by=current_user.id
            )
            
            # Guardar en base de datos para obtener ID
            db.session.add(report)
            db.session.flush()  # Flush para obtener el ID sin commit
            
            # Procesar imágenes subidas
            images_saved = 0
            for i, image_field in enumerate([form.image1, form.image2, form.image3], 1):
                if image_field.data and image_field.data.filename:
                    filename = save_uploaded_image(image_field.data, report.uuid, i)
                    if filename:
                        setattr(report, f'image{i}_filename', filename)
                        images_saved += 1
            
            # Commit final
            db.session.commit()
            
            flash(f'Informe técnico creado exitosamente. Se guardaron {images_saved} imágenes.', 'success')
            return redirect(url_for('informes.view', id=report.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el informe. Inténtalo de nuevo.', 'error')
            print(f"Error creando informe: {e}")  # Para debugging
    
    return render_template('informes/create.html', title='Crear Informe Técnico', form=form)

@bp.route('/view/<int:id>')
@login_required
def view(id):
    """Ver detalles de informe técnico."""
    
    report = TechnicalReport.query.get_or_404(id)
    return render_template('informes/view.html', report=report)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar informe técnico existente."""
    
    report = TechnicalReport.query.get_or_404(id)
    form = TechnicalReportForm(obj=report)
    
    if form.validate_on_submit():
        try:
            # Actualizar datos
            form.populate_obj(report)
            report.updated_at = datetime.utcnow()
            
            # Procesar nuevas imágenes
            images_updated = 0
            for i, image_field in enumerate([form.image1, form.image2, form.image3], 1):
                if image_field.data and image_field.data.filename:
                    # Eliminar imagen anterior si existe
                    old_filename = getattr(report, f'image{i}_filename')
                    if old_filename:
                        old_path = os.path.join('app', 'static', 'uploads', 'informes', old_filename)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except OSError:
                                pass
                    
                    # Guardar nueva imagen
                    filename = save_uploaded_image(image_field.data, report.uuid, i)
                    if filename:
                        setattr(report, f'image{i}_filename', filename)
                        images_updated += 1
            
            db.session.commit()
            
            message = 'Informe técnico actualizado exitosamente.'
            if images_updated > 0:
                message += f' Se actualizaron {images_updated} imágenes.'
            
            flash(message, 'success')
            return redirect(url_for('informes.view', id=report.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el informe. Inténtalo de nuevo.', 'error')
            print(f"Error actualizando informe: {e}")  # Para debugging
    
    return render_template('informes/edit.html', title='Editar Informe Técnico', form=form, report=report)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Eliminar informe técnico."""
    
    report = TechnicalReport.query.get_or_404(id)
    
    try:
        # Eliminar archivos asociados
        delete_report_files(report)
        
        # Eliminar de base de datos
        claim_number = report.claim_number
        device_type = report.device_type
        db.session.delete(report)
        db.session.commit()
        
        flash(f'Informe técnico eliminado: {claim_number} - {device_type}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el informe. Inténtalo de nuevo.', 'error')
        print(f"Error eliminando informe: {e}")  # Para debugging
    
    return redirect(url_for('informes.index'))

@bp.route('/generate-pdf/<int:id>')
@login_required
def generate_pdf(id):
    """Generar y descargar PDF del informe técnico."""
    
    report = TechnicalReport.query.get_or_404(id)
    
    try:
        print(f"🔍 Generando PDF para informe ID: {id}")
        
        # Verificar que existan las carpetas
        output_dir = os.path.join('app', 'static', 'reports')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"📁 Carpeta creada: {output_dir}")
        
        # Generar PDF
        print("📄 Llamando a generate_report_pdf...")
        pdf_path = generate_report_pdf(report)
        print(f"📄 PDF generado en: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            error_msg = f'PDF no encontrado en: {pdf_path}'
            print(f"❌ {error_msg}")
            flash(error_msg, 'error')
            return redirect(url_for('informes.view', id=id))
        
        # Verificar tamaño del archivo
        file_size = os.path.getsize(pdf_path)
        print(f"📊 Tamaño del PDF: {file_size} bytes")
        
        if file_size == 0:
            flash('Error: El PDF generado está vacío', 'error')
            return redirect(url_for('informes.view', id=id))
        
        # Nombre para descarga
        safe_claim = "".join(c for c in report.claim_number if c.isalnum() or c in (' ', '-', '_')).rstrip()
        download_name = f"Informe_Tecnico_{safe_claim}.pdf"
        print(f"💾 Nombre de descarga: {download_name}")
        
        # Enviar archivo
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        error_msg = f'Error generando PDF: {str(e)}'
        print(f"❌ {error_msg}")
        flash(error_msg, 'error')
        
        # Mostrar traceback completo para debugging
        import traceback
        traceback.print_exc()
        
        return redirect(url_for('informes.view', id=id))

@bp.route('/preview-pdf/<int:id>')
@login_required
def preview_pdf(id):
    """Vista previa del PDF en el navegador."""
    
    report = TechnicalReport.query.get_or_404(id)
    
    try:
        # Generar PDF
        pdf_path = generate_report_pdf(report)
        
        if not os.path.exists(pdf_path):
            flash('Error generando el PDF. Inténtalo de nuevo.', 'error')
            return redirect(url_for('informes.view', id=id))
        
        # Enviar para vista previa
        return send_file(
            pdf_path,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash('Error generando el PDF. Inténtalo de nuevo.', 'error')
        print(f"Error generando PDF: {e}")  # Para debugging
        return redirect(url_for('informes.view', id=id))

@bp.route('/delete-image/<int:id>/<int:image_num>', methods=['POST'])
@login_required
def delete_image(id, image_num):
    """Eliminar imagen específica de un informe."""
    
    if image_num not in [1, 2, 3]:
        return jsonify({'success': False, 'message': 'Número de imagen inválido'})
    
    report = TechnicalReport.query.get_or_404(id)
    
    try:
        # Obtener nombre del archivo
        filename_attr = f'image{image_num}_filename'
        filename = getattr(report, filename_attr)
        
        if not filename:
            return jsonify({'success': False, 'message': 'No hay imagen para eliminar'})
        
        # Eliminar archivo físico
        file_path = os.path.join('app', 'static', 'uploads', 'informes', filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Actualizar base de datos
        setattr(report, filename_attr, None)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Imagen {image_num} eliminada'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error eliminando la imagen'})

@bp.route('/stats')
@login_required
def stats():
    """API para estadísticas del módulo de informes."""
    
    try:
        # Estadísticas básicas
        total_reports = TechnicalReport.query.count()
        
        # Informes por mes (últimos 6 meses)
        from datetime import datetime, timedelta
        from sqlalchemy import func, extract
        
        six_months_ago = datetime.now() - timedelta(days=180)
        
        monthly_stats = db.session.query(
            extract('year', TechnicalReport.created_at).label('year'),
            extract('month', TechnicalReport.created_at).label('month'),
            func.count(TechnicalReport.id).label('count')
        ).filter(
            TechnicalReport.created_at >= six_months_ago
        ).group_by(
            extract('year', TechnicalReport.created_at),
            extract('month', TechnicalReport.created_at)
        ).all()
        
        # Top 5 marcas más reportadas
        top_brands = db.session.query(
            TechnicalReport.brand,
            func.count(TechnicalReport.id).label('count')
        ).group_by(
            TechnicalReport.brand
        ).order_by(
            func.count(TechnicalReport.id).desc()
        ).limit(5).all()
        
        return jsonify({
            'success': True,
            'total_reports': total_reports,
            'monthly_stats': [{'year': int(s.year), 'month': int(s.month), 'count': s.count} for s in monthly_stats],
            'top_brands': [{'brand': s.brand, 'count': s.count} for s in top_brands]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error obteniendo estadísticas'})