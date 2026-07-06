/**
 * RF-13/14 (lato lettura): inbox degli alert automatici destinati al medico.
 * In questa fase il medico li LEGGE e ne gestisce lo stato (letta/risolta);
 * la generazione e' compito dell'attore Sistema (fase successiva).
 */

import { useEffect, useState } from 'react';
import {
  getNotifiche,
  segnaNotificaLetta,
  segnaNotificaRisolta,
  type Notifica,
  type Severita,
} from '../../lib/medico';
import { Button, Badge, Loading, ErrorBox, Empty } from '../../components/ui';
import { formatDataOra } from '../../lib/format';
import styles from '../../styles/data.module.css';

const TIPO_LABEL: Record<string, string> = {
  sollecito_assunzione: 'Sollecito assunzione',
  mancata_aderenza: 'Mancata aderenza',
  glicemia_fuori_soglia: 'Glicemia fuori soglia',
};

const SEVERITA_CLASS: Record<Severita, string> = {
  critical: styles.notifCritical,
  warning: styles.notifWarning,
  info: styles.notifInfo,
};

const SEVERITA_TONE: Record<Severita, 'critical' | 'warning' | 'info'> = {
  critical: 'critical',
  warning: 'warning',
  info: 'info',
};

export default function NotifichePage() {
  const [notifiche, setNotifiche] = useState<Notifica[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [soloAperte, setSoloAperte] = useState(false);

  function ricarica() {
    getNotifiche(soloAperte)
      .then(setNotifiche)
      .catch((e) => setErrore(e.message));
  }

  useEffect(ricarica, [soloAperte]);

  async function segnaLetta(id: number) {
    await segnaNotificaLetta(id).catch((e) => setErrore(e.message));
    ricarica();
  }

  async function risolvi(id: number) {
    await segnaNotificaRisolta(id).catch((e) => setErrore(e.message));
    ricarica();
  }

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Notifiche & Alert</h1>
        <p className={styles.pageSubtitle}>
          Avvisi automatici su aderenza terapeutica e glicemie fuori soglia.
        </p>
      </div>

      <div className={styles.row} style={{ marginBottom: 'var(--space-4)' }}>
        <label className={styles.row} style={{ gap: 'var(--space-2)', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={soloAperte}
            onChange={(e) => setSoloAperte(e.target.checked)}
          />
          Mostra solo non risolte
        </label>
      </div>

      {errore && <ErrorBox message={errore} />}
      {!notifiche && !errore && <Loading label="Caricamento notifiche…" />}

      {notifiche && (
        notifiche.length === 0 ? (
          <Empty label="Nessuna notifica." />
        ) : (
          <div className={styles.stack}>
            {notifiche.map((n) => {
              const risolta = n.risolta_at !== null;
              return (
                <div
                  key={n.id}
                  className={`${styles.notifItem} ${SEVERITA_CLASS[n.severita]} ${
                    risolta ? styles.notifResolved : ''
                  }`}
                >
                  <div className={styles.rowBetween}>
                    <div className={styles.row}>
                      <Badge tone={SEVERITA_TONE[n.severita]}>{n.severita}</Badge>
                      <strong>{TIPO_LABEL[n.tipo] ?? n.tipo}</strong>
                    </div>
                    <span className={styles.notifMeta}>{formatDataOra(n.creato_at)}</span>
                  </div>

                  <p className={styles.notifText}>{n.messaggio}</p>

                  <div className={styles.row}>
                    {risolta ? (
                      <Badge tone="success">Risolta</Badge>
                    ) : (
                      <>
                        {n.letta_at === null && (
                          <Button small variant="secondary" onClick={() => segnaLetta(n.id)}>
                            Segna come letta
                          </Button>
                        )}
                        <Button small onClick={() => risolvi(n.id)}>
                          Risolvi
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )
      )}
    </div>
  );
}
