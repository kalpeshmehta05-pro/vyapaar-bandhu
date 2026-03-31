"""
VyapaarBandhu — Celery OCR Processing Task
Async OCR + classification + compliance evaluation.
Retries with exponential backoff. Sends result to user via WhatsApp.
"""

import uuid

import structlog
from celery import shared_task

from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=60,
    time_limit=90,
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_invoice_ocr(
    self,
    client_id: str,
    ca_id: str,
    media_id: str,
    whatsapp_message_id: str,
    phone: str,
):
    """
    Process invoice image through OCR + classification + compliance pipeline.
    Runs in Celery worker (not in the API process).

    Steps:
    1. Download image from WhatsApp
    2. Upload to MinIO/S3
    3. Run OCR pipeline (Tesseract + EasyOCR fallback)
    4. Run classification pipeline (keyword + BART + IndicBERT)
    5. Run compliance evaluation
    6. Save invoice to database
    7. Send extracted fields to user via WhatsApp
    """
    import asyncio
    asyncio.run(_process_invoice_async(
        self, client_id, ca_id, media_id, whatsapp_message_id, phone
    ))


async def _process_invoice_async(
    task,
    client_id: str,
    ca_id: str,
    media_id: str,
    whatsapp_message_id: str,
    phone: str,
):
    """Async wrapper for the OCR processing pipeline."""
    from decimal import Decimal
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.db.session import async_session_factory
    from app.models.invoice import Invoice
    from app.models.client import Client
    from app.services.whatsapp import client as wa_client
    from app.services.whatsapp.message_router import set_session
    from app.services.whatsapp.message_templates import MESSAGES
    from app.services.storage.s3_client import upload_invoice_image
    from app.services.ocr.pipeline import process_invoice_image
    from app.services.classification.pipeline import classify_invoice
    from app.services.compliance.engine import (
        evaluate_invoice_itc, InvoiceData, ClientData,
    )
    from app.utils.dedup import compute_dedup_hash

    try:
        # Step 1: Download image from WhatsApp
        image_bytes = await wa_client.download_media(media_id)
        if not image_bytes:
            await wa_client.send_text(phone, MESSAGES["ocr_failed"])
            return

        # Step 2: Upload to S3
        s3_key = await upload_invoice_image(image_bytes, uuid.UUID(client_id))

        # Step 3: OCR pipeline
        ocr_result = await process_invoice_image(image_bytes, s3_key)
        fields = ocr_result.fields

        # Step 4: Classification
        classification = await classify_invoice(
            fields.product_description or "", fields.total_amount
        )

        # Step 5: Compliance evaluation
        async with async_session_factory() as db:
            client_result = await db.execute(
                select(Client).where(Client.id == uuid.UUID(client_id))
            )
            client = client_result.scalar_one_or_none()

            if not client:
                return

            invoice_data = InvoiceData(
                seller_gstin=fields.seller_gstin,
                category=classification.category,
                product_description=fields.product_description,
                taxable_amount=Decimal(str(fields.taxable_amount or 0)),
                cgst_amount=Decimal(str(fields.cgst_amount or 0)),
                sgst_amount=Decimal(str(fields.sgst_amount or 0)),
                igst_amount=Decimal(str(fields.igst_amount or 0)),
                total_amount=Decimal(str(fields.total_amount or 0)),
            )
            client_data = ClientData(
                gstin=client.gstin,
                business_type=client.business_type,
                primary_activity=client.primary_activity,
                is_composition=client.is_composition,
            )
            evaluation = evaluate_invoice_itc(invoice_data, client_data)

            # Step 6: Compute dedup hash
            dedup_hash = compute_dedup_hash(
                fields.seller_gstin, fields.invoice_number, uuid.UUID(client_id)
            )

            # Check for duplicates
            dup_result = await db.execute(
                select(Invoice).where(Invoice.dedup_hash == dedup_hash)
            )
            if dup_result.scalar_one_or_none():
                await wa_client.send_text(
                    phone,
                    MESSAGES["duplicate"].format(invoice_number=fields.invoice_number or "unknown"),
                )
                return

            # Determine status based on confidence
            if ocr_result.confidence_score < 0.85:
                status = "flagged_low_confidence"
            elif classification.needs_ca_review:
                status = "flagged_classification"
            else:
                status = "pending_client_confirmation"

            # Parse date
            invoice_date = None
            if fields.invoice_date:
                try:
                    parts = fields.invoice_date.split("-")
                    if len(parts) == 3:
                        from datetime import date
                        invoice_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
                except (ValueError, IndexError):
                    pass

            # Step 7: Save invoice
            invoice = Invoice(
                client_id=uuid.UUID(client_id),
                ca_id=uuid.UUID(ca_id),
                image_s3_key=s3_key,
                source_type="whatsapp_photo",
                whatsapp_message_id=whatsapp_message_id,
                seller_gstin=fields.seller_gstin,
                seller_name=fields.seller_name,
                invoice_number=fields.invoice_number,
                invoice_date=invoice_date,
                taxable_amount=Decimal(str(fields.taxable_amount or 0)),
                cgst_amount=Decimal(str(fields.cgst_amount or 0)),
                sgst_amount=Decimal(str(fields.sgst_amount or 0)),
                igst_amount=Decimal(str(fields.igst_amount or 0)),
                total_amount=Decimal(str(fields.total_amount or 0)),
                product_description=fields.product_description,
                ocr_confidence_score=Decimal(str(ocr_result.confidence_score)),
                ocr_provider=ocr_result.provider,
                gstin_was_autocorrected=fields.gstin_was_autocorrected,
                gstin_original_ocr=fields.gstin_original_ocr,
                category=classification.category,
                classification_method=classification.method,
                classification_confidence=Decimal(str(classification.confidence)),
                is_itc_eligible_draft=evaluation.is_eligible,
                blocked_reason=evaluation.blocked_reason,
                is_rcm=evaluation.is_rcm,
                rcm_category=evaluation.rcm_category,
                status=status,
                dedup_hash=dedup_hash,
            )
            db.add(invoice)
            await db.commit()
            await db.refresh(invoice)

            # Step 8: Send result to user
            gstin_note = ""
            if fields.gstin_was_autocorrected and fields.gstin_original_ocr:
                gstin_note = MESSAGES["gstin_correction_note"].format(
                    original=fields.gstin_original_ocr
                )

            msg = MESSAGES["ocr_result"].format(
                seller_name=fields.seller_name or "N/A",
                seller_gstin=fields.seller_gstin or "N/A",
                gstin_correction_note=gstin_note,
                invoice_number=fields.invoice_number or "N/A",
                invoice_date=fields.invoice_date or "N/A",
                taxable_amount=f"{fields.taxable_amount or 0:,.2f}",
                cgst=f"{fields.cgst_amount or 0:,.2f}",
                sgst=f"{fields.sgst_amount or 0:,.2f}",
                igst=f"{fields.igst_amount or 0:,.2f}",
                total_amount=f"{fields.total_amount or 0:,.2f}",
                product_description=fields.product_description or "N/A",
            )

            if ocr_result.requires_mandatory_ca_review:
                msg += "\n\n" + MESSAGES["low_confidence_warning"]

            await wa_client.send_text(phone, msg)

            # Update session to AWAITING_CONFIRMATION
            await set_session(phone, {
                "state": "AWAITING_CONFIRMATION",
                "pending_invoice_id": str(invoice.id),
            })

    except Exception as exc:
        logger.error("ocr_task.failed", error=str(exc), client_id=client_id)
        try:
            await wa_client.send_text(phone, MESSAGES["ocr_failed"])
        except Exception:
            pass
        raise task.retry(exc=exc, countdown=30 * (2 ** task.request.retries))
