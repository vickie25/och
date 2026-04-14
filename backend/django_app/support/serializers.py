from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ProblemCode, SupportTicket, SupportTicketAttachment, SupportTicketResponse

User = get_user_model()


class SupportTicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicketAttachment
        fields = ['id', 'file_name', 'file_path', 'file_size', 'mime_type', 'created_at']
        read_only_fields = fields


class SupportTicketResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicketResponse
        fields = ['id', 'message', 'is_staff', 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']


class SupportTicketResponseCreateSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False)
    send_copy_to_email = serializers.BooleanField(default=False)


class ProblemCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemCode
        fields = [
            'id', 'code', 'name', 'description', 'category',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SupportTicketListSerializer(serializers.ModelSerializer):
    problem_code_display = serializers.SerializerMethodField()
    problem_code = serializers.SerializerMethodField()
    assigned_to_email = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'subject', 'status', 'priority', 'problem_code', 'problem_code_display',
            'reporter_email', 'reporter_name', 'assigned_to', 'assigned_to_email',
            'created_at', 'updated_at', 'resolved_at',
        ]

    def get_problem_code(self, obj):
        return obj.problem_code.code if obj.problem_code else ''

    def get_problem_code_display(self, obj):
        if obj.problem_code:
            return f"{obj.problem_code.code} – {obj.problem_code.name}"
        return None

    def get_assigned_to_email(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.email
        return None


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    problem_code_detail = ProblemCodeSerializer(source='problem_code', read_only=True)
    assigned_to_email = serializers.SerializerMethodField()
    responses = SupportTicketResponseSerializer(many=True, read_only=True)
    attachments = SupportTicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'subject', 'description', 'status', 'priority',
            'problem_code', 'problem_code_detail', 'internal_notes',
            'reporter_id', 'reporter_email', 'reporter_name',
            'assigned_to', 'assigned_to_email', 'resolution_notes',
            'resolved_at', 'created_at', 'updated_at', 'created_by',
            'responses', 'attachments',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_assigned_to_email(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.email
        return None


class SupportTicketCreateUpdateSerializer(serializers.ModelSerializer):
    problem_code = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.CharField(required=False, default='medium')

    class Meta:
        model = SupportTicket
        fields = [
            'subject', 'description', 'status', 'priority', 'problem_code',
            'internal_notes', 'reporter_id', 'reporter_email', 'reporter_name',
            'assigned_to', 'resolution_notes',
        ]

    def validate_problem_code(self, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        from .models import ProblemCode
        s = str(value).strip()
        try:
            if s.isdigit():
                return ProblemCode.objects.get(pk=int(s))
            return ProblemCode.objects.get(code=s)
        except ProblemCode.DoesNotExist:
            raise serializers.ValidationError("Invalid problem code.")

    def validate_priority(self, value):
        if not value:
            return 'medium'
        if value == 'critical':
            return 'urgent'
        valid = {'low', 'medium', 'high', 'urgent'}
        if value.lower() in valid:
            return value.lower()
        return 'medium'
