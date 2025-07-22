from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from app.models.pointage import Pointage
import random
import string

class User(UserMixin, db.Model):
    """Modèle pour les utilisateurs"""
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(10), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255))  # Augmenté de 128 à 255
    role = db.Column(db.String(20), nullable=False)  # 'admin' ou 'employee'
    departement = db.Column(db.String(50))
    premiere_connexion = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relation avec les pointages
    pointages = db.relationship('Pointage', backref='employe', lazy=True)

    def set_password(self, password):
        """Hash et enregistre le mot de passe"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie si le mot de passe est correct"""
        return check_password_hash(self.password_hash, password)

    def get_status_jour(self):
        """Récupère le statut de présence du jour"""
        from datetime import date
        today = date.today()
        dernier_pointage = Pointage.query.filter_by(
            user_id=self.id,
            date=today
        ).order_by(Pointage.heure.desc()).first()
        
        if not dernier_pointage:
            return "Absent"
        return "Présent" if dernier_pointage.type == "arrivee" else "Parti"

    def can_pointer(self):
        """Vérifie si l'utilisateur peut pointer"""
        from datetime import date
        today = date.today()
        dernier_pointage = Pointage.query.filter_by(
            user_id=self.id,
            date=today
        ).order_by(Pointage.heure.desc()).first()

        if not dernier_pointage:
            return True, "arrivee"
        return True, "depart" if dernier_pointage.type == "arrivee" else "arrivee"

    @classmethod
    def create_employee(cls, form):
        """Crée un nouvel employé à partir des données du formulaire"""
        try:
            # Génère un matricule et un mot de passe temporaire
            matricule = cls.generate_matricule()
            temp_password = cls.generate_temp_password()
            
            # Crée l'employé
            employee = cls(
                matricule=matricule,
                nom=form.nom.data,
                prenom=form.prenom.data,
                email=form.email.data,
                departement=form.departement.data,
                role='employee',
                premiere_connexion=True,
                is_active=True
            )
            employee.set_password(temp_password)
            
            return employee, temp_password
        except Exception as e:
            print(f"Erreur création employé: {str(e)}")
            return None, None

    @staticmethod
    def generate_matricule(prefix='EMP'):
        """Génère un matricule unique"""
        while True:
            number = random.randint(1, 999)
            matricule = f"{prefix}{number:03d}"
            if not User.query.filter_by(matricule=matricule).first():
                return matricule

    @staticmethod
    def generate_temp_password(length=10):
        """Génère un mot de passe temporaire"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(characters) for i in range(length))

    def __repr__(self):
        return f'<User {self.matricule}>'