from sqlalchemy.orm import Session
from app.models.base import User, Invoice, GSTLedger
from app.core.database import SessionLocal
from datetime import datetime


def get_or_create_user(phone: str) -> User:
    phone = phone.replace("whatsapp:+91", "").replace("whatsapp:+", "").replace("whatsapp:", "")[:15]
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            user = User(phone=phone)
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ New user created: {phone}")
        return user
    finally:
        db.close()


def check_duplicate_invoice(phone: str, fields: dict) -> dict:
    """
    Check if this invoice already exists for this user.
    Match on: invoice_no + seller_gstin (both must match).
    Returns: {"is_duplicate": True/False, "existing_id": int, "existing_date": str}
    """
    phone = phone.replace("whatsapp:+91", "").replace("whatsapp:+", "").replace("whatsapp:", "")[:15]
    invoice_no   = (fields.get("invoice_no",   {}).get("value") or "").strip()
    seller_gstin = (fields.get("seller_gstin", {}).get("value") or "").strip()

    # Can't detect duplicate without at least invoice number
    if not invoice_no:
        return {"is_duplicate": False}

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return {"is_duplicate": False}

        query = db.query(Invoice).filter(
            Invoice.user_id    == user.id,
            Invoice.invoice_no == invoice_no
        )

        # If GSTIN also available, match on both for stronger check
        if seller_gstin:
            query = query.filter(Invoice.seller_gstin == seller_gstin)

        existing = query.first()

        if existing:
            existing_date = existing.date.strftime("%d-%m-%Y") if existing.date else "unknown date"
            print(f"⚠️ Duplicate detected: Invoice #{invoice_no} already saved as ID={existing.id}")
            return {
                "is_duplicate": True,
                "existing_id":   existing.id,
                "existing_date": existing_date,
                "existing_total": round((existing.cgst or 0) + (existing.sgst or 0) + (existing.igst or 0), 2)
            }

        return {"is_duplicate": False}

    finally:
        db.close()


def save_invoice(phone: str, fields: dict) -> dict:
    phone = phone.replace("whatsapp:+91", "").replace("whatsapp:+", "").replace("whatsapp:", "")[:15]
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            user = User(phone=phone)
            db.add(user)
            db.commit()
            db.refresh(user)

        date_val = None
        raw_date = fields.get("invoice_date", {}).get("value")
        if raw_date:
            for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]:
                try:
                    date_val = datetime.strptime(raw_date, fmt)
                    break
                except:
                    pass

        invoice = Invoice(
            user_id      = user.id,
            seller_gstin = (fields.get("seller_gstin", {}).get("value") or "")[:15] or None,
            invoice_no   = (fields.get("invoice_no",   {}).get("value") or "")[:100] or None,
            date         = date_val,
            taxable_amt  = fields.get("taxable_amount", {}).get("value") or 0,
            cgst         = fields.get("cgst", {}).get("value") or 0,
            sgst         = fields.get("sgst", {}).get("value") or 0,
            igst         = fields.get("igst", {}).get("value") or 0,
            status       = "confirmed"
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        print(f"✅ Invoice saved: ID={invoice.id}")

        # Fix: inter-state (IGST only) vs intra-state (CGST + SGST)
        igst = invoice.igst or 0
        cgst = invoice.cgst or 0
        sgst = invoice.sgst or 0
        itc_amount = igst if igst > 0 else (cgst + sgst)

        period = datetime.utcnow().strftime("%Y-%m")
        ledger = db.query(GSTLedger).filter(
            GSTLedger.user_id == user.id,
            GSTLedger.period  == period
        ).first()

        if not ledger:
            ledger = GSTLedger(
                user_id         = user.id,
                period          = period,
                total_purchases = 0,
                itc_available   = 0,
                net_liability   = 0
            )
            db.add(ledger)

        ledger.total_purchases = (ledger.total_purchases or 0) + (invoice.taxable_amt or 0)
        ledger.itc_available   = (ledger.itc_available   or 0) + itc_amount
        db.commit()

        print(f"✅ ITC updated: +Rs.{itc_amount} | Total ITC: Rs.{ledger.itc_available}")

        return {
            "success":    True,
            "invoice_id": invoice.id,
            "itc_this":   round(itc_amount, 2),
            "itc_total":  round(ledger.itc_available, 2),
            "period":     period
        }

    except Exception as e:
        print(f"❌ DB Error: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_itc_balance(phone: str) -> dict:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return {"itc_total": 0, "period": "", "invoice_count": 0}

        period = datetime.utcnow().strftime("%Y-%m")
        ledger = db.query(GSTLedger).filter(
            GSTLedger.user_id == user.id,
            GSTLedger.period  == period
        ).first()

        invoice_count = db.query(Invoice).filter(
            Invoice.user_id == user.id
        ).count()

        return {
            "itc_total":     round(ledger.itc_available if ledger else 0, 2),
            "period":        period,
            "invoice_count": invoice_count
        }
    finally:
        db.close()