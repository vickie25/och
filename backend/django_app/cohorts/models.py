"""
Cohort Learning Models - Student-facing cohort experience.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from programs.models import Cohort, Enrollment

User = get_user_model()


class CohortDayMaterial(models.Model):
    """Learning materials organized by cohort day."""
    MATERIAL_TYPE_CHOICES = [
        ('video', 'Video'),
        ('article', 'Article'),
        ('slides', 'Slides'),
        ('lab', 'Lab'),
        ('reading', 'Reading'),
        ('exercise', 'Exercise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name='day_materials')
    day_number = models.IntegerField(help_text='Day number in cohort (1-based)')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES)
    content_url = models.URLField(blank=True, help_text='URL to video, article, etc.')
    content_text = models.TextField(blank=True, help_text='Embedded content')
    order = models.IntegerField(default=0, help_text='Order within the day')
    estimated_minutes = models.IntegerField(default=30)
    is_required = models.BooleanField(default=True)
    unlock_date = models.DateField(null=True, blank=True, help_text='Date when material becomes available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cohort_day_materials'
        ordering = ['cohort', 'day_number', 'order']
        unique_together = ['cohort', 'day_number', 'order']
    
    def __str__(self):
        return f"Day {self.day_number}: {self.title} ({self.cohort.name})"


class CohortMaterialProgress(models.Model):
    """Student progress on cohort materials."""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='material_progress')
    material = models.ForeignKey(CohortDayMaterial, on_delete=models.CASCADE, related_name='student_progress')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True, help_text='Student notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cohort_material_progress'
        unique_together = ['enrollment', 'material']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.enrollment.user.email} - {self.material.title}"


class CohortExam(models.Model):
    """Exams for cohorts."""
    EXAM_TYPE_CHOICES = [
        ('quiz', 'Quiz'),
        ('midterm', 'Midterm'),
        ('final', 'Final Exam'),
        ('practical', 'Practical Exam'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    description = models.TextField(blank=True)
    day_number = models.IntegerField(help_text='Day when exam is scheduled')
    duration_minutes = models.IntegerField(default=60)
    total_points = models.IntegerField(default=100)
    passing_score = models.IntegerField(default=70)
    questions = models.JSONField(default=list, help_text='List of questions')
    scheduled_date = models.DateTimeField()
    due_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cohort_exams'
        ordering = ['cohort', 'day_number']
    
    def __str__(self):
        return f"{self.title} - {self.cohort.name}"


class CohortExamSubmission(models.Model):
    """Student exam submissions."""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(CohortExam, on_delete=models.CASCADE, related_name='submissions')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='exam_submissions')
    answers = models.JSONField(default=dict, help_text='Student answers')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_exams')
    feedback = models.TextField(blank=True)
    
    class Meta:
        db_table = 'cohort_exam_submissions'
        unique_together = ['exam', 'enrollment']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.enrollment.user.email} - {self.exam.title}"


class CohortGrade(models.Model):
    """Comprehensive grades for cohort students."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='cohort_grade')
    
    # Component scores
    missions_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    capstones_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    labs_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    exams_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    participation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Overall
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    letter_grade = models.CharField(max_length=2, blank=True, help_text='A, B, C, D, F')
    rank = models.IntegerField(null=True, blank=True, help_text='Rank within cohort')
    
    # Metadata
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cohort_grades'
        ordering = ['-overall_score']
    
    def __str__(self):
        return f"{self.enrollment.user.email} - {self.overall_score}%"
    
    def calculate_overall(self):
        """Calculate overall score based on weighted components."""
        weights = {
            'missions': 0.25,
            'capstones': 0.30,
            'labs': 0.15,
            'exams': 0.25,
            'participation': 0.05,
        }
        
        self.overall_score = (
            float(self.missions_score) * weights['missions'] +
            float(self.capstones_score) * weights['capstones'] +
            float(self.labs_score) * weights['labs'] +
            float(self.exams_score) * weights['exams'] +
            float(self.participation_score) * weights['participation']
        )
        
        # Calculate letter grade
        if self.overall_score >= 90:
            self.letter_grade = 'A'
        elif self.overall_score >= 80:
            self.letter_grade = 'B'
        elif self.overall_score >= 70:
            self.letter_grade = 'C'
        elif self.overall_score >= 60:
            self.letter_grade = 'D'
        else:
            self.letter_grade = 'F'
        
        self.save()


class CohortPeerMessage(models.Model):
    """Peer-to-peer messaging within cohort."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name='peer_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_peer_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_peer_messages', null=True, blank=True)
    is_group_message = models.BooleanField(default=False, help_text='True if message to entire cohort')
    message = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cohort_peer_messages'
        ordering = ['-created_at']
    
    def __str__(self):
        recipient_str = "Group" if self.is_group_message else self.recipient.email
        return f"{self.sender.email} → {recipient_str}"


class CohortMentorMessage(models.Model):
    """Student-to-mentor messaging within cohort context."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name='mentor_messages')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cohort_mentor_messages_sent')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cohort_mentor_messages_received')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    is_read = models.BooleanField(default=False)
    replied_at = models.DateTimeField(null=True, blank=True)
    reply_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cohort_mentor_messages'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.email} → {self.mentor.email}: {self.subject}"


class CohortPayment(models.Model):
    """Cohort enrollment payments."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='cohort_payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Paystack fields
    paystack_reference = models.CharField(max_length=255, unique=True, db_index=True)
    paystack_access_code = models.CharField(max_length=255, blank=True)
    paystack_authorization_url = models.URLField(blank=True)
    paystack_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'cohort_payments'
        ordering = ['-initiated_at']
    
    def __str__(self):
        return f"{self.enrollment.user.email} - {self.amount} {self.currency} ({self.status})"
