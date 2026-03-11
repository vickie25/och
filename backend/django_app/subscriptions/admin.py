from django.contrib import admin
from .models import (
    UserSubscription, PaymentTransaction, PromotionalCode, AcademicDiscount, 
    SubscriptionInvoice, PaymentRetryAttempt, SubscriptionPlan, PaymentGateway
)

@admin.register(PromotionalCode)
class PromotionalCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'usage_limit_per_user', 'is_active', 'valid_until']
    list_filter = ['discount_type', 'is_active', 'valid_from']
    search_fields = ['code']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'discount_type', 'discount_value')
        }),
        ('Usage Limits', {
            'fields': ('max_redemptions', 'usage_limit_per_user')
        }),
        ('Validity', {
            'fields': ('is_active', 'valid_from', 'valid_until')
        }),
        ('Restrictions', {
            'fields': ('eligible_plans',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AcademicDiscount)
class AcademicDiscountAdmin(admin.ModelAdmin):
    list_display = ['user', 'institution_name', 'verification_status', 'verified_at']
    list_filter = ['verification_status', 'verification_method', 'verified_at']
    search_fields = ['user__email', 'institution_name', 'edu_email']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('user', 'institution_name', 'edu_email')
        }),
        ('Verification', {
            'fields': ('verification_method', 'verification_status', 'document_url', 'verified_at', 'verified_by')
        }),
        ('Validity', {
            'fields': ('expires_at', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SubscriptionInvoice)
class SubscriptionInvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'user', 'total_amount', 'status', 'invoice_date']
    list_filter = ['status', 'invoice_date']
    search_fields = ['invoice_number', 'user__email']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Invoice Details', {
            'fields': ('invoice_number', 'user', 'subscription', 'transaction')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'currency')
        }),
        ('Dates', {
            'fields': ('invoice_date', 'due_date', 'paid_at', 'sent_at')
        }),
        ('Status', {
            'fields': ('status', 'notes', 'pdf_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(PaymentRetryAttempt)
class PaymentRetryAttemptAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'attempt_number', 'status', 'scheduled_at', 'attempted_at']
    list_filter = ['status', 'attempt_number', 'scheduled_at']
    search_fields = ['subscription__user__email']
    readonly_fields = ['created_at', 'updated_at', 'attempted_at']
    
    fieldsets = (
        ('Retry Information', {
            'fields': ('subscription', 'attempt_number', 'amount', 'currency')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'attempted_at', 'completed_at')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'gateway_response')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# Update existing admin classes
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'gateway', 'created_at']
    list_filter = ['status', 'gateway', 'created_at']
    search_fields = ['user__email', 'gateway_transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'subscription', 'amount', 'currency', 'gateway_transaction_id')
        }),
        ('Payment Info', {
            'fields': ('gateway', 'status')
        }),
        ('Response Data', {
            'fields': ('gateway_response', 'failure_reason')
        }),
        ('Timestamps', {
            'fields': ('processed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_end', 'created_at']
    list_filter = ['status', 'plan', 'created_at']
    search_fields = ['user__email', 'stripe_subscription_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Billing', {
            'fields': ('current_period_start', 'current_period_end', 'enhanced_access_expires_at')
        }),
        ('Gateway Info', {
            'fields': ('stripe_subscription_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# Register additional models
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'price_monthly', 'created_at']
    list_filter = ['tier']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'enabled', 'test_mode', 'created_at']
    list_filter = ['enabled', 'test_mode', 'name']
    readonly_fields = ['created_at', 'updated_at']

# Register with updated admin classes
admin.site.register(UserSubscription, UserSubscriptionAdmin)
admin.site.register(PaymentTransaction, PaymentTransactionAdmin)