/**
 * RF-5 (lato lettura per il medico): sintomi, patologie concomitanti e terapie
 * parallele dichiarate dal paziente. Sola lettura in questa fase.
 */

import { useEffect, useState } from 'react';
import {
  getSintomi,
  getPatologieConcomitanti,
  getTerapieParallele,
  type Sintomo,
  type PatologiaConcomitante,
  type TerapiaParallela,
} from '../../../lib/medico';
import { Card, Badge, Loading, ErrorBox, Empty } from '../../../components/ui';
import { formatData } from '../../../lib/format';
import styles from '../../../styles/data.module.css';

const GRAVITA_TONE = {
  lieve: 'info',
  moderata: 'warning',
  grave: 'critical',
} as const;

export default function ClinicaSection({ patientId }: { patientId: number }) {
  const [sintomi, setSintomi] = useState<Sintomo[] | null>(null);
  const [patologie, setPatologie] = useState<PatologiaConcomitante[] | null>(null);
  const [parallele, setParallele] = useState<TerapiaParallela[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    getSintomi(patientId).then(setSintomi).catch((e) => setErrore(e.message));
    getPatologieConcomitanti(patientId).then(setPatologie).catch((e) => setErrore(e.message));
    getTerapieParallele(patientId).then(setParallele).catch((e) => setErrore(e.message));
  }, [patientId]);

  // Riga "periodo" comune (data inizio – data fine o "in corso")
  const periodo = (inizio: string, fine: string | null) =>
    `${formatData(inizio)} – ${fine ? formatData(fine) : 'in corso'}`;

  return (
    <div className={styles.stack}>
      {errore && <ErrorBox message={errore} />}

      {/* ---------- Sintomi ---------- */}
      <Card title="Sintomi segnalati">
        {!sintomi ? (
          <Loading />
        ) : sintomi.length === 0 ? (
          <Empty label="Nessun sintomo segnalato." />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Descrizione</th>
                  <th>Gravità</th>
                  <th>Periodo</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {sintomi.map((s) => (
                  <tr key={s.id}>
                    <td>{s.descrizione}</td>
                    <td>
                      {s.gravita ? (
                        <Badge tone={GRAVITA_TONE[s.gravita]}>{s.gravita}</Badge>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td>{periodo(s.data_inizio, s.data_fine)}</td>
                    <td>{s.note ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ---------- Patologie concomitanti ---------- */}
      <Card title="Patologie concomitanti">
        {!patologie ? (
          <Loading />
        ) : patologie.length === 0 ? (
          <Empty label="Nessuna patologia concomitante." />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Descrizione</th>
                  <th>Periodo</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {patologie.map((p) => (
                  <tr key={p.id}>
                    <td>{p.descrizione}</td>
                    <td>{periodo(p.data_inizio, p.data_fine)}</td>
                    <td>{p.note ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ---------- Terapie parallele ---------- */}
      <Card title="Terapie parallele">
        {!parallele ? (
          <Loading />
        ) : parallele.length === 0 ? (
          <Empty label="Nessuna terapia parallela." />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Farmaco</th>
                  <th>Posologia</th>
                  <th>Periodo</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {parallele.map((t) => (
                  <tr key={t.id}>
                    <td>{t.farmaco}</td>
                    <td>{t.posologia ?? '—'}</td>
                    <td>{periodo(t.data_inizio, t.data_fine)}</td>
                    <td>{t.note ?? '—'}</td>
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
