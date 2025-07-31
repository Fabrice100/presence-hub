from app import db
from datetime import datetime

class Conge(db.Model): 
    """Modèle pour les congés"""
    __tablename__ = 'conge'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    motif = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.String(20), default='en_attente')  # en_attente, approuve, refuse
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    employe = db.relationship('User', backref='conges', lazy=True)
    
    @property
    def duree(self):
        """Calcule la durée en jours"""
        return (self.date_fin - self.date_debut).days + 1
    
    @property
    def est_modifiable(self):
        """Vérifie si le congé peut être modifié"""
        return self.statut == 'en_attente'
    
    def __repr__(self):
        return f'<Conge {self.employe.matricule} {self.date_debut} - {self.date_fin}>'