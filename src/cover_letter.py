"""
src/cover_letter.py
===================
Generator nowoczesnych listów motywacyjnych z użyciem LLM.
"""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

from src.utils import load_prompt

class CoverLetterGenerator:
    """
    Generates a modern cover letter using OpenAI LLM.
    """
    def __init__(self, model: str = "gpt-4o") -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Create a .env file with OPENAI_API_KEY=<your-key> and load it "
                "before constructing CoverLetterGenerator."
            )
        self._model = model
        self._client = OpenAI(api_key=api_key)
        self._cover_letter_prompt = load_prompt("cover_letter")
        self.last_token_count = 0
        logger.info("CoverLetterGenerator initialized with model=%s", model)

    def generate(self, candidate_data_json: str, job_data_json: str) -> str:
        """
        Generate a modern cover letter based on candidate and job data (JSON strings).
        Returns the letter as plain text.
        """
        user_content = (
            "Dane kandydata (JSON):\n" + candidate_data_json +
            "\nDane oferty pracy (JSON):\n" + job_data_json
        )
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._cover_letter_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,
                max_tokens=1200,
            )
        except Exception as exc:
            logger.error(f"OpenAI API call failed: {exc}")
            raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

        self.last_token_count = getattr(getattr(response, "usage", None), "total_tokens", 0)
        letter = response.choices[0].message.content
        if not letter:
            raise RuntimeError("OpenAI did not return a cover letter.")
        logger.info("Cover letter generated.")
        return letter
