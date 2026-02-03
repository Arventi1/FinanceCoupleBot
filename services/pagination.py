from typing import List, Tuple, Dict, Any, Optional
from math import ceil
from utils.exceptions import PaginationError

class PaginationService:
    """Сервис для работы с пагинацией"""
    
    def __init__(self, page_size: int = 10, max_pages: int = 100):
        self.page_size = page_size
        self.max_pages = max_pages
    
    def validate_page(self, page: int, total_items: int) -> int:
        """Валидация номера страницы"""
        if page < 1:
            raise PaginationError("Номер страницы должен быть больше 0")
        
        total_pages = self.get_total_pages(total_items)
        
        if page > total_pages > 0:
            raise PaginationError(f"Страница {page} не существует. Всего страниц: {total_pages}")
        
        return page
    
    def get_total_pages(self, total_items: int) -> int:
        """Получить общее количество страниц"""
        if total_items <= 0:
            return 0
        return ceil(total_items / self.page_size)
    
    def get_page_info(self, page: int, total_items: int) -> Dict[str, Any]:
        """Получить информацию о странице"""
        total_pages = self.get_total_pages(total_items)
        
        return {
            'current_page': page,
            'total_pages': total_pages,
            'total_items': total_items,
            'page_size': self.page_size,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'start_item': (page - 1) * self.page_size + 1 if total_items > 0 else 0,
            'end_item': min(page * self.page_size, total_items)
        }
    
    def paginate_data(self, data: List, page: int) -> Tuple[List, Dict[str, Any]]:
        """Пагинация данных"""
        total_items = len(data)
        page_info = self.get_page_info(page, total_items)
        
        start_idx = (page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        
        paginated_data = data[start_idx:end_idx]
        
        return paginated_data, page_info

# Создаем экземпляр сервиса
pagination_service = PaginationService(page_size=config.PAGE_SIZE)