"""
Конфигурация бота Рекламный Инспектор
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Админ чат ID (для уведомлений)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

# Путь к папке с контекстом агента
AGENT_CONTEXT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "рекламный_инспектор",
    "_КОНТЕКСТ"
)

# Путь к папке для сохранения отчетов
REPORTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "рекламный_инспектор",
    "_ДАННЫЕ",
    "проверки"
)

# База данных
# Railway автоматически создаст PostgreSQL и установит DATABASE_URL
# Если DATABASE_URL не установлен, используется SQLite для локальной разработки
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Обязательный дисклеймер (точный текст из закона)
REQUIRED_DISCLAIMER = (
    "Банкротство влечет негативные последствия, в том числе ограничения на получение кредита "
    "и повторное банкротство в течение пяти лет. Предварительно обратитесь к своему кредитору и в МФЦ."
)

# Минимальный размер дисклеймера (% от площади)
MIN_DISCLAIMER_SIZE = 7
