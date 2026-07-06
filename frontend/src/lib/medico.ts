/**
 * Tipi e funzioni API dell'attore MEDICO.
 *
 * Ogni funzione corrisponde a un endpoint di `backend/app/routers/medico.py`.
 * I tipi rispecchiano gli schemi Pydantic di risposta.
 * Nota: niente `enum` TS (vietato da `erasableSyntaxOnly`) -> union di stringhe.
 */

import { apiGet, apiPost, apiPut, apiPatch } from './api';
import type {
  DoctorProfile,
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
  Unita,
} from './types';

// I tipi di dominio condivisi vivono in ./types; qui si ri-esportano per
// compatibilita' con gli import esistenti delle pagine medico.
export type * from './types';

// Riga sintetica dell'elenco pazienti: specifica del lato medico
export interface PazienteListItem {
  id: number;
  nome: string;
  cognome: string;
  doctor_id: number | null;
  num_notifiche_aperte: number;
  ultima_glicemia: number | null;
}

// Payload per creazione/modifica terapia (RF-8)
export interface TerapiaCreateInput {
  patient_id: number;
  farmaco: string;
  assunzioni_giornaliere: number;
  quantita: string;
  unita: Unita;
  indicazioni?: string | null;
}

export interface TerapiaUpdateInput {
  farmaco?: string;
  assunzioni_giornaliere?: number;
  quantita?: string;
  unita?: Unita;
  indicazioni?: string | null;
  is_active?: boolean;
}

export interface AnamnesiInput {
  fattori_rischio?: string | null;
  patologie_pregresse?: string | null;
  comorbita?: string | null;
}

// =========================================================
// FUNZIONI API
// =========================================================

// Profilo
export const getProfiloMedico = () => apiGet<DoctorProfile>('/medico/me');

// Pazienti & dati clinici (RF-9)
export const getPazienti = () => apiGet<PazienteListItem[]>('/medico/pazienti');
export const getScheda = (id: number) => apiGet<PatientProfile>(`/medico/pazienti/${id}`);
export const getGlicemie = (id: number) =>
  apiGet<Glicemia[]>(`/medico/pazienti/${id}/glicemie`);
export const getGlicemieAggregate = (id: number, periodo: 'settimana' | 'mese') =>
  apiGet<GlicemiaAggregata[]>(`/medico/pazienti/${id}/glicemie/aggregato?periodo=${periodo}`);
export const getSintomi = (id: number) =>
  apiGet<Sintomo[]>(`/medico/pazienti/${id}/sintomi`);
export const getPatologieConcomitanti = (id: number) =>
  apiGet<PatologiaConcomitante[]>(`/medico/pazienti/${id}/patologie-concomitanti`);
export const getTerapieParallele = (id: number) =>
  apiGet<TerapiaParallela[]>(`/medico/pazienti/${id}/terapie-parallele`);
export const getAssunzioni = (id: number) =>
  apiGet<Assunzione[]>(`/medico/pazienti/${id}/assunzioni`);

// Terapie (RF-8)
export const getTerapie = (id: number) =>
  apiGet<Terapia[]>(`/medico/pazienti/${id}/terapie`);
export const creaTerapia = (id: number, body: TerapiaCreateInput) =>
  apiPost<Terapia>(`/medico/pazienti/${id}/terapie`, body);
export const aggiornaTerapia = (terapiaId: number, body: TerapiaUpdateInput) =>
  apiPut<Terapia>(`/medico/terapie/${terapiaId}`, body);

// Anamnesi (RF-10)
export const aggiornaAnamnesi = (id: number, body: AnamnesiInput) =>
  apiPut<PatientProfile>(`/medico/pazienti/${id}/anamnesi`, body);

// Notifiche (RF-13/14)
export const getNotifiche = (soloAperte = false) =>
  apiGet<Notifica[]>(`/medico/notifiche?solo_aperte=${soloAperte}`);
export const segnaNotificaLetta = (id: number) =>
  apiPatch<Notifica>(`/medico/notifiche/${id}/letta`);
export const segnaNotificaRisolta = (id: number) =>
  apiPatch<Notifica>(`/medico/notifiche/${id}/risolta`);

// Messaggi (RF-7)
export const getMessaggi = () => apiGet<Messaggio[]>('/medico/messaggi');
export const rispondiMessaggio = (body: {
  destinatario_id: number;
  oggetto: string;
  corpo: string;
}) => apiPost<Messaggio>('/medico/messaggi', body);
export const segnaMessaggioLetto = (id: number) =>
  apiPatch<Messaggio>(`/medico/messaggi/${id}/letto`);
