"""
База данных для хранения пользователей
Поддержка PostgreSQL (Railway) и SQLite (локальная разработка)
"""
import os
from datetime import datetime
from typing import Optional, Dict, List

# Определяем какой драйвер использовать
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL для Railway
    import psycopg2
    from psycopg2.extras import RealDictCursor
    USE_POSTGRESQL = True
else:
    # SQLite для локальной разработки
    import sqlite3
    USE_POSTGRESQL = False


class Database:
    """Работа с базой данных пользователей"""
    
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = db_path
        self.use_postgresql = USE_POSTGRESQL
        
        if not self.use_postgresql:
            # SQLite: создаем директорию если нужно
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.init_db()
    
    def _get_connection(self):
        """Получить соединение с базой данных"""
        if self.use_postgresql:
            return psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.use_postgresql:
            # PostgreSQL синтаксис
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(255),
                    full_name VARCHAR(255),
                    phone VARCHAR(50),
                    registered_at TIMESTAMP DEFAULT NOW(),
                    gdpr_consent INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Таблица проверок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    material_type VARCHAR(50),
                    material_url TEXT,
                    verdict VARCHAR(50),
                    violations_count INTEGER,
                    checked_at TIMESTAMP DEFAULT NOW(),
                    report_path TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
        else:
            # SQLite синтаксис (для локальной разработки)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id TEXT UNIQUE NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    phone TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    gdpr_consent INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    material_type TEXT,
                    material_url TEXT,
                    verdict TEXT,
                    violations_count INTEGER,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    report_path TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, telegram_id: str, username: str, full_name: str, phone: str, gdpr_consent: bool = True) -> bool:
        """
        Регистрация нового пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            username: Username пользователя
            full_name: Полное имя пользователя
            phone: Телефон пользователя
            gdpr_consent: Согласие на обработку данных
            
        Returns:
            True если регистрация успешна
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if self.use_postgresql:
                cursor.execute('''
                    INSERT INTO users (telegram_id, username, full_name, phone, gdpr_consent)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (telegram_id, username, full_name, phone, 1 if gdpr_consent else 0))
            else:
                cursor.execute('''
                    INSERT INTO users (telegram_id, username, full_name, phone, gdpr_consent)
                    VALUES (?, ?, ?, ?, ?)
                ''', (telegram_id, username, full_name, phone, 1 if gdpr_consent else 0))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if self.use_postgresql:
                import psycopg2
                if isinstance(e, psycopg2.IntegrityError):
                    # Пользователь уже существует
                    conn.close()
                    return False
            else:
                if isinstance(e, sqlite3.IntegrityError):
                    conn.close()
                    return False
            print(f"Ошибка регистрации: {e}")
            conn.close()
            return False
    
    def get_user(self, telegram_id: str) -> Optional[Dict]:
        """Получить пользователя по telegram_id"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.use_postgresql:
            cursor.execute('SELECT * FROM users WHERE telegram_id = %s', (telegram_id,))
        else:
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            if self.use_postgresql:
                # PostgreSQL возвращает tuple, конвертируем в dict
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            else:
                # SQLite уже возвращает Row объект
                return dict(row)
        return None
    
    def is_user_registered(self, telegram_id: str) -> bool:
        """Проверить, зарегистрирован ли пользователь"""
        user = self.get_user(telegram_id)
        return user is not None and user.get('is_active', 0) == 1
    
    def save_check(self, telegram_id: str, material_type: str, material_url: str, 
                   verdict: str, violations_count: int, report_path: str) -> bool:
        """
        Сохранить проверку в базу
        
        Args:
            telegram_id: ID пользователя
            material_type: Тип материала
            material_url: URL или описание материала
            verdict: Вердикт
            violations_count: Количество нарушений
            report_path: Путь к отчету
            
        Returns:
            True если сохранение успешно
        """
        try:
            user = self.get_user(telegram_id)
            if not user:
                return False
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if self.use_postgresql:
                cursor.execute('''
                    INSERT INTO checks (user_id, material_type, material_url, verdict, violations_count, report_path)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (user['id'], material_type, material_url, verdict, violations_count, report_path))
            else:
                cursor.execute('''
                    INSERT INTO checks (user_id, material_type, material_url, verdict, violations_count, report_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user['id'], material_type, material_url, verdict, violations_count, report_path))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка сохранения проверки: {e}")
            return False
    
    def get_user_checks_count(self, telegram_id: str) -> int:
        """Получить количество проверок пользователя"""
        user = self.get_user(telegram_id)
        if not user:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.use_postgresql:
            cursor.execute('SELECT COUNT(*) FROM checks WHERE user_id = %s', (user['id'],))
        else:
            cursor.execute('SELECT COUNT(*) FROM checks WHERE user_id = ?', (user['id'],))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users ORDER BY registered_at DESC')
        rows = cursor.fetchall()
        
        conn.close()
        
        if self.use_postgresql:
            # Конвертируем tuples в dicts
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        else:
            return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict:
        """Получить статистику"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.use_postgresql:
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM checks')
            total_checks = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(registered_at) = CURRENT_DATE
            ''')
            today_registrations = cursor.fetchone()[0]
        else:
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM checks')
            total_checks = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(registered_at) = DATE('now')
            ''')
            today_registrations = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_checks': total_checks,
            'today_registrations': today_registrations
        }
