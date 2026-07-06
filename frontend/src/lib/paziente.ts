/**
 * Tipi di input e funzioni API dell'attore PAZIENTE.
 * Ogni funzione corrisponde a un endpoint di `backend/app/routers/paziente.py`.
 * I tipi di risposta sono quelli condivisi in ./types.
 */

import { apiGet, apiPost, apiPut, apiPatch } from './api';
import type {
  PatientProfile,
  Glicemia,
  GlicemiaAggregata,
  Terapia,
  Assunzione,
  Sintomo,
  PatologiaConcomitante,
  TerapiaParallela,
  Messaggio,
  Notifica,
  Momento,
  Gravita,
  Unita,
} from './types';

// =========================================================
// TIPI DI INPUT (payload delle create/update)
// =========================================================
export interface GlicemiaInput {
  valore: number;
  momento: Momento;
}

export interface AssunzioneInput {
  terapia_id: number;
  farmaco: string;
  quantita_assunta: string;
  unita: Unita;
}

export interface SintomoInput {
  descrizione: string;
  gravita?: Gravita | null;
  data_inizio: string;
  data_fine?: string | null;
  note?: string | null;
}

export interface DiarioVoceInput {
  descrizione: string;
  data_inizio: string;
  data_fine?: string | null;
  note?: string | null;
}

export interface TerapiaParallelaInput {
  farmaco: string;
  posologia?: string | null;
  data_inizio: string;
  data_fine?: string | null;
  note?: string | null;
}

// Per gli update (chiusura/correzione) tutti i campi sono opzionali
export type SintomoUpdateInput = Partial<SintomoInput>;
export type DiarioVoceUpdateInput = Partial<DiarioVoceInput>;
export type TerapiaParallelaUpdateInput = Partial<TerapiaParallelaInput>;

export interface MessaggioInput {
  oggetto: string;
  corpo: string;
}

// =========================================================
// FUNZIONI API
// =========================================================

// Profilo
export const getProfilo = () => apiGet<PatientProfile>('/paziente/me');

// Glicemie (RF-4)
export const getGlicemie = () => apiGet<Glicemia[]>('/paziente/glicemie');
export const getGlicemieAggregate = (periodo: 'settimana' | 'mese') =>
  apiGet<GlicemiaAggregata[]>(`/paziente/glicemie/aggregato?periodo=${periodo}`);
export const registraGlicemia = (body: GlicemiaInput) =>
  apiPost<Glicemia>('/paziente/glicemie', body);

// Terapie prescritte (lettura) + assunzioni (RF-6)
export const getTerapie = () => apiGet<Terapia[]>('/paziente/terapie');
export const getAssunzioni = () => apiGet<Assunzione[]>('/paziente/assunzioni');
export const registraAssunzione = (body: AssunzioneInput) =>
  apiPost<Assunzione>('/paziente/assunzioni', body);

// Diario clinico (RF-5)
export const getSintomi = () => apiGet<Sintomo[]>('/paziente/sintomi');
export const creaSintomo = (body: SintomoInput) =>
  apiPost<Sintomo>('/paziente/sintomi', body);
export const aggiornaSintomo = (id: number, body: SintomoUpdateInput) =>
  apiPut<Sintomo>(`/paziente/sintomi/${id}`, body);

export const getPatologie = () =>
  apiGet<PatologiaConcomitante[]>('/paziente/patologie-concomitanti');
export const creaPatologia = (body: DiarioVoceInput) =>
  apiPost<PatologiaConcomitante>('/paziente/patologie-concomitanti', body);
export const aggiornaPatologia = (id: number, body: DiarioVoceUpdateInput) =>
  apiPut<PatologiaConcomitante>(`/paziente/patologie-concomitanti/${id}`, body);

export const getTerapieParallele = () =>
  apiGet<TerapiaParallela[]>('/paziente/terapie-parallele');
export const creaTerapiaParallela = (body: TerapiaParallelaInput) =>
  apiPost<TerapiaParallela>('/paziente/terapie-parallele', body);
export const aggiornaTerapiaParallela = (id: number, body: TerapiaParallelaUpdateInput) =>
  apiPut<TerapiaParallela>(`/paziente/terapie-parallele/${id}`, body);

// Messaggi (RF-7)
export const getMessaggi = () => apiGet<Messaggio[]>('/paziente/messaggi');
export const inviaMessaggio = (body: MessaggioInput) =>
  apiPost<Messaggio>('/paziente/messaggi', body);
export const segnaMessaggioLetto = (id: number) =>
  apiPatch<Messaggio>(`/paziente/messaggi/${id}/letto`);

// Notifiche (RF-12/13)
export const getNotifiche = (soloAperte = false) =>
  apiGet<Notifica[]>(`/paziente/notifiche?solo_aperte=${soloAperte}`);
export const segnaNotificaLetta = (id: number) =>
  apiPatch<Notifica>(`/paziente/notifiche/${id}/letta`);
export const segnaNotificaRisolta = (id: number) =>
  apiPatch<Notifica>(`/paziente/notifiche/${id}/risolta`);
