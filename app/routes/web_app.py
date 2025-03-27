from flask import Blueprint, render_template, current_app
import os

web_app = Blueprint('web_app', __name__)

@web_app.route('/')
@web_app.route('/index.html')
def index():
    """Отображение главной страницы веб-приложения"""
    try:
        # Проверяем существование файла
        template_path = os.path.join(current_app.root_path, 'templates', 'index.html')
        if not os.path.exists(template_path):
            current_app.logger.error(f"Template file not found at {template_path}")
            return "Template file not found", 404
            
        return render_template('index.html')
    except Exception as e:
        current_app.logger.error(f"Error rendering template: {str(e)}")
        return "Internal server error", 500 