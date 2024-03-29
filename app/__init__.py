# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from config import Config  # Import the configuration

app = Flask(__name__)
db_name = 'dealership_backend'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://root@localhost/' + db_name

# Load the configuration
app.config.from_object(Config)

# Enable Cross-Origin Resource Sharing (CORS)
CORS(app)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Set up database migration
migrate = Migrate(app, db)

from app import routes, models  # Import routes and models
