"""
统计窗口 - 显示学习进度和统计数据
"""

import sys
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QWidget, QTextEdit, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.database import db
from src.models.book import Book
from src.models.word import Word
from src.models.review_record import ReviewRecord


class StatsWindow(QDialog):
    """统计窗口"""
    
    def __init__(self, scheduler=None, parent=None):
        super().__init__(parent)
        self.scheduler = scheduler
        self.book_id = scheduler.book_id if scheduler else None
        
        self.init_ui()
        self._apply_styles()
        self._load_stats()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("📊 学习统计")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # 标题
        title_label = QLabel("📊 学习统计")
        title_label.setFont(QFont("", 16, QFont.Bold))
        layout.addWidget(title_label)
        
        # 词书名称
        if self.book_id:
            book = Book.get_by_id(self.book_id)
            book_name = book.book_name if book else self.book_id
            self.book_label = QLabel(f"词书: {book_name}")
            self.book_label.setStyleSheet("color: #666;")
            layout.addWidget(self.book_label)
        
        # Tab
        tabs = QTabWidget()
        
        # ---- Tab1: 概览 ----
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        
        # 统计卡片（4个）
        card_layout = QGridLayout()
        card_layout.setSpacing(15)
        
        self.card_total = self._create_stat_card("📚 总单词数", "0")
        card_layout.addWidget(self.card_total, 0, 0)
        
        self.card_learned = self._create_stat_card("✅ 已学单词", "0")
        card_layout.addWidget(self.card_learned, 0, 1)
        
        self.card_progress = self._create_stat_card("📈 学习进度", "0%")
        card_layout.addWidget(self.card_progress, 0, 2)
        
        self.card_days = self._create_stat_card("📅 学习天数", "0")
        card_layout.addWidget(self.card_days, 0, 3)
        
        tab1_layout.addLayout(card_layout)
        
        # 今日统计
        today_group = QFrame()
        today_group.setObjectName("today_group")
        today_layout = QHBoxLayout(today_group)
        
        self.today_review_label = QLabel("今日复习: 0 词")
        self.today_review_label.setFont(QFont("", 11))
        today_layout.addWidget(self.today_review_label)
        
        today_layout.addStretch()
        
        self.today_new_label = QLabel("今日新词: 0 词")
        self.today_new_label.setFont(QFont("", 11))
        today_layout.addWidget(self.today_new_label)
        
        tab1_layout.addWidget(today_group)
        
        # 复习表现
        performance_group = QFrame()
        performance_group.setObjectName("performance_group")
        perf_layout = QGridLayout(performance_group)
        
        perf_layout.addWidget(QLabel("📊 复习表现"), 0, 0, 1, 2)
        perf_layout.itemAt(0).widget().setFont(QFont("", 11, QFont.Bold))
        
        self.perf_total_label = QLabel("总复习次数: 0")
        perf_layout.addWidget(self.perf_total_label, 1, 0)
        
        self.perf_correct_label = QLabel("正确次数: 0")
        perf_layout.addWidget(self.perf_correct_label, 1, 1)
        
        self.perf_rate_label = QLabel("正确率: 0%")
        perf_layout.addWidget(self.perf_rate_label, 2, 0)
        
        self.perf_wrong_label = QLabel("错误次数: 0")
        perf_layout.addWidget(self.perf_wrong_label, 2, 1)
        
        tab1_layout.addWidget(performance_group)
        tab1_layout.addStretch()
        
        # ---- Tab2: 错误排行榜 ----
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(4)
        self.error_table.setHorizontalHeaderLabels(["排名", "单词", "错误次数", "正确率"])
        self.error_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.error_table.setAlternatingRowColors(True)
        tab2_layout.addWidget(self.error_table)
        
        # 导出按钮
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        self.btn_export = QPushButton("📥 导出报告")
        self.btn_export.clicked.connect(self._on_export)
        export_layout.addWidget(self.btn_export)
        tab2_layout.addLayout(export_layout)
        
        tabs.addTab(tab1, "概览")
        tabs.addTab(tab2, "错误排行榜")
        
        layout.addWidget(tabs)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self._load_stats)
        btn_layout.addWidget(self.btn_refresh)
        
        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
    
    def _create_stat_card(self, title, value):
        """创建统计卡片"""
        card = QFrame()
        card.setObjectName("stat_card")
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 10pt;")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("stat_value")
        value_label.setFont(QFont("", 20, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(value_label)
        
        return card
    
    def _load_stats(self):
        """加载统计数据"""
        if not self.book_id:
            return
        
        # 获取词书信息
        book = Book.get_by_id(self.book_id)
        if not book:
            return
        
        # 总单词数
        total_words = book.word_count
        
        # 已学单词
        sql = '''
            SELECT COUNT(*) as count 
            FROM words w
            JOIN review_records r ON w.id = r.word_id
            WHERE w.book_id = ? AND r.is_new = 0
        '''
        rows = db.execute_query(sql, (self.book_id,))
        learned = rows[0]['count'] if rows else 0
        
        # 学习进度
        progress = (learned / total_words * 100) if total_words > 0 else 0
        
        # 学习天数（从最早导入日期算起）
        sql = 'SELECT MIN(created_date) as first_date FROM words WHERE book_id = ?'
        rows = db.execute_query(sql, (self.book_id,))
        if rows and rows[0]['first_date']:
            first_date = datetime.fromisoformat(rows[0]['first_date'])
            days = (datetime.now() - first_date).days + 1
        else:
            days = 0
        
        # 更新统计卡片
        self.card_total.findChild(QLabel, "stat_value").setText(str(total_words))
        self.card_learned.findChild(QLabel, "stat_value").setText(str(learned))
        self.card_progress.findChild(QLabel, "stat_value").setText(f"{progress:.1f}%")
        self.card_days.findChild(QLabel, "stat_value").setText(str(days))
        
        # 今日统计
        today = datetime.now().isoformat()
        review_words = Word.get_review_words(self.book_id, today)
        new_words = Word.get_new_words(self.book_id, 9999)
        self.today_review_label.setText(f"今日复习: {len(review_words)} 词")
        self.today_new_label.setText(f"今日新词: {len(new_words)} 词")
        
        # 复习表现
        sql = '''
            SELECT 
                SUM(review_count) as total_reviews,
                SUM(correct_count) as total_correct,
                SUM(wrong_count) as total_wrong
            FROM review_records r
            JOIN words w ON w.id = r.word_id
            WHERE w.book_id = ?
        '''
        rows = db.execute_query(sql, (self.book_id,))
        if rows and rows[0]['total_reviews']:
            total = rows[0]['total_reviews']
            correct = rows[0]['total_correct'] or 0
            wrong = rows[0]['total_wrong'] or 0
            rate = (correct / (correct + wrong) * 100) if (correct + wrong) > 0 else 0
            
            self.perf_total_label.setText(f"总复习次数: {total}")
            self.perf_correct_label.setText(f"正确次数: {correct}")
            self.perf_rate_label.setText(f"正确率: {rate:.1f}%")
            self.perf_wrong_label.setText(f"错误次数: {wrong}")
        else:
            self.perf_total_label.setText("总复习次数: 0")
            self.perf_correct_label.setText("正确次数: 0")
            self.perf_rate_label.setText("正确率: 0%")
            self.perf_wrong_label.setText("错误次数: 0")
        
        # 错误排行榜
        self._load_error_ranking()
    
    def _load_error_ranking(self):
        """加载错误排行榜"""
        sql = '''
            SELECT 
                w.word,
                w.translation,
                r.wrong_count,
                r.correct_count,
                (r.wrong_count + r.correct_count) as total
            FROM words w
            JOIN review_records r ON w.id = r.word_id
            WHERE w.book_id = ? AND r.wrong_count > 0
            ORDER BY r.wrong_count DESC
            LIMIT 20
        '''
        rows = db.execute_query(sql, (self.book_id,))
        
        self.error_table.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            # 排名
            rank_item = QTableWidgetItem(str(i + 1))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.error_table.setItem(i, 0, rank_item)
            
            # 单词
            word_item = QTableWidgetItem(row['word'])
            word_item.setFont(QFont("", 10, QFont.Bold))
            self.error_table.setItem(i, 1, word_item)
            
            # 错误次数
            wrong_item = QTableWidgetItem(str(row['wrong_count']))
            wrong_item.setTextAlignment(Qt.AlignCenter)
            if row['wrong_count'] >= 5:
                wrong_item.setForeground(QColor(220, 38, 38))  # 红色
            elif row['wrong_count'] >= 3:
                wrong_item.setForeground(QColor(234, 179, 8))  # 黄色
            self.error_table.setItem(i, 2, wrong_item)
            
            # 正确率
            total = row['correct_count'] + row['wrong_count']
            rate = (row['correct_count'] / total * 100) if total > 0 else 0
            rate_item = QTableWidgetItem(f"{rate:.1f}%")
            rate_item.setTextAlignment(Qt.AlignCenter)
            self.error_table.setItem(i, 3, rate_item)
    
    def _on_export(self):
        """导出报告"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出统计报告",
            f"统计报告_{datetime.now().strftime('%Y%m%d')}.txt",
            "文本文件 (*.txt);;CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.csv'):
                self._export_csv(file_path)
            else:
                self._export_txt(file_path)
            
            QMessageBox.information(self, "导出成功", f"报告已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出失败:\n{str(e)}")
    
    def _export_txt(self, file_path):
        """导出为文本文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write("WordMemory 学习统计报告\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            # 概览
            f.write("【学习概览】\n")
            f.write(f"总单词数: {self.card_total.findChild(QLabel).text()}\n")
            f.write(f"已学单词: {self.card_learned.findChild(QLabel).text()}\n")
            f.write(f"学习进度: {self.card_progress.findChild(QLabel).text()}\n")
            f.write(f"学习天数: {self.card_days.findChild(QLabel).text()} 天\n\n")
            
            # 今日统计
            f.write("【今日统计】\n")
            f.write(self.today_review_label.text() + "\n")
            f.write(self.today_new_label.text() + "\n\n")
            
            # 复习表现
            f.write("【复习表现】\n")
            f.write(self.perf_total_label.text() + "\n")
            f.write(self.perf_correct_label.text() + "\n")
            f.write(self.perf_wrong_label.text() + "\n")
            f.write(self.perf_rate_label.text() + "\n\n")
            
            # 错误排行榜
            f.write("【错误排行榜】\n")
            for i in range(self.error_table.rowCount()):
                word = self.error_table.item(i, 1).text()
                wrong = self.error_table.item(i, 2).text()
                rate = self.error_table.item(i, 3).text()
                f.write(f"{i+1}. {word} - 错误{wrong}次, 正确率{rate}\n")
    
    def _export_csv(self, file_path):
        """导出为CSV文件"""
        import csv
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['单词', '错误次数', '正确次数', '正确率'])
            
            for i in range(self.error_table.rowCount()):
                word = self.error_table.item(i, 1).text()
                wrong = self.error_table.item(i, 2).text()
                rate = self.error_table.item(i, 3).text()
                # 正确次数需要从数据库查询，简化处理
                writer.writerow([word, wrong, '-', rate])
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QFrame#stat_card {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e2e8f0;
                padding: 15px;
            }
            QFrame#today_group {
                background-color: #eff6ff;
                border-radius: 8px;
                padding: 12px 20px;
                border: 1px solid #bfdbfe;
            }
            QFrame#performance_group {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 15px;
            }
            QTableWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
            }
            QTableWidget::item {
                padding: 5px;
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