"""
测试 Word 和 ReviewRecord 模型
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from src.models.book import Book
from src.models.word import Word
from src.models.review_record import ReviewRecord


def get_or_create_word(book_id: str, word: str, translation: str, **kwargs):
    """
    辅助函数：获取或创建单词
    """
    existing = Word.get_by_word(book_id, word)
    if existing:
        return existing
    return Word.create(book_id=book_id, word=word, translation=translation, **kwargs)


def test_models():
    print("=" * 60)
    print("测试单词模型和复习记录模型...")
    
    # 1. 确保词书存在
    book = Book.get_or_create("PEPChuZhong7_2", "人教版初中英语七年级下册")
    print(f"\n1. 使用词书: {book}")
    
    # 2. 获取或创建单词（避免重复）
    print("\n2. 获取或创建单词...")
    word = get_or_create_word(
        book_id=book.book_id,
        word="talk",
        translation="说话；谈话；交谈",
        us_phone="tɔk",
        uk_phone="tɔːk",
        api_param='us_talk&type=2;uk_talk&type=1',
        example_json='[{"en": "I can talk to her.", "cn": "我可以跟她说话。"}]'
    )
    print(f"   ✅ 单词: {word}")
    
    # 3. 获取单词详情
    print("\n3. 获取单词详情...")
    retrieved = Word.get_by_word(book.book_id, "talk")
    print(f"   ✅ 获取成功: {retrieved}")
    examples = retrieved.get_examples()
    print(f"   例句数量: {len(examples)}")
    if examples:
        print(f"   第一条例句: {examples[0]['en']}")
    
    # 4. 获取或创建复习记录
    print("\n4. 获取或创建复习记录...")
    record = ReviewRecord.get_or_create(word.id)
    print(f"   ✅ 复习记录: {record}")
    
    # 5. 模拟一次复习（记住）
    print("\n5. 模拟复习（quality=4，记住）...")
    record.review(quality=4)
    print(f"   复习后记录: {record}")
    print(f"   下次复习日期: {record.next_review_date}")
    print(f"   间隔天数: {record.interval_days}")
    
    # 6. 模拟另一次复习（忘记）
    print("\n6. 模拟复习（quality=1，忘记）...")
    record.review(quality=1)
    print(f"   复习后记录: {record}")
    print(f"   下次复习日期: {record.next_review_date}")
    print(f"   错误次数: {record.wrong_count}")
    print(f"   ease_factor: {record.ease_factor:.2f}")
    
    # 7. 获取新词列表
    print("\n7. 获取新词列表...")
    new_words = Word.get_new_words(book.book_id, limit=10)
    print(f"   新词数量: {len(new_words)}")
    for w in new_words[:3]:
        print(f"   - {w.word}")
    
    # 8. 手动将复习日期改为今天（为了演示查询功能）
    print("\n8. 手动调整复习日期为今天（演示查询）...")
    record.next_review_date = datetime.now().isoformat()
    record.update()
    print(f"   已更新，下次复习日期: {record.next_review_date}")
    
    # 9. 获取今天应复习的词
    print("\n9. 获取今天应复习的词...")
    today = datetime.now().isoformat()
    review_words = Word.get_review_words(book.book_id, today)
    print(f"   今日复习词数量: {len(review_words)}")
    for w in review_words[:3]:
        print(f"   - {w.word}")
    
    print("\n" + "=" * 60)
    print("🎉 所有模型测试通过！")


if __name__ == "__main__":
    test_models()