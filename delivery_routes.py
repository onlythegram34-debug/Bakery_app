from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from models import Order, User, DeliveryVerification, db
from utils import role_required
from datetime import datetime

delivery_bp = Blueprint('delivery', __name__)

@delivery_bp.before_request
@login_required
@role_required('delivery')
def before_request():
    pass

@delivery_bp.route('/dashboard')
def dashboard():
    assigned_orders = Order.query.filter_by(
        delivery_guy_id=current_user.id,
        admin_approved=True
    ).filter(Order.status.in_(['ready_for_delivery', 'delivered'])).all()
    sales_team = User.query.filter_by(
        assigned_delivery_id=current_user.id,
        role='sales',
        status='approved'
    ).all()
    return render_template('delivery/dashboard.html', orders=assigned_orders, sales_team=sales_team)

@delivery_bp.route('/pickup-order/<int:order_id>')
def pickup_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.delivery_guy_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('delivery.dashboard'))
    if not order.baker_confirmed:
        flash('Baker has not confirmed this order yet', 'warning')
        return redirect(url_for('delivery.dashboard'))
    order.delivery_picked_up = True
    order.status = 'delivered'
    verif = DeliveryVerification.query.filter_by(order_id=order.id).first()
    if verif:
        verif.delivery_picked_up_at = datetime.utcnow()
    db.session.commit()
    flash('You have picked up the order from baker', 'success')
    return redirect(url_for('delivery.dashboard'))

@delivery_bp.route('/handover-order/<int:order_id>', methods=['GET', 'POST'])
def handover_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.delivery_guy_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('delivery.dashboard'))
    if request.method == 'POST':
        order.delivery_handed_over = True
        verif = DeliveryVerification.query.filter_by(order_id=order.id).first()
        if verif:
            verif.sales_received_at = datetime.utcnow()
        db.session.commit()
        flash('Order handed over to sales person', 'success')
        return redirect(url_for('delivery.dashboard'))
    return render_template('delivery/handover.html', order=order)

@delivery_bp.route('/collect-money/<int:order_id>', methods=['GET', 'POST'])
def collect_money(order_id):
    order = Order.query.get_or_404(order_id)
    if order.delivery_guy_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('delivery.dashboard'))
    if not order.delivery_handed_over:
        flash('You must hand over the cakes before collecting money', 'warning')
        return redirect(url_for('delivery.dashboard'))
    if request.method == 'POST':
        amount_received = float(request.form.get('amount_received', 0))
        if amount_received >= order.total_amount:
            order.payment_received = True
            order.payment_date = datetime.utcnow()
            order.money_collected = True
            order.status = 'completed'
            verif = DeliveryVerification.query.filter_by(order_id=order.id).first()
            if verif:
                verif.money_collected_at = datetime.utcnow()
            db.session.commit()
            flash(f'Payment of R{order.total_amount} collected. Order completed.', 'success')
        else:
            flash(f'Insufficient amount. Expected R{order.total_amount}, got R{amount_received}', 'danger')
            return redirect(url_for('delivery.collect_money', order_id=order.id))
        return redirect(url_for('delivery.dashboard'))
    return render_template('delivery/collect_money.html', order=order)
