/**
 * Elenco utenti (Amministratore). Per ogni utente: modifica anagrafica e reset
 * password; per i pazienti, assegnazione/cambio del medico di riferimento (RF-3).
 */

import { useEffect, useState, type FormEvent } from 'react';
import {
  getUtenti,
  getMedici,
  associaMedico,
  aggiornaAnagrafica,
  resetPassword,
} from '../../lib/admin';
import type { UserWithProfile, DoctorProfile } from '../../lib/types';
import { Card, Button, Badge, Field, Loading, ErrorBox, Empty } from '../../components/ui';
import styles from '../../styles/data.module.css';

const RUOLO_LABEL: Record<string, string> = {
  admin: 'Amministratore',
  doctor: 'Medico',
  patient: 'Paziente',
};

export default function UtentiPage() {
  const [utenti, setUtenti] = useState<UserWithProfile[] | null>(null);
  const [medici, setMedici] = useState<DoctorProfile[]>([]);
  const [errore, setErrore] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  function ricarica() {
    getUtenti().then(setUtenti).catch((e) => setErrore(e.message));
  }

  useEffect(() => {
    ricarica();
    getMedici().then(setMedici).catch((e) => setErrore(e.message));
  }, []);

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Utenti</h1>
        <p className={styles.pageSubtitle}>
          Gestisci anagrafiche, credenziali e associazioni paziente-medico.
        </p>
      </div>

      {errore && <ErrorBox message={errore} />}
      {feedback && (
        <p className={`${styles.formFeedback} ${styles.feedbackOk}`} role="status">
          {feedback}
        </p>
      )}
      {!utenti && !errore && <Loading label="Caricamento utenti…" />}

      {utenti && (
        utenti.length === 0 ? (
          <Empty label="Nessun utente." />
        ) : (
          <div className={styles.stack}>
            {utenti.map((u) => (
              <UtenteCard
                key={u.id}
                utente={u}
                medici={medici}
                onDone={(msg) => { setFeedback(msg); ricarica(); }}
                onError={setErrore}
              />
            ))}
          </div>
        )
      )}
    </div>
  );
}

// =========================================================
// Card singolo utente
// =========================================================
function UtenteCard({
  utente,
  medici,
  onDone,
  onError,
}: {
  utente: UserWithProfile;
  medici: DoctorProfile[];
  onDone: (msg: string) => void;
  onError: (msg: string) => void;
}) {
  const profilo = utente.doctor_profile || utente.patient_profile;
  const [modifica, setModifica] = useState(false);
  const [nome, setNome] = useState(profilo?.nome ?? '');
  const [cognome, setCognome] = useState(profilo?.cognome ?? '');
  const [email, setEmail] = useState(utente.email);
  const [password, setPassword] = useState('');

  async function salvaAnagrafica(e: FormEvent) {
    e.preventDefault();
    try {
      await aggiornaAnagrafica(utente.id, { nome, cognome, email });
      setModifica(false);
      onDone('Anagrafica aggiornata.');
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Errore.');
    }
  }

  async function cambiaMedico(doctorId: string) {
    try {
      await associaMedico(utente.patient_profile!.id, doctorId ? Number(doctorId) : null);
      onDone('Medico di riferimento aggiornato.');
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Errore.');
    }
  }

  async function eseguiReset(e: FormEvent) {
    e.preventDefault();
    try {
      await resetPassword(utente.id, password);
      setPassword('');
      onDone('Password reimpostata.');
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Errore.');
    }
  }

  return (
    <Card>
      <div className={styles.rowBetween}>
        <div className={styles.row}>
          <strong>{profilo ? `${profilo.nome} ${profilo.cognome}` : utente.email}</strong>
          <Badge tone={utente.role === 'doctor' ? 'info' : utente.role === 'patient' ? 'success' : 'neutral'}>
            {RUOLO_LABEL[utente.role]}
          </Badge>
        </div>
        <span className={styles.notifMeta}>{utente.email}</span>
      </div>

      {/* Associazione medico di riferimento (solo pazienti) — RF-3 */}
      {utente.patient_profile && (
        <div className={styles.row} style={{ marginTop: 'var(--space-3)' }}>
          <label htmlFor={`medico-${utente.id}`} style={{ fontWeight: 600, fontSize: '0.85rem' }}>
            Medico di riferimento:
          </label>
          <select
            id={`medico-${utente.id}`}
            defaultValue={utente.patient_profile.doctor_id ?? ''}
            onChange={(e) => cambiaMedico(e.target.value)}
            style={{ padding: 'var(--space-1) var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}
          >
            <option value="">— Nessuno —</option>
            {medici.map((m) => (
              <option key={m.id} value={m.id}>Dr. {m.nome} {m.cognome}</option>
            ))}
          </select>
        </div>
      )}

      {/* Azioni */}
      <div className={styles.row} style={{ marginTop: 'var(--space-3)' }}>
        <Button small variant="secondary" onClick={() => setModifica((v) => !v)}>
          {modifica ? 'Annulla' : 'Modifica anagrafica'}
        </Button>
      </div>

      {/* Form modifica anagrafica */}
      {modifica && (
        <form onSubmit={salvaAnagrafica} style={{ marginTop: 'var(--space-3)' }}>
          <div className={`${styles.formGrid} ${styles.formGrid2}`}>
            {profilo && (
              <>
                <Field id={`nome-${utente.id}`} label="Nome" value={nome} onChange={setNome} />
                <Field id={`cognome-${utente.id}`} label="Cognome" value={cognome} onChange={setCognome} />
              </>
            )}
            <Field id={`email-${utente.id}`} label="Email" type="email" value={email} onChange={setEmail} />
          </div>
          <div className={styles.formActions}>
            <Button type="submit" small>Salva anagrafica</Button>
          </div>
        </form>
      )}

      {/* Reset password */}
      <form onSubmit={eseguiReset} style={{ marginTop: 'var(--space-3)' }}>
        <div className={`${styles.formGrid} ${styles.formGrid2}`}>
          <Field
            id={`pw-${utente.id}`}
            label="Reset password (min. 12 caratteri, complessa)"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder="Nuova password…"
          />
        </div>
        <div className={styles.formActions}>
          <Button type="submit" small variant="secondary" disabled={password.length < 12}>
            Reimposta password
          </Button>
        </div>
      </form>
    </Card>
  );
}
