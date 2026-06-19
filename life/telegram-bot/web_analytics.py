#!/usr/bin/env python3
"""
Веб-интерфейс для аналитики Telegram-бота Р.О.С.Т.
Запускается локально и предоставляет удобную панель для просмотра статистики.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3
import aiosqlite

from flask import Flask, render_template, jsonify, request
import plotly.graph_objs as go
import plotly.utils
import pandas as pd

# Импортируем нашу аналитику
import analytics_db as adb
from config import DB_PATH

app = Flask(__name__)

# =======================
# ОСНОВНЫЕ МАРШРУТЫ
# =======================

@app.route('/')
def index():
    """Главная страница с общей статистикой."""
    try:
        stats = asyncio.run(adb.get_admin_dashboard())
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        return f"Ошибка загрузки статистики: {e}", 500

@app.route('/agents')
def agents_list():
    """Страница со списком всех агентов."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Получаем всех пользователей
        cursor.execute("""
            SELECT user_id, username, first_name, registration_date, last_activity
            FROM users 
            ORDER BY last_activity DESC
        """)
        agents = cursor.fetchall()
        
        # Добавляем статистику по каждому агенту
        agents_with_stats = []
        for agent in agents:
            user_id, username, first_name, reg_date, last_activity = agent
            
            # Получаем прогресс агента
            cursor.execute("""
                SELECT module_id, is_completed, best_score
                FROM user_progress 
                WHERE user_id = ?
            """, (user_id,))
            progress = cursor.fetchall()
            
            completed_modules = sum(1 for p in progress if p[1])
            avg_score = sum(p[2] for p in progress if p[2]) / len([p for p in progress if p[2]]) if progress else 0
            
            agents_with_stats.append({
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'registration_date': reg_date,
                'last_activity': last_activity,
                'completed_modules': completed_modules,
                'total_modules': len(progress),
                'avg_score': round(avg_score * 100, 1) if avg_score else 0
            })
        
        conn.close()
        
        return render_template('agents.html', agents=agents_with_stats)
    except Exception as e:
        return f"Ошибка загрузки списка агентов: {e}", 500

@app.route('/agent/<int:user_id>')
def agent_detail(user_id: int):
    """Детальная страница агента."""
    try:
        analytics = asyncio.run(adb.get_user_analytics(user_id))
        
        if not analytics:
            return "Агент не найден", 404
        
        return render_template('agent_detail.html', analytics=analytics)
    except Exception as e:
        return f"Ошибка загрузки данных агента: {e}", 500

@app.route('/analytics')
def analytics_page():
    """Страница с графиками и аналитикой."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Активность по дням за последний месяц
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as actions
            FROM user_activity_log 
            WHERE timestamp >= datetime('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """)
        daily_activity = cursor.fetchall()
        
        # Популярность модулей
        cursor.execute("""
            SELECT module_id, COUNT(*) as views
            FROM user_activity_log 
            WHERE action_type = 'start_lesson'
            GROUP BY module_id
            ORDER BY views DESC
        """)
        module_popularity = cursor.fetchall()
        
        conn.close()
        
        # Создаем графики с Plotly
        # График активности по дням
        activity_chart = go.Figure(data=[
            go.Scatter(
                x=[row[0] for row in daily_activity],
                y=[row[1] for row in daily_activity],
                mode='lines+markers',
                name='Действия пользователей',
                line=dict(color='#1f77b4')
            )
        ])
        activity_chart.update_layout(
            title='Активность пользователей по дням',
            xaxis_title='Дата',
            yaxis_title='Количество действий'
        )
        
        # График популярности модулей
        module_chart = go.Figure(data=[
            go.Bar(
                x=[f"Блок {row[0]}" for row in module_popularity],
                y=[row[1] for row in module_popularity],
                name='Просмотры модулей',
                marker_color='#ff7f0e'
            )
        ])
        module_chart.update_layout(
            title='Популярность учебных модулей',
            xaxis_title='Модуль',
            yaxis_title='Количество просмотров'
        )
        
        # Конвертируем графики в JSON для отображения в HTML
        activity_graph_json = json.dumps(activity_chart, cls=plotly.utils.PlotlyJSONEncoder)
        module_graph_json = json.dumps(module_chart, cls=plotly.utils.PlotlyJSONEncoder)
        
        return render_template('analytics.html', 
                             activity_graph_json=activity_graph_json,
                             module_graph_json=module_graph_json)
    except Exception as e:
        return f"Ошибка загрузки аналитики: {e}", 500

@app.route('/export')
def export_data():
    """Экспорт данных в различных форматах."""
    export_type = request.args.get('type', 'json')
    
    try:
        if export_type == 'json':
            # Полный экспорт всех данных
            stats = asyncio.run(adb.get_admin_dashboard())
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Получаем всех агентов с их данными
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            cursor.execute("SELECT * FROM user_progress")
            progress = cursor.fetchall()
            
            cursor.execute("SELECT * FROM user_activity_log")
            activity = cursor.fetchall()
            
            cursor.execute("SELECT * FROM quiz_results")
            quiz_results = cursor.fetchall()
            
            conn.close()
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'statistics': stats,
                'users': users,
                'progress': progress,
                'activity': activity,
                'quiz_results': quiz_results
            }
            
            response = jsonify(export_data)
            response.headers['Content-Disposition'] = 'attachment; filename=rost_bot_export.json'
            return response
            
        elif export_type == 'csv':
            # Экспорт только статистики по агентам в CSV
            conn = sqlite3.connect(DB_PATH)
            
            df_users = pd.read_sql_query("""
                SELECT user_id, username, first_name, registration_date, last_activity
                FROM users
                ORDER BY last_activity DESC
            """, conn)
            
            df_progress = pd.read_sql_query("""
                SELECT user_id, module_id, is_completed, best_score
                FROM user_progress
                WHERE is_completed = 1
            """, conn)
            
            conn.close()
            
            # Объединяем данные
            result = pd.merge(df_users, df_progress, on='user_id', how='left')
            
            response = app.response_class(
                result.to_csv(index=False),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=rost_agents_stats.csv'}
            )
            return response
            
        else:
            return "Неподдерживаемый формат экспорта", 400
            
    except Exception as e:
        return f"Ошибка при экспорте данных: {e}", 500

@app.route('/api/stats')
def api_stats():
    """API для получения статистики в формате JSON."""
    try:
        stats = asyncio.run(adb.get_admin_dashboard())
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/<int:user_id>')
def api_agent_stats(user_id: int):
    """API для получения статистики по конкретному агенту."""
    try:
        analytics = asyncio.run(adb.get_user_analytics(user_id))
        if not analytics:
            return jsonify({'error': 'Agent not found'}), 404
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =======================
# ЗАПУСК ПРИЛОЖЕНИЯ
# =======================

if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса аналитики Р.О.С.Т.")
    print("📊 Доступные страницы:")
    print("  • Главная: http://localhost:5000/")
    print("  • Список агентов: http://localhost:5000/agents")
    print("  • Аналитика: http://localhost:5000/analytics")
    print("  • Экспорт данных: http://localhost:5000/export")
    print("\n🔧 API endpoints:")
    print("  • Общая статистика: http://localhost:5000/api/stats")
    print("  • Данные агента: http://localhost:5000/api/agent/<user_id>")
    
    app.run(debug=True, host='0.0.0.0', port=5000)