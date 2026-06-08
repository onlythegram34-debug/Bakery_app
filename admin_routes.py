# Add these inside admin_routes.py after the existing routes

@admin_bp.route('/orders')
def orders():
    pending_orders = Order.query.filter_by(admin_approved=False, status='pending_admin').all()
    all_orders = Order.query.order_by(Order.order_date.desc()).limit(100).all()
    return render_template('admin/orders.html', pending=pending_orders, all_orders=all_orders)

@admin_bp.route('/approve-order/<int:order_id>')
def approve_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.admin_approved = True
    order.status = 'baking'
    # assign to a default baker (you can later assign manually)
    default_baker = User.query.filter_by(role='baker').first()
    if default_baker:
        order.baker_id = default_baker.id
    db.session.commit()
    flash(f'Order #{order.id} approved and sent to baker', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/create-delivery', methods=['GET','POST'])
def create_delivery():
    form = AdminCreateUserForm()
    if form.validate_on_submit():
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
        flash('Delivery guy created', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_delivery.html', form=form)

@admin_bp.route('/analytics')
def analytics():
    # Monthly revenue
    monthly = db.session.query(
        db.func.sum(Order.total_amount)
    ).filter(Order.payment_received==True).scalar() or 0
    
    # Sales person performance
    top_sales = db.session.query(
        User.name, db.func.sum(Order.total_amount).label('total')
    ).join(Order).filter(Order.payment_received==True).group_by(User.id).order_by(db.desc('total')).limit(10).all()
    
    # Delivery guys earnings (simplified)
    return render_template('admin/analytics.html', monthly=monthly, top_sales=top_sales)

@admin_bp.route('/assign-order-to-delivery/<int:order_id>', methods=['POST'])
def assign_order_to_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    delivery_id = request.form.get('delivery_id')
    order.delivery_guy_id = delivery_id
    db.session.commit()
    flash('Delivery guy assigned', 'success')
    return redirect(url_for('admin.orders'))
