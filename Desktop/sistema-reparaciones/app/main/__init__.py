# app/main/__init__.py
"""
Blueprint principal para rutas generales del sistema.
"""

from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes