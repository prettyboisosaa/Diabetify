/**
 * RF-15: consultazione del registro audit (inalterabile) delle operazioni dei
 * medici. Filtrabile per paziente.
 */

import { useEffect, useState } from 'react';
import { getAuditLogs, getPazienti } from '../../lib/admin';
import type { AuditLog, PatientProfile } from '../../lib/types';
import { Card, Badge, Field, Loading, ErrorBox, Empty } from '../../components/ui';
import { formatDataOra } from '../../lib/format';
import styles from '../../styles/data.module.css';

const AZIONE_LABEL: Record<string, string> = {
  VISUALIZZAZIONE_SCHEDA: 'Visualizzazione scheda',
  VISUALIZZAZIONE_GLICEMIE: 'Visualizzazione glicemie',
  CREAZIONE_TERAPIA: 'Creazione terapia',
  MODIFICA_TERAPIA: 'Modifica terapia',
  AGGIORNAMENTO_ANAMNESI: 'Aggiornamento anamnesi',
};

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[] | null>(null);
  const [pazienti, setPazienti] = useState<PatientProfile[]>([]);
  const [filtro, setFiltro] = useState('');
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    getPazienti().then(setPazienti).catch(() => {});
  }, []);

  useEffect(() => {
    setLogs(null);
    getAuditLogs(filtro ? Number(filtro) : undefined)
      .then(setLogs)
      .catch((e) => setErrore(e.message));
  }, [filtro]);

  // Mappa id paziente -> nome per la colonna "paziente"
  const nomePaziente = (id: number | null) => {
    if (id == null) return '—';
    const p = pazienti.find((x) => x.id === id);
    return p ? `${p.nome} ${p.cognome}` : `#${id}`;
  };

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Registro audit</h1>
        <p className={styles.pageSubtitle}>
          Tracciamento inalterabile di ogni operazione dei medici sui dati dei pazienti (RF-15).
        </p>
      </div>

      <div style={{ maxWidth: 360, marginBottom: 'var(--space-4)' }}>
        <Field
          id="filtro-paziente"
          label="Filtra per paziente"
          as="select"
          value={filtro}
          onChange={setFiltro}
        >
          <option value="">Tutti i pazienti</option>
          {pazienti.map((p) => (
            <option key={p.id} value={p.id}>{p.nome} {p.cognome}</option>
          ))}
        </Field>
      </div>

      {errore && <ErrorBox message={errore} />}
      {!logs && !errore && <Loading label="Caricamento registro…" />}

      {logs && (
        <Card>
          {logs.length === 0 ? (
            <Empty label="Nessuna operazione registrata." />
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Data e ora</th>
                    <th>Operatore (medico)</th>
                    <th>Azione</th>
                    <th>Paziente</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((l) => (
                    <tr key={l.id}>
                      <td>{formatDataOra(l.timestamp)}</td>
                      <td>#{l.operator_id}</td>
                      <td><Badge tone="info">{AZIONE_LABEL[l.azione] ?? l.azione}</Badge></td>
                      <td>{nomePaziente(l.target_paziente_id)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
