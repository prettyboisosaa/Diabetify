/**
 * RF-5 (UC-5): diario clinico del paziente — sintomi, patologie concomitanti e
 * terapie parallele, ciascuno con inserimento e possibilita' di CHIUSURA
 * (imposta la data di fine a oggi) tramite gli endpoint di update.
 */

import { useEffect, useState, type FormEvent } from 'react';
import {
  getSintomi, creaSintomo, aggiornaSintomo,
  getPatologie, creaPatologia, aggiornaPatologia,
  getTerapieParallele, creaTerapiaParallela, aggiornaTerapiaParallela,
} from '../../lib/paziente';
import type { Sintomo, PatologiaConcomitante, TerapiaParallela, Gravita } from '../../lib/types';
import { Card, Button, Badge, Field, Loading, ErrorBox, Empty } from '../../components/ui';
import { formatData } from '../../lib/format';
import styles from '../../styles/data.module.css';

const OGGI = () => new Date().toISOString().slice(0, 10);
const GRAVITA_TONE = { lieve: 'info', moderata: 'warning', grave: 'critical' } as const;

/** Riga "periodo": data inizio – data fine oppure "in corso". */
function periodoLabel(inizio: string, fine: string | null) {
  return `${formatData(inizio)} – ${fine ? formatData(fine) : 'in corso'}`;
}

export default function DiarioPage() {
  const [errore, setErrore] = useState<string | null>(null);

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Diario clinico</h1>
        <p className={styles.pageSubtitle}>
          Annota sintomi, patologie concomitanti e terapie parallele.
        </p>
      </div>

      {errore && <ErrorBox message={errore} />}

      <div className={styles.stack}>
        <SintomiCard onError={setErrore} />
        <PatologieCard onError={setErrore} />
        <TerapieParalleleCard onError={setErrore} />
      </div>
    </div>
  );
}

// =========================================================
// Sintomi
// =========================================================
function SintomiCard({ onError }: { onError: (m: string) => void }) {
  const [items, setItems] = useState<Sintomo[] | null>(null);
  const [descrizione, setDescrizione] = useState('');
  const [gravita, setGravita] = useState<Gravita>('lieve');
  const [dataInizio, setDataInizio] = useState(OGGI());
  const [note, setNote] = useState('');
  const [invio, setInvio] = useState(false);

  const ricarica = () => getSintomi().then(setItems).catch((e) => onError(e.message));
  useEffect(() => { ricarica(); }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setInvio(true);
    try {
      await creaSintomo({ descrizione, gravita, data_inizio: dataInizio, note: note || null });
      setDescrizione('');
      setNote('');
      ricarica();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Errore.');
    } finally {
      setInvio(false);
    }
  }

  async function chiudi(id: number) {
    await aggiornaSintomo(id, { data_fine: OGGI() }).catch((e) => onError(e.message));
    ricarica();
  }

  return (
    <Card title="Sintomi">
      {!items ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty label="Nessun sintomo registrato." />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Descrizione</th><th>Gravità</th><th>Periodo</th><th>Note</th><th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((s) => (
                <tr key={s.id}>
                  <td>{s.descrizione}</td>
                  <td>{s.gravita ? <Badge tone={GRAVITA_TONE[s.gravita]}>{s.gravita}</Badge> : '—'}</td>
                  <td>{periodoLabel(s.data_inizio, s.data_fine)}</td>
                  <td>{s.note ?? '—'}</td>
                  <td>
                    {s.data_fine === null && (
                      <Button small variant="secondary" onClick={() => chiudi(s.id)}>Chiudi</Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ marginTop: 'var(--space-4)' }}>
        <div className={`${styles.formGrid} ${styles.formGrid2}`}>
          <Field id="s-desc" label="Sintomo" value={descrizione} onChange={setDescrizione} required disabled={invio} placeholder="Es. spossatezza" />
          <Field id="s-grav" label="Gravità" as="select" value={gravita} onChange={(v) => setGravita(v as Gravita)} disabled={invio}>
            <option value="lieve">Lieve</option>
            <option value="moderata">Moderata</option>
            <option value="grave">Grave</option>
          </Field>
          <Field id="s-inizio" label="Data inizio" type="date" value={dataInizio} onChange={setDataInizio} required disabled={invio} />
          <Field id="s-note" label="Note (opzionale)" value={note} onChange={setNote} disabled={invio} />
        </div>
        <div className={styles.formActions}>
          <Button type="submit" disabled={invio || !descrizione}>Aggiungi sintomo</Button>
        </div>
      </form>
    </Card>
  );
}

// =========================================================
// Patologie concomitanti
// =========================================================
function PatologieCard({ onError }: { onError: (m: string) => void }) {
  const [items, setItems] = useState<PatologiaConcomitante[] | null>(null);
  const [descrizione, setDescrizione] = useState('');
  const [dataInizio, setDataInizio] = useState(OGGI());
  const [note, setNote] = useState('');
  const [invio, setInvio] = useState(false);

  const ricarica = () => getPatologie().then(setItems).catch((e) => onError(e.message));
  useEffect(() => { ricarica(); }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setInvio(true);
    try {
      await creaPatologia({ descrizione, data_inizio: dataInizio, note: note || null });
      setDescrizione('');
      setNote('');
      ricarica();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Errore.');
    } finally {
      setInvio(false);
    }
  }

  async function chiudi(id: number) {
    await aggiornaPatologia(id, { data_fine: OGGI() }).catch((e) => onError(e.message));
    ricarica();
  }

  return (
    <Card title="Patologie concomitanti">
      {!items ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty label="Nessuna patologia registrata." />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr><th>Descrizione</th><th>Periodo</th><th>Note</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td>{p.descrizione}</td>
                  <td>{periodoLabel(p.data_inizio, p.data_fine)}</td>
                  <td>{p.note ?? '—'}</td>
                  <td>
                    {p.data_fine === null && (
                      <Button small variant="secondary" onClick={() => chiudi(p.id)}>Chiudi</Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ marginTop: 'var(--space-4)' }}>
        <div className={`${styles.formGrid} ${styles.formGrid2}`}>
          <Field id="p-desc" label="Patologia" value={descrizione} onChange={setDescrizione} required disabled={invio} />
          <Field id="p-inizio" label="Data inizio" type="date" value={dataInizio} onChange={setDataInizio} required disabled={invio} />
          <Field id="p-note" label="Note (opzionale)" value={note} onChange={setNote} disabled={invio} />
        </div>
        <div className={styles.formActions}>
          <Button type="submit" disabled={invio || !descrizione}>Aggiungi patologia</Button>
        </div>
      </form>
    </Card>
  );
}

// =========================================================
// Terapie parallele
// =========================================================
function TerapieParalleleCard({ onError }: { onError: (m: string) => void }) {
  const [items, setItems] = useState<TerapiaParallela[] | null>(null);
  const [farmaco, setFarmaco] = useState('');
  const [posologia, setPosologia] = useState('');
  const [dataInizio, setDataInizio] = useState(OGGI());
  const [invio, setInvio] = useState(false);

  const ricarica = () => getTerapieParallele().then(setItems).catch((e) => onError(e.message));
  useEffect(() => { ricarica(); }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setInvio(true);
    try {
      await creaTerapiaParallela({ farmaco, posologia: posologia || null, data_inizio: dataInizio });
      setFarmaco('');
      setPosologia('');
      ricarica();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Errore.');
    } finally {
      setInvio(false);
    }
  }

  async function chiudi(id: number) {
    await aggiornaTerapiaParallela(id, { data_fine: OGGI() }).catch((e) => onError(e.message));
    ricarica();
  }

  return (
    <Card title="Terapie parallele">
      {!items ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty label="Nessuna terapia parallela registrata." />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr><th>Farmaco</th><th>Posologia</th><th>Periodo</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((t) => (
                <tr key={t.id}>
                  <td>{t.farmaco}</td>
                  <td>{t.posologia ?? '—'}</td>
                  <td>{periodoLabel(t.data_inizio, t.data_fine)}</td>
                  <td>
                    {t.data_fine === null && (
                      <Button small variant="secondary" onClick={() => chiudi(t.id)}>Chiudi</Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ marginTop: 'var(--space-4)' }}>
        <div className={`${styles.formGrid} ${styles.formGrid2}`}>
          <Field id="tp-farmaco" label="Farmaco" value={farmaco} onChange={setFarmaco} required disabled={invio} />
          <Field id="tp-poso" label="Posologia (opzionale)" value={posologia} onChange={setPosologia} disabled={invio} />
          <Field id="tp-inizio" label="Data inizio" type="date" value={dataInizio} onChange={setDataInizio} required disabled={invio} />
        </div>
        <div className={styles.formActions}>
          <Button type="submit" disabled={invio || !farmaco}>Aggiungi terapia parallela</Button>
        </div>
      </form>
    </Card>
  );
}
