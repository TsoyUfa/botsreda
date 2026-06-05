import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import HRFlowable

# --- ГЛОБАЛЬНЫЕ ЦВЕТА БЕНДА (Премиальный темный стиль) ---
COLOR_BG = colors.HexColor('#0b1220')       # Глубокий благородный темно-синий фон (тело баннера)
COLOR_CARD_BG = colors.HexColor('#0f172a')  # Слегка более светлый цвет для карточек (стекло)
COLOR_GOLD = colors.HexColor('#d8b46a')     # Премиальный золотой акцент (латунь)
COLOR_WHITE = colors.HexColor('#ffffff')    # Чистый белый для главных заголовков
COLOR_SOFT_WHITE = colors.HexColor('#e2e8f0') # Мягкий белый для основного текста
COLOR_MUTED = colors.HexColor('#94a3b8')    # Приглушенный серый для подписей
COLOR_BORDER = colors.HexColor('#1e293b')   # Темно-серые тонкие границы

# --- ЕДИНЫЙ ШАБЛОН ОФОРМЛЕНИЯ СТРАНИЦ ---
def draw_cover_page(canvas, doc):
    canvas.saveState()
    # Мягкий глубокий фон
    canvas.setFillColor(COLOR_BG)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
    
    # Тонкая рамка в едином стиле (как в HTML-баннере!)
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(1)
    canvas.rect(30, 30, doc.pagesize[0] - 60, doc.pagesize[1] - 60, fill=False, stroke=True)
    canvas.restoreState()

def draw_later_page(canvas, doc):
    canvas.saveState()
    # Мягкий глубокий фон
    canvas.setFillColor(COLOR_BG)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
    
    # Тонкая рамка в едином стиле
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(1)
    canvas.rect(30, 30, doc.pagesize[0] - 60, doc.pagesize[1] - 60, fill=False, stroke=True)
    
    # Верхний колонтитул (100% русский язык, без англицизмов!)
    canvas.setFont('Arial-Bold', 8)
    canvas.setFillColor(COLOR_GOLD)
    canvas.drawString(45, doc.pagesize[1] - 25, "МЕТОДОЛОГИЯ «РОСТ»")
    canvas.drawRightString(doc.pagesize[0] - 45, doc.pagesize[1] - 25, "СИСТЕМА ЛИЧНОЙ СВОБОДЫ")
    
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(45, doc.pagesize[1] - 30, doc.pagesize[0] - 45, doc.pagesize[1] - 30)
    
    # Нижний колонтитул (Оставляем только номер страницы на правой стороне)
    canvas.setFont('Arial', 8)
    canvas.setFillColor(COLOR_MUTED)
    canvas.drawRightString(doc.pagesize[0] - 45, 18, f"Страница {doc.page}")
    canvas.restoreState()

def generate_pdf():
    # 1. Регистрация системных шрифтов с поддержкой кириллицы
    font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
    font_bold_path = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
    
    if not os.path.exists(font_path) or not os.path.exists(font_bold_path):
        print("Системные шрифты Arial не найдены.")
        sys.exit(1)
        
    pdfmetrics.registerFont(TTFont('Arial', font_path))
    pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))

    pdf_path = "/Users/anton_tsoy/Desktop/Обсидиан/3. Мой клон/методология-РОСТ.pdf"
    
    # Настройка документа (A4, поля)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=45,
        rightMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    # Обычный текст
    body_style = ParagraphStyle(
        'CustomBody', parent=styles['Normal'],
        fontName='Arial', fontSize=10, leading=15,
        textColor=COLOR_SOFT_WHITE, spaceAfter=8
    )
    bullet_style = ParagraphStyle(
        'CustomBullet', parent=body_style,
        leftIndent=15, firstLineIndent=-10, spaceAfter=6
    )
    
    # Заголовки
    h1_style = ParagraphStyle(
        'CustomH1', parent=styles['Heading1'],
        fontName='Arial-Bold', fontSize=16, leading=20,
        textColor=COLOR_GOLD, spaceBefore=18, spaceAfter=10,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'CustomH2', parent=styles['Heading2'],
        fontName='Arial-Bold', fontSize=12, leading=16,
        textColor=COLOR_WHITE, spaceBefore=12, spaceAfter=6,
        keepWithNext=True
    )

    story = []

    # --- СТРАНИЦА 1: ОБЛОЖКА ---
    story.append(Spacer(1, 40))
    story.append(Paragraph("МЕТОДОЛОГИЯ «РОСТ»", ParagraphStyle('CT', parent=styles['Normal'], fontName='Arial-Bold', fontSize=30, leading=36, textColor=COLOR_GOLD, spaceAfter=10)))
    story.append(Paragraph("Система личной свободы и автоматизации процессов для предпринимателей", ParagraphStyle('CS', parent=styles['Normal'], fontName='Arial', fontSize=12, leading=16, textColor=COLOR_SOFT_WHITE, spaceAfter=30)))
    
    # Тонкая разделительная линия в золотом цвете
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_GOLD, spaceAfter=30, hAlign='LEFT'))
    
    # Расшифровка РОСТ
    letter_style = ParagraphStyle('LStyle', parent=styles['Normal'], fontName='Arial-Bold', fontSize=24, leading=28, textColor=COLOR_GOLD, alignment=1)
    word_style = ParagraphStyle('WStyle', parent=styles['Normal'], fontName='Arial-Bold', fontSize=11, leading=14, textColor=COLOR_GOLD)
    desc_style = ParagraphStyle('DStyle', parent=styles['Normal'], fontName='Arial', fontSize=10, leading=14, textColor=COLOR_SOFT_WHITE)
    
    rost_data = [
        [Paragraph("Р", letter_style), Paragraph("РЕГЛАМЕНТЫ", word_style), Paragraph("наведение идеального порядка в процессах и документах компании.", desc_style)],
        [Paragraph("О", letter_style), Paragraph("ОСВОБОЖДЕНИЕ", word_style), Paragraph("освобождение личного времени собственника от операционной рутины.", desc_style)],
        [Paragraph("С", letter_style), Paragraph("СВОБОДА", word_style), Paragraph("возвращение контроля над своей жизнью, стратегией и творчеством.", desc_style)],
        [Paragraph("Т", letter_style), Paragraph("ТЕХНОЛОГИИ", word_style), Paragraph("использование локального искусственного интеллекта на службе бизнеса.", desc_style)]
    ]
    
    # Ширина колонок: 40 + 110 + 350 = 500 (идеально для листа)
    rost_table = Table(rost_data, colWidths=[40, 110, 350])
    rost_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, COLOR_BORDER),
    ]))
    story.append(rost_table)
    story.append(Spacer(1, 30))
    
    # Карточка цели (Вертикальная структура карточки - решает проблему сдвига)
    goal_title = ParagraphStyle('GT', parent=styles['Normal'], fontName='Arial-Bold', fontSize=11, leading=14, textColor=COLOR_GOLD, spaceAfter=6)
    goal_body = ParagraphStyle('GB', parent=styles['Normal'], fontName='Arial', fontSize=10, leading=15, textColor=COLOR_WHITE)
    
    goal_data = [
        [Paragraph("ГЛАВНАЯ ЦЕЛЬ МЕТОДОЛОГИИ:", goal_title)],
        [Paragraph("Навести идеальный порядок в файлах, полностью освободить голову предпринимателя от операционной рутины и научить ИИ-помощника думать в его личном стиле.", goal_body)]
    ]
    goal_table = Table(goal_data, colWidths=[500])
    goal_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a150e')), # Теплый темно-золотой фон
        ('BOX', (0,0), (-1,-1), 1, COLOR_GOLD),                     # Золотая тонкая рамка
        ('LINEBEFORE', (0,0), (0,-1), 4.0, COLOR_GOLD),             # Жирный левый золотой акцент (4pt)
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (-1,-1), 18),
        ('RIGHTPADDING', (0,0), (-1,-1), 18),
    ]))
    story.append(goal_table)
    
    story.append(PageBreak())

    # --- СТРАНИЦА 2: ФИЛОСОФИЯ И 4 ПАПКИ ---
    story.append(Paragraph("1. Главный принцип: «Только то, что работает»", h1_style))
    story.append(Paragraph("Большинство баз знаний - это просто кладбище файлов на диске, которые никто никогда не открывает.", body_style))
    story.append(Paragraph("Во Втором Мозге предпринимателя действует жесткое правило: <b>Любая заметка должна вести к конкретному действию, окупаться в деньгах или упрощать работу.</b>", body_style))
    
    story.append(Paragraph("Три простых правила (Без лишней воды):", h2_style))
    story.append(Paragraph("<font color=\"#d8b46a\">•</font> <b>Не врать:</b> Писать только то, что реально проверено на практике. Никакой пустой теории.", bullet_style))
    story.append(Paragraph("<font color=\"#d8b46a\">•</font> <b>Не приукрашивать:</b> Считать результаты в рублях, часах и реальных сделках, а не в абстрактных успехах.", bullet_style))
    story.append(Paragraph("<font color=\"#d8b46a\">•</font> <b>Не подлизываться:</b> Писать регламенты просто и честно, без корпоративного пафоса и рекламных штампов.", bullet_style))
    
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceAfter=15))

    story.append(Paragraph("2. Четыре папки: Куда класть информацию", h1_style))
    story.append(Paragraph("Вся система разделена на 4 понятные папки. Это нужно, чтобы ты сам не путался, а ИИ мгновенно находил нужный документ за секунды.", body_style))
    
    # Таблица 4 папок с благородным темным заполнением
    fh_style = ParagraphStyle('FH', parent=styles['Normal'], fontName='Arial-Bold', fontSize=9.5, textColor=COLOR_GOLD)
    fb_style = ParagraphStyle('FB', parent=styles['Normal'], fontName='Arial', fontSize=9, leading=13.5, textColor=COLOR_SOFT_WHITE)
    
    folder_data = [
        [Paragraph("<b>Папка</b>", fh_style), Paragraph("<b>Что внутри</b>", fh_style), Paragraph("<b>Главный вопрос</b>", fh_style)],
        [Paragraph("<b>1. Бизнес</b>", fb_style), Paragraph("Описание продуктов, прайс-листы, портреты клиентов, коммерческие предложения.", fb_style), Paragraph("<i>«Что мы продаем и по какой цене?»</i>", fb_style)],
        [Paragraph("<b>2. План</b>", fb_style), Paragraph("Входящие задачи, календари, дорожные карты проектов, график публикаций.", fb_style), Paragraph("<i>«Что конкретно нужно сделать сегодня?»</i>", fb_style)],
        [Paragraph("<b>3. Мой клон</b>", fb_style), Paragraph("Манера речи, твой характер, правила обратной связи, инструкции для ИИ.", fb_style), Paragraph("<i>«Как общается собственник?»</i>", fb_style)],
        [Paragraph("<b>4. Мастерство</b>", fb_style), Paragraph("Инструкции по личной эффективности, чек-листы для сотрудников, шаблоны регламентов.", fb_style), Paragraph("<i>«Как сделать задачу хорошо?»</i>", fb_style)]
    ]
    
    folder_table = Table(folder_data, colWidths=[90, 240, 170])
    folder_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('BACKGROUND', (0,0), (-1,0), COLOR_CARD_BG),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#0d1527')), # Красивый темно-синий фон ячеек
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(folder_table)
    
    story.append(PageBreak())

    # --- СТРАНИЦА 3: СМЫСЛОВАЯ СБОРКА И СВЯЗКА С ИИ ---
    story.append(Paragraph("3. Смысловая сборка: Как навести порядок в мыслях", h1_style))
    story.append(Paragraph("Смысловая сборка - это простой перевод твоих мыслей и голосовых сообщений в готовые рабочие файлы.", body_style))
    
    # Пошаговый процесс с контрастным оформлением
    step_num_style = ParagraphStyle('StepNum', parent=styles['Normal'], fontName='Arial-Bold', fontSize=14, alignment=1, textColor=COLOR_GOLD)
    step_body_style = ParagraphStyle('StepBody', parent=styles['Normal'], fontName='Arial', fontSize=9.5, leading=14, textColor=COLOR_SOFT_WHITE)
    
    step_data = [
        [Paragraph("1", step_num_style), Paragraph("<b>Голосовое на ходу:</b> Ты просто наговариваешь мысль голосом в Телеграм-боте, когда едешь в машине или идешь со встречи. Бот переводит речь в текст.", step_body_style)],
        [Paragraph("2", step_num_style), Paragraph("<b>Обработка ИИ:</b> ИИ-помощник берет твой сырой набросок, убирает «воду» и собирает из него готовый регламент, пост или предложение.", step_body_style)],
        [Paragraph("3", step_num_style), Paragraph("<b>Единая база:</b> Все заметки связываются друг с другом простыми скобками. Так получается удобная база знаний, где любой документ легко найти за секунды.", step_body_style)]
    ]
    
    step_table = Table(step_data, colWidths=[35, 465])
    step_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD_BG),              # Общая темная подложка шагов
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#131d31')),   # Левая колонка с цифрами выделена более светлым синим
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (1,0), (1,-1), 12),
        ('RIGHTPADDING', (1,0), (1,-1), 12),
        ('LEFTPADDING', (0,0), (0,-1), 0),
        ('RIGHTPADDING', (0,0), (0,-1), 0),
    ]))
    story.append(step_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Черновики (Сырье):", h2_style))
    story.append(Paragraph("Любые быстрые заметки, диктовки с телефона, записи со встреч или незаконченные мысли уходят в специальный раздел для черновиков. Они лежат там, чтобы держать основные папки в чистоте и не путать ИИ-помощника устаревшей информацией.", body_style))
    
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceAfter=15))

    story.append(Paragraph("4. Как это работает вместе с ИИ", h1_style))
    story.append(Paragraph("Твой Второй Мозг - это топливный бак для твоего цифрового двойника.", body_style))
    story.append(Paragraph("<font color=\"#d8b46a\">•</font> <b>Быстрый поиск:</b> Когда ты отправляешь голосовое в Телеграм-бот, автоматизация за пару секунд находит нужный файл в твоей базе знаний и загружает его в память ИИ.", bullet_style))
    story.append(Paragraph("<font color=\"#d8b46a\">•</font> <b>Твой стиль:</b> ИИ-помощник читает твою манеру речи из папки <i>«3. Мой клон»</i> и автоматически пишет тексты твоими словами.", bullet_style))
    
    story.append(Spacer(1, 15))
    
    # Главный результат (Стильная темно-золотая карточка с толстой левой границей)
    result_title = ParagraphStyle('RT', parent=styles['Normal'], fontName='Arial-Bold', fontSize=11, leading=14, textColor=COLOR_GOLD, spaceAfter=6)
    result_body = ParagraphStyle('RB', parent=styles['Normal'], fontName='Arial', fontSize=9.5, leading=14, textColor=COLOR_WHITE)
    
    result_data = [
        [Paragraph("ГЛАВНЫЙ РЕЗУЛЬТАТ ДЛЯ ПРЕДПРИНИМАТЕЛЯ:", result_title)],
        [Paragraph("Каждый оцифрованный регламент или предложение во Втором Мозге - это твой личный цифровой актив. Он не уволится и не заболеет, работает 24/7 и полностью освобождает твое личное время для жизни и крупных сделок.", result_body)]
    ]
    result_table = Table(result_data, colWidths=[500])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a150e')), # Теплый темно-золотой фон
        ('BOX', (0,0), (-1,-1), 1, COLOR_GOLD),                     # Золотая тонкая рамка
        ('LINEBEFORE', (0,0), (0,-1), 4.0, COLOR_GOLD),             # Жирный левый золотой акцент (4pt)
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (-1,-1), 18),
        ('RIGHTPADDING', (0,0), (-1,-1), 18),
    ]))
    story.append(result_table)

    # Сборка документа с единым темным премиальным шаблоном
    doc.build(story, onFirstPage=draw_cover_page, onLaterPages=draw_later_page)
    print("PDF успешно сгенерирован в едином стиле по пути:", pdf_path)

if __name__ == "__main__":
    generate_pdf()
