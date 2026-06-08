from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)  # admin, sales, baker, delivery
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected (for sales)
    rejection_reason = db.Column(db.String(200))
    created_by_admin = db.Column(db.Boolean, default=False)  # True for baker/delivery
    assigned_delivery_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    residence_id = db.Column(db.Integer, db.ForeignKey('residences.id'))
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    residence = db.relationship('Residence', backref='sales_person', uselist=False, foreign_keys=[residence_id])
    orders = db.relationship('Order', backref='sales_person', lazy=True, foreign_keys='Order.sales_person_id')
    earnings = db.relationship('Earnings', backref='user', lazy=True)
    assigned_delivery = db.relationship('User', remote_side=[id], backref='sales_team', foreign_keys=[assigned_delivery_id])

class Residence(db.Model):
    __tablename__ = 'residences'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    sales_person_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    sales_person_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    baker_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    order_date = db.Column(db.Date, default=date.today)
    request_time = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.Date, nullable=False)
    total_buckets = db.Column(db.Integer, default=1)
    total_amount = db.Column(db.Float, nullable=False)
    payment_received = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime)
    status = db.Column(db.String(30), default='pending_admin')  # pending_admin, approved_admin, baking, ready_for_delivery, delivered, completed
    admin_approved = db.Column(db.Boolean, default=False)
    baker_confirmed = db.Column(db.Boolean, default=False)
    delivery_picked_up = db.Column(db.Boolean, default=False)
    delivery_handed_over = db.Column(db.Boolean, default=False)
    money_collected = db.Column(db.Boolean, default=False)

class DeliveryVerification(db.Model):
    __tablename__ = 'delivery_verifications'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    baker_confirmed_at = db.Column(db.DateTime)
    delivery_picked_up_at = db.Column(db.DateTime)
    sales_received_at = db.Column(db.DateTime)
    money_collected_at = db.Column(db.DateTime)

class Earnings(db.Model):
    __tablename__ = 'earnings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    amount = db.Column(db.Float, default=0.0)
    calculation_basis = db.Column(db.String(50))  # '10_orders' or '20_days'
