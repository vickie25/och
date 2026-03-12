"""
API Views for Dynamic Content Selection and Financial Monitoring
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
from .dynamic_content_models import (
    CohortContent, CohortContentTemplate, PaymentSuccessRateTracking,
    InvoiceDeliveryTracking, DunningRecoveryTracking, PCIComplianceMonitoring
)
from .models import Cohort, Track, Milestone, Module
from .permissions import IsDirectorOrAdmin


class CohortContentViewSet(viewsets.ModelViewSet):
    """Manage dynamic content selection for cohorts"""
    permission_classes = [IsAuthenticated, IsDirectorOrAdmin]
    
    def get_queryset(self):
        cohort_id = self.request.query_params.get('cohort')
        if cohort_id:
            return CohortContent.objects.filter(cohort_id=cohort_id).select_related(
                'cohort', 'milestone', 'module'
            )
        return CohortContent.objects.select_related('cohort', 'milestone', 'module')
    
    @action(detail=False, methods=['post'], url_path='bulk-add')
    def bulk_add_content(self, request):
        """Add multiple content items to a cohort"""
        cohort_id = request.data.get('cohort_id')
        content_items = request.data.get('content_items', [])
        
        if not cohort_id or not content_items:
            return Response(
                {'error': 'cohort_id and content_items are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cohort = Cohort.objects.get(id=cohort_id)
            created_items = []
            
            for item in content_items:
                milestone_id = item.get('milestone_id')
                module_id = item.get('module_id')
                
                if not milestone_id or not module_id:
                    continue
                
                content_item, created = CohortContent.objects.get_or_create(
                    cohort=cohort,
                    milestone_id=milestone_id,
                    module_id=module_id,
                    defaults={
                        'is_required': item.get('is_required', True),
                        'custom_order': item.get('custom_order', 0),
                        'custom_duration_hours': item.get('custom_duration_hours'),
                        'custom_description': item.get('custom_description', ''),
                        'added_by': request.user,
                    }
                )
                
                if created:
                    created_items.append({
                        'id': str(content_item.id),
                        'milestone_name': content_item.milestone.name,
                        'module_name': content_item.module.name,
                        'is_required': content_item.is_required,
                        'custom_order': content_item.custom_order,
                    })
            
            return Response({
                'success': True,
                'created_count': len(created_items),
                'created_items': created_items
            })
            
        except Cohort.DoesNotExist:
            return Response(
                {'error': 'Cohort not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='available-content')
    def available_content(self, request):
        """Get available content from a track for selection"""
        track_id = request.query_params.get('track_id')
        cohort_id = request.query_params.get('cohort_id')
        
        if not track_id:
            return Response(
                {'error': 'track_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            track = Track.objects.get(id=track_id)
            milestones = Milestone.objects.filter(track=track).prefetch_related('modules')
            
            # Get already selected content for this cohort
            selected_content = set()
            if cohort_id:
                selected_content = set(
                    CohortContent.objects.filter(cohort_id=cohort_id)
                    .values_list('milestone_id', 'module_id')
                )
            
            available_content = []
            for milestone in milestones:
                milestone_data = {
                    'id': str(milestone.id),
                    'name': milestone.name,
                    'description': milestone.description,
                    'order': milestone.order,
                    'duration_weeks': milestone.duration_weeks,
                    'modules': []
                }
                
                for module in milestone.modules.all():
                    is_selected = (str(milestone.id), str(module.id)) in selected_content
                    
                    module_data = {
                        'id': str(module.id),
                        'name': module.name,
                        'description': module.description,
                        'content_type': module.content_type,
                        'estimated_hours': module.estimated_hours,
                        'skills': module.skills,
                        'order': module.order,
                        'is_selected': is_selected,
                    }
                    milestone_data['modules'].append(module_data)
                
                available_content.append(milestone_data)
            
            return Response({
                'track': {
                    'id': str(track.id),
                    'name': track.name,
                    'description': track.description,
                },
                'milestones': available_content
            })
            
        except Track.DoesNotExist:
            return Response(
                {'error': 'Track not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CohortContentTemplateViewSet(viewsets.ModelViewSet):
    """Manage reusable content templates"""
    permission_classes = [IsAuthenticated, IsDirectorOrAdmin]
    
    def get_queryset(self):
        track_id = self.request.query_params.get('track')
        if track_id:
            return CohortContentTemplate.objects.filter(track_id=track_id)
        return CohortContentTemplate.objects.all()
    
    @action(detail=True, methods=['post'], url_path='apply-to-cohort')
    def apply_to_cohort(self, request, pk=None):
        """Apply a content template to a cohort"""
        template = self.get_object()
        cohort_id = request.data.get('cohort_id')
        
        if not cohort_id:
            return Response(
                {'error': 'cohort_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cohort = Cohort.objects.get(id=cohort_id)
            
            # Clear existing content
            CohortContent.objects.filter(cohort=cohort).delete()
            
            # Apply template
            created_items = []
            for item in template.content_selection:
                content_item = CohortContent.objects.create(
                    cohort=cohort,
                    milestone_id=item['milestone_id'],
                    module_id=item['module_id'],
                    is_required=item.get('is_required', True),
                    custom_order=item.get('custom_order', 0),
                    custom_duration_hours=item.get('custom_duration_hours'),
                    custom_description=item.get('custom_description', ''),
                    added_by=request.user,
                )
                created_items.append(content_item)
            
            # Update template usage count
            template.usage_count += 1
            template.save()
            
            return Response({
                'success': True,
                'applied_items_count': len(created_items),
                'template_name': template.name
            })
            
        except Cohort.DoesNotExist:
            return Response(
                {'error': 'Cohort not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_success_rate_dashboard(request):
    """Get payment success rate metrics for financial dashboard"""
    # Get date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get tracking data
    tracking_data = PaymentSuccessRateTracking.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Calculate overall metrics
    total_attempts = sum(t.total_attempts for t in tracking_data)
    total_successful = sum(t.successful_payments for t in tracking_data)
    overall_success_rate = (total_successful / total_attempts * 100) if total_attempts > 0 else 0
    
    # Daily breakdown
    daily_data = []
    for tracking in tracking_data:
        daily_data.append({
            'date': tracking.date.isoformat(),
            'success_rate': float(tracking.success_rate_percentage),
            'total_attempts': tracking.total_attempts,
            'successful_payments': tracking.successful_payments,
            'failed_payments': tracking.failed_payments,
            'meets_threshold': tracking.success_rate_percentage >= tracking.threshold_percentage,
        })
    
    # Gateway breakdown
    gateway_stats = {}
    for tracking in tracking_data:
        for gateway, stats in tracking.gateway_breakdown.items():
            if gateway not in gateway_stats:
                gateway_stats[gateway] = {'success': 0, 'failed': 0}
            gateway_stats[gateway]['success'] += stats.get('success', 0)
            gateway_stats[gateway]['failed'] += stats.get('failed', 0)
    
    # Calculate gateway success rates
    for gateway, stats in gateway_stats.items():
        total = stats['success'] + stats['failed']
        stats['success_rate'] = (stats['success'] / total * 100) if total > 0 else 0
    
    return Response({
        'overall_metrics': {
            'success_rate': round(overall_success_rate, 2),
            'total_attempts': total_attempts,
            'successful_payments': total_successful,
            'failed_payments': total_attempts - total_successful,
            'meets_95_percent_target': overall_success_rate >= 95.0,
        },
        'daily_data': daily_data,
        'gateway_breakdown': gateway_stats,
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_delivery_metrics(request):
    """Get invoice delivery time metrics for 5-minute SLA compliance"""
    # Get date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get delivery tracking data
    delivery_data = InvoiceDeliveryTracking.objects.filter(
        transaction_completed_at__range=[start_date, end_date]
    ).order_by('-transaction_completed_at')
    
    # Calculate metrics
    total_invoices = delivery_data.count()
    sla_compliant = delivery_data.filter(meets_5min_sla=True).count()
    sla_compliance_rate = (sla_compliant / total_invoices * 100) if total_invoices > 0 else 0
    
    # Average delivery times
    avg_generation_time = delivery_data.aggregate(
        avg=Avg('generation_time_seconds')
    )['avg'] or 0
    
    avg_total_time = delivery_data.aggregate(
        avg=Avg('total_time_seconds')
    )['avg'] or 0
    
    # Recent deliveries
    recent_deliveries = []
    for delivery in delivery_data[:20]:
        recent_deliveries.append({
            'invoice_number': delivery.invoice.invoice_number,
            'transaction_completed_at': delivery.transaction_completed_at.isoformat(),
            'total_time_seconds': delivery.total_time_seconds,
            'meets_5min_sla': delivery.meets_5min_sla,
            'sla_breach_reason': delivery.sla_breach_reason,
        })
    
    return Response({
        'sla_metrics': {
            'total_invoices': total_invoices,
            'sla_compliant': sla_compliant,
            'sla_compliance_rate': round(sla_compliance_rate, 2),
            'meets_5min_target': sla_compliance_rate >= 95.0,  # 95% should meet 5-min SLA
        },
        'timing_metrics': {
            'avg_generation_time_seconds': round(avg_generation_time, 2),
            'avg_total_time_seconds': round(avg_total_time, 2),
            'avg_generation_time_minutes': round(avg_generation_time / 60, 2),
            'avg_total_time_minutes': round(avg_total_time / 60, 2),
        },
        'recent_deliveries': recent_deliveries,
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dunning_recovery_metrics(request):
    """Get dunning management recovery rate metrics for 80% target compliance"""
    # Get date range
    days = int(request.GET.get('days', 90))  # Longer period for dunning cycles
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get dunning tracking data
    dunning_data = DunningRecoveryTracking.objects.filter(
        cycle_start_date__range=[start_date, end_date]
    )
    
    # Calculate recovery metrics
    total_cycles = dunning_data.count()
    recovered_cycles = dunning_data.filter(status='recovered').count()
    failed_cycles = dunning_data.filter(status='failed').count()
    active_cycles = dunning_data.filter(status='active').count()
    
    recovery_rate = (recovered_cycles / total_cycles * 100) if total_cycles > 0 else 0
    
    # Recovery amounts
    total_recovered_amount = dunning_data.filter(
        status='recovered'
    ).aggregate(
        total=models.Sum('recovery_amount')
    )['total'] or 0
    
    # Average recovery time
    completed_cycles = dunning_data.filter(status__in=['recovered', 'failed'])
    avg_cycle_duration = 0
    if completed_cycles.exists():
        durations = []
        for cycle in completed_cycles:
            if cycle.cycle_end_date:
                duration = (cycle.cycle_end_date - cycle.cycle_start_date).days
                durations.append(duration)
        avg_cycle_duration = sum(durations) / len(durations) if durations else 0
    
    # Recent recoveries
    recent_recoveries = []
    for recovery in dunning_data.filter(status='recovered').order_by('-recovered_at')[:10]:
        recent_recoveries.append({
            'user_email': recovery.subscription.user.email,
            'recovered_at': recovery.recovered_at.isoformat() if recovery.recovered_at else None,
            'recovery_amount': float(recovery.recovery_amount) if recovery.recovery_amount else 0,
            'total_attempts': recovery.total_attempts,
            'cycle_duration_days': (recovery.cycle_end_date - recovery.cycle_start_date).days if recovery.cycle_end_date else None,
        })
    
    return Response({
        'recovery_metrics': {
            'total_cycles': total_cycles,
            'recovered_cycles': recovered_cycles,
            'failed_cycles': failed_cycles,
            'active_cycles': active_cycles,
            'recovery_rate': round(recovery_rate, 2),
            'meets_80_percent_target': recovery_rate >= 80.0,
        },
        'financial_metrics': {
            'total_recovered_amount': float(total_recovered_amount),
            'avg_recovery_amount': float(total_recovered_amount / recovered_cycles) if recovered_cycles > 0 else 0,
        },
        'timing_metrics': {
            'avg_cycle_duration_days': round(avg_cycle_duration, 1),
        },
        'recent_recoveries': recent_recoveries,
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pci_compliance_dashboard(request):
    """Get PCI compliance monitoring dashboard"""
    # Get recent violations
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    violations = PCIComplianceMonitoring.objects.filter(
        detected_at__range=[start_date, end_date]
    ).order_by('-detected_at')
    
    # Calculate metrics
    total_violations = violations.count()
    open_violations = violations.filter(status='open').count()
    resolved_violations = violations.filter(status='resolved').count()
    critical_violations = violations.filter(severity='critical').count()
    
    # Violation breakdown by type
    violation_types = {}
    for violation in violations:
        vtype = violation.get_violation_type_display()
        if vtype not in violation_types:
            violation_types[vtype] = {'total': 0, 'open': 0, 'critical': 0}
        violation_types[vtype]['total'] += 1
        if violation.status == 'open':
            violation_types[vtype]['open'] += 1
        if violation.severity == 'critical':
            violation_types[vtype]['critical'] += 1
    
    # Recent violations
    recent_violations = []
    for violation in violations[:20]:
        recent_violations.append({
            'id': str(violation.id),
            'violation_type': violation.get_violation_type_display(),
            'severity': violation.severity,
            'status': violation.status,
            'detected_at': violation.detected_at.isoformat(),
            'description': violation.description[:200] + '...' if len(violation.description) > 200 else violation.description,
            'affected_systems': violation.affected_systems,
        })
    
    return Response({
        'compliance_status': {
            'total_violations': total_violations,
            'open_violations': open_violations,
            'resolved_violations': resolved_violations,
            'critical_violations': critical_violations,
            'zero_violations_target_met': total_violations == 0,
            'compliance_score': max(0, 100 - (open_violations * 10) - (critical_violations * 25)),
        },
        'violation_breakdown': violation_types,
        'recent_violations': recent_violations,
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days,
        }
    })