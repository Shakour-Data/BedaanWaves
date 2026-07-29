/**
 * auth.ts
 * ---------------------------------------------------------------------------
 * شبیه‌سازی احراز هویت. در production با API بک‌ند جایگزین می‌شود.
 */

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export async function loginApi(payload: LoginPayload): Promise<{ token: string; user: { name: string; email: string } }> {
  await new Promise((r) => setTimeout(r, 400));
  return { token: "mock-jwt-token", user: { name: payload.email.split("@")[0], email: payload.email } };
}

export async function registerApi(payload: RegisterPayload): Promise<{ token: string; user: { name: string; email: string } }> {
  await new Promise((r) => setTimeout(r, 400));
  return { token: "mock-jwt-token", user: { name: payload.name, email: payload.email } };
}
