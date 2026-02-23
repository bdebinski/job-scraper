import asyncio
from loguru import logger
from playwright.async_api import async_playwright

from ai_agent import AIAgent
from google_sheets_client import GoogleSheetClient
from scrapers.config import ScraperConfig
from scrapers.justjoinit_scraper import JustJoinItScraper
from scrapers.models import JobOfferRecord
from scrapers.pracuj_scraper import PracujScraper
from telegram_bot import send_telegram_alert


async def run_scraper(scraper_class, browser, urls, config):

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

    scraper = scraper_class(page)
    await scraper.setup_network_interception()

    try:
        await scraper.search(config.search_keywords)
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

        await context.close()


async def main():
    config = ScraperConfig.from_env()
    gc = GoogleSheetClient(config)

    # Inicjalizacja Agenta AI
    agent = AIAgent("Bartosz_Debinski_Test_Automation_Engineer.pdf")

    # collect offers
    logger.info("Start collecting offers...")
    worksheet = gc.spreadsheet.get_worksheet(0)
    pracuj_urls = worksheet.col_values(6)
    worksheet = gc.spreadsheet.get_worksheet(1)
    justjoinit_urls = worksheet.col_values(6)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--use-fake-ui-for-media-stream",
                "--window-position=0,0",
            ],
        )
        tasks = [
            run_scraper(PracujScraper, browser, pracuj_urls, config),
            run_scraper(JustJoinItScraper, browser, justjoinit_urls, config),
        ]
        jobs = await asyncio.gather(*tasks)

    # upload offers to google sheet
    for i, job_list in enumerate(jobs):
        columns = [
            "employer",
            "position",
            "salary",
            "requirements",
            "description",
            "url",
            "status",
        ]
        rows = []
        for offer in job_list:
            offer_dict = offer.model_dump()
            row = [offer_dict.get(col, "") for col in columns]
            rows.append(row)

        worksheet = gc.spreadsheet.get_worksheet(i)
        worksheet.insert_rows(rows, 2)

    # send offers to analyze and update googlesheeets after analyze
    jobs_by_sheet: dict[str, list[JobOfferRecord]] = {}
    for sheet in gc.spreadsheet.worksheets():
        records = sheet.get_all_records()
        sheet_name = sheet.title
        jobs_by_sheet[sheet_name] = []
        for idx, row in enumerate(records, start=2):
            if row.get("status") == "TO_ANALYZE":
                try:
                    job_record = JobOfferRecord(row_index=idx, **row)
                    jobs_by_sheet[sheet_name].append(job_record)
                except Exception as e:
                    logger.error(
                        f"Błąd walidacji wiersza {idx} w arkuszu {sheet.title}: {e}"
                    )

    for platform in jobs_by_sheet:
        current_sheet = gc.spreadsheet.worksheet(platform)
        headers = current_sheet.row_values(1)
        try:
            status_col_idx = headers.index("status") + 1
        except ValueError:
            logger.error(f"Nie znaleziono kolumny 'status' w arkuszu {platform}!")
            continue

        batch_size = 15
        if platform == "JustJoinIT":
            pass
        else:
            for i in range(0, len(jobs_by_sheet[platform]), batch_size):
                batch = jobs_by_sheet[platform][i : i + batch_size]
                logger.info(f"🧠 AI analizuje paczkę {len(batch)} ofert...")
                batch_results = await agent.evaluate_jobs_batch(batch)
                for idx, job in enumerate(batch):
                    analysis = batch_results.get(str(idx), {})
                    score = analysis.get("match_score", 0)
                    status_text = f"{score}/100 - {analysis.get('reason')}"
                    logger.info(
                        f"Aktualizacja wiersza {job.row_index} w {platform} (Score: {score})"
                    )

                    current_sheet.update_cell(
                        job.row_index, status_col_idx, status_text
                    )
                    if score >= 75:
                        await send_telegram_alert(job, analysis)

                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
