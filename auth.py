from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Residence, db
from forms import LoginForm, SalesRegistrationForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/register-sales', methods=['GET', 'POST'])
def register_sales():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SalesRegistrationForm()
    # populate residence choices
    form.residence_id.choices = [(0, 'Add new residence')] + [(r.id, r.name) for r in Residence.query.all()]
    if form.validate_on_submit():
        # handle new residence
        if form.residence_id.data == 0:
            if not form.new_residence_name.data:
                flash('Please provide a residence name', 'danger')
                return render_template('register_sales.html', form=form)
            new_res = Residence(
                name=form.new_residence_name.data,
                location=form.new_residence_location.data
            )
            db.session.add(new_res)
            db.session.flush()
            res_id = new_res.id
        else:
            res_id = form.residence_id.data
        # create sales user
        user = User(
            email=form.email.data,
            name=form.name.data,
            phone=form.phone.data,
            role='sales',
            status='pending',
            residence_id=res_id
        )
        user.password_hash = generate_password_hash(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration submitted. Admin will review your application.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register_sales.html', form=form)
