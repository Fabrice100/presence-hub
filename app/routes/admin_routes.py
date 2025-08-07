from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.pointage import Pointage
from app.forms.employee_forms import EmployeeForm, SearchForm
from app.services.email_service import send_welcome_email, send_status_change_email
from app.services.export_service import export_to_excel, export_to_pdf
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():
    """Dashboard administrateur"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('employee.dashboard'))

    try:
        # Initialisation du formulaire de recherche
        search_form = SearchForm(request.args)
        
        # Récupération des statistiques avec une seule requête
        from sqlalchemy import func, and_, or_, case
        from datetime import date, timedelta
        
        today = date.today()
        lundi = today - timedelta(days=today.weekday())
        
        # Statistiques optimisées
        stats_query = db.session.query(
            func.count(User.id).label('total'),
            func.count(Pointage.id).label('presents'),
            func.sum(case((Pointage.retard == True, 1), else_=0)).label('retards')
        ).outerjoin(
            Pointage, and_(
                User.id == Pointage.user_id,
                Pointage.date == today,
                Pointage.type == 'arrivee'
            )
        ).filter(User.role == 'employee', User.is_active == True)
        
        stats_result = stats_query.first()
        stats = {
            'total': stats_result.total or 0,
            'presents': stats_result.presents or 0,
            'retards': stats_result.retards or 0,
            'absents': (stats_result.total or 0) - (stats_result.presents or 0)
        }
        
        # Construction de la requête de recherche
        query = User.query.filter_by(role='employee')
        
        if request.args.get('search'):
            search = f"%{request.args.get('search')}%"
            query = query.filter(
                (User.nom.ilike(search)) |
                (User.prenom.ilike(search)) |
                (User.matricule.ilike(search))
            )
        
        if request.args.get('departement'):
            query = query.filter_by(departement=request.args.get('departement'))
        
        if request.args.get('status'):
            is_active = request.args.get('status') == 'active'
            query = query.filter_by(is_active=is_active)

        # Récupération des employés
        employees = query.order_by(User.nom).all()
        
        # Optimisation : Récupération des données de pointage en une seule requête
        employee_ids = [e.id for e in employees]
        
        if employee_ids:
            # Pointages du jour pour tous les employés
            pointages_jour = db.session.query(Pointage).filter(
                Pointage.user_id.in_(employee_ids),
                Pointage.date == today
            ).all()
            
            # Pointages de la semaine pour tous les employés
            pointages_semaine = db.session.query(Pointage).filter(
                Pointage.user_id.in_(employee_ids),
                Pointage.date >= lundi,
                Pointage.date <= today
            ).all()
            
            # Pointages du mois pour tous les employés
            premier_mois = today.replace(day=1)
            pointages_mois = db.session.query(Pointage).filter(
                Pointage.user_id.in_(employee_ids),
                Pointage.date >= premier_mois,
                Pointage.date <= today
            ).all()
            
            # Calcul optimisé des durées
            durees = {}
            totaux_semaine = {}
            totaux_mois = {}
            
            for employee in employees:
                # Pointages du jour pour cet employé
                emp_pointages_jour = [p for p in pointages_jour if p.user_id == employee.id]
                durees[employee.id] = User._calculate_duration_from_pointages(emp_pointages_jour, today)
                
                # Pointages de la semaine pour cet employé
                emp_pointages_semaine = [p for p in pointages_semaine if p.user_id == employee.id]
                totaux_semaine[employee.id] = User._calculate_weekly_duration_from_pointages(emp_pointages_semaine, lundi, today)
                
                # Pointages du mois pour cet employé
                emp_pointages_mois = [p for p in pointages_mois if p.user_id == employee.id]
                totaux_mois[employee.id] = User._calculate_monthly_duration_from_pointages(emp_pointages_mois, premier_mois, today)
        else:
            durees = {}
            totaux_semaine = {}
            totaux_mois = {}
        
        # Statistiques des alertes optimisées
        alertes = {
            'incomplets': sum(1 for e in employees if not durees.get(e.id)),
            'moins_8h': sum(1 for e in employees if durees.get(e.id) and (durees[e.id].seconds // 3600) < 8),
            'semaine_retard': sum(1 for e in employees if totaux_semaine.get(e.id) and User._calculate_weekly_progression(totaux_semaine[e.id]) < 80)
        }
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             employees=employees,
                             durees=durees,
                             totaux_semaine=totaux_semaine,
                             totaux_mois=totaux_mois,
                             alertes=alertes,
                             search_form=search_form)
        
                             
    except Exception as e:
        logger.error(f'Erreur dashboard admin: {str(e)}')
        flash('Une erreur s\'est produite lors du chargement du dashboard.', 'danger')
        return redirect(url_for('auth.login'))

@admin_bp.route('/admin/export/<format>')
@login_required
def export_data(format):
    """Export des données en Excel ou PDF"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        # Récupération des données
        employees = User.query.filter_by(role='employee').order_by(User.nom).all()
        pointages = Pointage.query.filter(
            Pointage.date == datetime.now().date()
        ).order_by(Pointage.heure.desc()).all()

        if format == 'excel':
            # Export Excel
            excel_file = export_to_excel(employees, pointages)
            return send_file(
                excel_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'presencehub_export_{datetime.now().strftime("%Y%m%d")}.xlsx'
            )
            
        elif format == 'pdf':
            # Export PDF
            pdf_file = export_to_pdf(employees, pointages)
            return send_file(
                pdf_file,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'presencehub_export_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            
        else:
            flash('Format d\'export non supporté.', 'danger')
            return redirect(url_for('admin.dashboard'))
            
    except Exception as e:
        logger.error(f'Erreur lors de l\'export {format}: {str(e)}')
        flash(f'Une erreur est survenue lors de l\'export en {format.upper()}.', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/employee/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    """Ajout d'un nouvel employé"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('auth.login'))

    form = EmployeeForm()
    
    if form.validate_on_submit():
        try:
            # Création de l'employé
            employee, temp_password = User.create_employee(form)
            if not employee:
                raise Exception("Erreur lors de la création de l'employé")

            db.session.add(employee)
            db.session.commit()
            
            # Envoi de l'email de bienvenue
            if send_welcome_email(employee, temp_password):
                flash(f'Employé créé avec succès. Matricule : {employee.matricule}', 'success')
            else:
                flash(f'Employé créé mais erreur lors de l\'envoi de l\'email. Matricule : {employee.matricule}', 'warning')
            
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Erreur création employé: {str(e)}')
            flash(f'Erreur lors de la création : {str(e)}', 'danger')
    
    return render_template('admin/employee_form.html',
                         form=form,
                         title="Nouvel Employé")

@admin_bp.route('/admin/employee/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    """Modification d'un employé"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        employee = User.query.get_or_404(id)
        form = EmployeeForm(original_email=employee.email)
        
        if form.validate_on_submit():
            # Mise à jour des informations
            employee.nom = form.nom.data
            employee.prenom = form.prenom.data
            employee.email = form.email.data
            employee.departement = form.departement.data
            
            # Gestion du changement de statut
            if employee.is_active != form.is_active.data:
                employee.is_active = form.is_active.data
                if not send_status_change_email(employee):
                    flash('Erreur lors de l\'envoi de l\'email de notification.', 'warning')
            
            db.session.commit()
            flash('Employé modifié avec succès.', 'success')
            return redirect(url_for('admin.dashboard'))
            
        elif request.method == 'GET':
            # Pré-remplissage du formulaire
            form.nom.data = employee.nom
            form.prenom.data = employee.prenom
            form.email.data = employee.email
            form.departement.data = employee.departement
            form.is_active.data = employee.is_active
        
        return render_template('admin/employee_form.html',
                             form=form,
                             employee=employee,
                             title="Modifier Employé")
                             
    except Exception as e:
        logger.error(f'Erreur modification employé: {str(e)}')
        flash('Une erreur s\'est produite lors de la modification.', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/employee/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_employee(id):
    """Activation/désactivation d'un employé"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Non autorisé'})

    try:
        employee = User.query.get_or_404(id)
        employee.is_active = not employee.is_active
        db.session.commit()
        
        if not send_status_change_email(employee):
            logger.warning(f'Erreur envoi email pour changement de statut: {employee.email}')
        
        return jsonify({
            'success': True,
            'message': f"Compte {'activé' if employee.is_active else 'désactivé'}",
            'is_active': employee.is_active
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erreur toggle employé: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/admin/reports')
@login_required
def reports():
    """Page des rapports"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        stats = {
            'total_employees': User.query.filter_by(role='employee').count(),
            'active_employees': User.query.filter_by(role='employee', is_active=True).count(),
            'total_pointages': Pointage.query.count(),
            'total_retards': Pointage.query.filter_by(retard=True).count()
        }
        
        return render_template('admin/reports.html', stats=stats)
        
    except Exception as e:
        logger.error(f'Erreur page rapports: {str(e)}')
        flash('Une erreur s\'est produite lors du chargement des rapports.', 'danger')
        return redirect(url_for('admin.dashboard'))