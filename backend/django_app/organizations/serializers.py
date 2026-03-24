"""
Organization serializers for DRF.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Organization, OrganizationMember
from users.serializers import UserSerializer


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for Organization model.
    Auto-generates slug from name if not provided.
    """
    owner = UserSerializer(read_only=True)
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    slug = serializers.SlugField(required=False, allow_blank=True)
    enrollment_status = serializers.SerializerMethodField()
    enrollment_status_label = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'logo_url',
            'website',
            'owner',
            'member_count',
            'org_type',
            'status',
            'is_active',
            'contact_person_name',
            'contact_email',
            'contact_phone',
            'enrollment_status',
            'enrollment_status_label',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

    def get_enrollment_status(self, obj):
        """
        Enrollment eligibility lifecycle for director organizations view:
        - active: contract created and invoice paid
        - pending_invoice_payment: contract exists but no paid invoice yet
        - pending_contract_creation: no contract yet
        """
        from finance.models import Contract, Invoice
        from organizations.institutional_models import InstitutionalContract, InstitutionalBilling

        today = timezone.now().date()

        # Finance contract path
        finance_contract_qs = Contract.objects.filter(
            organization=obj,
            type='institution',
            start_date__lte=today,
            end_date__gte=today,
        ).exclude(status='terminated')
        has_finance_contract = finance_contract_qs.exists()
        has_finance_paid = Invoice.objects.filter(
            contract__in=finance_contract_qs,
            status='paid',
        ).exists()

        # Institutional contract path
        institutional_contract_qs = InstitutionalContract.objects.filter(
            organization=obj,
            start_date__lte=today,
            end_date__gte=today,
        ).exclude(status='terminated')
        has_institutional_contract = institutional_contract_qs.exists()
        has_institutional_paid = InstitutionalBilling.objects.filter(
            contract__in=institutional_contract_qs,
            status='paid',
        ).exists()

        has_contract = has_finance_contract or has_institutional_contract
        has_paid = has_finance_paid or has_institutional_paid

        if has_paid:
            return 'active'
        if has_contract:
            return 'pending_invoice_payment'
        return 'pending_contract_creation'

    def get_enrollment_status_label(self, obj):
        status_value = self.get_enrollment_status(obj)
        labels = {
            'active': 'Active',
            'pending_contract_creation': 'Pending contract creation',
            'pending_invoice_payment': 'Pending invoice payment',
        }
        return labels.get(status_value, status_value)
    
    def validate(self, attrs):
        """Auto-generate slug from name if not provided."""
        from django.utils.text import slugify
        
        # If slug is not provided or empty, generate it from name
        if not attrs.get('slug'):
            name = attrs.get('name', '')
            if name:
                base_slug = slugify(name)[:50]  # Limit to 50 chars
                slug = base_slug
                
                # Ensure uniqueness by appending number if needed
                model = self.Meta.model
                counter = 1
                while model.objects.filter(slug=slug).exists():
                    # If updating, exclude current instance
                    if self.instance:
                        if model.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                            slug = f"{base_slug}-{counter}"[:50]
                            counter += 1
                        else:
                            break
                    else:
                        slug = f"{base_slug}-{counter}"[:50]
                        counter += 1
                
                attrs['slug'] = slug
        
        return attrs


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for OrganizationMember model.
    """
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = [
            'id',
            'organization',
            'user',
            'role',
            'joined_at',
        ]
        read_only_fields = ['id', 'joined_at']


