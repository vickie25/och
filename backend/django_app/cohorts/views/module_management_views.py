"""
Module Management Views - CRUD operations for cohort modules.
"""
import logging

from curriculum.models import CurriculumModule, CurriculumTrack
from django.db import models
from django.db.models import Max
from django.shortcuts import get_object_or_404
from programs.models import Cohort, Track
from programs.permissions import _is_director_or_admin
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cohorts.models import CohortDayMaterial

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cohort_modules_list(request, cohort_id):
    """Handle GET and POST for cohort modules list."""
    if request.method == 'GET':
        return get_cohort_modules(request, cohort_id)
    elif request.method == 'POST':
        return add_cohort_module(request, cohort_id)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def cohort_modules_detail(request, cohort_id, module_id):
    """Handle PUT and DELETE for individual cohort modules."""
    if request.method == 'PUT':
        return update_cohort_module(request, cohort_id, module_id)
    elif request.method == 'DELETE':
        return delete_cohort_module(request, cohort_id, module_id)


def get_cohort_modules(request, cohort_id):
    """
    GET /api/v1/cohorts/{cohort_id}/modules/

    Get all modules for a cohort with their day organization.
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)

        # Check permissions (program director/admin, coordinator, or assigned mentor)
        if not (
            _is_director_or_admin(request.user)
            or request.user == cohort.coordinator
            or request.user in [ma.mentor for ma in cohort.mentor_assignments.filter(active=True)]
        ):
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

        # Check permissions (program director/admin or coordinator)
        if not (
            _is_director_or_admin(request.user)
            or request.user == cohort.coordinator
        ):
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


def update_cohort_module(request, cohort_id, module_id):
    """
    PUT /api/v1/cohorts/{cohort_id}/modules/{module_id}/

    Update an existing cohort module.
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        module = get_object_or_404(CohortDayMaterial, id=module_id, cohort=cohort)

        # Check permissions (program director/admin or coordinator)
        if not (
            _is_director_or_admin(request.user)
            or request.user == cohort.coordinator
        ):
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


def delete_cohort_module(request, cohort_id, module_id):
    """
    DELETE /api/v1/cohorts/{cohort_id}/modules/{module_id}/

    Delete a cohort module.
    """
    try:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        module = get_object_or_404(CohortDayMaterial, id=module_id, cohort=cohort)

        # Check permissions (program director/admin or coordinator)
        if not (
            _is_director_or_admin(request.user)
            or request.user == cohort.coordinator
        ):
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

        # Check permissions (program director/admin or coordinator)
        if not (
            _is_director_or_admin(request.user)
            or request.user == cohort.coordinator
        ):
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

        # Check permissions (program director/admin or coordinator)
        if not (
            _is_director_or_admin(request.user)
            or request.user == cohort.coordinator
        ):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        start_day = data.get('start_day', 1)
        milestone_ids = data.get('milestone_ids', [])

        # ------------------------------------------------------------------
        # 1) Prefer explicit programs.Track if provided (backwards compatible)
        # ------------------------------------------------------------------
        track_id = data.get('track_id') or (cohort.track.id if cohort.track else None)

        # ------------------------------------------------------------------
        # 2) Curriculum-based import when cohort has curriculum_tracks
        #    Use the curriculum engine as the primary source of truth.
        # ------------------------------------------------------------------
        curriculum_slugs = []
        if isinstance(cohort.curriculum_tracks, list):
            curriculum_slugs = [s for s in cohort.curriculum_tracks if isinstance(s, str)]

        if not track_id and curriculum_slugs:
            # Resolve curriculum tracks from stored slugs
            curriculum_tracks = list(
                CurriculumTrack.objects.filter(
                    slug__in=curriculum_slugs,
                    is_active=True
                )
            )

            if not curriculum_tracks:
                return Response(
                    {
                        'message': 'Cohort has curriculum tracks assigned but none are active in curriculum engine.',
                        'imported_count': 0,
                        'days_created': 0,
                    },
                    status=status.HTTP_200_OK,
                )

            # Build list of keys we should match on for modules
            module_track_keys = []
            for ct in curriculum_tracks:
                if getattr(ct, 'slug', None):
                    module_track_keys.append(ct.slug)
                if getattr(ct, 'code', None):
                    module_track_keys.append(ct.code)

            # Fetch all active curriculum modules for these tracks.
            # Prefer FK linkage via track; fall back to track_key-based linkage.
            curriculum_modules = list(
                CurriculumModule.objects.filter(is_active=True).filter(
                    models.Q(track__in=curriculum_tracks) | models.Q(track_key__in=module_track_keys)
                ).order_by('track_key', 'order_index')
            )

            if not curriculum_modules:
                return Response(
                    {
                        'message': 'We have no modules on the assigned curriculum tracks to import.',
                        'imported_count': 0,
                        'days_created': 0,
                    },
                    status=status.HTTP_200_OK,
                )

            imported_count = 0
            current_day = start_day

            # Start ordering after any existing materials for the starting day
            current_order = (
                CohortDayMaterial.objects.filter(
                    cohort=cohort, day_number=current_day
                ).aggregate(max_order=Max('order'))['max_order']
                or 0
            )

            for cm in curriculum_modules:
                # When we move to a new day, recompute starting order for that day
                if imported_count > 0 and imported_count % 4 == 0:
                    current_day += 1
                    current_order = (
                        CohortDayMaterial.objects.filter(
                            cohort=cohort, day_number=current_day
                        ).aggregate(max_order=Max('order'))['max_order']
                        or 0
                    )

                current_order += 1

                CohortDayMaterial.objects.create(
                    cohort=cohort,
                    day_number=current_day,
                    title=cm.title,
                    description=cm.description,
                    # Curriculum modules are containers; map to a generic reading/article type
                    material_type='reading',
                    content_url='',
                    content_text='',
                    order=current_order,
                    estimated_minutes=cm.estimated_duration_minutes or 30,
                    is_required=cm.is_required,
                )
                imported_count += 1

            return Response(
                {
                    'message': f'Successfully imported {imported_count} modules from assigned curriculum tracks.',
                    'imported_count': imported_count,
                    'days_created': max(0, current_day - start_day + 1),
                }
            )

        # ------------------------------------------------------------------
        # 3) Legacy programs.Track-based import (existing behavior)
        # ------------------------------------------------------------------
        if not track_id:
            return Response(
                {
                    'error': 'Cohort has no assigned curriculum tracks with modules and no primary track. '
                             'Assign curriculum tracks or a primary track before importing.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        track = get_object_or_404(Track, id=track_id)

        # Get milestones
        milestones_query = track.milestones.all().order_by('order')
        if milestone_ids:
            milestones_query = milestones_query.filter(id__in=milestone_ids)

        imported_count = 0
        current_day = start_day

        # Start ordering after any existing materials for the starting day
        current_order = (
            CohortDayMaterial.objects.filter(
                cohort=cohort, day_number=current_day
            ).aggregate(max_order=Max('order'))['max_order']
            or 0
        )

        for milestone in milestones_query:
            modules = milestone.modules.all().order_by('order')

            for module in modules:
                if imported_count > 0 and imported_count % 4 == 0:
                    current_day += 1
                    current_order = (
                        CohortDayMaterial.objects.filter(
                            cohort=cohort, day_number=current_day
                        ).aggregate(max_order=Max('order'))['max_order']
                        or 0
                    )

                current_order += 1

                CohortDayMaterial.objects.create(
                    cohort=cohort,
                    day_number=current_day,
                    title=module.name,
                    description=module.description,
                    material_type=module.content_type,
                    content_url=module.content_url,
                    order=current_order,
                    estimated_minutes=int((module.estimated_hours or 1) * 60),
                    is_required=True,
                )
                imported_count += 1

        return Response(
            {
                'message': f'Successfully imported {imported_count} modules from track.',
                'imported_count': imported_count,
                'days_created': max(0, current_day - start_day + 1),
            }
        )

    except Exception as e:
        logger.error(f"Import track modules error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
