"""
VyapaarBandhu — GSTR-3B JSON Generator
GSTN portal-compatible format. Only CA-confirmed figures included.
Includes RCM liability in Table 3.1(d).

CRITICAL: Never include draft/unconfirmed figures in the GSTR-3B output.
"""

import structlog

logger = structlog.get_logger()


def generate_gstr3b_json(
    gstin: str,
    tax_period: str,
    confirmed_cgst_itc: str,
    confirmed_sgst_itc: str,
    confirmed_igst_itc: str,
    confirmed_rcm_liability: str = "0.00",
) -> dict:
    """
    Generate GSTR-3B JSON in GSTN portal-accepted format.
    Only CA-confirmed figures are included.
    Reference: GSTN GSTR-3B JSON schema specification.
    """
    # Convert YYYY-MM to MMYYYY for GSTN
    parts = tax_period.split("-")
    gstn_period = f"{parts[1]}{parts[0]}"

    gstr3b = {
        "gstin": gstin or "",
        "ret_period": gstn_period,
        "inward_sup": {
            "isup_details": [
                {
                    "ty": "GST",
                    "inter": confirmed_igst_itc,
                    "intra": str(
                        float(confirmed_cgst_itc) + float(confirmed_sgst_itc)
                    ),
                }
            ]
        },
        "itc_elg": {
            "itc_avl": [
                {"ty": "IMPG", "iamt": "0.00", "camt": "0.00", "samt": "0.00", "csamt": "0.00"},
                {"ty": "IMPS", "iamt": "0.00", "camt": "0.00", "samt": "0.00", "csamt": "0.00"},
                {
                    "ty": "ISRC",
                    "iamt": confirmed_igst_itc,
                    "camt": confirmed_cgst_itc,
                    "samt": confirmed_sgst_itc,
                    "csamt": "0.00",
                },
                {"ty": "ISD", "iamt": "0.00", "camt": "0.00", "samt": "0.00", "csamt": "0.00"},
                {"ty": "OTH", "iamt": "0.00", "camt": "0.00", "samt": "0.00", "csamt": "0.00"},
            ],
            "itc_rev": [],
            "itc_net": [],
            "itc_inelg": [],
        },
        # Table 3.1(d) — Inward supplies liable to reverse charge
        "sup_details": {
            "isup_rev": {
                "txval": confirmed_rcm_liability,
                "iamt": "0.00",
                "camt": "0.00",
                "samt": "0.00",
                "csamt": "0.00",
            }
        },
    }

    logger.info("export.gstr3b.generated", gstin=gstin[:5] + "XXXXX" if gstin else "N/A")
    return gstr3b
