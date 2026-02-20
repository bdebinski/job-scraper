import asyncio
from dotenv import load_dotenv
from scrapers.models import JobOffer
from telegram_bot import send_telegram_alert

# Ładujemy tokeny z .env
load_dotenv()

async def run_test():
    print("⏳ Przygotowuję testową ofertę...")
    
    # 1. Sztuczna oferta udająca to, co wypluwa Scraper
    dummy_job = JobOffer(
        employer="Test-Pol S.A.",
        position="Senior Test Automation Engineer (Python)",
        salary="20 000 - 28 000 PLN net/miesiąc (B2B)",
        requirements="Python 3.11, Pytest, Playwright, CI/CD (Azure DevOps), Docker",
        url="https://justjoin.it/"
    )
    
    # 2. Sztuczna ocena udająca odpowiedź z Gemini
    dummy_analysis = {
        "match_score": 95,
        "reason": "Masz wszystko, czego chcą: Pythona, Playwrighta i Azure DevOps. Idealne dopasowanie z Twoim CV!",
        "is_remote": True
    }
    
    print("🚀 Wysyłam powiadomienie na Telegram...")
    # 3. Wywołanie naszej funkcji
    await send_telegram_alert(dummy_job, dummy_analysis)
    print("✅ Skrypt zakończył pracę. Sprawdź telefon!")

if __name__ == "__main__":
    asyncio.run(run_test())