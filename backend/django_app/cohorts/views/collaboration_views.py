"""
Collaboration Views - Handle peer and mentor messaging.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from programs.models import Enrollment
from cohorts.models import CohortPeerMessage, CohortMentorMessage
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def peer_messages(request):
    """
    GET /api/v1/cohorts/messages/peers?cohort_id=uuid
    POST /api/v1/cohorts/messages/peers
    
    Get or send peer messages.
    """
    if request.method == 'GET':
        try:
            cohort_id = request.query_params.get('cohort_id')
            
            if not cohort_id:
                return Response(
                    {'error': 'cohort_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify enrollment
            try:
                enrollment = Enrollment.objects.get(
                    cohort_id=cohort_id,
                    user=request.user
                )
            except Enrollment.DoesNotExist:
                return Response(
                    {'error': 'Not enrolled in this cohort'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get messages
            messages = CohortPeerMessage.objects.filter(
                cohort_id=cohort_id
            ).filter(
                models.Q(sender=request.user) |
                models.Q(recipient=request.user) |
                models.Q(is_group_message=True)
            ).select_related('sender', 'recipient').order_by('-created_at')[:50]
            
            messages_data = []
            for msg in messages:
                messages_data.append({
                    'id': str(msg.id),
                    'sender': {
                        'id': str(msg.sender.id),
                        'name': f"{msg.sender.first_name} {msg.sender.last_name}",
                        'email': msg.sender.email
                    },
                    'recipient': {
                        'id': str(msg.recipient.id),
                        'name': f"{msg.recipient.first_name} {msg.recipient.last_name}",
                        'email': msg.recipient.email
                    } if msg.recipient else None,
                    'is_group_message': msg.is_group_message,
                    'message': msg.message,
                    'attachments': msg.attachments,
                    'read_at': msg.read_at.isoformat() if msg.read_at else None,
                    'created_at': msg.created_at.isoformat()
                })
            
            return Response({'messages': messages_data})
        
        except Exception as e:
            logger.error(f"Get peer messages error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    else:  # POST
        try:
            cohort_id = request.data.get('cohort_id')
            recipient_id = request.data.get('recipient_id')
            message = request.data.get('message')
            is_group = request.data.get('is_group_message', False)
            
            if not cohort_id or not message:
                return Response(
                    {'error': 'cohort_id and message are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify enrollment
            try:
                enrollment = Enrollment.objects.get(
                    cohort_id=cohort_id,
                    user=request.user
                )
            except Enrollment.DoesNotExist:
                return Response(
                    {'error': 'Not enrolled in this cohort'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Create message
            msg = CohortPeerMessage.objects.create(
                cohort_id=cohort_id,
                sender=request.user,
                recipient_id=recipient_id if not is_group else None,
                is_group_message=is_group,
                message=message
            )
            
            return Response({
                'id': str(msg.id),
                'message': 'Message sent successfully',
                'created_at': msg.created_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Send peer message error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def mentor_messages(request):
    """
    GET /api/v1/cohorts/messages/mentors?cohort_id=uuid
    POST /api/v1/cohorts/messages/mentors
    
    Get or send mentor messages.
    """
    if request.method == 'GET':
        try:
            cohort_id = request.query_params.get('cohort_id')
            
            if not cohort_id:
                return Response(
                    {'error': 'cohort_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify enrollment
            try:
                enrollment = Enrollment.objects.get(
                    cohort_id=cohort_id,
                    user=request.user
                )
            except Enrollment.DoesNotExist:
                return Response(
                    {'error': 'Not enrolled in this cohort'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get messages
            messages = CohortMentorMessage.objects.filter(
                cohort_id=cohort_id,
                student=request.user
            ).select_related('mentor').order_by('-created_at')
            
            messages_data = []
            for msg in messages:
                messages_data.append({
                    'id': str(msg.id),
                    'mentor': {
                        'id': str(msg.mentor.id),
                        'name': f"{msg.mentor.first_name} {msg.mentor.last_name}",
                        'email': msg.mentor.email
                    },
                    'subject': msg.subject,
                    'message': msg.message,
                    'reply_message': msg.reply_message,
                    'is_read': msg.is_read,
                    'replied_at': msg.replied_at.isoformat() if msg.replied_at else None,
                    'created_at': msg.created_at.isoformat()
                })
            
            return Response({'messages': messages_data})
        
        except Exception as e:
            logger.error(f"Get mentor messages error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    else:  # POST
        try:
            cohort_id = request.data.get('cohort_id')
            mentor_id = request.data.get('mentor_id')
            subject = request.data.get('subject')
            message = request.data.get('message')
            
            if not all([cohort_id, mentor_id, subject, message]):
                return Response(
                    {'error': 'cohort_id, mentor_id, subject, and message are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify enrollment
            try:
                enrollment = Enrollment.objects.get(
                    cohort_id=cohort_id,
                    user=request.user
                )
            except Enrollment.DoesNotExist:
                return Response(
                    {'error': 'Not enrolled in this cohort'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Create message
            msg = CohortMentorMessage.objects.create(
                cohort_id=cohort_id,
                student=request.user,
                mentor_id=mentor_id,
                subject=subject,
                message=message
            )
            
            return Response({
                'id': str(msg.id),
                'message': 'Message sent to mentor successfully',
                'created_at': msg.created_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Send mentor message error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cohort_peers(request):
    """
    GET /api/v1/cohorts/peers?cohort_id=uuid
    
    Get list of peers in cohort.
    """
    try:
        cohort_id = request.query_params.get('cohort_id')
        
        if not cohort_id:
            return Response(
                {'error': 'cohort_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify enrollment
        try:
            enrollment = Enrollment.objects.get(
                cohort_id=cohort_id,
                user=request.user
            )
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this cohort'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get peers
        peers = Enrollment.objects.filter(
            cohort_id=cohort_id,
            status='active'
        ).exclude(user=request.user).select_related('user')
        
        peers_data = []
        for peer in peers:
            peers_data.append({
                'id': str(peer.user.id),
                'name': f"{peer.user.first_name} {peer.user.last_name}",
                'email': peer.user.email,
                'track': peer.track_key
            })
        
        return Response({'peers': peers_data})
    
    except Exception as e:
        logger.error(f"Get peers error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
