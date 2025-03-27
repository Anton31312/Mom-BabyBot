import logging
from flask import render_template, request, jsonify
from app.models.user import User, db

logger = logging.getLogger(__name__)

def init_routes(app):
    """Инициализация маршрутов Flask"""
    
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/user', methods=['POST'])
    def create_user():
        try:
            data = request.json
            user = User(
                telegram_id=data['telegram_id'],
                username=data['username'],
                is_pregnant=data.get('is_pregnant', False),
                baby_age=data.get('baby_age')
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"Создан новый пользователь через API: {data['username']}")
            return jsonify({"message": "User created successfully"})
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя через API: {str(e)}")
            return jsonify({"error": str(e)}), 400 