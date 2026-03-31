"""
VyapaarBandhu — EasyOCR Adapter (Fallback)
Free, open-source, supports Hindi+English natively.
Used when Tesseract confidence is below threshold.
"""

import io
import structlog
from dataclasses import dataclass

from app.services.ocr.tesseract import RawOCRResult

logger = structlog.get_logger()

# Lazy-loaded EasyOCR reader (heavy initialization)
_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en", "hi"], gpu=False)
        logger.info("ocr.easyocr.initialized")
    return _reader


async def easyocr_extract(image_bytes: bytes) -> RawOCRResult:
    """
    Extract text from invoice image using EasyOCR.
    Fallback OCR provider when Tesseract confidence is low.
    """
    try:
        reader = _get_reader()
        results = reader.readtext(image_bytes)

        # results: list of (bbox, text, confidence)
        texts = []
        confidences = []
        for _bbox, text, conf in results:
            texts.append(text)
            confidences.append(conf)

        full_text = "\n".join(texts)
        avg_confidence = (
            sum(confidences) / len(confidences)
            if confidences else 0.0
        )

        logger.info(
            "ocr.easyocr.complete",
            text_length=len(full_text),
            confidence=round(avg_confidence, 4),
            segment_count=len(results),
        )

        return RawOCRResult(
            text=full_text,
            overall_confidence=round(avg_confidence, 4),
            provider="easyocr",
        )

    except Exception as e:
        logger.error("ocr.easyocr.failed", error=str(e))
        raise
