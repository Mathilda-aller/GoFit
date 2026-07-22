from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.action_cards import router as action_cards_router
from app.api.routes.experiences import router as experiences_router
from app.api.routes.health import router as health_router
from app.api.routes.me import router as me_router
from app.api.routes.plans import router as plans_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.videos import router as videos_router
from app.db.database import lifespan


app = FastAPI(
    title="GoFit Business Center",
    version="0.1.0",
    description="Business API for the GoFit hackathon MVP.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(videos_router, prefix="/api/v1")
app.include_router(action_cards_router, prefix="/api/v1")
app.include_router(plans_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(experiences_router, prefix="/api/v1")
app.include_router(me_router, prefix="/api/v1")
