/**
 * RF-7 (lato medico): lettura dei messaggi ricevuti dai pazienti e risposta.
 * Cliccando "Rispondi" si apre un form; l'invio usa come destinatario il
 * mittente del messaggio originale.
 */

import { useEffect, useState, type FormEvent } from 'react';
import {
  getMessaggi,
  rispondiMessaggio,
  segnaMessaggioLetto,
  type Messaggio,
} from '../../lib/medico';
import { Card, Button, Badge, Field, Loading, ErrorBox, Empty } from '../../components/ui';
import { formatDataOra } from '../../lib/format';
import styles from '../../styles/data.module.css';

export default function MessaggiPage() {
  const [messaggi, setMessaggi] = useState<Messaggio[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [rispostaA, setRispostaA] = useState<Messaggio | null>(null);
  const [corpo, setCorpo] = useState('');
  const [invio, setInvio] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  function ricarica() {
    getMessaggi().then(setMessaggi).catch((e) => setErrore(e.message));
  }

  useEffect(ricarica, []);

  // Apre il form di risposta e segna il messaggio come letto
  async function apriRisposta(m: Messaggio) {
    setRispostaA(m);
    setCorpo('');
    setFeedback(null);
    if (m.letto_at === null) {
      await segnaMessaggioLetto(m.id).catch(() => {});
      ricarica();
    }
  }

  async function inviaRisposta(e: FormEvent) {
    e.preventDefault();
    if (!rispostaA) return;
    setInvio(true);
    try {
      await rispondiMessaggio({
        destinatario_id: rispostaA.mittente_id,
        oggetto: `Re: ${rispostaA.oggetto}`,
        corpo,
      });
      setFeedback('Risposta inviata al paziente.');
      setRispostaA(null);
      setCorpo('');
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : 'Errore durante l’invio.');
    } finally {
      setInvio(false);
    }
  }

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Messaggi</h1>
        <p className={styles.pageSubtitle}>Comunicazioni ricevute dai pazienti.</p>
      </div>

      {errore && <ErrorBox message={errore} />}
      {feedback && (
        <p className={`${styles.formFeedback} ${styles.feedbackOk}`} role="status">
          {feedback}
        </p>
      )}
      {!messaggi && !errore && <Loading label="Caricamento messaggi…" />}

      {messaggi && (
        messaggi.length === 0 ? (
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

                <div className={styles.row} style={{ marginTop: 'var(--space-3)' }}>
                  <Button small variant="secondary" onClick={() => apriRisposta(m)}>
                    Rispondi
                  </Button>
                </div>

                {rispostaA?.id === m.id && (
                  <form onSubmit={inviaRisposta} style={{ marginTop: 'var(--space-4)' }}>
                    <Field
                      id={`risposta-${m.id}`}
                      label={`Rispondi a "${m.oggetto}"`}
                      as="textarea"
                      value={corpo}
                      onChange={setCorpo}
                      required
                      disabled={invio}
                      placeholder="Scrivi la tua risposta…"
                    />
                    <div className={styles.formActions}>
                      <Button type="submit" disabled={invio || !corpo.trim()}>
                        {invio ? 'Invio…' : 'Invia risposta'}
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => setRispostaA(null)}
                        disabled={invio}
                      >
                        Annulla
                      </Button>
                    </div>
                  </form>
                )}
              </Card>
            ))}
          </div>
        )
      )}
    </div>
  );
}
