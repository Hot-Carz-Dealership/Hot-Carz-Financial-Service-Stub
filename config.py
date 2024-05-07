# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # General configuration settings
    # --------------- check for if testing is needed for this stub -------------

    SECRET_KEY = os.getenv("SECRET_KEY")
    
     #SWAP COMMENTS FOR LOCAL DEV
    #SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:{os.getenv('SECRET_KEY')}@localhost/dealership_backend"

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:aGGeAzhlGdyhqpkesCDkjgcyKXHYXEuK@viaduct.proxy.rlwy.net:20836/dealership_backend"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
