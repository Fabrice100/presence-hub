from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
import random
import string
import re

class LoginAttempt(db.Model):
    """Modèle pour gérer les tentatives de connexion"""
    __tablename__ = 'login_attempt'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(10), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 compatible
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=False)

    @classmethod
    def record_attempt(cls, matricule, ip_address, success=False):
        """Enregistre une tentative de connexion"""
        attempt = cls(
            matricule=matricule,
            ip_address=ip_address,
            success=success
        )
        db.session.add(attempt)
        db.session.commit()
        return attempt

    @classmethod
    def is_locked_out(cls, matricule, ip_address, max_attempts=5, lockout_time=15):
        """Vérifie si un compte est verrouillé"""
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=lockout_time)
        
        # Compter les tentatives échouées récentes
        failed_attempts = cls.query.filter(
            cls.matricule == matricule,
            cls.ip_address == ip_address,
            cls.success == False,
            cls.timestamp > cutoff_time
        ).count()
        
        return failed_attempts >= max_attempts

    @classmethod
    def cleanup_old_attempts(cls, days=7):
        """Nettoie les anciennes tentatives"""
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        cls.query.filter(cls.timestamp < cutoff_time).delete()
        db.session.commit()

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
        if not self.validate_password_strength(password):
            raise ValueError("Le mot de passe ne respecte pas les critères de sécurité")
        
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie si le mot de passe est correct"""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def validate_password_strength(password):
        """Valide la force du mot de passe"""
        from flask import current_app
        
        if len(password) < current_app.config.get('MIN_PASSWORD_LENGTH', 8):
            return False
        
        if current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True):
            if not re.search(r'[A-Z]', password):
                return False
        
        if current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True):
            if not re.search(r'[a-z]', password):
                return False
        
        if current_app.config.get('PASSWORD_REQUIRE_DIGITS', True):
            if not re.search(r'\d', password):
                return False
        
        if current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True):
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return False
        
        return True

    @staticmethod
    def get_password_requirements():
        """Retourne les exigences de mot de passe"""
        from flask import current_app
        
        requirements = []
        requirements.append(f"Au moins {current_app.config.get('MIN_PASSWORD_LENGTH', 8)} caractères")
        
        if current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True):
            requirements.append("Au moins une lettre majuscule")
        
        if current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True):
            requirements.append("Au moins une lettre minuscule")
        
        if current_app.config.get('PASSWORD_REQUIRE_DIGITS', True):
            requirements.append("Au moins un chiffre")
        
        if current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True):
            requirements.append("Au moins un caractère spécial (!@#$%^&*)")
        
        return requirements

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
        from app.models.pointage import Pointage
        
        # Vérifier d'abord si on peut pointer une arrivée
        can_arrivee, reason_arrivee = Pointage.can_point_today(self.id, "arrivee")
        if can_arrivee:
            return True, "arrivee"
        
        # Vérifier si on peut pointer un départ
        can_depart, reason_depart = Pointage.can_point_today(self.id, "depart")
        if can_depart:
            return True, "depart"
        
        # Si on ne peut pointer ni arrivée ni départ, retourner False avec la raison
        return False, reason_arrivee if not can_arrivee else reason_depart

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
    def generate_temp_password(length=12):
        """Génère un mot de passe temporaire qui respecte les critères de sécurité"""
        # Assurer au moins un de chaque type requis
        password = []
        password.append(random.choice(string.ascii_uppercase))  # Au moins une majuscule
        password.append(random.choice(string.ascii_lowercase))  # Au moins une minuscule
        password.append(random.choice(string.digits))           # Au moins un chiffre
        password.append(random.choice("!@#$%^&*"))             # Au moins un caractère spécial
    
        # Remplir le reste avec des caractères aléatoires
        remaining_length = length - 4
        all_characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password.extend(random.choice(all_characters) for _ in range(remaining_length))
    
        # Mélanger le mot de passe
        random.shuffle(password)
        return ''.join(password)
    
    def get_duree_travail_jour(self, date_cible=None):
        """Calcule la durée de travail pour un jour donné (aujourd'hui par défaut)"""
        from app.models.pointage import Pointage
        from datetime import date, datetime, timedelta

        if date_cible is None:
            date_cible = date.today()

        pointages = Pointage.query.filter_by(user_id=self.id, date=date_cible).order_by(Pointage.heure).all()
        
        if not pointages:
            return None
        
        # Séparer les arrivées et départs
        arrivees = [p for p in pointages if p.type == 'arrivee']
        departs = [p for p in pointages if p.type == 'depart']
        
        if not arrivees:
            return None
        
        # Prendre la première arrivée
        heure_arrivee = arrivees[0].heure
        
        # Prendre le dernier départ s'il y en a
        heure_depart = departs[-1].heure if departs else None
        
        if heure_arrivee and heure_depart:
            dt_arrivee = datetime.combine(date_cible, heure_arrivee)
            dt_depart = datetime.combine(date_cible, heure_depart)
            duree = dt_depart - dt_arrivee
            
            # Limiter à 8h maximum par jour
            duree_max = timedelta(hours=8)
            if duree > duree_max:
                duree = duree_max
            
            return duree
        
        return None

    def get_duree_travail_jour_brute(self, date_cible=None):
        """Calcule la durée de travail brute (sans limite) pour un jour donné"""
        from app.models.pointage import Pointage
        from datetime import date, datetime

        if date_cible is None:
            date_cible = date.today()

        pointages = Pointage.query.filter_by(user_id=self.id, date=date_cible).order_by(Pointage.heure).all()
        
        if not pointages:
            return None
        
        # Séparer les arrivées et départs
        arrivees = [p for p in pointages if p.type == 'arrivee']
        departs = [p for p in pointages if p.type == 'depart']
        
        if not arrivees:
            return None
        
        # Prendre la première arrivée
        heure_arrivee = arrivees[0].heure
        
        # Prendre le dernier départ s'il y en a
        heure_depart = departs[-1].heure if departs else None
        
        if heure_arrivee and heure_depart:
            dt_arrivee = datetime.combine(date_cible, heure_arrivee)
            dt_depart = datetime.combine(date_cible, heure_depart)
            duree = dt_depart - dt_arrivee
            return duree
        
        return None

    def get_total_heures_semaine(self):
        """Total d'heures travaillées cette semaine (lundi à vendredi uniquement)"""
        from app.models.pointage import Pointage
        from datetime import date, timedelta

        today = date.today()
        lundi = today - timedelta(days=today.weekday())
        total = timedelta()
        for i in range((today - lundi).days + 1):
            jour = lundi + timedelta(days=i)
            if jour.weekday() < 5:  # 0=lundi, 4=vendredi
                duree = self.get_duree_travail_jour(jour)
                if duree:
                    total += duree
        return total

    def get_total_heures_weekend(self):
        """Total d'heures travaillées le week-end cette semaine"""
        from app.models.pointage import Pointage
        from datetime import date, timedelta

        today = date.today()
        lundi = today - timedelta(days=today.weekday())
        total = timedelta()
        for i in range((today - lundi).days + 1):
            jour = lundi + timedelta(days=i)
            if jour.weekday() >= 5:  # 5=samedi, 6=dimanche
                duree = self.get_duree_travail_jour_brute(jour)
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
        duree_limitee = self.get_duree_travail_jour()
        duree_brute = self.get_duree_travail_jour_brute()
        
        if not duree_limitee:
            return "incomplete", "Pointage incomplet"
    
        heures = duree_limitee.seconds // 3600 + duree_limitee.days * 24
        minutes = (duree_limitee.seconds // 60) % 60
        total_minutes = heures * 60 + minutes
    
        # Vérifier s'il y a des heures supplémentaires
        heures_supplementaires = ""
        if duree_brute and duree_brute > duree_limitee:
            heures_sup = duree_brute.seconds // 3600 + duree_brute.days * 24
            minutes_sup = (duree_brute.seconds // 60) % 60
            heures_supplementaires = f" (+{heures_sup}h{minutes_sup:02d}min supp.)"
    
        if total_minutes >= 480:  # 8h = 480 minutes
            return "ok", f"{heures}h{minutes:02d}min{heures_supplementaires}"
        elif total_minutes >= 360:  # 6h minimum
            return "warning", f"{heures}h{minutes:02d}min (moins de 8h){heures_supplementaires}"
        else:
            return "danger", f"{heures}h{minutes:02d}min (insuffisant){heures_supplementaires}"

    def get_progression_semaine(self):
        """Calcule la progression de la semaine (objectif 40h)"""
        try:
            total_semaine = self.get_total_heures_semaine()
            total_minutes = total_semaine.seconds // 60 + total_semaine.days * 24 * 60
            progression = (total_minutes / 2400) * 100  # 40h = 2400 minutes
            return min(progression, 100)
        except Exception as e:
            print(f"Erreur dans get_progression_semaine: {e}")
            return 0

    def get_status_semaine(self):
        """Retourne le statut de la semaine"""
        try:
            progression = self.get_progression_semaine()
            heures_weekend = self.get_total_heures_weekend()
            heures_sup = heures_weekend.seconds // 3600 + heures_weekend.days * 24
            minutes_sup = (heures_weekend.seconds // 60) % 60
            weekend_text = f" (+{heures_sup}h{minutes_sup:02d}min week-end)" if heures_sup > 0 else ""
            if progression >= 100:
                return "success", f"{progression:.0f}% (objectif atteint){weekend_text}"
            elif progression >= 80:
                return "warning", f"{progression:.0f}% (en cours){weekend_text}"
            else:
                return "danger", f"{progression:.0f}% (en retard){weekend_text}"
        except Exception as e:
            print(f"Erreur dans get_status_semaine: {e}")
            return "danger", "0% (erreur de calcul)"