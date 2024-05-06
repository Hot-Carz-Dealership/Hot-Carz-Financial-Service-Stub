# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint
from config import Config  # Import the configuration

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/docs.yml'  # Our API url (can of course be a local resource)

app = Flask(__name__)
app.secret_key = 'secret_key'

db_name = 'dealership_backend'

# --------------- check for if testing is needed for this stub -------------
 #SWAP COMMENTS FOR LOCAL DEV
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://root@localhost/' + db_name 
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://root:aGGeAzhlGdyhqpkesCDkjgcyKXHYXEuK@viaduct.proxy.rlwy.net:20836/dealership_backend"

# Load the configuration
app.config.from_object(Config)

# Enable Cross-Origin Resource Sharing (CORS)
CORS(app)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
)

app.register_blueprint(swaggerui_blueprint)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Set up database migration
migrate = Migrate(app, db)

from app import routes, models  # Import routes and models
