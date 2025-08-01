# app/informes/__init__.py
"""
Blueprint de informes técnicos - funcionalidad para generar PDFs de seguros.
"""

from flask import Blueprint

bp = Blueprint('informes', __name__)

from app.informes import routes