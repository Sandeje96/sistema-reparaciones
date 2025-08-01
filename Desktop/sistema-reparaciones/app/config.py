# app/config.py
"""
Configuración de la aplicación del Sistema de Gestión de Reparaciones.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base de la aplicación."""
    
    # Clave secreta para formularios y sesiones
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-por-defecto-cambiar-en-produccion'
    
    # Configuración de base de datos
    # Para Railway, usar DATABASE_URL si está disponible
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///reparaciones.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de la aplicación
    APP_NAME = os.environ.get('APP_NAME') or 'Sistema de Reparaciones'
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or 'Tu Taller'
    
    # Paginación
    REPAIRS_PER_PAGE = int(os.environ.get('REPAIRS_PER_PAGE') or 20)
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16 * 1024 * 1024)  # 16MB
    
    # Configuración de WTF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora

class DevelopmentConfig(Config):
    """Configuración para desarrollo."""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Configuración para producción."""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # En producción, forzar HTTPS
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        PREFERRED_URL_SCHEME = 'https'

class TestingConfig(Config):
    """Configuración para testing."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig if os.environ.get('RAILWAY_ENVIRONMENT') else DevelopmentConfig
}