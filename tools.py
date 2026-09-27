from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RATES = json.loads((ROOT / "data/rates.json").read_text(encoding="utf-8"))

TOOL_SCHEMA = {
    "name": "estimate_trip_cost",
    "description": (
        "교육용 현행 국내 출장의 숙박비와 식비 상한을 계산한다. "
        "2026-07-01 이후, 국내 도시, 정수 1~6박만 지원한다. "
        "도시와 숙박 수를 사용자에게 확인한 뒤 호출한다. 승인/예약/결제를 하지 않는다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "enum": ["서울", "부산", "기타"],
                "description": "기타는 서울/부산 외의 국내 도시만 의미한다.",
            },
            "nights": {
                "type": "integer",
                "description": "숙박 수. 1부터 6까지의 정수.",
            },
        },
        "required": ["city", "nights"],
        "additionalProperties": False,
    },
    "strict": True,
}


class ToolInputError(ValueError):
    pass


def estimate_trip_cost(city: str, nights: int) -> dict[str, object]:
    if not isinstance(city, str) or city not in RATES["lodging_per_night"]:
        raise ToolInputError("city는 서울, 부산, 기타 국내 도시 중 하나여야 합니다.")
    if (
        type(nights) is not int
        or not RATES["min_nights"] <= nights <= RATES["max_nights"]
    ):
        raise ToolInputError(
            "nights는 1~6 사이의 정수여야 합니다. 0박/당일 출장은 지원하지 않습니다."
        )
    days = nights + 1
    lodging = RATES["lodging_per_night"][city] * nights
    meals = RATES["meal_per_day"] * days
    return {
        "ok": True,
        "city": city,
        "nights": nights,
        "days": days,
        "lodging": lodging,
        "meals": meals,
        "total": lodging + meals,
        "currency": RATES["currency"],
        "policy_id": RATES["policy_id"],
        "status": "estimate_only",
        "approval_required": True,
        "excluded": ["transportation", "other_expenses"],
    }


def execute_tool(name: str, arguments: str) -> dict[str, object]:
    if name != TOOL_SCHEMA["name"]:
        raise ToolInputError(f"허용되지 않은 도구: {name}")
    try:
        values = json.loads(arguments)
    except json.JSONDecodeError as exc:
        raise ToolInputError("도구 인수가 올바른 JSON이 아닙니다.") from exc
    if not isinstance(values, dict) or set(values) != {"city", "nights"}:
        raise ToolInputError("도구 인수에는 city와 nights만 있어야 합니다.")
    return estimate_trip_cost(values["city"], values["nights"])
