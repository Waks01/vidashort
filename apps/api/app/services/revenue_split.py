"""
Locked product economics. Per CLAUDE.md §4 these numbers must not change without
explicit user approval — they are the unit economics of vidashort.

Exposed as named constants so callers can't drift from the source of truth.
"""

# Episode unlock cost — locked at 25 coins (₦2.50 at 10 coins = ₦1)
EPISODE_UNLOCK_COST: int = 25

# Rewarded ad reward — locked at 20 coins (₦2.00)
REWARDED_AD_REWARD: int = 20

# Creator / platform revenue split — locked at 60/40
CREATOR_SPLIT: float = 0.6
PLATFORM_SPLIT: float = 0.4

# Daily ad cap per user — locked at 100
DAILY_AD_CAP: int = 100

# Minimum creator payout — locked at 50,000 coins (₦5,000)
MIN_PAYOUT_COINS: int = 50_000

# Coin ↔ Naira rate — locked at 10 coins = ₦1
COINS_PER_NAIRA: int = 10


def compute_creator_coins(gross_coins: int) -> int:
    """60% of gross_coins to the creator."""
    return int(gross_coins * CREATOR_SPLIT)


def compute_platform_coins(gross_coins: int) -> int:
    """40% of gross_coins to the platform."""
    return int(gross_coins * PLATFORM_SPLIT)