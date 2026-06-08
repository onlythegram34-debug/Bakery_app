from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Order, DeliveryVerification, db
from utils import role_required
from datetime import datetime

baker_bp = Blueprint('baker', __name__)

@baker_bp.before_request
@login_required
@role_required('baker')
def before_request():
    pass

@baker_bp.route('/dashboard')
def dashboard():
    orders = Order.query.filter_by(
        baker_id=current_user.id,
        admin_approved=True,
        baker_confirmed=False
    ).all()
    completed = Order.query.filter_by(
        baker_id=current_user.id,
        baker_confirmed=True
    ).order_by(Order.order_date.desc()).limit(20).all()
    return render_template('baker/dashboard.html', orders=orders, completed=completed)

@baker_bp.route('/confirm-bake/<int:order_id>')
def confirm_bake(order_id):
    order = Order.query.get_or_404(order_id)
    if order.baker_id != current_user.id:
        flash('Not your order', 'danger')
        return redirect(url_for('baker.dashboard'))
    if order.baker_confirmed:
        flash('Already confirmed', 'warning')
        return redirect(url_for('baker.dashboard'))
    order.baker_confirmed = True
    order.status = 'ready_for_delivery'
    verif = DeliveryVerification.query.filter_by(order_id=order.id).first()
    if not verif:
        verif = DeliveryVerification(order_id=order.id)
        db.session.add(verif)
    verif.baker_confirmed_at = datetime.utcnow()
    db.session.commit()
    flash(f'Order #{order.id} is ready for pickup', 'success')
    return redirect(url_for('baker.dashboard'))
