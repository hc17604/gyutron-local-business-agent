from __future__ import annotations

from sqlite3 import Row

from app.database import get_connection
from app.llm.adapter import LLMConfig, provider_default_base_url


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "********"
    return f"{api_key[:4]}...{api_key[-4:]}"


def serialize_config(row: Row | None, *, include_secret: bool = False) -> dict | None:
    if row is None:
        return None
    data = dict(row)
    data["provider"] = data.get("provider") or data.get("provider_name") or "openai_compatible"
    data["display_name"] = data.get("display_name") or data["provider"]
    data["is_active"] = bool(data.get("is_active") or data.get("is_default"))
    data["supports_streaming"] = bool(data.get("supports_streaming"))
    if include_secret:
        return data
    data["api_key"] = mask_api_key(data.get("api_key") or "")
    return data


def get_active_model_config(*, include_secret: bool = False) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM llm_configs
            ORDER BY is_active DESC, is_default DESC, updated_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
    return serialize_config(row, include_secret=include_secret)


def get_active_llm_config() -> LLMConfig | None:
    config = get_active_model_config(include_secret=True)
    if not config:
        return None
    return LLMConfig(
        provider=config["provider"],
        base_url=config["base_url"],
        api_key=config.get("api_key") or "",
        model_name=config["model_name"],
    )


def save_model_config(payload: dict) -> dict:
    provider = payload.get("provider") or "openai_compatible"
    base_url = payload.get("base_url") or provider_default_base_url(provider)
    display_name = payload.get("display_name") or provider.replace("_", " ").title()
    api_key = payload.get("api_key") or ""
    if api_key.startswith("****") or "..." in api_key:
        existing = get_active_model_config(include_secret=True)
        api_key = (existing or {}).get("api_key") or ""

    with get_connection() as connection:
        connection.execute("UPDATE llm_configs SET is_active = 0, is_default = 0")
        config_id = payload.get("id")
        if config_id:
            connection.execute(
                """
                UPDATE llm_configs
                SET provider = ?, provider_name = ?, display_name = ?, base_url = ?, api_key = ?,
                    model_name = ?, is_active = 1, is_default = 1, supports_streaming = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    provider,
                    provider,
                    display_name,
                    base_url,
                    api_key,
                    payload.get("model_name") or "gpt-4.1-mini",
                    int(bool(payload.get("supports_streaming"))),
                    config_id,
                ),
            )
        else:
            cursor = connection.execute(
                """
                INSERT INTO llm_configs (
                  provider, provider_name, display_name, base_url, api_key, model_name,
                  is_active, is_default, supports_streaming
                ) VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?)
                """,
                (
                    provider,
                    provider,
                    display_name,
                    base_url,
                    api_key,
                    payload.get("model_name") or "gpt-4.1-mini",
                    int(bool(payload.get("supports_streaming"))),
                ),
            )
            config_id = cursor.lastrowid
        connection.commit()
        row = connection.execute("SELECT * FROM llm_configs WHERE id = ?", (config_id,)).fetchone()
    return serialize_config(row) or {}
