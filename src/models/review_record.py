"""
复习记录模型 - 管理 review_records 表的数据操作
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from .database import db


class ReviewRecord:
    """复习记录模型类"""
    
    def __init__(self, word_id: int,
                 last_review_date: str = None,
                 next_review_date: str = None,
                 review_count: int = 0,
                 correct_count: int = 0,
                 wrong_count: int = 0,
                 consecutive_correct: int = 0,
                 ease_factor: float = 2.5,
                 interval_days: int = 1,
                 last_quality: int = None,
                 is_new: int = 1,
                 id: int = None):
        self.id = id
        self.word_id = word_id
        self.last_review_date = last_review_date or datetime.now().isoformat()
        self.next_review_date = next_review_date or (datetime.now() + timedelta(days=1)).isoformat()
        self.review_count = review_count
        self.correct_count = correct_count
        self.wrong_count = wrong_count
        self.consecutive_correct = consecutive_correct
        self.ease_factor = ease_factor
        self.interval_days = interval_days
        self.last_quality = last_quality
        self.is_new = is_new
    
    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> 'ReviewRecord':
        """从数据库行创建 ReviewRecord 对象"""
        return cls(
            id=row['id'],
            word_id=row['word_id'],
            last_review_date=row['last_review_date'],
            next_review_date=row['next_review_date'],
            review_count=row['review_count'],
            correct_count=row['correct_count'],
            wrong_count=row['wrong_count'],
            consecutive_correct=row['consecutive_correct'],
            ease_factor=row['ease_factor'],
            interval_days=row['interval_days'],
            last_quality=row['last_quality'],
            is_new=row['is_new']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于数据库操作）"""
        return {
            'word_id': self.word_id,
            'last_review_date': self.last_review_date,
            'next_review_date': self.next_review_date,
            'review_count': self.review_count,
            'correct_count': self.correct_count,
            'wrong_count': self.wrong_count,
            'consecutive_correct': self.consecutive_correct,
            'ease_factor': self.ease_factor,
            'interval_days': self.interval_days,
            'last_quality': self.last_quality,
            'is_new': self.is_new
        }
    
    # ========== SM-2 算法核心 ==========
    
    def review(self, quality: int) -> None:
        """
        执行一次复习，更新所有算法参数
        quality: 0-5 评分（0=完全忘记，5=完美记住）
        """
        from .database import db  # 延迟导入避免循环依赖
        
        # 获取算法参数（从设置中读取，支持动态调整）
        ease_min = float(db.get_setting('ease_factor_min', '1.3'))
        ease_max = float(db.get_setting('ease_factor_max', '2.5'))
        wrong_penalty = float(db.get_setting('wrong_penalty_factor', '0.15'))
        
        # 更新统计
        self.review_count += 1
        self.last_review_date = datetime.now().isoformat()
        self.last_quality = quality
        
        # 判断对错
        if quality >= 3:  # 记住
            self.correct_count += 1
            self.consecutive_correct += 1
            self.is_new = 0  # 标记为已学
        else:  # 忘记
            self.wrong_count += 1
            self.consecutive_correct = 0
        
        # SM-2 公式计算 ease_factor
        if quality >= 3:
            # 正常调整
            ease_adjust = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
            self.ease_factor += ease_adjust
        else:
            # 错误：额外惩罚（方案C：结合 wrong_count）
            penalty = wrong_penalty * (1 + self.wrong_count / 10)
            self.ease_factor -= penalty
        
        # 限制 ease_factor 范围
        self.ease_factor = max(ease_min, min(ease_max, self.ease_factor))
        
        # 计算新的间隔
        if self.review_count == 1 and quality >= 3:
            # 第一次记住：间隔1天
            self.interval_days = 1
        elif self.review_count == 2 and quality >= 3:
            # 第二次记住：间隔6天
            self.interval_days = 6
        else:
            # 使用 SM-2 公式
            if quality >= 3:
                self.interval_days = int(self.interval_days * self.ease_factor)
            else:
                # 答错重置间隔为1天
                self.interval_days = 1
        
        # 计算下次复习日期
        next_date = datetime.now() + timedelta(days=self.interval_days)
        self.next_review_date = next_date.isoformat()
        
        # 保存到数据库
        self.update()
    
    # ========== 数据库操作（类方法） ==========
    
    @classmethod
    def create(cls, word_id: int) -> 'ReviewRecord':
        """
        为单词创建初始复习记录
        """
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        record = cls(
            word_id=word_id,
            last_review_date=now.isoformat(),
            next_review_date=tomorrow.isoformat(),
            is_new=1
        )
        
        sql = '''
            INSERT INTO review_records (
                word_id, last_review_date, next_review_date,
                review_count, correct_count, wrong_count,
                consecutive_correct, ease_factor, interval_days,
                last_quality, is_new
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        record.id = db.execute_insert(sql, (
            record.word_id,
            record.last_review_date,
            record.next_review_date,
            record.review_count,
            record.correct_count,
            record.wrong_count,
            record.consecutive_correct,
            record.ease_factor,
            record.interval_days,
            record.last_quality,
            record.is_new
        ))
        return record
    
    @classmethod
    def get_by_word_id(cls, word_id: int) -> Optional['ReviewRecord']:
        """根据单词ID获取复习记录"""
        sql = 'SELECT * FROM review_records WHERE word_id = ?'
        rows = db.execute_query(sql, (word_id,))
        if rows:
            return cls.from_row(rows[0])
        return None
    
    @classmethod
    def get_or_create(cls, word_id: int) -> 'ReviewRecord':
        """获取或创建复习记录"""
        record = cls.get_by_word_id(word_id)
        if record:
            return record
        return cls.create(word_id)
    
    def update(self) -> bool:
        """更新复习记录"""
        sql = '''
            UPDATE review_records 
            SET last_review_date = ?, next_review_date = ?,
                review_count = ?, correct_count = ?, wrong_count = ?,
                consecutive_correct = ?, ease_factor = ?, interval_days = ?,
                last_quality = ?, is_new = ?
            WHERE id = ?
        '''
        affected = db.execute_update(sql, (
            self.last_review_date, self.next_review_date,
            self.review_count, self.correct_count, self.wrong_count,
            self.consecutive_correct, self.ease_factor, self.interval_days,
            self.last_quality, self.is_new,
            self.id
        ))
        return affected > 0
    
    def __repr__(self):
        status = "新词" if self.is_new else f"复习(间隔{self.interval_days}天)"
        return f"<ReviewRecord(word_id={self.word_id}, {status}, 正确={self.correct_count}, 错误={self.wrong_count})>"