"""Examination models"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import random
import string


class QuestionBank(models.Model):
    """题库表"""
    
    name = models.CharField(_('题库名称'), max_length=100)
    code = models.CharField(_('题库代码'), max_length=50, unique=True)
    category = models.CharField(_('题库分类'), max_length=50, blank=True)
    description = models.TextField(_('题库描述'), blank=True)
    question_count = models.IntegerField(_('题目数量'), default=0)
    total_score = models.DecimalField(_('总分'), max_digits=5, decimal_places=2, default=100.00)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('创建人'),
        related_name='created_question_banks'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('题库')
        verbose_name_plural = _('题库')
        db_table = 'question_banks'
    
    def __str__(self):
        return self.name
    
    def update_question_count(self):
        """更新题目数量"""
        self.question_count = self.questions.count()
        self.save()


class Question(models.Model):
    """题目表"""
    
    class QuestionType(models.TextChoices):
        SINGLE_CHOICE = 'single_choice', _('单选题')
        MULTIPLE_CHOICE = 'multiple_choice', _('多选题')
        TRUE_FALSE = 'true_false', _('判断题')
        FILL_BLANK = 'fill_blank', _('填空题')
        SHORT_ANSWER = 'short_answer', _('简答题')
    
    class Difficulty(models.TextChoices):
        EASY = 'easy', _('简单')
        MEDIUM = 'medium', _('中等')
        HARD = 'hard', _('困难')
    
    question_bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        verbose_name=_('所属题库'),
        related_name='questions'
    )
    question_type = models.CharField(
        _('题型'),
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.SINGLE_CHOICE
    )
    difficulty = models.CharField(
        _('难度'),
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM
    )
    title = models.TextField(_('题目'))
    content = models.TextField(_('题目内容'), blank=True)
    options = models.JSONField(_('选项'), default=dict, blank=True)
    correct_answer = models.JSONField(_('正确答案'), default=dict)
    explanation = models.TextField(_('答案解析'), blank=True)
    score = models.DecimalField(_('分值'), max_digits=5, decimal_places=2, default=1.00)
    sort_order = models.IntegerField(_('排序'), default=0)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('创建人'),
        related_name='created_questions'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('题目')
        verbose_name_plural = _('题目')
        db_table = 'questions'
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['question_bank']),
            models.Index(fields=['question_type']),
            models.Index(fields=['difficulty']),
        ]
    
    def __str__(self):
        return f"{self.get_question_type_display()} - {self.title[:50]}"
    
    @property
    def option_list(self):
        """获取选项列表"""
        return self.options.get('options', [])
    
    @property
    def correct_answer_list(self):
        """获取正确答案列表"""
        return self.correct_answer.get('answer', [])


class Exam(models.Model):
    """考试表"""
    
    class ExamType(models.TextChoices):
        PRACTICE = 'practice', _('练习')
        FORMAL = 'formal', _('正式考试')
        MAKEUP = 'makeup', _('补考')
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('草稿')
        PUBLISHED = 'published', _('已发布')
        IN_PROGRESS = 'in_progress', _('进行中')
        COMPLETED = 'completed', _('已结束')
    
    code = models.CharField(_('考试编号'), max_length=50, unique=True)
    title = models.CharField(_('考试标题'), max_length=200)
    exam_type = models.CharField(
        _('考试类型'),
        max_length=20,
        choices=ExamType.choices,
        default=ExamType.FORMAL
    )
    course = models.ForeignKey(
        'training.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('关联课程'),
        related_name='exams'
    )
    question_bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        verbose_name=_('题库'),
        related_name='exams'
    )
    total_questions = models.IntegerField(_('题目数量'), default=50)
    total_score = models.DecimalField(_('总分'), max_digits=5, decimal_places=2, default=100.00)
    passing_score = models.DecimalField(_('及格分数'), max_digits=5, decimal_places=2, default=60.00)
    time_limit = models.IntegerField(_('考试时长(分钟)'), default=60)
    start_time = models.DateTimeField(_('开始时间'))
    end_time = models.DateTimeField(_('结束时间'))
    max_attempts = models.IntegerField(_('最大尝试次数'), default=1)
    show_result = models.BooleanField(_('显示成绩'), default=True)
    show_answer = models.BooleanField(_('显示答案'), default=False)
    random_order = models.BooleanField(_('随机题目顺序'), default=True)
    shuffle_options = models.BooleanField(_('随机选项顺序'), default=False)
    description = models.TextField(_('考试说明'), blank=True)
    instructions = models.TextField(_('考试须知'), blank=True)
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    participants = models.ManyToManyField(
        'users.User',
        blank=True,
        verbose_name=_('参与人员'),
        related_name='exams'
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('创建人'),
        related_name='created_exams'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    published_at = models.DateTimeField(_('发布时间'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('考试')
        verbose_name_plural = _('考试')
        db_table = 'exams'
        indexes = [
            models.Index(fields=['course']),
            models.Index(fields=['question_bank']),
            models.Index(fields=['exam_type']),
            models.Index(fields=['status']),
            models.Index(fields=['start_time']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def participant_count(self):
        """参与人数"""
        return self.participants.count()
    
    @property
    def result_count(self):
        """已考试人数"""
        return self.exam_results.filter(submitted_at__isnull=False).count()
    
    def publish(self):
        """发布考试"""
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save()
    
    def is_in_progress(self):
        """检查考试是否正在进行"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time


class ExamResult(models.Model):
    """考试成绩表"""
    
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', _('未开始')
        IN_PROGRESS = 'in_progress', _('进行中')
        SUBMITTED = 'submitted', _('已提交')
        GRADED = 'graded', _('已评分')
    
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        verbose_name=_('考试'),
        related_name='exam_results'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('用户'),
        related_name='exam_results'
    )
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED
    )
    score = models.DecimalField(_('得分'), max_digits=5, decimal_places=2, null=True, blank=True)
    correct_count = models.IntegerField(_('答对题数'), default=0)
    wrong_count = models.IntegerField(_('答错题数'), default=0)
    is_passed = models.BooleanField(_('是否通过'), default=False)
    duration = models.IntegerField(_('用时(分钟)'), default=0)
    start_time = models.DateTimeField(_('开始答题时间'), null=True, blank=True)
    submitted_at = models.DateTimeField(_('提交时间'), null=True, blank=True)
    answers = models.JSONField(_('答案数据'), default=dict, blank=True)
    review_comment = models.TextField(_('评语'), blank=True)
    certificate_no = models.CharField(_('证书编号'), max_length=100, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('考试成绩')
        verbose_name_plural = _('考试成绩')
        db_table = 'exam_results'
        unique_together = ['exam', 'user']
        indexes = [
            models.Index(fields=['exam']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['is_passed']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.real_name} - {self.exam.title}"
    
    def generate_certificate_no(self):
        """生成证书编号"""
        if not self.certificate_no and self.is_passed:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.certificate_no = f"CERT{timestamp}{random_str}"
            self.save()
        return self.certificate_no
    
    def grade(self):
        """评分"""
        if self.answers and self.status == self.Status.SUBMITTED:
            # 计算得分
            total_score = 0
            correct_count = 0
            wrong_count = 0
            
            for question_id, answer in self.answers.items():
                try:
                    question = Question.objects.get(id=question_id)
                    if answer == question.correct_answer:
                        total_score += float(question.score)
                        correct_count += 1
                    else:
                        wrong_count += 1
                except Question.DoesNotExist:
                    continue
            
            self.score = total_score
            self.correct_count = correct_count
            self.wrong_count = wrong_count
            self.is_passed = total_score >= float(self.exam.passing_score)
            self.status = self.Status.GRADED
            self.save()
            
            # 生成证书编号
            if self.is_passed:
                self.generate_certificate_no()
            
            return self.score
        return None