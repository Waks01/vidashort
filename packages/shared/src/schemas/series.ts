import { z } from "zod";

export const Genre = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
});

export const EpisodeMeta = z.object({
  id: z.string(),
  seriesId: z.string(),
  episodeNumber: z.number(),
  title: z.string(),
  cost: z.number(),
  isFree: z.boolean(),
  durationSec: z.number(),
  thumbnailUrl: z.string().url(),
});

export const Series = z.object({
  id: z.string(),
  title: z.string(),
  synopsis: z.string(),
  posterUrl: z.string().url(),
  genres: z.array(Genre),
  creatorId: z.string(),
  status: z.enum(["draft", "pending", "approved", "rejected"]),
  viewCount: z.number(),
  createdAt: z.coerce.date(),
});
