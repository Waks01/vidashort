import { z } from "zod";

export const Comment = z.object({
  id: z.string(),
  user: z.object({
    id: z.string(),
    name: z.string(),
    avatarUrl: z.string().url().nullable(),
  }),
  body: z.string(),
  likes: z.number(),
  liked: z.boolean(),
  replies: z.array(z.any()).default([]),
  createdAt: z.string().datetime().nullable(),
});

export const CommentCreate = z.object({
  body: z.string().min(1).max(1000),
  parentId: z.string().nullable().default(null),
});
