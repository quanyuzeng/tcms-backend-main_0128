"""Competency models"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import random
import string


class Competency(models.Model):
    """能力表"""
    
    class Level(models.TextChoices):
        AWARE = 'aware', _('了解')
        PROFICIENT = 'proficient', _('掌握')
        SKILLED = 'skilled', _('熟练')
        MASTER = 'master', _('精通')
    
    class AssessmentMethod(models.TextChoices):
        EXAM = 'exam', _('考试')
        EVALUATION = 'evaluation', _('评估')
        CERTIFICATION = 'certification', _('认证')
        PRACTICAL = 'practical', _('实操')
    
    name = models.CharField(_('能力名称'), max_length=100)
    code = models.CharField(_('能力代码'), max_length=50, unique=True)
    description = models.TextField(_('能力描述'), blank=True)
    category = models.CharField(_('能力分类'), max_length=50, blank=True)
    level = models.CharField(
        _('能力级别'),
        max_length=20,
        choices=Level.choices,
        default=Level.PROFICIENT
    )
    assessment_method = models.CharField(
        _('评估方式'),
        max_length=20,
        choices=AssessmentMethod.choices,
        default=AssessmentMethod.EXAM
    )
    required = models.BooleanField(_('是否必需'), default=True)
    passing_score = models.DecimalField(_('达标分数'), max_digits=5, decimal_places=2, default=60.00)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('上级能力'),
        related_name='children'
    )
    related_positions = models.ManyToManyField(
        'organization.Position',
        blank=True,
        verbose_name=_('关联岗位'),
        related_name='required_competencies'
    )
    related_courses = models.ManyToManyField(
        'training.Course',
        blank=True,
        verbose_name=_('关联课程'),
        related_name='related_competencies'
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('创建人'),
        related_name='created_competencies'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('能力')
        verbose_name_plural = _('能力')
        db_table = 'competencies'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CompetencyAssessment(models.Model):
    """能力评估表"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('待评估')
        IN_PROGRESS = 'in_progress', _('评估中')
        COMPLETED = 'completed', _('已完成')
        APPROVED = 'approved', _('已审批')
        REJECTED = 'rejected', _('已拒绝')
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('被评估人'),
        related_name='competency_assessments'
    )
    competency = models.ForeignKey(
        Competency,
        on_delete=models.CASCADE,
        verbose_name=_('能力'),
        related_name='assessments'
    )
    assessor = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('评估人'),
        related_name='conducted_assessments'
    )
    level = models.CharField(
        _('评估级别'),
        max_length=20,
        choices=Competency.Level.choices,
        null=True,
        blank=True
    )
    score = models.DecimalField(_('评估分数'), max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        _('评估状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    evidence = models.TextField(_('能力证明'), blank=True)
    assessor_comment = models.TextField(_('评估意见'), blank=True)
    assessed_at = models.DateTimeField(_('评估时间'), null=True, blank=True)
    expires_at = models.DateTimeField(_('过期时间'), null=True, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('能力评估')
        verbose_name_plural = _('能力评估')
        db_table = 'competency_assessments'
        unique_together = ['user', 'competency']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['competency']),
            models.Index(fields=['assessor']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.real_name} - {self.competency.name}"
    
    @property
    def is_expired(self):
        """检查评估是否过期"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def approve(self):
        """审批通过"""
        self.status = self.Status.APPROVED
        self.assessed_at = timezone.now()
        self.save()
    
    # 修复：添加生成证书方法
    def generate_certificate(self, issued_by=None, expiry_days=365):
        """根据评估生成证书"""
        if self.status != self.Status.APPROVED:
            raise ValueError('只有已审批的评估才能生成证书')
        
        from .models import Certificate
        
        # 计算到期日期
        issue_date = timezone.now().date()
        expiry_date = issue_date + timezone.timedelta(days=expiry_days)
        
        # 创建证书
        certificate = Certificate.objects.create(
            name=f"{self.competency.name}证书",
            user=self.user,
            competency=self.competency,
            assessment=self,
            issue_date=issue_date,
            expiry_date=expiry_date,
            issued_by=issued_by or self.assessor
        )
        
        return certificate


class Certificate(models.Model):
    """证书表"""
    
    class Status(models.TextChoices):
        VALID = 'valid', _('有效')
        EXPIRED = 'expired', _('已过期')
        REVOKED = 'revoked', _('已吊销')
    
    name = models.CharField(_('证书名称'), max_length=100)
    certificate_no = models.CharField(_('证书编号'), max_length=100, unique=True)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('持有人'),
        related_name='certificates'
    )
    competency = models.ForeignKey(
        Competency,
        on_delete=models.CASCADE,
        verbose_name=_('关联能力'),
        related_name='certificates'
    )
    assessment = models.ForeignKey(
        CompetencyAssessment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('关联评估'),
        related_name='certificate'
    )
    exam_result = models.ForeignKey(
        'examination.ExamResult',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('关联考试成绩'),
        related_name='certificate'
    )
    issue_date = models.DateField(_('颁发日期'))
    expiry_date = models.DateField(_('到期日期'), null=True, blank=True)
    verification_code = models.CharField(_('验证码'), max_length=50, unique=True)
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.VALID
    )
    issued_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('颁发人'),
        related_name='issued_certificates'
    )
    certificate_file = models.FileField(
        _('证书文件'),
        upload_to='certificates/%Y/%m/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('证书')
        verbose_name_plural = _('证书')
        db_table = 'certificates'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['competency']),
            models.Index(fields=['status']),
            models.Index(fields=['certificate_no']),
            models.Index(fields=['verification_code']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.real_name}"
    
    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = self.generate_verification_code()
        if not self.certificate_no:
            self.certificate_no = self.generate_certificate_no()
        super().save(*args, **kwargs)
    
    def generate_verification_code(self):
        """生成验证码"""
        timestamp = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"VC{timestamp}{random_str}"
    
    def generate_certificate_no(self):
        """生成证书编号"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"CERT{timestamp}{random_str}"
    
    @property
    def is_expired(self):
        """检查证书是否过期"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    def revoke(self):
        """吊销证书"""
        self.status = self.Status.REVOKED
        self.save()
    
    def verify(self):
        """验证证书有效性"""
        if self.status == self.Status.REVOKED:
            return False, _('证书已被吊销')
        if self.is_expired:
            return False, _('证书已过期')
        return True, _('证书有效')