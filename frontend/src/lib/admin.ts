/**
 * Tipi di input e funzioni API dell'attore AMMINISTRATORE + trigger Sistema.
 * Ogni funzione corrisponde a un endpoint di `backend/app/routers/admin.py`
 * o `sistema.py`.
 */

import { apiGet, apiPost, apiPut } from './api';
import type {
  UserWithProfile,
  DoctorProfile,
  PatientProfile,
  AuditLog,
} from './types';

// =========================================================
// TIPI DI INPUT
// =========================================================
export interface CreaMedicoInput {
  user: { email: string; role: 'doctor'; password: string };
  profile: { nome: string; cognome: string };
}

export interface CreaPazienteInput {
  user: { email: string; role: 'patient'; password: string };
  profile: {
    nome: string;
    cognome: string;
    fattori_rischio?: string | null;
    patologie_pregresse?: string | null;
    comorbita?: string | null;
  };
  doctor_id?: number | null;
}

export interface AnagraficaInput {
  nome?: string;
  cognome?: string;
  email?: string;
}

export interface ControlliSistemaResult {
  notifiche_create: number;
  dettaglio: string[];
}

// =========================================================
// FUNZIONI API — Amministratore
// =========================================================
export const getUtenti = () => apiGet<UserWithProfile[]>('/admin/utenti');
export const getMedici = () => apiGet<DoctorProfile[]>('/admin/medici');
export const getPazienti = () => apiGet<PatientProfile[]>('/admin/pazienti');

export const creaMedico = (body: CreaMedicoInput) =>
  apiPost<UserWithProfile>('/admin/medici', body);
export const creaPaziente = (body: CreaPazienteInput) =>
  apiPost<UserWithProfile>('/admin/pazienti', body);

export const associaMedico = (patientId: number, doctorId: number | null) =>
  apiPut<PatientProfile>(`/admin/pazienti/${patientId}/medico`, { doctor_id: doctorId });

export const aggiornaAnagrafica = (userId: number, body: AnagraficaInput) =>
  apiPut<UserWithProfile>(`/admin/utenti/${userId}/anagrafica`, body);

export const resetPassword = (userId: number, password: string) =>
  apiPost<{ message: string }>(`/admin/utenti/${userId}/reset-password`, { password });

export const getAuditLogs = (pazienteId?: number) =>
  apiGet<AuditLog[]>(
    pazienteId != null ? `/admin/audit-logs?paziente_id=${pazienteId}` : '/admin/audit-logs',
  );

// =========================================================
// FUNZIONI API — Sistema (trigger controlli)
// =========================================================
export const eseguiControlliSistema = () =>
  apiPost<ControlliSistemaResult>('/sistema/esegui-controlli');
