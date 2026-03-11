"""
Public Assessment Views - Handle public application tests.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def get_public_assessment(request):
    """
    GET /api/v1/programs/public/assessment/
    
    Get public assessment questions (no auth required).
    """
    return Response({
        'message': 'Public assessment not implemented yet',
        'questions': []
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_public_assessment(request):
    """
    POST /api/v1/programs/public/assessment/submit/
    
    Submit public assessment answers (no auth required).
    """
    return Response({
        'message': 'Assessment submission not implemented yet',
        'score': 0
    })