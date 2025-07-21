# simulation_data.py
from app import create_app, db
from app.models.user import User
from app.models.pointage import Pointage
from datetime import datetime, timedelta
import random

app = create_app()

def create_simulation_data(days_back=30):
    """
    Crée des données de simulation sur une période donnée
    days_back: nombre de jours dans le passé à simuler
    """
    with app.app_context():
        # Créer quelques départements
        departments = ['IT', 'RH', 'Finance', 'Marketing', 'Production']
        
        # Créer 10 employés de test s'ils n'existent pas
        for i in range(1, 11):
            matricule = f'EMP{i:03d}'  # EMP001, EMP002, etc.
            if not User.query.filter_by(matricule=matricule).first():
                employee = User(
                    matricule=matricule,
                    nom=f'Nom{i}',
                    prenom=f'Prenom{i}',
                    email=f'emp{i:03d}@presencehub.com',
                    role='employee',
                    departement=random.choice(departments)
                )
                employee.set_password('password123')
                db.session.add(employee)
        
        db.session.commit()
        print("Employés créés avec succès!")

        # Récupérer tous les employés
        employees = User.query.filter_by(role='employee').all()
        
        # Simuler les pointages sur la période
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        current_date = start_date

        while current_date <= end_date:
            if current_date.weekday() < 5:  # Lundi à Vendredi
                for employee in employees:
                    # 90% de chance de présence
                    if random.random() < 0.9:
                        # Heure d'arrivée (entre 7h45 et 9h15)
                        arrival_hour = random.randint(7, 9)
                        arrival_minute = random.randint(0, 59)
                        if arrival_hour == 7:
                            arrival_minute = random.randint(45, 59)
                        elif arrival_hour == 9:
                            arrival_minute = random.randint(0, 15)
                            
                        arrival_time = current_date.replace(
                            hour=arrival_hour,
                            minute=arrival_minute,
                            second=0
                        )

                        # Créer pointage d'arrivée
                        pointage_arrivee = Pointage(
                            user_id=employee.id,
                            date=current_date.date(),
                            heure=arrival_time.time(),
                            type='arrivee',
                            retard=(arrival_hour >= 9)
                        )
                        db.session.add(pointage_arrivee)

                        # Heure de départ (entre 16h30 et 18h30)
                        departure_hour = random.randint(16, 18)
                        departure_minute = random.randint(0, 59)
                        if departure_hour == 16:
                            departure_minute = random.randint(30, 59)
                            
                        departure_time = current_date.replace(
                            hour=departure_hour,
                            minute=departure_minute,
                            second=0
                        )

                        # Créer pointage de départ
                        pointage_depart = Pointage(
                            user_id=employee.id,
                            date=current_date.date(),
                            heure=departure_time.time(),
                            type='depart'
                        )
                        db.session.add(pointage_depart)

            current_date += timedelta(days=1)
        
        db.session.commit()
        print("Simulation des pointages terminée!")

        # Afficher quelques statistiques
        print("\nStatistiques de la simulation:")
        print("==============================")
        total_pointages = Pointage.query.count()
        total_retards = Pointage.query.filter_by(retard=True).count()
        print(f"Nombre total de pointages: {total_pointages}")
        print(f"Nombre total de retards: {total_retards}")
        print(f"Période simulée: {start_date.date()} au {end_date.date()}")
        print("\nEmployés créés:")
        for emp in employees:
            print(f"- {emp.matricule}: {emp.nom} {emp.prenom} ({emp.departement})")
        print("\nVous pouvez vous connecter avec n'importe quel matricule et le mot de passe: password123")

if __name__ == '__main__':
    # Supprimer toutes les données existantes
    with app.app_context():
        # Garder l'admin
        admin = User.query.filter_by(role='admin').first()
        
        # Supprimer tous les pointages
        Pointage.query.delete()
        
        # Supprimer tous les employés
        User.query.filter_by(role='employee').delete()
        
        db.session.commit()
    
    # Créer les nouvelles données
    create_simulation_data(days_back=30)  # Simule les 30 derniers jours