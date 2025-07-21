from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from app.models.pointage import Pointage
from app import db
from datetime import datetime

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/employee/dashboard')
@login_required
def dashboard():
    if current_user.role != 'employee':
        return redirect(url_for('auth.login'))

    # Récupérer les statistiques de l'employé
    stats = {
        'presences': Pointage.get_monthly_presence_count(current_user.id),
        'retards': Pointage.get_retards_jour(),
        'status': current_user.get_status_jour()
    }

    # Récupérer l'historique des pointages
    historique = Pointage.get_user_pointages_today(current_user.id)

    return render_template('employee/dashboard.html',
                         stats=stats,
                         historique=historique)

@employee_bp.route('/employee/pointer', methods=['POST'])
@login_required
def pointer():
    if current_user.role != 'employee':
        return jsonify({'success': False, 'message': 'Non autorisé'})

    try:
        # Vérifier si l'employé peut pointer
        can_point, type_pointage = current_user.can_pointer()
        
        if not can_point:
            return jsonify({
                'success': False,
                'message': 'Pointage non autorisé pour le moment'
            })

        # Créer le pointage
        pointage = Pointage.create_pointage(
            user_id=current_user.id,
            type_pointage=type_pointage
        )

        message = "Arrivée enregistrée" if type_pointage == "arrivee" else "Départ enregistré"
        if pointage.retard:
            message += " (Retard)"

        return jsonify({
            'success': True,
            'message': message,
            'type': type_pointage
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Erreur lors du pointage: {str(e)}"
        })