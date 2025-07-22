from datetime import datetime, date, time
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
        """Crée un nouveau pointage"""
        try:
            now = datetime.now()
            retard = False
            
            if type_pointage == "arrivee":
                # Considérer comme retard si arrivée après 9h
                if now.time() > time(9, 0):
                    retard = True

            pointage = cls(
                user_id=user_id,
                type=type_pointage,
                date=now.date(),
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