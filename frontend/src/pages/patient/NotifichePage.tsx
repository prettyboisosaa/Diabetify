/**
 * RF-12/13 (lato lettura): il paziente legge i solleciti/promemoria automatici
 * (completamento assunzioni, dimenticanza farmaci) e ne gestisce lo stato.
 * La generazione degli avvisi e' compito dell'attore Sistema (fase separata).
 */

import { useEffect, useState } from 'react';
import {
  getNotifiche,
  segnaNotificaLetta,
  segnaNotificaRisolta,
} from '../../lib/paziente';
import type { Notifica, Severita } from '../../lib/types';
import { Button, Badge, Loading, ErrorBox, Empty } from '../../components/ui';
import { formatDataOra } from '../../lib/format';
import styles from '../../styles/data.module.css';

const TIPO_LABEL: Record<string, string> = {
  sollecito_assunzione: 'Promemoria assunzione',
  mancata_aderenza: 'Mancata aderenza',
  glicemia_fuori_soglia: 'Glicemia fuori soglia',
};

const SEVERITA_CLASS: Record<Severita, string> = {
  critical: styles.notifCritical,
  warning: styles.notifWarning,
  info: styles.notifInfo,
};

export default function NotifichePage() {
  const [notifiche, setNotifiche] = useState<Notifica[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [soloAperte, setSoloAperte] = useState(false);

  function ricarica() {
    getNotifiche(soloAperte).then(setNotifiche).catch((e) => setErrore(e.message));
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
        <h1 className={styles.pageTitle}>Avvisi & Promemoria</h1>
        <p className={styles.pageSubtitle}>
          Ricordati di registrare le assunzioni e tieni monitorate le tue glicemie.
        </p>
      </div>

      <div className={styles.row} style={{ marginBottom: 'var(--space-4)' }}>
        <label className={styles.row} style={{ gap: 'var(--space-2)', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={soloAperte}
            onChange={(e) => setSoloAperte(e.target.checked)}
          />
          Mostra solo non risolti
        </label>
      </div>

      {errore && <ErrorBox message={errore} />}
      {!notifiche && !errore && <Loading label="Caricamento avvisi…" />}

      {notifiche && (
        notifiche.length === 0 ? (
          <Empty label="Nessun avviso." />
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
                    <strong>{TIPO_LABEL[n.tipo] ?? n.tipo}</strong>
                    <span className={styles.notifMeta}>{formatDataOra(n.creato_at)}</span>
                  </div>
                  <p className={styles.notifText}>{n.messaggio}</p>
                  <div className={styles.row}>
                    {risolta ? (
                      <Badge tone="success">Risolto</Badge>
                    ) : (
                      <>
                        {n.letta_at === null && (
                          <Button small variant="secondary" onClick={() => segnaLetta(n.id)}>
                            Segna come letto
                          </Button>
                        )}
                        <Button small onClick={() => risolvi(n.id)}>
                          Fatto
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
