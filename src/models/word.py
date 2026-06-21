"""
单词模型 - 管理 words 表的数据操作
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from .database import db


class Word:
    """单词模型类"""
    
    def __init__(self, book_id: str, word: str, translation: str,
                 us_phone: str = "", uk_phone: str = "",
                 api_param: str = "", audio_local_path: str = "",
                 example_json: str = "", phrase_json: str = "",
                 synonym_json: str = "", root_json: str = "",
                 raw_json: str = "", created_date: str = None,
                 id: int = None):
        self.id = id
        self.book_id = book_id
        self.word = word
        self.translation = translation
        self.us_phone = us_phone
        self.uk_phone = uk_phone
        self.api_param = api_param
        self.audio_local_path = audio_local_path
        self.example_json = example_json
        self.phrase_json = phrase_json
        self.synonym_json = synonym_json
        self.root_json = root_json
        self.raw_json = raw_json
        self.created_date = created_date or datetime.now().isoformat()
    
    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> 'Word':
        """从数据库行创建 Word 对象"""
        return cls(
            id=row['id'],
            book_id=row['book_id'],
            word=row['word'],
            translation=row['translation'],
            us_phone=row['us_phone'] or "",
            uk_phone=row['uk_phone'] or "",
            api_param=row['api_param'] or "",
            audio_local_path=row['audio_local_path'] or "",
            example_json=row['example_json'] or "",
            phrase_json=row['phrase_json'] or "",
            synonym_json=row['synonym_json'] or "",
            root_json=row['root_json'] or "",
            raw_json=row['raw_json'] or "",
            created_date=row['created_date']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于数据库操作）"""
        return {
            'book_id': self.book_id,
            'word': self.word,
            'translation': self.translation,
            'us_phone': self.us_phone,
            'uk_phone': self.uk_phone,
            'api_param': self.api_param,
            'audio_local_path': self.audio_local_path,
            'example_json': self.example_json,
            'phrase_json': self.phrase_json,
            'synonym_json': self.synonym_json,
            'root_json': self.root_json,
            'raw_json': self.raw_json,
            'created_date': self.created_date
        }
    
    # ========== 辅助方法（解析JSON） ==========
    
    def get_examples(self) -> List[Dict[str, str]]:
        """获取例句列表"""
        if self.example_json:
            try:
                return json.loads(self.example_json)
            except:
                return []
        return []
    
    def get_phrases(self) -> List[Dict[str, str]]:
        """获取短语列表"""
        if self.phrase_json:
            try:
                return json.loads(self.phrase_json)
            except:
                return []
        return []
    
    def get_synonyms(self) -> List[Dict[str, Any]]:
        """获取同义词列表"""
        if self.synonym_json:
            try:
                return json.loads(self.synonym_json)
            except:
                return []
        return []
    
    def get_roots(self) -> List[Dict[str, Any]]:
        """获取同根词列表"""
        if self.root_json:
            try:
                return json.loads(self.root_json)
            except:
                return []
        return []
    
    # ========== 数据库操作（类方法） ==========
    
    @classmethod
    def create(cls, book_id: str, word: str, translation: str,
               us_phone: str = "", uk_phone: str = "",
               api_param: str = "", audio_local_path: str = "",
               example_json: str = "", phrase_json: str = "",
               synonym_json: str = "", root_json: str = "",
               raw_json: str = "") -> 'Word':
        """
        创建新单词
        """
        word_obj = cls(
            book_id=book_id,
            word=word,
            translation=translation,
            us_phone=us_phone,
            uk_phone=uk_phone,
            api_param=api_param,
            audio_local_path=audio_local_path,
            example_json=example_json,
            phrase_json=phrase_json,
            synonym_json=synonym_json,
            root_json=root_json,
            raw_json=raw_json
        )
        
        sql = '''
            INSERT INTO words (
                book_id, word, translation, us_phone, uk_phone,
                api_param, audio_local_path, example_json, phrase_json,
                synonym_json, root_json, raw_json, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        word_obj.id = db.execute_insert(sql, (
            word_obj.book_id, word_obj.word, word_obj.translation,
            word_obj.us_phone, word_obj.uk_phone,
            word_obj.api_param, word_obj.audio_local_path,
            word_obj.example_json, word_obj.phrase_json,
            word_obj.synonym_json, word_obj.root_json,
            word_obj.raw_json, word_obj.created_date
        ))
        return word_obj
    
    @classmethod
    def get_by_id(cls, word_id: int) -> Optional['Word']:
        """根据ID获取单词"""
        sql = 'SELECT * FROM words WHERE id = ?'
        rows = db.execute_query(sql, (word_id,))
        if rows:
            return cls.from_row(rows[0])
        return None
    
    @classmethod
    def get_by_word(cls, book_id: str, word: str) -> Optional['Word']:
        """根据词书ID和单词获取"""
        sql = 'SELECT * FROM words WHERE book_id = ? AND word = ?'
        rows = db.execute_query(sql, (book_id, word))
        if rows:
            return cls.from_row(rows[0])
        return None
    
    @classmethod
    def get_by_book(cls, book_id: str, limit: int = None, offset: int = 0) -> List['Word']:
        """获取词书中的所有单词"""
        sql = 'SELECT * FROM words WHERE book_id = ? ORDER BY created_date'
        params = [book_id]
        if limit:
            sql += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
        rows = db.execute_query(sql, tuple(params))
        return [cls.from_row(row) for row in rows]
    
    @classmethod
    def get_new_words(cls, book_id: str, limit: int) -> List['Word']:
        """
        获取词书中未学的新词（按导入顺序）
        """
        sql = '''
            SELECT w.* FROM words w
            JOIN review_records r ON w.id = r.word_id
            WHERE w.book_id = ? AND r.is_new = 1
            ORDER BY w.created_date
            LIMIT ?
        '''
        rows = db.execute_query(sql, (book_id, limit))
        return [cls.from_row(row) for row in rows]
    
    @classmethod
    def get_review_words(cls, book_id: str, today: str) -> List['Word']:
        """
        获取今天需要复习的单词（按错误率排序）
        """
        sql = '''
            SELECT w.* FROM words w
            JOIN review_records r ON w.id = r.word_id
            WHERE w.book_id = ? 
              AND r.is_new = 0 
              AND r.next_review_date <= ?
            ORDER BY (r.wrong_count * 1.0 / (r.correct_count + r.wrong_count + 1)) DESC,
                     r.ease_factor ASC
        '''
        rows = db.execute_query(sql, (book_id, today))
        return [cls.from_row(row) for row in rows]
    
    def update(self) -> bool:
        """更新单词信息"""
        sql = '''
            UPDATE words 
            SET translation = ?, us_phone = ?, uk_phone = ?,
                api_param = ?, audio_local_path = ?,
                example_json = ?, phrase_json = ?,
                synonym_json = ?, root_json = ?, raw_json = ?
            WHERE id = ?
        '''
        affected = db.execute_update(sql, (
            self.translation, self.us_phone, self.uk_phone,
            self.api_param, self.audio_local_path,
            self.example_json, self.phrase_json,
            self.synonym_json, self.root_json, self.raw_json,
            self.id
        ))
        return affected > 0
    
    def delete(self) -> bool:
        """删除单词（级联删除会同时删除复习记录）"""
        sql = 'DELETE FROM words WHERE id = ?'
        affected = db.execute_update(sql, (self.id,))
        return affected > 0
    
    def __repr__(self):
        return f"<Word(id={self.id}, word={self.word}, book={self.book_id})>"