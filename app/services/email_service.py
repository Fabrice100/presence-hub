from flask_mail import Message
from app import mail
from flask import current_app
from threading import Thread
import logging

logger = logging.getLogger(__name__)

# Fonctions existantes (inchangées)
def send_welcome_email(employee, password):
    """[Votre code existant]"""
    # ... Garder votre code tel quel ...

def send_status_change_email(employee):
    """[Votre code existant]"""
    # ... Garder votre code tel quel ...

def send_password_reset_email(employee, new_password):
    """[Votre code existant]"""
    # ... Garder votre code tel quel ...

def send_otp_email(employee, otp_code):
    """[Votre code existant]"""
    # ... Garder votre code tel quel ...

# Nouvelles fonctions pour les congés
def send_conge_demande_email(conge):
    """
    Envoie l'email de confirmation de demande de congé
    
    Args:
        conge: Instance de Conge
    
    Returns:
        bool: True si l'email a été envoyé avec succès, False sinon
    """
    try:
        msg = Message(
            'Confirmation de votre demande de congé',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[conge.employe.email]
        )
        
        msg.body = f"""
        Bonjour {conge.employe.prenom} {conge.employe.nom},

        Nous confirmons la réception de votre demande de congé :

        Période : Du {conge.date_debut.strftime('%d/%m/%Y')} au {conge.date_fin.strftime('%d/%m/%Y')}
        Durée : {conge.duree} jour(s)
        Motif : {conge.motif}

        Votre demande est actuellement en cours d'examen.
        Vous recevrez une notification dès qu'une décision sera prise.

        Cordialement,
        L'équipe PresenceHub
        """
        
        mail.send(msg)
        logger.info(f"Email de confirmation de demande de congé envoyé à {conge.employe.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de confirmation de congé à {conge.employe.email}: {str(e)}")
        return False

def send_conge_decision_email(conge):
    """
    Envoie l'email de décision de congé
    
    Args:
        conge: Instance de Conge
    
    Returns:
        bool: True si l'email a été envoyé avec succès, False sinon
    """
    try:
        status = "approuvée" if conge.statut == 'approuve' else "refusée"
        
        msg = Message(
            f'Votre demande de congé a été {status}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[conge.employe.email]
        )
        
        msg.body = f"""
        Bonjour {conge.employe.prenom} {conge.employe.nom},

        Votre demande de congé a été {status}.

        Détails de la demande :
        Période : Du {conge.date_debut.strftime('%d/%m/%Y')} au {conge.date_fin.strftime('%d/%m/%Y')}
        Durée : {conge.duree} jour(s)
        Motif : {conge.motif}

        {"Nous vous souhaitons d'excellents congés !" if conge.statut == 'approuve' 
         else "Pour plus d'informations, veuillez contacter votre responsable."}

        Cordialement,
        L'équipe PresenceHub
        """
        
        mail.send(msg)
        logger.info(f"Email de décision de congé envoyé à {conge.employe.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de décision de congé à {conge.employe.email}: {str(e)}")
        return False

def send_conge_rappel_email(conge):
    """
    Envoie l'email de rappel de congé à venir
    
    Args:
        conge: Instance de Conge
    
    Returns:
        bool: True si l'email a été envoyé avec succès, False sinon
    """
    try:
        msg = Message(
            'Rappel : Congé à venir',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[conge.employe.email]
        )
        
        msg.body = f"""
        Bonjour {conge.employe.prenom} {conge.employe.nom},

        Nous vous rappelons que votre congé débute prochainement :

        Début : {conge.date_debut.strftime('%d/%m/%Y')}
        Fin : {conge.date_fin.strftime('%d/%m/%Y')}
        Durée : {conge.duree} jour(s)

        N'oubliez pas de :
        - Mettre à jour vos tâches en cours
        - Configurer votre message d'absence
        - Informer vos collègues

        Nous vous souhaitons d'excellents congés !

        Cordialement,
        L'équipe PresenceHub
        """
        
        mail.send(msg)
        logger.info(f"Email de rappel de congé envoyé à {conge.employe.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de rappel de congé à {conge.employe.email}: {str(e)}")
        return False