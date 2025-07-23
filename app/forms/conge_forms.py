from flask_wtf import FlaskForm
from wtforms import DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Length
from datetime import date

class CongeForm(FlaskForm):
    """Formulaire de demande de congé"""
    date_debut = DateField(
        'Date de début',
        validators=[DataRequired(message="La date de début est requise")],
        format='%Y-%m-%d'
    )
    
    date_fin = DateField(
        'Date de fin',
        validators=[DataRequired(message="La date de fin est requise")],
        format='%Y-%m-%d'
    )
    
    motif = TextAreaField(
        'Motif',
        validators=[
            DataRequired(message="Le motif est requis"),
            Length(min=10, max=200, message="Le motif doit contenir entre 10 et 200 caractères")
        ]
    )
    
    submit = SubmitField('Soumettre la demande')
    
    def validate_date_debut(self, field):
        """Validation de la date de début"""
        if not field.data:
            return
        if field.data < date.today():
            raise ValidationError('La date de début ne peut pas être dans le passé')
    
    def validate_date_fin(self, field):
        """Validation de la date de fin"""
        if not field.data or not self.date_debut.data:
            return
        
        if field.data < self.date_debut.data:
            raise ValidationError('La date de fin doit être après la date de début')
        
        delta = field.data - self.date_debut.data
        if delta.days > 30:
            raise ValidationError('La durée maximale est de 30 jours')
        elif delta.days < 0:
            raise ValidationError('La date de fin ne peut pas être avant la date de début')