"""
Finance views for wallet, credits, contracts, and financial management.
"""
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Sum
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers as drf_serializers
from users.utils.sms_utils import send_sms_message
import logging
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import (
    Wallet, Transaction, Credit, Contract, TaxRate,
    MentorPayout, Invoice, Payment
)
from .serializers import (
    WalletSerializer, TransactionSerializer, CreditSerializer,
    ContractSerializer, TaxRateSerializer, MentorPayoutSerializer,
    InvoiceSerializer, PaymentSerializer, WalletTopUpSerializer,
    CreditPurchaseSerializer
)
from subscriptions.models import UserSubscription
from programs.permissions import user_has_finance_role
from organizations.models import OrganizationMember
from users.models import Role, UserRole

logger = logging.getLogger(__name__)
User = get_user_model()


class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Wallet.objects.all()
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """Get current user's wallet."""
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def top_up(self, request, pk=None):
        """Add balance to wallet."""
        wallet = self.get_object()
        if wallet.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = WalletTopUpSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            description = serializer.validated_data['description']
            
            wallet.add_balance(amount, description)
            
            return Response({
                'message': 'Wallet topped up successfully',
                'new_balance': wallet.balance
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get wallet transaction history."""
        wallet = self.get_object()
        if wallet.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        transactions = wallet.transactions.all()[:50]  # Last 50 transactions
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(wallet__user=self.request.user)


class CreditViewSet(viewsets.ModelViewSet):
    serializer_class = CreditSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Credit.objects.all()
        return Credit.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def purchase(self, request):
        """Purchase credits."""
        serializer = CreditPurchaseSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            credit_type = serializer.validated_data['type']
            expires_days = serializer.validated_data.get('expires_days')
            
            expires_at = None
            if expires_days:
                expires_at = timezone.now() + timedelta(days=expires_days)
            
            credit = Credit.objects.create(
                user=request.user,
                type=credit_type,
                amount=amount,
                remaining=amount,
                expires_at=expires_at
            )
            
            # Add to wallet
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            wallet.add_balance(amount, f"Credit purchase - {credit_type}")
            
            return Response({
                'message': 'Credits purchased successfully',
                'credit_id': credit.id,
                'amount': amount
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get user's credit summary."""
        credits = self.get_queryset().filter(remaining__gt=0)
        
        # Group by type
        summary = {}
        for credit in credits:
            if credit.type not in summary:
                summary[credit.type] = {
                    'total_amount': Decimal('0'),
                    'total_remaining': Decimal('0'),
                    'count': 0
                }
            summary[credit.type]['total_amount'] += credit.amount
            summary[credit.type]['total_remaining'] += credit.remaining
            summary[credit.type]['count'] += 1
        
        return Response(summary)


class ContractViewSet(viewsets.ModelViewSet):
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user_has_finance_role(user):
            return Contract.objects.all()
        # Users can only see contracts for their organizations
        user_orgs = user.organizations.all()
        return Contract.objects.filter(organization__in=user_orgs)

    def get_permissions(self):
        if getattr(self, 'action', None) in {
            'institution_onboarding_preview',
            'institution_onboarding_complete',
        }:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        """
        Create contracts with temporary backend defaults for value/terms and
        notify institutions by email with onboarding steps.
        """
        with transaction.atomic():
            contract = serializer.save(
                status='proposal',
                total_value=serializer.validated_data.get('total_value', Decimal('0.00')),
                payment_terms=serializer.validated_data.get('payment_terms', 'Net 30'),
            )
            org = contract.organization
            if not org or not org.contact_email:
                raise drf_serializers.ValidationError(
                    {'organization': 'Organization contact email is required before creating a contract.'}
                )
            logger.info(
                "Contract created id=%s type=%s org_id=%s org_name=%s",
                contract.id,
                contract.type,
                getattr(org, 'id', None),
                getattr(org, 'name', None),
            )
            app_base = getattr(settings, 'FRONTEND_URL', None) or getattr(
                settings, 'NEXT_PUBLIC_APP_URL', None
            ) or 'http://localhost:3000'
            onboarding_target = f"/onboarding/institution?organization={org.id}&contract={contract.id}"
            onboarding_link = f"{app_base}{onboarding_target}"
            if contract.type == 'institution':
                subject = f"OCH Institutional Contract Pack - {org.name}"
                body = (
                    f"Hello {org.contact_person_name or org.name},\n\n"
                    f"Your institutional contract has been created for OCH.\n\n"
                    f"Contract information:\n"
                    f"- Organization: {org.name}\n"
                    f"- Contract type: {contract.type}\n"
                    f"- Start date: {contract.start_date}\n"
                    f"- End date: {contract.end_date}\n"
                    f"- Minimum commitment: 12 months\n\n"
                    f"Onboarding link:\n{onboarding_link}\n\n"
                    "From this onboarding flow your institution can:\n"
                    "1) Accept terms and conditions\n"
                    "2) Choose preferred tier and billing cycle\n"
                    "3) Receive invoice and complete payment\n"
                    "4) Join organization portal and add students\n\n"
                    "Institution licensing model:\n"
                    "University and educational institution licensing follows a contract-based model "
                    "with mandatory 12-month minimum commitment, per-student licensing pricing, and "
                    "custom billing cycles. Institutions can also purchase dedicated cohort seats in "
                    "bulk through their contract.\n\n"
                    "Contract requirements and minimums:\n"
                    "- Minimum contract duration: 12 months required\n"
                    "- Early termination: 60-day notice; remaining balance prorated to termination date\n"
                    "- Automatic renewal: additional 12-month terms unless 60-day non-renewal notice\n"
                    "- Renewal pricing: annual review and updated quote where applicable\n\n"
                    "Per-student licensing tiers:\n"
                    "- 1-50 students: $15/student/month ($180/year)\n"
                    "- 51-200 students: $12/student/month ($144/year)\n"
                    "- 201-500 students: $9/student/month ($108/year)\n"
                    "- 500+ students: $7/student/month ($84/year)\n\n"
                    "Invoice generation and billing cycles:\n"
                    "- Monthly billing: net 30\n"
                    "- Quarterly billing: net 30\n"
                    "- Annual billing: net 30, often includes 2-3% annual discount\n"
                    "- Seat count adjustments: prorated and reflected in next invoice\n"
                    "- Invoice details include institution name, contract period, seat count, "
                    "per-student rate, total amount, tax, and due date\n\n"
                    "Regards,\n"
                    "OCH Finance Team"
                )
            else:
                subject = f"OCH Employer Contract Pack - {org.name}"
                body = (
                    f"Hello {org.contact_person_name or org.name},\n\n"
                    f"Your employer contract has been created for OCH.\n\n"
                    f"Contract information:\n"
                    f"- Organization: {org.name}\n"
                    f"- Contract type: {contract.type}\n"
                    f"- Start date: {contract.start_date}\n"
                    f"- End date: {contract.end_date}\n"
                    f"- Minimum commitment: 12 months\n\n"
                    f"Onboarding link:\n{onboarding_link}\n\n"
                    "Employers pay a monthly retainer fee to access the talent pipeline and recruit from OCH graduates. "
                    "Employers can also sponsor private cohorts for their employees, creating a multi-dimensional partnership.\n\n"
                    "2.3.1 Monthly Retainer Fee Tiers\n"
                    "Employer access is structured around monthly retainer tiers with candidate access guarantees:\n"
                    "Tier | Monthly Retainer | Candidate Access/Quarter | Key Features\n"
                    "Starter | $500/month | Up to 5 candidates/quarter | Basic talent pipeline access, standard matching\n"
                    "Growth | $1,500/month | Up to 15 candidates/quarter | Priority matching, dedicated account manager\n"
                    "Enterprise | $3,500/month | Unlimited pipeline | VIP matching, custom reports, exclusive pipeline\n\n"
                    "2.3.2 Per-Candidate Successful Placement Fees\n"
                    "- Placement Fee Trigger: Fee charged when candidate successfully completes interview process, accepts offer, and completes first 90 days of employment\n"
                    "- Starter Tier Fee: $2,000 per successful placement\n"
                    "- Growth Tier Fee: $1,500 per successful placement (lower fee recognizes higher retainer)\n"
                    "- Enterprise Tier Fee: $1,000 per successful placement (discount reflects volume commitment)\n"
                    "- Fee Billing: Placement fees invoiced monthly; separate line item from retainer\n"
                    "- Fee Cap: Monthly placement fees capped at 2x monthly retainer\n\n"
                    "2.3.3 Contract Tiers Comparison\n"
                    "Feature | Starter | Growth | Enterprise | Custom\n"
                    "Monthly Retainer | $500 | $1,500 | $3,500 | Negotiated\n"
                    "Candidates/Quarter | 5 | 15 | Unlimited | Unlimited\n"
                    "Per-Placement Fee | $2,000 | $1,500 | $1,000 | Negotiated\n"
                    "Dedicated Account Manager | No | Yes | Yes | Yes\n\n"
                    "2.3.4 Talent Pipeline SLA and Quality Guarantees\n"
                    "- Time-to-Shortlist SLA: first candidate shortlist within 5 business days\n"
                    "- Candidate Quality Score: minimum 75%+ quality score on skills assessment\n"
                    "- Track Completion Level: minimum tier level appropriate to role\n"
                    "- Mission Score Baseline: minimum mission completion score (70%+)\n"
                    "- Portfolio Quality: verified portfolio before candidate presentation\n"
                    "- Replacement Guarantee: replacement if candidate leaves within 60 days\n"
                    "- Placement Success Rate Target: >70% target; <60% triggers alignment discussion\n\n"
                    "2.3.5 Contract Lifecycle Stages\n"
                    "- Proposal\n- Negotiation\n- Signed\n- Active\n- Renewal/Termination\n\n"
                    "2.3.6 Marketplace Integration and Priority Access\n"
                    "- Talent matching engine\n"
                    "- Priority matching queue for contract employers\n"
                    "- Candidate presentation priority\n"
                    "- Optional exclusivity window (48-72 hours) for premium tiers\n"
                    "- Analytics visibility on recommendations and outcomes\n\n"
                    "2.3.7 Performance-Based Pricing Adjustments\n"
                    "- Annual performance review at renewal\n"
                    "- Success Rate = successful placements / candidates presented\n"
                    "- >90% success: 10% renewal retainer discount\n"
                    "- <60% success: matching analysis and improvement plan\n\n"
                    "2.3.8 Exclusivity Clauses and Premium Pricing\n"
                    "- Optional exclusivity with 50% retainer premium\n"
                    "- Typical exclusivity duration 3-6 months\n"
                    "- Candidate replacement within exclusivity pool where applicable\n"
                    "- Exclusivity can be offered to multiple non-competing employers\n\n"
                    "2.3.9 Talent Replacement Guarantee\n"
                    "- Standard 60-day guarantee window\n"
                    "- Replacement shortlist within 10 business days\n"
                    "- Enterprise tier receives 90-day guarantee\n"
                    "- Exclusions apply for employer-initiated performance terminations\n"
                    "- Up to 3 replacements before partnership review\n\n"
                    "Regards,\n"
                    "OCH Finance Team"
                )
            try:
                logger.info(
                    "Sending contract email id=%s to=%s host=%s port=%s ssl=%s tls=%s backend=%s",
                    contract.id,
                    org.contact_email,
                    getattr(settings, 'EMAIL_HOST', None),
                    getattr(settings, 'EMAIL_PORT', None),
                    getattr(settings, 'EMAIL_USE_SSL', None),
                    getattr(settings, 'EMAIL_USE_TLS', None),
                    getattr(settings, 'EMAIL_BACKEND', None),
                )
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@och.local'),
                    recipient_list=[org.contact_email],
                    fail_silently=False,
                )
                logger.info("Contract email sent id=%s to=%s", contract.id, org.contact_email)
            except Exception as exc:
                logger.exception("Contract email failed id=%s to=%s", contract.id, org.contact_email)
                raise drf_serializers.ValidationError(
                    {'email': f'Contract email could not be sent: {exc}'}
                )
            email_sent = True

            # Best-effort SMS notification to billing contact phone.
            sms_sent = False
            if getattr(org, 'contact_phone', None):
                sms_message = (
                    f"OCH contract created for {org.name}. "
                    f"Type: {contract.type}. Start: {contract.start_date}. End: {contract.end_date}. "
                    f"Onboarding: {onboarding_link}"
                )
                logger.info(
                    "Sending contract SMS id=%s to=%s provider=%s",
                    contract.id,
                    org.contact_phone,
                    getattr(settings, 'SMS_PROVIDER', 'textsms'),
                )
                sms_sent = send_sms_message(org.contact_phone, sms_message)
                if not sms_sent:
                    logger.warning(
                        "Contract SMS not sent for org_id=%s phone=%s. Check SMS provider credentials.",
                        org.id,
                        org.contact_phone,
                    )
                else:
                    logger.info("Contract SMS sent id=%s to=%s", contract.id, org.contact_phone)
            self._notification_status = {
                'email_sent': email_sent,
                'sms_sent': sms_sent,
                'email_recipient': org.contact_email,
                'sms_recipient': getattr(org, 'contact_phone', None),
                'sms_provider': getattr(settings, 'SMS_PROVIDER', 'textsms'),
            }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        payload = dict(serializer.data)
        payload['notifications'] = getattr(
            self,
            '_notification_status',
            {
                'email_sent': False,
                'sms_sent': False,
                'email_recipient': None,
                'sms_recipient': None,
                'sms_provider': getattr(settings, 'SMS_PROVIDER', 'textsms'),
            },
        )
        return Response(payload, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path='institution-onboarding-preview')
    def institution_onboarding_preview(self, request):
        org_id = request.query_params.get('organization')
        contract_id = request.query_params.get('contract')
        if not org_id or not contract_id:
            return Response(
                {'detail': 'organization and contract are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            contract = Contract.objects.select_related('organization').get(
                id=contract_id,
                organization_id=org_id,
                type='institution',
            )
        except Contract.DoesNotExist:
            return Response({'detail': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                'organization': {
                    'id': contract.organization.id,
                    'name': contract.organization.name,
                    'contact_email': contract.organization.contact_email,
                    'contact_person_name': contract.organization.contact_person_name,
                },
                'contract': {
                    'id': str(contract.id),
                    'type': contract.type,
                    'status': contract.status,
                    'start_date': contract.start_date,
                    'end_date': contract.end_date,
                    'auto_renew': contract.auto_renew,
                    'renewal_notice_days': contract.renewal_notice_days,
                },
            }
        )

    @action(detail=False, methods=['post'], url_path='institution-onboarding-complete')
    def institution_onboarding_complete(self, request):
        org_id = request.data.get('organization')
        contract_id = request.data.get('contract')
        email = (request.data.get('email') or '').strip().lower()
        first_name = (request.data.get('first_name') or '').strip()
        last_name = (request.data.get('last_name') or '').strip()
        password = request.data.get('password') or ''
        terms_accepted = bool(request.data.get('terms_accepted'))
        if not org_id or not contract_id:
            return Response(
                {'detail': 'organization and contract are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(password) < 8:
            return Response(
                {'detail': 'Password must be at least 8 characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not email:
            return Response(
                {'detail': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not terms_accepted:
            return Response(
                {'detail': 'You must accept the Terms and Conditions.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            contract = Contract.objects.select_related('organization').get(
                id=contract_id,
                organization_id=org_id,
                type='institution',
            )
        except Contract.DoesNotExist:
            return Response({'detail': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

        org = contract.organization
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first_name or (org.contact_person_name or org.name),
                    'last_name': last_name,
                    'email_verified': True,
                    'account_status': 'active',
                    'org_id': org,
                },
            )
            if not created:
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                if getattr(user, 'org_id_id', None) is None:
                    user.org_id = org
                if getattr(user, 'account_status', None) != 'active':
                    user.account_status = 'active'
                user.email_verified = True
            user.set_password(password)
            user.save()

            OrganizationMember.objects.get_or_create(
                organization=org,
                user=user,
                defaults={'role': 'admin'},
            )
            role = (
                Role.objects.filter(name='institution_admin').first()
                or Role.objects.filter(name='organization_admin').first()
            )
            if role is None:
                role = Role.objects.create(
                    name='institution_admin',
                    display_name='Institution Admin',
                    description='Admin access for institution/organization portal users',
                    is_system_role=True,
                )

            UserRole.objects.get_or_create(
                user=user,
                role=role,
                scope='org',
                scope_ref=None,
                org_id=org,
                defaults={'assigned_by': None, 'is_active': True},
            )

        return Response(
            {
                'success': True,
                'email': email,
                'organization': org.id,
                'contract': str(contract.id),
                'next': f"/dashboard/institution?organization={org.id}&contract={contract.id}",
            }
        )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active contracts."""
        active_contracts = self.get_queryset().filter(
            status='active',
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        )
        serializer = self.get_serializer(active_contracts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get contracts expiring in next 30 days."""
        thirty_days = timezone.now().date() + timedelta(days=30)
        expiring = self.get_queryset().filter(
            status='active',
            end_date__lte=thirty_days,
            end_date__gte=timezone.now().date()
        )
        serializer = self.get_serializer(expiring, many=True)
        return Response(serializer.data)


class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    # Default to admin-only; see get_permissions for read override
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        """
        Allow any authenticated user to READ tax rates,
        but restrict CREATE/UPDATE/DELETE to admins.
        """
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Get tax rate by country and region."""
        country = request.query_params.get('country')
        region = request.query_params.get('region', '')
        tax_type = request.query_params.get('type', 'VAT')
        
        if not country:
            return Response(
                {'error': 'Country parameter required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rate = TaxRate.get_tax_rate(country, region, tax_type)
        return Response({'rate': rate, 'country': country, 'region': region})


class MentorPayoutViewSet(viewsets.ModelViewSet):
    serializer_class = MentorPayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def get_queryset(self):
        qs = MentorPayout.objects.select_related('mentor', 'cohort')
        if self.request.user.is_staff:
            qs = qs.all()
        else:
            qs = qs.filter(mentor=self.request.user)
        cohort_id = self.request.query_params.get('cohort_id')
        if cohort_id:
            qs = qs.filter(cohort_id=cohort_id)
        mode = self.request.query_params.get('compensation_mode')
        if mode in ('paid', 'volunteer'):
            qs = qs.filter(compensation_mode=mode)
        return qs
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve mentor payout (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        payout = self.get_object()
        payout.status = 'approved'
        payout.save()
        
        return Response({'message': 'Payout approved'})
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark payout as paid (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        payout = self.get_object()
        payout.status = 'paid'
        payout.save()
        
        return Response({'message': 'Payout marked as paid'})


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user_has_finance_role(user):
            return Invoice.objects.all()
        
        # Users can see their own invoices and organization invoices
        user_orgs = user.organizations.all()
        return Invoice.objects.filter(
            Q(user=user) | Q(organization__in=user_orgs)
        )
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid."""
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.paid_date = timezone.now()
        invoice.save()
        
        return Response({'message': 'Invoice marked as paid'})


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user_has_finance_role(user):
            return Payment.objects.all()
        
        # Users can see payments for their invoices
        user_orgs = user.organizations.all()
        return Payment.objects.filter(
            Q(invoice__user=user) | 
            Q(invoice__organization__in=user_orgs)
        )


class FinancialDashboardView(APIView):
    """Financial dashboard with key metrics."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        range_key = (request.query_params.get('range') or '30d').lower()
        range_days_map = {
            '7d': 7,
            '30d': 30,
            '90d': 90,
            '1y': 365,
        }
        days = range_days_map.get(range_key, 30)
        window_start = timezone.now() - timedelta(days=days)
        
        # Get user's wallet
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # Get user's credits
        active_credits = Credit.objects.filter(
            user=user,
            remaining__gt=0
        ).aggregate(
            total=Sum('remaining')
        )['total'] or Decimal('0')
        
        # Get user's invoices
        user_orgs = user.organizations.all()
        invoices = Invoice.objects.filter(
            Q(user=user) | Q(organization__in=user_orgs)
        )
        invoices_in_window = invoices.filter(created_at__gte=window_start)
        
        pending_invoices = invoices_in_window.filter(status__in=['draft', 'sent']).count()
        overdue_invoices = invoices_in_window.filter(
            status='sent',
            due_date__lt=timezone.now()
        ).count()
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            wallet=wallet
        ).filter(
            created_at__gte=window_start
        )[:10]

        subscription_payload = None
        try:
            us = UserSubscription.objects.select_related('plan').get(user=user)
            plan = us.plan
            cat = plan.catalog or {}
            display = (cat.get('display_name') or '').strip() or plan.name.replace('_', ' ').title()
            subscription_payload = {
                'plan_name': plan.name,
                'plan_display_name': display,
                'tier': plan.tier,
                'status': us.status,
                'billing_interval': getattr(us, 'billing_interval', None) or plan.billing_interval,
                'current_period_start': us.current_period_start.isoformat() if us.current_period_start else None,
                'current_period_end': us.current_period_end.isoformat() if us.current_period_end else None,
                'price_monthly_kes': float(plan.price_monthly or 0),
            }
        except UserSubscription.DoesNotExist:
            pass

        return Response({
            'wallet': {
                'balance': wallet.balance,
                'currency': wallet.currency,
                'last_transaction_at': wallet.last_transaction_at
            },
            'credits': {
                'active_balance': active_credits,
                'total_credits': Credit.objects.filter(user=user).count()
            },
            'invoices': {
                'pending': pending_invoices,
                'overdue': overdue_invoices,
                'total': invoices_in_window.count()
            },
            'recent_transactions': TransactionSerializer(
                recent_transactions, many=True
            ).data,
            'subscription': subscription_payload,
            'range': range_key,
        })