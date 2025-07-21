from datetime import datetime, date
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
        now = datetime.now()
        retard = False
        
        if type_pointage == "arrivee":
            # Considérer comme retard si arrivée après 9h
            if now.time() > datetime.strptime("09:00", "%H:%M").time():
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

    @classmethod
    def get_pointages_jour(cls):
        """Récupère les pointages du jour"""
        return cls.query.filter(
            cls.date == date.today(),
            cls.type == 'arrivee'
        )

    @classmethod
    def get_retards_jour(cls):
        """Récupère les retards du jour"""
        return cls.query.filter(
            cls.date == date.today(),
            cls.retard == True
        ).count()

    @classmethod
    def get_absents_jour(cls, total_employes):
        """Calcule le nombre d'absents"""
        presents = cls.get_pointages_jour().count()
        return total_employes - presents

    @staticmethod
    def get_monthly_presence_count(user_id):
        """Compte le nombre de jours de présence dans le mois"""
        today = date.today()
        first_day = today.replace(day=1)
        return Pointage.query.filter(
            Pointage.user_id == user_id,
            Pointage.date >= first_day,
            Pointage.date <= today,
            Pointage.type == 'arrivee'
        ).count()

    @staticmethod
    def get_user_pointages_today(user_id):
        """Récupère les pointages d'un utilisateur pour aujourd'hui"""
        return Pointage.query.filter(
            Pointage.user_id == user_id,
            Pointage.date == date.today()
        ).order_by(Pointage.heure).all()