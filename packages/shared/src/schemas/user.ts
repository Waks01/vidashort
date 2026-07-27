import { z } from "zod";

export const User = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string(),
  avatarUrl: z.string().url().nullable(),
  role: z.enum(["viewer", "creator", "admin"]),
  coins: z.number(),
  isVip: z.boolean(),
  vipExpiresAt: z.coerce.date().nullable(),
  createdAt: z.coerce.date(),
});

export const UserIdentity = z.object({
  id: z.string(),
  userId: z.string(),
  provider: z.enum(["email", "apple", "google"]),
  providerId: z.string(),
  email: z.string().email(),
});
