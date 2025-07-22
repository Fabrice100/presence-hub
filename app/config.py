import os
from datetime import timedelta

class Config:
    """Configuration de l'application"""
    # Clé secrète pour la sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-tres-secrete'
    
    # Configuration Base de données
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration Email avec Mailtrap
    MAIL_SERVER = 'sandbox.smtp.mailtrap.io'
    MAIL_PORT = 2525  # Utilisons le port 2525 qui est le plus stable
    MAIL_USE_TLS = True
    MAIL_USERNAME = '1a7b198de7ad5e'  # Votre username Mailtrap
    MAIL_PASSWORD = '5932cf0f1347df'            # Votre password Mailtrap
    MAIL_DEFAULT_SENDER = 'PresenceHub <noreply@presencehub.com>'
    
    # Configuration OTP
    OTP_EXPIRATION = timedelta(minutes=5)