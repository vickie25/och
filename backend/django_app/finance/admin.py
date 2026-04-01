"""
Finance admin interface.
"""
from django.contrib import admin
from .models import (
    Wallet, Transaction, Credit, Contract, TaxRate,
    MentorPayout, Invoice, Payment, ReconciliationRun,
    PricingTier, PricingHistory
)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'currency', 'last_transaction_at', 'created_at']
    list_filter = ['currency', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'type', 'amount', 'reference_type', 'created_at']
    list_filter = ['type', 'reference_type', 'created_at']
    search_fields = ['wallet__user__email', 'description']
    readonly_fields = ['created_at']


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'amount', 'remaining', 'expires_at', 'created_at']
    list_filter = ['type', 'expires_at', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['organization', 'type', 'status', 'total_value', 'start_date', 'end_date']
    list_filter = ['type', 'status', 'start_date', 'end_date']
    search_fields = ['organization__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ['country', 'region', 'type', 'rate', 'is_active', 'effective_date']
    list_filter = ['country', 'type', 'is_active', 'effective_date']
    search_fields = ['country', 'region']
    readonly_fields = ['created_at']


@admin.register(MentorPayout)
class MentorPayoutAdmin(admin.ModelAdmin):
    list_display = [
        'mentor', 'cohort', 'compensation_mode', 'amount', 'status',
        'period_start', 'period_end', 'created_at',
    ]
    list_filter = ['status', 'payout_method', 'compensation_mode', 'created_at']
    search_fields = ['mentor__email', 'mentor__first_name', 'mentor__last_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['mentor', 'cohort']
    date_hierarchy = 'period_start'


@admin.register(ReconciliationRun)
class ReconciliationRunAdmin(admin.ModelAdmin):
    list_display = ['period_start', 'period_end', 'book_total', 'bank_total', 'difference', 'currency', 'created_at']
    list_filter = ['currency', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'user', 'organization', 'type', 'total', 'status', 'due_date']
    list_filter = ['type', 'status', 'due_date', 'created_at']
    search_fields = ['invoice_number', 'user__email', 'organization__name']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at']
    date_hierarchy = 'due_date'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'currency', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['invoice__invoice_number', 'paystack_reference']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'display_name', 'tier_type', 'min_quantity', 'max_quantity',
        'price_per_unit', 'currency', 'billing_frequency', 'is_active', 'effective_date'
    ]
    list_filter = ['tier_type', 'currency', 'billing_frequency', 'is_active', 'effective_date']
    search_fields = ['name', 'display_name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['price_per_unit', 'is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'tier_type', 'is_active')
        }),
        ('Pricing Configuration', {
            'fields': (
                'min_quantity', 'max_quantity', 'price_per_unit', 'currency',
                'billing_frequency', 'annual_discount_percent'
            )
        }),
        ('Effective Period', {
            'fields': ('effective_date', 'expiry_date')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Track pricing changes when updated via admin"""
        if change:  # This is an update, not a creation
            old_obj = PricingTier.objects.get(pk=obj.pk)
            if old_obj.price_per_unit != obj.price_per_unit or old_obj.annual_discount_percent != obj.annual_discount_percent:
                from .services import DynamicPricingService
                DynamicPricingService.update_pricing_record(
                    tier_id=str(obj.pk),
                    new_price=obj.price_per_unit,
                    new_discount=obj.annual_discount_percent,
                    reason=f"Updated via Django Admin by {request.user.email}",
                    changed_by_user=request.user
                )
        super().save_model(request, obj, form, change)


@admin.register(PricingHistory)
class PricingHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'pricing_tier', 'old_price_per_unit', 'new_price_per_unit',
        'old_annual_discount', 'new_annual_discount', 'changed_by', 'changed_at'
    ]
    list_filter = ['pricing_tier__tier_type', 'changed_at']
    search_fields = ['pricing_tier__name', 'change_reason', 'changed_by__email']
    readonly_fields = ['pricing_tier', 'old_price_per_unit', 'new_price_per_unit', 
                      'old_annual_discount', 'new_annual_discount', 'changed_by', 'changed_at']
    date_hierarchy = 'changed_at'
    
    def has_add_permission(self, request):
        """Prevent manual addition of pricing history"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of pricing history"""
        return False