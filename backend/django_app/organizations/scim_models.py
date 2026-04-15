import hashlib
import secrets
import uuid

from django.db import models
from django.utils import timezone

from users.models import User

from .institutional_models import InstitutionalContract


class InstitutionalSCIMToken(models.Model):
    """
    Bearer token for SCIM provisioning scoped to a single institutional contract.
    Stored as a SHA-256 hash to avoid persisting raw tokens.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.OneToOneField(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='scim_token'
    )
    token_hash = models.CharField(max_length=64, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'institutional_scim_tokens'

    @staticmethod
    def hash_token(raw: str) -> str:
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @classmethod
    def rotate_token(cls, contract):
        raw = secrets.token_urlsafe(48)
        obj, _ = cls.objects.update_or_create(
            contract=contract,
            defaults={'token_hash': cls.hash_token(raw), 'is_active': True},
        )
        return obj, raw


class InstitutionalSCIMUser(models.Model):
    """
    Maps SCIM external user IDs to local users within a contract scope.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='scim_users'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='institutional_scim_mappings'
    )
    external_id = models.CharField(max_length=255, db_index=True)
    is_active = models.BooleanField(default=True)
    raw_profile = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'institutional_scim_users'
        unique_together = [
            ('contract', 'external_id'),
            ('contract', 'user'),
        ]
        indexes = [
            models.Index(fields=['contract', 'external_id']),
            models.Index(fields=['contract', 'is_active']),
        ]


class InstitutionalSCIMEvent(models.Model):
    """
    Audit log for provisioning events.
    """
    EVENT_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('deactivate', 'Deactivate'),
        ('reactivate', 'Reactivate'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        InstitutionalContract,
        on_delete=models.CASCADE,
        related_name='scim_events'
    )
    external_id = models.CharField(max_length=255, blank=True, default='')
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    success = models.BooleanField(default=True)
    error = models.TextField(blank=True, default='')
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'institutional_scim_events'
        indexes = [
            models.Index(fields=['contract', 'created_at']),
            models.Index(fields=['contract', 'event_type']),
        ]

