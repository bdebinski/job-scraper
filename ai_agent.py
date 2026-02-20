import os
import json
from google import genai
from loguru import logger
from scrapers.models import JobOffer
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
        self.cv_file = self.client.files.upload(file=cv_path, config={'display_name': 'CV_Bartek'})
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
        # Używamy wywołań asynchronicznych (.aio) z nowego SDK i szybszego modelu 2.5
        response = await self.client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=[self.cv_file, prompt]
        )
        
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
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
            )

        prompt = f"""
        Przeanalizuj poniższe {len(jobs)} ofert pracy pod kątem mojego CV. 
        Dla każdej oferty (po ID) wystaw ocenę match_score (0-100) oraz krótkie uzasadnienie.
        
        Oferty:
        {offers_to_analyze}
        
        Zwróć wynik WYŁĄCZNIE jako czysty JSON (bez Markdown):
        {{
            "0": {{"match_score": 85, "reason": "Znasz Pythona i Playwright, pasuje."}},
            "1": {{"match_score": 20, "reason": "Wymagają Javy, której nie znasz."}}
        }}
        """

        try:
            # Używamy modelu flash dla szybkości i wyższych limitów darmowych
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=[self.cv_file, prompt]
            )
            
            # Oczyszczanie odpowiedzi z ewentualnych znaczników markdown
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"Błąd analizy batchowej AI: {e}")
            return {}

    def cleanup(self):
        """Sprzątanie po sobie – usuwa plik z serwerów Google"""
        logger.info("Usuwanie pliku CV z serwerów Google...")
        self.client.files.delete(name=self.cv_file.name)
        logger.success("Pamięć Google wyczyszczona.")