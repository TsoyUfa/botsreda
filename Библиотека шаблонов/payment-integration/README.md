# 💳 Шаблон интеграции с платежными системами

## Описание шаблона

Готовые решения для интеграции платежных систем в Telegram-ботов, веб-приложения и CRM. Включает настройки для популярных платежных провайдеров, примеры кода и руководство по безопасности.

## 🏗️ Структура шаблона

```
payment-integration/
├── README.md                     # Этот файл
├── providers/                    # Платежные провайдеры
│   ├── yookassa/                # ЮKassa
│   │   ├── README.md
│   │   ├── config.py
│   │   ├── yookassa_service.py
│   │   └── webhooks.py
│   ├── telegram-payments/       # Telegram Payments
│   │   ├── README.md
│   │   ├── config.py
│   │   ├── telegram_payments.py
│   │   └── handlers.py
│   ├── cloudpayments/           # CloudPayments
│   │   ├── README.md
│   │   ├── config.py
│   │   ├── cloudpayments.py
│   │   └── webhooks.py
│   └── stripe/                  # Stripe (международные)
│       ├── README.md
│       ├── config.py
│       ├── stripe_service.py
│       └── webhooks.py
├── templates/                   # Шаблоны платежных страниц
│   ├── payment_page.html
│   ├── success_page.html
│   ├── error_page.html
│   └── invoice_template.html
├── services/                    # Сервисы обработки
│   ├── payment_service.py       # Основной сервис
│   ├── notification_service.py  # Уведомления
│   ├── security_service.py      # Безопасность
│   └── log_service.py          # Логирование
├── examples/                    # Примеры использования
│   ├── telegram_bot_example.py  # Telegram-бот
│   ├── web_app_example.py       # Веб-приложение
│   ├── crm_integration.py       # Интеграция с CRM
│   └── subscription_example.py   # Подписки
├── docs/                        # Документация
│   ├── security-guide.md        # Руководство по безопасности
│   ├── compliance-152-fz.md     # Соответствие 152-ФЗ
│   ├── testing-guide.md         # Тестирование платежей
│   └── troubleshooting.md        # Решение проблем
└── scripts/                     # Скрипты
    ├── migrate_payments.py      # Миграция платежей
    ├── reconcile_payments.py    # Сверка платежей
    └── backup_payments.py       # Бэкап платежных данных
```

## 🚀 Быстрый старт

### 1. Выбор платежного провайдера

| Провайдер | Комиссия | Мин. сумма | Особенности | Рекомендация |
|-----------|----------|------------|------------|--------------|
| ЮKassa | 2.9% + 30₽ | 1₽ | Лучше для РФ, СБП, рассрочка | ✅ Для РФ |
| Telegram Payments | 0% | 75₽ | Удобно для пользователей | ✅ Для Telegram |
| CloudPayments | 2.5% | 10₽ | Международные платежи | ⚠️ Для международных |
| Stripe | 2.9% + 30¢ | $0.50 | Глобальные платежи | ⚠️ Для международных |

### 2. Копирование шаблона

```bash
# Создайте новую папку для вашего проекта
mkdir my-payment-system
cd my-payment-system

# Скопируйте шаблон выбранного провайдера
cp -r "../Библиотека шаблонов/payment-integration/providers/yookassa/*" .
```

### 3. Настройка окружения

```bash
# Создайте .env файл
cp .env.example .env

# Заполните данные
nano .env
```

Пример заполнения `.env`:

```bash
# ЮKassa
YOOKASSA_SHOP_ID=123456
YOOKASSA_API_KEY=test_123456
YOOKASSA_SECRET_KEY=test_789012

# Telegram
BOT_TOKEN=ваш_бот_токен
PAYMENT_PROVIDER_TOKEN=ваш_платежный_токен

# Безопасность
WEBHOOK_SECRET=ваш_секретный_ключ
ENCRYPTION_KEY=ваш_ключ_шифрования
```

### 4. Установка зависимостей

```bash
pip install yookassa python-dotenv fastapi uvicorn
```

## 💳 Интеграция с ЮKassa (Рекомендуется)

### Настройка ЮKassa

1. **Регистрация в ЮKassa**
   - Перейдите на [yookassa.ru](https://yookassa.ru/)
   - Зарегистрируйте магазин
   - Получите API ключи

2. **Настройка вебхуков**
   ```python
   # webhooks.py
   from fastapi import FastAPI, Request, HTTPException
   from yookassa import Configuration
   import hmac
   import hashlib

   app = FastAPI()

   async def webhook_handler(request: Request):
       # Проверка подписи
       signature = request.headers.get('Content-Signature')
       payload = await request.body()
       
       if not verify_webhook(signature, payload):
           raise HTTPException(status_code=400, detail="Invalid signature")
       
       # Обработка платежа
       payment_data = await request.json()
       await process_payment(payment_data)
       
       return {"status": "ok"}
   ```

3. **Создание платежа**
   ```python
   # yookassa_service.py
   from yookassa import Payment, Configuration

   Configuration.account_id = YOOKASSA_SHOP_ID
   Configuration.secret_key = YOOKASSA_SECRET_KEY

   async def create_payment(amount, description, user_id):
       payment = Payment.create({
           "amount": {
               "value": amount,
               "currency": "RUB"
           },
           "confirmation": {
               "type": "redirect",
               "return_url": "https://your-site.com/success"
           },
           "description": description,
           "metadata": {
               "user_id": user_id
           }
       })
       
       return payment
   ```

## 📱 Интеграция с Telegram Payments

### Настройка в Telegram

1. **Настройка платежей в боте**
   - Напишите @BotFather
   - Команда `/payments`
   - Выберите вашего бота
   - Настройте платежи

2. **Отправка счета**
   ```python
   # telegram_payments.py
   from aiogram import Bot, types

   async def send_invoice(bot: Bot, user_id: int):
       await bot.send_invoice(
           chat_id=user_id,
           title="Премиум-доступ",
           description="Полный доступ ко всем курсам",
           payload="premium_access",
           provider_token=PAYMENT_PROVIDER_TOKEN,
           currency="RUB",
           prices=[
               types.LabeledPrice(
                   label="Премиум-доступ",
                   amount=499000  # 4990 рублей в копейках
               )
           ],
           start_parameter="premium_access"
       )
   ```

3. **Обработка платежа**
   ```python
   # handlers.py
   from aiogram import Dispatcher

   async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
       await pre_checkout_query.answer(ok=True)

   async def successful_payment(message: types.Message):
       user_id = message.from_user.id
       await activate_premium(user_id)
       
       await message.answer(
           "✅ Платеж успешно получен! "
           "Ваш премиум-доступ активирован."
       )
   ```

## 🔒 Интеграция с CloudPayments

### Настройка CloudPayments

1. **Регистрация**
   - Перейдите на [cloudpayments.ru](https://cloudpayments.ru/)
   - Зарегистрируйте магазин
   - Получите Public ID и API Secret

2. **Настройка виджета**
   ```html
   <!-- payment_page.html -->
   <div id="payment-form"></div>
   
   <script src="https://widget.cloudpayments.ru/bundles/cloudpayments"></script>
   <script>
       const widget = new cp.CloudPayments();
       
       widget.pay('charge', {
           publicId: 'pk_123456',
           description: 'Премиум-доступ',
           amount: 4990,
           currency: 'RUB',
           invoiceId: '12345',
           accountId: 'user_123',
           data: {
               user_id: 123
           }
       });
   </script>
   ```

3. **Обработка вебхуков**
   ```python
   # cloudpayments.py
   from fastapi import FastAPI, Request

   app = FastAPI()

   @app.post("/webhooks/cloudpayments")
   async def cloudpayments_webhook(request: Request):
       data = await request.json()
       
       if data.get('Code') == 0:  # Успешный платеж
           await process_successful_payment(data)
       
       return {"code": 0}
   ```

## 🛡️ Безопасность и соответствие

### Защита данных (152-ФЗ)

1. **Хранение данных**
   - Не храните номера карт
   - Используйте токенизацию
   - Храните только ID платежей

2. **Шифрование**
   ```python
   # security_service.py
   from cryptography.fernet import Fernet
   
   class SecurityService:
       def __init__(self, key):
           self.cipher = Fernet(key)
       
       def encrypt(self, data):
           return self.cipher.encrypt(data.encode())
       
       def decrypt(self, encrypted_data):
           return self.cipher.decrypt(encrypted_data).decode()
   ```

3. **Вебхуки**
   ```python
   # webhooks.py
   def verify_webhook(signature, payload):
       secret = WEBHOOK_SECRET.encode()
       expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
       return hmac.compare_digest(expected, signature)
   ```

### Рекомендации по безопасности

1. **Используйте HTTPS**
   - Обязательно для production
   - Сертификаты от Let's Encrypt бесплатно

2. **Валидация данных**
   ```python
   # validation.py
   from pydantic import BaseModel, condecimal
   from decimal import Decimal

   class PaymentRequest(BaseModel):
       amount: condecimal(gt=0, le=1000000)  # от 0 до 1 млн
       currency: str = "RUB"
       description: str
       user_id: int
   ```

3. **Логирование**
   ```python
   # log_service.py
   import logging
   from datetime import datetime

   class PaymentLogger:
       def __init__(self):
           self.logger = logging.getLogger('payments')
       
       def log_payment(self, payment_data):
           self.logger.info({
               "timestamp": datetime.now().isoformat(),
               "payment_id": payment_data.get("id"),
               "amount": payment_data.get("amount"),
               "status": payment_data.get("status")
           })
   ```

## 📊 Мониторинг и аналитика

### Отслеживание платежей

```python
# monitoring.py
from datetime import datetime, timedelta
import statistics

class PaymentMonitor:
    def get_daily_stats(self):
        today = datetime.now().date()
        payments = self.get_payments_by_date(today)
        
        return {
            "count": len(payments),
            "total": sum(p["amount"] for p in payments),
            "average": statistics.mean(p["amount"] for p in payments),
            "conversion_rate": self.calculate_conversion_rate(payments)
        }
    
    def get_failed_payments(self):
        return self.get_payments_by_status("failed")
```

### Оповещения о проблемах

```python
# notification_service.py
class NotificationService:
    async def alert_failed_payment(self, payment_data):
        message = f"❌ Ошибка платежа: {payment_data.get('id')}"
        await self.send_admin_alert(message)
    
    async def alert_high_amount(self, payment_data):
        if payment_data.get("amount") > 50000:
            message = f"💰 Крупный платеж: {payment_data.get('amount')}₽"
            await self.send_admin_alert(message)
```

## 🧪 Тестирование платежей

### Тестовые режимы

1. **ЮKassa тест-режим**
   ```python
   # test_yookassa.py
   Configuration.account_id = TEST_SHOP_ID
   Configuration.secret_key = TEST_SECRET_KEY
   
   async def test_payment():
       payment = await create_payment(1.00, "Тестовый платеж", 123)
       assert payment.status == "pending"
   ```

2. **Telegram Payments тест**
   ```python
   # test_telegram.py
   async def test_telegram_payment():
       # Используйте тестовый токен
       test_token = "TEST:PAYMENT_TOKEN"
       
       await send_invoice(bot, TEST_USER_ID)
   ```

### Чек-лист тестирования

- [ ] Создание тестового платежа
- [ ] Обработка успешного платежа
- [ ] Обработка ошибки платежа
- [ ] Проверка вебхуков
- [ ] Тестирование валидации
- [ ] Тестирование безопасности
- [ ] Нагрузочное тестирование

## 🐛 Решение проблем

### Частые проблемы

1. **Платеж не проходит**
   - Проверьте API ключи
   - Убедитесь, что аккаунт верифицирован
   - Проверьте ограничения суммы

2. **Вебхуки не работают**
   - Проверьте URL вебхука
   - Убедитесь, что сервер доступен
   - Проверьте подпись вебхука

3. **Telegram Payments не работают**
   - Проверьте настройки в @BotFather
   - Убедитесь, что товарный аккаунт активен
   - Проверьте валюту и сумму

### Логирование ошибок

```python
# error_handler.py
import logging

class PaymentErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger('payment_errors')
    
    def handle_error(self, error, payment_data=None):
        error_info = {
            "error": str(error),
            "payment_data": payment_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.error(error_info)
        
        # Отправка уведомления администратору
        self.send_alert(error_info)
```

## 🚀 Деплой

### Настройка production

1. **Environment variables**
   ```bash
   # .env.production
   YOOKASSA_SHOP_ID=${YOOKASSA_SHOP_ID}
   YOOKASSA_API_KEY=${YOOKASSA_API_KEY}
   YOOKASSA_SECRET_KEY=${YOOKASSA_SECRET_KEY}
   WEBHOOK_SECRET=${WEBHOOK_SECRET}
   ENCRYPTION_KEY=${ENCRYPTION_KEY}
   ```

2. **Docker-контейнер**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Настройка домена и HTTPS**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location /webhooks/ {
           proxy_pass http://localhost:8000;
       }
   }
   ```

## 📞 Поддержка

Если нужна помощь с интеграцией:
- Telegram: @anton_tsoy
- Документация ЮKassa: https://yookassa.ru/developers
- Документация Telegram Payments: https://core.telegram.org/bots/payments

---

*Этот шаблон основан на реальных платежных интеграциях с обработкой 1000+ платежей в месяц*