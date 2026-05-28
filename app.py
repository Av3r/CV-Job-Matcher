import os
import tempfile
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Importy komponentów AI
from src.parsers.pdf_parser import CVParser
from src.anonymizer import TextAnonymizer
from src.extractor import DataExtractor
from src.job_reader import JobReader
from src.matcher import SkillMatcher
from src.upskiller import UpskillAssistant  # NOWY IMPORT

# Importy bazy danych
from src.database import init_db, save_match_record, get_all_records

st.set_page_config(page_title="SkillAlign AI", page_icon="🎯", layout="wide")

@st.cache_resource
def load_components():
    init_db()
    return {
        "parser": CVParser(),
        "anonymizer": TextAnonymizer(),
        "extractor": DataExtractor(),
        "job_reader": JobReader(),
        "matcher": SkillMatcher(),
        "upskiller": UpskillAssistant()  # INICJALIZACJA MODUŁU
    }

components = load_components()

# --- INICJALIZACJA PAMIĘCI SESJI (SESSION STATE) ---
if "report" not in st.session_state:
    st.session_state.report = None
if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = None
if "job_data" not in st.session_state:
    st.session_state.job_data = None
if "safe_cv_text" not in st.session_state:
    st.session_state.safe_cv_text = None
if "upskill_plan" not in st.session_state:
    st.session_state.upskill_plan = None

st.title("🎯 SkillAlign AI")
st.markdown("Inteligentny Asystent Rekrutacji i Analizy Kompetencji")

with st.sidebar:
    st.header("⚙️ Ustawienia")
    api_key = st.text_input("Klucz OpenAI API", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        
    st.divider()
    st.header("📄 Wgraj CV Kandydata")
    uploaded_file = st.file_uploader("Wybierz plik PDF", type="pdf")

tab1, tab2 = st.tabs(["🚀 Nowa Analiza", "📚 Historia Aplikacji"])

# ==========================================
# ZAKŁADKA 1: NOWA ANALIZA
# ==========================================
with tab1:
    job_url = st.text_input("Wklej link do oferty pracy (np. z JustJoin.it)")

    if st.button("🚀 Przeprowadź Analizę Dopasowania", type="primary", use_container_width=True):
        if not os.environ.get("OPENAI_API_KEY"):
            st.error("Błąd: Wprowadź klucz OpenAI API w pasku bocznym!")
            st.stop()
            
        if not uploaded_file or not job_url:
            st.warning("Błąd: Wgraj plik CV i podaj link do oferty pracy!")
            st.stop()

        status_text = st.empty()
        progress_bar = st.progress(0)

        # Resetujemy plan nauki z poprzednich analiz
        st.session_state.upskill_plan = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_pdf_path = tmp_file.name

            status_text.info("⏳ Odczytywanie i anonimizacja CV...")
            parsed_cv = components["parser"].parse(Path(tmp_pdf_path))
            st.session_state.safe_cv_text = components["anonymizer"].anonymize(parsed_cv.raw_text)
            progress_bar.progress(25)

            status_text.info("🧠 AI analizuje kompetencje kandydata...")
            st.session_state.candidate_data = components["extractor"].extract_cv(st.session_state.safe_cv_text)
            progress_bar.progress(50)

            status_text.info("🌐 Pobieranie i analiza wymagań z oferty...")
            raw_job_text = components["job_reader"].fetch_from_url(job_url)
            st.session_state.job_data = components["extractor"].extract_job_offer(raw_job_text)
            progress_bar.progress(75)

            status_text.info("🔥 Generowanie Raportu Dopasowania...")
            st.session_state.report = components["matcher"].compare(st.session_state.candidate_data, st.session_state.job_data)
            
            status_text.info("💾 Zapisywanie wyników w bazie...")
            save_match_record(
                job_url=job_url,
                match_score=st.session_state.report.procent_dopasowania,
                candidate_json=st.session_state.candidate_data.model_dump_json(),
                job_json=st.session_state.job_data.model_dump_json(),
                report_json=st.session_state.report.model_dump_json()
            )
            
            progress_bar.progress(100)
            status_text.success("✅ Analiza zakończona!")
            os.unlink(tmp_pdf_path)

        except Exception as e:
            st.error(f"Wystąpił błąd w potoku: {e}")
            st.stop()

    # Wyświetlanie wyników z pamięci sesji (dzięki temu nie znikną po kliknięciu innych przycisków)
    if st.session_state.report:
        report = st.session_state.report
        st.divider()
        st.metric(label="Match Score (Procent Dopasowania)", value=f"{report.procent_dopasowania}%")

        col1, col2 = st.columns(2)
        with col1:
            st.success("🟢 Spełnione Wymagania")
            for req in report.spelnione_wymagania:
                st.write(f"- {req}")
        
        with col2:
            st.error("🔴 Brakujące Kompetencje")
            if not report.brakujace_wymagania:
                st.write("Brak!")
            else:
                for missing in report.brakujace_wymagania:
                    st.write(f"- {missing}")
                
                # Przycisk do wygenerowania materiałów edukacyjnych (Lazy Loading)
                st.markdown("---")
                if st.button("📚 Wygeneruj materiały do nauki brakujących technologii"):
                    with st.spinner("Szukam odpowiednich kursów i dokumentacji..."):
                        try:
                            st.session_state.upskill_plan = components["upskiller"].generate_plan(report.brakujace_wymagania)
                        except Exception as e:
                            st.error(f"Błąd generatora: {e}")

        # Sekcja wyświetlania wygenerowanego planu
        if st.session_state.upskill_plan:
            st.info("🎓 Twój Spersonalizowany Plan Rozwoju")
            for skill in st.session_state.upskill_plan.plan_nauki:
                with st.expander(f"🛠 Umiejętność: {skill.nazwa_umiejetnosci}"):
                    for mat in skill.materialy:
                        st.markdown(f"- **[{mat.typ_materialu}]** [{mat.tytul}]({mat.url})")

        st.info("💡 Rekomendacje dla Kandydata")
        for rec in report.rekomendacje_zmian_w_cv:
            st.write(f"> {rec}")

# ==========================================
# ZAKŁADKA 2: HISTORIA
# ==========================================
with tab2:
    st.header("Zapisane Analizy")
    st.markdown("Odśwież stronę (Ctrl+R) po wykonaniu nowej analizy, aby zaktualizować listę.")
    records = get_all_records()
    if not records:
        st.info("Brak historii.")
    else:
        import json
        for record in records:
            with st.expander(f"Wynik: {record.match_score}% | {record.created_at.strftime('%Y-%m-%d %H:%M')} | Oferta: {record.job_url[:50]}..."):
                st.write(f"**Pełny link:** {record.job_url}")
                tab_a, tab_b, tab_c = st.tabs(["Raport AI", "Zrozumiane CV", "Zrozumiana Oferta"])
                with tab_a: st.json(json.loads(record.report_json))
                with tab_b: st.json(json.loads(record.candidate_data_json))
                with tab_c: st.json(json.loads(record.job_data_json))