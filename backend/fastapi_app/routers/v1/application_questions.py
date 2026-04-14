"""
FastAPI router for AI-generated application questions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from services.application_questions_service import ApplicationQuestionAIService
from utils.auth import verify_token

router = APIRouter(prefix="/application-questions", tags=["application-questions"])


class QuestionGenerationRequest(BaseModel):
  cohort_id: str = Field(..., description="Cohort UUID from Django")
  cohort_name: str | None = Field(None, description="Optional cohort name for better prompts")
  tracks: list[str] = Field(default_factory=list, description="Track keys or names for this cohort")
  categories: list[str] = Field(
      default_factory=list,
      description="Requested categories: logical, critical, track, behavioral",
  )
  count: int = Field(default=4, ge=1, le=20)


class GeneratedQuestion(BaseModel):
  type: str
  question_text: str
  options: list[str]
  correct_answer: str
  scoring_weight: float


class QuestionGenerationResponse(BaseModel):
  questions: list[GeneratedQuestion]


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

