"""
Finance views for wallet, credits, contracts, and financial management.
"""
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Sum
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
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
        if self.request.user.is_staff:
            return Contract.objects.all()
        # Users can only see contracts for their organizations
        user_orgs = self.request.user.organizations.all()
        return Contract.objects.filter(organization__in=user_orgs)
    
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
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return MentorPayout.objects.all()
        return MentorPayout.objects.filter(mentor=self.request.user)
    
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
        if self.request.user.is_staff:
            return Invoice.objects.all()
        
        # Users can see their own invoices and organization invoices
        user_orgs = self.request.user.organizations.all()
        return Invoice.objects.filter(
            Q(user=self.request.user) | Q(organization__in=user_orgs)
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
        if self.request.user.is_staff:
            return Payment.objects.all()
        
        # Users can see payments for their invoices
        user_orgs = self.request.user.organizations.all()
        return Payment.objects.filter(
            Q(invoice__user=self.request.user) | 
            Q(invoice__organization__in=user_orgs)
        )


class FinancialDashboardView(APIView):
    """Financial dashboard with key metrics."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
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
        
        pending_invoices = invoices.filter(status__in=['draft', 'sent']).count()
        overdue_invoices = invoices.filter(
            status='sent',
            due_date__lt=timezone.now()
        ).count()
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            wallet=wallet
        )[:10]
        
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
                'total': invoices.count()
            },
            'recent_transactions': TransactionSerializer(
                recent_transactions, many=True
            ).data
        })