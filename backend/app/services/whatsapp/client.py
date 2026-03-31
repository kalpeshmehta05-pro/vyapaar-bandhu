"""
VyapaarBandhu — Meta WhatsApp Cloud API Client
Official API only. Free tier: 1,000 conversations/month.
"""

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()

BASE_URL = f"https://graph.facebook.com/{settings.WA_API_VERSION}"


async def send_text(phone: str, message: str) -> str | None:
    """
    Send a text message via WhatsApp Cloud API.
    Phone must be in E.164 format without +.
    Returns the WhatsApp message ID or None on failure.
    """
    phone_clean = phone.lstrip("+")
    url = f"{BASE_URL}/{settings.WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_clean,
        "type": "text",
        "text": {"body": message},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                msg_id = data.get("messages", [{}])[0].get("id")
                logger.info("whatsapp.message.sent", to_masked=phone_clean[:5] + "XXXXX")
                return msg_id
            else:
                logger.error(
                    "whatsapp.message.failed",
                    status=response.status_code,
                    body=response.text[:200],
                )
                return None
        except Exception as e:
            logger.error("whatsapp.message.error", error=str(e))
            return None


async def download_media(media_id: str) -> bytes | None:
    """
    Download media (image) from WhatsApp Cloud API.
    Two-step: get URL, then download bytes.
    """
    headers = {"Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}"}

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            # Step 1: Get media URL
            url_response = await client.get(
                f"{BASE_URL}/{media_id}", headers=headers
            )
            if url_response.status_code != 200:
                logger.error("whatsapp.media.url_failed", status=url_response.status_code)
                return None

            media_url = url_response.json().get("url")
            if not media_url:
                return None

            # Step 2: Download bytes
            dl_response = await client.get(media_url, headers=headers)
            if dl_response.status_code == 200:
                logger.info("whatsapp.media.downloaded", size=len(dl_response.content))
                return dl_response.content
            else:
                logger.error("whatsapp.media.download_failed", status=dl_response.status_code)
                return None

        except Exception as e:
            logger.error("whatsapp.media.error", error=str(e))
            return None


async def mark_as_read(message_id: str) -> None:
    """Mark a message as read (blue ticks)."""
    url = f"{BASE_URL}/{settings.WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json=payload, headers=headers)
        except Exception:
            pass  # Non-critical
