/**
 * RF-2 (UC-1): l'amministratore inserisce i dati iniziali e le credenziali di un
 * nuovo medico o paziente. Per il paziente è possibile indicare subito il medico
 * di riferimento (RF-3).
 */

import { useEffect, useState, type FormEvent } from 'react';
import {
  creaMedico,
  creaPaziente,
  getMedici,
} from '../../lib/admin';
import type { DoctorProfile } from '../../lib/types';
import { Card, Button, Field } from '../../components/ui';
import styles from '../../styles/data.module.css';

type Ruolo = 'doctor' | 'patient';

export default function CreaUtentePage() {
  const [ruolo, setRuolo] = useState<Ruolo>('doctor');
  const [medici, setMedici] = useState<DoctorProfile[]>([]);

  // Campi comuni
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [nome, setNome] = useState('');
  const [cognome, setCognome] = useState('');
  // Campi paziente
  const [doctorId, setDoctorId] = useState('');
  const [fattoriRischio, setFattoriRischio] = useState('');

  const [invio, setInvio] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; testo: string } | null>(null);

  useEffect(() => {
    getMedici().then(setMedici).catch(() => {});
  }, []);

  function reset() {
    setEmail(''); setPassword(''); setNome(''); setCognome('');
    setDoctorId(''); setFattoriRischio('');
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setInvio(true);
    setFeedback(null);
    try {
      if (ruolo === 'doctor') {
        await creaMedico({
          user: { email, role: 'doctor', password },
          profile: { nome, cognome },
        });
      } else {
        await creaPaziente({
          user: { email, role: 'patient', password },
          profile: { nome, cognome, fattori_rischio: fattoriRischio || null },
          doctor_id: doctorId ? Number(doctorId) : null,
        });
      }
      setFeedback({ ok: true, testo: 'Utente creato con successo.' });
      reset();
    } catch (err) {
      setFeedback({
        ok: false,
        testo: err instanceof Error ? err.message : 'Errore durante la creazione.',
      });
    } finally {
      setInvio(false);
    }
  }

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Crea utente</h1>
        <p className={styles.pageSubtitle}>
          Inserisci le credenziali iniziali di un medico o di un paziente.
        </p>
      </div>

      <Card>
        {/* Selettore ruolo */}
        <div className={styles.tabs} style={{ marginBottom: 'var(--space-4)' }}>
          <button
            className={`${styles.tab} ${ruolo === 'doctor' ? styles.tabActive : ''}`}
            onClick={() => setRuolo('doctor')}
            type="button"
          >
            Medico
          </button>
          <button
            className={`${styles.tab} ${ruolo === 'patient' ? styles.tabActive : ''}`}
            onClick={() => setRuolo('patient')}
            type="button"
          >
            Paziente
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={`${styles.formGrid} ${styles.formGrid2}`}>
            <Field id="nome" label="Nome" value={nome} onChange={setNome} required disabled={invio} />
            <Field id="cognome" label="Cognome" value={cognome} onChange={setCognome} required disabled={invio} />
            <Field id="email" label="Email" type="email" value={email} onChange={setEmail} required disabled={invio} placeholder="nome@esempio.it" />
            <Field
              id="password"
              label="Password (min. 12, con maiuscola, minuscola, cifra e simbolo)"
              type="password"
              value={password}
              onChange={setPassword}
              required
              disabled={invio}
            />

            {ruolo === 'patient' && (
              <Field
                id="doctor"
                label="Medico di riferimento (opzionale)"
                as="select"
                value={doctorId}
                onChange={setDoctorId}
                disabled={invio}
              >
                <option value="">— Nessuno —</option>
                {medici.map((m) => (
                  <option key={m.id} value={m.id}>Dr. {m.nome} {m.cognome}</option>
                ))}
              </Field>
            )}
          </div>

          {ruolo === 'patient' && (
            <div style={{ marginTop: 'var(--space-4)' }}>
              <Field
                id="fattori"
                label="Fattori di rischio (opzionale)"
                as="textarea"
                value={fattoriRischio}
                onChange={setFattoriRischio}
                disabled={invio}
              />
            </div>
          )}

          <div className={styles.formActions}>
            <Button type="submit" disabled={invio}>
              {invio ? 'Creazione…' : `Crea ${ruolo === 'doctor' ? 'medico' : 'paziente'}`}
            </Button>
          </div>

          {feedback && (
            <p
              className={`${styles.formFeedback} ${feedback.ok ? styles.feedbackOk : styles.feedbackErr}`}
              role="alert"
            >
              {feedback.testo}
            </p>
          )}
        </form>
      </Card>
    </div>
  );
}
