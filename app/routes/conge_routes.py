from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.conge import Conge
from app.forms.conge_forms import CongeForm
from app.services.email_service import send_conge_demande_email, send_conge_decision_email
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

conge_bp = Blueprint('conge', __name__)

@conge_bp.route('/conges')
@login_required
def liste_conges():
    """Liste des congés"""
    try:
        if current_user.role == 'admin':
            conges = Conge.query.order_by(Conge.created_at.desc()).all()
        else:
            conges = Conge.query.filter_by(user_id=current_user.id)\
                               .order_by(Conge.created_at.desc()).all()
        return render_template('conge/liste.html', conges=conges)
    except Exception as e:
        logger.error(f"Erreur liste des congés: {str(e)}")
        flash("Une erreur s'est produite lors du chargement des congés.", 'danger')
        return redirect(url_for('employee.dashboard'))

@conge_bp.route('/conges/demande', methods=['GET', 'POST'])
@login_required
def demande_conge():
    """Demande de congé"""
    if current_user.role == 'admin':
        flash('Les administrateurs ne peuvent pas demander de congés.', 'warning')
        return redirect(url_for('conge.liste_conges'))
    
    form = CongeForm()
    if form.validate_on_submit():
        try:
            # Vérification des dates
            if form.date_fin.data < form.date_debut.data:
                flash('La date de fin doit être après la date de début.', 'danger')
                return render_template('conge/demande.html', form=form)
            
            # Création du congé
            conge = Conge(
                user_id=current_user.id,
                date_debut=form.date_debut.data,
                date_fin=form.date_fin.data,
                motif=form.motif.data,
                statut='en_attente'
            )
            db.session.add(conge)
            db.session.commit()
            
            # Envoi de l'email de confirmation
            if send_conge_demande_email(conge):
                logger.info(f"Email de confirmation envoyé pour le congé #{conge.id}")
            else:
                logger.warning(f"Échec de l'envoi de l'email de confirmation pour le congé #{conge.id}")
            
            flash('Demande de congé soumise avec succès!', 'success')
            return redirect(url_for('conge.liste_conges'))
            
        except Exception as e:
            logger.error(f"Erreur création congé: {str(e)}")
            db.session.rollback()
            flash("Une erreur s'est produite lors de la création de la demande.", 'danger')
            return redirect(url_for('conge.demande_conge'))
    
    return render_template('conge/demande.html', form=form)

@conge_bp.route('/conges/<int:id>/statut', methods=['POST'])
@login_required
def update_statut(id):
    """Mise à jour du statut d'un congé"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    try:
        conge = Conge.query.get_or_404(id)
        
        if not conge.est_modifiable:
            return jsonify({
                'success': False,
                'message': 'Ce congé ne peut plus être modifié'
            }), 400
        
        nouveau_statut = request.json.get('statut')
        if nouveau_statut not in ['approuve', 'refuse']:
            return jsonify({
                'success': False,
                'message': 'Statut invalide'
            }), 400
        
        ancien_statut = conge.statut
        conge.statut = nouveau_statut
        db.session.commit()
        
        # Envoi de l'email de décision si le statut a changé
        if ancien_statut != nouveau_statut:
            if send_conge_decision_email(conge):
                logger.info(f"Email de décision envoyé pour le congé #{conge.id}")
            else:
                logger.warning(f"Échec de l'envoi de l'email de décision pour le congé #{conge.id}")
        
        return jsonify({
            'success': True,
            'message': f'Congé {nouveau_statut}',
            'statut': nouveau_statut
        })
        
    except Exception as e:
        logger.error(f"Erreur mise à jour statut congé: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@conge_bp.route('/conges/calendrier')
@login_required
def calendrier():
    """Vue calendrier des congés"""
    return render_template('conge/calendrier.html')

@conge_bp.route('/api/conges/calendrier')
@login_required
def api_calendrier():
    """API pour le calendrier"""
    try:
        # [Le reste du code reste identique]
        # Récupération des paramètres de date (optionnels)
        start = request.args.get('start')
        end = request.args.get('end')
        
        # Construction de la requête de base
        query = Conge.query
        
        # Filtrer par date si les paramètres sont fournis
        if start:
            start_date = datetime.fromisoformat(start.split('T')[0])
            query = query.filter(Conge.date_fin >= start_date)
        if end:
            end_date = datetime.fromisoformat(end.split('T')[0])
            query = query.filter(Conge.date_debut <= end_date)
        
        # Filtrer par utilisateur si non admin
        if current_user.role != 'admin':
            query = query.filter_by(user_id=current_user.id)
        
        # Trier par date de début
        query = query.order_by(Conge.date_debut)
        
        # Récupérer les congés
        conges = query.all()
        
        # Définir les couleurs par statut
        colors = {
            'en_attente': '#ffc107',  # warning
            'approuve': '#28a745',    # success
            'refuse': '#dc3545'       # danger
        }
        
        # Construire les événements
        events = []
        for conge in conges:
            # Pour les dates de fin, on ajoute un jour car FullCalendar utilise des dates exclusives
            date_fin = conge.date_fin + timedelta(days=1)
            
            # Formatage du titre selon le rôle
            if current_user.role == 'admin':
                title = f"{conge.employe.prenom} {conge.employe.nom}"
            else:
                title = "Mon congé"
            
            events.append({
                'id': conge.id,
                'title': title,
                'start': conge.date_debut.isoformat(),
                'end': date_fin.isoformat(),
                'backgroundColor': colors[conge.statut],
                'borderColor': colors[conge.statut],
                'textColor': '#ffffff',
                'allDay': True,
                'extendedProps': {
                    'status': conge.statut,
                    'motif': conge.motif,
                    'employe': f"{conge.employe.prenom} {conge.employe.nom}"
                }
            })
        
        return jsonify(events)
        
    except Exception as e:
        logger.error(f"Erreur API calendrier: {str(e)}")
        return jsonify({
            'error': 'Une erreur est survenue lors du chargement des événements',
            'details': str(e)
        }), 500