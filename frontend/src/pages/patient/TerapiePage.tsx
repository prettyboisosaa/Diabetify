/**
 * RF-6 (UC-6): il paziente consulta le terapie prescritte dal medico (sola
 * lettura) e registra l'assunzione dei farmaci, collegandola a una terapia attiva.
 * Le assunzioni sono immutabili (solo creazione + lettura).
 */

import { useEffect, useState, type FormEvent } from 'react';
import {
  getTerapie,
  getAssunzioni,
  registraAssunzione,
} from '../../lib/paziente';
import type { Terapia, Assunzione, Unita } from '../../lib/types';
import { Card, Button, Badge, Field, Loading, ErrorBox, Empty } from '../../components/ui';
import { formatData, formatDataOra } from '../../lib/format';
import styles from '../../styles/data.module.css';

const UNITA: Unita[] = ['mg', 'UI', 'ml', 'compresse'];

export default function TerapiePage() {
  const [terapie, setTerapie] = useState<Terapia[] | null>(null);
  const [assunzioni, setAssunzioni] = useState<Assunzione[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  // Stato form assunzione
  const [terapiaId, setTerapiaId] = useState('');
  const [quantita, setQuantita] = useState('');
  const [unita, setUnita] = useState<Unita>('mg');
  const [invio, setInvio] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; testo: string } | null>(null);

  function ricarica() {
    getTerapie().then(setTerapie).catch((e) => setErrore(e.message));
    getAssunzioni().then(setAssunzioni).catch((e) => setErrore(e.message));
  }

  useEffect(ricarica, []);

  const terapieAttive = (terapie ?? []).filter((t) => t.is_active);

  // Quando l'utente sceglie una terapia, precompila unità e quantità prescritta
  function selezionaTerapia(id: string) {
    setTerapiaId(id);
    const t = terapieAttive.find((x) => String(x.id) === id);
    if (t) {
      setUnita(t.unita);
      setQuantita(String(Number(t.quantita)));
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!terapiaId) return;
    setInvio(true);
    setFeedback(null);
    const terapia = terapieAttive.find((x) => String(x.id) === terapiaId);
    try {
      await registraAssunzione({
        terapia_id: Number(terapiaId),
        farmaco: terapia ? terapia.farmaco : '',
        quantita_assunta: quantita,
        unita,
      });
      setFeedback({ ok: true, testo: 'Assunzione registrata.' });
      ricarica();
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
        <h1 className={styles.pageTitle}>Terapie & Assunzioni</h1>
        <p className={styles.pageSubtitle}>
          Le terapie prescritte dal tuo medico e le assunzioni che registri.
        </p>
      </div>

      {errore && <ErrorBox message={errore} />}

      <div className={styles.stack}>
        {/* ---------- Terapie prescritte (lettura) ---------- */}
        <Card title="Terapie prescritte">
          {!terapie ? (
            <Loading />
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
                  </tr>
                </thead>
                <tbody>
                  {terapie.map((t) => (
                    <tr key={t.id}>
                      <td><strong>{t.farmaco}</strong></td>
                      <td>{t.assunzioni_giornaliere}</td>
                      <td>{Number(t.quantita)} {t.unita}</td>
                      <td>{t.indicazioni ?? '—'}</td>
                      <td>{formatData(t.data_inizio)}</td>
                      <td>
                        {t.is_active ? (
                          <Badge tone="success">Attiva</Badge>
                        ) : (
                          <Badge tone="neutral">Sospesa</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* ---------- Registra assunzione ---------- */}
        <Card title="Registra un'assunzione">
          {terapieAttive.length === 0 ? (
            <Empty label="Non hai terapie attive da registrare." />
          ) : (
            <form onSubmit={handleSubmit}>
              <div className={`${styles.formGrid} ${styles.formGrid2}`}>
                <Field
                  id="terapia"
                  label="Terapia"
                  as="select"
                  value={terapiaId}
                  onChange={selezionaTerapia}
                  disabled={invio}
                  required
                >
                  <option value="">— Seleziona —</option>
                  {terapieAttive.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.farmaco} ({Number(t.quantita)} {t.unita})
                    </option>
                  ))}
                </Field>
                <Field
                  id="quantita"
                  label="Quantità assunta"
                  type="number"
                  step="0.001"
                  min={0}
                  value={quantita}
                  onChange={setQuantita}
                  required
                  disabled={invio}
                />
                <Field
                  id="unita"
                  label="Unità"
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
              <div className={styles.formActions}>
                <Button type="submit" disabled={invio || !terapiaId}>
                  {invio ? 'Salvataggio…' : 'Registra assunzione'}
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
          )}
        </Card>

        {/* ---------- Storico assunzioni ---------- */}
        <Card title="Assunzioni registrate">
          {!assunzioni ? (
            <Loading />
          ) : assunzioni.length === 0 ? (
            <Empty label="Non hai ancora registrato assunzioni." />
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Data e ora</th>
                    <th>Farmaco</th>
                    <th>Quantità</th>
                  </tr>
                </thead>
                <tbody>
                  {assunzioni.map((a) => (
                    <tr key={a.id}>
                      <td>{formatDataOra(a.timestamp)}</td>
                      <td>{a.farmaco}</td>
                      <td>{Number(a.quantita_assunta)} {a.unita}</td>
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
