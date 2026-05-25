"""
src/job_reader.py
=================
Fetches job offer content from the web using the Jina Reader API,
which converts any URL into clean, LLM-friendly Markdown text.
"""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

_JINA_PREFIX = "https://r.jina.ai/"
_DEFAULT_TIMEOUT = 30  # seconds


class JobReader:
    """
    Retrieves plain-text (Markdown) content of a job offer page via
    `Jina Reader <https://jina.ai/reader/>`_.

    Jina Reader strips HTML boilerplate and returns a clean Markdown
    representation suitable for direct use as LLM input.

    Parameters
    ----------
    timeout:
        HTTP request timeout in seconds.  Defaults to ``30``.
    """

    def __init__(self, timeout: int = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def fetch_from_url(self, url: str) -> str:
        """
        Fetch and return the Markdown content of a job offer page.

        The URL is forwarded to the Jina Reader API
        (``https://r.jina.ai/<url>``), which renders the page and returns
        clean Markdown.

        Parameters
        ----------
        url:
            Full URL of the job offer page (e.g.
            ``"https://www.pracuj.pl/praca/..."``).

        Returns
        -------
        str
            Markdown text of the page content.

        Raises
        ------
        ValueError
            If *url* is empty.
        RuntimeError
            If the HTTP request fails (network error, non-2xx status, timeout).
        """
        if not url or not url.strip():
            raise ValueError("URL must not be empty.")

        jina_url = f"{_JINA_PREFIX}{url.strip()}"
        logger.info("Fetching job offer via Jina Reader: %s", jina_url)

        try:
            response = requests.get(
                jina_url,
                timeout=self._timeout,
                headers={"Accept": "text/markdown"},
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                f"Request timed out after {self._timeout}s for URL: {url}"
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(
                f"HTTP error {exc.response.status_code} while fetching URL: {url}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Network error while fetching URL '{url}': {exc}"
            ) from exc

        text = response.text.strip()
        logger.info(
            "Fetched %d characters of Markdown content for URL: %s", len(text), url
        )
        return text
