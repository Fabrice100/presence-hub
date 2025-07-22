from flask_mail import Message
from app import mail
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def send_welcome_email(employee, password):
    """
    Envoie l'email de bienvenue avec les credentials
    
    Args:
        employee: Instance de User (nouvel employé)
        password: Mot de passe temporaire généré
    
    Returns:
        bool: True si l'email a été envoyé avec succès, False sinon
    """
    try:
        msg = Message(
            'Bienvenue sur PresenceHub',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[employee.email]
        )
        
        msg.body = f"""
        Bienvenue {employee.prenom} {employee.nom},

        Votre compte PresenceHub a été créé avec succès.

        Vos identifiants de connexion :
        Matricule : {employee.matricule}
        Mot de passe temporaire : {password}

        Lors de votre première connexion, vous devrez changer votre mot de passe.

        Cordialement,
        L'équipe PresenceHub
        """
        
        mail.send(msg)
        logger.info(f"Email de bienvenue envoyé à {employee.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de bienvenue à {employee.email}: {str(e)}")
        return False

def send_status_change_email(employee):
    """
    Envoie un email lors du changement de statut d'un compte
    
    Args:
        employee: Instance de User dont le statut a changé
    
    Returns:
        bool: True si l'email a été envoyé avec succès, False sinon
    """
    try:
        msg = Message(
            'Modification du statut de votre compte PresenceHub',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[employee.email]
        )
        
        status = "activé" if employee.is_active else "désactivé"
        
        msg.body = f"""
        Bonjour {employee.prenom} {employee.nom},

        Votre compte PresenceHub a été {status}.
        
        {'Vous pouvez maintenant vous connecter normalement.' if employee.is_active 
         else 'Vous ne pourrez plus vous connecter jusqu\'à la réactivation de votre compte.'}

        Si vous pensez qu'il s'agit d'une erreur, contactez votre administrateur.

        Cordialement,
        L'équipe PresenceHub
        """
        
        mail.send(msg)
        logger.info(f"Email de changement de statut envoyé à {employee.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de changement de statut à {employee.email}: {str(e)}")
        return False

def send_password_reset_email(employee, new_password):
    """
    Envoie un email avec le nouveau mot de passe
    
    Args:
        employee: Instance de User
        new_password: Nouveau mot de passe généré
    
    Returns:
        bool: True si l'email a été envoyé avec succès, False sinon
    """
    try:
        msg = Message(
            'Réinitialisation de votre mot de passe PresenceHub',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[employee.email]
        )
        
        msg.body = f"""
        Bonjour {employee.prenom} {employee.nom},

        Votre mot de passe a été réinitialisé.

        Votre nouveau mot de passe temporaire est : {new_password}

        Veuillez le changer lors de votre prochaine connexion.

        Cordialement,
        L'équipe PresenceHub
        """
        
        mail.send(msg)
        logger.info(f"Email de réinitialisation de mot de passe envoyé à {employee.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation de mot de passe à {employee.email}: {str(e)}")
        return False

def send_otp_email(employee, otp_code):
    """
    Envoie le code OTP par email
    
    Args:
        employee: Instance de User
        otp_code: Code OTP généré
    
    Returns:
        bool: True si l'email a été envoyé avec succès, False sinon
    """
    try:
        msg = Message(
            'Code de vérification PresenceHub',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[employee.email]
        )
        
        msg.body = f"""
        Bonjour {employee.prenom} {employee.nom},

        Votre code de vérification pour le pointage est : {otp_code}

        Ce code est valable pendant 5 minutes.

        Si vous n'avez pas demandé ce code, veuillez contacter votre administrateur.

        Cordialement,
        L'équipe PresenceHub
        """
        
        mail.send(msg)
        logger.info(f"Email de code OTP envoyé à {employee.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de code OTP à {employee.email}: {str(e)}")
        return False