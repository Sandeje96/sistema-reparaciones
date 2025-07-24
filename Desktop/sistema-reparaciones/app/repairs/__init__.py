# app/repairs/__init__.py
"""
Blueprint de reparaciones - funcionalidad principal del sistema.
"""

from flask import Blueprint

bp = Blueprint('repairs', __name__)

from app.repairs import routes