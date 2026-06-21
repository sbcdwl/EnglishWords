"""
JSON 导入器 - 解析 JSON 文件并将单词导入数据库
"""

import json
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime

from ..models.database import db
from ..models.book import Book
from ..models.word import Word
from ..models.review_record import ReviewRecord


class Importer:
    """JSON 导入器类"""
    
    def __init__(self):
        self.book = None
        self.stats = {
            'total': 0,
            'success': 0,
            'skipped': 0,
            'errors': 0,
            'error_messages': []
        }
    
    def import_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        从 JSON 文件导入单词
        返回导入统计信息
        """
        self.stats = {
            'total': 0,
            'success': 0,
            'skipped': 0,
            'errors': 0,
            'error_messages': []
        }
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.stats['errors'] += 1
            self.stats['error_messages'].append(f"文件不存在: {file_path}")
            return self.stats
        
        # 读取 JSON 文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stats['errors'] += 1
            self.stats['error_messages'].append(f"JSON 解析失败: {str(e)}")
            return self.stats
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['error_messages'].append(f"读取文件失败: {str(e)}")
            return self.stats
        
        # 判断是单个单词还是多个单词
        if isinstance(data, list):
            # 多个单词（数组）
            return self._import_multiple(data)
        elif isinstance(data, dict):
            # 单个单词对象
            return self._import_single(data)
        else:
            self.stats['errors'] += 1
            self.stats['error_messages'].append(f"不支持的JSON格式: {type(data)}")
            return self.stats
    
    def _import_single(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """导入单个单词"""
        self.stats['total'] = 1
        
        try:
            # 提取词书ID
            book_id = data.get('bookId', '')
            if not book_id:
                self.stats['errors'] += 1
                self.stats['error_messages'].append("缺少 bookId 字段")
                return self.stats
            
            # 获取或创建词书
            self.book = Book.get_or_create(book_id, book_id)
            
            # 解析单词数据
            word_data = self._parse_word_data(data)
            if not word_data:
                self.stats['errors'] += 1
                return self.stats
            
            # 检查是否已存在
            existing = Word.get_by_word(book_id, word_data['word'])
            if existing:
                self.stats['skipped'] += 1
                self.stats['error_messages'].append(f"单词已存在: {word_data['word']}")
                # 即使跳过，也要确保词书计数正确
                self.book.update_word_count()
                return self.stats
            
            # 创建单词
            word = Word.create(**word_data)
            
            # 创建复习记录
            ReviewRecord.create(word.id)
            
            # 更新词书单词数量
            self.book.update_word_count()
            
            self.stats['success'] += 1
            
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['error_messages'].append(f"导入失败: {str(e)}")
        
        return self.stats
    
    def _import_multiple(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量导入多个单词"""
        self.stats['total'] = len(data_list)
        
        # 记录所有涉及到的词书ID
        book_ids = set()
        
        for data in data_list:
            try:
                # 提取词书ID
                book_id = data.get('bookId', '')
                if not book_id:
                    self.stats['errors'] += 1
                    self.stats['error_messages'].append(f"单词 {data.get('headWord', '未知')} 缺少 bookId")
                    continue
                
                book_ids.add(book_id)
                
                # 获取或创建词书
                self.book = Book.get_or_create(book_id, book_id)
                
                # 解析单词数据
                word_data = self._parse_word_data(data)
                if not word_data:
                    self.stats['errors'] += 1
                    continue
                
                # 检查是否已存在
                existing = Word.get_by_word(book_id, word_data['word'])
                if existing:
                    self.stats['skipped'] += 1
                    continue
                
                # 创建单词
                word = Word.create(**word_data)
                
                # 创建复习记录
                ReviewRecord.create(word.id)
                
                self.stats['success'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                self.stats['error_messages'].append(f"导入失败: {str(e)}")
        
        # 更新所有涉及词书的单词数量（根据数据库实际统计）
        for book_id in book_ids:
            book = Book.get_by_id(book_id)
            if book:
                book.update_word_count()
        
        return self.stats
    
    def _parse_word_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 JSON 数据，提取单词信息
        返回字典，包含所有字段
        """
        try:
            head_word = data.get('headWord', '')
            if not head_word:
                self.stats['errors'] += 1
                self.stats['error_messages'].append("缺少 headWord 字段")
                return None
            
            content = data.get('content', {})
            word_content = content.get('word', {})
            content_data = word_content.get('content', {})
            
            # 1. 提取释义
            trans_list = content_data.get('trans', [])
            translations = []
            for t in trans_list:
                if 'tranCn' in t:
                    translations.append(t['tranCn'])
            translation = '；'.join(translations) if translations else ''
            
            # 2. 提取音标
            us_phone = content_data.get('usphone', '')
            uk_phone = content_data.get('ukphone', '')
            
            # 3. 提取音频参数
            api_params = []
            us_speech = content_data.get('usspeech', '')
            uk_speech = content_data.get('ukspeech', '')
            if us_speech:
                api_params.append(f"us_{us_speech}")
            if uk_speech:
                api_params.append(f"uk_{uk_speech}")
            api_param = ';'.join(api_params) if api_params else ''
            
            # 4. 提取例句
            sentences = content_data.get('sentence', {})
            sentence_list = sentences.get('sentences', [])
            examples = []
            for s in sentence_list:
                examples.append({
                    'en': s.get('sContent', ''),
                    'cn': s.get('sCn', '')
                })
            example_json = json.dumps(examples, ensure_ascii=False) if examples else ''
            
            # 5. 提取短语
            phrases_data = content_data.get('phrase', {})
            phrase_list = phrases_data.get('phrases', [])
            phrases = []
            for p in phrase_list:
                phrases.append({
                    'phrase': p.get('pContent', ''),
                    'cn': p.get('pCn', '')
                })
            phrase_json = json.dumps(phrases, ensure_ascii=False) if phrases else ''
            
            # 6. 提取同义词
            syno_data = content_data.get('syno', {})
            syno_list = syno_data.get('synos', [])
            synonym_json = json.dumps(syno_list, ensure_ascii=False) if syno_list else ''
            
            # 7. 提取同根词
            rel_data = content_data.get('relWord', {})
            rel_list = rel_data.get('rels', [])
            root_json = json.dumps(rel_list, ensure_ascii=False) if rel_list else ''
            
            # 8. 原始JSON
            raw_json = json.dumps(data, ensure_ascii=False)
            
            return {
                'book_id': data.get('bookId', ''),
                'word': head_word,
                'translation': translation,
                'us_phone': us_phone,
                'uk_phone': uk_phone,
                'api_param': api_param,
                'audio_local_path': '',  # 预留
                'example_json': example_json,
                'phrase_json': phrase_json,
                'synonym_json': synonym_json,
                'root_json': root_json,
                'raw_json': raw_json
            }
            
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['error_messages'].append(f"解析数据失败: {str(e)}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取导入统计信息"""
        return self.stats
    
    def get_book(self) -> Book:
        """获取导入的词书"""
        return self.book