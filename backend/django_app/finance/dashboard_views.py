"""
Financial Dashboard Views - Complete Implementation
API endpoints for all dashboard types and financial operations
"""

import logging
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .dashboard_models import *
from .models import *
from .serializers import *
from .services import *

logger = logging.getLogger(__name__)

class FinancialDashboardViewSet(viewsets.ModelViewSet):
    """ViewSet for financial dashboard management"""
    serializer_class = FinancialDashboardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FinancialDashboard.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def admin_dashboard(self, request):
        """Get admin financial dashboard data"""
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'},
                          status=status.HTTP_403_FORBIDDEN)

        today = timezone.now().date()
        last_month = today - timedelta(days=30)

        # Revenue metrics
        analytics = FinancialAnalyticsService()
        mrr = analytics.calculate_mrr()
        arr = analytics.calculate_arr()
        revenue_breakdown = analytics.generate_revenue_breakdown(last_month, today)

        # KPIs
        kpis = FinancialKPI.objects.all()
        kpi_data = []
        for kpi in kpis:
            kpi_data.append({
                'name': kpi.name,
                'category': kpi.category,
                'current_value': float(kpi.current_value),
                'target_value': float(kpi.target_value) if kpi.target_value else None,
                'growth_rate': float(kpi.growth_rate),
                'target_achievement': float(kpi.target_achievement),
                'unit': kpi.unit
            })

        # Active alerts
        alerts = FinancialAlert.objects.filter(status='active').order_by('-created_at')[:10]
        alert_data = []
        for alert in alerts:
            alert_data.append({
                'id': str(alert.id),
                'type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'description': alert.description,
                'created_at': alert.created_at
            })

        # Cash flow projection
        cash_flow = CashFlowProjection.objects.filter(
            projection_type='monthly'
        ).order_by('-created_at').first()

        cash_flow_data = None
        if cash_flow:
            cash_flow_data = {
                'total_revenue': float(cash_flow.total_revenue),
                'total_expenses': float(cash_flow.total_expenses),
                'net_cash_flow': float(cash_flow.net_cash_flow),
                'confidence_score': float(cash_flow.confidence_score)
            }

        return Response({
            'revenue_metrics': {
                'mrr': float(mrr),
                'arr': float(arr),
                'breakdown': revenue_breakdown
            },
            'kpis': kpi_data,
            'alerts': alert_data,
            'cash_flow': cash_flow_data,
            'last_updated': timezone.now()
        })

    @action(detail=False, methods=['get'])
    def student_dashboard(self, request):
        """Get student financial dashboard data"""
        user = request.user

        # Subscription info
        subscription = getattr(user, 'subscription', None)
        subscription_data = None
        if subscription:
            subscription_data = {
                'plan': subscription.plan.name,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'enhanced_access_expires_at': subscription.enhanced_access_expires_at
            }

        # Wallet info
        wallet = getattr(user, 'wallet', None)
        wallet_data = None
        if wallet:
            wallet_data = {
                'balance': float(wallet.balance),
                'currency': wallet.currency,
                'last_transaction_at': wallet.last_transaction_at
            }

            # Recent transactions
            recent_transactions = wallet.transactions.order_by('-created_at')[:5]
            wallet_data['recent_transactions'] = []
            for transaction in recent_transactions:
                wallet_data['recent_transactions'].append({
                    'type': transaction.type,
                    'amount': float(transaction.amount),
                    'description': transaction.description,
                    'created_at': transaction.created_at
                })

        # Cohort enrollments
        enrollments = user.enrollments.filter(status='active')
        enrollment_data = []
        for enrollment in enrollments:
            enrollment_data.append({
                'cohort_name': enrollment.cohort.name,
                'seat_type': enrollment.seat_type,
                'payment_status': enrollment.payment_status,
                'joined_at': enrollment.joined_at
            })

        # Payment history
        payments = PaymentTransaction.objects.filter(user=user).order_by('-created_at')[:10]
        payment_data = []
        for payment in payments:
            payment_data.append({
                'amount': float(payment.amount),
                'currency': payment.currency,
                'status': payment.status,
                'created_at': payment.created_at
            })

        return Response({
            'subscription': subscription_data,
            'wallet': wallet_data,
            'enrollments': enrollment_data,
            'payment_history': payment_data
        })

    @action(detail=False, methods=['get'])
    def institution_dashboard(self, request):
        """Get institution financial dashboard data"""
        # Get user's organization
        try:
            organization = request.user.organization_memberships.first().organization
        except:
            return Response({'error': 'No organization found'},
                          status=status.HTTP_404_NOT_FOUND)

        # Contract info
        contracts = organization.contracts.filter(status='active')
        contract_data = []
        total_contract_value = 0

        for contract in contracts:
            contract_data.append({
                'id': str(contract.id),
                'type': contract.type,
                'total_value': float(contract.total_value),
                'start_date': contract.start_date,
                'end_date': contract.end_date,
                'days_until_expiry': contract.days_until_expiry
            })
            total_contract_value += contract.total_value

        # Student enrollments
        enrollments = Enrollment.objects.filter(org=organization)
        enrollment_metrics = {
            'total_enrollments': enrollments.count(),
            'active_enrollments': enrollments.filter(status='active').count(),
            'completed_enrollments': enrollments.filter(status='completed').count()
        }

        # Invoices
        invoices = organization.invoices.order_by('-created_at')[:10]
        invoice_data = []
        for invoice in invoices:
            invoice_data.append({
                'invoice_number': invoice.invoice_number,
                'total': float(invoice.total),
                'status': invoice.status,
                'due_date': invoice.due_date,
                'created_at': invoice.created_at
            })

        return Response({
            'organization': {
                'name': organization.name,
                'total_contract_value': float(total_contract_value)
            },
            'contracts': contract_data,
            'enrollment_metrics': enrollment_metrics,
            'recent_invoices': invoice_data
        })

    @action(detail=False, methods=['get'])
    def employer_dashboard(self, request):
        """Get employer financial dashboard data"""
        try:
            employer = request.user.employer_profile
        except:
            return Response({'error': 'Employer profile not found'},
                          status=status.HTTP_404_NOT_FOUND)

        # Job postings
        job_postings = employer.job_postings.filter(is_active=True)
        job_data = []
        for job in job_postings:
            applications_count = job.applications.count()
            job_data.append({
                'title': job.title,
                'applications_count': applications_count,
                'posted_at': job.posted_at
            })

        # Talent interactions
        interest_logs = employer.interest_logs.order_by('-created_at')[:10]
        interaction_data = []
        for log in interest_logs:
            interaction_data.append({
                'action': log.action,
                'candidate_email': log.profile.mentee.email,
                'created_at': log.created_at
            })

        return Response({
            'employer': {
                'company_name': employer.company_name,
                'sector': employer.sector
            },
            'job_postings': job_data,
            'recent_interactions': interaction_data
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revenue_analytics(request):
    """Get revenue analytics data"""
    period = request.GET.get('period', '30')  # days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=int(period))

    analytics = FinancialAnalyticsService()

    # Revenue breakdown
    revenue_breakdown = analytics.generate_revenue_breakdown(start_date, end_date)

    # Key metrics
    mrr = analytics.calculate_mrr()
    arr = analytics.calculate_arr()
    churn_rate = analytics.calculate_churn_rate(start_date, end_date)
    arpu = analytics.calculate_arpu(start_date, end_date)
    ltv = analytics.calculate_ltv()

    return Response({
        'revenue_breakdown': revenue_breakdown,
        'key_metrics': {
            'mrr': float(mrr),
            'arr': float(arr),
            'churn_rate': float(churn_rate),
            'arpu': float(arpu),
            'ltv': float(ltv)
        },
        'period': {
            'start_date': start_date,
            'end_date': end_date,
            'days': int(period)
        }
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_report(request):
    """Generate financial report"""
    report_type = request.data.get('report_type')
    period_start = datetime.strptime(request.data.get('period_start'), '%Y-%m-%d').date()
    period_end = datetime.strptime(request.data.get('period_end'), '%Y-%m-%d').date()

    reporting_service = FinancialReportingService()

    try:
        if report_type == 'revenue_summary':
            report = reporting_service.generate_revenue_summary_report(
                period_start, period_end, request.user
            )
        elif report_type == 'subscription_analytics':
            report = reporting_service.generate_subscription_analytics_report(
                period_start, period_end, request.user
            )
        elif report_type == 'cohort_financials':
            report = reporting_service.generate_cohort_financials_report(
                period_start, period_end, request.user
            )
        elif report_type == 'audit_report':
            report = ComplianceService.generate_audit_report(
                period_start, period_end, request.user
            )
        else:
            return Response({'error': 'Invalid report type'},
                          status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'report_id': str(report.id),
            'status': report.status,
            'title': report.title,
            'created_at': report.created_at
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        return Response({'error': 'Failed to generate report'},
                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def cash_flow_projections(request):
    """Get cash flow projections"""
    projection_type = request.GET.get('type', 'monthly')

    projections = CashFlowProjection.objects.filter(
        projection_type=projection_type
    ).order_by('-created_at')[:12]  # Last 12 periods

    projection_data = []
    for projection in projections:
        projection_data.append({
            'period_start': projection.period_start,
            'period_end': projection.period_end,
            'total_revenue': float(projection.total_revenue),
            'total_expenses': float(projection.total_expenses),
            'net_cash_flow': float(projection.net_cash_flow),
            'confidence_score': float(projection.confidence_score),
            'created_at': projection.created_at
        })

    return Response({
        'projections': projection_data,
        'projection_type': projection_type
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def update_cash_flow_projections(request):
    """Update all cash flow projections"""
    try:
        CashFlowService.update_all_projections()
        return Response({'message': 'Cash flow projections updated successfully'})
    except Exception as e:
        logger.error(f"Failed to update cash flow projections: {str(e)}")
        return Response({'error': 'Failed to update projections'},
                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def financial_alerts(request):
    """Get financial alerts"""
    status_filter = request.GET.get('status', 'active')
    severity_filter = request.GET.get('severity')

    alerts = FinancialAlert.objects.filter(status=status_filter)
    if severity_filter:
        alerts = alerts.filter(severity=severity_filter)

    alerts = alerts.order_by('-created_at')[:50]

    alert_data = []
    for alert in alerts:
        alert_data.append({
            'id': str(alert.id),
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'title': alert.title,
            'description': alert.description,
            'status': alert.status,
            'data': alert.data,
            'created_at': alert.created_at,
            'assigned_to': alert.assigned_to.email if alert.assigned_to else None
        })

    return Response({
        'alerts': alert_data,
        'total_count': len(alert_data)
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def acknowledge_alert(request, alert_id):
    """Acknowledge financial alert"""
    try:
        alert = get_object_or_404(FinancialAlert, id=alert_id)
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()

        return Response({'message': 'Alert acknowledged successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def resolve_alert(request, alert_id):
    """Resolve financial alert"""
    try:
        alert = get_object_or_404(FinancialAlert, id=alert_id)
        alert.status = 'resolved'
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.save()

        return Response({'message': 'Alert resolved successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def kpi_dashboard(request):
    """Get KPI dashboard data"""
    kpis = FinancialKPI.objects.all().order_by('category', 'name')

    kpi_data = {}
    for kpi in kpis:
        if kpi.category not in kpi_data:
            kpi_data[kpi.category] = []

        kpi_data[kpi.category].append({
            'name': kpi.name,
            'current_value': float(kpi.current_value),
            'target_value': float(kpi.target_value) if kpi.target_value else None,
            'previous_value': float(kpi.previous_value) if kpi.previous_value else None,
            'growth_rate': float(kpi.growth_rate),
            'target_achievement': float(kpi.target_achievement),
            'unit': kpi.unit,
            'period': kpi.period,
            'last_updated': kpi.last_updated
        })

    return Response({
        'kpis_by_category': kpi_data,
        'last_updated': timezone.now()
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def update_kpis(request):
    """Update all KPIs"""
    try:
        KPIService.update_all_kpis()
        return Response({'message': 'KPIs updated successfully'})
    except Exception as e:
        logger.error(f"Failed to update KPIs: {str(e)}")
        return Response({'error': 'Failed to update KPIs'},
                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def compliance_status(request):
    """Get compliance status overview"""
    compliance_status = ComplianceService.check_compliance_status()

    # Recent compliance records
    recent_records = ComplianceRecord.objects.order_by('-created_at')[:10]
    record_data = []
    for record in recent_records:
        record_data.append({
            'id': str(record.id),
            'compliance_type': record.compliance_type,
            'title': record.title,
            'status': record.status,
            'compliance_date': record.compliance_date,
            'next_review_date': record.next_review_date
        })

    return Response({
        'compliance_overview': compliance_status,
        'recent_records': record_data
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def audit_logs(request):
    """Get audit logs"""
    page_size = int(request.GET.get('page_size', 50))
    page = int(request.GET.get('page', 1))
    action_type = request.GET.get('action_type')
    user_id = request.GET.get('user_id')

    logs = AuditLog.objects.all()

    if action_type:
        logs = logs.filter(action_type=action_type)
    if user_id:
        logs = logs.filter(user_id=user_id)

    logs = logs.order_by('-created_at')

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated_logs = logs[start:end]

    log_data = []
    for log in paginated_logs:
        log_data.append({
            'id': str(log.id),
            'user': log.user.email if log.user else 'System',
            'action_type': log.action_type,
            'resource_type': log.resource_type,
            'resource_id': str(log.resource_id),
            'changes_summary': log.changes_summary,
            'created_at': log.created_at,
            'ip_address': log.ip_address
        })

    return Response({
        'logs': log_data,
        'total_count': logs.count(),
        'page': page,
        'page_size': page_size
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def run_financial_checks(request):
    """Run all financial alert checks"""
    try:
        FinancialAlertService.run_all_checks()
        return Response({'message': 'Financial checks completed successfully'})
    except Exception as e:
        logger.error(f"Failed to run financial checks: {str(e)}")
        return Response({'error': 'Failed to run financial checks'},
                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)
