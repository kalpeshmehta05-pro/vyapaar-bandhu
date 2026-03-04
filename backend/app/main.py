from fastapi import FastAPI
from app.models.base import Base
from app.core.database import engine
from app.routes.gstin import router as gstin_router
from app.routes.compliance import router as compliance_router


app = FastAPI(
    title="VyapaarBandhu",
    description="AI GST Compliance Assistant for Indian Small Businesses",
    version="0.1.0"
)

app.include_router(gstin_router)
app.include_router(compliance_router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("✅ All 8 tables created")

@app.get("/health")
def health_check():
    return {
        "status": "alive",
        "product": "VyapaarBandhu",
        "version": "0.1.0"
    }