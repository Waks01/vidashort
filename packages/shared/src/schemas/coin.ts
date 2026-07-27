import { z } from "zod";

export const CoinTxn = z.object({
  id: z.string(),
  userId: z.string(),
  amount: z.number(),
  direction: z.enum(["in", "out"]),
  reason: z.enum(["unlock", "purchase", "reward", "payout", "admin"]),
  refId: z.string().nullable(),
  createdAt: z.coerce.date(),
});
