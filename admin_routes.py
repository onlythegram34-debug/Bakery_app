from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User, Order, Residence, Earnings, db
from forms import AdminCreateUserForm
from utils import role_required
from datetime import datetime, date

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
@role_required('admin')
def before_request():
    pass

@admin_bp.route('/dashboard')
def dashboard():
    pending_applicants = User.query.filter_by(role='sales', status='pending').count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(Order.payment_received==True).scalar() or 0
    return render_template('admin/dashboard.html', pending=pending_applicants, orders=total_orders, revenue=total_revenue)

@admin_bp.route('/applicants')
def applicants():
    applicants = User.query.filter_by(role='sales', status='pending').all()
    return render_template('admin/applicants.html', applicants=applicants)

@admin_bp.route('/approve/<int:user_id>', methods=['POST'])
def approve_applicant(user_id):
    sales = User.query.get_or_404(user_id)
    delivery_id = request.form.get('delivery_id')
    sales.status = 'approved'
    sales.assigned_delivery_id = delivery_id
    # ensure residence not taken
    if sales.residence_id and Residence.query.filter_by(sales_person_id=sales.id).first():
        flash('Residence already has a sales person', 'danger')
        return redirect(url_for('admin.applicants'))
    if sales.residence_id:
        residence = Residence.query.get(sales.residence_id)
        residence.sales_person_id = sales.id
    db.session.commit()
    flash('Sales person approved', 'success')
    return redirect(url_for('admin.applicants'))

@admin_bp.route('/reject/<int:user_id>', methods=['POST'])
def reject_applicant(user_id):
    sales = User.query.get_or_404(user_id)
    reason = request.form.get('reason')
    sales.status = 'rejected'
    sales.rejection_reason = reason
    db.session.commit()
    flash('Application rejected', 'warning')
    return redirect(url_for('admin.applicants'))

@admin_bp.route('/create-baker', methods=['GET','POST'])
def create_baker():
    form = AdminCreateUserForm()
    if form.validate_on_submit():
        baker = User(
            email=form.email.data,
            name=form.name.data,
            phone=form.phone.data,
            role='baker',
            status='approved',
            created_by_admin=True
        )
        baker.password_hash = generate_password_hash(form.password.data)
        db.session.add(baker)
        db.session.commit()
        flash('Baker created', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_baker.html', form=form)

# Similarly create_delivery, orders list, analytics, etc.
