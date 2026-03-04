from fastapi import APIRouter
from app.services.compliance_engine import (
    check_itc_eligibility,
    calculate_gst_liability,
    calculate_penalty,
    get_filing_deadlines
)

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get("/itc/{category}")
def itc_check(category: str):
    return check_itc_eligibility(category)


@router.get("/deadlines/{period}")
def deadlines(period: str):
    return get_filing_deadlines(period)


@router.get("/penalty/{return_type}/{days_late}/{tax_liability}")
def penalty(return_type: str, days_late: int, tax_liability: float):
    return calculate_penalty(return_type, days_late, tax_liability)


@router.post("/liability")
def liability(transactions: list):
    return calculate_gst_liability(transactions)