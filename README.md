# AxonHorizon - Социальная сеть для научного сообщества

Социальная платформа для ученых, исследователей и научных сотрудников с функциями AI-анализа данных.

## Основные возможности

- **Социальная сеть** - профили, друзья, лента публикаций
- **Научные сообщества** - тематические группы по областям знаний
- **AI-анализ** - анализ научных данных с помощью DeepSeek AI
- **Чат** - общение между пользователями
- **Рекомендации** - умные рекомендации по статьям и коллегам

## Технологический стек

- **Backend**: Django 4.2, Django REST Framework
- **База данных**: SQLite (разработка), PostgreSQL (продакшен)
- **Аутентификация**: JWT токены
- **AI/ML**: DeepSeek API, OpenRouter
- **Frontend**: Bootstrap 5, JavaScript
- **Кэширование**: Redis/MongoDB

## Установка и запуск

1. **Клонируйте репозиторий**

 git clone https://github.com/your-username/AxonHorizon.git
cd AxonHorizon

2. **Создайте виртуальное окружение**

**python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

3. **Установите зависимости**

pip install -r requirements.txt

4. **Примените миграции**

python manage.py migrate

5. **Создайте суперпользователя**

python manage.py createsuperuser

6. **Запустите сервер**

python manage.py runserver