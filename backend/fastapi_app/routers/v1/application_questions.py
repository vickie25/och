"""
FastAPI router for AI-generated application questions.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from utils.auth import verify_token
from services.application_questions_service import ApplicationQuestionAIService


router = APIRouter(prefix="/application-questions", tags=["application-questions"])


class QuestionGenerationRequest(BaseModel):
  cohort_id: str = Field(..., description="Cohort UUID from Django")
  cohort_name: Optional[str] = Field(None, description="Optional cohort name for better prompts")
  tracks: List[str] = Field(default_factory=list, description="Track keys or names for this cohort")
  categories: List[str] = Field(
      default_factory=list,
      description="Requested categories: logical, critical, track, behavioral",
  )
  count: int = Field(default=4, ge=1, le=20)


class GeneratedQuestion(BaseModel):
  type: str
  question_text: str
  options: List[str]
  correct_answer: str
  scoring_weight: float


class QuestionGenerationResponse(BaseModel):
  questions: List[GeneratedQuestion]


@router.post("/generate", response_model=QuestionGenerationResponse)
async def generate_application_questions(
  payload: QuestionGenerationRequest,
  user_id: int = Depends(verify_token),
):
  """
  POST /api/v1/application-questions/generate

  Uses OpenAI (or configured LLM) to generate application questions.
  Requires a valid JWT (same as other FastAPI AI endpoints).
  """
  service = ApplicationQuestionAIService()
  try:
    questions = service.generate_questions(
      cohort_name=payload.cohort_name or "",
      tracks=payload.tracks,
      categories=payload.categories,
      count=payload.count,
    )
  except RuntimeError as e:
    # OpenAI key not configured
    raise HTTPException(
      status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
      detail=str(e),
    )
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to generate questions: {e}",
    )

  return QuestionGenerationResponse(questions=[GeneratedQuestion(**q) for q in questions])

