"""
设置对话框 - 修改软件设置
"""

import sys
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QCheckBox,
    QGroupBox, QGridLayout, QMessageBox, QSpinBox,
    QDoubleSpinBox, QTabWidget, QWidget, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.database import db
from src.models.book import Book


class SettingsDialog(QDialog):
    """设置对话框"""
    
    # 设置已更改信号
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 加载当前设置
        self.settings = self._load_settings()
        self.books = Book.get_all(active_only=True)
        
        self.init_ui()
        self._apply_styles()
        self._load_values()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("⚙️ 设置")
        self.setMinimumSize(650, 550)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # ===== 标题 =====
        title_label = QLabel("⚙️ 设置")
        title_label.setFont(QFont("", 16, QFont.Bold))
        layout.addWidget(title_label)
        
        # ===== Tab 控件 =====
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        
        # ---- Tab1: 学习设置 ----
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setSpacing(15)
        
        # 每日新词数
        group1 = QGroupBox("📖 学习计划")
        grid1 = QGridLayout(group1)
        grid1.setSpacing(10)
        grid1.setColumnStretch(1, 1)
        
        grid1.addWidget(QLabel("每日新词数量:"), 0, 0)
        self.spin_new_words = QSpinBox()
        self.spin_new_words.setRange(1, 100)
        self.spin_new_words.setSuffix(" 词")
        grid1.addWidget(self.spin_new_words, 0, 1)
        
        hint_label1 = QLabel("提示: 太少进度慢，太多复习压力大")
        hint_label1.setStyleSheet("color: #888; font-size: 9pt;")
        grid1.addWidget(hint_label1, 1, 0, 1, 2)
        
        tab1_layout.addWidget(group1)
        
        # 学习模式
        group2 = QGroupBox("🎯 学习模式")
        grid2 = QGridLayout(group2)
        grid2.setSpacing(10)
        
        grid2.addWidget(QLabel("默认学习模式:"), 0, 0)
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("看词想义", "show_then_check")
        self.combo_mode.addItem("拼写模式", "type_answer")
        grid2.addWidget(self.combo_mode, 0, 1)
        
        hint_label2 = QLabel("提示: 可在学习界面切换")
        hint_label2.setStyleSheet("color: #888; font-size: 9pt;")
        grid2.addWidget(hint_label2, 1, 0, 1, 2)
        
        tab1_layout.addWidget(group2)
        
        # 选择默认词书
        group3 = QGroupBox("📚 默认词书")
        grid3 = QGridLayout(group3)
        grid3.setSpacing(10)
        
        grid3.addWidget(QLabel("启动时自动加载:"), 0, 0)
        self.combo_book = QComboBox()
        self.combo_book.addItem("无 (显示空状态)", "")
        for book in self.books:
            display_name = f"{book.book_name} ({book.book_id})"
            self.combo_book.addItem(display_name, book.book_id)
        grid3.addWidget(self.combo_book, 0, 1)
        
        tab1_layout.addWidget(group3)
        tab1_layout.addStretch()
        
        # ---- Tab2: 显示设置 ----
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setSpacing(15)
        
        group4 = QGroupBox("🎨 卡片显示")
        grid4 = QGridLayout(group4)
        grid4.setSpacing(10)
        grid4.setColumnStretch(1, 1)
        
        self.check_phonetic = QCheckBox("显示音标")
        self.check_phonetic.setChecked(True)
        grid4.addWidget(self.check_phonetic, 0, 0, 1, 2)
        
        self.check_examples = QCheckBox("显示例句")
        self.check_examples.setChecked(True)
        grid4.addWidget(self.check_examples, 1, 0, 1, 2)
        
        grid4.addWidget(QLabel("默认显示例句数:"), 2, 0)
        self.spin_examples = QSpinBox()
        self.spin_examples.setRange(0, 5)
        self.spin_examples.setSuffix(" 条")
        grid4.addWidget(self.spin_examples, 2, 1)
        
        tab2_layout.addWidget(group4)
        tab2_layout.addStretch()
        
        # ---- Tab3: 算法参数 ----
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.setSpacing(15)
        
        group5 = QGroupBox("🔬 SM-2 算法参数")
        grid5 = QGridLayout(group5)
        grid5.setSpacing(10)
        grid5.setColumnStretch(1, 1)
        
        grid5.addWidget(QLabel("最小难度因子:"), 0, 0)
        self.double_ease_min = QDoubleSpinBox()
        self.double_ease_min.setRange(1.0, 3.0)
        self.double_ease_min.setSingleStep(0.05)
        self.double_ease_min.setDecimals(2)
        grid5.addWidget(self.double_ease_min, 0, 1)
        
        grid5.addWidget(QLabel("最大难度因子:"), 1, 0)
        self.double_ease_max = QDoubleSpinBox()
        self.double_ease_max.setRange(1.0, 3.0)
        self.double_ease_max.setSingleStep(0.05)
        self.double_ease_max.setDecimals(2)
        grid5.addWidget(self.double_ease_max, 1, 1)
        
        grid5.addWidget(QLabel("错误惩罚系数:"), 2, 0)
        self.double_penalty = QDoubleSpinBox()
        self.double_penalty.setRange(0.01, 0.5)
        self.double_penalty.setSingleStep(0.01)
        self.double_penalty.setDecimals(2)
        grid5.addWidget(self.double_penalty, 2, 1)
        
        hint_label3 = QLabel("提示: 惩罚系数越高，答错后单词越频繁出现")
        hint_label3.setStyleSheet("color: #888; font-size: 9pt;")
        grid5.addWidget(hint_label3, 3, 0, 1, 2)
        
        tab3_layout.addWidget(group5)
        
        # 恢复默认按钮
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        self.btn_reset_default = QPushButton("🔄 恢复默认设置")
        self.btn_reset_default.clicked.connect(self._on_reset_default)
        reset_layout.addWidget(self.btn_reset_default)
        tab3_layout.addLayout(reset_layout)
        
        tab3_layout.addStretch()
        
        # ---- 添加到Tab ----
        tabs.addTab(tab1, "学习")
        tabs.addTab(tab2, "显示")
        tabs.addTab(tab3, "高级")
        
        layout.addWidget(tabs)
        
        # ===== 底部按钮 =====
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_save = QPushButton("💾 保存")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setFixedWidth(120)
        self.btn_save.setFixedHeight(40)
        self.btn_save.clicked.connect(self._on_save)
        button_layout.addWidget(self.btn_save)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
    
    def _load_settings(self):
        """从数据库加载设置"""
        return {
            'daily_new_words': int(db.get_setting('daily_new_words', '20')),
            'review_mode': db.get_setting('review_mode', 'show_then_check'),
            'show_phonetic': db.get_setting('show_phonetic', 'true') == 'true',
            'max_examples': int(db.get_setting('max_examples_display', '2')),
            'ease_factor_min': float(db.get_setting('ease_factor_min', '1.3')),
            'ease_factor_max': float(db.get_setting('ease_factor_max', '2.5')),
            'wrong_penalty_factor': float(db.get_setting('wrong_penalty_factor', '0.15')),
            'default_book_id': db.get_setting('default_book_id', '')
        }
    
    def _load_values(self):
        """加载设置值到控件"""
        s = self.settings
        
        self.spin_new_words.setValue(s['daily_new_words'])
        
        # 学习模式
        index = self.combo_mode.findData(s['review_mode'])
        if index >= 0:
            self.combo_mode.setCurrentIndex(index)
        
        # 默认词书
        index = self.combo_book.findData(s['default_book_id'])
        if index >= 0:
            self.combo_book.setCurrentIndex(index)
        
        self.check_phonetic.setChecked(s['show_phonetic'])
        self.spin_examples.setValue(s['max_examples'])
        
        self.double_ease_min.setValue(s['ease_factor_min'])
        self.double_ease_max.setValue(s['ease_factor_max'])
        self.double_penalty.setValue(s['wrong_penalty_factor'])
    
    def _get_values(self):
        """从控件获取当前值"""
        return {
            'daily_new_words': self.spin_new_words.value(),
            'review_mode': self.combo_mode.currentData(),
            'default_book_id': self.combo_book.currentData(),
            'show_phonetic': self.check_phonetic.isChecked(),
            'max_examples': self.spin_examples.value(),
            'ease_factor_min': self.double_ease_min.value(),
            'ease_factor_max': self.double_ease_max.value(),
            'wrong_penalty_factor': self.double_penalty.value()
        }
    
    def _on_save(self):
        """保存设置"""
        values = self._get_values()
        
        # 保存到数据库
        db.update_setting('daily_new_words', values['daily_new_words'])
        db.update_setting('review_mode', values['review_mode'])
        db.update_setting('default_book_id', values['default_book_id'])
        db.update_setting('show_phonetic', 'true' if values['show_phonetic'] else 'false')
        db.update_setting('max_examples_display', values['max_examples'])
        db.update_setting('ease_factor_min', values['ease_factor_min'])
        db.update_setting('ease_factor_max', values['ease_factor_max'])
        db.update_setting('wrong_penalty_factor', values['wrong_penalty_factor'])
        
        self.settings = values
        
        QMessageBox.information(self, "成功", "设置已保存！")
        
        self.settings_changed.emit()
        self.accept()
    
    def _on_reset_default(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self,
            "确认恢复",
            "确定要恢复所有设置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        # 默认值
        defaults = {
            'daily_new_words': 20,
            'review_mode': 'show_then_check',
            'show_phonetic': True,
            'max_examples': 2,
            'ease_factor_min': 1.3,
            'ease_factor_max': 2.5,
            'wrong_penalty_factor': 0.15
        }
        
        # 应用到控件
        self.spin_new_words.setValue(defaults['daily_new_words'])
        self.combo_mode.setCurrentIndex(0)
        self.check_phonetic.setChecked(defaults['show_phonetic'])
        self.spin_examples.setValue(defaults['max_examples'])
        self.double_ease_min.setValue(defaults['ease_factor_min'])
        self.double_ease_max.setValue(defaults['ease_factor_max'])
        self.double_penalty.setValue(defaults['wrong_penalty_factor'])
        
        QMessageBox.information(self, "已恢复", "所有设置已恢复为默认值")
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #d0d7e2;
                background-color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f0f2f5;
                border-color: #b0b8c4;
            }
            QPushButton#btn_save {
                background-color: #2563eb;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton#btn_save:hover {
                background-color: #1d4ed8;
            }
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {
                padding: 6px 10px;
                border: 1px solid #d0d7e2;
                border-radius: 6px;
                background-color: white;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QLineEdit:focus {
                border-color: #2563eb;
            }
            QCheckBox {
                spacing: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-bottom: none;
            }
            QTabBar::tab:!selected {
                background-color: #f1f5f9;
            }
        """)
    
    def get_settings(self):
        """获取当前设置（供外部调用）"""
        return self.settings