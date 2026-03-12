"""
Module Management Views - CRUD operations for cohort modules.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from programs.models import Cohort, Track, Module, Milestone
from cohorts.models import CohortDayMaterial
from cohorts.services.materials_service import materials_service
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cohort_modules(request, cohort_id):
    """
    GET /api/v1/cohorts/{cohort_id}/modules/
    
    Get all modules for a cohort with their day organization.
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        
        # Check permissions (director, coordinator, or mentor)
        if not (request.user == cohort.coordinator or 
                request.user in [ma.mentor for ma in cohort.mentor_assignments.filter(active=True)] or
                request.user.role in ['admin', 'director']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        modules = CohortDayMaterial.objects.filter(cohort=cohort).order_by('day_number', 'order')
        
        modules_data = []
        for module in modules:
            modules_data.append({
                'id': str(module.id),
                'day_number': module.day_number,
                'title': module.title,
                'description': module.description,
                'material_type': module.material_type,
                'content_url': module.content_url,
                'content_text': module.content_text,
                'order': module.order,
                'estimated_minutes': module.estimated_minutes,
                'is_required': module.is_required,
                'unlock_date': module.unlock_date.isoformat() if module.unlock_date else None,
                'created_at': module.created_at.isoformat(),
                'updated_at': module.updated_at.isoformat()
            })
        
        return Response({
            'cohort_id': str(cohort.id),
            'cohort_name': cohort.name,
            'modules': modules_data,
            'total_modules': len(modules_data)
        })
    
    except Exception as e:
        logger.error(f"Get cohort modules error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_cohort_module(request, cohort_id):
    """
    POST /api/v1/cohorts/{cohort_id}/modules/
    
    Add a new module to a cohort.
    
    Request body:
    {
        "day_number": 1,
        "title": "Introduction to Cybersecurity",
        "description": "Basic concepts and principles",
        "material_type": "video",
        "content_url": "https://example.com/video",
        "content_text": "Optional embedded content",
        "estimated_minutes": 30,
        "is_required": true,
        "unlock_date": "2024-01-01"
    }
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        
        # Check permissions
        if not (request.user == cohort.coordinator or 
                request.user.role in ['admin', 'director']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data
        
        # Validate required fields
        required_fields = ['day_number', 'title', 'material_type']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get next order for the day
        from django.db.models import Max
        max_order = CohortDayMaterial.objects.filter(
            cohort=cohort,
            day_number=data['day_number']
        ).aggregate(max_order=Max('order'))['max_order'] or 0
        
        # Create module
        module = CohortDayMaterial.objects.create(
            cohort=cohort,
            day_number=data['day_number'],
            title=data['title'],
            description=data.get('description', ''),
            material_type=data['material_type'],
            content_url=data.get('content_url', ''),
            content_text=data.get('content_text', ''),
            order=max_order + 1,
            estimated_minutes=data.get('estimated_minutes', 30),
            is_required=data.get('is_required', True),
            unlock_date=data.get('unlock_date')
        )
        
        return Response({
            'id': str(module.id),
            'message': 'Module added successfully',
            'module': {
                'id': str(module.id),
                'day_number': module.day_number,
                'title': module.title,
                'material_type': module.material_type,
                'order': module.order
            }
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Add cohort module error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cohort_module(request, cohort_id, module_id):
    """
    PUT /api/v1/cohorts/{cohort_id}/modules/{module_id}/
    
    Update an existing cohort module.
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        module = get_object_or_404(CohortDayMaterial, id=module_id, cohort=cohort)
        
        # Check permissions
        if not (request.user == cohort.coordinator or 
                request.user.role in ['admin', 'director']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data
        
        # Update fields
        updateable_fields = [
            'title', 'description', 'material_type', 'content_url', 
            'content_text', 'estimated_minutes', 'is_required', 'unlock_date'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(module, field, data[field])
        
        module.save()
        
        return Response({
            'message': 'Module updated successfully',
            'module': {
                'id': str(module.id),
                'title': module.title,
                'material_type': module.material_type,
                'updated_at': module.updated_at.isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"Update cohort module error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_cohort_module(request, cohort_id, module_id):
    """
    DELETE /api/v1/cohorts/{cohort_id}/modules/{module_id}/
    
    Delete a cohort module.
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        module = get_object_or_404(CohortDayMaterial, id=module_id, cohort=cohort)
        
        # Check permissions
        if not (request.user == cohort.coordinator or 
                request.user.role in ['admin', 'director']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        module_title = module.title
        module.delete()
        
        return Response({
            'message': f'Module "{module_title}" deleted successfully'
        })
    
    except Exception as e:
        logger.error(f"Delete cohort module error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reorder_cohort_modules(request, cohort_id):
    """
    POST /api/v1/cohorts/{cohort_id}/modules/reorder/
    
    Reorder modules within a day.
    
    Request body:
    {
        "day_number": 1,
        "module_orders": [
            {"module_id": "uuid1", "order": 1},
            {"module_id": "uuid2", "order": 2}
        ]
    }
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        
        # Check permissions
        if not (request.user == cohort.coordinator or 
                request.user.role in ['admin', 'director']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data
        day_number = data.get('day_number')
        module_orders = data.get('module_orders', [])
        
        if not day_number or not module_orders:
            return Response(
                {'error': 'day_number and module_orders are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update orders
        for item in module_orders:
            module_id = item.get('module_id')
            order = item.get('order')
            
            if module_id and order is not None:
                CohortDayMaterial.objects.filter(
                    id=module_id,
                    cohort=cohort,
                    day_number=day_number
                ).update(order=order)
        
        return Response({
            'message': f'Modules reordered successfully for day {day_number}'
        })
    
    except Exception as e:
        logger.error(f"Reorder cohort modules error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_track_modules(request, cohort_id):
    """
    POST /api/v1/cohorts/{cohort_id}/modules/import-track/
    
    Import modules from the cohort's track structure.
    
    Request body:
    {
        "track_id": "uuid",
        "start_day": 1,
        "milestone_ids": ["uuid1", "uuid2"]  // optional filter
    }
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        
        # Check permissions
        if not (request.user == cohort.coordinator or 
                request.user.role in ['admin', 'director']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data
        track_id = data.get('track_id') or (cohort.track.id if cohort.track else None)
        start_day = data.get('start_day', 1)
        milestone_ids = data.get('milestone_ids', [])
        
        if not track_id:
            return Response(
                {'error': 'track_id is required or cohort must have a track'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        track = get_object_or_404(Track, id=track_id)
        
        # Get milestones
        milestones_query = track.milestones.all().order_by('order')
        if milestone_ids:
            milestones_query = milestones_query.filter(id__in=milestone_ids)
        
        imported_count = 0
        current_day = start_day
        
        for milestone in milestones_query:
            modules = milestone.modules.all().order_by('order')
            
            for module in modules:
                # Create cohort day material
                CohortDayMaterial.objects.create(
                    cohort=cohort,
                    day_number=current_day,
                    title=module.name,
                    description=module.description,
                    material_type=module.content_type,
                    content_url=module.content_url,
                    order=imported_count % 10 + 1,  # Simple ordering
                    estimated_minutes=int((module.estimated_hours or 1) * 60),
                    is_required=True
                )
                imported_count += 1
                
                # Move to next day every 3-5 modules
                if imported_count % 4 == 0:
                    current_day += 1
        
        return Response({
            'message': f'Successfully imported {imported_count} modules from track',
            'imported_count': imported_count,
            'days_created': current_day - start_day + 1
        })
    
    except Exception as e:
        logger.error(f"Import track modules error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )