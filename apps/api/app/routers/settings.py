from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.llm.adapter import LLMAdapter, PROVIDERS
from app.services.audit import write_audit_log
from app.services.model_settings import get_active_llm_config, get_active_model_config, save_model_config


router = APIRouter(prefix="/settings/model", tags=["model-settings"])


class ModelSettingsPayload(BaseModel):
    id: int | None = None
    provider: str = "openai_compatible"
    display_name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_name: str = "gpt-4.1-mini"
    supports_streaming: bool = False


@router.get("")
def get_model_settings():
    return get_active_model_config() or {
        "id": None,
        "provider": "openai_compatible",
        "display_name": "OpenAI-compatible",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "model_name": "gpt-4.1-mini",
        "is_active": False,
        "supports_streaming": False,
    }


@router.post("")
def update_model_settings(payload: ModelSettingsPayload):
    saved = save_model_config(payload.dict())
    write_audit_log(
        "model_settings_saved",
        "llm_config",
        target_id=str(saved.get("id")),
        risk_level="medium",
        input_summary=f"provider={saved.get('provider')}, model={saved.get('model_name')}",
        output_summary="Model settings saved with masked API key.",
    )
    return saved


@router.post("/test")
async def test_model_settings(payload: ModelSettingsPayload | None = None):
    if payload is not None:
        config_data = save_model_config(payload.dict())
        config = get_active_llm_config()
        target_id = str(config_data.get("id"))
    else:
        config = get_active_llm_config()
        target_id = None
    if config is None:
        raise HTTPException(status_code=400, detail="No active model settings configured.")

    try:
        answer = await LLMAdapter(config).chat([{"role": "user", "content": "Reply only with OK."}], temperature=0)
    except Exception as exc:
        write_audit_log(
            "model_connection_test",
            "llm_config",
            target_id=target_id,
            risk_level="medium",
            input_summary=f"provider={config.provider}, model={config.model_name}",
            output_summary=f"failed: {type(exc).__name__}",
        )
        raise HTTPException(status_code=502, detail=f"Model connection failed: {type(exc).__name__}") from exc

    write_audit_log(
        "model_connection_test",
        "llm_config",
        target_id=target_id,
        risk_level="medium",
        input_summary=f"provider={config.provider}, model={config.model_name}",
        output_summary="connected",
    )
    return {"status": "connected", "reply": answer.strip()[:120]}


@router.get("/providers")
def get_model_providers():
    return {"providers": PROVIDERS}
