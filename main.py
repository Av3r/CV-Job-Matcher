import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ładowanie zmiennych z pliku .env
load_dotenv()

from src.parsers.pdf_parser import CVParser
from src.anonymizer import TextAnonymizer
from src.extractor import DataExtractor

def test_pelnego_potoku(sciezka_pdf: str):
    print("=== URUCHAMIANIE TESTU INTEGRACYJNEGO ===")
    
    # 1. Inicjalizacja komponentów
    print("[1/4] Inicjalizacja parsera, anonimizatora i ekstraktora LLM...")
    parser = CVParser()
    anonymizer = TextAnonymizer()
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("BŁĄD: Brak klucza OPENAI_API_KEY w środowisku! Sprawdź plik .env.")
        return
        
    extractor = DataExtractor()
    
    if not os.path.exists(sciezka_pdf):
        print(f"BŁĄD: Nie znaleziono pliku {sciezka_pdf}. Wrzuć swoje CV do folderu data/ i podaj prawidłową nazwę.")
        return

    # 2. Parsowanie PDF
    print(f"\n[2/4] Wyciąganie tekstu z pliku: {sciezka_pdf}...")
    try:
        wynik_pdf = parser.parse(Path(sciezka_pdf))
        surowy_tekst = wynik_pdf.raw_text
        print(f"-> Pomyślnie sparsowano PDF. Liczba słów: {wynik_pdf.word_count}")
    except Exception as e:
        print(f"BŁĄD parsowania: {e}")
        return

    # 3. Anonimizacja
    print("\n[3/4] Uruchamianie anonimizacji danych (Presidio NLP)...")
    zanonimizowany_tekst = anonymizer.anonymize(surowy_tekst)
    
    print("\n--- PODGLĄD ZANONIMIZOWANEGO TEKSTU (Pierwsze 300 znaków) ---")
    print(zanonimizowany_tekst)#zanonimizowany_tekst[:300])
    print("-----------------------------------------------------------\n")

    # 4. Ekstrakcja danych przez OpenAI
    print("[4/4] Wysyłanie bezpiecznego tekstu do OpenAI (gpt-4o-mini)...")
    try:
        dane_kandydata = extractor.extract_cv(zanonimizowany_tekst)
        
        print("\n=== SUKCES! WYNIK EKSTRAKCJI Z LLM (JSON) ===")
        print(f"Poziom stanowiska: {dane_kandydata.seniority_level}")
        print(f"Lata doświadczenia: {dane_kandydata.lata_doswiadczenia}")
        print(f"Umiejętności twarde: {dane_kandydata.umiejetnosci_twarde}")
        print(f"Umiejętności miękkie: {dane_kandydata.umiejetnosci_miekkie}")
        print(f"Języki : {dane_kandydata.znane_jezyki}")
        
    except Exception as e:
        print(f"BŁĄD podczas ekstrakcji LLM: {e}")

if __name__ == "__main__":
    # Domyślna ścieżka do testów
    plik_do_testu = "data/test_krystyna_hardcore.pdf" 
    
    # Jeśli podasz argument w konsoli, użyje go
    if len(sys.argv) > 1:
        plik_do_testu = sys.argv[1]
        
    test_pelnego_potoku(plik_do_testu)