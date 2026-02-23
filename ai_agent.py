import os
import json
from google import genai
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


class AIAgent:
    def __init__(self, cv_path: str):
        # Nowy, oficjalny klient SDK dla Google GenAI
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        if not os.path.exists(cv_path):
            raise FileNotFoundError(f"Nie znaleziono pliku CV: {cv_path}")

        logger.info(f"Wgrywam plik CV do Google (Nowe API): {cv_path}")
        # Wgrywamy plik raz na starcie aplikacji
        self.cv_file = self.client.files.upload(
            file=cv_path, config={"display_name": "CV_Bartek"}
        )
        logger.success("CV załadowane pomyślnie! Mózg operacji gotowy.")

    async def get_search_keywords(self) -> list:
        """Generuje frazy wyszukiwania na podstawie CV"""
        prompt = """
        Jesteś moim osobistym doradcą zawodowym. Przeanalizuj moje CV i wygeneruj 
        dokładnie 3 KRÓTKIE, standardowe frazy kluczowe (max 2-3 słowa każda) do wyszukiwarki portali pracy (np. JustJoin.it, Pracuj.pl). 
        Muszą to być popularne nazwy stanowisk, których używa HR. Unikaj długich, specyficznych zdań.
        Celuj w moje mocne strony, ale skup się na QA i stanowiskach testerskich: automatyzacja w Pythonie, backend, SDET.
        
        Zwróć TYLKO czysty JSON: {"keywords": ["fraza1", "fraza2", "fraza3"]}
        """
        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=[self.cv_file, prompt]
        )
        raw_text = response.text or ""
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)["keywords"]

    async def evaluate_jobs_batch(self, jobs: list) -> dict:
        """Ocenia paczkę ofert w jednym zapytaniu (oszczędność limitu RPD)."""
        if not jobs:
            return {}

        # Przygotowanie tekstu z ofertami do promptu
        offers_to_analyze = ""
        for i, job in enumerate(jobs):
            offers_to_analyze += (
                f"\nID: {i}\n"
                f"Firma: {job.employer}\n"
                f"Stanowisko: {job.position}\n"
                f"Wymagania: {job.requirements}\n"
                f"Opis: {job.description}"
            )

        prompt = f"""
        Przeanalizuj poniższe {len(jobs)} ofert pracy pod kątem mojego CV. 

        Twoim zadaniem jest ocena dopasowania oraz wskazanie konkretnych kroków, które zwiększą szanse na zdobycie danej pracy. Przy wystawianiu "match_score" (0-100) weź pod uwagę:
        1. Skille i ich transferowalność: Jeśli nie znam technologii X, ale znam bardzo podobną technologię Y (np. Selenium -> Playwright, React -> Vue), potraktuj to jako wysoki potencjał i uwzględnij to w ocenie.
        2. Doświadczenie i Seniority: Zgodność lat pracy oraz poziomu odpowiedzialności.
        3. Kontekst projektów: Czy moje projekty rozwiązują problemy podobne do tych w ogłoszeniu?

        Dla każdej oferty zwróć:
        - "match_score": liczba 0-100.
        - "reason": krótkie uzasadnienie (skille + doświadczenie + projekty).
        - "cv_optimization": co konkretnie zmienić lub uwypuklić w opisie moich projektów, aby lepiej "klikały" z tą ofertą.
        - "quick_wins": lista 1-2 technologii/pojęć, których mogę się nauczyć w weekend (mając moją bazę), aby zamknąć lukę w wymaganiach.

        Zwróć wynik WYŁĄCZNIE jako czysty JSON (bez Markdown i zbędnego tekstu):
        {{
            "ID_OFERTY": {{
                "match_score": 85,
                "reason": "Masz mocny stack w Pythonie i doświadczenie w dużych systemach, co pasuje do profilu firmy.",
                "cv_optimization": "W projekcie 'X' podkreśl użycie asynchroniczności, bo oferta kładzie na to nacisk.",
                "quick_wins": "Naucz się podstaw Playwright (znasz Selenium, więc zajmie Ci to 2h) oraz poznaj podstawy AWS Lambda."
            }}
        }}

        Oferty do analizy:
        {offers_to_analyze}
        """

        try:
            # Używamy modelu flash dla szybkości i wyższych limitów darmowych
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash", contents=[self.cv_file, prompt]
            )

            # Oczyszczanie odpowiedzi z ewentualnych znaczników markdown
            raw_text = response.text or ""
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"Błąd analizy batchowej AI: {e}")
            return {}

    def cleanup(self):
        """Sprzątanie po sobie – usuwa plik z serwerów Google"""
        logger.info("Usuwanie pliku CV z serwerów Google...")
        self.client.files.delete(name=self.cv_file.name)
        logger.success("Pamięć Google wyczyszczona.")
