"""
Генератор отчетов в форматах Markdown и HTML
"""
import os
from datetime import datetime
from typing import Dict
from config import REPORTS_PATH, REQUIRED_DISCLAIMER


class ReportGenerator:
    """Генератор отчетов о проверке рекламы"""
    
    def __init__(self):
        self.reports_path = REPORTS_PATH
        os.makedirs(self.reports_path, exist_ok=True)
    
    def generate_markdown(self, analysis_result: Dict, material_info: Dict) -> str:
        """
        Генерирует отчет в формате Markdown
        
        Args:
            analysis_result: Результаты анализа
            material_info: Информация о материале (url, type, etc.)
            
        Returns:
            Строка с отчетом в формате Markdown
        """
        verdict_emoji = {
            'СООТВЕТСТВУЕТ': '✅',
            'ЧАСТИЧНОЕ_НАРУШЕНИЕ': '⚠️',
            'НЕ_СООТВЕТСТВУЕТ': '❌',
            'КРИТИЧЕСКИЕ_НАРУШЕНИЯ': '🚨',
            'ERROR': '❌'
        }
        
        verdict = analysis_result.get('verdict', 'ERROR')
        emoji = verdict_emoji.get(verdict, '❓')
        
        report = f"""# 🔍 РЕКЛАМНЫЙ ИНСПЕКТОР | Проверка рекламы банкротства

**Дата проверки:** {datetime.now().strftime('%d.%m.%Y')}
**Материал:** {material_info.get('url', material_info.get('text', 'Не указано'))[:100]}
**Тип материала:** {material_info.get('type', 'Не указано')}

---

## 📊 ВЕРДИКТ

{emoji} {verdict.replace('_', ' ')}

"""
        
        if verdict == 'ERROR':
            report += f"**Ошибка:** {analysis_result.get('error', 'Неизвестная ошибка')}\n"
            return report
        
        # Дисклеймер
        disclaimer = analysis_result.get('disclaimer', {})
        report += self._format_disclaimer_section(disclaimer)
        
        # Нарушения
        violations = analysis_result.get('violations', {})
        report += self._format_violations_section(violations)
        
        # Рекомендации
        report += self._format_recommendations(disclaimer, violations)
        
        # Нормативная база
        report += self._format_legal_basis()
        
        return report
    
    def generate_html(self, analysis_result: Dict, material_info: Dict) -> str:
        """
        Генерирует отчет в формате HTML
        
        Args:
            analysis_result: Результаты анализа
            material_info: Информация о материале
            
        Returns:
            HTML-строка с отчетом
        """
        # Используем шаблон из существующего HTML-отчета
        # В реальной реализации здесь будет генерация HTML на основе анализа
        
        # Пока возвращаем простой HTML
        verdict = analysis_result.get('verdict', 'ERROR')
        
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Рекламный Инспектор | Отчет</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        .verdict {{ padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .fail {{ background: #fee; border: 2px solid #e74c3c; }}
        .success {{ background: #efe; border: 2px solid #27ae60; }}
    </style>
</head>
<body>
    <h1>🔍 РЕКЛАМНЫЙ ИНСПЕКТОР</h1>
    <p><strong>Дата:</strong> {datetime.now().strftime('%d.%m.%Y')}</p>
    <p><strong>Материал:</strong> {material_info.get('url', 'Текст')}</p>
    <div class="verdict {'fail' if 'НЕ' in verdict or 'КРИТИЧЕСКИЕ' in verdict else 'success'}">
        <h2>Вердикт: {verdict.replace('_', ' ')}</h2>
    </div>
    <!-- Здесь будет полный HTML-отчет -->
</body>
</html>"""
        
        return html
    
    def save_report(self, analysis_result: Dict, material_info: Dict, format: str = 'markdown') -> str:
        """
        Сохраняет отчет в файл
        
        Args:
            analysis_result: Результаты анализа
            material_info: Информация о материале
            format: Формат отчета (markdown или html)
            
        Returns:
            Путь к сохраненному файлу
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        material_name = material_info.get('url', 'text').replace('https://', '').replace('http://', '').replace('/', '_')[:50]
        
        if format == 'html':
            content = self.generate_html(analysis_result, material_info)
            filename = f"{date_str}_{material_name}.html"
        else:
            content = self.generate_markdown(analysis_result, material_info)
            filename = f"{date_str}_{material_name}.md"
        
        filepath = os.path.join(self.reports_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def _format_disclaimer_section(self, disclaimer: Dict) -> str:
        """Форматирует раздел о дисклеймере"""
        section = "## 1️⃣ ОБЯЗАТЕЛЬНЫЙ ДИСКЛЕЙМЕР\n\n"
        
        if disclaimer.get('found'):
            section += "**Статус:** ✅ Найден"
            if not disclaimer.get('exact_match'):
                section += " ⚠️ (текст может быть изменен)"
            section += "\n\n"
            section += f"**Текст дисклеймера:**\n```\n{REQUIRED_DISCLAIMER}\n```\n\n"
        else:
            section += "**Статус:** ❌ Не найден\n\n"
        
        return section
    
    def _format_violations_section(self, violations: Dict) -> str:
        """Форматирует раздел о нарушениях"""
        section = "## 2️⃣ ЗАПРЕТЫ (ФЗ \"О рекламе\", ст. 28.1)\n\n"
        
        violation_names = {
            'guarantees': 'Гарантии и обещания освобождения',
            'calls_not_pay': 'Призывы не исполнять обязательства',
            'state_system': 'Упоминания о государственной системе',
            'mention_exemption': 'Упоминания о возможности освобождения',
            'property_preservation': 'Обещания сохранения имущества',
            'money_back': 'Гарантии возврата средств',
            'take_loans': 'Призывы брать кредиты',
            'any_cases': 'Обещания взяться за любые дела',
        }
        
        for key, name in violation_names.items():
            found_violations = violations.get(key, [])
            if found_violations:
                section += f"### {name}\n**Статус:** ❌ Нарушение обнаружено\n\n"
                section += "**Найденные формулировки:**\n"
                for violation in found_violations[:5]:  # Показываем первые 5
                    section += f"- \"{violation.get('phrase', '')}\"\n"
                section += "\n"
            else:
                section += f"### {name}\n**Статус:** ✅ Нет нарушений\n\n"
        
        return section
    
    def _format_recommendations(self, disclaimer: Dict, violations: Dict) -> str:
        """Форматирует раздел с рекомендациями"""
        section = "## 💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ\n\n"
        
        # Рекомендации по дисклеймеру
        if not disclaimer.get('found'):
            section += "### ❌ Проблема: Отсутствует обязательный дисклеймер\n\n"
            section += "**Как исправить:**\n"
            section += f"1. Добавить дисклеймер в видимую часть материала\n"
            section += f"2. Точный текст: \"{REQUIRED_DISCLAIMER}\"\n"
            section += f"3. Размер должен быть не менее 7% площади\n\n"
        
        # Рекомендации по нарушениям
        allowed_phrases = [
            "Помогаем в процедуре банкротства",
            "Сопровождаем процесс банкротства",
            "Консультируем по вопросам банкротства",
            "Работаем в рамках законодательства",
        ]
        
        for key, violation_list in violations.items():
            if violation_list:
                section += f"### ❌ Проблема: Найдены запрещенные формулировки\n\n"
                section += "**Как исправить:**\n"
                section += "1. Удалить найденные запрещенные фразы\n"
                section += "2. Заменить на разрешенные формулировки:\n"
                for phrase in allowed_phrases:
                    section += f"   ✅ \"{phrase}\"\n"
                section += "\n"
                break
        
        return section
    
    def _format_legal_basis(self) -> str:
        """Форматирует раздел с нормативной базой"""
        return """## 📚 НОРМАТИВНАЯ БАЗА

- ФЗ "О рекламе" № 38-ФЗ от 13.03.2006
- Федеральный закон № 332-ФЗ от 31.07.2025 (изменения с 1 января 2026)
- Статья 28.1 ФЗ "О рекламе" (запреты на рекламу банкротства)
- Дополнительные требования АРИБ

---

"""
