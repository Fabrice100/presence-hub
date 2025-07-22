from app import create_app, db
from app.models.user import User
from app.models.pointage import Pointage
from app.services.email_service import send_welcome_email
from datetime import datetime, timedelta
import random

# Données de test
PRENOMS = ['Thomas', 'Sophie', 'Lucas', 'Emma', 'Hugo', 'Léa', 'Gabriel', 'Chloé', 
           'Arthur', 'Inès', 'Louis', 'Sarah', 'Jules', 'Jade', 'Adam']

NOMS = ['Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand',
        'Leroy', 'Moreau', 'Simon', 'Laurent', 'Lefebvre', 'Michel', 'Garcia']

DEPARTEMENTS = ['IT', 'RH', 'FIN', 'MKT', 'PROD']

def create_test_employees():
    app = create_app()
    with app.app_context():
        print("Création des employés de test...")
        
        # Création des employés
        for i in range(15):
            prenom = PRENOMS[i]
            nom = NOMS[i]
            email = f"{prenom.lower()}.{nom.lower()}@presencehub.com"
            departement = random.choice(DEPARTEMENTS)
            password = 'password123'  # Même mot de passe pour tous les employés
            
            employee = User(
                matricule=f"EMP{(i+1):03d}",
                nom=nom,
                prenom=prenom,
                email=email,
                role='employee',
                departement=departement,
                premiere_connexion=True,  # Changé à True pour forcer le changement de mot de passe
                is_active=True,
                created_at=datetime.utcnow()
            )
            employee.set_password(password)
            db.session.add(employee)
            
            # Envoi de l'email de bienvenue
            try:
                send_welcome_email(employee, password)
                print(f"✓ Email envoyé à {email}")
            except Exception as e:
                print(f"✗ Erreur envoi email à {email}: {str(e)}")
            
            # Création de pointages pour aujourd'hui (pour certains employés)
            if random.random() > 0.2:  # 80% de présence
                today = datetime.now().date()
                arrival_time = datetime.now().replace(
                    hour=random.randint(8, 9),
                    minute=random.randint(0, 59),
                    second=0
                )
                
                # Pointage d'arrivée
                pointage_arrivee = Pointage(
                    user_id=i+1,
                    date=today,
                    heure=arrival_time.time(),
                    type='arrivee',
                    retard=(arrival_time.hour >= 9)
                )
                db.session.add(pointage_arrivee)
                
                # 50% des employés présents ont déjà pointé leur départ
                if random.random() > 0.5:
                    departure_time = datetime.now().replace(
                        hour=random.randint(16, 18),
                        minute=random.randint(0, 59),
                        second=0
                    )
                    pointage_depart = Pointage(
                        user_id=i+1,
                        date=today,
                        heure=departure_time.time(),
                        type='depart',
                        retard=False
                    )
                    db.session.add(pointage_depart)
        
        try:
            db.session.commit()
            print("\n✓ 15 employés créés avec succès!")
            print("\nIdentifiants de connexion :")
            print("----------------------------")
            print("Format des matricules : EMP001 à EMP015")
            print("Mot de passe pour tous : password123")
            print("\nDépartements :")
            print("IT : Informatique")
            print("RH : Ressources Humaines")
            print("FIN : Finance")
            print("MKT : Marketing")
            print("PROD : Production")
            print("\nNotes :")
            print("- Les employés devront changer leur mot de passe à la première connexion")
            print("- Les emails ont été envoyés via Mailtrap")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Erreur lors de la création des données : {str(e)}")

if __name__ == '__main__':
    create_test_employees()