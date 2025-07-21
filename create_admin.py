# create_admin.py
from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Vérifie si l'admin existe déjà
    admin = User.query.filter_by(matricule='ADMIN001').first()
    if not admin:
        admin = User(
            matricule='ADMIN001',
            nom='Admin',
            prenom='System',
            email='admin@presencehub.com',
            role='admin',
            premiere_connexion=False
        )
        admin.set_password('admin123')  # Mot de passe temporaire
        db.session.add(admin)
        db.session.commit()
        print("Admin créé avec succès!")
    else:
        print("L'admin existe déjà!")