from app import create_app, db
from app.models.user import User
from datetime import datetime

app = create_app()

with app.app_context():
    # Création des tables
    db.create_all()
    
    # Vérification si l'admin existe déjà
    admin = User.query.filter_by(matricule='ADMIN001').first()
    if not admin:
        # Création de l'admin
        admin = User(
            matricule='ADMIN001',
            email='admin@presencehub.com',
            nom='Admin',
            prenom='System',
            role='admin',
            is_active=True,
            premiere_connexion=False,
            created_at=datetime.utcnow()
        )
        admin.set_password('admin123')
        
        # Ajout à la base de données
        db.session.add(admin)
        db.session.commit()
        print("Administrateur créé avec succès!")
        print("Matricule: ADMIN001")
        print("Mot de passe: admin123")
    else:
        print("L'administrateur existe déjà!")