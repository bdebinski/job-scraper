import os
import httpx
from loguru import logger
from scrapers.models import JobOffer


async def send_telegram_alert(job: JobOffer, analysis: dict):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.warning("Brak tokenów Telegrama w .env! Pomijam wysyłkę.")
        return

    score = analysis.get("match_score", 0)
    reason = analysis.get("reason", "Brak uzasadnienia")
    cv_tip = analysis.get("cv_optimization", "Brak wskazówek")
    quick_win = analysis.get("quick_wins", "Brak sugestii")

    # Formatujemy wiadomość w prostym HTML-u dla Telegrama
    text = (
        f"🚀 <b>NOWA OFERTA! (Match: {score}%)</b>\n\n"
        f"🏢 <b>Firma:</b> {job.employer}\n"
        f"💼 <b>Stanowisko:</b> {job.position}\n"
        f"💰 <b>Płaca:</b> {job.salary}\n\n"
        f"🤖 <b>AI Insight:</b>\n<i>{reason}</i>\n\n"
        f"📝 <b>TIP do CV:</b>\n<u>{cv_tip}</u>\n\n"
        f"💡 <b>Weekendowy cel (Quick Win):</b>\n{quick_win}\n\n"
        f"🔗 <a href='{job.url}'>ZOBACZ OGŁOSZENIE</a>"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.success(f"Wysłano powiadomienie Telegram dla: {job.position}")
        except Exception as e:
            logger.error(f"Błąd wysyłania na Telegram: {e}")
