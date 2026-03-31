"""
VyapaarBandhu — BART Zero-Shot Classifier (Layer 2)
Local inference using facebook/bart-large-mnli.
No API calls, no rate limits, no cost.
"""

import structlog

from app.config import settings
from app.services.classification.categories import (
    BART_CANDIDATE_LABELS,
    BART_LABEL_MAP,
    ClassificationResult,
)

logger = structlog.get_logger()

# Lazy-loaded pipeline (heavy — ~1.6GB model)
_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        from transformers import pipeline
        _classifier = pipeline(
            "zero-shot-classification",
            model=settings.BART_MODEL_ID,
            device=-1,  # CPU
        )
        logger.info("classification.bart.loaded", model=settings.BART_MODEL_ID)
    return _classifier


async def classify(description: str) -> ClassificationResult:
    """
    Layer 2: BART zero-shot classification.
    Runs locally — no API calls.
    Accepts if confidence >= BART_CONFIDENCE_THRESHOLD (0.75).
    """
    try:
        classifier = _get_classifier()
        result = classifier(
            description,
            candidate_labels=BART_CANDIDATE_LABELS,
            multi_label=False,
        )

        top_label = result["labels"][0]
        top_score = result["scores"][0]
        category = BART_LABEL_MAP.get(top_label, "unknown")

        logger.info(
            "classification.bart.result",
            description=description[:60],
            label=top_label,
            category=category,
            confidence=round(top_score, 4),
        )

        return ClassificationResult(
            category=category,
            method="bart",
            confidence=round(top_score, 4),
            needs_ca_review=(top_score < settings.BART_CONFIDENCE_THRESHOLD),
        )

    except Exception as e:
        logger.warning("classification.bart.failed", error=str(e))
        return ClassificationResult(
            category="unknown", method="bart", confidence=0.0, needs_ca_review=True
        )
