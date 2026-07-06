/**
 * Elenco pazienti (RF-9): qualsiasi medico vede qualsiasi paziente.
 * Ricerca per nome/cognome; ogni card apre la scheda clinica.
 */

import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPazienti, type PazienteListItem } from '../../lib/medico';
import { Badge, ErrorBox, Loading, Empty, Field } from '../../components/ui';
import styles from '../../styles/data.module.css';

export default function PatientListPage() {
  const navigate = useNavigate();
  const [pazienti, setPazienti] = useState<PazienteListItem[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [ricerca, setRicerca] = useState('');

  useEffect(() => {
    getPazienti()
      .then(setPazienti)
      .catch((e) => setErrore(e.message));
  }, []);

  // Filtro client-side per nome/cognome
  const filtrati = useMemo(() => {
    if (!pazienti) return [];
    const q = ricerca.trim().toLowerCase();
    if (!q) return pazienti;
    return pazienti.filter((p) =>
      `${p.nome} ${p.cognome}`.toLowerCase().includes(q),
    );
  }, [pazienti, ricerca]);

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Pazienti</h1>
        <p className={styles.pageSubtitle}>
          Seleziona un paziente per consultarne la scheda clinica.
        </p>
      </div>

      {errore && <ErrorBox message={errore} />}
      {!pazienti && !errore && <Loading label="Caricamento pazienti…" />}

      {pazienti && (
        <div className={styles.stack}>
          <div style={{ maxWidth: 360 }}>
            <Field
              id="ricerca"
              label="Cerca paziente"
              value={ricerca}
              onChange={setRicerca}
              placeholder="Nome o cognome…"
            />
          </div>

          {filtrati.length === 0 ? (
            <Empty label="Nessun paziente corrisponde alla ricerca." />
          ) : (
            <div className={styles.patientGrid}>
              {filtrati.map((p) => (
                <button
                  key={p.id}
                  className={styles.patientCard}
                  onClick={() => navigate(`/doctor/pazienti/${p.id}`)}
                >
                  <span className={styles.patientName}>
                    {p.nome} {p.cognome}
                  </span>
                  <span className={styles.patientMeta}>
                    <span>
                      Ultima glicemia:{' '}
                      {p.ultima_glicemia !== null ? `${p.ultima_glicemia} mg/dL` : '—'}
                    </span>
                    {p.num_notifiche_aperte > 0 && (
                      <Badge tone="critical">
                        {p.num_notifiche_aperte} alert
                      </Badge>
                    )}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
