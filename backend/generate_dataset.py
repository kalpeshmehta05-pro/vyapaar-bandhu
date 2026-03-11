import csv
import random

# Indian SME transaction descriptions by category
templates = {
    "Electronics": [
        "Laptop purchase Dell Inspiron", "Mobile phone Samsung Galaxy", "Printer HP LaserJet",
        "Computer accessories keyboard mouse", "CCTV camera installation", "LED monitor LG",
        "UPS battery backup", "Hard disk WD 1TB", "Router TP-Link WiFi", "Projector Epson",
        "laptop", "mobile", "printer", "computer", "CCTV", "monitor", "router", "projector",
        "laptop kharido", "mobile phone", "computer saaman", "printer cartridge",
    ],
    "Food": [
        "Restaurant bill dinner", "Catering service lunch", "Hotel food expense",
        "Bhojan ka bill", "Khana catering", "Restaurant dinner party",
        "Food court lunch", "Canteen meal expense", "Chai nashta", "Lunch box catering",
        "bhojan", "khana", "restaurant", "catering", "nashta", "chai", "lunch", "dinner",
        "khane ka bill", "hotel ka khana", "party catering", "food expense",
    ],
    "Office": [
        "Stationery purchase pens notebooks", "Office furniture chair table",
        "Printing paper A4 ream", "Whiteboard marker set", "File folder document",
        "Office supplies", "Pen pencil eraser", "Stapler binding", "Courier service",
        "karyalay saaman", "office furniture", "stationery items", "printing paper",
        "office chair", "desk table", "notebook register", "stamp pad",
    ],
    "Pharma": [
        "Medicine purchase chemist", "Pharmaceutical drugs wholesale",
        "Medical supplies hospital", "Dawa purchase", "Medicine stock",
        "Chemist bill", "Hospital supplies", "Medical equipment", "Surgical items",
        "dawa", "medicine", "pharmaceutical", "medical", "hospital supply",
        "dawakhana purchase", "medical store", "health products",
    ],
    "Travel": [
        "Train ticket IRCTC", "Flight booking Mumbai Delhi", "Bus ticket interstate",
        "Fuel petrol diesel", "Vehicle maintenance service", "Toll tax highway",
        "Auto rickshaw Ola Uber", "yatra ticket", "safar ka kharcha",
        "petrol diesel", "gaadi service", "toll", "flight ticket", "train",
        "bus ticket", "taxi fare", "travel expense", "hotel stay business trip",
    ],
    "Clothing": [
        "Fabric purchase wholesale", "Garment manufacturing", "Textile material cotton",
        "Uniform stitching", "Cloth kapda purchase", "Readymade garments",
        "kapda", "fabric", "garment", "textile", "uniform", "clothing",
        "kapde ka bill", "suit stitching", "saree purchase", "shirt pant",
    ],
    "Vehicle": [
        "Car purchase personal use", "Two wheeler bike scooter",
        "Vehicle insurance premium", "Car loan EMI", "Personal vehicle maintenance",
        "gaadi", "car", "bike", "scooter", "vehicle", "auto",
        "personal car", "gaadi kharido", "bike purchase", "car insurance",
    ],
}

# Section 17(5) blocked categories
BLOCKED = {"Food", "Vehicle"}

rows = []
for category, descs in templates.items():
    per_category = 2000 // len(templates)
    for _ in range(per_category):
        desc = random.choice(descs)
        # Add variation
        amount = random.randint(500, 50000)
        gstin = f"24AABC{random.randint(1000,9999)}A1Z{random.randint(1,9)}"
        itc_eligible = "No" if category in BLOCKED else "Yes"
        rows.append({
            "description": desc,
            "amount": amount,
            "category": category,
            "itc_eligible": itc_eligible,
            "gstin": gstin,
        })

# Shuffle
random.shuffle(rows)

# Write CSV
with open("dataset/indian_sme_transactions.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["description", "amount", "category", "itc_eligible", "gstin"])
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Generated {len(rows)} labeled transactions")
print("Categories:", {cat: sum(1 for r in rows if r['category'] == cat) for cat in templates})
print("Saved to: dataset/indian_sme_transactions.csv")