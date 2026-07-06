/**
 * RF-9: visualizzazione dati glicemici.
 *  - Dettaglio: elenco delle singole rilevazioni con badge "fuori soglia" (RNF-1).
 *  - Aggregato: media/min/max/n. fuori soglia per settimana o mese (solo tabella).
 * L'apertura registra un audit lato backend (RF-15).
 */

import { useEffect, useState } from 'react';
import {
  getGlicemie,
  getGlicemieAggregate,
  type Glicemia,
  type GlicemiaAggregata,
} from '../../../lib/medico';
import { Badge, Card, Loading, ErrorBox, Empty } from '../../../components/ui';
import { formatData, formatDataOra } from '../../../lib/format';
import styles from '../../../styles/data.module.css';

const MOMENTO_LABEL: Record<string, string> = {
  prima_pasto: 'Prima del pasto',
  dopo_pasto: 'Dopo il pasto',
};

export default function GlicemieSection({ patientId }: { patientId: number }) {
  const [dettaglio, setDettaglio] = useState<Glicemia[] | null>(null);
  const [aggregato, setAggregato] = useState<GlicemiaAggregata[] | null>(null);
  const [periodo, setPeriodo] = useState<'settimana' | 'mese'>('settimana');
  const [errore, setErrore] = useState<string | null>(null);

  // Dettaglio: caricato una volta
  useEffect(() => {
    getGlicemie(patientId)
      .then(setDettaglio)
      .catch((e) => setErrore(e.message));
  }, [patientId]);

  // Aggregato: ricaricato al cambio periodo
  useEffect(() => {
    setAggregato(null);
    getGlicemieAggregate(patientId, periodo)
      .then(setAggregato)
      .catch((e) => setErrore(e.message));
  }, [patientId, periodo]);

  return (
    <div className={styles.stack}>
      {errore && <ErrorBox message={errore} />}

      {/* ---------- Aggregato ---------- */}
      <Card title="Andamento aggregato">
        <div className={styles.rowBetween} style={{ marginBottom: 'var(--space-4)' }}>
          <div className={styles.tabs} style={{ border: 'none', margin: 0 }}>
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

      {/* ---------- Dettaglio ---------- */}
      <Card title="Rilevazioni in dettaglio">
        {!dettaglio ? (
          <Loading label="Caricamento rilevazioni…" />
        ) : dettaglio.length === 0 ? (
          <Empty label="Nessuna rilevazione glicemica registrata." />
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
  );
}
