import { z } from "zod";

export const UserSchema = z.object({
  name: z.string(),
  email: z.string(),
  age: z.number().optional(),
});

export interface ApiResponse {
  status: number;
  data: unknown;
  message?: string;
}

export type PaginationParams = {
  page: number;
  limit: number;
  sortBy?: string;
};

export function validateInput(data: unknown): boolean {
  return UserSchema.safeParse(data).success;
}

export async function fetchUsers(
  params: PaginationParams
): Promise<ApiResponse> {
  return { status: 200, data: [], message: "ok" };
}

export const transformName = (name: string, uppercase: boolean): string => {
  return uppercase ? name.toUpperCase() : name;
};

function _internalHelper(x: number): number {
  return x * 2;
}
