/**
 * Tipi di dominio CONDIVISI tra gli attori (medico e paziente).
 * Rispecchiano gli schemi di risposta Pydantic del backend.
 * Nota: niente `enum` TS (vietato da `erasableSyntaxOnly`) -> union di stringhe.
 */

export type Momento = 'prima_pasto' | 'dopo_pasto';
export type Unita = 'mg' | 'UI' | 'ml' | 'compresse';
export type Gravita = 'lieve' | 'moderata' | 'grave';
export type TipoNotifica =
  | 'sollecito_assunzione'
  | 'mancata_aderenza'
  | 'glicemia_fuori_soglia';
export type Severita = 'info' | 'warning' | 'critical';

export interface DoctorProfile {
  id: number;
  user_id: number;
  nome: string;
  cognome: string;
}

export interface PatientProfile {
  id: number;
  user_id: number;
  doctor_id: number | null;
  nome: string;
  cognome: string;
  fattori_rischio: string | null;
  patologie_pregresse: string | null;
  comorbita: string | null;
}

export interface Glicemia {
  id: number;
  patient_id: number;
  valore: number;
  momento: Momento;
  timestamp: string;
  fuori_soglia: boolean;
}

export interface GlicemiaAggregata {
  periodo_inizio: string;
  periodo_fine: string;
  media: number;
  minimo: number;
  massimo: number;
  num_misurazioni: number;
  num_fuori_soglia: number;
}

export interface Terapia {
  id: number;
  patient_id: number;
  doctor_id: number;
  farmaco: string;
  assunzioni_giornaliere: number;
  quantita: string; // Decimal serializzato come stringa
  unita: Unita;
  indicazioni: string | null;
  data_inizio: string;
  is_active: boolean;
}

export interface Assunzione {
  id: number;
  patient_id: number;
  terapia_id: number;
  farmaco: string;
  quantita_assunta: string;
  unita: Unita;
  timestamp: string;
}

export interface Sintomo {
  id: number;
  patient_id: number;
  descrizione: string;
  gravita: Gravita | null;
  data_inizio: string;
  data_fine: string | null;
  note: string | null;
}

export interface PatologiaConcomitante {
  id: number;
  patient_id: number;
  descrizione: string;
  data_inizio: string;
  data_fine: string | null;
  note: string | null;
}

export interface TerapiaParallela {
  id: number;
  patient_id: number;
  farmaco: string;
  posologia: string | null;
  data_inizio: string;
  data_fine: string | null;
  note: string | null;
}

export interface Messaggio {
  id: number;
  mittente_id: number;
  destinatario_id: number;
  oggetto: string;
  corpo: string;
  inviato_at: string;
  letto_at: string | null;
}

export interface Notifica {
  id: number;
  destinatario_id: number;
  paziente_riferimento_id: number | null;
  tipo: TipoNotifica;
  severita: Severita;
  messaggio: string;
  creato_at: string;
  letta_at: string | null;
  risolta_at: string | null;
}

export type Ruolo = 'admin' | 'doctor' | 'patient';

/** Utente con il relativo profilo (usato lato amministratore). */
export interface UserWithProfile {
  id: number;
  email: string;
  role: Ruolo;
  is_active: boolean;
  doctor_profile: DoctorProfile | null;
  patient_profile: PatientProfile | null;
}

/** Voce del registro audit (RF-15). */
export interface AuditLog {
  id: number;
  operator_id: number;
  azione: string;
  target_paziente_id: number | null;
  timestamp: string;
}
