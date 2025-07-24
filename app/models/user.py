from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
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
        
        from app.models.pointage import Pointage
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
        
        from app.models.pointage import Pointage
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
    
    def get_duree_travail_jour(self, date_cible=None):
        """Calcule la durée de travail pour un jour donné (aujourd'hui par défaut)"""
        from app.models.pointage import Pointage
        from datetime import date, datetime

        if date_cible is None:
            date_cible = date.today()

        pointages = Pointage.query.filter_by(user_id=self.id, date=date_cible).order_by(Pointage.heure).all()
        heure_arrivee = None
        heure_depart = None

        for p in pointages:
            if p.type == 'arrivee' and heure_arrivee is None:
                heure_arrivee = p.heure
            if p.type == 'depart':
                heure_depart = p.heure  # On prend le dernier départ s'il y en a plusieurs

        if heure_arrivee and heure_depart:
            dt_arrivee = datetime.combine(date_cible, heure_arrivee)
            dt_depart = datetime.combine(date_cible, heure_depart)
            duree = dt_depart - dt_arrivee
            return duree
        return None

    def __repr__(self):
        return f'<User {self.matricule}>'
    
    
    def get_total_heures_semaine(self):
        """Total d'heures travaillées cette semaine (lundi à aujourd'hui)"""
        from app.models.pointage import Pointage
        from datetime import date, timedelta

        today = date.today()
        lundi = today - timedelta(days=today.weekday())
        total = timedelta()
        for i in range((today - lundi).days + 1):
            jour = lundi + timedelta(days=i)
            duree = self.get_duree_travail_jour(jour)
            if duree:
                total += duree
        return total

    def get_total_heures_mois(self):
        """Total d'heures travaillées ce mois-ci (du 1er à aujourd'hui)"""
        from app.models.pointage import Pointage
        from datetime import date, timedelta

        today = date.today()
        premier = today.replace(day=1)
        total = timedelta()
        for i in range((today - premier).days + 1):
            jour = premier + timedelta(days=i)
            duree = self.get_duree_travail_jour(jour)
            if duree:
                total += duree
        return total
    
    def get_status_duree_jour(self):
        """Retourne le statut de la durée travaillée aujourd'hui"""
        duree = self.get_duree_travail_jour()
        if not duree:
            return "incomplete", "Pointage incomplet"
    
        heures = duree.seconds // 3600 + duree.days * 24
        minutes = (duree.seconds // 60) % 60
        total_minutes = heures * 60 + minutes
    
        if total_minutes >= 480:  # 8h = 480 minutes
            return "ok", f"{heures}h{minutes:02d}min"
        elif total_minutes >= 360:  # 6h minimum
            return "warning", f"{heures}h{minutes:02d}min (moins de 8h)"
        else:
            return "danger", f"{heures}h{minutes:02d}min (insuffisant)"

    def get_progression_semaine(self):
        """Calcule la progression de la semaine (objectif 40h)"""
        total_semaine = self.get_total_heures_semaine()
        total_minutes = total_semaine.seconds // 60 + total_semaine.days * 24 * 60
        progression = (total_minutes / 2400) * 100  # 40h = 2400 minutes
        return min(progression, 100)

    def get_status_semaine(self):
        """Retourne le statut de la semaine"""
        progression = self.get_progression_semaine()
        if progression >= 100:
            return "success", f"{progression:.0f}% (objectif atteint)"
        elif progression >= 80:
            return "warning", f"{progression:.0f}% (en cours)"
        else:
            return "danger", f"{progression:.0f}% (en retard)"