from fastapi import FastAPI

from app.api.routes.health import router as health_router


app = FastAPI(
    title="GoFit Business Center",
    version="0.1.0",
    description="Business API for the GoFit hackathon MVP.",
)

app.include_router(health_router, prefix="/api/v1")
