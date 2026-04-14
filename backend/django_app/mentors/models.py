"""
Mentor models for Ongóza Cyber Hub.
Complete mentor dashboard system with student assignments and feedback tracking.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Mentor(models.Model):
    """
    Extended mentor profile with expertise, capacity, and availability.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_profile'
    )

    # Profile
    mentor_slug = models.SlugField(unique=True, max_length=100, help_text="URL-friendly identifier")
    bio = models.TextField(blank=True, null=True, help_text="Mentor biography and experience")

    # Expertise and capacity
    expertise_tracks = models.JSONField(
        default=list,
        blank=True,
        help_text='["defender", "grc", "offensive", "innovation", "leadership"]'
    )
    max_students_per_cohort = models.IntegerField(default=25, help_text="Maximum students mentor can handle")

    # Availability (Google Calendar integration)
    availability_calendar = models.JSONField(
        default=dict,
        blank=True,
        help_text='Google Calendar integration data'
    )

    # Rating (computed from student ratings)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average rating from all student ratings (1-5)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mentors'
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['mentor_slug']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.mentor_slug})"

    def get_assigned_students_count(self):
        """Get current number of assigned students."""
        return self.mentor_assignments.filter(is_active=True).count()

    def get_available_capacity(self):
        """Get remaining capacity for new students."""
        return max(0, self.max_students_per_cohort - self.get_assigned_students_count())

    def is_at_capacity(self):
        """Check if mentor is at maximum capacity."""
        return self.get_assigned_students_count() >= self.max_students_per_cohort

    def update_average_rating(self):
        """Update mentor's average rating from all ratings."""
        from django.db.models import Avg
        avg = self.ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
        if avg is not None:
            self.average_rating = round(avg, 2)
            self.save(update_fields=['average_rating'])


class MentorStudentAssignment(models.Model):
    """
    Mentor-student assignments with track-specific relationships.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        related_name='dashboard_assignments'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_mentor_assignments'
    )

    # Assignment details
    track_slug = models.CharField(max_length=50, help_text="Track: defender, grc, offensive, etc.")
    assigned_at = models.DateTimeField(auto_now_add=True)
    last_interaction_at = models.DateTimeField(null=True, blank=True)

    # Performance tracking
    feedback_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average rating from student (1-5)"
    )

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'mentor_student_assignments'
        unique_together = ['mentor', 'student', 'track_slug']
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['mentor', 'is_active']),
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['track_slug']),
            models.Index(fields=['assigned_at']),
        ]

    def __str__(self):
        return f"{self.mentor} → {self.student} ({self.track_slug})"

    def update_last_interaction(self):
        """Update last interaction timestamp."""
        self.last_interaction_at = timezone.now()
        self.save(update_fields=['last_interaction_at'])


class MentorStudentNote(models.Model):
    """
    Mentor feedback and notes on students.
    """
    NOTE_TYPES = [
        ('strength', 'Strength'),
        ('improvement', 'Improvement Area'),
        ('action_item', 'Action Item'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        related_name='dashboard_notes'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_mentor_notes'
    )

    # Note details
    track_slug = models.CharField(max_length=50, null=True, blank=True)
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES)
    content = models.TextField(help_text="Detailed feedback or note content")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mentor_student_notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mentor']),
            models.Index(fields=['student']),
            models.Index(fields=['note_type']),
            models.Index(fields=['track_slug']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.mentor} note on {self.student}: {self.note_type}"


class MentorSession(models.Model):
    """
    Scheduled 1:1 mentor sessions.
    """
    SESSION_STATUS = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        related_name='dashboard_sessions'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_mentor_sessions'
    )

    # Session details
    track_slug = models.CharField(max_length=50, help_text="Track being discussed")
    title = models.CharField(max_length=200, help_text="Session title/agenda")
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='scheduled')

    # Meeting details
    meeting_url = models.URLField(null=True, blank=True, help_text="Zoom/Google Meet link")
    notes = models.TextField(blank=True, null=True, help_text="Session preparation notes")

    # Outcome tracking
    completed_at = models.DateTimeField(null=True, blank=True)
    student_feedback = models.TextField(blank=True, null=True)
    mentor_feedback = models.TextField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mentor_sessions'
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['mentor', 'scheduled_at']),
            models.Index(fields=['student', 'scheduled_at']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_at']),
        ]

    def __str__(self):
        return f"{self.mentor} ↔ {self.student} ({self.scheduled_at.date()})"

    def mark_completed(self, student_feedback=None, mentor_feedback=None):
        """Mark session as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if student_feedback:
            self.student_feedback = student_feedback
        if mentor_feedback:
            self.mentor_feedback = mentor_feedback
        self.save()

    def is_upcoming(self):
        """Check if session is upcoming."""
        return self.status in ['scheduled', 'confirmed'] and self.scheduled_at > timezone.now()

    def is_today(self):
        """Check if session is scheduled for today."""
        today = timezone.now().date()
        return self.scheduled_at.date() == today and self.is_upcoming()


class MentorRating(models.Model):
    """
    Student ratings and reviews for mentors.
    Ratings convert to credits: 5 stars = 10 credits, 4 stars = 8, 3 stars = 6, 2 stars = 4, 1 star = 2
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_ratings_given'
    )

    # Rating details
    rating = models.IntegerField(
        choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)],
        help_text="Rating from 1-5 stars"
    )
    review = models.TextField(blank=True, null=True, help_text="Written review/feedback")

    # Credits awarded for this rating
    credits_awarded = models.IntegerField(default=0, help_text="Credits awarded to mentor based on rating")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mentor_ratings'
        unique_together = ['mentor', 'student']  # One rating per student per mentor
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mentor', 'rating']),
            models.Index(fields=['student']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.student} rated {self.mentor}: {self.rating} stars"

    def calculate_credits(self):
        """Calculate credits based on rating: 5=10, 4=8, 3=6, 2=4, 1=2"""
        credit_map = {5: 10, 4: 8, 3: 6, 2: 4, 1: 2}
        return credit_map.get(self.rating, 0)

    def save(self, *args, **kwargs):
        """
        Override save to calculate and award credits.

        - On first rating by a student: award full credits (5→10, 4→8, 3→6, 2→4, 1→2)
        - On updates: award only the positive delta if the new rating increases credits
          (we do not claw back credits if the rating is lowered).
        """
        is_new = self._state.adding
        previous_credits = 0
        if not is_new and self.pk:
            try:
                previous_credits = (
                    MentorRating.objects.only("credits_awarded").get(pk=self.pk).credits_awarded
                    or 0
                )
            except MentorRating.DoesNotExist:
                previous_credits = 0

        # Calculate credits for this rating
        self.credits_awarded = self.calculate_credits()

        super().save(*args, **kwargs)

        # Award credits to mentor (new rating or positive delta)
        delta = self.credits_awarded - previous_credits
        if is_new or delta > 0:
            from .services import MentorCreditService
            MentorCreditService.award_credits_for_rating(self, override_amount=delta if not is_new else None)

        # Update mentor's average rating
        self.mentor.update_average_rating()


class MentorCredit(models.Model):
    """
    Mentor credits balance and tracking.
    Credits earned from student ratings, can be redeemed for courses, certificates, badges, priority matching.
    """
    CREDIT_SOURCES = [
        ('rating', 'Student Rating'),
        ('bonus', 'Platform Bonus'),
        ('referral', 'Referral'),
        ('achievement', 'Achievement Unlock'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.OneToOneField(
        Mentor,
        on_delete=models.CASCADE,
        related_name='credit_balance'
    )

    # Balance
    total_earned = models.IntegerField(default=0, help_text="Total credits ever earned")
    total_redeemed = models.IntegerField(default=0, help_text="Total credits redeemed")
    current_balance = models.IntegerField(default=0, help_text="Available credits")

    # Metadata
    last_earned_at = models.DateTimeField(null=True, blank=True)
    last_redeemed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mentor_credits'
        ordering = ['-current_balance']

    def __str__(self):
        return f"{self.mentor}: {self.current_balance} credits"

    def add_credits(self, amount, source='rating'):
        """Add credits to balance"""
        self.total_earned += amount
        self.current_balance += amount
        self.last_earned_at = timezone.now()
        self.save()

    def redeem_credits(self, amount):
        """Redeem credits (deduct from balance)"""
        if amount > self.current_balance:
            raise ValueError("Insufficient credits")

        self.total_redeemed += amount
        self.current_balance -= amount
        self.last_redeemed_at = timezone.now()
        self.save()

    def has_sufficient_credits(self, amount):
        """Check if mentor has sufficient credits"""
        return self.current_balance >= amount


class CreditTransaction(models.Model):
    """
    History of all credit transactions (earnings and redemptions).
    """
    TRANSACTION_TYPES = [
        ('earned', 'Credits Earned'),
        ('redeemed', 'Credits Redeemed'),
        ('expired', 'Credits Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        related_name='credit_transactions'
    )

    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField(help_text="Number of credits")
    description = models.CharField(max_length=255)

    # Source/reason
    source = models.CharField(
        max_length=50,
        choices=MentorCredit.CREDIT_SOURCES,
        null=True,
        blank=True
    )
    related_rating = models.ForeignKey(
        MentorRating,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_transaction'
    )

    # Running balance after this transaction
    balance_after = models.IntegerField(help_text="Balance after this transaction")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'credit_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mentor', 'created_at']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.mentor}: {self.transaction_type} {self.amount} credits"


class CreditRedemption(models.Model):
    """
    Mentor credit redemptions for rewards (courses, certificates, badges, priority matching).
    """
    REDEMPTION_TYPES = [
        ('course', 'Course Purchase'),
        ('certificate', 'Certificate Generation'),
        ('badge', 'Profile Badge'),
        ('priority_matching', 'Priority Student Matching'),
        ('featured_profile', 'Featured Profile'),
    ]

    REDEMPTION_COSTS = {
        'course': 50,
        'certificate': 30,
        'badge': 20,
        'priority_matching': 40,
        'featured_profile': 100,
    }

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        related_name='credit_redemptions'
    )

    # Redemption details
    redemption_type = models.CharField(max_length=30, choices=REDEMPTION_TYPES)
    credits_used = models.IntegerField(help_text="Credits redeemed")
    description = models.CharField(max_length=255, help_text="What was redeemed")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Related entities
    course_id = models.UUIDField(null=True, blank=True, help_text="If redeeming for course")
    certificate_id = models.UUIDField(null=True, blank=True, help_text="If generating certificate")
    badge_type = models.CharField(max_length=50, null=True, blank=True, help_text="If redeeming for badge")

    # Metadata
    redeemed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'credit_redemptions'
        ordering = ['-redeemed_at']
        indexes = [
            models.Index(fields=['mentor', 'status']),
            models.Index(fields=['redemption_type']),
            models.Index(fields=['redeemed_at']),
        ]

    def __str__(self):
        return f"{self.mentor}: {self.redemption_type} ({self.credits_used} credits)"

    @classmethod
    def get_cost(cls, redemption_type):
        """Get credit cost for a redemption type"""
        return cls.REDEMPTION_COSTS.get(redemption_type, 0)

    def mark_completed(self):
        """Mark redemption as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
