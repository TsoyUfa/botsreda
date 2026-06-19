from flask import Flask, send_from_directory, jsonify, request
import os
import json
from webapp_manager import WebAppContentManager
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__, 
            static_folder='webapp',
            static_url_path='')

# Инициализируем менеджер контента
content_manager = WebAppContentManager()

@app.route('/')
def index():
    """Главная страница Web App"""
    return send_from_directory('webapp', 'index.html')

@app.route('/api/modules')
def get_modules():
    """API для получения списка модулей"""
    modules = content_manager.get_modules_list()
    return jsonify({"success": True, "modules": modules})

@app.route('/api/modules/<int:module_id>')
def get_module(module_id):
    """API для получения данных модуля"""
    module_data = content_manager.get_module_data(module_id)
    if module_data:
        return jsonify({"success": True, "module": module_data})
    else:
        return jsonify({"success": False, "error": "Module not found"}), 404

@app.route('/api/modules/<int:module_id>/lessons')
def get_module_lessons(module_id):
    """API для получения уроков модуля"""
    lessons = content_manager.get_lessons_for_module(module_id)
    return jsonify({"success": True, "lessons": lessons})

@app.route('/api/modules/<int:module_id>/lessons/<int:lesson_id>')
def get_lesson(module_id, lesson_id):
    """API для получения данных урока"""
    lesson_data = content_manager.get_lesson_data(module_id, lesson_id)
    if lesson_data:
        return jsonify({"success": True, "lesson": lesson_data})
    else:
        return jsonify({"success": False, "error": "Lesson not found"}), 404

@app.route('/api/user/data')
def get_user_data():
    """API для получения данных пользователя (заглушка для разработки)"""
    # В реальном приложении здесь будет аутентификация
    user_data = {
        "user_id": 123456,
        "first_name": "Антон",
        "username": "anton_tsoy",
        "progress": {
            "1": {"lessons_completed": 3, "total_lessons": 3, "study_time": 45},
            "2": {"lessons_completed": 1, "total_lessons": 3, "study_time": 15},
            "3": {"lessons_completed": 0, "total_lessons": 3, "study_time": 0}
        }
    }
    return jsonify({"success": True, "user": user_data})

@app.route('/api/user/progress')
def get_user_progress():
    """API для получения прогресса пользователя"""
    # Заглушка для разработки
    progress = {
        "modules_completed": 1,
        "total_modules": 7,
        "lessons_completed": 4,
        "total_lessons": 21,
        "study_time": 60,  # в минутах
        "assignments_completed": 2,
        "total_assignments": 21
    }
    return jsonify({"success": True, "progress": progress})

@app.route('/api/content/all')
def get_all_content():
    """API для получения всего контента в формате JSON"""
    content_json = content_manager.get_all_content_json()
    return content_json, 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/api/sitemap')
def get_sitemap():
    """API для получения карты сайта в формате Markdown"""
    sitemap = content_manager.create_sitemap()
    return sitemap, 200, {'Content-Type': 'text/markdown; charset=utf-8'}

@app.route('/health')
def health_check():
    """Проверка работоспособности сервера"""
    return jsonify({"status": "ok", "message": "Web App server is running"})

if __name__ == '__main__':
    # Получаем порт из переменных окружения или используем 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Запускаем сервер
    print("🚀 Запускаем сервер Web App...")
    print("📱 Web App доступен по адресу: http://localhost:5000")
    print("🔧 API доступно по адресу: http://localhost:5000/api")
    print("📋 Карта сайта: http://localhost:5000/api/sitemap")
    
    app.run(host='0.0.0.0', port=port, debug=True)