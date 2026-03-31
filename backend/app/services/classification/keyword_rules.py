"""
VyapaarBandhu — Keyword-Based Classification (Layer 1)
400+ keyword rules for deterministic, fast invoice classification.
Ported from the original classification_service.py.
"""

from dataclasses import dataclass

from app.services.classification.categories import ClassificationResult


@dataclass
class KeywordMatch:
    category: str
    confidence: float


# ── KEYWORD RULES ─────────────────────────────────────────────────────
# Format: (list of keywords, category)
# If any keyword is found in the description, the category is assigned.
# More specific keywords first — first match wins.

KEYWORD_RULES: list[tuple[list[str], str]] = [
    # ── Electronics & IT ──────────────────────────────────────────
    ([
        "dell", "hp", "lenovo", "asus", "acer", "apple", "samsung", "sony",
        "lg", "mi", "xiaomi", "oneplus", "realme", "oppo", "vivo", "nokia",
        "motorola", "redmi", "poco", "iqoo", "nothing",
        "bose", "jbl", "boat", "zebronics",
        "panasonic", "philips", "whirlpool", "bosch", "siemens", "godrej",
        "voltas", "hitachi", "haier", "tcl", "hisense",
        "laptop", "notebook", "desktop", "computer", "macbook",
        "chromebook", "ultrabook", "workstation",
        "inspiron", "thinkpad", "ideapad", "vivobook", "zenbook",
        "pavilion", "elitebook", "spectre", "surface",
        "monitor", "display", "led monitor", "lcd monitor",
        "keyboard", "mouse", "webcam", "headset", "headphone",
        "earphone", "earbuds", "speaker", "microphone", "printer", "scanner",
        "projector", "router", "modem", "network switch",
        "pen drive", "usb drive", "hard disk", "hdd", "ssd", "ram",
        "processor", "cpu", "gpu", "graphics card", "motherboard",
        "ups", "stabilizer", "extension board",
        "hdmi", "charger", "adapter", "power bank",
        "mobile", "phone", "smartphone", "iphone", "tablet", "ipad",
        "smartwatch", "fitness band",
        "refrigerator", "fridge", "washing machine", "microwave",
        "air conditioner", "ac", "cooler", "geyser", "water heater",
        "television", "smart tv", "set top box",
        "vacuum cleaner", "iron box", "mixer", "grinder", "juicer",
        "induction", "chimney", "dishwasher",
        "camera", "dslr", "drone", "lens",
        "software license", "antivirus",
        "cloud storage", "aws", "azure", "google cloud", "web hosting",
        "domain", "ssl certificate",
        "toner", "cartridge", "ink",
        "server", "rack", "firewall",
    ], "electronics_and_it"),

    # ── Office Supplies ───────────────────────────────────────────
    ([
        "paper", "a4", "a3", "photocopy", "xerox",
        "pen", "pencil", "marker", "highlighter", "eraser", "sharpener",
        "notebook", "register", "file", "folder", "binder",
        "stapler", "staples", "paper clip", "rubber band",
        "tape", "adhesive", "glue", "scissors",
        "envelope", "stamp", "courier", "postage",
        "whiteboard", "board marker", "duster",
        "desk", "chair", "table", "cabinet", "shelf", "rack",
        "stationery", "office supplies",
        "visiting card", "business card", "letterhead",
        "diary", "planner", "calendar",
        "bill book", "receipt book", "voucher",
        "accounting software", "tally", "busy", "marg",
        "internet bill", "broadband", "wifi", "telephone bill",
        "electricity bill", "water bill", "rent",
        "cleaning", "housekeeping", "sanitation",
        "security deposit", "maintenance charge",
        "courier service", "speed post",
        "legal fee", "consultation fee", "audit fee", "ca fee",
        "professional fee", "registration fee",
    ], "office_supplies"),

    # ── Raw Materials ─────────────────────────────────────────────
    ([
        "raw material", "steel", "iron", "copper", "aluminium", "aluminum",
        "brass", "zinc", "tin", "lead",
        "cement", "sand", "gravel", "brick", "tile",
        "wood", "timber", "plywood", "laminate", "veneer",
        "fabric", "cloth", "yarn", "thread", "cotton",
        "chemical", "solvent", "acid", "alkali", "dye", "pigment",
        "plastic", "polymer", "rubber", "silicone",
        "glass", "ceramic", "marble", "granite",
        "nut", "bolt", "screw", "washer", "rivet",
        "pipe", "tube", "fitting", "valve", "flange",
        "wire", "cable", "conduit",
        "packaging", "box", "carton", "wrapper",
        "label", "sticker", "barcode",
        "adhesive", "sealant", "lubricant", "oil",
        "paint", "primer", "thinner", "varnish",
    ], "raw_materials"),

    # ── Capital Goods ─────────────────────────────────────────────
    ([
        "machinery", "machine", "lathe", "cnc", "drilling",
        "compressor", "generator", "transformer", "motor",
        "conveyor", "crane", "forklift", "hoist",
        "furnace", "kiln", "boiler", "chiller",
        "air handling unit", "ahu", "hvac",
        "solar panel", "inverter", "battery bank",
        "vehicle", "truck", "van", "car", "scooter", "bike",
        "weighing scale", "weighbridge",
        "die", "mould", "mold", "jig", "fixture",
        "tool", "power tool", "hand tool",
        "pump", "blower", "fan",
        "building renovation", "construction", "civil work",
        "office renovation", "interior",
    ], "capital_goods"),

    # ── Food & Beverages ──────────────────────────────────────────
    ([
        "food", "meal", "lunch", "dinner", "breakfast", "snack",
        "tea", "coffee", "cold drink", "soft drink", "juice",
        "water bottle", "mineral water",
        "restaurant", "hotel bill", "catering",
        "sweets", "mithai", "namkeen", "biscuit", "chips",
        "biryani", "pizza", "burger", "sandwich",
        "zomato", "swiggy", "uber eats",
        "canteen", "mess", "tiffin",
        "fruit", "vegetable", "grocery",
        "milk", "curd", "paneer", "butter", "ghee",
        "rice", "wheat", "flour", "dal", "oil",
        "spice", "masala", "salt", "sugar",
        "chocolate", "ice cream", "cake", "bakery",
        "alcohol", "liquor", "beer", "wine", "whisky",
    ], "food_and_beverages"),

    # ── Personal Clothing ─────────────────────────────────────────
    ([
        "clothing", "clothes", "garment", "apparel",
        "shirt", "pant", "trouser", "jeans", "t-shirt",
        "saree", "sari", "salwar", "kurta", "kurti", "lehenga",
        "suit", "blazer", "jacket", "coat",
        "uniform", "apron",
        "shoes", "footwear", "sandal", "chappal", "boot", "sneaker",
        "belt", "tie", "scarf", "shawl", "dupatta",
        "undergarment", "socks", "gloves",
        "watch", "jewellery", "jewelry", "ring", "chain", "bracelet",
        "handbag", "purse", "wallet", "luggage", "bag",
        "sunglasses", "spectacles", "eyeglasses",
    ], "personal_clothing"),

    # ── Health & Wellness ─────────────────────────────────────────
    ([
        "medicine", "tablet", "capsule", "syrup", "injection",
        "pharmacy", "medical store", "chemist",
        "hospital", "clinic", "doctor", "consultation",
        "diagnostic", "test", "x-ray", "mri", "ct scan", "ultrasound",
        "pathology", "blood test", "urine test",
        "dental", "dentist", "eye care", "optician",
        "gym", "fitness", "yoga", "spa", "massage",
        "beauty", "salon", "parlour", "parlor",
        "cosmetic", "cream", "lotion", "shampoo", "soap",
        "perfume", "deodorant",
        "sanitizer", "mask", "ppe kit",
        "first aid", "bandage", "thermometer",
        "health insurance", "medical insurance",
        "ayurvedic", "homeopathic", "herbal",
    ], "health_and_wellness"),
]


def classify(description: str) -> ClassificationResult:
    """
    Layer 1: Keyword-based classification.
    Fast, deterministic, handles known brands and product types.
    Returns confidence >= 0.92 if a match is found.
    """
    if not description or len(description.strip()) < 3:
        return ClassificationResult(
            category="unknown", method="keyword", confidence=0.0
        )

    desc_lower = description.lower().strip()

    for keywords, category in KEYWORD_RULES:
        for keyword in keywords:
            if keyword in desc_lower:
                return ClassificationResult(
                    category=category,
                    method="keyword",
                    confidence=0.95,
                )

    return ClassificationResult(
        category="unknown", method="keyword", confidence=0.0
    )
