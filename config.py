import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql+pg8000://postgres:26041564@127.0.0.1:5432/dentalDBFlask'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
