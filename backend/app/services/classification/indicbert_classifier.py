"""
VyapaarBandhu — IndicBERT GST Classifier (Layer 3)
Local inference using meet136/indicbert-gst-classifier.
Fine-tuned on Indian SME transaction descriptions.
"""

import structlog

from app.config import settings
from app.services.classification.categories import ClassificationResult

logger = structlog.get_logger()

# Lazy-loaded pipeline (~440MB model)
_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        from transformers import pipeline
        _classifier = pipeline(
            "text-classification",
            model=settings.INDICBERT_MODEL_ID,
            device=-1,  # CPU
        )
        logger.info("classification.indicbert.loaded", model=settings.INDICBERT_MODEL_ID)
    return _classifier


async def classify(description: str) -> ClassificationResult:
    """
    Layer 3: IndicBERT fine-tuned GST classifier.
    Runs locally — no API calls.
    Flags needs_ca_review if confidence < INDICBERT_CA_REVIEW_THRESHOLD (0.65).
    """
    try:
        classifier = _get_classifier()
        result = classifier(description)

        if result and len(result) > 0:
            top = result[0]
            label = top["label"]
            score = top["score"]

            logger.info(
                "classification.indicbert.result",
                description=description[:60],
                label=label,
                confidence=round(score, 4),
            )

            return ClassificationResult(
                category=label,
                method="indicbert",
                confidence=round(score, 4),
                needs_ca_review=(score < settings.INDICBERT_CA_REVIEW_THRESHOLD),
            )

        return ClassificationResult(
            category="unknown", method="indicbert", confidence=0.0, needs_ca_review=True
        )

    except Exception as e:
        logger.warning("classification.indicbert.failed", error=str(e))
        return ClassificationResult(
            category="unknown", method="indicbert", confidence=0.0, needs_ca_review=True
        )
