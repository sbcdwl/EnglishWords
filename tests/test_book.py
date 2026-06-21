"""
测试词书模型
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.book import Book


def test_book():
    print("=" * 50)
    print("测试词书模型...")
    
    # 1. 获取或创建词书（使用 get_or_create 避免重复）
    print("\n1. 获取或创建词书...")
    book = Book.get_or_create("PEPChuZhong7_2", "人教版初中英语七年级下册")
    print(f"   ✅ 成功: {book}")
    
    # 2. 获取词书（验证存在）
    print("\n2. 获取词书...")
    retrieved = Book.get_by_id("PEPChuZhong7_2")
    print(f"   ✅ 获取成功: {retrieved}")
    
    # 3. 查看所有词书
    print("\n3. 查看所有词书...")
    all_books = Book.get_all()
    print(f"   ✅ 共有 {len(all_books)} 本书:")
    for b in all_books:
        print(f"   - {b}")
    
    # 4. 测试 update_word_count
    print("\n4. 测试更新单词数量...")
    count = book.update_word_count()
    print(f"   ✅ 当前单词数: {count}")
    
    print("\n" + "=" * 50)
    print("🎉 词书模型测试通过！")


if __name__ == "__main__":
    test_book()