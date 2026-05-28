"""
src/upskiller.py
================
LLM-powered upskilling assistant — generates a personalized learning plan for missing skills.
"""

from __future__ import annotations

import os
import logging
from typing import List

from openai import OpenAI
from src.models import UpskillPlan

logger = logging.getLogger(__name__)

_UPSKILL_SYSTEM_PROMPT = """\
Jesteś ekspertem IT i mentorem. Dla każdej podanej brakującej umiejętności wygeneruj po 2 konkretne, darmowe i wysokiej jakości materiały do nauki (rzeczywiste linki do YouTube, oficjalnej dokumentacji, lub platform typu freeCodeCamp). Zwróć dane zgodnie ze strukturą JSON.
"""

class UpskillAssistant:
    """
    Generates an upskilling plan (learning resources) for a list of missing skills using OpenAI LLM.
    """
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Create a .env file with OPENAI_API_KEY=<your-key> and load it "
                "before constructing UpskillAssistant."
            )
        self._model = model
        self._client = OpenAI(api_key=api_key)
        logger.info("UpskillAssistant initialized with model=%s", model)

    def generate_plan(self, missing_skills: List[str]) -> UpskillPlan:
        """
        Generate an upskilling plan for the given missing skills.
        Returns an UpskillPlan with 2 high-quality, free resources per skill.
        If missing_skills is empty, returns an empty plan.
        """
        if not missing_skills:
            logger.info("No missing skills provided — returning empty UpskillPlan.")
            return UpskillPlan(plan_nauki=[])

        user_content = (
            "Brakujące umiejętności:\n" + "\n".join(f"- {s}" for s in missing_skills)
        )
        try:
            response = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": _UPSKILL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format=UpskillPlan,
            )
        except Exception as exc:
            logger.error(f"OpenAI API call failed: {exc}")
            raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError(
                "OpenAI returned a refusal or could not produce a structured response. "
                f"Finish reason: {response.choices[0].finish_reason}"
            )
        logger.info("Upskill plan generated for %d skills.", len(missing_skills))
        return parsed
