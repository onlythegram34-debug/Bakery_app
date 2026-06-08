import os
from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
from dotenv import load_dotenv
from extensions import db, migrate, login_manager

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///bakery.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import models here to avoid circular imports
    from models import User, Residence, Order, DeliveryVerification, Earnings

    # Register blueprints
    from auth import auth_bp
    from admin_routes import admin_bp
    from sales_routes import sales_bp
    from baker_routes import baker_bp
    from delivery_routes import delivery_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(baker_bp, url_prefix='/baker')
    app.register_blueprint(delivery_bp, url_prefix='/delivery')

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            role = current_user.role
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role == 'sales':
                return redirect(url_for('sales.dashboard'))
            elif role == 'baker':
                return redirect(url_for('baker.dashboard'))
            elif role == 'delivery':
                return redirect(url_for('delivery.dashboard'))
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
