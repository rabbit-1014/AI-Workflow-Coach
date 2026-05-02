import json
from pathlib import Path

from schemas import BlockageOutput, RouteOutput


STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "app_state.json"


def _default_state() -> dict:
    return {
        "user_goal": "",
        "route_result": None,
        "blockage_result": None,
    }


def load_app_state() -> dict:
    if not STATE_FILE.exists():
        return _default_state()

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))

        route_result = (
            RouteOutput.model_validate(data["route_result"])
            if data.get("route_result")
            else None
        )
        blockage_result = (
            BlockageOutput.model_validate(data["blockage_result"])
            if data.get("blockage_result")
            else None
        )

        return {
            "user_goal": data.get("user_goal", ""),
            "route_result": route_result,
            "blockage_result": blockage_result,
        }
    except Exception:
        return _default_state()


def save_app_state(
    user_goal: str,
    route_result=None,
    blockage_result=None,
) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "user_goal": user_goal,
            "route_result": route_result.model_dump() if route_result else None,
            "blockage_result": blockage_result.model_dump() if blockage_result else None,
        }

        STATE_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def clear_app_state() -> None:
    try:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
    except Exception:
        pass
