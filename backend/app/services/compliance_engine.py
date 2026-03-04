# ============================================
# VYAPAAR BANDHU — GST COMPLIANCE ENGINE
# 100% Pure Python. Zero AI. Zero API calls.
# This is your core IP.
# ============================================

from datetime import datetime, date

# ── SECTION 17(5) BLOCKED ITC CATEGORIES ──
# These are hardcoded from the GST Act.
# Never use AI to determine these — they are law.

BLOCKED_ITC_CATEGORIES = {
    "motor_vehicle",
    "food_beverage",
    "beauty_treatment",
    "health_services",
    "club_membership",
    "gym_membership",
    "travel_benefit",
    "works_contract",
    "construction",
    "gift",
    "personal_consumption",
    "life_insurance",
    "health_insurance",
    "rent_a_cab",
    "outdoor_catering",
}

# ── GST RATES BY HSN CODE CATEGORY ──
GST_RATES = {
    "textile":          5.0,
    "garments":         12.0,
    "electronics":      18.0,
    "software":         18.0,
    "restaurant":       5.0,
    "hotel":            12.0,
    "gold":             3.0,
    "medicine":         12.0,
    "mobile":           18.0,
    "automobile":       28.0,
    "default":          18.0,
}

# ── FILING DEADLINES ──
GSTR1_DAY  = 11   # GSTR-1 due on 11th of next month
GSTR3B_DAY = 20   # GSTR-3B due on 20th of next month


def check_itc_eligibility(category: str) -> dict:
    """
    Checks if a purchase category is eligible for ITC.
    Input:  category string (e.g. "food_beverage")
    Output: dict with eligible bool + reason
    """
    category = category.lower().strip()
    
    if category in BLOCKED_ITC_CATEGORIES:
        return {
            "eligible": False,
            "reason": f"'{category}' is blocked under Section 17(5) of GST Act",
            "itc_amount": 0
        }
    
    return {
        "eligible": True,
        "reason": "Purchase is eligible for Input Tax Credit",
        "itc_amount": None  # calculated separately
    }


def calculate_gst_liability(transactions: list) -> dict:
    """
    Calculates net GST liability for a given month.
    
    Input: list of transactions
    [
        {"type": "sale", "amount": 10000, "gst_rate": 18},
        {"type": "purchase", "amount": 5000, "gst_rate": 12, "itc_eligible": True},
    ]
    
    Output: complete GST position
    """
    total_gst_collected = 0   # from sales
    total_itc_available = 0   # from eligible purchases
    
    for txn in transactions:
        gst_amount = txn["amount"] * txn["gst_rate"] / 100
        
        if txn["type"] == "sale":
            total_gst_collected += gst_amount
            
        elif txn["type"] == "purchase":
            if txn.get("itc_eligible", False):
                total_itc_available += gst_amount
    
    net_liability = max(0, total_gst_collected - total_itc_available)
    
    return {
        "total_gst_collected": round(total_gst_collected, 2),
        "total_itc_available": round(total_itc_available, 2),
        "net_liability":       round(net_liability, 2),
        "period":              datetime.now().strftime("%Y-%m"),
    }


def calculate_penalty(return_type: str, days_late: int, tax_liability: float) -> dict:
    """
    Calculates exact GST penalty for late filing.
    
    GSTR-1:  ₹50/day (₹25 CGST + ₹25 SGST). Max ₹10,000
    GSTR-3B: ₹50/day if liability > 0
             ₹20/day if nil return
             18% per annum interest on tax due
    """
    if days_late <= 0:
        return {"penalty": 0, "interest": 0, "total": 0}
    
    if return_type == "GSTR-1":
        penalty = min(days_late * 50, 10000)
        interest = 0
        
    elif return_type == "GSTR-3B":
        if tax_liability > 0:
            penalty  = min(days_late * 50, 10000)
            interest = round(tax_liability * 0.18 * days_late / 365, 2)
        else:
            penalty  = min(days_late * 20, 10000)
            interest = 0
    else:
        penalty  = 0
        interest = 0
    
    return {
        "days_late":   days_late,
        "penalty":     round(penalty, 2),
        "interest":    interest,
        "total":       round(penalty + interest, 2),
        "message_hi":  f"{days_late} din late filing. Penalty: ₹{penalty} + Interest: ₹{interest}"
    }


def get_filing_deadlines(period: str) -> dict:
    """
    Returns filing deadlines for a given period.
    Period format: "2025-03"
    """
    year, month = map(int, period.split("-"))
    
    # Deadlines are in the NEXT month
    if month == 12:
        next_month = 1
        next_year  = year + 1
    else:
        next_month = month + 1
        next_year  = year
    
    gstr1_deadline  = date(next_year, next_month, GSTR1_DAY)
    gstr3b_deadline = date(next_year, next_month, GSTR3B_DAY)
    today           = date.today()
    
    return {
        "period":           period,
        "gstr1_deadline":   str(gstr1_deadline),
        "gstr3b_deadline":  str(gstr3b_deadline),
        "days_to_gstr1":    (gstr1_deadline  - today).days,
        "days_to_gstr3b":   (gstr3b_deadline - today).days,
    }