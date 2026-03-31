"""
VyapaarBandhu — Hinglish WhatsApp Message Templates
All user-facing messages in one place for consistency.
"""

MESSAGES = {
    "consent_request": (
        "Namaste! Aapke CA ({ca_firm_name}) ne aapko VyapaarBandhu se connect kiya hai.\n\n"
        "VyapaarBandhu ek GST document management tool hai jo:\n"
        "- Aapki invoice photos se data extract karta hai\n"
        "- ITC draft prepare karta hai aapke CA ke liye\n"
        "- Filing deadlines ki yaad dilata hai\n\n"
        "Iske liye hum yeh data collect karenge:\n"
        "- Phone number, GSTIN, invoice images aur financial details\n\n"
        "Yeh data sirf aapke CA ko dikhaya jayega.\n"
        "Images 3 saal aur data 7 saal tak stored rahega.\n\n"
        "Agree karne ke liye *haan* reply karein.\n"
        "Cancel karne ke liye *nahi* reply karein."
    ),
    "consent_given": (
        "Shukriya! Aapne VyapaarBandhu ko consent de diya hai.\n\n"
        "Ab aap apni invoices ki photo yahan bhej sakte hain "
        "aur hum automatically ITC calculate karenge.\n\n"
        "Shuru karne ke liye invoice ki photo bhejiye! 📸"
    ),
    "consent_denied": (
        "Theek hai. Aapka data process nahi kiya jayega.\n"
        "Agar baad mein use karna ho toh apne CA se contact karein."
    ),
    "received": (
        "📸 Photo mil gayi! Processing kar raha hoon... "
        "({invoice_count} invoices is month mein ab tak)"
    ),
    "ocr_result": (
        "✅ Invoice details extract ho gayi:\n\n"
        "🏢 Seller: {seller_name}\n"
        "🔢 GSTIN: {seller_gstin}{gstin_correction_note}\n"
        "📄 Invoice No: {invoice_number}\n"
        "📅 Date: {invoice_date}\n"
        "💰 Taxable Amount: Rs.{taxable_amount}\n"
        "🧾 CGST: Rs.{cgst} | SGST: Rs.{sgst} | IGST: Rs.{igst}\n"
        "💵 Total: Rs.{total_amount}\n"
        "📦 Description: {product_description}\n\n"
        "Kya yeh sahi hai? Reply karein:\n"
        "✅ *haan* — save karein\n"
        "✏️ *edit date* / *edit total* / *edit gstin* — correct karein\n"
        "❌ *cancel* — discard karein"
    ),
    "gstin_correction_note": " *(auto-corrected from {original})*",
    "low_confidence_warning": (
        "⚠️ *Dhyan dein:* Is invoice ki image thodi unclear hai. "
        "Kripya sabhi fields dhyan se check karein aur confirm karein. "
        "CA dashboard mein bhi yeh flagged rahega."
    ),
    "saved": (
        "✅ Invoice save ho gayi! Aapke CA ({ca_firm_name}) ke dashboard mein add ho gayi hai.\n\n"
        "📊 Is mahine ka draft ITC: Rs.{draft_itc_total} *(CA approval pending)*\n"
        "📋 Total invoices: {invoice_count}\n"
        "📅 GSTR-3B deadline: {gstr3b_deadline}"
    ),
    "duplicate": (
        "⚠️ Yeh invoice pehle se save hai (Invoice No: {invoice_number}). "
        "Duplicate nahi save ki."
    ),
    "summary": (
        "📊 *{tax_period} ka Summary*\n\n"
        "Total Invoices: {invoice_count}\n"
        "Draft ITC: Rs.{draft_itc_total} *(CA approval pending)*\n"
        "Approved ITC: Rs.{approved_itc_total}\n"
        "Pending CA Review: {pending_count} invoices\n\n"
        "📅 GSTR-1 Deadline: {gstr1_deadline}\n"
        "📅 GSTR-3B Deadline: {gstr3b_deadline}\n\n"
        "_Yeh figures aapke CA ({ca_firm_name}) ke approval ke baad final hongi._"
    ),
    "reminder_7day": (
        "📅 *{ca_firm_name} se reminder:*\n\n"
        "GSTR-3B deadline {days_remaining} din mein hai ({deadline_date}).\n"
        "Aapne {invoice_count} invoices upload ki hain.\n"
        "Draft ITC: Rs.{draft_itc_total}\n\n"
        "Baaki invoices abhi bhej dein! 📸"
    ),
    "not_registered": (
        "Aapka number registered nahi hai. Apne CA se VyapaarBandhu ke baare mein poochein."
    ),
    "help": (
        "Aap yeh kar sakte hain:\n"
        "📸 Invoice ki photo bhejein\n"
        "📊 *summary* type karke is month ka summary dekhein\n"
        "❓ *help* type karke yeh instructions dekhein"
    ),
    "unrecognised_command": (
        "Mujhe samajh nahi aaya. Aap:\n"
        "📸 Invoice ki photo bhej sakte hain\n"
        "📊 *summary* type karke summary dekh sakte hain\n"
        "❓ *help* type karke instructions dekh sakte hain"
    ),
    "edit_prompt": "Naya {field_name} bhejein:",
    "edit_saved": "✅ {field_name} update ho gaya: {new_value}",
    "cancelled": "❌ Invoice discard kar di gayi.",
    "ocr_failed": "❌ Invoice read nahi ho payi. Kripya clear photo bhejein.",
    "consent_withdrawn": (
        "Aapka consent withdraw ho gaya hai. Aapka data GST Act ke under "
        "{retention_years} saal tak stored rahega, uske baad automatically delete ho jayega."
    ),
}
