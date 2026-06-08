from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import User, Residence, Order, DeliveryVerification, Earnings, db
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
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(Order.payment_received == True).scalar() or 0
    active_sales = User.query.filter_by(role='sales', status='approved').count()
    active_bakers = User.query.filter_by(role='baker', status='approved').count()
    active_delivery = User.query.filter_by(role='delivery', status='approved').count()
    return render_template('admin/dashboard.html',
                           pending=pending_applicants,
                           orders=total_orders,
                           revenue=total_revenue,
                           active_sales=active_sales,
                           active_bakers=active_bakers,
                           active_delivery=active_delivery)

@admin_bp.route('/applicants')
def applicants():
    pending_applicants = User.query.filter_by(role='sales', status='pending').all()
    approved_sales = User.query.filter_by(role='sales', status='approved').all()
    rejected_sales = User.query.filter_by(role='sales', status='rejected').all()
    delivery_guys = User.query.filter_by(role='delivery', status='approved').all()
    return render_template('admin/applicants.html',
                           applicants=pending_applicants,
                           approved=approved_sales,
                           rejected=rejected_sales,
                           delivery_guys=delivery_guys)

@admin_bp.route('/approve/<int:user_id>', methods=['POST'])
def approve_applicant(user_id):
    sales = User.query.get_or_404(user_id)
    delivery_id = request.form.get('delivery_id')
    if not delivery_id:
        flash('Please select a delivery guy to assign', 'danger')
        return redirect(url_for('admin.applicants'))
    if sales.residence_id:
        existing = User.query.filter_by(residence_id=sales.residence_id, role='sales', status='approved').first()
        if existing and existing.id != sales.id:
            flash(f'Residence already has an approved sales person: {existing.name}', 'danger')
            return redirect(url_for('admin.applicants'))
    sales.status = 'approved'
    sales.assigned_delivery_id = delivery_id
    if sales.residence_id:
        residence = Residence.query.get(sales.residence_id)
        if residence:
            residence.sales_person_id = sales.id
    db.session.commit()
    flash(f'Sales person {sales.name} approved', 'success')
    return redirect(url_for('admin.applicants'))

@admin_bp.route('/reject/<int:user_id>', methods=['POST'])
def reject_applicant(user_id):
    sales = User.query.get_or_404(user_id)
    reason = request.form.get('reason')
    if not reason:
        flash('Please provide a rejection reason', 'danger')
        return redirect(url_for('admin.applicants'))
    sales.status = 'rejected'
    sales.rejection_reason = reason
    db.session.commit()
    flash(f'Application from {sales.name} rejected', 'warning')
    return redirect(url_for('admin.applicants'))

@admin_bp.route('/create-baker', methods=['GET', 'POST'])
def create_baker():
    form = AdminCreateUserForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash('Email already exists', 'danger')
            return render_template('admin/create_baker.html', form=form)
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
        flash(f'Baker {baker.name} created', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_baker.html', form=form)

@admin_bp.route('/create-delivery', methods=['GET', 'POST'])
def create_delivery():
    form = AdminCreateUserForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash('Email already exists', 'danger')
            return render_template('admin/create_delivery.html', form=form)
        delivery = User(
            email=form.email.data,
            name=form.name.data,
            phone=form.phone.data,
            role='delivery',
            status='approved',
            created_by_admin=True
        )
        delivery.password_hash = generate_password_hash(form.password.data)
        db.session.add(delivery)
        db.session.commit()
        flash(f'Delivery guy {delivery.name} created', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_delivery.html', form=form)

@admin_bp.route('/orders')
def orders():
    pending_orders = Order.query.filter_by(admin_approved=False, status='pending_admin').order_by(Order.request_time.asc()).all()
    all_orders = Order.query.order_by(Order.order_date.desc()).limit(100).all()
    delivery_guys = User.query.filter_by(role='delivery', status='approved').all()
    return render_template('admin/orders.html',
                           pending=pending_orders,
                           all_orders=all_orders,
                           delivery_guys=delivery_guys)

@admin_bp.route('/approve-order/<int:order_id>')
def approve_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.admin_approved:
        flash('Order already approved', 'warning')
        return redirect(url_for('admin.orders'))
    order.admin_approved = True
    order.status = 'baking'
    baker = User.query.filter_by(role='baker').first()
    if baker:
        order.baker_id = baker.id
    else:
        flash('No baker available. Create a baker first.', 'danger')
        return redirect(url_for('admin.orders'))
    db.session.commit()
    flash(f'Order #{order.id} approved', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/assign-order-to-delivery/<int:order_id>', methods=['POST'])
def assign_order_to_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    delivery_id = request.form.get('delivery_id')
    if not delivery_id:
        flash('Select a delivery guy', 'danger')
        return redirect(url_for('admin.orders'))
    order.delivery_guy_id = delivery_id
    db.session.commit()
    flash(f'Order #{order.id} assigned', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/residences')
def residences():
    all_residences = Residence.query.all()
    return render_template('admin/residences.html', residences=all_residences)

@admin_bp.route('/add-residence', methods=['GET', 'POST'])
def add_residence():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        if name:
            res = Residence(name=name, location=location)
            db.session.add(res)
            db.session.commit()
            flash('Residence added', 'success')
        else:
            flash('Name required', 'danger')
        return redirect(url_for('admin.residences'))
    return render_template('admin/add_residence.html')

@admin_bp.route('/analytics')
def analytics():
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(Order.payment_received == True).scalar() or 0
    today = date.today()
    first_of_month = date(today.year, today.month, 1)
    monthly_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.payment_received == True,
        Order.payment_date >= first_of_month
    ).scalar() or 0
    top_sales = db.session.query(
        User.name,
        db.func.sum(Order.total_amount).label('total_sales'),
        db.func.count(Order.id).label('order_count')
    ).join(Order).filter(Order.payment_received == True).group_by(User.id).order_by(db.desc('total_sales')).limit(10).all()
    unpaid_orders = Order.query.filter_by(payment_received=False).order_by(Order.order_date.asc()).all()
    status_counts = db.session.query(Order.status, db.func.count(Order.id)).group_by(Order.status).all()
    return render_template('admin/analytics.html',
                           total_revenue=total_revenue,
                           monthly_revenue=monthly_revenue,
                           top_sales=top_sales,
                           unpaid_orders=unpaid_orders,
                           status_counts=status_counts)

@admin_bp.route('/update-earnings')
def update_earnings():
    sales_users = User.query.filter_by(role='sales', status='approved').all()
    for sales in sales_users:
        completed_count = Order.query.filter_by(sales_person_id=sales.id, payment_received=True).count()
        earned_cycles = Earnings.query.filter_by(user_id=sales.id, calculation_basis='10_orders').count()
        expected_cycles = completed_count // 10
        for _ in range(expected_cycles - earned_cycles):
            earning = Earnings(
                user_id=sales.id,
                period_start=date.today(),
                period_end=date.today(),
                amount=50.00,
                calculation_basis='10_orders'
            )
            db.session.add(earning)
    delivery_users = User.query.filter_by(role='delivery', status='approved').all()
    for delivery in delivery_users:
        last_earning = Earnings.query.filter_by(user_id=delivery.id, calculation_basis='20_days').order_by(Earnings.period_end.desc()).first()
        if last_earning:
            days_since = (date.today() - last_earning.period_end).days
        else:
            days_since = 999
        if days_since >= 20:
            team_size = User.query.filter_by(assigned_delivery_id=delivery.id, status='approved').count()
            amount = 200.0 + (team_size - 5) * 10 if team_size > 5 else 200.0
            earning = Earnings(
                user_id=delivery.id,
                period_start=last_earning.period_end if last_earning else delivery.date_joined.date(),
                period_end=date.today(),
                amount=amount,
                calculation_basis='20_days'
            )
            db.session.add(earning)
    db.session.commit()
    flash('Earnings updated', 'success')
    return redirect(url_for('admin.analytics'))

@admin_bp.route('/users')
def users():
    all_users = User.query.all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/deactivate-user/<int:user_id>')
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot deactivate another admin', 'danger')
    else:
        user.status = 'rejected'
        db.session.commit()
        flash(f'User {user.name} deactivated', 'warning')
    return redirect(url_for('admin.users'))
