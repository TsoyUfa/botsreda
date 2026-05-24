#!/usr/bin/env python3
"""
Транскрибация аудио файлов с помощью Whisper API от OpenAI
Скрипт принимает аудио файл и создаёт текстовый файл с транскрипцией
"""

import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    print("❌ Ошибка: библиотека openai не установлена")
    print("📦 Установите её командой: pip install openai")
    sys.exit(1)


def transcribe_audio(audio_path, output_path=None, language="ru"):
    """
    Транскрибировать аудио файл
    
    Args:
        audio_path: путь к аудио файлу
        output_path: путь для сохранения транскрипции (опционально)
        language: язык аудио ('ru' для русского, 'en' для английского, None для авто-определения)
    """
    # Проверяем наличие API ключа
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Ошибка: не найден API ключ OpenAI")
        print("\n📝 Инструкция по настройке:")
        print("1. Получите API ключ на https://platform.openai.com/api-keys")
        print("2. Добавьте в ~/.zshrc строку:")
        print('   export OPENAI_API_KEY="your-api-key-here"')
        print("3. Выполните: source ~/.zshrc")
        print("\nИли укажите ключ напрямую:")
        print('   export OPENAI_API_KEY="your-api-key-here"')
        sys.exit(1)
    
    audio_path = Path(audio_path)
    
    # Проверяем существование файла
    if not audio_path.exists():
        print(f"❌ Ошибка: файл не найден: {audio_path}")
        sys.exit(1)
    
    # Проверяем формат файла
    supported_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
    if audio_path.suffix.lower() not in supported_formats:
        print(f"⚠️  Предупреждение: формат {audio_path.suffix} может не поддерживаться")
        print(f"   Поддерживаемые форматы: {', '.join(supported_formats)}")
    
    # Проверяем размер файла (лимит 25 МБ)
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 25:
        print(f"❌ Ошибка: размер файла {file_size_mb:.1f} МБ превышает лимит 25 МБ")
        print("💡 Совет: сожмите файл или разделите на части")
        sys.exit(1)
    
    print("\n🎙️  ТРАНСКРИБАЦИЯ АУДИО")
    print("=" * 60)
    print(f"📁 Файл: {audio_path.name}")
    print(f"📊 Размер: {file_size_mb:.2f} МБ")
    print(f"🌍 Язык: {language if language else 'авто-определение'}")
    print("=" * 60)
    print("\n⏳ Отправляю файл на транскрибацию...")
    
    # Инициализируем клиент OpenAI
    client = OpenAI(api_key=api_key)
    
    try:
        # Открываем и отправляем файл
        with open(audio_path, "rb") as audio_file:
            start_time = datetime.now()
            
            # Отправляем запрос к API
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language if language else None,
                response_format="text"
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Транскрибация завершена за {duration:.1f} сек")
        
        # Определяем путь для сохранения
        if output_path is None:
            output_path = audio_path.with_suffix('.txt')
        else:
            output_path = Path(output_path)
        
        # Сохраняем результат
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Транскрибация: {audio_path.name}\n")
            f.write(f"# Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write(f"# Язык: {language if language else 'авто'}\n")
            f.write("\n" + "=" * 60 + "\n\n")
            f.write(transcript)
        
        print(f"💾 Сохранено в: {output_path}")
        print("\n" + "=" * 60)
        print("📝 ТРАНСКРИПЦИЯ:")
        print("=" * 60)
        print(transcript)
        print("\n" + "=" * 60)
        
        # Статистика
        word_count = len(transcript.split())
        char_count = len(transcript)
        print(f"\n📊 Статистика:")
        print(f"   • Слов: {word_count}")
        print(f"   • Символов: {char_count}")
        print(f"   • Примерная стоимость: ~${file_size_mb * 0.006:.4f}")
        
        return transcript
        
    except Exception as e:
        print(f"\n❌ Ошибка при транскрибации: {e}")
        sys.exit(1)


def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("\n🎙️  ТРАНСКРИБАЦИЯ АУДИО С ПОМОЩЬЮ WHISPER API")
        print("=" * 60)
        print("\n📖 Использование:")
        print(f"   python {Path(__file__).name} <путь_к_аудио> [язык] [путь_вывода]")
        print("\n📝 Примеры:")
        print(f"   python {Path(__file__).name} recording.mp3")
        print(f"   python {Path(__file__).name} recording.mp3 ru")
        print(f"   python {Path(__file__).name} recording.mp3 ru output.txt")
        print(f"   python {Path(__file__).name} recording.mp3 en")
        print("\n🌍 Языки:")
        print("   ru - русский")
        print("   en - английский")
        print("   (оставьте пустым для авто-определения)")
        print("\n💡 Поддерживаемые форматы: mp3, mp4, mpeg, mpga, m4a, wav, webm")
        print("   Максимальный размер: 25 МБ")
        print("\n" + "=" * 60)
        sys.exit(1)
    
    audio_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "ru"
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    transcribe_audio(audio_path, output_path, language)
    print("\n✅ Готово!\n")


if __name__ == "__main__":
    main()

