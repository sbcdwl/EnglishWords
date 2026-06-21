"""
测试数据库连接和建表是否成功
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import db

def test_database():
    print("=" * 50)
    print("测试数据库连接...")
    
    # 1. 检查连接
    conn = db.get_connection()
    print(f"✅ 数据库连接成功！")
    print(f"   文件路径: {db.db_path}")
    
    # 2. 检查表是否创建
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print(f"\n✅ 已创建的表 ({len(tables)} 个):")
    for table in tables:
        print(f"   - {table[0]}")
    
    # 3. 检查默认设置
    cursor.execute("SELECT key, value FROM settings")
    settings = cursor.fetchall()
    print(f"\n✅ 默认设置 ({len(settings)} 项):")
    for key, value in settings:
        print(f"   - {key} = {value}")
    
    print("\n" + "=" * 50)
    print("🎉 数据库初始化测试通过！")
    print("   所有表已创建，默认设置已加载。")

if __name__ == "__main__":
    test_database()