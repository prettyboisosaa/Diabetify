/**
 * RF-7 (UC-7): il paziente scrive al proprio medico di riferimento e legge le
 * risposte ricevute. Il destinatario e' determinato dal backend (medico di
 * riferimento): qui si inseriscono solo oggetto e corpo.
 */

import { useEffect, useState, type FormEvent } from 'react';
import {
  getMessaggi,
  inviaMessaggio,
  segnaMessaggioLetto,
} from '../../lib/paziente';
import type { Messaggio } from '../../lib/types';
import { Card, Button, Badge, Field, Loading, ErrorBox, Empty } from '../../components/ui';
import { formatDataOra } from '../../lib/format';
import styles from '../../styles/data.module.css';

export default function MessaggiPage() {
  const [messaggi, setMessaggi] = useState<Messaggio[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [oggetto, setOggetto] = useState('');
  const [corpo, setCorpo] = useState('');
  const [invio, setInvio] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; testo: string } | null>(null);

  function ricarica() {
    getMessaggi().then(setMessaggi).catch((e) => setErrore(e.message));
  }

  useEffect(ricarica, []);

  async function handleInvia(e: FormEvent) {
    e.preventDefault();
    setInvio(true);
    setFeedback(null);
    try {
      await inviaMessaggio({ oggetto, corpo });
      setOggetto('');
      setCorpo('');
      setFeedback({ ok: true, testo: 'Messaggio inviato al tuo medico.' });
    } catch (err) {
      setFeedback({
        ok: false,
        testo: err instanceof Error ? err.message : 'Errore durante l’invio.',
      });
    } finally {
      setInvio(false);
    }
  }

  async function segnaLetto(m: Messaggio) {
    if (m.letto_at !== null) return;
    await segnaMessaggioLetto(m.id).catch(() => {});
    ricarica();
  }

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Messaggi</h1>
        <p className={styles.pageSubtitle}>Comunica con il tuo medico di riferimento.</p>
      </div>

      {errore && <ErrorBox message={errore} />}

      <div className={styles.stack}>
        {/* ---------- Nuovo messaggio ---------- */}
        <Card title="Scrivi al tuo medico">
          <form onSubmit={handleInvia}>
            <div className={styles.formGrid}>
              <Field
                id="oggetto"
                label="Oggetto"
                value={oggetto}
                onChange={setOggetto}
                required
                disabled={invio}
                placeholder="Es. Dubbio sul dosaggio"
              />
              <Field
                id="corpo"
                label="Messaggio"
                as="textarea"
                value={corpo}
                onChange={setCorpo}
                required
                disabled={invio}
                placeholder="Scrivi la tua richiesta…"
              />
            </div>
            <div className={styles.formActions}>
              <Button type="submit" disabled={invio || !oggetto.trim() || !corpo.trim()}>
                {invio ? 'Invio…' : 'Invia messaggio'}
              </Button>
            </div>
            {feedback && (
              <p
                className={`${styles.formFeedback} ${
                  feedback.ok ? styles.feedbackOk : styles.feedbackErr
                }`}
                role="alert"
              >
                {feedback.testo}
              </p>
            )}
          </form>
        </Card>

        {/* ---------- Messaggi ricevuti ---------- */}
        {!messaggi ? (
          <Loading label="Caricamento messaggi…" />
        ) : messaggi.length === 0 ? (
          <Empty label="Nessun messaggio ricevuto." />
        ) : (
          <div className={styles.stack}>
            {messaggi.map((m) => (
              <Card key={m.id} className={m.letto_at === null ? styles.msgUnread : undefined}>
                <div className={styles.rowBetween}>
                  <div className={styles.row}>
                    <strong>{m.oggetto}</strong>
                    {m.letto_at === null && <Badge tone="info">Nuovo</Badge>}
                  </div>
                  <span className={styles.notifMeta}>{formatDataOra(m.inviato_at)}</span>
                </div>
                <p className={styles.msgBody}>{m.corpo}</p>
                {m.letto_at === null && (
                  <div className={styles.row} style={{ marginTop: 'var(--space-3)' }}>
                    <Button small variant="secondary" onClick={() => segnaLetto(m)}>
                      Segna come letto
                    </Button>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
