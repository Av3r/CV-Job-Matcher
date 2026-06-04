"""
src/ats_optimizer.py
====================
ATS optimization assistant — rewrites CV fragments to improve ATS keyword matching.
"""

import os
import logging
from typing import List
from openai import OpenAI
from src.models import ATSReport
from src.utils import load_prompt

logger = logging.getLogger(__name__)

class ATSOptimizer:
    """
    Optimizes CV text for ATS by rewriting selected fragments to include missing keywords.
    """
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Create a .env file with OPENAI_API_KEY=<your-key> and load it "
                "before constructing ATSOptimizer."
            )
        self._model = model
        self._client = OpenAI(api_key=api_key)
        self._ats_prompt = load_prompt("ats")
        self.last_token_count = 0
        logger.info("ATSOptimizer initialized with model=%s", model)

    def optimize(self, safe_cv_text: str, missing_skills: List[str]) -> ATSReport:
        """
        Analyze CV and missing skills, return ATSReport with 3-4 optimized fragments.
        """
        if not safe_cv_text or not missing_skills:
            logger.info("No CV text or missing skills provided — returning empty ATSReport.")
            return ATSReport(korekty=[])

        user_content = (
            "Tekst CV:\n" + safe_cv_text +
            "\nBrakujące wymagania:\n" + "\n".join(f"- {s}" for s in missing_skills)
        )
        try:
            response = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._ats_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format=ATSReport,
            )
        except Exception as exc:
            logger.error(f"OpenAI API call failed: {exc}")
            raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

        self.last_token_count = getattr(getattr(response, "usage", None), "total_tokens", 0)
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError(
                "OpenAI returned a refusal or could not produce a structured response. "
                f"Finish reason: {response.choices[0].finish_reason}"
            )
        logger.info("ATS optimization report generated.")
        return parsed
