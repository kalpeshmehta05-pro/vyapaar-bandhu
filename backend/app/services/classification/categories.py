"""
VyapaarBandhu — Canonical Invoice Categories
7 categories mapped to GST ITC eligibility rules.
"""

from dataclasses import dataclass

CATEGORIES = [
    "electronics_and_it",
    "office_supplies",
    "raw_materials",
    "capital_goods",
    "food_and_beverages",
    "personal_clothing",
    "health_and_wellness",
]

# Mapping from categories to ITC eligibility (default, before Sec 17(5) check)
CATEGORY_ITC_MAP: dict[str, dict] = {
    "electronics_and_it": {"default_eligible": True, "note": "Business use electronics"},
    "office_supplies": {"default_eligible": True, "note": "Office consumables"},
    "raw_materials": {"default_eligible": True, "note": "Manufacturing inputs"},
    "capital_goods": {"default_eligible": True, "note": "Special rules — CA must confirm end-use"},
    "food_and_beverages": {"default_eligible": False, "note": "Section 17(5)(b)(i) — generally blocked"},
    "personal_clothing": {"default_eligible": False, "note": "Section 17(5) — personal use"},
    "health_and_wellness": {"default_eligible": False, "note": "Section 17(5)(b)(iii) — generally blocked"},
}

# BART zero-shot candidate labels mapped to our categories
BART_LABEL_MAP: dict[str, str] = {
    "Electronics & IT Equipment": "electronics_and_it",
    "Office Supplies & Stationery": "office_supplies",
    "Raw Materials & Industrial Goods": "raw_materials",
    "Capital Goods & Machinery": "capital_goods",
    "Food & Beverages": "food_and_beverages",
    "Clothing & Apparel": "personal_clothing",
    "Health & Wellness Products": "health_and_wellness",
    "Professional Services": "office_supplies",
    "Furniture & Fixtures": "capital_goods",
    "Travel & Transportation": "office_supplies",
}

BART_CANDIDATE_LABELS = list(BART_LABEL_MAP.keys())


@dataclass
class ClassificationResult:
    category: str
    method: str  # "keyword" | "bart" | "indicbert" | "all_failed"
    confidence: float
    needs_ca_review: bool = False
