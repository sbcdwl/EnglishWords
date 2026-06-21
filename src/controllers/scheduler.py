"""
调度器 - 艾宾浩斯遗忘曲线核心算法
负责每天筛选新词和复习词
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from ..models.database import db
from ..models.book import Book
from ..models.word import Word
from ..models.review_record import ReviewRecord


class Scheduler:
    """学习调度器"""
    
    def __init__(self, book_id: str = None):
        self.book_id = book_id
        self.book = None
        if book_id:
            self.book = Book.get_by_id(book_id)
    
    def set_book(self, book_id: str):
        """切换当前学习的词书"""
        self.book_id = book_id
        self.book = Book.get_by_id(book_id)
    
    def get_daily_words(self, date: str = None) -> Tuple[List[Word], List[Word]]:
        """
        获取今日学习队列
        返回: (复习词列表, 新词列表)
        """
        if not self.book:
            raise ValueError("未设置词书，请先调用 set_book()")
        
        today = date or datetime.now().isoformat()
        
        # 1. 获取今天需要复习的词
        review_words = Word.get_review_words(self.book_id, today)
        
        # 2. 获取每日新词数量
        daily_new = int(db.get_setting('daily_new_words', '20'))
        
        # 3. 获取新词
        new_words = Word.get_new_words(self.book_id, daily_new)
        
        return review_words, new_words
    
    def get_combined_queue(self, date: str = None) -> List[Dict[str, Any]]:
        """
        获取合并后的学习队列（复习词在前，新词在后）
        返回: [{'word': Word对象, 'type': 'review'/'new', 'record': ReviewRecord对象}, ...]
        """
        review_words, new_words = self.get_daily_words(date)
        
        queue = []
        
        # 复习词
        for word in review_words:
            record = ReviewRecord.get_by_word_id(word.id)
            queue.append({
                'word': word,
                'type': 'review',
                'record': record,
                'priority': self._calculate_priority(record)  # 用于排序
            })
        
        # 新词
        for word in new_words:
            record = ReviewRecord.get_by_word_id(word.id)
            queue.append({
                'word': word,
                'type': 'new',
                'record': record,
                'priority': 0
            })
        
        # 复习词按优先级排序（错误率高的优先）
        review_items = [q for q in queue if q['type'] == 'review']
        new_items = [q for q in queue if q['type'] == 'new']
        
        review_items.sort(key=lambda x: x['priority'], reverse=True)
        
        return review_items + new_items
    
    def _calculate_priority(self, record: ReviewRecord) -> float:
        """
        计算复习优先级（错误率越高，优先级越高）
        """
        total = record.correct_count + record.wrong_count
        if total == 0:
            return 0
        return record.wrong_count / total
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取学习统计
        """
        if not self.book:
            return {}
        
        today = datetime.now().isoformat()
        review_words = Word.get_review_words(self.book_id, today)
        new_words_count = self.book.get_new_words_count()
        total_words = self.book.word_count
        
        # 已学单词数
        sql = '''
            SELECT COUNT(*) as count 
            FROM words w
            JOIN review_records r ON w.id = r.word_id
            WHERE w.book_id = ? AND r.is_new = 0
        '''
        rows = db.execute_query(sql, (self.book_id,))
        learned_count = rows[0]['count'] if rows else 0
        
        return {
            'total_words': total_words,
            'learned_words': learned_count,
            'new_words': new_words_count,
            'today_review': len(review_words),
            'progress': (learned_count / total_words * 100) if total_words > 0 else 0
        }
    
    def get_today_stats(self) -> Dict[str, Any]:
        """
        获取今日学习统计（用于界面显示）
        """
        review_words, new_words = self.get_daily_words()
        return {
            'review_count': len(review_words),
            'new_count': len(new_words),
            'total_count': len(review_words) + len(new_words)
        }