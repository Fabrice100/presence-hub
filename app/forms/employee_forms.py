from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, EmailField, SubmitField, BooleanField, SearchField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models.user import User

class EmployeeForm(FlaskForm):
    """Formulaire de création/modification d'employé"""
    nom = StringField('Nom', validators=[
        DataRequired(message="Le nom est requis"),
        Length(min=2, max=50, message="Le nom doit contenir entre 2 et 50 caractères")
    ])
    
    prenom = StringField('Prénom', validators=[
        DataRequired(message="Le prénom est requis"),
        Length(min=2, max=50, message="Le prénom doit contenir entre 2 et 50 caractères")
    ])
    
    email = EmailField('Email', validators=[
        DataRequired(message="L'email est requis"),
        Email(message="Veuillez entrer un email valide")
    ])
    
    departement = SelectField('Département', validators=[
        DataRequired(message="Le département est requis")
    ], choices=[
        ('IT', 'Informatique'),
        ('RH', 'Ressources Humaines'),
        ('FIN', 'Finance'),
        ('MKT', 'Marketing'),
        ('PROD', 'Production')
    ])

    is_active = BooleanField('Compte actif', default=True)
    submit = SubmitField('Enregistrer')

    def __init__(self, original_email=None, *args, **kwargs):
        """Initialise le formulaire avec l'email original pour la validation"""
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, field):
        """Valide que l'email n'est pas déjà utilisé"""
        if self.original_email and self.original_email == field.data:
            return
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé.')

class SearchForm(FlaskForm):
    """Formulaire de recherche d'employés"""
    search = StringField('Rechercher', 
                        render_kw={"placeholder": "Rechercher par nom, matricule..."})
    
    departement = SelectField('Département', choices=[
        ('', 'Tous les départements'),
        ('IT', 'Informatique'),
        ('RH', 'Ressources Humaines'),
        ('FIN', 'Finance'),
        ('MKT', 'Marketing'),
        ('PROD', 'Production')
    ], default='')
    
    status = SelectField('Statut', choices=[
        ('', 'Tous les statuts'),
        ('active', 'Actif'),
        ('inactive', 'Inactif')
    ], default='')

class ChangePasswordForm(FlaskForm):
    """Formulaire de changement de mot de passe"""
    current_password = StringField('Mot de passe actuel', validators=[
        DataRequired(message="Le mot de passe actuel est requis")
    ])
    
    new_password = StringField('Nouveau mot de passe', validators=[
        DataRequired(message="Le nouveau mot de passe est requis"),
        Length(min=8, message="Le mot de passe doit contenir au moins 8 caractères")
    ])
    
    confirm_password = StringField('Confirmer le mot de passe', validators=[
        DataRequired(message="La confirmation du mot de passe est requise")
    ])
    
    submit = SubmitField('Changer le mot de passe')

    def validate_confirm_password(self, field):
        """Vérifie que les deux mots de passe correspondent"""
        if field.data != self.new_password.data:
            raise ValidationError('Les mots de passe ne correspondent pas.')