"""
Cohorts Admin Configuration.
"""
from django.contrib import admin
from .models import (
    CohortDayMaterial,
    CohortMaterialProgress,
    CohortExam,
    CohortExamSubmission,
    CohortGrade,
    CohortPeerMessage,
    CohortMentorMessage,
    CohortPayment
)


@admin.register(CohortDayMaterial)
class CohortDayMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'cohort', 'day_number', 'material_type', 'is_required', 'unlock_date']
    list_filter = ['cohort', 'material_type', 'is_required']
    search_fields = ['title', 'description']
    ordering = ['cohort', 'day_number', 'order']


@admin.register(CohortMaterialProgress)
class CohortMaterialProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'material', 'status', 'completed_at']
    list_filter = ['status']
    search_fields = ['enrollment__user__email', 'material__title']


@admin.register(CohortExam)
class CohortExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'cohort', 'exam_type', 'day_number', 'scheduled_date', 'is_published']
    list_filter = ['cohort', 'exam_type', 'is_published']
    search_fields = ['title', 'description']


@admin.register(CohortExamSubmission)
class CohortExamSubmissionAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'exam', 'status', 'score', 'submitted_at', 'graded_at']
    list_filter = ['status', 'exam']
    search_fields = ['enrollment__user__email', 'exam__title']


@admin.register(CohortGrade)
class CohortGradeAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'overall_score', 'letter_grade', 'rank', 'last_calculated']
    list_filter = ['letter_grade']
    search_fields = ['enrollment__user__email']
    ordering = ['-overall_score']


@admin.register(CohortPeerMessage)
class CohortPeerMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'cohort', 'is_group_message', 'created_at']
    list_filter = ['cohort', 'is_group_message']
    search_fields = ['sender__email', 'recipient__email', 'message']


@admin.register(CohortMentorMessage)
class CohortMentorMessageAdmin(admin.ModelAdmin):
    list_display = ['student', 'mentor', 'cohort', 'subject', 'is_read', 'created_at']
    list_filter = ['cohort', 'is_read']
    search_fields = ['student__email', 'mentor__email', 'subject']


@admin.register(CohortPayment)
class CohortPaymentAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'amount', 'currency', 'status', 'paystack_reference', 'initiated_at', 'completed_at']
    list_filter = ['status', 'currency']
    search_fields = ['enrollment__user__email', 'paystack_reference']
    readonly_fields = ['paystack_response']
