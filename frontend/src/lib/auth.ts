export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export async function loginApi(_payload: LoginPayload): Promise<{ token: string; user: { name: string; email: string } }> {
  throw new Error('loginApi mock has been removed. Use the auth store login action instead.');
}

export async function registerApi(_payload: RegisterPayload): Promise<{ token: string; user: { name: string; email: string } }> {
  throw new Error('registerApi mock has been removed. Use the auth store register action instead.');
}
