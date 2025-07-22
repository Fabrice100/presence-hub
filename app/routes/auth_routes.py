from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.forms.employee_forms import ChangePasswordForm
from app import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Route de connexion"""
    # Si l'utilisateur est déjà connecté
    if current_user.is_authenticated:
        if current_user.premiere_connexion:
            return redirect(url_for('auth.change_password'))
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('employee.dashboard'))

    # Nettoyage de la session
    session.clear()
    
    if request.method == 'POST':
        try:
            matricule = request.form.get('matricule')
            password = request.form.get('password')
            
            user = User.query.filter_by(matricule=matricule).first()
            
            if user and user.check_password(password):
                # Vérification si le compte est actif
                if not user.is_active:
                    flash('Votre compte est désactivé. Contactez l\'administrateur.', 'danger')
                    return redirect(url_for('auth.login'))
                
                # Connexion de l'utilisateur
                login_user(user, remember=True)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Redirection selon le rôle et l'état de première connexion
                if user.premiere_connexion:
                    flash('Vous devez changer votre mot de passe.', 'warning')
                    return redirect(url_for('auth.change_password'))
                
                flash('Connexion réussie !', 'success')
                return redirect(url_for('admin.dashboard' if user.role == 'admin' else 'employee.dashboard'))
            
            flash('Matricule ou mot de passe incorrect.', 'danger')
            
        except Exception as e:
            logger.error(f'Erreur lors de la connexion: {str(e)}')
            flash('Une erreur est survenue lors de la connexion.', 'danger')
            db.session.rollback()
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Route de déconnexion"""
    try:
        session.clear()
        logout_user()
        flash('Vous avez été déconnecté.', 'info')
    except Exception as e:
        logger.error(f'Erreur lors de la déconnexion: {str(e)}')
        flash('Une erreur est survenue lors de la déconnexion.', 'danger')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Route de changement de mot de passe"""
    if not current_user.premiere_connexion and current_user.role != 'admin':
        return redirect(url_for('employee.dashboard'))
        
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        try:
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                current_user.premiere_connexion = False
                db.session.commit()
                
                flash('Mot de passe modifié avec succès !', 'success')
                return redirect(url_for('admin.dashboard' if current_user.role == 'admin' else 'employee.dashboard'))
            else:
                flash('Mot de passe actuel incorrect.', 'danger')
        except Exception as e:
            logger.error(f'Erreur lors du changement de mot de passe: {str(e)}')
            flash('Une erreur est survenue lors du changement de mot de passe.', 'danger')
            db.session.rollback()
            
    return render_template('auth/change_password.html', form=form)