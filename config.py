import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env for local development if present
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'change-this-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_HOURS', '24')))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///university.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REEVALUATION_PERIOD_DAYS = int(os.environ.get('REEVALUATION_PERIOD_DAYS', '7'))