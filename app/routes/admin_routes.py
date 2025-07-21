from flask import Blueprint, redirect, render_template, jsonify, request, url_for
from flask_login import login_required, current_user
from app.models.user import User
from app.models.pointage import Pointage
from app import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    # Statistiques simples pour commencer
    stats = {
        'total': User.query.filter_by(role='employee').count(),
        'presents': Pointage.get_pointages_jour().count(),
        'absents': 0,  # À calculer
        'retards': 0   # À calculer
    }
    
    # Liste des employés
    employes = User.query.filter_by(role='employee').all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         employes=employes)

@admin_bp.route('/admin/employee/add', methods=['POST'])
@login_required
def add_employee():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Non autorisé'})
    
    try:
        data = request.json
        
        # Vérifier si le matricule existe déjà
        if User.query.filter_by(matricule=data['matricule']).first():
            return jsonify({'success': False, 'message': 'Matricule déjà utilisé'})
        
        # Créer le nouvel employé
        employee = User(
            matricule=data['matricule'],
            nom=data['nom'],
            prenom=data['prenom'],
            email=data['email'],
            departement=data['departement'],
            role='employee'
        )
        
        # Définir le mot de passe
        employee.set_password(data['password'])
        
        db.session.add(employee)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Employé ajouté avec succès'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})