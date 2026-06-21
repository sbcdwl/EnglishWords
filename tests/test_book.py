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
    
    # 1. 创建词书
    print("\n1. 创建词书...")
    book = Book.create("PEPChuZhong7_2", "人教版初中英语七年级下册")
    print(f"   ✅ 创建成功: {book}")
    
    # 2. 获取词书
    print("\n2. 获取词书...")
    retrieved = Book.get_by_id("PEPChuZhong7_2")
    print(f"   ✅ 获取成功: {retrieved}")
    
    # 3. 检查是否存在重复创建（应该返回已存在的）
    print("\n3. 再次创建相同词书...")
    book2 = Book.get_or_create("PEPChuZhong7_2", "人教版初中英语七年级下册")
    print(f"   ✅ get_or_create 返回: {book2}")
    print(f"   ✅ 是否为同一本书: {book.id == book2.id}")
    
    # 4. 查看所有词书
    print("\n4. 查看所有词书...")
    all_books = Book.get_all()
    for b in all_books:
        print(f"   - {b}")
    
    print("\n" + "=" * 50)
    print("🎉 词书模型测试通过！")


if __name__ == "__main__":
    test_book()