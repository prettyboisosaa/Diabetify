/**
 * RF-8 / UC-8: gestione terapia farmacologica.
 *  - Elenco terapie con possibilita' di disattivare/riattivare (modifica is_active).
 *  - Form per prescrivere una nuova terapia (farmaco, assunzioni/die, quantita+unita, indicazioni).
 *  - Elenco assunzioni registrate dal paziente (RF-6) per confronto visivo (RF-11 lato lettura).
 * Ogni creazione/modifica registra un audit lato backend (RF-15).
 */

import { useEffect, useState, type FormEvent } from 'react';
import {
  getTerapie,
  creaTerapia,
  aggiornaTerapia,
  getAssunzioni,
  type Terapia,
  type Assunzione,
  type Unita,
} from '../../../lib/medico';
import { Card, Button, Badge, Field, Loading, ErrorBox, Empty } from '../../../components/ui';
import { formatData, formatDataOra } from '../../../lib/format';
import styles from '../../../styles/data.module.css';

const UNITA: Unita[] = ['mg', 'UI', 'ml', 'compresse'];

export default function TerapieSection({ patientId }: { patientId: number }) {
  const [terapie, setTerapie] = useState<Terapia[] | null>(null);
  const [assunzioni, setAssunzioni] = useState<Assunzione[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  // Stato del form "nuova terapia"
  const [farmaco, setFarmaco] = useState('');
  const [assunzioniDie, setAssunzioniDie] = useState('1');
  const [quantita, setQuantita] = useState('');
  const [unita, setUnita] = useState<Unita>('mg');
  const [indicazioni, setIndicazioni] = useState('');
  const [invio, setInvio] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; testo: string } | null>(null);

  function ricarica() {
    getTerapie(patientId).then(setTerapie).catch((e) => setErrore(e.message));
    getAssunzioni(patientId).then(setAssunzioni).catch((e) => setErrore(e.message));
  }

  useEffect(ricarica, [patientId]);

  async function handleCrea(e: FormEvent) {
    e.preventDefault();
    setInvio(true);
    setFeedback(null);
    try {
      await creaTerapia(patientId, {
        patient_id: patientId,
        farmaco,
        assunzioni_giornaliere: Number(assunzioniDie),
        quantita,
        unita,
        indicazioni: indicazioni || null,
      });
      // Reset form e ricarica elenco
      setFarmaco('');
      setAssunzioniDie('1');
      setQuantita('');
      setUnita('mg');
      setIndicazioni('');
      setFeedback({ ok: true, testo: 'Terapia prescritta correttamente.' });
      ricarica();
    } catch (err) {
      setFeedback({
        ok: false,
        testo: err instanceof Error ? err.message : 'Errore durante la prescrizione.',
      });
    } finally {
      setInvio(false);
    }
  }

  async function toggleAttiva(t: Terapia) {
    try {
      await aggiornaTerapia(t.id, { is_active: !t.is_active });
      ricarica();
    } catch (err) {
      setErrore(err instanceof Error ? err.message : 'Errore aggiornamento terapia.');
    }
  }

  return (
    <div className={styles.stack}>
      {errore && <ErrorBox message={errore} />}

      {/* ---------- Elenco terapie ---------- */}
      <Card title="Terapie prescritte">
        {!terapie ? (
          <Loading label="Caricamento terapie…" />
        ) : terapie.length === 0 ? (
          <Empty label="Nessuna terapia prescritta." />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Farmaco</th>
                  <th>Assunzioni/die</th>
                  <th>Quantità</th>
                  <th>Indicazioni</th>
                  <th>Inizio</th>
                  <th>Stato</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {terapie.map((t) => (
                  <tr key={t.id}>
                    <td><strong>{t.farmaco}</strong></td>
                    <td>{t.assunzioni_giornaliere}</td>
                    <td>
                      {Number(t.quantita)} {t.unita}
                    </td>
                    <td>{t.indicazioni ?? '—'}</td>
                    <td>{formatData(t.data_inizio)}</td>
                    <td>
                      {t.is_active ? (
                        <Badge tone="success">Attiva</Badge>
                      ) : (
                        <Badge tone="neutral">Sospesa</Badge>
                      )}
                    </td>
                    <td>
                      <Button
                        small
                        variant={t.is_active ? 'danger' : 'secondary'}
                        onClick={() => toggleAttiva(t)}
                      >
                        {t.is_active ? 'Sospendi' : 'Riattiva'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ---------- Nuova terapia ---------- */}
      <Card title="Prescrivi nuova terapia">
        <form onSubmit={handleCrea}>
          <div className={`${styles.formGrid} ${styles.formGrid2}`}>
            <Field
              id="farmaco"
              label="Farmaco"
              value={farmaco}
              onChange={setFarmaco}
              required
              disabled={invio}
              placeholder="Es. Metformina"
            />
            <Field
              id="assunzioni_die"
              label="Assunzioni giornaliere"
              type="number"
              min={1}
              value={assunzioniDie}
              onChange={setAssunzioniDie}
              required
              disabled={invio}
            />
            <Field
              id="quantita"
              label="Quantità per assunzione"
              type="number"
              step="0.001"
              min={0}
              value={quantita}
              onChange={setQuantita}
              required
              disabled={invio}
              placeholder="Es. 500"
            />
            <Field
              id="unita"
              label="Unità di misura"
              as="select"
              value={unita}
              onChange={(v) => setUnita(v as Unita)}
              disabled={invio}
            >
              {UNITA.map((u) => (
                <option key={u} value={u}>{u}</option>
              ))}
            </Field>
          </div>

          <div style={{ marginTop: 'var(--space-4)' }}>
            <Field
              id="indicazioni"
              label="Indicazioni (es. dopo i pasti, lontano dai pasti)"
              as="textarea"
              value={indicazioni}
              onChange={setIndicazioni}
              disabled={invio}
            />
          </div>

          <div className={styles.formActions}>
            <Button type="submit" disabled={invio}>
              {invio ? 'Salvataggio…' : 'Prescrivi terapia'}
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

      {/* ---------- Assunzioni del paziente ---------- */}
      <Card title="Assunzioni registrate dal paziente">
        {!assunzioni ? (
          <Loading label="Caricamento assunzioni…" />
        ) : assunzioni.length === 0 ? (
          <Empty label="Il paziente non ha ancora registrato assunzioni." />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Data e ora</th>
                  <th>Farmaco</th>
                  <th>Quantità assunta</th>
                </tr>
              </thead>
              <tbody>
                {assunzioni.map((a) => (
                  <tr key={a.id}>
                    <td>{formatDataOra(a.timestamp)}</td>
                    <td>{a.farmaco}</td>
                    <td>
                      {Number(a.quantita_assunta)} {a.unita}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
