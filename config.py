# app/config.py
"""
Configuración de la aplicación del Sistema de Gestión de Reparaciones.
Basado en configuración probada que funciona en Railway.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener directorio base del proyecto (no del módulo app)
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    """Configuración base de la aplicación."""
    
    # Clave secreta para formularios y sesiones - CRÍTICO para seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
    
    # Configuración de base de datos
    # Para Railway, usar DATABASE_URL si está disponible
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///reparaciones.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True if os.environ.get('FLASK_ENV') == 'production' else False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuración de Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = True if os.environ.get('FLASK_ENV') == 'production' else False
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Configuración de la aplicación
    APP_NAME = os.environ.get('APP_NAME') or 'Sistema de Reparaciones'
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or 'Tu Taller'
    
    # Paginación
    REPAIRS_PER_PAGE = int(os.environ.get('REPAIRS_PER_PAGE') or 20)
    RECORDS_PER_PAGE = 25
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16 * 1024 * 1024)  # 16MB
    
    # Configuración de WTF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora
    
    # Configuración de zona horaria
    TIMEZONE = os.environ.get('TIMEZONE') or 'America/Argentina/Buenos_Aires'
    
    # Configuración de logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    
    @staticmethod
    def init_app(app):
        """Método para inicializar configuraciones específicas de la aplicación."""
        pass

class DevelopmentConfig(Config):
    """Configuración para desarrollo."""
    DEBUG = True
    FLASK_ENV = 'development'
    
    # Base de datos SQLite para desarrollo local
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DEV_DATABASE_URL') or 
        'sqlite:///' + os.path.join(basedir, 'reparaciones_dev.db')
    )
    
    # Configuración menos estricta para desarrollo
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Logging más detallado en desarrollo
    SQLALCHEMY_ECHO = False  # Cambiar a True si quieres ver todas las queries SQL
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Configuración adicional para desarrollo
        import logging
        from logging import StreamHandler
        
        if not app.debug and not app.testing:
            stream_handler = StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)

class ProductionConfig(Config):
    """Configuración para producción."""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Base de datos PostgreSQL en producción
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 
        os.environ.get('POSTGRES_URL') or
        'postgresql://localhost/reparaciones_prod'
    )
    
    # En producción, forzar HTTPS
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        PREFERRED_URL_SCHEME = 'https'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # ⭐ CLAVE: Arreglar URL de PostgreSQL si viene de Railway
        database_url = app.config['SQLALCHEMY_DATABASE_URI']
        if database_url and database_url.startswith('postgres://'):
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace(
                'postgres://', 'postgresql://'
            )
        
        # Configuración de logging para producción
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        
        if not app.debug and not app.testing:
            if app.config['LOG_TO_STDOUT']:
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(logging.INFO)
                app.logger.addHandler(stream_handler)
            else:
                # Crear directorio de logs si no existe
                if not os.path.exists('logs'):
                    os.mkdir('logs')
                file_handler = RotatingFileHandler(
                    'logs/reparaciones.log', maxBytes=10240, backupCount=10
                )
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                ))
                file_handler.setLevel(logging.INFO)
                app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Sistema de Reparaciones iniciado')

class TestingConfig(Config):
    """Configuración para testing."""
    TESTING = True
    DEBUG = False
    
    # Base de datos en memoria para pruebas
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Configuración de sesiones para pruebas
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Paginación reducida para pruebas
    REPAIRS_PER_PAGE = 5
    RECORDS_PER_PAGE = 5
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Configuración adicional para pruebas
        import logging
        app.logger.setLevel(logging.CRITICAL)

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig if os.environ.get('RAILWAY_ENVIRONMENT') else DevelopmentConfig
}