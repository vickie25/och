from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import MarketplaceEscrow, MarketplaceCommissionLedger, JobApplication, Employer
from .escrow_serializers import (
    MarketplaceEscrowSerializer,
    MarketplaceEscrowCreateSerializer,
)


class MarketplaceEscrowViewSet(viewsets.ModelViewSet):
    """
    Escrow for job-application placement funds.
    Employers see their own; staff see all.
    """
    serializer_class = MarketplaceEscrowSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = MarketplaceEscrow.objects.select_related(
            'job_application__job_posting__employer',
            'job_application__applicant',
        )
        if user.is_staff:
            return qs.order_by('-created_at')
        emp = Employer.objects.filter(user=user).first()
        if emp:
            return qs.filter(job_application__job_posting__employer=emp).order_by('-created_at')
        return qs.none()

    def create(self, request, *args, **kwargs):
        if not (request.user.is_staff or Employer.objects.filter(user=request.user).exists()):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        ser = MarketplaceEscrowCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        app = JobApplication.objects.select_related('job_posting__employer').get(
            pk=ser.validated_data['job_application_id']
        )
        if not request.user.is_staff:
            emp = Employer.objects.filter(user=request.user).first()
            if not emp or app.job_posting.employer_id != emp.id:
                return Response({'error': 'Not your job application'}, status=status.HTTP_403_FORBIDDEN)
        escrow = MarketplaceEscrow.objects.create(
            job_application=app,
            gross_amount=ser.validated_data['gross_amount'],
            currency=ser.validated_data.get('currency', 'USD'),
            commission_rate_percent=ser.validated_data.get('commission_rate_percent', 10),
            paystack_reference=ser.validated_data.get('paystack_reference', ''),
            status='held',
        )
        return Response(MarketplaceEscrowSerializer(escrow).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def release(self, request, pk=None):
        escrow = self.get_object()
        if not request.user.is_staff:
            emp = Employer.objects.filter(user=request.user).first()
            if not emp or escrow.job_application.job_posting.employer_id != emp.id:
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        if escrow.status != 'held':
            return Response({'error': 'Only held escrows can be released'}, status=status.HTTP_400_BAD_REQUEST)
        escrow.status = 'released'
        escrow.released_at = timezone.now()
        escrow.save()
        if not MarketplaceCommissionLedger.objects.filter(escrow=escrow).exists():
            MarketplaceCommissionLedger.objects.create(
                escrow=escrow,
                job_application=escrow.job_application,
                gross_amount=escrow.gross_amount,
                commission_amount=escrow.commission_amount,
                net_to_candidate=escrow.net_to_candidate,
                currency=escrow.currency,
            )
        return Response(MarketplaceEscrowSerializer(escrow).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def refund(self, request, pk=None):
        escrow = self.get_object()
        if escrow.status != 'held':
            return Response({'error': 'Only held escrows can be refunded'}, status=status.HTTP_400_BAD_REQUEST)
        escrow.status = 'refunded'
        escrow.released_at = timezone.now()
        escrow.save()
        return Response(MarketplaceEscrowSerializer(escrow).data)
