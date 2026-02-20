import os
import asyncio
import random
from loguru import logger
from playwright.async_api import async_playwright

from ai_agent import AIAgent
from google_sheets_client import GoogleSheetClient
from scrapers.config import ScraperConfig
from scrapers.justjoinit_scraper import JustJoinItScraper
from scrapers.pracuj_scraper import PracujScraper
from telegram_bot import send_telegram_alert

async def run_scraper(scraper_class, urls, config):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=[
            "--disable-blink-features=AutomationControlled",
            "--use-fake-ui-for-media-stream",
            "--window-position=0,0"
        ])
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="pl-PL",
            java_script_enabled=False,
        )
        await context.tracing.start(screenshots=True, snapshots=True, sources=True)
        
        page = await context.new_page()

        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        scraper = scraper_class(context, browser, 2)
        scraper.page = page
        await scraper.setup_network_interception()
        
        try:
            await scraper.search(config.search_keywords)
            # await scraper.accept_cookies()
            found_jobs = await scraper.extract_job_data(urls)
            return found_jobs
        except Exception as e:
            logger.error(f"💥 Błąd krytyczny w {scraper_class.__name__}: {e}")
            return []
        finally:
            logger.info(f"💾 Próba zapisu Trace Viewera dla {scraper_class.__name__}...")
            try:
                await context.tracing.stop(path=f"trace_{scraper_class.__name__}.zip")
                logger.success(f"✅ Trace zapisany: trace_{scraper_class.__name__}.zip")
            except Exception as trace_err:
                logger.error(f"❌ Nie udało się zapisać śladu: {trace_err}")
                
            await browser.close()

async def main():
    config = ScraperConfig.from_env()
    gc = GoogleSheetClient(config.credentials_path)
    gc.open_spreadsheet(config.spreadsheet_name)
    
    # Inicjalizacja Agenta AI
    # agent = AIAgent("Bartosz_Debinski_Test_Automation_Engineer.pdf")
    
    # collect offers
    logger.info("Start collecting offers...")
    worksheet = gc.spreadsheet.get_worksheet(0)
    pracuj_urls = worksheet.col_values(6)
    worksheet = gc.spreadsheet.get_worksheet(1)
    justjoinit_urls = worksheet.col_values(6)
    tasks = [
        run_scraper(PracujScraper, pracuj_urls, config),
        run_scraper(JustJoinItScraper, justjoinit_urls, config)
    ]
    jobs = await asyncio.gather(*tasks)
    for i, job_list in enumerate(jobs):
        columns = ["employer", "position", "salary", "requirements", "description", "url",
                    "status"]
        rows = []
        for offer in job_list:
            offer_dict = offer.model_dump()
            row = [offer_dict.get(col, "") for col in columns]
            rows.append(row)

        worksheet = gc.spreadsheet.get_worksheet(i)
        worksheet.insert_rows(rows, 2)
    # try:
    #     # KROK 1: Słowa kluczowe od AI
    #     # dynamic_keywords = await agent.get_search_keywords()
    #     dynamic_keywords = ["Test Automation Engineer"]
    #     logger.info(f"🤖 AI sugeruje szukanie: {dynamic_keywords}")
        
    #     scrapers_config = [
    #         {"class": PracujScraper, "sheet_idx": 0},
    #         {"class": JustJoinItScraper, "sheet_idx": 1}
    #     ]

    #     for keyword in dynamic_keywords:
    #         logger.info(f"🚀 ROZPOCZYNAM SEKWENCJĘ DLA: '{keyword}'")
    #         config.search_keywords = keyword
            
    #         for scraper_info in scrapers_config:
    #             s_class = scraper_info["class"]
    #             s_idx = scraper_info["sheet_idx"]
                
    #             # Pobranie starych URLi z konkretnego arkusza
    #             worksheet = gc.spreadsheet.get_worksheet(s_idx)
    #             existing_urls = worksheet.col_values(5)
                
    #             # KROK 2: Scrapowanie (sekwencyjne)
    #             new_jobs = await run_scraper(s_class, existing_urls, config)
                
    #             if not new_jobs:
    #                 logger.info(f"Brak nowych ofert na {s_class.__name__}")
    #                 continue

    #             # KROK 3: Analiza BATCHOWA (Paczki po 15 ofert)
    #             rows_to_insert = []
    #             batch_size = 15
            
    #         # for i in range(0, len(new_jobs), batch_size):
    #         #     batch = new_jobs[i:i + batch_size]
    #         #     logger.info(f"🧠 AI analizuje paczkę {len(batch)} ofert...")
                
    #         #     # Wysyłamy paczkę do AI (zużywamy 1 zapytanie RPD)
    #         #     batch_results = await agent.evaluate_jobs_batch(batch)
                
    #         #     for idx, job in enumerate(batch):
    #         #         # Pobieramy wynik dla konkretnego ID z paczki
    #         #         analysis = batch_results.get(str(idx), {})
    #         #         score = analysis.get("match_score", 0)
    #         #         reason = analysis.get("reason", "Brak analizy")

    #         #         status_text = f"Wynik: {score}/100 - {reason}"
    #         #         row = [job.employer, job.position, job.salary, job.requirements, job.url, status_text]
    #         #         rows_to_insert.append(row)
                    
    #         #         # KROK 4: Powiadomienie Telegram
    #         #         if score >= 75:
    #         #             await send_telegram_alert(job, analysis)

    #         #     # Krótka pauza, by nie przekroczyć limitu zapytań na minutę (RPM)
    #         #     await asyncio.sleep(5)

    #         if rows_to_insert:
    #             worksheet.insert_rows(rows_to_insert, 2)
    #             logger.success(f"💾 Zapisano {len(rows_to_insert)} ofert do arkusza {s_idx}")

    #         # await asyncio.sleep(random.randint(15, 25))

    # finally:
    #     # Usuwamy CV z serwerów Google po zakończeniu
    #     # agent.cleanup()
    #     pass

if __name__ == "__main__":
    asyncio.run(main())