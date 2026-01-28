"""
Telegram бот Рекламный Инспектор (ЛИД-МАГНИТ)
Проверка рекламы банкротства на соответствие ФЗ "О рекламе"
"""
import logging
import os
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)
from telegram.constants import ParseMode

from config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, LOG_LEVEL, LOG_FORMAT
from analyzer.material_analyzer import MaterialAnalyzer
from reports.report_generator import ReportGenerator
from reports.pdf_generator import PDFGenerator
from database import Database

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Проверка обязательных переменных окружения
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не установлен! Установите переменную окружения.")
    raise ValueError("TELEGRAM_BOT_TOKEN обязателен для работы бота")

# Инициализация компонентов
try:
    logger.info("Инициализация компонентов...")
    analyzer = MaterialAnalyzer()
    logger.info("MaterialAnalyzer инициализирован")
    report_generator = ReportGenerator()
    logger.info("ReportGenerator инициализирован")
    pdf_generator = PDFGenerator()
    logger.info("PDFGenerator инициализирован")
    db = Database()
    logger.info("Database инициализирована")
    logger.info("Все компоненты инициализированы успешно")
except Exception as e:
    logger.error(f"Ошибка инициализации компонентов: {e}", exc_info=True)
    print(f"ERROR: Ошибка инициализации компонентов: {e}")
    import traceback
    traceback.print_exc()
    raise

# Состояния для регистрации
ASKING_NAME, ASKING_PHONE, ASKING_GDPR = range(3)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - начало регистрации или приветствие"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Проверяем, зарегистрирован ли пользователь
    if db.is_user_registered(telegram_id):
        user_data = db.get_user(telegram_id)
        checks_count = db.get_user_checks_count(telegram_id)
        
        welcome_text = f"""
🔍 **РЕКЛАМНЫЙ ИНСПЕКТОР**

С возвращением, {user_data.get('full_name', user.first_name)}!

📊 Ваша статистика:
• Проверок выполнено: {checks_count}

**Как использовать:**
• Отправь URL сайта — проверю на нарушения
• Отправь текст объявления — проверю текст
• Получишь PDF-отчет с детальными рекомендациями

**Команды:**
/help — Справка
/profile — Мой профиль
/stats — Статистика

Отправь мне URL или текст для проверки! 👇
"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Начинаем регистрацию
        welcome_text = f"""
🔍 **РЕКЛАМНЫЙ ИНСПЕКТОР**

Привет, {user.first_name}!

Я проверяю рекламу банкротства на соответствие ФЗ "О рекламе".

**Что я делаю:**
✅ Проверяю сайты, тексты, объявления
✅ Нахожу нарушения ФЗ "О рекламе"
✅ Даю рекомендации по исправлению
✅ Отправляю PDF-отчет

**Для начала работы нужна регистрация:**

Как тебя зовут? (Имя и Фамилия)
"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ASKING_NAME


async def asking_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем имя пользователя"""
    full_name = update.message.text.strip()
    
    # Сохраняем имя в контекст
    context.user_data['full_name'] = full_name
    
    await update.message.reply_text(
        f"Отлично, {full_name}!\n\n"
        "Теперь отправь свой номер телефона.\n\n"
        "Можешь:\n"
        "• Написать вручную (например: +79991234567)\n"
        "• Или нажать кнопку ниже 👇",
        reply_markup=ReplyKeyboardMarkup(
            [[{"text": "📱 Отправить номер", "request_contact": True}]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    
    return ASKING_PHONE


async def asking_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем телефон пользователя"""
    # Проверяем, пришел ли контакт или текст
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()
    
    # Сохраняем телефон в контекст
    context.user_data['phone'] = phone
    
    # Показываем согласие на обработку данных
    keyboard = [
        [
            InlineKeyboardButton("✅ Принимаю", callback_data='gdpr_accept'),
            InlineKeyboardButton("❌ Отказываюсь", callback_data='gdpr_decline')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    gdpr_text = """
📋 **СОГЛАСИЕ НА ОБРАБОТКУ ПЕРСОНАЛЬНЫХ ДАННЫХ**

Для использования бота необходимо согласие на обработку персональных данных.

**Какие данные собираем:**
• Имя и фамилия
• Номер телефона
• Telegram ID и username
• История проверок материалов

**Для чего используем:**
• Предоставление услуги проверки рекламы
• Отправка отчетов
• Статистика использования

**Гарантии:**
• Данные защищены и не передаются третьим лицам
• Используются только для предоставления услуги
• Можно запросить удаление в любой момент

Обработка данных осуществляется в соответствии с ФЗ-152 "О персональных данных".

Принимаешь условия?
"""
    
    await update.message.reply_text(
        gdpr_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    
    return ASKING_GDPR


async def gdpr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка согласия на GDPR"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'gdpr_accept':
        # Регистрируем пользователя
        user = update.effective_user
        telegram_id = str(user.id)
        username = user.username or "no_username"
        full_name = context.user_data.get('full_name', user.first_name)
        phone = context.user_data.get('phone', 'не указан')
        
        # Сохраняем в базу
        success = db.register_user(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            phone=phone,
            gdpr_consent=True
        )
        
        if success:
            # Уведомляем админа о новой регистрации
            if ADMIN_CHAT_ID:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"""
🆕 **Новая регистрация в Рекламном Инспекторе!**

👤 Имя: {full_name}
📱 Телефон: {phone}
🆔 Username: @{username}
📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}
""",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            # Приветствуем пользователя
            await query.edit_message_text(
                f"""
✅ **Регистрация завершена!**

Спасибо, {full_name}!

Теперь можешь отправлять материалы для проверки:

📌 **Отправь мне:**
• URL сайта (например: https://site.ru)
• Текст объявления
• Ссылку на соцсети

📄 В ответ получишь **PDF-отчет** с:
• Вердиктом о соответствии ФЗ
• Списком нарушений
• Детальными рекомендациями по исправлению

Отправь материал для проверки! 👇
""",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=ReplyKeyboardRemove()
            )
            
            return ConversationHandler.END
        else:
            await query.edit_message_text(
                "❌ Ошибка регистрации. Попробуй еще раз: /start"
            )
            return ConversationHandler.END
    
    else:
        await query.edit_message_text(
            "❌ Без согласия на обработку данных бот не может работать.\n\n"
            "Если передумаешь — отправь /start"
        )
        return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена регистрации"""
    await update.message.reply_text(
        "Регистрация отменена. Если передумаешь — отправь /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📚 **Справка по боту**

**Основные команды:**
/start — Начало работы / Регистрация
/help — Эта справка
/profile — Мой профиль
/stats — Моя статистика

**Как проверить материал:**

1. **Сайт:** Отправь URL (например: `https://site.ru`)
2. **Текст:** Отправь текст объявления
3. **Соцсети:** Отправь ссылку на пост/профиль

**Что проверяю:**

✅ Обязательный дисклеймер (≥7% площади)
❌ Гарантии списания долгов
❌ Призывы не платить по кредитам
❌ Упоминания о списании долгов
❌ Гарантии возврата средств
❌ И другие запреты ФЗ "О рекламе"

**Результат:**
📄 PDF-отчет с детальными рекомендациями по исправлению
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /profile - профиль пользователя"""
    telegram_id = str(update.effective_user.id)
    
    if not db.is_user_registered(telegram_id):
        await update.message.reply_text(
            "Ты не зарегистрирован. Отправь /start для регистрации."
        )
        return
    
    user_data = db.get_user(telegram_id)
    checks_count = db.get_user_checks_count(telegram_id)
    
    profile_text = f"""
👤 **Мой профиль**

Имя: {user_data.get('full_name', 'Не указано')}
Телефон: {user_data.get('phone', 'Не указан')}
Username: @{user_data.get('username', 'не указан')}

📊 Статистика:
• Проверок выполнено: {checks_count}
• Дата регистрации: {user_data.get('registered_at', 'н/д')}

✅ Согласие на обработку данных: Да
"""
    
    await update.message.reply_text(
        profile_text,
        parse_mode=ParseMode.MARKDOWN
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика админа"""
    telegram_id = str(update.effective_user.id)
    
    # Только для админа
    if telegram_id != ADMIN_CHAT_ID:
        await update.message.reply_text("У тебя нет доступа к этой команде.")
        return
    
    stats = db.get_stats()
    
    stats_text = f"""
📊 **СТАТИСТИКА БОТА**

👥 Всего пользователей: {stats['total_users']}
🔍 Всего проверок: {stats['total_checks']}
🆕 Регистраций сегодня: {stats['today_registrations']}

**Средняя активность:**
{stats['total_checks'] / max(stats['total_users'], 1):.1f} проверок на пользователя
"""
    
    await update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка материала (URL или текст)"""
    telegram_id = str(update.effective_user.id)
    
    # Проверяем регистрацию
    if not db.is_user_registered(telegram_id):
        await update.message.reply_text(
            "⚠️ Для проверки материалов нужна регистрация.\n\n"
            "Отправь /start для регистрации.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    text = update.message.text.strip()
    
    # Пропускаем команды
    if text.startswith('/'):
        return
    
    # Определяем тип материала
    is_url = text.startswith('http://') or text.startswith('https://')
    
    if is_url:
        await handle_url(update, context, text)
    else:
        await handle_text_material(update, context, text)


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Обработка URL"""
    telegram_id = str(update.effective_user.id)
    
    await update.message.reply_text("🔍 Анализирую сайт... Пожалуйста, подожди.")
    
    try:
        # Анализируем сайт
        analysis_result = analyzer.analyze_url(url)
        
        if analysis_result.get('error'):
            await update.message.reply_text(
                f"❌ Ошибка: {analysis_result['error']}\n\n"
                "Попробуй отправить текст материала."
            )
            return
        
        # Генерируем отчеты
        material_info = {
            'url': url,
            'type': 'Сайт'
        }
        
        # Отправляем краткий отчет
        await send_brief_report(update, context, analysis_result, material_info)
        
        # Генерируем HTML-отчет
        html_path = report_generator.save_report(analysis_result, material_info, format='html')
        
        # Конвертируем в PDF
        if html_path and os.path.exists(html_path):
            pdf_filename = os.path.basename(html_path).replace('.html', '')
            pdf_path = pdf_generator.generate_from_html_file(html_path, pdf_filename)
            
            if pdf_path and os.path.exists(pdf_path):
                # Отправляем PDF
                with open(pdf_path, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        filename=f"Отчет_РекламныйИнспектор_{datetime.now().strftime('%Y%m%d')}.pdf",
                        caption="📄 Полный PDF-отчет с детальными рекомендациями"
                    )
                
                # Сохраняем проверку в базу
                db.save_check(
                    telegram_id=telegram_id,
                    material_type='site',
                    material_url=url,
                    verdict=analysis_result.get('verdict', 'ERROR'),
                    violations_count=analysis_result.get('total_violations', 0),
                    report_path=pdf_path
                )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе URL: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при анализе сайта.\n\n"
            "Попробуй отправить текст материала."
        )


async def handle_text_material(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка текста"""
    telegram_id = str(update.effective_user.id)
    
    await update.message.reply_text("🔍 Анализирую текст... Пожалуйста, подожди.")
    
    try:
        # Анализируем текст
        analysis_result = analyzer.analyze_text(text, material_type='text')
        
        # Генерируем отчеты
        material_info = {
            'text': text[:100],
            'type': 'Текст объявления'
        }
        
        # Отправляем краткий отчет
        await send_brief_report(update, context, analysis_result, material_info)
        
        # Генерируем HTML-отчет
        html_path = report_generator.save_report(analysis_result, material_info, format='html')
        
        # Конвертируем в PDF
        if html_path and os.path.exists(html_path):
            pdf_filename = os.path.basename(html_path).replace('.html', '')
            pdf_path = pdf_generator.generate_from_html_file(html_path, pdf_filename)
            
            if pdf_path and os.path.exists(pdf_path):
                # Отправляем PDF
                with open(pdf_path, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        filename=f"Отчет_РекламныйИнспектор_{datetime.now().strftime('%Y%m%d')}.pdf",
                        caption="📄 Полный PDF-отчет с детальными рекомендациями"
                    )
                
                # Сохраняем проверку в базу
                db.save_check(
                    telegram_id=telegram_id,
                    material_type='text',
                    material_url=text[:100],
                    verdict=analysis_result.get('verdict', 'ERROR'),
                    violations_count=analysis_result.get('total_violations', 0),
                    report_path=pdf_path
                )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе текста: {e}")
        await update.message.reply_text("❌ Произошла ошибка при анализе текста.")


async def send_brief_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    analysis_result: dict,
    material_info: dict
):
    """Отправляет краткий отчет пользователю"""
    verdict = analysis_result.get('verdict', 'ERROR')
    
    verdict_emoji = {
        'СООТВЕТСТВУЕТ': '✅',
        'ЧАСТИЧНОЕ_НАРУШЕНИЕ': '⚠️',
        'НЕ_СООТВЕТСТВУЕТ': '❌',
        'КРИТИЧЕСКИЕ_НАРУШЕНИЯ': '🚨',
        'ERROR': '❌'
    }
    
    emoji = verdict_emoji.get(verdict, '❓')
    verdict_text = verdict.replace('_', ' ')
    
    # Формируем краткий отчет
    report_text = f"""
{emoji} **ВЕРДИКТ: {verdict_text}**

📋 **Материал:** {material_info.get('url', material_info.get('text', 'Не указано'))[:80]}
📅 **Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

"""
    
    # Дисклеймер
    disclaimer = analysis_result.get('disclaimer', {})
    if disclaimer.get('found'):
        report_text += "✅ **Дисклеймер:** Найден\n"
    else:
        report_text += "❌ **Дисклеймер:** Не найден\n"
    
    # Нарушения
    total_violations = analysis_result.get('total_violations', 0)
    
    if total_violations > 0:
        report_text += f"\n❌ **Нарушений найдено:** {total_violations}\n"
    else:
        report_text += "\n✅ **Нарушений не обнаружено**\n"
    
    report_text += "\n📄 Загружаю PDF-отчет с рекомендациями..."
    
    await update.message.reply_text(
        report_text,
        parse_mode=ParseMode.MARKDOWN
    )


def main():
    """Запуск бота"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN не установлен!")
            print("ERROR: TELEGRAM_BOT_TOKEN не установлен!")
            return
        
        logger.info("Начинаю запуск бота...")
        logger.info(f"LOG_LEVEL: {LOG_LEVEL}")
        logger.info(f"ADMIN_CHAT_ID: {'установлен' if ADMIN_CHAT_ID else 'не установлен'}")
        
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        logger.info("Приложение создано успешно")
        
        # Регистрация пользователя (ConversationHandler)
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start_command)],
            states={
                ASKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, asking_name)],
                ASKING_PHONE: [
                    MessageHandler(filters.CONTACT, asking_phone),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, asking_phone)
                ],
                ASKING_GDPR: [CallbackQueryHandler(gdpr_callback)]
            },
            fallbacks=[CommandHandler("cancel", cancel_registration)]
        )
        
        application.add_handler(conv_handler)
        
        # Остальные команды
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("stats", stats_command))
        
        # Обработка материалов
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_material))
        
        # Запускаем бота
        logger.info("🔍 Рекламный Инспектор запущен!")
        print("INFO: Бот запущен успешно!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        print(f"ERROR: Критическая ошибка: {e}")
        raise


if __name__ == '__main__':
    main()
