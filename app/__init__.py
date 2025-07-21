# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from .config import Config

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

# Définir le user_loader avant create_app
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

def create_app():
    """Création et configuration de l'application Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Configuration login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

    with app.app_context():
        # Import des modèles
        from .models.user import User
        from .models.pointage import Pointage
        
        # Import et enregistrement des blueprints
        from .routes.auth_routes import auth_bp
        from .routes.employee_routes import employee_bp
        from .routes.admin_routes import admin_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(employee_bp)
        app.register_blueprint(admin_bp)

        # Création des tables
        db.create_all()

    return app