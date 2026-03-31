"""
VyapaarBandhu — OCR Pipeline Orchestrator
Primary: Tesseract 5 | Fallback: EasyOCR
Post-processing: field extraction + GSTIN validation
"""

import structlog
from dataclasses import dataclass

from app.config import settings
from app.services.ocr.tesseract import tesseract_extract, RawOCRResult
from app.services.ocr.easyocr_adapter import easyocr_extract
from app.services.ocr.field_extractor import extract_fields_from_raw, ExtractedFields
from app.services.ocr.gstin_validator import validate_and_correct_gstin

logger = structlog.get_logger()


class LowConfidenceError(Exception):
    pass


@dataclass
class OCRResult:
    fields: ExtractedFields
    confidence_score: float
    confidence_level: str  # "green" | "amber" | "red"
    provider: str
    requires_mandatory_ca_review: bool
    raw_text_length: int = 0


async def process_invoice_image(image_bytes: bytes, image_s3_key: str) -> OCRResult:
    """
    Process an invoice image through the OCR pipeline.

    1. Primary: Tesseract 5
    2. Fallback: EasyOCR (if Tesseract confidence < 0.50)
    3. Field extraction (regex + heuristics)
    4. GSTIN validation + auto-correction
    5. Confidence classification

    Returns OCRResult with extracted fields, confidence, and provider.
    """

    # Step 1: Primary OCR (Tesseract)
    raw_result: RawOCRResult | None = None
    provider = "tesseract"

    try:
        raw_result = await tesseract_extract(image_bytes)
        if raw_result.overall_confidence < settings.OCR_FALLBACK_THRESHOLD:
            logger.warning(
                "ocr.tesseract.low_confidence",
                confidence=raw_result.overall_confidence,
                threshold=settings.OCR_FALLBACK_THRESHOLD,
            )
            raise LowConfidenceError(raw_result.overall_confidence)
    except (LowConfidenceError, Exception) as e:
        # Step 2: Fallback OCR (EasyOCR)
        logger.info("ocr.fallback.easyocr", reason=str(e))
        try:
            raw_result = await easyocr_extract(image_bytes)
            provider = "easyocr"
        except Exception as fallback_err:
            logger.error("ocr.all_failed", error=str(fallback_err))
            # If both fail, use whatever Tesseract gave us (if anything)
            if raw_result is None:
                raise

    # Step 3: Field extraction
    fields = extract_fields_from_raw(raw_result.text)

    # Step 4: GSTIN validation + auto-correction
    if fields.seller_gstin:
        correction = validate_and_correct_gstin(fields.seller_gstin)
        if correction.was_corrected:
            fields.gstin_original_ocr = fields.seller_gstin
            fields.seller_gstin = correction.corrected
            fields.gstin_was_autocorrected = True
            logger.info(
                "ocr.gstin.autocorrected",
                original=fields.gstin_original_ocr,
                corrected=fields.seller_gstin,
            )

    # Step 5: Confidence classification
    confidence = raw_result.overall_confidence
    confidence_level = classify_confidence(confidence)

    return OCRResult(
        fields=fields,
        confidence_score=confidence,
        confidence_level=confidence_level,
        provider=provider,
        requires_mandatory_ca_review=(confidence < settings.OCR_CONFIDENCE_THRESHOLD),
        raw_text_length=len(raw_result.text),
    )


def classify_confidence(score: float) -> str:
    """
    Classify OCR confidence into traffic light levels.
    Thresholds set from config (empirical evaluation in Phase 3.12-3.15).
    """
    if score >= settings.OCR_CONFIDENCE_THRESHOLD:
        return "green"  # >= 0.85
    elif score >= settings.OCR_AMBER_THRESHOLD:
        return "amber"  # 0.75 - 0.85
    else:
        return "red"    # < 0.75
