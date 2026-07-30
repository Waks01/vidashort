import { z } from "zod";

export const PushToken = z.object({
  id: z.string(),
  userId: z.string(),
  token: z.string(),
  platform: z.enum(["ios", "android", "web"]),
  active: z.boolean(),
  createdAt: z.string().datetime().nullable(),
});

export const DeviceRegister = z.object({
  token: z.string().min(10),
  platform: z.enum(["ios", "android", "web"]),
});
