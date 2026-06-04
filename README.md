# 🎯 SkillAlign AI (Inteligentny System Rekrutacyjny)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)](https://openai.com/)

Zaawansowana aplikacja typu Proof of Concept (PoC) automatyzująca proces mapowania kompetencji zawodowych. System wykorzystuje duże modele językowe (LLM) do ewaluacji dokumentów CV (PDF) względem ofert pracy (URL), implementując przy tym hybrydowy mechanizm ochrony danych wrażliwych (PII).

## 🚀 Kluczowe funkcjonalności

* **Zaawansowane parsowanie PDF:** Ekstrakcja tekstu z asymetrycznych i wielokolumnowych życiorysów przy użyciu biblioteki `pdfplumber` (zachowanie układu przestrzennego).
* **Security by Design (Anonimizacja PII):** Lokalna pseudonimizacja danych wrażliwych (maile, telefony, linki, nazwiska) przed wysłaniem ich do zewnętrznego API. Wykorzystuje silnik **Microsoft Presidio**, modele **spaCy** oraz system wyrażeń regularnych (Regex).
* **Structured Outputs (Pydantic):** Wymuszenie deterministycznych odpowiedzi w formacie JSON od modeli OpenAI, co eliminuje zjawisko halucynacji schematów.
* **Moduły Premium (AI):**
  * **Upskiller:** Automatyczne generowanie spersonalizowanych ścieżek rozwoju i rekomendacji kursów dla brakujących umiejętności.
  * **Klinika ATS:** Narzędzie do optymalizacji fragmentów CV pod kątem algorytmów Applicant Tracking Systems (ATS).
  * **Cover Letter Generator:** Tworzenie unikalnych listów motywacyjnych metodą "Show, don't tell".
* **FinOps i Observability:** Monitorowanie zużycia tokenów API w czasie rzeczywistym.
* **Persystencja danych:** Zapis historii analiz w relacyjnej bazie **SQLite** przy użyciu **SQLAlchemy** (ORM).

## 🛠️ Stack Technologiczny

* **Język:** Python 3.11+
* **Frontend / UI:** Streamlit
* **AI / LLM:** OpenAI API (`gpt-4o`, `gpt-4o-mini`)
* **Strukturyzacja Danych:** Pydantic
* **NLP & Ochrona Danych:** Microsoft Presidio, spaCy (`pl_core_news_lg`), `re`
* **Przetwarzanie dokumentów i Web Scraping:** pdfplumber, Jina Reader API
* **Baza danych:** SQLite, SQLAlchemy 2.0

## ⚙️ Instalacja i Uruchomienie

**1. Klonowanie repozytorium**
```bash
git clone [https://github.com/TwojUsername/SkillAlign-AI.git](https://github.com/TwojUsername/SkillAlign-AI.git)
cd SkillAlign-AI