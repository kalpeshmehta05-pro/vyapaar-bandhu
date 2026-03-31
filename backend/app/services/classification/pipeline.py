"""
VyapaarBandhu — 3-Layer Classification Pipeline
Layer 1: Keyword rules (deterministic, fast, ~400 rules)
Layer 2: BART zero-shot (local inference)
Layer 3: IndicBERT fine-tuned (local inference)

Falls through on low confidence. CA review flagged on uncertainty.
"""

import structlog

from app.config import settings
from app.services.classification.categories import ClassificationResult
from app.services.classification import keyword_rules, bart_classifier, indicbert_classifier

logger = structlog.get_logger()


async def classify_invoice(description: str, amount: float | None = None) -> ClassificationResult:
    """
    3-layer classification pipeline. Falls through on low confidence.

    Layer 1: Keywords — fast, deterministic, confidence >= 0.92 accepted
    Layer 2: BART — zero-shot, confidence >= 0.75 accepted
    Layer 3: IndicBERT — fine-tuned, always returns (flags CA review if < 0.65)
    """
    if not description or len(description.strip()) < 3:
        return ClassificationResult(
            category="unknown",
            method="all_failed",
            confidence=0.0,
            needs_ca_review=True,
        )

    # ── Layer 1: Keyword rules ────────────────────────────────────
    result = keyword_rules.classify(description)
    if result.confidence >= settings.KEYWORD_CONFIDENCE_THRESHOLD:
        logger.info(
            "classification.pipeline.keyword_match",
            category=result.category,
            confidence=result.confidence,
        )
        return result

    # ── Layer 2: BART zero-shot ───────────────────────────────────
    try:
        result = await bart_classifier.classify(description)
        if result.confidence >= settings.BART_CONFIDENCE_THRESHOLD:
            logger.info(
                "classification.pipeline.bart_match",
                category=result.category,
                confidence=result.confidence,
            )
            return result
    except Exception as e:
        logger.warning("classification.pipeline.bart_failed", error=str(e))

    # ── Layer 3: IndicBERT fine-tuned ─────────────────────────────
    try:
        result = await indicbert_classifier.classify(description)
        logger.info(
            "classification.pipeline.indicbert_result",
            category=result.category,
            confidence=result.confidence,
            needs_ca_review=result.needs_ca_review,
        )
        return result
    except Exception as e:
        logger.error("classification.pipeline.indicbert_failed", error=str(e))

    # ── All layers failed ─────────────────────────────────────────
    return ClassificationResult(
        category="unknown",
        method="all_failed",
        confidence=0.0,
        needs_ca_review=True,
    )
