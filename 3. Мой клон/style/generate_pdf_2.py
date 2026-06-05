import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import HRFlowable

# --- ГЛОБАЛЬНЫЕ ЦВЕТА БРЕНДА (Премиальный темный стиль РОСТ) ---
COLOR_BG = colors.HexColor('#0b1220')       # Глубокий темно-синий фон
COLOR_CARD_BG = colors.HexColor('#0f172a')  # Цвет карточек (темное стекло)
COLOR_GOLD = colors.HexColor('#d8b46a')     # Золотой акцент (латунь)
COLOR_WHITE = colors.HexColor('#ffffff')    # Чистый белый для заголовков
COLOR_SOFT_WHITE = colors.HexColor('#e2e8f0') # Мягкий белый для текста
COLOR_MUTED = colors.HexColor('#94a3b8')    # Серый для второстепенного текста
COLOR_BORDER = colors.HexColor('#1e293b')   # Темно-серые границы

# --- ЕДИНЫЙ ШАБЛОН СТРАНИЦ ---
def draw_cover_page(canvas, doc):
    canvas.saveState()
    # Фоновая заливка
    canvas.setFillColor(COLOR_BG)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
    
    # Тонкая рамка (эффект A4-постера)
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(1)
    canvas.rect(30, 30, doc.pagesize[0] - 60, doc.pagesize[1] - 60, fill=False, stroke=True)
    canvas.restoreState()

def draw_later_page(canvas, doc):
    canvas.saveState()
    # Фоновая заливка
    canvas.setFillColor(COLOR_BG)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
    
    # Тонкая рамка по контуру страницы
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(1)
    canvas.rect(30, 30, doc.pagesize[0] - 60, doc.pagesize[1] - 60, fill=False, stroke=True)
    
    # Верхний колонтитул (100% русский язык)
    canvas.setFont('Arial-Bold', 8)
    canvas.setFillColor(COLOR_GOLD)
    canvas.drawString(45, doc.pagesize[1] - 25, "МЕТОДИЧКА «РОСТ» №2")
    canvas.drawRightString(doc.pagesize[0] - 45, doc.pagesize[1] - 25, "УПРАВЛЕНИЕ БИЗНЕСОМ ГОЛОСОМ")
    
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(45, doc.pagesize[1] - 30, doc.pagesize[0] - 45, doc.pagesize[1] - 30)
    
    # Нижний колонтитул (номер страницы)
    canvas.setFont('Arial', 8)
    canvas.setFillColor(COLOR_MUTED)
    canvas.drawRightString(doc.pagesize[0] - 45, 18, f"Страница {doc.page}")
    canvas.restoreState()

def generate_pdf():
    # Регистрация шрифтов
    font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
    font_bold_path = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
    
    if not os.path.exists(font_path) or not os.path.exists(font_bold_path):
        print("Системные шрифты Arial не найдены.")
        sys.exit(1)
        
    pdfmetrics.registerFont(TTFont('Arial', font_path))
    pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))

    pdf_path = "/Users/anton_tsoy/Desktop/Обсидиан/3. Мой клон/методология-РОСТ-2.pdf"
    
    # Инициализация документа
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=45,
        rightMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    # Стили текста
    body_style = ParagraphStyle(
        'CustomBody', parent=styles['Normal'],
        fontName='Arial', fontSize=9.5, leading=14,
        textColor=COLOR_SOFT_WHITE, spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'CustomBullet', parent=body_style,
        leftIndent=15, firstLineIndent=-10, spaceAfter=4
    )
    
    # Стили заголовков
    h1_style = ParagraphStyle(
        'CustomH1', parent=styles['Heading1'],
        fontName='Arial-Bold', fontSize=14, leading=18,
        textColor=COLOR_GOLD, spaceBefore=14, spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'CustomH2', parent=styles['Heading2'],
        fontName='Arial-Bold', fontSize=11, leading=15,
        textColor=COLOR_WHITE, spaceBefore=10, spaceAfter=4,
        keepWithNext=True
    )

    story = []

    # --- СТРАНИЦА 1: ОБЛОЖКА ---
    story.append(Spacer(1, 30))
    story.append(Paragraph("МЕТОДИЧКА «РОСТ» №2", ParagraphStyle('CT', parent=styles['Normal'], fontName='Arial-Bold', fontSize=26, leading=32, textColor=COLOR_GOLD, spaceAfter=8)))
    story.append(Paragraph("Как управлять бизнесом голосом через Телеграм без рутины", ParagraphStyle('CS', parent=styles['Normal'], fontName='Arial', fontSize=11, leading=15, textColor=COLOR_SOFT_WHITE, spaceAfter=20)))
    
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_GOLD, spaceAfter=20, hAlign='LEFT'))
    
    # Расшифровка РОСТ в таблице
    letter_style = ParagraphStyle('LStyle', parent=styles['Normal'], fontName='Arial-Bold', fontSize=22, leading=26, textColor=COLOR_GOLD, alignment=1)
    word_style = ParagraphStyle('WStyle', parent=styles['Normal'], fontName='Arial-Bold', fontSize=10, leading=13, textColor=COLOR_GOLD)
    desc_style = ParagraphStyle('DStyle', parent=styles['Normal'], fontName='Arial', fontSize=9.5, leading=13, textColor=COLOR_SOFT_WHITE)
    
    rost_data = [
        [Paragraph("Р", letter_style), Paragraph("РЕГЛАМЕНТЫ", word_style), Paragraph("Ты один раз наговариваешь боту, как делать задачу, а ИИ собирает из этого четкую инструкцию.", desc_style)],
        [Paragraph("О", letter_style), Paragraph("ОЦИФРОВКА", word_style), Paragraph("Все мысли, знания, цены и контакты хранятся в одном надежном месте, а не теряются в мессенджерах.", desc_style)],
        [Paragraph("С", letter_style), Paragraph("СВОБОДА", word_style), Paragraph("Когда процессы оцифрованы, ты выходишь из операционки, зарабатываешь 500k+ рублей и свободно живешь.", desc_style)],
        [Paragraph("Т", letter_style), Paragraph("ТЕХНОЛОГИИ", word_style), Paragraph("Умный ИИ-помощник и Телеграм-бот делают всю рутинную и грязную работу за тебя.", desc_style)]
    ]
    
    rost_table = Table(rost_data, colWidths=[35, 105, 360])
    rost_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, COLOR_BORDER),
    ]))
    story.append(rost_table)
    story.append(Spacer(1, 20))
    
    # Карточка главной цели
    goal_title = ParagraphStyle('GT', parent=styles['Normal'], fontName='Arial-Bold', fontSize=10.5, leading=13, textColor=COLOR_GOLD, spaceAfter=4)
    goal_body = ParagraphStyle('GB', parent=styles['Normal'], fontName='Arial', fontSize=9.5, leading=14, textColor=COLOR_WHITE)
    
    goal_data = [
        [Paragraph("ГЛАВНАЯ ЦЕЛЬ МЕТОДИЧКИ:", goal_title)],
        [Paragraph("Объяснить на пальцах, как работает твоя База знаний и твой личный ИИ-помощник, чтобы ты мог ставить задачи и сохранять идеи обычным голосом, лежа на диване или за рулем автомобиля.", goal_body)]
    ]
    goal_table = Table(goal_data, colWidths=[500])
    goal_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a150e')),
        ('BOX', (0,0), (-1,-1), 1, COLOR_GOLD),
        ('LINEBEFORE', (0,0), (0,-1), 4.0, COLOR_GOLD),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(goal_table)
    
    story.append(PageBreak())

    # --- СТРАНИЦА 2: ЗАЧЕМ ЭТО НУЖНО & 4 ПАПКИ ---
    story.append(Paragraph("❓ Зачем тебе это нужно? (Проблема и решение)", h1_style))
    story.append(Paragraph("Представь обычный день предпринимателя: в голове крутится миллион мыслей по задачам, ассистентам, постам и ценам. В это же время разрывается телефон, клиенты пишут во все мессенджеры, рутина сжирает все свободное время, а важные задачи забываются.", body_style))
    story.append(Paragraph("<b>Решение - твой Второй Мозг.</b> Это надежная внешняя флешка для твоих мыслей. Ты просто наговариваешь идеи в Телеграм-бот обычным голосом, а умный ИИ-помощник сам раскладывает их по нужным ячейкам в твоей Базе знаний.", body_style))
    
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceAfter=10))

    story.append(Paragraph("📂 4 папки: Куда ИИ складывает твои мысли?", h1_style))
    story.append(Paragraph("Вся твоя База знаний состоит всего из четырех папок. ИИ-помощник знает правила и сам решает, в какой ящик положить твою голосовую заметку.", body_style))
    
    # Таблица 4 папок
    fh_style = ParagraphStyle('FH', parent=styles['Normal'], fontName='Arial-Bold', fontSize=9, textColor=COLOR_GOLD)
    fb_style = ParagraphStyle('FB', parent=styles['Normal'], fontName='Arial', fontSize=8.5, leading=12.5, textColor=COLOR_SOFT_WHITE)
    
    folder_data = [
        [Paragraph("<b>Папка</b>", fh_style), Paragraph("<b>Что внутри</b>", fh_style), Paragraph("<b>Главный вопрос</b>", fh_style)],
        [Paragraph("<b>1. Бизнес</b>", fb_style), Paragraph("Описание твоих услуг, прайс-листы, портреты идеальных клиентов, готовые коммерческие предложения.", fb_style), Paragraph("<i>«Что и по какой цене мы продаем?»</i>", fb_style)],
        [Paragraph("<b>2. План</b>", fb_style), Paragraph("Задачи на сегодня, календарь встреч, списки дел на неделю, планы по выпуску контента.", fb_style), Paragraph("<i>«Что конкретно нужно сделать прямо сейчас?»</i>", fb_style)],
        [Paragraph("<b>3. Мой клон</b>", fb_style), Paragraph("Твоя Манера речи (Голос автора), твои жизненные правила, принципы общения с клиентами.", fb_style), Paragraph("<i>«Как именно я общаюсь и какие ценности?»</i>", fb_style)],
        [Paragraph("<b>4. Мастерство</b>", fb_style), Paragraph("Чек-листы, стандарты качества, пошаговые инструкции, как делать работу быстро и круто.", fb_style), Paragraph("<i>«Как сделать работу идеально с первого раза?»</i>", fb_style)]
    ]
    
    folder_table = Table(folder_data, colWidths=[80, 250, 170])
    folder_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('BACKGROUND', (0,0), (-1,0), COLOR_CARD_BG),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#0d1527')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(folder_table)
    
    story.append(PageBreak())

    # --- СТРАНИЦА 3: РЕАЛЬНЫЕ ПРИМЕРЫ (КЕЙСЫ) ---
    story.append(Paragraph("🛠 Как это работает на практике? (3 реальных примера)", h1_style))
    story.append(Paragraph("Тебе не нужно учить сложные команды. Ты просто общаешься с Телеграм-ботом голосом.", body_style))
    
    # 3 Карточки примеров
    case_title_style = ParagraphStyle('CTS', parent=styles['Normal'], fontName='Arial-Bold', fontSize=10, leading=13, textColor=COLOR_GOLD, spaceAfter=4)
    case_voice_style = ParagraphStyle('CVS', parent=styles['Normal'], fontName='Arial', fontSize=8.5, leading=12, textColor=colors.HexColor('#94a3b8'))
    case_ai_style = ParagraphStyle('CAS', parent=styles['Normal'], fontName='Arial', fontSize=8.5, leading=12.5, textColor=COLOR_SOFT_WHITE)
    
    # Пример 1
    case1_data = [
      [Paragraph("🎯 Пример 1: Оцифровка идеи и быстрое делегирование", case_title_style)],
      [Paragraph("<b>Голос:</b> <i>«Давай сделаем для клиентов новую премиальную услугу - оцифровку их бизнес-процессов под ключ за 150 тысяч рублей. Запиши это описание в папку Бизнес. И еще, поставь задачу ассистенту на понедельник на 10 утра: подготовить шаблон КП под этот продукт...»</i>", case_voice_style)],
      [Paragraph("<b>ИИ-помощник:</b> Создает документ услуги в папке <b>1. Бизнес</b>, записывает задачу в календарь <b>2. План</b> и автоматически генерирует ТЗ для твоего ассистента, экономя твое время.", case_ai_style)]
    ]
    case1_table = Table(case1_data, colWidths=[500])
    case1_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD_BG),
        ('BOX', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(case1_table)
    story.append(Spacer(1, 10))
    
    # Пример 2
    case2_data = [
      [Paragraph("🎯 Пример 2: Быстрое создание регламента на основе ошибки", case_title_style)],
      [Paragraph("<b>Голос:</b> <i>«Запиши новое правило для менеджеров по продажам. Я сегодня заметил, что мы потеряли клиента, потому что менеджер ответил на заявку только через 3 часа. Вводим жесткий регламент: ответ на входящий запрос должен быть максимум в течение 15 минут...»</i>", case_voice_style)],
      [Paragraph("<b>ИИ-помощник:</b> Находит в папке <b>4. Мастерство</b> файл со стандартами продаж, создает новый понятный регламент «Правило 15 минут», прописывая ценность скорости в рублях, и сохраняет его навсегда.", case_ai_style)]
    ]
    case2_table = Table(case2_data, colWidths=[500])
    case2_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD_BG),
        ('BOX', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(case2_table)
    story.append(Spacer(1, 10))
    
    # Пример 3
    case3_data = [
      [Paragraph("🎯 Пример 3: Создание прогревающего поста из твоих мыслей на ходу", case_title_style)],
      [Paragraph("<b>Голос:</b> <i>«Я еду со встречи и понял важную вещь. Многие предприниматели внедряют CRM, но сотрудники саботируют работу, потому что нет простых правил. Напиши об этом пост в мой канал... Напиши просто, с юмором, как я обычно общаюсь.»</i>", case_voice_style)],
      [Paragraph("<b>ИИ-помощник:</b> Открывает Манеру речи из папки <b>3. Мой клон</b>, пишет вовлекающий и честный пост без ИИ-воды и шаблонных фраз, сохраняет черновик в контент-план в <b>2. План</b> и присылает тебе на утверждение.", case_ai_style)]
    ]
    case3_table = Table(case3_data, colWidths=[500])
    case3_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD_BG),
        ('BOX', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(case3_table)
    
    story.append(PageBreak())

    # --- СТРАНИЦА 4: С ЧЕГО НАЧАТЬ & СВЯЗКИ ---
    story.append(Paragraph("🚀 С чего начать?", h1_style))
    story.append(Paragraph("Просто запиши свое первое голосовое сообщение в Телеграм-бот. Например: <i>«Бот, привет! Давай начнем. Запиши мои тарифы на консалтинг и аудит...»</i>. И наблюдай, как твоя База знаний начинает наполняться полезными цифровыми активами, освобождая твое драгоценное время.", body_style))
    
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceAfter=15))

    story.append(Paragraph("🔗 Полезные ссылки твоей Базы знаний:", h1_style))
    story.append(Paragraph("<font color=\"#d8b46a\">•</font> Основной манифест оцифровки: <b>методология-РОСТ</b>", bullet_style))
    story.append(Paragraph("<font color=\"#d8b46a\">•</font> Стандарты фирменного стиля: <b>дизайн-код-РОСТ</b>", bullet_style))
    story.append(Paragraph("<font color=\"#d8b46a\">•</font> Настройка выдачи лид-магнита в Директ: <b>воронка-ChatPlace</b>", bullet_style))
    
    story.append(Spacer(1, 20))
    
    # Главный результат (Темно-золотая карточка РОСТ-Стиль)
    result_title = ParagraphStyle('RT', parent=styles['Normal'], fontName='Arial-Bold', fontSize=10.5, leading=13, textColor=COLOR_GOLD, spaceAfter=4)
    result_body = ParagraphStyle('RB', parent=styles['Normal'], fontName='Arial', fontSize=9.5, leading=14, textColor=COLOR_WHITE)
    
    result_data = [
        [Paragraph("ГЛАВНЫЙ РЕЗУЛЬТАТ ДЛЯ ПРЕДПРИНИМАТЕЛЯ:", result_title)],
        [Paragraph("Каждый оцифрованный регламент или предложение во Втором Мозге - это твой личный цифровой актив. Он не уволится и не заболеет, работает 24/7 и полностью освобождает твое личное время для жизни и крупных сделок.", result_body)]
    ]
    result_table = Table(result_data, colWidths=[500])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a150e')),
        ('BOX', (0,0), (-1,-1), 1, COLOR_GOLD),
        ('LINEBEFORE', (0,0), (0,-1), 4.0, COLOR_GOLD),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(result_table)

    # Сборка документа
    doc.build(story, onFirstPage=draw_cover_page, onLaterPages=draw_later_page)
    print("PDF успешно сгенерирован в едином стиле по пути:", pdf_path)

if __name__ == "__main__":
    generate_pdf()
