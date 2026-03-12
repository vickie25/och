"""
Audit logging system for financial transactions and compliance.
Provides immutable audit trail with 7-year retention.
"""
import uuid
import json
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings

User = get_user_model()


class AuditLog(models.Model):
    """Immutable audit log for all financial operations."""
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('transfer', 'Transfer'),
        ('login', 'Login'),
        ('access', 'Access'),
    ]
    
    ENTITY_TYPES = [
        ('wallet', 'Wallet'),
        ('transaction', 'Transaction'),
        ('invoice', 'Invoice'),
        ('payment', 'Payment'),
        ('contract', 'Contract'),
        ('credit', 'Credit'),
        ('user', 'User'),
        ('subscription', 'Subscription'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who performed the action
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,  # Never delete audit logs
        related_name='audit_logs',
        null=True,
        blank=True
    )
    user_email = models.EmailField(help_text='Cached user email for retention')
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # What action was performed
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    entity_id = models.UUIDField(help_text='ID of the affected entity')
    
    # When and where
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    session_id = models.CharField(max_length=255, blank=True)
    
    # What changed (encrypted)
    old_values = models.TextField(blank=True, help_text='Encrypted JSON of old values')
    new_values = models.TextField(blank=True, help_text='Encrypted JSON of new values')
    
    # Additional context
    description = models.TextField()
    risk_level = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='low'
    )
    
    # Compliance fields
    retention_until = models.DateTimeField(
        default=lambda: timezone.now() + timedelta(days=2555),  # 7 years
        help_text='Retain until this date for compliance'
    )
    is_pci_relevant = models.BooleanField(default=False)
    is_gdpr_relevant = models.BooleanField(default=False)
    
    # Integrity protection
    checksum = models.CharField(max_length=64, help_text='SHA-256 checksum for integrity')
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'entity_type']),
            models.Index(fields=['user', 'action']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['risk_level', 'timestamp']),
            models.Index(fields=['retention_until']),
        ]
    
    def __str__(self):
        return f"{self.user_email} {self.action} {self.entity_type} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        # Encrypt sensitive data before saving
        if self.old_values and not self.old_values.startswith('gAAAAA'):  # Not already encrypted
            self.old_values = self._encrypt_data(self.old_values)
        if self.new_values and not self.new_values.startswith('gAAAAA'):  # Not already encrypted
            self.new_values = self._encrypt_data(self.new_values)
        
        # Generate integrity checksum
        self.checksum = self._generate_checksum()
        
        super().save(*args, **kwargs)
    
    def _encrypt_data(self, data):
        """Encrypt sensitive data using Fernet (AES-256)."""
        if not data:
            return data
        
        key = getattr(settings, 'AUDIT_ENCRYPTION_KEY', Fernet.generate_key())
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt sensitive data."""
        if not encrypted_data or not encrypted_data.startswith('gAAAAA'):
            return encrypted_data
        
        key = getattr(settings, 'AUDIT_ENCRYPTION_KEY', None)
        if not key:
            return '[ENCRYPTED - KEY NOT AVAILABLE]'
        
        f = Fernet(key)
        try:
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return '[DECRYPTION FAILED]'
    
    def _generate_checksum(self):
        """Generate SHA-256 checksum for integrity verification."""
        import hashlib
        data = f"{self.user_email}{self.action}{self.entity_type}{self.entity_id}{self.timestamp}{self.description}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_old_values(self):
        """Get decrypted old values."""
        return json.loads(self._decrypt_data(self.old_values)) if self.old_values else {}
    
    def get_new_values(self):
        """Get decrypted new values."""
        return json.loads(self._decrypt_data(self.new_values)) if self.new_values else {}
    
    def verify_integrity(self):
        """Verify the integrity of this audit log entry."""
        expected_checksum = self._generate_checksum()
        return self.checksum == expected_checksum


class ComplianceReport(models.Model):
    """Compliance reporting for financial operations."""
    
    REPORT_TYPES = [
        ('pci_dss', 'PCI-DSS Compliance'),
        ('gdpr', 'GDPR Compliance'),
        ('sox', 'SOX Compliance'),
        ('audit_trail', 'Audit Trail Report'),
        ('data_retention', 'Data Retention Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Report data (encrypted)
    report_data = models.TextField(help_text='Encrypted JSON report data')
    summary = models.TextField()
    
    # Compliance status
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    issues_found = models.IntegerField(default=0)
    critical_issues = models.IntegerField(default=0)
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    generated_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500, blank=True)
    
    class Meta:
        db_table = 'compliance_reports'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', 'generated_at']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period_start.date()} to {self.period_end.date()}"


class SecurityEvent(models.Model):
    """Security events and incidents tracking."""
    
    EVENT_TYPES = [
        ('failed_login', 'Failed Login'),
        ('suspicious_transaction', 'Suspicious Transaction'),
        ('data_access', 'Unauthorized Data Access'),
        ('payment_fraud', 'Payment Fraud Attempt'),
        ('api_abuse', 'API Abuse'),
        ('privilege_escalation', 'Privilege Escalation'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # Event details
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Event data
    description = models.TextField()
    event_data = models.JSONField(default=dict)
    
    # Response
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_events'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'security_events'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['severity', 'is_resolved']),
            models.Index(fields=['event_type', 'detected_at']),
            models.Index(fields=['user_ip', 'detected_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.severity} - {self.detected_at}"


# Audit logging utility functions
def log_financial_action(user, action, entity_type, entity_id, description, 
                        old_values=None, new_values=None, request=None, risk_level='low'):
    """Log a financial action to the audit trail."""
    
    user_ip = None
    user_agent = ''
    session_id = ''
    
    if request:
        user_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        session_id = request.session.session_key or ''
    
    # Determine compliance relevance
    is_pci_relevant = action in ['payment', 'refund'] or entity_type in ['payment', 'invoice']
    is_gdpr_relevant = entity_type in ['user', 'wallet'] or 'personal' in description.lower()
    
    AuditLog.objects.create(
        user=user,
        user_email=user.email if user else 'system@ongoza.com',
        user_ip=user_ip,
        user_agent=user_agent,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        session_id=session_id,
        old_values=json.dumps(old_values) if old_values else '',
        new_values=json.dumps(new_values) if new_values else '',
        description=description,
        risk_level=risk_level,
        is_pci_relevant=is_pci_relevant,
        is_gdpr_relevant=is_gdpr_relevant
    )


def log_security_event(event_type, severity, description, user=None, request=None, event_data=None):
    """Log a security event."""
    
    user_ip = '127.0.0.1'
    user_agent = ''
    
    if request:
        user_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    SecurityEvent.objects.create(
        event_type=event_type,
        severity=severity,
        user=user,
        user_ip=user_ip,
        user_agent=user_agent,
        description=description,
        event_data=event_data or {}
    )


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip