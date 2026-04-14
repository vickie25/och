from django.contrib.auth import get_user_model
from rest_framework import serializers

from .employer_contracts import *

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']

class RetainerTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetainerTier
        fields = '__all__'

class EmployerContractSerializer(serializers.ModelSerializer):
    employer = UserBasicSerializer(read_only=True)
    retainer_tier = RetainerTierSerializer(read_only=True)

    class Meta:
        model = EmployerContract
        fields = '__all__'

class EmployerContractCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerContract
        exclude = ['id', 'created_at', 'updated_at']

class CandidateRequirementSerializer(serializers.ModelSerializer):
    contract = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CandidateRequirement
        fields = '__all__'

class CandidateRequirementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateRequirement
        exclude = ['id', 'created_at', 'updated_at']

class CandidatePresentationSerializer(serializers.ModelSerializer):
    requirement = CandidateRequirementSerializer(read_only=True)
    candidate = UserBasicSerializer(read_only=True)

    class Meta:
        model = CandidatePresentation
        fields = '__all__'

class CandidatePresentationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidatePresentation
        exclude = ['id', 'created_at', 'updated_at']

class SuccessfulPlacementSerializer(serializers.ModelSerializer):
    presentation = CandidatePresentationSerializer(read_only=True)

    class Meta:
        model = SuccessfulPlacement
        fields = '__all__'

class SuccessfulPlacementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuccessfulPlacement
        exclude = ['id', 'created_at', 'updated_at']

class ContractPerformanceMetricSerializer(serializers.ModelSerializer):
    contract = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ContractPerformanceMetric
        fields = '__all__'

class ReplacementGuaranteeSerializer(serializers.ModelSerializer):
    placement = SuccessfulPlacementSerializer(read_only=True)
    replacement_candidate = UserBasicSerializer(read_only=True)

    class Meta:
        model = ReplacementGuarantee
        fields = '__all__'

class ReplacementGuaranteeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplacementGuarantee
        exclude = ['id', 'created_at', 'updated_at']

class ContractSLATrackingSerializer(serializers.ModelSerializer):
    requirement = CandidateRequirementSerializer(read_only=True)

    class Meta:
        model = ContractSLATracking
        fields = '__all__'

# Dashboard serializers
class ContractDashboardSerializer(serializers.ModelSerializer):
    employer = UserBasicSerializer(read_only=True)
    retainer_tier = RetainerTierSerializer(read_only=True)
    active_requirements_count = serializers.IntegerField(read_only=True)
    total_placements = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = EmployerContract
        fields = ['id', 'employer', 'retainer_tier', 'status', 'start_date', 'end_date',
                 'active_requirements_count', 'total_placements', 'total_revenue']

class RequirementDashboardSerializer(serializers.ModelSerializer):
    contract = serializers.StringRelatedField(read_only=True)
    presentations_count = serializers.IntegerField(read_only=True)
    successful_placements_count = serializers.IntegerField(read_only=True)
    days_since_posted = serializers.IntegerField(read_only=True)
    sla_status = serializers.CharField(read_only=True)

    class Meta:
        model = CandidateRequirement
        fields = ['id', 'contract', 'title', 'status', 'priority', 'posted_date',
                 'presentations_count', 'successful_placements_count', 'days_since_posted', 'sla_status']

class PerformanceAnalyticsSerializer(serializers.Serializer):
    contract_id = serializers.UUIDField()
    total_requirements = serializers.IntegerField()
    active_requirements = serializers.IntegerField()
    total_presentations = serializers.IntegerField()
    total_placements = serializers.IntegerField()
    placement_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    avg_time_to_shortlist = serializers.DecimalField(max_digits=5, decimal_places=2)
    avg_time_to_placement = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    sla_compliance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    replacement_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
