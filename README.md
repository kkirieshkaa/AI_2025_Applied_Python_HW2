# AI_2025_Applied_Python_HW2
# Репозиторий для ДЗ 2 - Telegram-бот для расчёта нормы воды, калорий и трекинга активности.

## Требования
- Python **3.10+**
- Telegram Bot Token
- (опционально) OpenWeather API Key

## Установка и запуск

### 1. Создание виртуального окружения
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Переменные окружения
Создайте файл .env в корне проекта:
```bash
BOT_TOKEN=your_telegram_bot_token
OPENWEATHER_API_KEY=your_openweather_api_key
```
OPENWEATHER_API_KEY не является обязательным.
Если ключ не указан, температура просто не учитывается в расчётах.

### 4. Запуск бота
```bash
python bot.py
```

### 5. Команды бота

- /start — начало работы
- /help — список команд
- /set_profile — настройка профиля
- /log_water <мл> — логирование воды
- /log_food <продукт> — логирование еды
- /log_workout <тип> <минуты> — логирование тренировки
- /check_progress — текущий прогресс
- /profile — просмотр профиля
- /plot — график дневного прогресса
