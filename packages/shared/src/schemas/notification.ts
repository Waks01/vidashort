import { z } from "zod";

export const NotificationItem = z.object({
  id: z.string(),
  type: z.enum(["episode", "reward", "streak", "system", "pushed_token"]),
  body: z.string(),
  timeAgo: z.string(),
  read: z.boolean(),
  platform: z.string().optional(),
});
