const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const TOKEN_KEY = 'diabetify_token';
const ROLE_KEY = 'diabetify_role';

export type Role = 'admin' | 'doctor' | 'patient';

export async function login(email: string, password: string): Promise<Role> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: 'Errore di rete' }));
    throw new Error(data.detail ?? 'Login fallito');
  }

  const { access_token, role } = await res.json();
  localStorage.setItem(TOKEN_KEY, access_token);
  localStorage.setItem(ROLE_KEY, role);
  return role as Role;
}

export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY);

export const getRole = (): Role | null =>
  localStorage.getItem(ROLE_KEY) as Role | null;

export const isAuthenticated = (): boolean => Boolean(getToken());

export const logout = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
};
