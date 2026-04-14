from rest_framework import serializers

from .models import MarketplaceEscrow


class MarketplaceEscrowSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job_application.job_posting.title', read_only=True)
    applicant_email = serializers.CharField(source='job_application.applicant.email', read_only=True)

    class Meta:
        model = MarketplaceEscrow
        fields = [
            'id', 'job_application', 'job_title', 'applicant_email',
            'gross_amount', 'currency', 'commission_rate_percent',
            'commission_amount', 'net_to_candidate', 'status',
            'paystack_reference', 'released_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'commission_amount', 'net_to_candidate',
            'released_at', 'created_at', 'updated_at',
            'job_title', 'applicant_email',
        ]


class MarketplaceEscrowCreateSerializer(serializers.Serializer):
    job_application_id = serializers.UUIDField()
    gross_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    currency = serializers.CharField(max_length=3, default='USD')
    commission_rate_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100, required=False, default=10,
    )
    paystack_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
