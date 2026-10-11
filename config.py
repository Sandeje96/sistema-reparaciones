# config.py
"""
Configuración principal para Taller Mecánico Don Orlando.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


def resolve_database_uri(base_directory):
    """
    Resuelve la URI de la base de datos de manera robusta.
    Detecta automáticamente PostgreSQL en Railway y otros PaaS,
    o utiliza SQLite como fallback seguro sin fallar en localhost:5432.
    """
    db_url = (
        os.environ.get('DATABASE_URL') or
        os.environ.get('DATABASE_PRIVATE_URL') or
        os.environ.get('DATABASE_PUBLIC_URL') or
        os.environ.get('POSTGRES_URL') or
        os.environ.get('POSTGRESQL_URL')
    )
    
    if not db_url and os.environ.get('PGHOST'):
        pghost = os.environ.get('PGHOST')
        pguser = os.environ.get('PGUSER', 'postgres')
        pgpass = os.environ.get('PGPASSWORD', '')
        pgport = os.environ.get('PGPORT', '5432')
        pgdb = os.environ.get('PGDATABASE', 'railway')
        auth = f"{pguser}:{pgpass}@" if pgpass else f"{pguser}@"
        db_url = f"postgresql://{auth}{pghost}:{pgport}/{pgdb}"
        
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
        
    db_path = os.path.join(base_directory, 'taller.db')
    return f'sqlite:///{db_path}'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'don-orlando-secret-key-taller-2026'
    SQLALCHEMY_DATABASE_URI = resolve_database_uri(basedir)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True if os.environ.get('FLASK_ENV') == 'production' else False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = True if os.environ.get('FLASK_ENV') == 'production' else False
    REMEMBER_COOKIE_HTTPONLY = True
    
    APP_NAME = os.environ.get('APP_NAME') or 'Taller Mecánico Don Orlando'
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or 'Taller Mecánico Don Orlando'
    
    REPAIRS_PER_PAGE = int(os.environ.get('REPAIRS_PER_PAGE') or 20)
    RECORDS_PER_PAGE = 25
    
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16 * 1024 * 1024)
    
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    TIMEZONE = os.environ.get('TIMEZONE') or 'America/Argentina/Buenos_Aires'
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', '1')
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SQLALCHEMY_ECHO = False
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    SQLALCHEMY_DATABASE_URI = resolve_database_uri(basedir)
    
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        PREFERRED_URL_SCHEME = 'https'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_url.startswith('postgres://'):
            app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig if (os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLASK_ENV') == 'production') else DevelopmentConfig
}