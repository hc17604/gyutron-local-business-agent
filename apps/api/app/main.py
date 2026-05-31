from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_database
from app.routers.agent import router as agent_router
from app.routers.alerts import router as alerts_router
from app.routers.automations import router as automations_router
from app.routers.connectors import router as connectors_router
from app.routers.health import router as health_router
from app.routers.overview import router as overview_router
from app.routers.reports import router as reports_router
from app.routers.settings import router as settings_router
from app.routers.workspace import router as workspace_router
from app.scheduler.scheduler import local_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    local_scheduler.start()
    yield
    local_scheduler.stop()


app = FastAPI(
    title="GyuTron Local Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(settings_router)
app.include_router(agent_router)
app.include_router(workspace_router)
app.include_router(connectors_router)
app.include_router(automations_router)
app.include_router(alerts_router)
app.include_router(reports_router)
app.include_router(overview_router)
