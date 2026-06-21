"""
测试 JSON 导入器
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.importer import Importer


def test_importer():
    print("=" * 60)
    print("测试 JSON 导入器...")
    
    # 1. 准备测试数据
    print("\n1. 准备测试 JSON 数据...")
    test_data = {
        "wordRank": 18,
        "headWord": "talk",
        "content": {
            "word": {
                "wordHead": "talk",
                "wordId": "PEPChuZhong7_2_18",
                "content": {
                    "sentence": {
                        "sentences": [
                            {
                                "sContent": "I could hear Sarah and Andy talking in the next room.",
                                "sCn": "我听到萨拉和安迪在隔壁讲话。"
                            },
                            {
                                "sContent": "Sue and Bob still aren't talking.",
                                "sCn": "休和鲍勃仍然互不理睬。"
                            }
                        ]
                    },
                    "usphone": "tɔk",
                    "ukphone": "tɔːk",
                    "syno": {
                        "synos": [
                            {
                                "pos": "vt",
                                "tran": "说；谈话；讨论",
                                "hwds": [{"w": "tell"}, {"w": "speak"}]
                            }
                        ]
                    },
                    "usspeech": "talk&type=2",
                    "ukspeech": "talk&type=1",
                    "phrase": {
                        "phrases": [
                            {"pContent": "talk about", "pCn": "谈论某事"},
                            {"pContent": "talk to", "pCn": "对某人说话"}
                        ]
                    },
                    "relWord": {
                        "rels": [
                            {
                                "pos": "n",
                                "words": [{"hwd": "talker", "tran": "说话者"}]
                            }
                        ]
                    },
                    "trans": [
                        {
                            "tranCn": "说话；谈话",
                            "pos": "v",
                            "descCn": "中释"
                        },
                        {
                            "tranCn": "交谈",
                            "pos": "n",
                            "descCn": "中释"
                        }
                    ]
                }
            }
        },
        "bookId": "PEPChuZhong7_2"
    }
    
    # 保存测试文件
    import json
    test_file = "test_word.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print(f"   ✅ 测试文件已创建: {test_file}")
    
    # 2. 导入单词
    print("\n2. 导入单词...")
    importer = Importer()
    stats = importer.import_from_file(test_file)
    
    print(f"   ✅ 导入统计:")
    print(f"      总计: {stats['total']}")
    print(f"      成功: {stats['success']}")
    print(f"      跳过: {stats['skipped']}")
    print(f"      错误: {stats['errors']}")
    if stats['error_messages']:
        print(f"      错误信息:")
        for msg in stats['error_messages']:
            print(f"        - {msg}")
    
    # 3. 验证导入结果
    print("\n3. 验证导入结果...")
    from src.models.book import Book
    from src.models.word import Word
    
    book = Book.get_by_id("PEPChuZhong7_2")
    print(f"   词书: {book}")
    print(f"   单词总数: {book.word_count}")
    
    word = Word.get_by_word("PEPChuZhong7_2", "talk")
    if word:
        print(f"   单词: {word.word}")
        print(f"   翻译: {word.translation}")
        print(f"   美式音标: {word.us_phone}")
        print(f"   英式音标: {word.uk_phone}")
        print(f"   例句数量: {len(word.get_examples())}")
        print(f"   短语数量: {len(word.get_phrases())}")
        
        # 显示例句
        examples = word.get_examples()
        print(f"   例句:")
        for i, ex in enumerate(examples, 1):
            print(f"     {i}. {ex['en']}")
            print(f"        {ex['cn']}")
    else:
        print("   ❌ 单词未找到！")
    
    # 4. 再次导入（测试去重）
    print("\n4. 再次导入相同文件（测试去重）...")
    stats2 = importer.import_from_file(test_file)
    print(f"   ✅ 再次导入统计:")
    print(f"      成功: {stats2['success']}")
    print(f"      跳过: {stats2['skipped']} (应该为1)")
    
    # 5. 清理测试文件
    print("\n5. 清理测试文件...")
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"   ✅ 已删除: {test_file}")
    
    print("\n" + "=" * 60)
    print("🎉 JSON 导入器测试通过！")


if __name__ == "__main__":
    test_importer()