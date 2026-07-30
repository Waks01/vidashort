import { z } from "zod";

export const WatchHistory = z.object({
  id: z.string(),
  seriesId: z.string(),
  episodeId: z.string(),
  position_s: z.number(),
  completed: z.boolean(),
  watchedAt: z.string().datetime().nullable(),
});
