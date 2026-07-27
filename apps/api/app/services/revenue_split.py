ECONOMY = {
    "episode_cost_coins": 25,
    "ad_reward_coins": 20,
    "revenue_split": {"creator": 0.6, "platform": 0.4},
    "min_payout_coins": 50000,
}


def compute_creator_coins(gross_coins: int) -> int:
    return int(gross_coins * ECONOMY["revenue_split"]["creator"])


def compute_platform_coins(gross_coins: int) -> int:
    return int(gross_coins * ECONOMY["revenue_split"]["platform"])