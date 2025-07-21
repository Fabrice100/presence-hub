# test_data.py
from app import create_app, db
from app.models.user import User
from app.models.pointage import Pointage
from datetime import datetime, timedelta
import random

app = create_app()

def create_test_data():
    with app.app_context():
        # Créer quelques employés de test
        departments = ['IT', 'RH', 'Finance', 'Marketing']
        for i in range(1, 6):
            matricule = f'EMP00{i}'
            if not User.query.filter_by(matricule=matricule).first():
                employee = User(
                    matricule=matricule,
                    nom=f'Nom{i}',
                    prenom=f'Prenom{i}',
                    email=f'emp{i}@presencehub.com',
                    role='employee',
                    departement=random.choice(departments)
                )
                employee.set_password('password123')
                db.session.add(employee)
                
        db.session.commit()
        
        # Créer des pointages aléatoires pour les 7 derniers jours
        employees = User.query.filter_by(role='employee').all()
        for employee in employees:
            for i in range(7):
                date = datetime.now().date() - timedelta(days=i)
                # Pointage d'arrivée
                Pointage.create_pointage(
                    user_id=employee.id,
                    type_pointage='arrivee',
                    date=date,
                    heure=datetime.strptime(f'08:{random.randint(0,59):02d}', '%H:%M').time()
                )
                # Pointage de départ
                Pointage.create_pointage(
                    user_id=employee.id,
                    type_pointage='depart',
                    date=date,
                    heure=datetime.strptime(f'17:{random.randint(0,59):02d}', '%H:%M').time()
                )

        print("Données de test créées avec succès!")

if __name__ == '__main__':
    create_test_data()