import { z } from "zod";

export const Favorite = z.object({
  id: z.string(),
  userId: z.string(),
  seriesId: z.string(),
  createdAt: z.string().datetime().nullable(),
});
