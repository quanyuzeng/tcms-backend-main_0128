"""邮件通知服务"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_email_async(subject, message, recipient_list, html_message=None):
    """异步发送邮件"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"邮件发送成功: {subject} -> {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {subject} -> {recipient_list}, 错误: {str(e)}")
        return False


class EmailService:
    """邮件服务类"""
    
    @staticmethod
    def send_course_enrollment_notification(user, course):
        """发送课程报名通知"""
        subject = f'课程报名成功 - {course.title}'
        
        # HTML模板
        html_message = render_to_string('email/course_enrollment.html', {
            'user': user,
            'course': course,
            'site_name': 'TCMS培训管理系统'
        })
        
        # 纯文本版本
        plain_message = strip_tags(html_message)
        
        # 发送邮件
        send_email_async.delay(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )
    
    @staticmethod
    def send_exam_notification(user, exam):
        """发送考试通知"""
        subject = f'考试通知 - {exam.title}'
        
        html_message = render_to_string('email/exam_notification.html', {
            'user': user,
            'exam': exam,
            'site_name': 'TCMS培训管理系统'
        })
        
        plain_message = strip_tags(html_message)
        
        send_email_async.delay(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )
    
    @staticmethod
    def send_exam_result_notification(user, exam_result):
        """发送考试成绩通知"""
        subject = f'考试成绩通知 - {exam_result.exam.title}'
        
        html_message = render_to_string('email/exam_result.html', {
            'user': user,
            'exam_result': exam_result,
            'site_name': 'TCMS培训管理系统'
        })
        
        plain_message = strip_tags(html_message)
        
        send_email_async.delay(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )
    
    @staticmethod
    def send_certificate_notification(user, certificate):
        """发送证书颁发通知"""
        subject = f'培训证书颁发 - {certificate.name}'
        
        html_message = render_to_string('email/certificate_notification.html', {
            'user': user,
            'certificate': certificate,
            'site_name': 'TCMS培训管理系统'
        })
        
        plain_message = strip_tags(html_message)
        
        send_email_async.delay(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )
    
    @staticmethod
    def send_training_plan_approval_notification(plan, is_approved, approver, comment=''):
        """发送培训计划审批通知"""
        subject = f'培训计划审批结果 - {plan.title}'
        
        # 通知创建者
        if plan.created_by and plan.created_by.email:
            html_message = render_to_string('email/training_plan_approval.html', {
                'plan': plan,
                'is_approved': is_approved,
                'approver': approver,
                'comment': comment,
                'site_name': 'TCMS培训管理系统'
            })
            
            plain_message = strip_tags(html_message)
            
            send_email_async.delay(
                subject=subject,
                message=plain_message,
                recipient_list=[plan.created_by.email],
                html_message=html_message
            )
    
    @staticmethod
    def send_password_reset_email(user, reset_token):
        """发送密码重置邮件"""
        subject = '密码重置请求'
        
        html_message = render_to_string('email/password_reset.html', {
            'user': user,
            'reset_token': reset_token,
            'site_name': 'TCMS培训管理系统'
        })
        
        plain_message = strip_tags(html_message)
        
        send_email_async.delay(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )
    
    @staticmethod
    def send_user_created_notification(user, temp_password):
        """发送用户创建通知"""
        subject = '账户创建通知'
        
        html_message = render_to_string('email/user_created.html', {
            'user': user,
            'temp_password': temp_password,
            'site_name': 'TCMS培训管理系统'
        })
        
        plain_message = strip_tags(html_message)
        
        send_email_async.delay(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )
    
    @staticmethod
    def send_certificate_expiry_warning(user, certificate):
        """发送证书即将到期提醒"""
        subject = f'证书即将到期提醒 - {certificate.name}'
        
        html_message = render_to_string('email/certificate_expiry_warning.html', {
            'user': user,
            'certificate': certificate,
            'site_name': 'TCMS培训管理系统'
        })
        
        plain_message = strip_tags(html_message)
        
        send_email_async.delay(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )
    
    @staticmethod
    def send_training_reminder(user, course):
        """发送培训提醒"""
        subject = f'培训提醒 - {course.title}'
        
        html_message = render_to_string('email/training_reminder.html', {
            'user': user,
            'course': course,
            'site_name': 'TCMS培训管理系统'
        })
        
        plain_message = strip_tags(html_message)
        
        send_email_async.delay(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )