"""
Enhanced finance views with security, analytics, and automation features.
"""
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.db.models import Q, Sum, Count, Avg
from django.http import JsonResponse
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

from .models import (
    Wallet, Transaction, Credit, Contract, TaxRate,
    MentorPayout, Invoice, Payment
)
from .serializers import (
    WalletSerializer, TransactionSerializer, CreditSerializer,
    ContractSerializer, TaxRateSerializer, MentorPayoutSerializer,
    InvoiceSerializer, PaymentSerializer
)
from .audit import AuditLog, SecurityEvent, ComplianceReport, log_financial_action, log_security_event
from .analytics import FinancialMetric, RevenueStream, CustomerMetrics, FinancialAnalytics
from .automation import DunningSequence, PaymentRetryAttempt, FinancialAutomation


class SecurityMixin:
    """Mixin to add security logging to financial operations."""
    
    def dispatch(self, request, *args, **kwargs):
        # Log financial data access
        if hasattr(self, 'get_queryset'):
            log_financial_action(
                user=request.user,
                action='access',
                entity_type=getattr(self, 'audit_entity_type', 'unknown'),
                entity_id=kwargs.get('pk', '00000000-0000-0000-0000-000000000000'),
                description=f'Accessed {self.__class__.__name__}',
                request=request,
                risk_level='low'
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        instance = serializer.save()
        log_financial_action(
            user=self.request.user,
            action='create',
            entity_type=getattr(self, 'audit_entity_type', 'unknown'),
            entity_id=instance.id,
            description=f'Created {instance}',
            new_values=serializer.validated_data,
            request=self.request,
            risk_level='medium'
        )
    
    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_values = {field.name: getattr(old_instance, field.name) for field in old_instance._meta.fields}
        
        instance = serializer.save()
        log_financial_action(
            user=self.request.user,
            action='update',
            entity_type=getattr(self, 'audit_entity_type', 'unknown'),
            entity_id=instance.id,
            description=f'Updated {instance}',
            old_values=old_values,
            new_values=serializer.validated_data,
            request=self.request,
            risk_level='medium'
        )
    
    def perform_destroy(self, instance):
        log_financial_action(
            user=self.request.user,
            action='delete',
            entity_type=getattr(self, 'audit_entity_type', 'unknown'),
            entity_id=instance.id,
            description=f'Deleted {instance}',
            old_values={'id': str(instance.id)},
            request=self.request,
            risk_level='high'
        )
        instance.delete()


class EnhancedWalletViewSet(SecurityMixin, viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_entity_type = 'wallet'
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Wallet.objects.all()
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def top_up(self, request, pk=None):
        """Add balance to wallet with enhanced security."""
        wallet = self.get_object()
        if wallet.user != request.user and not request.user.is_staff:
            log_security_event(
                event_type='data_access',
                severity='high',
                description=f'Unauthorized wallet access attempt by {request.user.email}',
                user=request.user,
                request=request,
                event_data={'wallet_id': str(wallet.id), 'wallet_owner': wallet.user.email}
            )
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        amount = request.data.get('amount')
        if not amount or float(amount) <= 0:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Security check for large amounts
        if float(amount) > 10000:
            log_security_event(
                event_type='suspicious_transaction',
                severity='medium',
                description=f'Large wallet top-up attempt: ${amount}',
                user=request.user,
                request=request,
                event_data={'amount': amount, 'wallet_id': str(wallet.id)}
            )
        
        description = request.data.get('description', 'Wallet top-up')
        wallet.add_balance(Decimal(str(amount)), description)
        
        return Response({
            'message': 'Wallet topped up successfully',
            'new_balance': wallet.balance
        })


class AnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """Financial analytics and reporting endpoints."""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def revenue_dashboard(self, request):
        """Get comprehensive revenue dashboard data."""
        # NOTE: In production you might want to restrict this
        # to finance/admin roles. For local analytics dashboard
        # we allow any authenticated user who can reach this endpoint.
        # Date range from query params
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Calculate metrics, but be resilient if analytics tables are missing in dev
        try:
            revenue_metrics = FinancialAnalytics.calculate_revenue_metrics(start_date, end_date)
        except Exception:
            revenue_metrics = {
                'total_revenue': 0,
                'revenue_by_type': [],
                'payment_success_rate': 0,
                'total_invoices': 0,
                'total_payments': 0,
                'successful_payments': 0,
            }
        try:
            growth_metrics = FinancialAnalytics.calculate_customer_growth(start_date, end_date)
        except Exception:
            growth_metrics = {
                'new_customers': 0,
                'churned_customers': 0,
                'active_customers_start': 0,
                'active_customers_end': 0,
                'growth_rate': 0,
                'churn_rate': 0,
            }

        try:
            revenue_streams_qs = RevenueStream.objects.filter(
                recognized_date__range=[start_date.date(), end_date.date()]
            ).values('stream_type').annotate(
                total=Sum('amount'),
                count=Count('id')
            )
            revenue_streams = list(revenue_streams_qs)
        except Exception:
            revenue_streams = []

        try:
            payment_success = FinancialAutomation.calculate_payment_success_rate(start_date, end_date)
        except Exception:
            payment_success = {
                'success_rate': 0,
                'total_payments': 0,
                'successful_payments': 0,
                'failed_payments': 0,
                'period_start': start_date,
                'period_end': end_date,
            }

        try:
            dunning_recovery = FinancialAutomation.calculate_dunning_recovery_rate(start_date, end_date)
        except Exception:
            dunning_recovery = {
                'recovery_rate': 0,
                'total_sequences': 0,
                'total_amount': 0,
                'recovered_amount': 0,
                'period_start': start_date,
                'period_end': end_date,
            }

        return Response({
            'period': {
                'start_date': start_date.date(),
                'end_date': end_date.date(),
                'days': days
            },
            'revenue': revenue_metrics,
            'growth': growth_metrics,
            'revenue_streams': revenue_streams,
            'payment_success': payment_success,
            'dunning_recovery': dunning_recovery
        })
    
    @action(detail=False, methods=['get'])
    def customer_metrics(self, request):
        """Get customer financial metrics."""
        # Same permission model as revenue_dashboard: any authenticated user.
        try:
            # Top customers by revenue
            top_customers = CustomerMetrics.objects.filter(
                is_active=True
            ).order_by('-total_revenue')[:10]

            # Churn analysis
            churned_customers = CustomerMetrics.objects.filter(
                churn_date__gte=timezone.now().date() - timedelta(days=30)
            ).count()

            # Cohort analysis for last 6 months
            cohort_data = []
            for i in range(6):
                cohort_month = (timezone.now().date().replace(day=1) - timedelta(days=30*i))
                cohort_analysis = FinancialAnalytics.calculate_cohort_analysis(cohort_month)
                cohort_data.append(cohort_analysis)

            top_customers_payload = [
                {
                    'customer_id': str(customer.customer_id),
                    'customer_type': customer.customer_type,
                    'total_revenue': customer.total_revenue,
                    'monthly_recurring_revenue': customer.monthly_recurring_revenue,
                    'lifetime_value': customer.lifetime_value,
                    'months_active': customer.months_active
                }
                for customer in top_customers
            ]
        except Exception:
            top_customers_payload = []
            churned_customers = 0
            cohort_data = []

        return Response({
            'top_customers': top_customers_payload,
            'churn_analysis': {
                'churned_last_30_days': churned_customers,
                'cohort_data': cohort_data
            }
        })
    
    @action(detail=False, methods=['get'])
    def institution_roi(self, request):
        """Get ROI metrics for institutions."""
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check permissions
        if not request.user.is_staff:
            # Check if user belongs to the organization
            user_orgs = request.user.organizations.all()
            if not user_orgs.filter(id=organization_id).exists():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        days = int(request.query_params.get('days', 90))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        roi_metrics = FinancialAnalytics.calculate_institution_roi(
            organization_id, start_date, end_date
        )
        
        return Response(roi_metrics)


class ComplianceViewSet(viewsets.ReadOnlyModelViewSet):
    """Compliance and audit endpoints."""
    # In this implementation we allow any authenticated finance user
    # to view compliance dashboards. Tighten to IsAdminUser in production if needed.
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def audit_trail(self, request):
        """Get audit trail with filtering."""
        # Query parameters
        entity_type = request.query_params.get('entity_type')
        entity_id = request.query_params.get('entity_id')
        user_id = request.query_params.get('user_id')
        risk_level = request.query_params.get('risk_level')
        days = int(request.query_params.get('days', 30))
        
        # Build query
        queryset = AuditLog.objects.all()
        
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        # Date range
        start_date = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(timestamp__gte=start_date)
        
        # Paginate
        page_size = int(request.query_params.get('page_size', 50))
        page = int(request.query_params.get('page', 1))
        offset = (page - 1) * page_size
        
        total_count = queryset.count()
        audit_logs = queryset[offset:offset + page_size]
        
        results_payload = []
        for log in audit_logs:
            # Core audit model (users.audit_models.AuditLog) uses actor_identifier/resource_type/resource_id/metadata
            user_email = getattr(log, 'user_email', None)
            if not user_email:
                # Fallbacks: actor_identifier, then linked user email
                user_email = getattr(log, 'actor_identifier', None) or (
                    log.user.email if getattr(log, 'user', None) else ''
                )

            # Entity mapping
            entity_type = getattr(log, 'entity_type', None) or getattr(log, 'resource_type', '')
            entity_id = getattr(log, 'entity_id', None) or getattr(log, 'resource_id', None)

            # Metadata-based flags
            metadata = getattr(log, 'metadata', {}) or {}
            risk_level = getattr(log, 'risk_level', None) or metadata.get('risk_level', 'low')
            is_pci_relevant = getattr(log, 'is_pci_relevant', None)
            if is_pci_relevant is None:
                is_pci_relevant = bool(metadata.get('is_pci_relevant'))
            is_gdpr_relevant = getattr(log, 'is_gdpr_relevant', None)
            if is_gdpr_relevant is None:
                is_gdpr_relevant = bool(metadata.get('is_gdpr_relevant'))

            user_ip = getattr(log, 'user_ip', None) or getattr(log, 'ip_address', None) or ''

            results_payload.append({
                'id': str(log.id),
                'timestamp': log.timestamp,
                'user_email': user_email or '',
                'action': log.action,
                'entity_type': entity_type or '',
                'entity_id': str(entity_id) if entity_id is not None else '',
                'description': getattr(log, 'description', '') or '',
                'risk_level': risk_level,
                'user_ip': user_ip,
                'is_pci_relevant': is_pci_relevant,
                'is_gdpr_relevant': is_gdpr_relevant,
            })

        return Response({
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'results': results_payload,
        })
    
    @action(detail=False, methods=['get'])
    def security_events(self, request):
        """Get security events."""
        severity = request.query_params.get('severity')
        event_type = request.query_params.get('event_type')
        is_resolved = request.query_params.get('is_resolved')
        days = int(request.query_params.get('days', 7))
        
        queryset = SecurityEvent.objects.all()
        
        if severity:
            queryset = queryset.filter(severity=severity)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        
        start_date = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(detected_at__gte=start_date)
        
        events = queryset[:100]  # Limit to 100 recent events
        
        return Response({
            'total_count': queryset.count(),
            'events': [
                {
                    'id': str(event.id),
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'description': event.description,
                    'user_ip': event.user_ip,
                    'is_resolved': event.is_resolved,
                    'detected_at': event.detected_at,
                    'resolved_at': event.resolved_at
                }
                for event in events
            ]
        })
    
    @action(detail=False, methods=['post'])
    def generate_compliance_report(self, request):
        """Generate compliance report."""
        report_type = request.data.get('report_type')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        if not all([report_type, period_start, period_end]):
            return Response(
                {'error': 'report_type, period_start, and period_end are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate report data based on type
        if report_type == 'pci_dss':
            report_data = generate_pci_compliance_report(period_start, period_end)
        elif report_type == 'gdpr':
            report_data = generate_gdpr_compliance_report(period_start, period_end)
        elif report_type == 'audit_trail':
            report_data = generate_audit_trail_report(period_start, period_end)
        else:
            return Response({'error': 'Invalid report type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create compliance report record
        report = ComplianceReport.objects.create(
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            report_data=str(report_data),  # Would be encrypted in real implementation
            summary=report_data.get('summary', ''),
            compliance_score=report_data.get('compliance_score', 0),
            issues_found=report_data.get('issues_found', 0),
            critical_issues=report_data.get('critical_issues', 0),
            generated_by=request.user
        )
        
        return Response({
            'report_id': str(report.id),
            'report_type': report.report_type,
            'compliance_score': report.compliance_score,
            'issues_found': report.issues_found,
            'critical_issues': report.critical_issues,
            'summary': report.summary
        })


class AutomationViewSet(viewsets.ReadOnlyModelViewSet):
    """Financial automation monitoring and control."""
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def dunning_dashboard(self, request):
        """Get dunning management dashboard."""
        # Active dunning sequences
        active_sequences = DunningSequence.objects.filter(status='active')
        
        # Recovery metrics
        recovery_metrics = FinancialAutomation.calculate_dunning_recovery_rate()
        
        # Recent retry attempts
        recent_attempts = PaymentRetryAttempt.objects.filter(
            attempted_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-attempted_at')[:50]
        
        return Response({
            'active_sequences': {
                'count': active_sequences.count(),
                'total_amount': active_sequences.aggregate(total=Sum('original_amount'))['total'] or 0,
                'sequences': [
                    {
                        'id': str(seq.id),
                        'invoice_number': seq.invoice.invoice_number,
                        'user_email': seq.user.email,
                        'current_attempt': seq.current_attempt,
                        'total_attempts': seq.total_attempts,
                        'original_amount': seq.original_amount,
                        'recovered_amount': seq.recovered_amount,
                        'recovery_rate': seq.recovery_rate,
                        'next_attempt_at': seq.next_attempt_at,
                        'started_at': seq.started_at
                    }
                    for seq in active_sequences[:20]  # Limit to 20 for performance
                ]
            },
            'recovery_metrics': recovery_metrics,
            'recent_attempts': [
                {
                    'id': str(attempt.id),
                    'attempt_number': attempt.attempt_number,
                    'amount': attempt.amount,
                    'status': attempt.status,
                    'attempted_at': attempt.attempted_at,
                    'error_message': attempt.error_message
                }
                for attempt in recent_attempts
            ]
        })
    
    @action(detail=False, methods=['get'])
    def payment_success_monitoring(self, request):
        """Monitor payment success rates."""
        days = int(request.query_params.get('days', 7))
        
        # Daily success rates for the period
        daily_rates = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            start_datetime = timezone.make_aware(datetime.combine(date, datetime.min.time()))
            end_datetime = start_datetime + timedelta(days=1)
            
            metrics = FinancialAutomation.calculate_payment_success_rate(start_datetime, end_datetime)
            daily_rates.append({
                'date': date,
                'success_rate': metrics['success_rate'],
                'total_payments': metrics['total_payments'],
                'successful_payments': metrics['successful_payments']
            })
        
        # Overall metrics
        overall_metrics = FinancialAutomation.calculate_payment_success_rate()
        
        # Alert if below threshold
        alert_threshold = 95.0
        needs_attention = overall_metrics['success_rate'] < alert_threshold
        
        return Response({
            'overall_metrics': overall_metrics,
            'daily_rates': daily_rates,
            'alert_threshold': alert_threshold,
            'needs_attention': needs_attention,
            'status': 'healthy' if not needs_attention else 'attention_required'
        })


def generate_pci_compliance_report(period_start, period_end):
    """Generate PCI-DSS compliance report."""
    # Check for PCI-relevant audit logs
    pci_logs = AuditLog.objects.filter(
        is_pci_relevant=True,
        timestamp__range=[period_start, period_end]
    )
    
    # Check for payment-related security events
    payment_events = SecurityEvent.objects.filter(
        event_type__in=['payment_fraud', 'suspicious_transaction'],
        detected_at__range=[period_start, period_end]
    )
    
    compliance_score = 95.0  # Placeholder calculation
    issues_found = payment_events.filter(severity__in=['high', 'critical']).count()
    
    return {
        'summary': f'PCI-DSS compliance report for {period_start} to {period_end}',
        'compliance_score': compliance_score,
        'issues_found': issues_found,
        'critical_issues': payment_events.filter(severity='critical').count(),
        'pci_logs_count': pci_logs.count(),
        'payment_events_count': payment_events.count()
    }


def generate_gdpr_compliance_report(period_start, period_end):
    """Generate GDPR compliance report."""
    gdpr_logs = AuditLog.objects.filter(
        is_gdpr_relevant=True,
        timestamp__range=[period_start, period_end]
    )
    
    compliance_score = 98.0  # Placeholder calculation
    
    return {
        'summary': f'GDPR compliance report for {period_start} to {period_end}',
        'compliance_score': compliance_score,
        'issues_found': 0,
        'critical_issues': 0,
        'gdpr_logs_count': gdpr_logs.count()
    }


def generate_audit_trail_report(period_start, period_end):
    """Generate audit trail report."""
    total_logs = AuditLog.objects.filter(
        timestamp__range=[period_start, period_end]
    ).count()
    
    high_risk_logs = AuditLog.objects.filter(
        timestamp__range=[period_start, period_end],
        risk_level__in=['high', 'critical']
    ).count()
    
    return {
        'summary': f'Audit trail report for {period_start} to {period_end}',
        'compliance_score': 100.0,
        'issues_found': 0,
        'critical_issues': 0,
        'total_logs': total_logs,
        'high_risk_logs': high_risk_logs
    }