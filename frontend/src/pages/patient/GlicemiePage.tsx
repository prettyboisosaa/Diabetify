/**
 * RF-4 (UC-4): il paziente registra le rilevazioni glicemiche (valore + momento)
 * e consulta lo storico in dettaglio e l'andamento aggregato (RF-9, self).
 * Le rilevazioni sono immutabili (solo creazione + lettura).
 */

import { useEffect, useState, type FormEvent } from 'react';
import {
  registraGlicemia,
  getGlicemie,
  getGlicemieAggregate,
} from '../../lib/paziente';
import type { Glicemia, GlicemiaAggregata, Momento } from '../../lib/types';
import { Card, Button, Badge, Field, Loading, ErrorBox, Empty } from '../../components/ui';
import { formatData, formatDataOra } from '../../lib/format';
import styles from '../../styles/data.module.css';

const MOMENTO_LABEL: Record<string, string> = {
  prima_pasto: 'Prima del pasto',
  dopo_pasto: 'Dopo il pasto',
};

export default function GlicemiePage() {
  const [dettaglio, setDettaglio] = useState<Glicemia[] | null>(null);
  const [aggregato, setAggregato] = useState<GlicemiaAggregata[] | null>(null);
  const [periodo, setPeriodo] = useState<'settimana' | 'mese'>('settimana');
  const [errore, setErrore] = useState<string | null>(null);

  // Stato del form
  const [valore, setValore] = useState('');
  const [momento, setMomento] = useState<Momento>('prima_pasto');
  const [invio, setInvio] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; testo: string } | null>(null);

  function ricaricaDettaglio() {
    getGlicemie().then(setDettaglio).catch((e) => setErrore(e.message));
  }

  useEffect(ricaricaDettaglio, []);

  // Aggregato: ricaricato al cambio periodo e dopo un inserimento
  useEffect(() => {
    setAggregato(null);
    getGlicemieAggregate(periodo).then(setAggregato).catch((e) => setErrore(e.message));
  }, [periodo, dettaglio]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setInvio(true);
    setFeedback(null);
    try {
      await registraGlicemia({ valore: Number(valore), momento });
      setValore('');
      setFeedback({ ok: true, testo: 'Rilevazione registrata.' });
      ricaricaDettaglio();
    } catch (err) {
      setFeedback({
        ok: false,
        testo: err instanceof Error ? err.message : 'Errore durante il salvataggio.',
      });
    } finally {
      setInvio(false);
    }
  }

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Glicemie</h1>
        <p className={styles.pageSubtitle}>
          Registra le tue misurazioni e tieni sotto controllo l'andamento.
        </p>
      </div>

      {errore && <ErrorBox message={errore} />}

      <div className={styles.stack}>
        {/* ---------- Form nuova rilevazione ---------- */}
        <Card title="Nuova rilevazione">
          <form onSubmit={handleSubmit}>
            <div className={`${styles.formGrid} ${styles.formGrid2}`}>
              <Field
                id="valore"
                label="Valore (mg/dL)"
                type="number"
                min={1}
                value={valore}
                onChange={setValore}
                required
                disabled={invio}
                placeholder="Es. 110"
              />
              <Field
                id="momento"
                label="Momento della misurazione"
                as="select"
                value={momento}
                onChange={(v) => setMomento(v as Momento)}
                disabled={invio}
              >
                <option value="prima_pasto">Prima del pasto</option>
                <option value="dopo_pasto">Dopo il pasto</option>
              </Field>
            </div>
            <div className={styles.formActions}>
              <Button type="submit" disabled={invio || !valore}>
                {invio ? 'Salvataggio…' : 'Registra'}
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

        {/* ---------- Andamento aggregato ---------- */}
        <Card title="Andamento aggregato">
          <div className={styles.tabs} style={{ marginBottom: 'var(--space-4)' }}>
            <button
              className={`${styles.tab} ${periodo === 'settimana' ? styles.tabActive : ''}`}
              onClick={() => setPeriodo('settimana')}
            >
              Settimana
            </button>
            <button
              className={`${styles.tab} ${periodo === 'mese' ? styles.tabActive : ''}`}
              onClick={() => setPeriodo('mese')}
            >
              Mese
            </button>
          </div>

          {!aggregato ? (
            <Loading label="Caricamento andamento…" />
          ) : aggregato.length === 0 ? (
            <Empty label="Nessuna rilevazione da aggregare." />
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Periodo</th>
                    <th>Media</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Misurazioni</th>
                    <th>Fuori soglia</th>
                  </tr>
                </thead>
                <tbody>
                  {aggregato.map((a) => (
                    <tr key={a.periodo_inizio}>
                      <td>
                        {formatData(a.periodo_inizio)} – {formatData(a.periodo_fine)}
                      </td>
                      <td>{a.media} mg/dL</td>
                      <td>{a.minimo}</td>
                      <td>{a.massimo}</td>
                      <td>{a.num_misurazioni}</td>
                      <td>
                        {a.num_fuori_soglia > 0 ? (
                          <Badge tone="warning">{a.num_fuori_soglia}</Badge>
                        ) : (
                          <Badge tone="success">0</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* ---------- Storico dettaglio ---------- */}
        <Card title="Storico rilevazioni">
          {!dettaglio ? (
            <Loading label="Caricamento…" />
          ) : dettaglio.length === 0 ? (
            <Empty label="Non hai ancora registrato rilevazioni." />
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Data e ora</th>
                    <th>Valore</th>
                    <th>Momento</th>
                    <th>Stato</th>
                  </tr>
                </thead>
                <tbody>
                  {dettaglio.map((g) => (
                    <tr key={g.id} className={g.fuori_soglia ? styles.rowAlert : ''}>
                      <td>{formatDataOra(g.timestamp)}</td>
                      <td>
                        <strong>{g.valore}</strong> mg/dL
                      </td>
                      <td>{MOMENTO_LABEL[g.momento] ?? g.momento}</td>
                      <td>
                        {g.fuori_soglia ? (
                          <Badge tone="critical">Fuori soglia</Badge>
                        ) : (
                          <Badge tone="success">Nella norma</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
