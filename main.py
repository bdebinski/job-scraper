import asyncio
import gspread
from loguru import logger
from playwright.async_api import Browser, async_playwright

from scrapers.base_scraper import BaseScraper
from services.ai_agent import AIAgent
from services.google_sheets_client import GoogleSheetClient
from core.config import ScraperConfig
from core.models import JobOffer, JobOfferRecord
from services.telegram_bot import send_telegram_alert


async def run_scraper(
    scraper_class: type[BaseScraper],
    browser: Browser,
    urls_to_skip: list[str],
    config: ScraperConfig,
) -> list[JobOffer]:

    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        locale="pl-PL",
        java_script_enabled=False,
    )
    await context.tracing.start(screenshots=True, snapshots=True, sources=True)

    page = await context.new_page()

    scraper = scraper_class(page)
    await scraper.setup_network_interception()

    try:
        await scraper.search(config.search_keywords)
        found_jobs = await scraper.extract_job_data(urls_to_skip)
        return found_jobs
    except Exception as e:
        logger.error(f"Critical error in {scraper_class.__name__}: {e}")
        return []
    finally:
        logger.info(f"Saving trace viewer for{scraper_class.__name__}...")
        try:
            await context.tracing.stop(path=f"data/trace_{scraper_class.__name__}.zip")
            logger.success(f"Trace saved trace_{scraper_class.__name__}.zip")
        except Exception as trace_err:
            logger.error(f"Can't save trace {trace_err}")

        await context.close()


async def extract_offers(
    config: ScraperConfig, gc: GoogleSheetClient
) -> dict[str, list[JobOffer]]:
    logger.info("Start collecting offers...")
    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--use-fake-ui-for-media-stream",
                "--window-position=0,0",
            ],
        )
        tasks = []
        platforms = []
        for scraper_cls, sheet_name in config.SCRAPER_TO_SHEET.items():
            urls_to_skip = gc.spreadsheet.worksheet(sheet_name).col_values(6)
            task = run_scraper(scraper_cls, browser, urls_to_skip, config)
            tasks.append(task)
            platforms.append(sheet_name)
        scraped_lists = await asyncio.gather(*tasks)

        for sheet_name, offers in zip(platforms, scraped_lists):
            results[sheet_name] = offers

    return results


def upload_scraped_offers(
    gc: GoogleSheetClient, scraped_data: dict[str, list[JobOffer]]
):
    logger.info("Saving offers to google sheets")
    columns = [
        "employer",
        "position",
        "salary",
        "requirements",
        "description",
        "url",
        "status",
    ]

    for platform, offers in scraped_data.items():
        if not offers:
            continue

        rows_to_insert = [
            [offer.model_dump().get(col, "") for col in columns] for offer in offers
        ]

        worksheet = gc.spreadsheet.worksheet(platform)
        worksheet.insert_rows(rows_to_insert, 2)
        logger.success(f"Saved {len(offers)} offers to: {worksheet.title}")


def get_pending_offers(gc: GoogleSheetClient) -> dict[str, list[JobOfferRecord]]:
    logger.info("Searching offers to analyz")
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
                        f"Row validation error {idx} in sheet {sheet.title}: {e}"
                    )
    return jobs_by_sheet


def prepare_sheet_update_payload(
    batch: list[JobOfferRecord], batch_results: dict, col_idx: int
) -> list[dict]:
    cells_to_update = []
    for idx_in_batch, job in enumerate(batch):
        analysis = batch_results.get(str(idx_in_batch), {})
        score = analysis.get("match_score", 0)
        reason = analysis.get("reason", "Analize missing")

        status_text = f"{score}/100 - {reason}"
        cell_address = gspread.utils.rowcol_to_a1(job.row_index, col_idx)
        cells_to_update.append({"range": cell_address, "values": [[status_text]]})
    return cells_to_update


async def analyze_and_update_offers(
    gc: GoogleSheetClient,
    agent: AIAgent,
    pending_offers: dict[str, list[JobOfferRecord]],
):
    batch_size = 15

    for platform, job_list in pending_offers.items():
        if not job_list:
            continue

        current_sheet = gc.spreadsheet.worksheet(platform)
        try:
            status_col_idx = current_sheet.row_values(1).index("status") + 1
        except ValueError:
            logger.error(f"Column status not founnd in {platform}!")
            continue

        for i in range(0, len(job_list), batch_size):
            batch = job_list[i : i + batch_size]
            logger.info(f"AI is analyzing {len(batch)} offers from {platform}...")
            batch_results = await agent.evaluate_jobs_batch(batch)
            for idx_in_batch, job in enumerate(batch):
                analysis = batch_results.get(str(idx_in_batch), {})
                if analysis.get("match_score", 0) >= 75:
                    await send_telegram_alert(job, analysis)
            payload = prepare_sheet_update_payload(batch, batch_results, status_col_idx)
            if payload:
                current_sheet.batch_update(payload)
                logger.success(f"Statuses in spredsheet {platform} updated.")

            await asyncio.sleep(5)


async def main():
    config = ScraperConfig.from_env()
    gc = GoogleSheetClient(config)
    agent = AIAgent("data/Bartosz_Debinski_Test_Automation_Engineer.pdf")
    print(config.search_keywords)
    try:
        jobs = await extract_offers(config, gc)
        upload_scraped_offers(gc, jobs)

        pending_offers = get_pending_offers(gc)
        await analyze_and_update_offers(gc, agent, pending_offers)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
    finally:
        agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
