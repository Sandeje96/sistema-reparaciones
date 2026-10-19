# app/repairs/utils.py
"""
Utilidades para generar el PDF de Proforma / Presupuesto en el Taller Mecánico Don Orlando.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


def format_currency(amount):
    """Formatea un monto numérico como moneda legible (ej: $ 185.000,00 o $ 185.000)."""
    if amount is None:
        amount = 0.0
    if float(amount).is_integer():
        return f"$ {int(amount):,}".replace(",", ".")
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {formatted}"


def generate_proforma_pdf(vehicle):
    """
    Genera un archivo PDF de Proforma / Presupuesto para un vehículo y sus ítems.
    Retorna la ruta absoluta del PDF generado.
    """
    output_dir = os.path.join('app', 'static', 'reports')
    os.makedirs(output_dir, exist_ok=True)

    safe_plate = vehicle.clean_plate(vehicle.license_plate) or f"auto_{vehicle.id}"
    filename = f"Proforma_{safe_plate}_{vehicle.id}.pdf"
    output_path = os.path.abspath(os.path.join(output_dir, filename))

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"Presupuesto Proforma - {vehicle.formatted_plate}",
        author="Taller Mecánico Don Orlando"
    )

    styles = getSampleStyleSheet()
    primary_dark = HexColor('#0F172A')
    brand_orange = HexColor('#C2410C')
    accent_blue = HexColor('#0284C7')
    light_bg = HexColor('#F8FAFC')
    border_color = HexColor('#CBD5E1')
    muted_text = HexColor('#64748B')

    # Estilos tipográficos
    title_style = ParagraphStyle(
        'ShopTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_dark
    )
    subtitle_style = ParagraphStyle(
        'ShopSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=brand_orange
    )
    doc_type_style = ParagraphStyle(
        'DocType',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_RIGHT,
        textColor=accent_blue
    )
    meta_right_style = ParagraphStyle(
        'MetaRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        alignment=TA_RIGHT,
        textColor=muted_text
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=primary_dark,
        spaceBefore=6,
        spaceAfter=4
    )
    cell_label_style = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=muted_text
    )
    cell_value_style = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=primary_dark
    )
    body_text_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=primary_dark
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=white
    )
    table_header_right = ParagraphStyle(
        'TableHeaderRight',
        parent=table_header_style,
        alignment=TA_RIGHT
    )
    item_desc_style = ParagraphStyle(
        'ItemDesc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=primary_dark
    )
    item_price_style = ParagraphStyle(
        'ItemPrice',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        alignment=TA_RIGHT,
        textColor=primary_dark
    )
    total_label_style = ParagraphStyle(
        'TotalLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        alignment=TA_RIGHT,
        textColor=primary_dark
    )
    total_value_style = ParagraphStyle(
        'TotalValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        alignment=TA_RIGHT,
        textColor=brand_orange
    )
    footer_style = ParagraphStyle(
        'FooterNote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=muted_text
    )

    story = []

    # 1. Encabezado con Logo y Datos de Proforma
    logo_path = os.path.join('app', 'static', 'images', 'logo_don_orlando.jpg')
    if os.path.exists(logo_path):
        try:
            logo_Flowable = Image(logo_path, width=22 * mm, height=22 * mm)
        except Exception:
            logo_Flowable = Paragraph("", body_text_style)
    else:
        logo_Flowable = Paragraph("", body_text_style)

    shop_info = [
        Paragraph("TALLER MECÁNICO DON ORLANDO", title_style),
        Paragraph("SERVICIO MECÁNICO INTEGRAL Y DIAGNÓSTICO", subtitle_style),
    ]

    issue_date_str = datetime.now().strftime('%d/%m/%Y')
    doc_info = [
        Paragraph("PRESUPUESTO / PROFORMA", doc_type_style),
        Paragraph(f"N° Orden: <b>#{vehicle.id:04d}</b>", meta_right_style),
        Paragraph(f"Fecha: <b>{issue_date_str}</b>", meta_right_style),
    ]

    if os.path.exists(logo_path):
        header_table = Table(
            [[logo_Flowable, shop_info, doc_info]],
            colWidths=[26 * mm, 92 * mm, 60 * mm]
        )
    else:
        header_table = Table(
            [[shop_info, doc_info]],
            colWidths=[118 * mm, 60 * mm]
        )

    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_dark, spaceBefore=2 * mm, spaceAfter=5 * mm))

    # 2. Cuadro de Datos del Cliente y del Vehículo
    year_str = f" ({vehicle.year})" if vehicle.year else ""
    km_str = f"{vehicle.mileage:,}".replace(",", ".") + " km" if vehicle.mileage else "S/D"
    phone_str = vehicle.client_phone or "No registrado"

    info_data = [
        [
            Paragraph("CLIENTE", cell_label_style),
            Paragraph("TELÉFONO / WHATSAPP", cell_label_style),
            Paragraph("VEHÍCULO", cell_label_style),
            Paragraph("PATENTE / DOMINIO", cell_label_style),
        ],
        [
            Paragraph(vehicle.client_name, cell_value_style),
            Paragraph(phone_str, cell_value_style),
            Paragraph(f"{vehicle.brand} {vehicle.model}{year_str}", cell_value_style),
            Paragraph(f"{vehicle.formatted_plate} ({km_str})", cell_value_style),
        ]
    ]

    info_table = Table(info_data, colWidths=[48 * mm, 40 * mm, 48 * mm, 42 * mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 5 * mm))

    # 3. Diagnóstico / Motivo (si está cargado)
    if vehicle.diagnosis:
        story.append(Paragraph("DIAGNÓSTICO / REVISIÓN TÉCNICA", section_title_style))
        diag_text = vehicle.diagnosis.replace('\n', '<br/>')
        diag_box = Table([[Paragraph(diag_text, body_text_style)]], colWidths=[178 * mm])
        diag_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F0F9FF')),
            ('BOX', (0, 0), (-1, -1), 0.8, HexColor('#BAE6FD')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(diag_box)
        story.append(Spacer(1, 5 * mm))

    # 4. Tabla de Ítems a Reparar / Presupuesto
    story.append(Paragraph("DETALLE DE ÍTEMS Y TRABAJOS PRESUPUESTADOS", section_title_style))

    items_rows = [
        [
            Paragraph("#", table_header_style),
            Paragraph("Descripción del Ítem / Trabajo / Repuesto", table_header_style),
            Paragraph("Importe", table_header_right),
        ]
    ]

    total_amount = 0.0
    if vehicle.items:
        for idx, item in enumerate(vehicle.items, start=1):
            price_val = float(item.price or 0.0)
            total_amount += price_val
            items_rows.append([
                Paragraph(str(idx), body_text_style),
                Paragraph(item.description, item_desc_style),
                Paragraph(format_currency(price_val), item_price_style),
            ])
    else:
        # Si aún no cargó filas individuales pero tiene work_to_do o estimated_cost
        fallback_desc = vehicle.work_to_do or vehicle.problem_description or "Servicio de reparación general"
        total_amount = float(vehicle.estimated_cost or 0.0)
        items_rows.append([
            Paragraph("1", body_text_style),
            Paragraph(fallback_desc.replace('\n', '<br/>'), item_desc_style),
            Paragraph(format_currency(total_amount), item_price_style),
        ])

    # Fila de Total General
    items_rows.append([
        Paragraph("", body_text_style),
        Paragraph("TOTAL PRESUPUESTADO:", total_label_style),
        Paragraph(format_currency(total_amount), total_value_style),
    ])

    items_table = Table(items_rows, colWidths=[12 * mm, 124 * mm, 42 * mm], repeatRows=1)

    table_styles = [
        # Cabecera
        ('BACKGROUND', (0, 0), (-1, 0), primary_dark),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        # Filas de ítems
        ('TOPPADDING', (0, 1), (-1, -2), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -2), 7),
        ('GRID', (0, 0), (-1, -2), 0.5, border_color),

        # Fila de Total
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#FFF7ED')),
        ('BOX', (0, -1), (-1, -1), 1.2, brand_orange),
        ('TOPPADDING', (0, -1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 9),
    ]

    # Alternar colores de fila para lectura fácil
    for row_idx in range(1, len(items_rows) - 1):
        if row_idx % 2 == 0:
            table_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), light_bg))

    items_table.setStyle(TableStyle(table_styles))
    story.append(items_table)

    # 5. Observaciones / Repuestos adicionales si existen
    if vehicle.parts_needed:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("OBSERVACIONES / NOTAS ADICIONALES", section_title_style))
        notes_box = Table([[Paragraph(vehicle.parts_needed.replace('\n', '<br/>'), body_text_style)]], colWidths=[178 * mm])
        notes_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_bg),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(notes_box)

    # 6. Pie de documento
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=2 * mm, spaceAfter=3 * mm))
    story.append(Paragraph(
        "Documento emitido en carácter de Proforma / Presupuesto por Taller Mecánico Don Orlando.",
        footer_style
    ))

    doc.build(story)
    return output_path
