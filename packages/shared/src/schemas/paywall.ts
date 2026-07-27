import { z } from "zod";

export const PaywallDecision = z.object({
  path: z.enum(["vip", "coins", "ad", "premium"]),
  requiresCoins: z.number(),
  requiresAd: z.boolean(),
});
