"""
测试调度器
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from src.controllers.scheduler import Scheduler
from src.models.book import Book
from src.models.word import Word
from src.models.review_record import ReviewRecord
from src.models.database import db


def test_scheduler():
    print("=" * 60)
    print("测试调度器...")
    
    # 1. 确保有词书和单词
    book = Book.get_or_create("PEPChuZhong7_2", "人教版初中英语七年级下册")
    print(f"\n1. 使用词书: {book}")
    
    # 2. 创建一个新词用于测试（确保有新词可学）
    print("\n2. 创建测试新词...")
    word = Word.get_by_word(book.book_id, "hello")
    if not word:
        word = Word.create(
            book_id=book.book_id,
            word="hello",
            translation="你好；喂",
            us_phone="həˈloʊ",
            uk_phone="həˈləʊ",
            example_json='[{"en": "Hello, world!", "cn": "你好，世界！"}]'
        )
        ReviewRecord.create(word.id)
        book.update_word_count()
        print(f"   ✅ 创建新词: {word}")
    else:
        print(f"   ⚠️ 单词已存在: {word}")
    
    # 3. 初始化调度器
    print("\n3. 初始化调度器...")
    scheduler = Scheduler(book.book_id)
    print(f"   ✅ 调度器已绑定词书: {scheduler.book.book_id}")
    
    # 4. 查看今日统计
    print("\n4. 查看今日统计...")
    stats = scheduler.get_today_stats()
    print(f"   今日复习词: {stats['review_count']}")
    print(f"   今日新词: {stats['new_count']}")
    print(f"   今日总计: {stats['total_count']}")
    
    # 5. 获取学习队列
    print("\n5. 获取学习队列...")
    queue = scheduler.get_combined_queue()
    print(f"   队列长度: {len(queue)}")
    for i, item in enumerate(queue[:5], 1):
        word_obj = item['word']
        item_type = item['type']
        print(f"   {i}. [{item_type}] {word_obj.word} - {word_obj.translation[:20]}...")
    
    # 6. 查看学习进度
    print("\n6. 查看学习进度...")
    progress = scheduler.get_stats()
    print(f"   总单词数: {progress['total_words']}")
    print(f"   已学单词: {progress['learned_words']}")
    print(f"   待学新词: {progress['new_words']}")
    print(f"   今日复习: {progress['today_review']}")
    print(f"   完成度: {progress['progress']:.1f}%")
    
    print("\n" + "=" * 60)
    print("🎉 调度器测试通过！")


if __name__ == "__main__":
    test_scheduler()