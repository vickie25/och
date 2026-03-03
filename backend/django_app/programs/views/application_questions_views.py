"""
Director: set application questions per cohort (manual or AI-generated).
Requires application_question_bank and cohort_application_questions tables (run application_questions_grades.sql).
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

from programs.permissions import IsProgramDirector
from programs.models import Cohort, ApplicationQuestionBank, CohortApplicationQuestions


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def save_cohort_application_questions(request):
    """
    GET  /api/v1/director/application-questions/
      -> { cohorts: [{ cohort_id, question_count }] }   (summary)

    GET  /api/v1/director/application-questions/?cohort_id=...
      -> { cohort_id, time_limit_minutes, opens_at, questions: [...] }

    POST /api/v1/director/application-questions/
      Body: { cohort_id, time_limit_minutes, test_date?, questions: [{ type, question_text, options?, correct_answer?, scoring_weight? }] }
      Creates question bank entries and cohort_application_questions config.
    """
    if request.method == 'GET':
        cohort_id = request.query_params.get('cohort_id')
        if not cohort_id:
            # Summary: which cohorts have questions configured
            configs = CohortApplicationQuestions.objects.all().select_related('cohort')
            data = []
            for cfg in configs:
                try:
                    qids = cfg.question_ids or []
                    count = len(qids)
                except TypeError:
                    count = 0
                data.append({
                    'cohort_id': str(getattr(cfg.cohort, 'id', '')),
                    'question_count': count,
                })
            return Response({'cohorts': data}, status=status.HTTP_200_OK)

        cohort = get_object_or_404(Cohort, id=cohort_id)
        try:
            config = CohortApplicationQuestions.objects.get(cohort=cohort)
        except CohortApplicationQuestions.DoesNotExist:
            return Response({'error': 'No questions configured for this cohort'}, status=status.HTTP_404_NOT_FOUND)
        # Fetch questions in the saved order
        question_ids = [str(qid) for qid in (config.question_ids or [])]
        bank_qs = list(ApplicationQuestionBank.objects.filter(id__in=question_ids))
        bank_map = {str(q.id): q for q in bank_qs}
        questions = []
        for qid in question_ids:
            q = bank_map.get(str(qid))
            if not q:
                continue
            questions.append({
                'id': str(q.id),
                'type': q.type,
                'question_text': q.question_text,
                'options': q.options or [],
                'correct_answer': q.correct_answer or '',
                'scoring_weight': float(q.scoring_weight or 1),
            })
        return Response({
            'cohort_id': str(cohort.id),
            'time_limit_minutes': config.time_limit_minutes,
            'opens_at': config.opens_at.isoformat() if config.opens_at else None,
            'questions': questions,
        }, status=status.HTTP_200_OK)

    # POST: save/update configuration
    cohort_id = request.data.get('cohort_id')
    if not cohort_id:
        return Response({'error': 'cohort_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    cohort = get_object_or_404(Cohort, id=cohort_id)
    time_limit_minutes = request.data.get('time_limit_minutes', 60)
    test_date = request.data.get('test_date')
    questions_payload = request.data.get('questions') or []
    if not questions_payload:
        return Response({'error': 'At least one question is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            question_ids = []
            for q in questions_payload:
                qtype = (q.get('type') or 'mcq').lower()
                if qtype not in ('mcq', 'scenario', 'behavioral'):
                    qtype = 'mcq'
                options = q.get('options')
                if options is None and qtype == 'mcq':
                    options = []
                if not isinstance(options, list):
                    options = []
                obj = ApplicationQuestionBank(
                    type=qtype,
                    question_text=(q.get('question_text') or '').strip() or 'Question',
                    options=options,
                    correct_answer=(q.get('correct_answer') or '').strip() or None,
                    scoring_weight=float(q.get('scoring_weight') or 1),
                )
                obj.save()
                question_ids.append(str(obj.id))
            opens_at = None
            if test_date:
                try:
                    from datetime import datetime
                    s = (test_date or '').strip()[:19]
                    if len(s) >= 16 and 'T' in s:
                        opens_at = datetime.strptime(s[:16], '%Y-%m-%dT%H:%M')
                    else:
                        opens_at = datetime.strptime(s[:10], '%Y-%m-%d')
                    if opens_at and timezone.is_naive(opens_at):
                        opens_at = timezone.make_aware(opens_at)
                except Exception:
                    pass
            CohortApplicationQuestions.objects.update_or_create(
                cohort=cohort,
                defaults={
                    'question_ids': question_ids,
                    'time_limit_minutes': int(time_limit_minutes),
                    'opens_at': opens_at,
                },
            )
        return Response({'cohort_id': str(cohort.id), 'question_count': len(question_ids)}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
