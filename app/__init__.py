from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from .config import Config
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

def create_app():
    """Fonction de création et configuration de l'application Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    print("DB URI:", app.config["SQLALCHEMY_DATABASE_URI"])
    
    # Initialisation des extensions avec l'app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configuration du login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    with app.app_context():
        # Import des modèles
        from .models.user import User
        from .models.pointage import Pointage
        from .models.conge import Conge  # Nouveau modèle
        
        # Import des routes
        from .routes.auth_routes import auth_bp
        from .routes.employee_routes import employee_bp
        from .routes.admin_routes import admin_bp
        from .routes.conge_routes import conge_bp  # Nouvelles routes
        
        # Enregistrement des blueprints
        app.register_blueprint(auth_bp)
        app.register_blueprint(employee_bp)
        app.register_blueprint(admin_bp)
        app.register_blueprint(conge_bp)  # Nouveau blueprint
        
        # Création des tables
        db.create_all()
        
        print("Tables créées (ou déjà existantes)")
        # Création d'un admin par défaut si aucun n'existe
        try:
            if not User.query.filter_by(role='admin').first():
                admin = User(
                    matricule='ADMIN001',
                    email='admin@presencehub.com',
                    nom='Admin',
                    prenom='System',
                    role='admin',
                    is_active=True,
                    premiere_connexion=False
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                logger.info('Compte administrateur créé avec succès.')
        except Exception as e:
            logger.error(f'Erreur lors de la création du compte admin: {str(e)}')
            db.session.rollback()
            
    return app