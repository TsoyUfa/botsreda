import yaml
import json
from typing import Dict, List, Any
from datetime import datetime
import os

class WebAppContentManager:
    """Менеджер контента для Telegram Web App"""
    
    def __init__(self, content_file: str = "webapp/content.yml"):
        self.content_file = content_file
        self.content_data = {}
        self.load_content()
    
    def load_content(self):
        """Загрузка контента из YAML файла"""
        try:
            with open(self.content_file, 'r', encoding='utf-8') as file:
                self.content_data = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Content file {self.content_file} not found, using empty content")
            self.content_data = {"modules": {}}
        except yaml.YAMLError as e:
            print(f"Error loading YAML content: {e}")
            self.content_data = {"modules": {}}
    
    def get_modules_list(self) -> List[Dict]:
        """Получить список всех модулей"""
        modules = []
        for module_id, module_data in self.content_data.get("modules", {}).items():
            modules.append({
                "id": int(module_id),
                "title": module_data.get("title", ""),
                "description": module_data.get("description", ""),
                "estimated_time": module_data.get("estimated_time", "30 мин"),
                "lessons_count": len(module_data.get("lessons", {})),
                "video_url": module_data.get("video_url", ""),
                "pdf_files": module_data.get("pdf_files", []),
                "excel_files": module_data.get("excel_files", [])
            })
        return modules
    
    def get_module_data(self, module_id: int) -> Dict[str, Any]:
        """Получить данные модуля по ID"""
        module_key = str(module_id)
        if module_key not in self.content_data.get("modules", {}):
            return None
        
        module_data = self.content_data["modules"][module_key].copy()
        module_data["id"] = module_id
        return module_data
    
    def get_lesson_data(self, module_id: int, lesson_id: int) -> Dict[str, Any]:
        """Получить данные урока по ID модуля и урока"""
        module_data = self.get_module_data(module_id)
        if not module_data:
            return None
        
        lessons = module_data.get("lessons", {})
        lesson_key = str(lesson_id)
        
        if lesson_key not in lessons:
            return None
        
        lesson_data = lessons[lesson_key].copy()
        lesson_data["id"] = lesson_id
        lesson_data["module_id"] = module_id
        
        return lesson_data
    
    def get_lessons_for_module(self, module_id: int) -> List[Dict]:
        """Получить все уроки для модуля"""
        module_data = self.get_module_data(module_id)
        if not module_data:
            return []
        
        lessons = []
        for lesson_id, lesson_data in module_data.get("lessons", {}).items():
            lesson_info = lesson_data.copy()
            lesson_info["id"] = int(lesson_id)
            lesson_info["module_id"] = module_id
            lessons.append(lesson_info)
        
        return lessons
    
    def get_video_embed_url(self, video_url: str) -> str:
        """Преобразовать URL видео в embed URL для iframe"""
        video_platforms = self.content_data.get("video_platforms", {})
        
        if "youtube.com" in video_url or "youtu.be" in video_url:
            video_id = self.extract_youtube_id(video_url)
            return f"{video_platforms['youtube']['embed_url']}{video_id}"
        
        elif "vk.com" in video_url:
            video_id = self.extract_vk_id(video_url)
            return f"{video_platforms['vk']['embed_url']}{video_id}"
        
        elif "kinescope.io" in video_url:
            video_id = self.extract_kinescope_id(video_url)
            return f"{video_platforms['kinescope']['embed_url']}{video_id}"
        
        return video_url
    
    def extract_youtube_id(self, url: str) -> str:
        """Извлечь ID видео из YouTube URL"""
        import re
        regex = r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)"
        match = re.search(regex, url)
        return match.group(1) if match else ""
    
    def extract_vk_id(self, url: str) -> str:
        """Извлечь параметры видео из VK URL"""
        import re
        regex = r"video(-?\d+)_(\d+)"
        match = re.search(regex, url)
        if match:
            return f"oid={match.group(1)}&id={match.group(2)}"
        return ""
    
    def extract_kinescope_id(self, url: str) -> str:
        """Извлечь ID видео из Kinescope URL"""
        import re
        regex = r"kinescope\.io\/(?:embed\/)?([^\/\s]+)"
        match = re.search(regex, url)
        return match.group(1) if match else ""
    
    def get_file_icon(self, filename: str) -> str:
        """Получить иконку для файла по расширению"""
        icons = {
            'pdf': '📄',
            'doc': '📝',
            'docx': '📝',
            'xls': '📊',
            'xlsx': '📊',
            'ppt': '📽️',
            'pptx': '📽️',
            'txt': '📃',
            'mp4': '🎬',
            'avi': '🎬',
            'mkv': '🎬'
        }
        
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        return icons.get(extension, '📎')
    
    def format_file_size(self, size_bytes: int) -> str:
        """Форматировать размер файла в читаемый вид"""
        if size_bytes == 0:
            return "0 Б"
        
        size_names = ["Б", "КБ", "МБ", "ГБ"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def get_module_statistics(self, module_id: int) -> Dict[str, Any]:
        """Получить статистику по модулю"""
        module_data = self.get_module_data(module_id)
        if not module_data:
            return {}
        
        lessons = module_data.get("lessons", {})
        
        stats = {
            "total_lessons": len(lessons),
            "video_lessons": sum(1 for lesson in lessons.values() if lesson.get("video_url")),
            "text_lessons": sum(1 for lesson in lessons.values() if lesson.get("text_content")),
            "assignments": sum(1 for lesson in lessons.values() if lesson.get("assignment")),
            "pdf_files": len(module_data.get("pdf_files", [])),
            "excel_files": len(module_data.get("excel_files", [])),
            "estimated_duration": self.calculate_module_duration(lessons)
        }
        
        return stats
    
    def calculate_module_duration(self, lessons: Dict) -> str:
        """Рассчитать общую длительность модуля"""
        total_minutes = 0
        
        for lesson in lessons.values():
            duration = lesson.get("duration", "0 мин")
            if isinstance(duration, str):
                # Извлечь число из строки "15 мин", "20 мин"
                import re
                match = re.search(r'(\d+)', duration)
                if match:
                    total_minutes += int(match.group(1))
        
        if total_minutes < 60:
            return f"{total_minutes} мин"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes == 0:
                return f"{hours} ч"
            else:
                return f"{hours} ч {minutes} мин"
    
    def get_all_content_json(self) -> str:
        """Получить весь контент в формате JSON для Web App"""
        modules_list = []
        
        for module_id, module_data in self.content_data.get("modules", {}).items():
            module_info = {
                "id": int(module_id),
                "title": module_data.get("title", ""),
                "description": module_data.get("description", ""),
                "estimated_time": module_data.get("estimated_time", "30 мин"),
                "lessons": []
            }
            
            for lesson_id, lesson_data in module_data.get("lessons", {}).items():
                lesson_info = {
                    "id": int(lesson_id),
                    "title": lesson_data.get("title", ""),
                    "duration": lesson_data.get("duration", "15 мин"),
                    "video_url": lesson_data.get("video_url", ""),
                    "video_embed_url": self.get_video_embed_url(lesson_data.get("video_url", "")) if lesson_data.get("video_url") else "",
                    "text_content": lesson_data.get("text_content", ""),
                    "files": []
                }
                
                # Добавить PDF файлы
                for pdf_file in module_data.get("pdf_files", []):
                    lesson_info["files"].append({
                        "name": pdf_file.get("name", ""),
                        "url": pdf_file.get("url", ""),
                        "type": "pdf",
                        "icon": self.get_file_icon(pdf_file.get("name", ""))
                    })
                
                # Добавить Excel файлы
                for excel_file in module_data.get("excel_files", []):
                    lesson_info["files"].append({
                        "name": excel_file.get("name", ""),
                        "url": excel_file.get("url", ""),
                        "type": "excel",
                        "icon": self.get_file_icon(excel_file.get("name", ""))
                    })
                
                # Добавить задание
                if lesson_data.get("assignment"):
                    lesson_info["assignment"] = lesson_data["assignment"]
                
                module_info["lessons"].append(lesson_info)
            
            modules_list.append(module_info)
        
        return json.dumps(modules_list, ensure_ascii=False, indent=2)
    
    def create_sitemap(self) -> str:
        """Создать карту сайта для контента"""
        sitemap = "# Карта контента обучения\n\n"
        
        for module_id, module_data in self.content_data.get("modules", {}).items():
            sitemap += f"## Модуль {module_id}: {module_data.get('title', '')}\n\n"
            sitemap += f"**Описание:** {module_data.get('description', '')}\n"
            sitemap += f"**Продолжительность:** {module_data.get('estimated_time', '30 мин')}\n\n"
            
            if module_data.get("video_url"):
                sitemap += f"**Видео:** [Смотреть]({module_data['video_url']})\n\n"
            
            if module_data.get("pdf_files"):
                sitemap += "**PDF материалы:**\n"
                for pdf_file in module_data["pdf_files"]:
                    sitemap += f"- [{pdf_file.get('name', '')}]({pdf_file.get('url', '')})\n"
                sitemap += "\n"
            
            if module_data.get("excel_files"):
                sitemap += "**Excel материалы:**\n"
                for excel_file in module_data["excel_files"]:
                    sitemap += f"- [{excel_file.get('name', '')}]({excel_file.get('url', '')})\n"
                sitemap += "\n"
            
            sitemap += "**Уроки:**\n"
            for lesson_id, lesson_data in module_data.get("lessons", {}).items():
                sitemap += f"{lesson_id}. {lesson_data.get('title', '')} ({lesson_data.get('duration', '15 мин')})\n"
                if lesson_data.get("assignment"):
                    sitemap += f"   - Задание: {lesson_data['assignment'].get('title', '')}\n"
            sitemap += "\n---\n\n"
        
        return sitemap

# Глобальный экземпляр менеджера контента
webapp_content = WebAppContentManager()