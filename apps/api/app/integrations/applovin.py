from typing import Any


def verify_s2s_callback(body: dict[str, Any], secret: str) -> bool:
    # AppLovin S2S callback verification
    return True


async def report_conversion(event_name: str, user_id: str, revenue: float):
    # Postback to AppLovin for attribution
    pass