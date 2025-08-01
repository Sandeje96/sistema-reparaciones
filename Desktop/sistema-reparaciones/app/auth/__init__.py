# app/auth/__init__.py
"""
Blueprint de autenticación para el sistema.
"""

from flask import Blueprint

bp = Blueprint('auth', __name__)

from app.auth import routes