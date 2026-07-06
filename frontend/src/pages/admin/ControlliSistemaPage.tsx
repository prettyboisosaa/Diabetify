/**
 * Superficie visibile dell'attore SISTEMA: il Responsabile del Servizio avvia
 * manualmente i controlli temporali di aderenza terapeutica (RF-11/12/13).
 * Gli avvisi generati compaiono poi nelle inbox notifiche di medico e paziente.
 * In produzione questi controlli girerebbero via cron (RNF-3, script run_sistema.py).
 */

import { useState } from 'react';
import { eseguiControlliSistema, type ControlliSistemaResult } from '../../lib/admin';
import { Card, Button, Badge, ErrorBox } from '../../components/ui';
import styles from '../../styles/data.module.css';

export default function ControlliSistemaPage() {
  const [inCorso, setInCorso] = useState(false);
  const [risultato, setRisultato] = useState<ControlliSistemaResult | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  async function esegui() {
    setInCorso(true);
    setErrore(null);
    setRisultato(null);
    try {
      setRisultato(await eseguiControlliSistema());
    } catch (err) {
      setErrore(err instanceof Error ? err.message : 'Errore durante i controlli.');
    } finally {
      setInCorso(false);
    }
  }

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Controlli di sistema</h1>
        <p className={styles.pageSubtitle}>
          Verifica dell'aderenza terapeutica: genera solleciti ai pazienti (RF-12) e
          alert di mancata aderenza ai medici (RF-13).
        </p>
      </div>

      <Card>
        <p style={{ marginTop: 0, color: 'var(--text-muted)' }}>
          I controlli sulle glicemie fuori soglia (RF-14) sono automatici a ogni
          rilevazione. Qui esegui i controlli temporali sull'assunzione dei farmaci.
          L'operazione è idempotente: ripeterla non crea avvisi duplicati.
        </p>
        <div className={styles.formActions}>
          <Button onClick={esegui} disabled={inCorso}>
            {inCorso ? 'Esecuzione…' : 'Esegui controlli di sistema'}
          </Button>
        </div>
      </Card>

      {errore && <div style={{ marginTop: 'var(--space-4)' }}><ErrorBox message={errore} /></div>}

      {risultato && (
        <div style={{ marginTop: 'var(--space-4)' }}>
          <Card title="Esito controlli">
            <div className={styles.row} style={{ marginBottom: 'var(--space-3)' }}>
              <Badge tone={risultato.notifiche_create > 0 ? 'warning' : 'success'}>
                {risultato.notifiche_create} notifiche generate
              </Badge>
            </div>
            {risultato.dettaglio.length === 0 ? (
              <p style={{ margin: 0, color: 'var(--text-muted)' }}>
                Nessun nuovo avviso: tutti i pazienti risultano in regola (o già avvisati).
              </p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 'var(--space-5)' }}>
                {risultato.dettaglio.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
