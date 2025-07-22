import os
from datetime import timedelta
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

class Config:
    """Configuration de l'application"""
    # Clé secrète pour la sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-tres-secrete'
    
    # Configuration Base de données PostgreSQL
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration Email avec Mailtrap
    MAIL_SERVER = 'sandbox.smtp.mailtrap.io'
    MAIL_PORT = 2525  # Utilisons le port 2525 qui est le plus stable
    MAIL_USE_TLS = True
    MAIL_USERNAME = '1a7b198de7ad5e'  # Votre username Mailtrap
    MAIL_PASSWORD = '5932cf0f1347df'  # Votre password Mailtrap
    MAIL_DEFAULT_SENDER = 'PresenceHub <noreply@presencehub.com>'
    
    # Configuration OTP
    OTP_EXPIRATION = timedelta(minutes=5)

    # Configuration Application
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    DEBUG = True
    TESTING = False
    
    # Départements
    DEPARTMENTS = [
        ('IT', 'Informatique'),
        ('RH', 'Ressources Humaines'),
        ('FIN', 'Finance'),
        ('MKT', 'Marketing'),
        ('PROD', 'Production')
    ]

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    SECRET_KEY = os.getenv('SECRET_KEY')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/presencehub_test"
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}