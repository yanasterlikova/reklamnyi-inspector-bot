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
            pdf_path = os.path.join(self.reports_path, f"{output_filename}.pdf")
            
            # Генерируем PDF
            HTML(string=html_content).write_pdf(pdf_path)
            
            return pdf_path
        except Exception as e:
            print(f"Ошибка генерации PDF: {e}")
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
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return self.html_to_pdf(html_content, output_filename)
        except Exception as e:
            print(f"Ошибка чтения HTML-файла: {e}")
            return None
