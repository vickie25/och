"""
Finance admin interface.
"""
from django.contrib import admin
from .models import (
    Wallet, Transaction, Credit, Contract, TaxRate,
    MentorPayout, Invoice, Payment, ReconciliationRun,
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