"""
Public application test (assessment) – no auth.
Token in query/body links to a CohortPublicApplication via form_data.application_test_token.
MCQ: auto-scored. Scenario and behavioral: graded by AI; report kept for mentor correction.
"""
import json
import logging
import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from programs.models import CohortPublicApplication, CohortApplicationQuestions, ApplicationQuestionBank

logger = logging.getLogger(__name__)


def _grade_scenario_behavioral_with_ai(question_type: str, question_text: str, student_answer: str, max_score: float):
    """
    Grade a single scenario or behavioral answer using OpenAI.
    Returns (score, feedback) where score is 0 to max_score, feedback is a short explanation.
    On failure returns (None, None).
    """
    if not (student_answer and str(student_answer).strip()):
        return (0.0, "No response provided.")
    api_key = os.environ.get('CHAT_GPT_API_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('CHATGPT_API_KEY')
    if not api_key:
        logger.warning("Application test: OpenAI API key not set; skipping AI grading for scenario/behavioral.")
        return (None, None)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = os.environ.get('AI_COACH_MODEL', 'gpt-4o-mini')
        max_score_val = max(0.1, float(max_score))
        system_msg = (
            "You are an expert cybersecurity admissions assessor. Grade the candidate's written response "
            "for a single application test question. Be fair and consistent. Return only valid JSON with two keys: "
            '"score" (number from 0 to max_score, can be decimal) and "feedback" (one or two sentences explaining '
            "why this score was given)."
        )
        user_msg = (
            f"Question type: {question_type}. Max score for this question: {max_score_val}\n\n"
            f"Question: {question_text}\n\n"
            f"Student answer: {student_answer}\n\n"
            "Return JSON: {\"score\": <number 0 to max_score>, \"feedback\": \"<short explanation>\"}"
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        content = (resp.choices[0].message.content or "").strip()
        # Parse JSON (allow wrapped in markdown)
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            content = content[start : end + 1]
        data = json.loads(content)
        score_val = data.get("score")
        feedback_val = data.get("feedback") or ""
        if score_val is not None:
            try:
                score_val = float(score_val)
            except (TypeError, ValueError):
                score_val = None
        if score_val is not None:
            score_val = max(0.0, min(max_score_val, score_val))
        return (score_val, feedback_val if feedback_val else None)
    except Exception as e:
        logger.warning("Application test AI grading failed: %s", e, exc_info=True)
        return (None, None)


def _get_application_by_token(token: str):
    if not (token or str(token).strip()):
        return None
    return CohortPublicApplication.objects.filter(
        form_data__application_test_token=str(token).strip(),
        applicant_type='student',
    ).select_related('cohort').first()


def _run_application_test_grading(app, form_data, answers):
    """Compute per-question and overall score from answers; mutate form_data with application_test_results."""
    try:
        cohort = app.cohort
        config = CohortApplicationQuestions.objects.get(cohort=cohort)
        question_ids = [str(qid) for qid in (config.question_ids or [])]
        bank_qs = list(ApplicationQuestionBank.objects.filter(id__in=question_ids))
        bank_map = {str(q.id): q for q in bank_qs}

        answer_map = {}
        for item in answers:
            if not isinstance(item, dict):
                continue
            qid = str(item.get('question_id') or '').strip()
            if not qid:
                continue
            ans = (item.get('answer') or '').strip()
            answer_map[qid] = ans

        per_question = []
        total_points = 0.0
        total_weight = 0.0

        for qid in question_ids:
            q = bank_map.get(qid)
            if not q:
                continue
            qtype = q.type
            max_score = float(q.scoring_weight or 1.0)
            ans = (answer_map.get(qid) or '').strip()
            score = None
            ai_feedback = None

            if qtype == 'mcq' and q.correct_answer:
                correct = (q.correct_answer or '').strip()
                if ans and ans.lower() == correct.lower():
                    score = max_score
                else:
                    score = 0.0
                total_points += float(score)
                total_weight += max_score

            per_question.append({
                'question_id': qid,
                'type': qtype,
                'question_text': q.question_text,
                'answer': ans,
                'correct_answer': q.correct_answer or '',
                'score': score,
                'max_score': max_score,
                'ai_feedback': ai_feedback,
            })

        # AI-grade scenario and behavioral questions
        for pq in per_question:
            qtype = pq.get('type')
            if qtype not in ('scenario', 'behavioral'):
                continue
            ans = (pq.get('answer') or '').strip()
            max_score = float(pq.get('max_score') or 1.0)
            if not ans:
                pq['score'] = 0.0
                pq['ai_feedback'] = "No response provided."
                total_points += 0.0
                total_weight += max_score
                continue
            score_val, feedback_val = _grade_scenario_behavioral_with_ai(
                qtype, pq.get('question_text') or '', ans, max_score
            )
            if score_val is not None:
                pq['score'] = score_val
                pq['ai_feedback'] = feedback_val
                total_points += score_val
                total_weight += max_score
            else:
                pq['ai_feedback'] = feedback_val or "AI grading unavailable; mentor review recommended."

        overall_score = None
        if total_weight > 0:
            overall_score = float((total_points / total_weight) * 100.0)

        mcq_correct = sum(1 for pq in per_question if pq.get('type') == 'mcq' and pq.get('score') is not None and float(pq.get('score') or 0) > 0)
        mcq_total = sum(1 for pq in per_question if pq.get('type') == 'mcq')
        scenario_behavioral = [pq for pq in per_question if pq.get('type') in ('scenario', 'behavioral')]
        sb_graded = sum(1 for pq in scenario_behavioral if pq.get('score') is not None)
        grade_summary_parts = []
        if mcq_total > 0:
            mcq_pct = (float(mcq_correct) / mcq_total * 100.0) if mcq_total else 0
            grade_summary_parts.append(
                "Multiple-choice: {:.0f}% ({} of {} correct).".format(mcq_pct, mcq_correct, mcq_total)
            )
        if scenario_behavioral:
            if sb_graded == len(scenario_behavioral):
                grade_summary_parts.append(
                    "Scenario and behavioral responses were graded by AI; per-question feedback is in the report below. "
                    "Mentors may correct scores or feedback if needed."
                )
            elif sb_graded > 0:
                grade_summary_parts.append(
                    "Some scenario/behavioral responses were AI-graded; others could not be graded (see report). "
                    "Mentors may correct or complete grading."
                )
            else:
                grade_summary_parts.append(
                    "Scenario and behavioral responses could not be AI-graded (e.g. API unavailable); mentor review recommended."
                )
        grade_summary = " ".join(grade_summary_parts) if grade_summary_parts else "No questions graded."

        form_data['application_test_results'] = {
            'overall_score': overall_score,
            'max_score': 100.0 if overall_score is not None else None,
            'total_points': total_points,
            'total_weight': total_weight,
            'per_question': per_question,
            'grade_summary': grade_summary,
        }
    except CohortApplicationQuestions.DoesNotExist:
        form_data['application_test_results'] = {'overall_score': None, 'per_question': [], 'grade_summary': None}
    except Exception:
        form_data.setdefault('application_test_results', {'overall_score': None, 'per_question': [], 'grade_summary': None})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_public_assessment(request):
    """
    GET /api/v1/public/assessment/?token=xxx
    If the applicant has already completed the test: { completed: true, completed_at }.
    Else: { cohort_name, time_limit_minutes, sections: [{ section_name, time_minutes, questions }], token }.
    Sections: single section for now (whole test).
    """
    token = request.query_params.get('token') or request.query_params.get('t')
    app = _get_application_by_token(token)
    if not app:
        return Response({'error': 'Invalid or expired assessment link.'}, status=status.HTTP_404_NOT_FOUND)

    form_data = app.form_data or {}
    if form_data.get('application_test_completed_at'):
        return Response({
            'completed': True,
            'completed_at': form_data.get('application_test_completed_at'),
            'message': 'You have already completed this assessment.',
        }, status=status.HTTP_200_OK)

    cohort = app.cohort
    try:
        config = CohortApplicationQuestions.objects.get(cohort=cohort)
    except CohortApplicationQuestions.DoesNotExist:
        return Response({'error': 'No assessment is configured for this cohort.'}, status=status.HTTP_404_NOT_FOUND)

    question_ids = [str(qid) for qid in (config.question_ids or [])]
    if not question_ids:
        return Response({'error': 'No questions configured for this assessment.'}, status=status.HTTP_404_NOT_FOUND)

    bank_qs = list(ApplicationQuestionBank.objects.filter(id__in=question_ids))
    bank_map = {str(q.id): q for q in bank_qs}
    questions = []
    for qid in question_ids:
        q = bank_map.get(qid)
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

    time_limit_minutes = getattr(config, 'time_limit_minutes', 60) or 60
    cohort_name = cohort.name if cohort else 'Program'

    return Response({
        'completed': False,
        'token': token,
        'cohort_name': cohort_name,
        'time_limit_minutes': time_limit_minutes,
        'sections': [
            {
                'section_name': 'Assessment',
                'time_minutes': time_limit_minutes,
                'questions': questions,
            }
        ],
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_public_assessment(request):
    """
    POST /api/v1/public/assessment/submit/
    Body: { token: string, answers: [ { question_id: string, answer: string } ] }
    Saves answers to form_data.application_test_answers, sets application_test_completed_at,
    and computes an automatic grade per question (where possible) + overall score.
    """
    token = (request.data.get('token') or request.data.get('t') or '').strip()
    app = _get_application_by_token(token)
    if not app:
        return Response({'error': 'Invalid or expired assessment link.'}, status=status.HTTP_404_NOT_FOUND)

    form_data = app.form_data or {}
    if form_data.get('application_test_completed_at'):
        return Response({
            'success': True,
            'completed': True,
            'message': 'You have already completed this assessment.',
        }, status=status.HTTP_200_OK)

    answers = request.data.get('answers')
    if not isinstance(answers, list):
        answers = []

    # Persist raw answers & completion timestamp
    form_data['application_test_answers'] = answers
    form_data['application_test_completed_at'] = timezone.now().isoformat()

    _run_application_test_grading(app, form_data, answers)

    app.form_data = form_data
    app.save(update_fields=['form_data', 'updated_at'])

    return Response({
        'success': True,
        'completed': True,
        'message': 'Your assessment has been submitted successfully.',
    }, status=status.HTTP_200_OK)
