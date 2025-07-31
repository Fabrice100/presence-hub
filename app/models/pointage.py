from datetime import datetime, date, time, timedelta
from app import db
from sqlalchemy import and_, func

class Pointage(db.Model):
    """Modèle pour les pointages"""
    __tablename__ = 'pointage'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    heure = db.Column(db.Time, nullable=False, default=datetime.utcnow().time)
    type = db.Column(db.String(20), nullable=False)  # 'arrivee' ou 'depart'
    retard = db.Column(db.Boolean, default=False)

    @classmethod
    def create_pointage(cls, user_id, type_pointage):
        """Crée un nouveau pointage avec validations"""
        try:
            now = datetime.now()
            today = now.date()
            
            # Vérifier si on peut pointer ce type aujourd'hui
            can_point, reason = cls.can_point_today(user_id, type_pointage)
            if not can_point:
                raise ValueError(reason)
            
            retard = False
            if type_pointage == "arrivee":
                # Considérer comme retard si arrivée après 9h
                if now.time() > time(9, 0):
                    retard = True

            pointage = cls(
                user_id=user_id,
                type=type_pointage,
                date=today,
                heure=now.time(),
                retard=retard
            )
            db.session.add(pointage)
            db.session.commit()
            return pointage
        except Exception as e:
            print(f"Erreur création pointage: {str(e)}")
            db.session.rollback()
            return None

    @classmethod
    def can_point_today(cls, user_id, type_pointage):
        """Vérifie si on peut pointer ce type aujourd'hui"""
        today = date.today()
        
        # Récupérer tous les pointages d'aujourd'hui pour cet utilisateur
        pointages_aujourd_hui = cls.query.filter_by(
            user_id=user_id,
            date=today
        ).order_by(cls.heure).all()
        
        # Compter les arrivées et départs
        arrivees = [p for p in pointages_aujourd_hui if p.type == 'arrivee']
        departs = [p for p in pointages_aujourd_hui if p.type == 'depart']
        
        if type_pointage == 'arrivee':
            # Vérifier si on a déjà une arrivée aujourd'hui
            if arrivees:
                return False, "Vous avez déjà pointé votre arrivée aujourd'hui"
            
            # Vérifier si on a un départ sans arrivée (cas d'erreur)
            if departs and not arrivees:
                return False, "Erreur : départ enregistré sans arrivée"
                
        elif type_pointage == 'depart':
            # Vérifier si on a une arrivée
            if not arrivees:
                return False, "Vous devez d'abord pointer votre arrivée"
            
            # Vérifier si on a déjà un départ
            if departs:
                return False, "Vous avez déjà pointé votre départ aujourd'hui"
            
            # Vérifier la durée minimale de travail (au moins 30 minutes)
            derniere_arrivee = arrivees[-1]
            duree_travail = datetime.combine(today, datetime.now().time()) - datetime.combine(today, derniere_arrivee.heure)
            if duree_travail < timedelta(minutes=30):
                return False, "Durée de travail minimale non respectée (30 minutes)"
        
        return True, "OK"

    @classmethod
    def get_pointages_jour(cls):
        """Récupère les pointages du jour"""
        try:
            return cls.query.filter(
                cls.date == date.today(),
                cls.type == 'arrivee'
            )
        except Exception as e:
            print(f"Erreur get_pointages_jour: {str(e)}")
            return cls.query.filter(cls.id == -1)  # Retourne une requête vide

    @classmethod
    def get_retards_jour(cls):
        """Récupère les retards du jour"""
        try:
            return cls.query.filter(
                cls.date == date.today(),
                cls.retard == True
            ).count()
        except Exception as e:
            print(f"Erreur get_retards_jour: {str(e)}")
            return 0

    @classmethod
    def get_absents_jour(cls, total_employes):
        """Calcule le nombre d'absents"""
        try:
            presents = cls.get_pointages_jour().count()
            return total_employes - presents
        except Exception as e:
            print(f"Erreur get_absents_jour: {str(e)}")
            return 0

    @staticmethod
    def get_monthly_presence_count(user_id):
        """Compte le nombre de jours de présence dans le mois"""
        try:
            today = date.today()
            first_day = today.replace(day=1)
            return Pointage.query.filter(
                Pointage.user_id == user_id,
                Pointage.date >= first_day,
                Pointage.date <= today,
                Pointage.type == 'arrivee'
            ).count()
        except Exception as e:
            print(f"Erreur get_monthly_presence_count: {str(e)}")
            return 0

    @staticmethod
    def get_user_pointages_today(user_id):
        """Récupère les pointages d'un utilisateur pour aujourd'hui"""
        try:
            return Pointage.query.filter(
                Pointage.user_id == user_id,
                Pointage.date == date.today()
            ).order_by(Pointage.heure).all()
        except Exception as e:
            print(f"Erreur get_user_pointages_today: {str(e)}")
            return []

    @staticmethod
    def get_user_last_pointage(user_id):
        """Récupère le dernier pointage d'un utilisateur"""
        try:
            return Pointage.query.filter_by(user_id=user_id)\
                .order_by(Pointage.date.desc(), Pointage.heure.desc())\
                .first()
        except Exception as e:
            print(f"Erreur get_user_last_pointage: {str(e)}")
            return None

    def __repr__(self):
        return f'<Pointage {self.user_id} {self.date} {self.type}>'