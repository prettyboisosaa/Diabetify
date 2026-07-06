/**
 * Client HTTP autenticato.
 *
 * Estende il pattern gia' usato in `auth.ts` (fetch + API_URL + throw su !res.ok
 * leggendo `detail`) aggiungendo automaticamente l'header
 * `Authorization: Bearer <token>` letto da localStorage.
 *
 * Su 401 (sessione scaduta / token non valido) esegue logout e rimanda al login.
 */

import { getToken, logout } from './auth';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

/** Errore applicativo con lo status HTTP, cosi' le pagine possono reagire. */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/** Nucleo condiviso: costruisce la richiesta, gestisce token, errori e parsing. */
async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // Sessione scaduta / non autenticato: pulisci e torna al login
  if (res.status === 401) {
    logout();
    window.location.href = '/login';
    throw new ApiError('Sessione scaduta', 401);
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: 'Errore di rete' }));
    throw new ApiError(data.detail ?? 'Richiesta fallita', res.status);
  }

  // 204 No Content oppure corpo vuoto
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const apiGet = <T>(path: string) => request<T>('GET', path);
export const apiPost = <T>(path: string, body?: unknown) => request<T>('POST', path, body);
export const apiPut = <T>(path: string, body?: unknown) => request<T>('PUT', path, body);
export const apiPatch = <T>(path: string, body?: unknown) => request<T>('PATCH', path, body);
