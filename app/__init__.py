"""
Mom&BabyBot - Telegram бот для помощи мамам и будущим мамам
""" 

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config
from app.routes.web_app import web_app

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Регистрация blueprints
    app.register_blueprint(web_app)
    
    return app 