from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_database
from app.routers.agent import router as agent_router
from app.routers.alerts import router as alerts_router
from app.routers.audit import router as audit_router
from app.routers.auth import router as auth_router
from app.routers.automations import router as automations_router
from app.routers.backups import router as backups_router
from app.routers.commerce import router as commerce_router
from app.routers.connectors import router as connectors_router
from app.routers.demo import router as demo_router
from app.routers.health import router as health_router
from app.routers.license import router as license_router
from app.routers.overview import router as overview_router
from app.routers.reports import router as reports_router
from app.routers.rules import router as rules_router
from app.routers.security import router as security_router
from app.routers.tasks import router as tasks_router
from app.routers.settings import router as settings_router
from app.routers.setup import router as setup_router
from app.routers.system import router as system_router
from app.routers.users import router as users_router
from app.routers.workspace import router as workspace_router
from app.scheduler.scheduler import local_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    from app.services.bootstrap import ensure_phase3_defaults

    ensure_phase3_defaults()
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
app.include_router(setup_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(settings_router)
app.include_router(agent_router)
app.include_router(workspace_router)
app.include_router(connectors_router)
app.include_router(automations_router)
app.include_router(alerts_router)
app.include_router(reports_router)
app.include_router(tasks_router)
app.include_router(rules_router)
app.include_router(commerce_router)
app.include_router(overview_router)
app.include_router(security_router)
app.include_router(backups_router)
app.include_router(license_router)
app.include_router(demo_router)
app.include_router(system_router)
app.include_router(audit_router)
