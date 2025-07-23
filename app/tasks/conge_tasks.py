from app import create_app, db
from app.models.conge import Conge
from app.services.email_service import send_conge_rappel_email
from datetime import datetime, timedelta

def send_conge_reminders():
    """Envoie les rappels pour les congés à venir"""
    app = create_app()
    
    with app.app_context():
        # Congés approuvés qui commencent dans 3 jours
        date_reference = datetime.now().date() + timedelta(days=3)
        
        conges = Conge.query.filter(
            Conge.statut == 'approuve',
            Conge.date_debut == date_reference
        ).all()
        
        for conge in conges:
            send_conge_rappel_email(conge)

if __name__ == '__main__':
    send_conge_reminders()