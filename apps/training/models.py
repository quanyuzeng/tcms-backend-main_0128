"""Training models"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class CourseCategory(models.Model):
    """课程分类表"""
    
    name = models.CharField(_('分类名称'), max_length=100)
    code = models.CharField(_('分类代码'), max_length=50, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('上级分类'),
        related_name='children'
    )
    description = models.TextField(_('分类描述'), blank=True)
    sort_order = models.IntegerField(_('排序'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('课程分类')
        verbose_name_plural = _('课程分类')
        db_table = 'course_categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class Course(models.Model):
    """课程表"""
    
    class CourseType(models.TextChoices):
        ONLINE = 'online', _('在线课程')
        OFFLINE = 'offline', _('线下培训')
        MIXED = 'mixed', _('混合模式')
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('草稿')
        PUBLISHED = 'published', _('已发布')
        ARCHIVED = 'archived', _('已归档')
    
    code = models.CharField(_('课程编号'), max_length=50, unique=True)
    title = models.CharField(_('课程标题'), max_length=200)
    description = models.TextField(_('课程描述'), blank=True)
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('课程分类'),
        related_name='courses'
    )
    course_type = models.CharField(
        _('课程类型'),
        max_length=20,
        choices=CourseType.choices,
        default=CourseType.ONLINE
    )
    duration = models.IntegerField(_('课程时长(分钟)'), default=60)
    credit = models.DecimalField(_('学分'), max_digits=3, decimal_places=1, default=1.0)
    passing_score = models.DecimalField(_('及格分数'), max_digits=5, decimal_places=2, default=60.00)
    instructor = models.CharField(_('讲师'), max_length=100, blank=True)
    thumbnail = models.ImageField(
        _('课程封面'),
        upload_to='courses/%Y/%m/',
        blank=True,
        null=True
    )
    content_url = models.URLField(_('课程内容链接'), blank=True)
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        verbose_name=_('前置课程'),
        related_name='prerequisite_for'
    )
    tags = models.CharField(_('标签'), max_length=255, blank=True)
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    view_count = models.IntegerField(_('浏览次数'), default=0)
    enrollment_count = models.IntegerField(_('报名人数'), default=0)
    completion_count = models.IntegerField(_('完成人数'), default=0)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('创建人'),
        related_name='created_courses'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    published_at = models.DateTimeField(_('发布时间'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('课程')
        verbose_name_plural = _('课程')
        db_table = 'courses'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['course_type']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def completion_rate(self):
        """课程完成率"""
        if self.enrollment_count == 0:
            return 0.0
        return round((self.completion_count / self.enrollment_count) * 100, 2)
    
    def publish(self):
        """发布课程"""
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save()


class TrainingPlan(models.Model):
    """培训计划表"""
    
    class PlanType(models.TextChoices):
        INDIVIDUAL = 'individual', _('个人计划')
        DEPARTMENT = 'department', _('部门计划')
        POSITION = 'position', _('岗位计划')
        COMPANY = 'company', _('公司计划')
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('草稿')
        PENDING = 'pending', _('待审批')
        APPROVED = 'approved', _('已批准')
        REJECTED = 'rejected', _('已拒绝')
        IN_PROGRESS = 'in_progress', _('进行中')
        COMPLETED = 'completed', _('已完成')
        CANCELLED = 'cancelled', _('已取消')
    
    code = models.CharField(_('计划编号'), max_length=50, unique=True)
    title = models.CharField(_('计划标题'), max_length=200)
    description = models.TextField(_('计划描述'), blank=True)
    plan_type = models.CharField(
        _('计划类型'),
        max_length=20,
        choices=PlanType.choices,
        default=PlanType.DEPARTMENT
    )
    target_department = models.ForeignKey(
        'organization.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('目标部门'),
        related_name='training_plans'
    )
    target_position = models.ForeignKey(
        'organization.Position',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('目标岗位'),
        related_name='training_plans'
    )
    target_users = models.ManyToManyField(
        'users.User',
        blank=True,
        verbose_name=_('目标用户'),
        related_name='assigned_training_plans'
    )
    courses = models.ManyToManyField(
        Course,
        verbose_name=_('课程列表'),
        related_name='training_plans'
    )
    start_date = models.DateField(_('开始日期'))
    end_date = models.DateField(_('结束日期'))
    total_hours = models.IntegerField(_('总学时'), default=0)
    total_courses = models.IntegerField(_('课程数量'), default=0)
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('审批人'),
        related_name='approved_training_plans'
    )
    approved_at = models.DateTimeField(_('审批时间'), null=True, blank=True)
    approval_comment = models.TextField(_('审批意见'), blank=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('创建人'),
        related_name='created_training_plans'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('培训计划')
        verbose_name_plural = _('培训计划')
        db_table = 'training_plans'
        indexes = [
            models.Index(fields=['plan_type']),
            models.Index(fields=['status']),
            models.Index(fields=['target_department']),
            models.Index(fields=['target_position']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # 自动计算总学时和课程数量
        if self.pk:
            self.total_hours = sum(course.duration for course in self.courses.all())
            self.total_courses = self.courses.count()
        super().save(*args, **kwargs)
    
    def approve(self, approved_by, comment=''):
        """审批培训计划"""
        self.status = self.Status.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_comment = comment
        self.save()


class TrainingRecord(models.Model):
    """培训记录表"""
    
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', _('未开始')
        IN_PROGRESS = 'in_progress', _('学习中')
        COMPLETED = 'completed', _('已完成')
        FAILED = 'failed', _('未通过')
        EXEMPTED = 'exempted', _('免修')
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('用户'),
        related_name='training_records'
    )
    plan = models.ForeignKey(
        TrainingPlan,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('培训计划'),
        related_name='training_records'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name=_('课程'),
        related_name='training_records'
    )
    status = models.CharField(
        _('学习状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED
    )
    progress = models.IntegerField(_('学习进度(%)'), default=0)
    study_duration = models.IntegerField(_('学习时长(分钟)'), default=0)
    complete_date = models.DateTimeField(_('完成时间'), null=True, blank=True)
    score = models.DecimalField(_('考试成绩'), max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(_('学习反馈'), blank=True)
    evaluation = models.TextField(_('课程评价'), blank=True)
    certificate_no = models.CharField(_('证书编号'), max_length=100, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('培训记录')
        verbose_name_plural = _('培训记录')
        db_table = 'training_records'
        unique_together = ['user', 'course', 'plan']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['course']),
            models.Index(fields=['plan']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.real_name} - {self.course.title}"
    
    def complete(self, score=None, certificate_no=''):
        """完成培训"""
        self.status = self.Status.COMPLETED
        self.progress = 100
        self.complete_date = timezone.now()
        self.score = score
        self.certificate_no = certificate_no
        self.save()
        
        # 更新课程统计
        self.course.completion_count += 1
        self.course.save()