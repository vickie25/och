"""
Institutional Billing Views - API endpoints for contract management and billing.
"""
import logging
from datetime import date, timedelta

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from programs.permissions import IsFinanceUser, IsProgramDirector
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .institutional_models import (
    InstitutionalBilling,
    InstitutionalBillingSchedule,
    InstitutionalContract,
    InstitutionalStudent,
)
from .institutional_service import InstitutionalBillingService
from .models import Organization

logger = logging.getLogger(__name__)


class InstitutionalContractViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing institutional contracts.
    Supports CRUD operations and contract lifecycle management.
    """
    permission_classes = [IsAuthenticated, IsProgramDirector]

    def get_queryset(self):
        """Filter contracts based on user permissions"""
        return InstitutionalContract.objects.select_related('organization').all()

    def list(self, request):
        """
        GET /api/v1/institutional/contracts/
        List all institutional contracts with filtering.
        """
        try:
            queryset = self.get_queryset()

            # Apply filters
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            organization_id = request.query_params.get('organization_id')
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)

            # Pagination
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
            offset = (page - 1) * page_size

            total_count = queryset.count()
            contracts = queryset[offset:offset + page_size]

            contracts_data = []
            for contract in contracts:
                # Get basic analytics
                active_students = contract.enrolled_students.filter(is_active=True).count()
                total_invoiced = contract.billing_records.aggregate(
                    total=Sum('total_amount')
                )['total'] or 0

                contracts_data.append({
                    'id': str(contract.id),
                    'contract_number': contract.contract_number,
                    'organization': {
                        'id': contract.organization.id,
                        'name': contract.organization.name
                    },
                    'status': contract.status,
                    'start_date': contract.start_date.isoformat(),
                    'end_date': contract.end_date.isoformat(),
                    'student_seat_count': contract.student_seat_count,
                    'per_student_rate': float(contract.per_student_rate),
                    'billing_cycle': contract.billing_cycle,
                    'monthly_amount': float(contract.monthly_amount),
                    'annual_amount': float(contract.annual_amount),
                    'active_students': active_students,
                    'seat_utilization': round((active_students / contract.student_seat_count * 100), 2) if contract.student_seat_count > 0 else 0,
                    'total_invoiced': float(total_invoiced),
                    'days_until_expiry': contract.days_until_expiry,
                    'is_renewable': contract.is_renewable,
                    'created_at': contract.created_at.isoformat()
                })

            return Response({
                'contracts': contracts_data,
                'pagination': {
                    'total': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            })

        except Exception as e:
            logger.error(f"Error listing contracts: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request):
        """
        POST /api/v1/institutional/contracts/
        Create a new institutional contract.
        """
        try:
            data = request.data

            # Validate required fields
            required_fields = ['organization_id', 'student_seat_count', 'billing_contact_name', 'billing_contact_email']
            for field in required_fields:
                if not data.get(field):
                    return Response(
                        {'error': f'{field} is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Get organization
            try:
                organization = Organization.objects.get(id=data['organization_id'])
            except Organization.DoesNotExist:
                return Response(
                    {'error': 'Organization not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create contract
            contract = InstitutionalBillingService.create_contract(
                organization=organization,
                seat_count=int(data['student_seat_count']),
                billing_cycle=data.get('billing_cycle', 'monthly'),
                billing_contact_name=data['billing_contact_name'],
                billing_contact_email=data['billing_contact_email'],
                billing_contact_phone=data.get('billing_contact_phone', ''),
                billing_address=data.get('billing_address', ''),
                purchase_order_required=data.get('purchase_order_required', False),
                custom_discount=data.get('custom_discount', 0),
                start_date=data.get('start_date'),
                created_by=request.user
            )

            return Response({
                'id': str(contract.id),
                'contract_number': contract.contract_number,
                'message': f'Contract {contract.contract_number} created successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating contract: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, pk=None):
        """
        GET /api/v1/institutional/contracts/{id}/
        Get detailed contract information.
        """
        try:
            contract = get_object_or_404(InstitutionalContract, id=pk)
            analytics = InstitutionalBillingService.get_contract_analytics(contract.id)

            # Get recent invoices
            recent_invoices = contract.billing_records.order_by('-invoice_date')[:5]
            invoices_data = []
            for invoice in recent_invoices:
                invoices_data.append({
                    'id': str(invoice.id),
                    'invoice_number': invoice.invoice_number,
                    'invoice_date': invoice.invoice_date.isoformat(),
                    'due_date': invoice.due_date.isoformat(),
                    'total_amount': float(invoice.total_amount),
                    'status': invoice.status,
                    'is_overdue': invoice.is_overdue,
                    'days_overdue': invoice.days_overdue
                })

            # Get seat adjustments
            adjustments = contract.seat_adjustments.order_by('-created_at')[:10]
            adjustments_data = []
            for adj in adjustments:
                adjustments_data.append({
                    'id': str(adj.id),
                    'adjustment_type': adj.adjustment_type,
                    'previous_seat_count': adj.previous_seat_count,
                    'new_seat_count': adj.new_seat_count,
                    'adjustment_amount': adj.adjustment_amount,
                    'prorated_amount': float(adj.prorated_amount),
                    'effective_date': adj.effective_date.isoformat(),
                    'reason': adj.reason,
                    'created_at': adj.created_at.isoformat()
                })

            contract_data = {
                'id': str(contract.id),
                'contract_number': contract.contract_number,
                'organization': {
                    'id': contract.organization.id,
                    'name': contract.organization.name,
                    'contact_email': contract.organization.contact_email
                },
                'status': contract.status,
                'start_date': contract.start_date.isoformat(),
                'end_date': contract.end_date.isoformat(),
                'student_seat_count': contract.student_seat_count,
                'per_student_rate': float(contract.per_student_rate),
                'billing_cycle': contract.billing_cycle,
                'monthly_amount': float(contract.monthly_amount),
                'annual_amount': float(contract.annual_amount),
                'auto_renew': contract.auto_renew,
                'custom_discount': float(contract.custom_discount),
                'annual_payment_discount': float(contract.annual_payment_discount),
                'billing_contact_name': contract.billing_contact_name,
                'billing_contact_email': contract.billing_contact_email,
                'billing_contact_phone': contract.billing_contact_phone,
                'billing_address': contract.billing_address,
                'purchase_order_required': contract.purchase_order_required,
                'signed_at': contract.signed_at.isoformat() if contract.signed_at else None,
                'created_at': contract.created_at.isoformat(),
                'analytics': analytics,
                'recent_invoices': invoices_data,
                'seat_adjustments': adjustments_data
            }

            return Response(contract_data)

        except Exception as e:
            logger.error(f"Error retrieving contract {pk}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        POST /api/v1/institutional/contracts/{id}/activate/
        Activate a contract and start billing.
        """
        try:
            contract = InstitutionalBillingService.activate_contract(
                contract_id=pk,
                signed_by=request.user
            )

            return Response({
                'message': f'Contract {contract.contract_number} activated successfully',
                'status': contract.status,
                'signed_at': contract.signed_at.isoformat()
            })

        except Exception as e:
            logger.error(f"Error activating contract {pk}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def adjust_seats(self, request, pk=None):
        """
        POST /api/v1/institutional/contracts/{id}/adjust_seats/
        Adjust seat count with proration.
        """
        try:
            data = request.data
            new_seat_count = data.get('new_seat_count')
            effective_date = data.get('effective_date')
            reason = data.get('reason', '')

            if not new_seat_count:
                return Response(
                    {'error': 'new_seat_count is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            adjustment = InstitutionalBillingService.adjust_seat_count(
                contract_id=pk,
                new_seat_count=int(new_seat_count),
                effective_date=effective_date,
                reason=reason,
                created_by=request.user
            )

            return Response({
                'message': f'Seat count adjusted from {adjustment.previous_seat_count} to {adjustment.new_seat_count}',
                'adjustment_id': str(adjustment.id),
                'prorated_amount': float(adjustment.prorated_amount),
                'effective_date': adjustment.effective_date.isoformat()
            })

        except Exception as e:
            logger.error(f"Error adjusting seats for contract {pk}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def enroll_student(self, request, pk=None):
        """
        POST /api/v1/institutional/contracts/{id}/enroll_student/
        Enroll a student under the contract.
        """
        try:
            data = request.data
            user_id = data.get('user_id')

            if not user_id:
                return Response(
                    {'error': 'user_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            enrollment = InstitutionalBillingService.enroll_student(
                contract_id=pk,
                user_id=user_id,
                enrollment_type='director_enrolled',
                created_by=request.user
            )

            return Response({
                'message': f'Student {enrollment.user.email} enrolled successfully',
                'enrollment_id': str(enrollment.id),
                'enrolled_at': enrollment.enrolled_at.isoformat()
            })

        except Exception as e:
            logger.error(f"Error enrolling student in contract {pk}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def renewal_quote(self, request, pk=None):
        """
        GET /api/v1/institutional/contracts/{id}/renewal_quote/
        Generate renewal quote for contract.
        """
        try:
            new_seat_count = request.query_params.get('new_seat_count')
            new_billing_cycle = request.query_params.get('new_billing_cycle')

            quote = InstitutionalBillingService.generate_contract_renewal_quote(
                contract_id=pk,
                new_seat_count=int(new_seat_count) if new_seat_count else None,
                new_billing_cycle=new_billing_cycle
            )

            return Response(quote)

        except Exception as e:
            logger.error(f"Error generating renewal quote for contract {pk}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class InstitutionalBillingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for institutional billing and invoices.
    Read-only access to billing records.
    """
    permission_classes = [IsAuthenticated, IsFinanceUser]

    def get_queryset(self):
        """Get billing records with related data"""
        return InstitutionalBilling.objects.select_related(
            'contract__organization'
        ).all()

    def list(self, request):
        """
        GET /api/v1/institutional/billing/
        List institutional invoices with filtering.
        """
        try:
            queryset = self.get_queryset()

            # Apply filters
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            contract_id = request.query_params.get('contract_id')
            if contract_id:
                queryset = queryset.filter(contract_id=contract_id)

            organization_id = request.query_params.get('organization_id')
            if organization_id:
                queryset = queryset.filter(contract__organization_id=organization_id)

            # Date range filter
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            if start_date:
                queryset = queryset.filter(invoice_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(invoice_date__lte=end_date)

            # Pagination
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
            offset = (page - 1) * page_size

            total_count = queryset.count()
            invoices = queryset.order_by('-invoice_date')[offset:offset + page_size]

            invoices_data = []
            for invoice in invoices:
                invoices_data.append({
                    'id': str(invoice.id),
                    'invoice_number': invoice.invoice_number,
                    'contract': {
                        'id': str(invoice.contract.id),
                        'contract_number': invoice.contract.contract_number,
                        'organization_name': invoice.contract.organization.name
                    },
                    'billing_period_start': invoice.billing_period_start.isoformat(),
                    'billing_period_end': invoice.billing_period_end.isoformat(),
                    'invoice_date': invoice.invoice_date.isoformat(),
                    'due_date': invoice.due_date.isoformat(),
                    'total_amount': float(invoice.total_amount),
                    'status': invoice.status,
                    'is_overdue': invoice.is_overdue,
                    'days_overdue': invoice.days_overdue,
                    'sent_at': invoice.sent_at.isoformat() if invoice.sent_at else None,
                    'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None
                })

            # Calculate summary stats
            total_amount = queryset.aggregate(total=Sum('total_amount'))['total'] or 0
            paid_amount = queryset.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
            overdue_amount = queryset.filter(status='overdue').aggregate(total=Sum('total_amount'))['total'] or 0

            return Response({
                'invoices': invoices_data,
                'summary': {
                    'total_invoiced': float(total_amount),
                    'total_paid': float(paid_amount),
                    'total_outstanding': float(total_amount - paid_amount),
                    'total_overdue': float(overdue_amount)
                },
                'pagination': {
                    'total': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            })

        except Exception as e:
            logger.error(f"Error listing billing records: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, pk=None):
        """
        GET /api/v1/institutional/billing/{id}/
        Get detailed invoice information.
        """
        try:
            invoice = get_object_or_404(InstitutionalBilling, id=pk)

            invoice_data = {
                'id': str(invoice.id),
                'invoice_number': invoice.invoice_number,
                'contract': {
                    'id': str(invoice.contract.id),
                    'contract_number': invoice.contract.contract_number,
                    'organization': {
                        'id': invoice.contract.organization.id,
                        'name': invoice.contract.organization.name,
                        'contact_email': invoice.contract.organization.contact_email
                    }
                },
                'billing_period_start': invoice.billing_period_start.isoformat(),
                'billing_period_end': invoice.billing_period_end.isoformat(),
                'billing_cycle': invoice.billing_cycle,
                'base_seat_count': invoice.base_seat_count,
                'active_seat_count': invoice.active_seat_count,
                'base_amount': float(invoice.base_amount),
                'adjustment_amount': float(invoice.adjustment_amount),
                'discount_amount': float(invoice.discount_amount),
                'tax_amount': float(invoice.tax_amount),
                'total_amount': float(invoice.total_amount),
                'currency': invoice.currency,
                'status': invoice.status,
                'invoice_date': invoice.invoice_date.isoformat(),
                'due_date': invoice.due_date.isoformat(),
                'is_overdue': invoice.is_overdue,
                'days_overdue': invoice.days_overdue,
                'sent_at': invoice.sent_at.isoformat() if invoice.sent_at else None,
                'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None,
                'payment_method': invoice.payment_method,
                'payment_reference': invoice.payment_reference,
                'purchase_order_number': invoice.purchase_order_number,
                'line_items': invoice.line_items,
                'pdf_url': invoice.pdf_url,
                'created_at': invoice.created_at.isoformat()
            }

            return Response(invoice_data)

        except Exception as e:
            logger.error(f"Error retrieving invoice {pk}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """
        POST /api/v1/institutional/billing/{id}/mark_paid/
        Mark invoice as paid.
        """
        try:
            invoice = get_object_or_404(InstitutionalBilling, id=pk)

            payment_method = request.data.get('payment_method', '')
            payment_reference = request.data.get('payment_reference', '')

            invoice.mark_as_paid(payment_method, payment_reference)

            return Response({
                'message': f'Invoice {invoice.invoice_number} marked as paid',
                'paid_at': invoice.paid_at.isoformat(),
                'status': invoice.status
            })

        except Exception as e:
            logger.error(f"Error marking invoice {pk} as paid: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def send_invoice(self, request, pk=None):
        """
        POST /api/v1/institutional/billing/{id}/send_invoice/
        Send invoice email to billing contact.
        """
        try:
            success = InstitutionalBillingService.send_invoice_email(pk)

            if success:
                return Response({
                    'message': 'Invoice email sent successfully'
                })
            else:
                return Response(
                    {'error': 'Failed to send invoice email'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Error sending invoice {pk}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class InstitutionalStudentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Institutional students for director UI (camelCase payload).
    GET /api/v1/institutional/students/
    POST .../students/{id}/deactivate/ | reactivate/
    """

    permission_classes = [IsAuthenticated, IsProgramDirector]

    def get_queryset(self):
        return InstitutionalStudent.objects.select_related(
            'user', 'contract__organization'
        ).order_by('-enrolled_at')

    def list(self, request):
        try:
            qs = self.get_queryset()
            contract_id = request.query_params.get('contract_id')
            if contract_id:
                qs = qs.filter(contract_id=contract_id)
            status_filter = request.query_params.get('status')
            if status_filter == 'active':
                qs = qs.filter(is_active=True)
            elif status_filter == 'inactive':
                qs = qs.filter(is_active=False)
            search = (request.query_params.get('search') or '').strip()
            if search:
                qs = qs.filter(
                    Q(user__email__icontains=search)
                    | Q(user__first_name__icontains=search)
                    | Q(user__last_name__icontains=search)
                )
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
            offset = (page - 1) * page_size
            total_count = qs.count()
            rows = qs[offset : offset + page_size]

            students_data = []
            for enr in rows:
                u = enr.user
                students_data.append(
                    {
                        'id': str(enr.id),
                        'user': {
                            'id': str(u.id),
                            'email': u.email,
                            'firstName': u.first_name or '',
                            'lastName': u.last_name or '',
                        },
                        'contract': {
                            'id': str(enr.contract.id),
                            'contractNumber': enr.contract.contract_number,
                            'organizationName': enr.contract.organization.name,
                        },
                        'enrolledAt': enr.enrolled_at.isoformat(),
                        'enrollmentType': enr.enrollment_type,
                        'isActive': enr.is_active,
                        'trackAssignments': [],
                    }
                )

            return Response(
                {
                    'students': students_data,
                    'pagination': {
                        'total': total_count,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': (total_count + page_size - 1) // page_size
                        if page_size
                        else 1,
                    },
                }
            )
        except Exception as e:
            logger.error('Error listing institutional students: %s', e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        reason = (request.data.get('reason') or '').strip() or 'Deactivated by administrator'
        try:
            enr = get_object_or_404(InstitutionalStudent, id=pk)
            enr.deactivate(reason=reason)
            return Response({'message': 'Student deactivated', 'isActive': False})
        except Exception as e:
            logger.error('Deactivate institutional student %s: %s', pk, e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reactivate')
    def reactivate(self, request, pk=None):
        try:
            enr = get_object_or_404(InstitutionalStudent, id=pk)
            enr.reactivate()
            return Response({'message': 'Student reactivated', 'isActive': True})
        except Exception as e:
            logger.error('Reactivate institutional student %s: %s', pk, e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsFinanceUser])
def institutional_analytics(request):
    """
    GET /api/v1/institutional/analytics/
    Get institutional billing analytics and metrics.
    """
    try:
        # Date range filter
        days = int(request.query_params.get('days', 30))
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Contract metrics
        total_contracts = InstitutionalContract.objects.count()
        active_contracts = InstitutionalContract.objects.filter(status='active').count()
        expiring_contracts = InstitutionalContract.objects.filter(
            status='active',
            end_date__lte=end_date + timedelta(days=60)
        ).count()

        # Revenue metrics
        total_mrr = InstitutionalContract.objects.filter(
            status='active'
        ).aggregate(
            total=Sum('student_seat_count') * Sum('per_student_rate')
        )['total'] or 0

        # Invoice metrics
        invoices_in_period = InstitutionalBilling.objects.filter(
            invoice_date__gte=start_date,
            invoice_date__lte=end_date
        )

        total_invoiced = invoices_in_period.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = invoices_in_period.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
        total_overdue = InstitutionalBilling.objects.filter(status='overdue').aggregate(total=Sum('total_amount'))['total'] or 0

        # Student metrics
        total_licensed_seats = InstitutionalContract.objects.filter(
            status='active'
        ).aggregate(total=Sum('student_seat_count'))['total'] or 0

        active_students = InstitutionalStudent.objects.filter(
            is_active=True,
            contract__status='active'
        ).count()

        seat_utilization = (active_students / total_licensed_seats * 100) if total_licensed_seats > 0 else 0

        # Top organizations by revenue
        top_orgs = InstitutionalContract.objects.filter(
            status='active'
        ).values(
            'organization__name'
        ).annotate(
            monthly_revenue=Sum('student_seat_count') * Sum('per_student_rate')
        ).order_by('-monthly_revenue')[:10]

        analytics = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'contracts': {
                'total_contracts': total_contracts,
                'active_contracts': active_contracts,
                'expiring_soon': expiring_contracts,
                'contract_health': round((active_contracts / total_contracts * 100), 2) if total_contracts > 0 else 0
            },
            'revenue': {
                'monthly_recurring_revenue': float(total_mrr),
                'annual_recurring_revenue': float(total_mrr * 12),
                'total_invoiced_period': float(total_invoiced),
                'total_paid_period': float(total_paid),
                'collection_rate': round((total_paid / total_invoiced * 100), 2) if total_invoiced > 0 else 0,
                'total_overdue': float(total_overdue)
            },
            'students': {
                'total_licensed_seats': total_licensed_seats,
                'active_students': active_students,
                'seat_utilization': round(seat_utilization, 2),
                'available_seats': total_licensed_seats - active_students
            },
            'top_organizations': [
                {
                    'name': org['organization__name'],
                    'monthly_revenue': float(org['monthly_revenue'])
                }
                for org in top_orgs
            ]
        }

        return Response(analytics)

    except Exception as e:
        logger.error(f"Error generating institutional analytics: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def process_scheduled_billing(request):
    """
    POST /api/v1/institutional/process_billing/
    Manually trigger scheduled billing processing.
    """
    try:
        # Get pending schedules
        pending_schedules = InstitutionalBillingSchedule.objects.filter(
            is_processed=False,
            next_billing_date__lte=date.today()
        )

        results = {
            'processed': 0,
            'errors': [],
            'invoices_generated': []
        }

        for schedule in pending_schedules:
            try:
                invoice = InstitutionalBillingService.process_scheduled_billing(schedule.id)
                results['processed'] += 1
                results['invoices_generated'].append({
                    'invoice_number': invoice.invoice_number,
                    'contract_number': invoice.contract.contract_number,
                    'amount': float(invoice.total_amount)
                })
            except Exception as e:
                results['errors'].append(f"Schedule {schedule.id}: {str(e)}")

        return Response(results)

    except Exception as e:
        logger.error(f"Error processing scheduled billing: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
