from datetime import datetime
from app.database import db

class User(db.Model):
    """Модель пользователя"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(64))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    is_pregnant = db.Column(db.Boolean, default=False)
    pregnancy_week = db.Column(db.Integer)
    baby_age = db.Column(db.String(50))
    is_premium = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.telegram_id}>'

async def get_user(telegram_id: int) -> User:
    """Получение пользователя по telegram_id"""
    return User.query.filter_by(telegram_id=telegram_id).first() 