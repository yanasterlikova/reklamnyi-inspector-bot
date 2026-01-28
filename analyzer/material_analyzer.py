"""
Анализатор рекламных материалов
Проверяет материалы на соответствие ФЗ "О рекламе"
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from config import REQUIRED_DISCLAIMER, MIN_DISCLAIMER_SIZE


class MaterialAnalyzer:
    """Анализатор рекламных материалов на соответствие ФЗ "О рекламе" """
    
    def __init__(self):
        self.required_disclaimer = REQUIRED_DISCLAIMER
        self.min_disclaimer_size = MIN_DISCLAIMER_SIZE
        
        # Запрещенные слова и фразы
        self.prohibited_patterns = {
            'guarantees': [
                r'гарантируем',
                r'гарантия',
                r'100%[\s]*списание',
                r'полное[\s]*списание',
                r'гарантированное[\s]*освобождение',
                r'обещаем[\s]*списание',
                r'обещаем[\s]*освобождение',
            ],
            'calls_not_pay': [
                r'не[\s]*платите',
                r'перестаньте[\s]*платить',
                r'прекратите[\s]*платежи',
                r'можно[\s]*не[\s]*платить',
                r'не[\s]*исполняйте[\s]*обязательства',
            ],
            'state_system': [
                r'государство[\s]*создало',
                r'государственная[\s]*программа',
                r'государство[\s]*помогает',
                r'система[\s]*освобождения',
            ],
            'mention_exemption': [
                r'спишем[\s]*долги',
                r'списание[\s]*долгов',
                r'освобождение[\s]*от[\s]*долгов',
                r'освобождение[\s]*от[\s]*кредитов',
                r'избавимся[\s]*от[\s]*долгов',
                r'долг[\s]*=[\s]*0',
                r'долг[\s]*равен[\s]*нулю',
            ],
            'property_preservation': [
                r'сохраним[\s]*имущество',
                r'сохраним[\s]*квартиру',
                r'сохраним[\s]*машину',
                r'гарантируем[\s]*сохранение',
            ],
            'money_back': [
                r'вернем[\s]*деньги',
                r'компенсируем[\s]*расходы',
                r'гарантия[\s]*возврата',
                r'деньги[\s]*назад',
            ],
            'take_loans': [
                r'возьмите[\s]*кредит',
                r'берите[\s]*займы',
                r'кредит[\s]*на[\s]*банкротство',
            ],
            'any_cases': [
                r'беремся[\s]*за[\s]*любые[\s]*дела',
                r'не[\s]*важно[\s]*на[\s]*что',
                r'не[\s]*важно[\s]*сколько',
                r'лудоман[\s]*не[\s]*проблема',
            ],
        }
    
    def analyze_url(self, url: str) -> Dict:
        """
        Анализирует сайт по URL
        
        Args:
            url: URL сайта для проверки
            
        Returns:
            Dict с результатами анализа
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлекаем текст
            text = soup.get_text(separator=' ', strip=True)
            
            # Удаляем лишние пробелы
            text = ' '.join(text.split())
            
            return self.analyze_text(text, material_type='site', url=url)
            
        except Exception as e:
            return {
                'error': f'Ошибка при загрузке сайта: {str(e)}',
                'verdict': 'ERROR'
            }
    
    def analyze_text(self, text: str, material_type: str = 'text', **kwargs) -> Dict:
        """
        Анализирует текст на наличие нарушений
        
        Args:
            text: Текст для анализа
            material_type: Тип материала (site, text, card)
            **kwargs: Дополнительные параметры (url, etc.)
            
        Returns:
            Dict с результатами анализа
        """
        text_lower = text.lower()
        
        # Проверка дисклеймера
        disclaimer_check = self._check_disclaimer(text)
        
        # Проверка запрещенных формулировок
        violations = self._check_prohibited_formulations(text_lower, text)
        
        # Формирование вердикта
        verdict = self._determine_verdict(disclaimer_check, violations)
        
        return {
            'verdict': verdict,
            'material_type': material_type,
            'url': kwargs.get('url'),
            'disclaimer': disclaimer_check,
            'violations': violations,
            'total_violations': sum(len(v) for v in violations.values() if v),
        }
    
    def _check_disclaimer(self, text: str) -> Dict:
        """
        Проверяет наличие и корректность дисклеймера
        
        Returns:
            Dict с результатами проверки
        """
        disclaimer_lower = self.required_disclaimer.lower()
        text_lower = text.lower()
        
        # Точное совпадение
        if disclaimer_lower in text_lower:
            return {
                'found': True,
                'exact_match': True,
                'location': 'found',
                'size_check': 'needs_calculation',  # Для сайтов нужен точный расчет
                'readable': True,
                'visible': 'needs_check',  # Нужно проверить видимость
            }
        
        # Проверка на частичное совпадение
        key_phrases = [
            'банкротство влечет негативные последствия',
            'ограничения на получение кредита',
            'повторное банкротство в течение пяти лет',
        ]
        
        found_phrases = sum(1 for phrase in key_phrases if phrase in text_lower)
        
        if found_phrases >= 2:
            return {
                'found': True,
                'exact_match': False,
                'location': 'found',
                'size_check': 'needs_calculation',
                'readable': True,
                'visible': 'needs_check',
                'warning': 'Дисклеймер найден, но текст может быть изменен'
            }
        
        return {
            'found': False,
            'exact_match': False,
            'location': 'not_found',
            'size_check': 'not_applicable',
            'readable': False,
            'visible': False,
        }
    
    def _check_prohibited_formulations(self, text_lower: str, text_original: str) -> Dict:
        """
        Проверяет наличие запрещенных формулировок
        
        Returns:
            Dict с найденными нарушениями по категориям
        """
        violations = {
            'guarantees': [],
            'calls_not_pay': [],
            'state_system': [],
            'mention_exemption': [],
            'property_preservation': [],
            'money_back': [],
            'take_loans': [],
            'any_cases': [],
        }
        
        # Ищем запрещенные фразы
        for category, patterns in self.prohibited_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    # Извлекаем контекст (50 символов до и после)
                    start = max(0, match.start() - 50)
                    end = min(len(text_original), match.end() + 50)
                    context = text_original[start:end]
                    
                    violations[category].append({
                        'phrase': match.group(),
                        'context': context.strip(),
                        'position': match.start()
                    })
        
        return violations
    
    def _determine_verdict(self, disclaimer_check: Dict, violations: Dict) -> str:
        """
        Определяет вердикт на основе проверок
        
        Returns:
            Вердикт: СООТВЕТСТВУЕТ, ЧАСТИЧНОЕ_НАРУШЕНИЕ, НЕ_СООТВЕТСТВУЕТ, КРИТИЧЕСКИЕ_НАРУШЕНИЯ
        """
        total_violations = sum(len(v) for v in violations.values() if v)
        
        # Критические нарушения
        if not disclaimer_check.get('found') or total_violations > 5:
            return 'КРИТИЧЕСКИЕ_НАРУШЕНИЯ'
        
        # Не соответствует
        if total_violations > 0:
            return 'НЕ_СООТВЕТСТВУЕТ'
        
        # Частичное нарушение
        if not disclaimer_check.get('exact_match') or disclaimer_check.get('warning'):
            return 'ЧАСТИЧНОЕ_НАРУШЕНИЕ'
        
        # Соответствует
        return 'СООТВЕТСТВУЕТ'
