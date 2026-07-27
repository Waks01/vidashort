import { z } from "zod";

export const AdCap = z.object({
  userId: z.string(),
  watchedToday: z.number(),
  dailyLimit: z.number().default(100),
  resetAt: z.coerce.date(),
});
