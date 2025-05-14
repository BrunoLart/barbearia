from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os

app = Flask(__name__)

# Configuration
# Assuming config.py is in the root directory (e.g., flask_barbershop/config.py)
# To make this work, the root directory flask_barbershop needs to be in PYTHONPATH
# or config.py needs to be in the 'app' package, or use instance-relative config.
# For simplicity with from_object, let's assume config.py is discoverable.
# A common pattern is to have config.py in the instance folder or use create_app factory.
# Given the current structure, let's try to load it from the root.
# If run.py is in flask_barbershop, and app is a sub-package, 'config.Config' should work if flask_barbershop is the CWD or in path.

# Simplified config loading for now, directly setting common values if config.py loading is tricky
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# Login manager settings
login_manager.login_view = 'users.login'  # Assuming user routes are in a 'users' blueprint, or adjust if in main routes.py
                                        # The previous routes.py was not a blueprint. Let's assume it's 'routes.login' for now.
login_manager.login_message_category = 'info'

# Import and register blueprints
# User authentication routes (assuming they are in app/routes.py and need to be converted to a blueprint or imported directly)
# For now, let's assume app/routes.py defines routes on 'app' directly.
from app import routes
# This will register routes defined in app/routes.py on the 'app' instance

# Appointments blueprint
from app.routes.appointments import appointments_bp
app.register_blueprint(appointments_bp, url_prefix='/appointments')

# Import models (after db and app are initialized)
from app import models

# Create database tables if they don't exist (for SQLite, simple setup)
# For more robust setup, Flask-Migrate is used.
# with app.app_context():
#     db.create_all() # This might be needed if not using migrations for the very first run, or if migrations handle it.


