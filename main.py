"""
WordMemory - 背单词软件
入口文件
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from src.views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WordMemory")
    
    # 设置应用图标（如果有）
    # app.setWindowIcon(QIcon("resources/icons/app.ico"))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()