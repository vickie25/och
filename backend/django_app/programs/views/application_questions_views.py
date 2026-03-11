"""
Application Questions Views - Handle cohort application questions.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_cohort_application_questions(request):
    """
    POST /api/v1/programs/director/application-questions/
    
    Save application questions for a cohort.
    """
    return Response({
        'message': 'Application questions not implemented yet'
    })