"""
VyapaarBandhu — Tesseract 5 OCR Adapter (Primary)
Free, open-source, runs locally. Supports English + Hindi.
"""

import io
import structlog
from dataclasses import dataclass

from PIL import Image

from app.config import settings

logger = structlog.get_logger()


@dataclass
class RawOCRResult:
    text: str
    overall_confidence: float  # 0.0 to 1.0
    provider: str = "tesseract"


async def tesseract_extract(image_bytes: bytes) -> RawOCRResult:
    """
    Extract text from invoice image using Tesseract 5.
    Configured for English + Hindi (Indian invoices).
    Returns raw text + confidence score.
    """
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Get detailed data with confidence scores
        data = pytesseract.image_to_data(
            img, lang="eng+hin", output_type=pytesseract.Output.DICT
        )

        # Extract text
        text = pytesseract.image_to_string(img, lang="eng+hin")

        # Calculate average confidence (excluding -1 which means no text detected)
        confidences = [
            int(c) for c in data["conf"] if int(c) >= 0
        ]
        avg_confidence = (
            sum(confidences) / len(confidences) / 100.0
            if confidences else 0.0
        )

        logger.info(
            "ocr.tesseract.complete",
            text_length=len(text),
            confidence=round(avg_confidence, 4),
            word_count=len([w for w in data["text"] if w.strip()]),
        )

        return RawOCRResult(
            text=text,
            overall_confidence=round(avg_confidence, 4),
            provider="tesseract",
        )

    except Exception as e:
        logger.error("ocr.tesseract.failed", error=str(e))
        raise
