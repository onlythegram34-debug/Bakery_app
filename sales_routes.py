from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Order, db
from forms import OrderRequestForm
from datetime import datetime, date, time
from utils import role_required

sales_bp = Blueprint('sales', __name__)

@sales_bp.before_request
@login_required
@role_required('sales')
def before_request():
    pass

@sales_bp.route('/dashboard')
def dashboard():
    orders = Order.query.filter_by(sales_person_id=current_user.id).order_by(Order.order_date.desc()).all()
    earnings = sum([e.amount for e in current_user.earnings])
    return render_template('sales/dashboard.html', orders=orders, earnings=earnings)

@sales_bp.route('/request-order', methods=['GET','POST'])
def request_order():
    # Check for unpaid previous orders
    unpaid = Order.query.filter_by(sales_person_id=current_user.id, payment_received=False).first()
    if unpaid:
        flash(f'You have unpaid order #{unpaid.id}. Please pay before requesting new stock.', 'danger')
        return redirect(url_for('sales.dashboard'))

    form = OrderRequestForm()
    if form.validate_on_submit():
        now = datetime.now()
        cutoff = time(4, 0)
        if form.delivery_date.data == date.today() and now.time() > cutoff:
            flash('Orders for today must be placed before 4:00 AM. Please choose tomorrow.', 'danger')
            return render_template('sales/request_order.html', form=form)
        
        order = Order(
            sales_person_id=current_user.id,
            delivery_date=form.delivery_date.data,
            total_buckets=form.total_buckets.data,
            total_amount=form.total_amount.data,
            status='pending_admin'
        )
        db.session.add(order)
        db.session.commit()
        flash('Order requested. Awaiting admin approval.', 'success')
        return redirect(url_for('sales.dashboard'))
    return render_template('sales/request_order.html', form=form)

@sales_bp.route('/earnings')
def earnings():
    return render_template('sales/earnings.html', earnings=current_user.earnings)
        return redirect(url_for('sales.dashboard'))
    return render_template('sales/request_order.html', form=form)
