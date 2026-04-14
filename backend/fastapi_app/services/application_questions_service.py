"""
AI-powered application question generation service.
Uses OpenAI via the new client (same pattern as GPTProfilerService).
"""
import json
import os
from typing import Any

from openai import OpenAI


class ApplicationQuestionAIService:
    """
    Generate logical, critical thinking, track-based, and behavioral questions
    for application tests, using an LLM.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("CHAT_GPT_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def _ensure_client(self) -> bool:
        return bool(self.api_key and self.client)

    def generate_questions(
        self,
        cohort_name: str,
        tracks: list[str],
        categories: list[str],
        count: int = 4,
    ) -> list[dict[str, Any]]:
        """
        Ask GPT to synthesize application questions.

        Returns a list of:
          { "type": "mcq|scenario|behavioral",
            "question_text": "...",
            "options": [...],        # for MCQ
            "correct_answer": "...", # optional
            "scoring_weight": 1.0 }
        """
        if not self._ensure_client():
            # If no API key is configured, fail loudly so we don't fake AI.
            raise RuntimeError("OpenAI API key not configured for ApplicationQuestionAIService")

        # Normalize categories
        cats = [c.lower() for c in (categories or [])]
        if not cats:
            cats = ["logical", "critical", "track", "behavioral"]

        # Build prompt
        tracks_text = ", ".join(tracks) if tracks else "general cybersecurity"
        categories_text = ", ".join(cats)

        system_msg = (
            "You are an expert cybersecurity admissions assessor. "
            "You design application test questions that are challenging but fair."
        )
        user_msg = f"""
Generate {count} application test questions for the cohort "{cohort_name or 'Unnamed Cohort'}"
in the tracks: {tracks_text}.

Question categories to include: {categories_text}.

Requirements:
- Mix of MCQ, scenario, and behavioral questions.
- For MCQ questions, provide 3-5 answer options and specify correct_answer.
- For scenario/behavioral questions, do NOT provide options; leave options as an empty list and correct_answer as an empty string.
- scoring_weight should be a float between 0.8 and 1.5 depending on difficulty.

Return STRICTLY valid JSON with a top-level key "questions" as a list of objects,
each with: type, question_text, options, correct_answer, scoring_weight.
"""

        resp = self.client.chat.completions.create(
            model=os.getenv("AI_COACH_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.8,
            max_tokens=1200,
        )

        content = resp.choices[0].message.content or ""
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to recover JSON inside markdown or text
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                data = json.loads(content[start : end + 1])
            else:
                raise

        questions = data.get("questions") or []
        result: list[dict[str, Any]] = []
        for q in questions:
            qtype = (q.get("type") or "mcq").lower()
            if qtype not in ("mcq", "scenario", "behavioral"):
                qtype = "mcq"
            options = q.get("options") or []
            if not isinstance(options, list):
                options = []
            scoring_weight = q.get("scoring_weight") or 1.0
            try:
                scoring_weight = float(scoring_weight)
            except (TypeError, ValueError):
                scoring_weight = 1.0
            result.append(
                {
                    "type": qtype,
                    "question_text": q.get("question_text") or "",
                    "options": options,
                    "correct_answer": q.get("correct_answer") or "",
                    "scoring_weight": scoring_weight,
                }
            )
        return result

