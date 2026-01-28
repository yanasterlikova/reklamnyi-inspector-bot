"""
Генератор PDF-отчетов
Конвертирует HTML-отчеты в PDF
"""
import os
from weasyprint import HTML
from typing import Optional


class PDFGenerator:
    """Генератор PDF-отчетов из HTML"""
    
    def __init__(self, reports_path: str = "data/reports"):
        self.reports_path = reports_path
        os.makedirs(reports_path, exist_ok=True)
    
    def html_to_pdf(self, html_content: str, output_filename: str) -> Optional[str]:
        """
        Конвертирует HTML в PDF
        
        Args:
            html_content: HTML-контент
            output_filename: Имя файла для сохранения (без расширения)
            
        Returns:
            Путь к PDF-файлу или None при ошибке
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            pdf_path = os.path.join(self.reports_path, f"{output_filename}.pdf")
            logger.info(f"Генерирую PDF: {pdf_path}")
            
            # Генерируем PDF
            HTML(string=html_content).write_pdf(pdf_path)
            
            if os.path.exists(pdf_path):
                logger.info(f"PDF успешно создан: {pdf_path}, размер: {os.path.getsize(pdf_path)} байт")
                return pdf_path
            else:
                logger.error(f"PDF файл не создан: {pdf_path}")
                return None
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка генерации PDF: {e}", exc_info=True)
            traceback.print_exc()
            print(f"ERROR: Ошибка генерации PDF: {e}")
            return None
    
    def generate_from_html_file(self, html_file_path: str, output_filename: str) -> Optional[str]:
        """
        Конвертирует HTML-файл в PDF
        
        Args:
            html_file_path: Путь к HTML-файлу
            output_filename: Имя выходного файла (без расширения)
            
        Returns:
            Путь к PDF-файлу или None при ошибке
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"Читаю HTML файл: {html_file_path}")
            if not os.path.exists(html_file_path):
                logger.error(f"HTML файл не найден: {html_file_path}")
                return None
            
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            logger.info(f"HTML файл прочитан, размер: {len(html_content)} символов")
            return self.html_to_pdf(html_content, output_filename)
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка чтения HTML-файла: {e}", exc_info=True)
            traceback.print_exc()
            print(f"ERROR: Ошибка чтения HTML-файла: {e}")
            return None
