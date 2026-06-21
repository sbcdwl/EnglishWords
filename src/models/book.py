"""
词书模型 - 管理 books 表的数据操作
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from .database import db


class Book:
    """词书模型类"""
    
    def __init__(self, book_id: str, book_name: str = "", word_count: int = 0, 
                 import_date: str = None, is_active: int = 1, id: int = None):
        self.id = id
        self.book_id = book_id
        self.book_name = book_name or book_id  # 如果没填名称，默认用 book_id
        self.word_count = word_count
        self.import_date = import_date or datetime.now().isoformat()
        self.is_active = is_active
    
    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> 'Book':
        """从数据库行创建 Book 对象"""
        return cls(
            id=row['id'],
            book_id=row['book_id'],
            book_name=row['book_name'],
            word_count=row['word_count'],
            import_date=row['import_date'],
            is_active=row['is_active']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于数据库操作）"""
        return {
            'book_id': self.book_id,
            'book_name': self.book_name,
            'word_count': self.word_count,
            'import_date': self.import_date,
            'is_active': self.is_active
        }
    
    # ========== 数据库操作（类方法） ==========
    
    @classmethod
    def create(cls, book_id: str, book_name: str = "") -> 'Book':
        """
        创建新词书
        """
        book = cls(book_id, book_name)
        sql = '''
            INSERT INTO books (book_id, book_name, word_count, import_date, is_active)
            VALUES (?, ?, ?, ?, ?)
        '''
        book.id = db.execute_insert(sql, (
            book.book_id, book.book_name, book.word_count, 
            book.import_date, book.is_active
        ))
        return book
    
    @classmethod
    def get_by_id(cls, book_id: str) -> Optional['Book']:
        """
        根据词书ID获取词书
        """
        sql = 'SELECT * FROM books WHERE book_id = ?'
        rows = db.execute_query(sql, (book_id,))
        if rows:
            return cls.from_row(rows[0])
        return None
    
    @classmethod
    def get_all(cls, active_only: bool = True) -> List['Book']:
        """
        获取所有词书
        active_only: True 只返回启用的词书
        """
        sql = 'SELECT * FROM books'
        if active_only:
            sql += ' WHERE is_active = 1'
        sql += ' ORDER BY import_date DESC'
        rows = db.execute_query(sql)
        return [cls.from_row(row) for row in rows]
    
    @classmethod
    def get_or_create(cls, book_id: str, book_name: str = "") -> 'Book':
        """
        获取或创建词书（如果不存在则创建）
        """
        book = cls.get_by_id(book_id)
        if book:
            return book
        return cls.create(book_id, book_name)
    
    def update(self) -> bool:
        """
        更新词书信息（保存当前对象的状态）
        """
        sql = '''
            UPDATE books 
            SET book_name = ?, word_count = ?, is_active = ?
            WHERE book_id = ?
        '''
        affected = db.execute_update(sql, (
            self.book_name, self.word_count, self.is_active, self.book_id
        ))
        return affected > 0
    
    def delete(self) -> bool:
        """
        删除词书（级联删除会同时删除该词书的所有单词和复习记录）
        """
        sql = 'DELETE FROM books WHERE book_id = ?'
        affected = db.execute_update(sql, (self.book_id,))
        return affected > 0
    
    def update_word_count(self) -> int:
        """
        更新词书中的单词总数（重新统计）
        返回更新后的单词数量
        """
        sql = 'SELECT COUNT(*) as count FROM words WHERE book_id = ?'
        rows = db.execute_query(sql, (self.book_id,))
        if rows:
            self.word_count = rows[0]['count']
            self.update()
            return self.word_count
        return 0
    
    def get_words(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取词书中的所有单词（返回原始数据，用于展示）
        """
        sql = 'SELECT * FROM words WHERE book_id = ? ORDER BY created_date'
        if limit:
            sql += f' LIMIT {limit} OFFSET {offset}'
        return db.execute_query(sql, (self.book_id,))
    
    def get_new_words_count(self) -> int:
        """
        获取词书中未学的新词数量
        """
        sql = '''
            SELECT COUNT(*) as count 
            FROM words w
            JOIN review_records r ON w.id = r.word_id
            WHERE w.book_id = ? AND r.is_new = 1
        '''
        rows = db.execute_query(sql, (self.book_id,))
        return rows[0]['count'] if rows else 0
    
    def __repr__(self):
        return f"<Book(id={self.book_id}, name={self.book_name}, words={self.word_count})>"