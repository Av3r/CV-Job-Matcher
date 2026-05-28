from fpdf import FPDF
from pathlib import Path

def generuj_cv_junior_data_scientist(sciezka: Path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Anna Nowak", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 5, "Email: anna.nowak@example.com | Tel: +48 111 222 333 | GitHub: github.com/annanowak", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Podsumowanie", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, "Junior Data Scientist z rocznym doswiadczeniem komercyjnym. Pasjonatka analizy danych i uczenia maszynowego. Szukam pierwszej pracy na pelen etat.")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Doswiadczenie Komercyjne", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, "Stazysta Data Analyst - DataTech Sp. z o.o.", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 5, "06.2023 - 09.2023", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, "- Czyszczenie i przygotowywanie danych dla zespolu inzynierow.\n- Budowanie prostych dashboardow w Tableau.\n- Skrypty automatyzujace raportowanie w Pythonie (Pandas, Matplotlib).")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Umiejetnosci", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, "Twarde: Python, R, SQL, Pandas, Scikit-Learn, podstawy NLP, Tableau, Git.\nMiekkie: Szybkie uczenie sie, praca zespolowa, prezentacja wynikow.\nJezyki: Polski (ojczysty), Angielski (C1).")
    
    pdf.output(str(sciezka))
    print(f"Wygenerowano: {sciezka}")

def generuj_cv_senior_frontend(sciezka: Path):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "PIOTR ZIELINSKI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 6, "SENIOR FRONTEND ARCHITECT", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    left_x = 10
    right_x = 90
    
    # LEWA KOLUMNA
    pdf.set_xy(left_x, 40)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(left_x, 8, "Profil", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(left_x, 50)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(75, 5, "Ekspert technologii webowych z 8-letnim stazem. Specjalizuje sie w skalowalnych aplikacjach SPA i architekturze mikro-frontendow.")
    
    pdf.set_xy(left_x, 80)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(left_x, 8, "Kontakt", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(left_x, 90)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(75, 5, "Tel: 987-654-321\nEmail: p.zielinski@dev.pl\nLinkedIn: linkedin.com/in/pzielinski")
    
    pdf.set_xy(left_x, 120)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(left_x, 8, "Tech Stack", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(left_x, 130)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(75, 5, "- JavaScript (ES6+), TypeScript\n- React, Vue.js, Angular\n- Node.js, Express\n- Webpack, Vite\n- Cypress, Jest\n- AWS, Vercel")

    # PRAWA KOLUMNA
    pdf.set_xy(right_x, 40)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(right_x, 8, "Doswiadczenie", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(right_x, 50)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(110, 5, "Senior Frontend Developer - FinTech Global")
    pdf.set_xy(right_x, 55)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(110, 5, "01.2020 - Obecnie")
    pdf.set_xy(right_x, 60)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(110, 5, "Projektowanie architektury nowej bankowosci online. Migracja legacy kodu AngularJS do Reacta. Mentoring zespolu (5 juniorow). Wdrazanie standardow CI/CD.")
    
    pdf.set_xy(right_x, 90)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(110, 5, "Mid Web Developer - E-commerce Solutions")
    pdf.set_xy(right_x, 95)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(110, 5, "03.2016 - 12.2019")
    pdf.set_xy(right_x, 100)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(110, 5, "Tworzenie responsywnych sklepow internetowych. Optymalizacja wydajnosci (Core Web Vitals). Integracja z REST API oraz GraphQL.")

    pdf.set_xy(right_x, 130)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(right_x, 8, "Jezyki", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(right_x, 140)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(110, 5, "Angielski: C2 (Native-like)\nPolski: Ojczysty\nNiemiecki: A2")
    
    pdf.output(str(sciezka))
    print(f"Wygenerowano: {sciezka}")

def generuj_cv_hardcore_tester(sciezka: Path):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 26)
    pdf.cell(0, 12, "KRYSTYNA KOWALCZYK", new_x="LMARGIN", new_y="NEXT", align="R") 
    
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Senior Cloud Data Engineer", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.cell(0, 6, "krystyna.k@data-cloud.pl  |  Tel: 555-111-222  |  github.com/kkowalczyk", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.set_text_color(0, 0, 0)
    
    pdf.line(10, 35, 200, 35)
    
    left_x = 10
    left_w = 60
    right_x = 75
    right_w = 125
    
    pdf.set_xy(left_x, 45)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(left_w, 8, "UMIEJETNOSCI", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", size=9)
    umiejetnosci = [
        ("Python (Data)", "[######]"),
        ("SQL / BigQuery", "[#####-]"),
        ("Apache Spark", "[####--]"),
        ("Docker & K8s", "[#####-]"),
        ("AWS / GCP", "[####--]"),
        ("Terraform", "[###---]"),
    ]
    
    y_pos = 55
    for skill, bar in umiejetnosci:
        pdf.set_xy(left_x, y_pos)
        pdf.cell(30, 5, skill)
        pdf.set_xy(left_x + 35, y_pos)
        pdf.cell(25, 5, bar)
        y_pos += 6

    pdf.set_xy(left_x, y_pos + 10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(left_w, 8, "CERTYFIKATY", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=9)
    pdf.set_xy(left_x, y_pos + 20)
    pdf.multi_cell(left_w, 5, "1. AWS Certified Solutions Architect\n2. GCP Data Engineer\n3. ITIL v4 Foundation")

    pdf.set_xy(right_x, 45)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(right_w, 8, "DOSWIADCZENIE ZAWODOWE", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(right_x, 55)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(right_w, 6, "Glowny Inzynier Danych (Lead Data Engineer)", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(right_x, 61)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(right_w, 5, "FinTech Solutions Sp. z o.o.  |  04.2021 - Obecnie", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(right_x, 68)
    pdf.set_font("Helvetica", size=10)
    opis_1 = (
        "Zarzadzanie architektura hurtowni danych w srodowisku wielochmurowym (AWS + GCP). "
        "Projektowanie zautomatyzowanych potokow ETL wykorzystujacych Apache Airflow oraz PySpark, "
        "co zredukowalo czas przetwarzania o 40%. Wdrazanie modeli Machine Learningowych na produkcje "
        "przy uzyciu MLflow oraz FastAPI. Zarzadzanie infrastruktura jako kodem (IaC) za pomoca Terraform."
    )
    pdf.multi_cell(right_w, 5, opis_1)

    pdf.set_xy(right_x, 100)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(right_w, 6, "Data Engineer / Python Developer", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(right_x, 106)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(right_w, 5, "DataCorp Enterprise  |  08.2017 - 03.2021", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(right_x, 113)
    pdf.set_font("Helvetica", size=10)
    opis_2 = (
        "Rozwoj i utrzymanie systemow raportowych zasilanych z baz PostgreSQL i Oracle. "
        "Tworzenie skryptow w Pythonie do czyszczenia danych (Pandas, NumPy). "
        "Migracja lokalnych baz danych do chmury obliczeniowej. "
        "Wspolpraca w metodologii Scrum (Jira, Confluence)."
    )
    pdf.multi_cell(right_w, 5, opis_2)
    
    pdf.set_xy(10, 260)
    pdf.set_font("Helvetica", size=7)
    pdf.set_text_color(150, 150, 150)
    rodo = "Wyrazam zgode na przetwarzanie moich danych osobowych w celu prowadzenia rekrutacji na aplikowane przeze mnie stanowisko."
    pdf.multi_cell(0, 3, rodo)

    pdf.output(str(sciezka))
    print(f"Wygenerowano HARDCORE STRESS TEST: {sciezka}")

if __name__ == "__main__":
    folder_danych = Path("data")
    folder_danych.mkdir(exist_ok=True)
    
    generuj_cv_junior_data_scientist(folder_danych / "test_anna_junior.pdf")
    generuj_cv_senior_frontend(folder_danych / "test_piotr_senior.pdf")
    generuj_cv_hardcore_tester(folder_danych / "test_krystyna_hardcore.pdf")