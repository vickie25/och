"""
Organization models for the Ongoza CyberHub platform.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Organization(models.Model):
    """
    Organization model representing companies, teams, or groups.
    Supports Sponsors, Employers, and Partners.
    """
    ORG_TYPES = [
        ('sponsor', 'Sponsor'),
        ('employer', 'Employer'),
        ('partner', 'Partner'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    org_type = models.CharField(max_length=20, choices=ORG_TYPES, default='sponsor')
    description = models.TextField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    country = models.CharField(max_length=2, null=True, blank=True)  # ISO 3166-1 alpha-2
    
    # Billing contact (used when director enrolls students from this org; invoice is sent here)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(max_length=254, blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    
    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Deprecated, use status instead
    
    # Relationships
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_organizations'
    )
    members = models.ManyToManyField(
        User,
        through='OrganizationMember',
        related_name='organizations'
    )
    
    class Meta:
        db_table = 'organizations'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    """
    Through model for Organization-User relationship with roles.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'organization_members'
        unique_together = ['organization', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"


class OrganizationEnrollmentInvoice(models.Model):
    """
    Invoice sent to an organization when director enrolls students from that org.
    Finance can track status; payment via Paystack link in email.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('waived', 'Waived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='enrollment_invoices',
    )
    contact_person_name = models.CharField(max_length=255)
    contact_email = models.EmailField(max_length=254)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    line_items = models.JSONField(default=list)  # [{"student_name","email","plan_name","amount_kes"}, ...]
    total_amount_kes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='KES')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_link = models.URLField(blank=True, null=True)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_org_enrollment_invoices',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'organization_enrollment_invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f"Org invoice {self.organization.name} - {self.total_amount_kes} {self.currency}"

