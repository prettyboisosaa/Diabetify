/**
 * Home del paziente: riepilogo a colpo d'occhio (ultima glicemia, terapie attive,
 * notifiche aperte) e scorciatoie alle azioni rapide.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getProfilo,
  getGlicemie,
  getTerapie,
  getNotifiche,
} from '../../lib/paziente';
import { Button, Badge, Loading } from '../../components/ui';
import styles from '../../styles/data.module.css';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [nome, setNome] = useState('');
  const [ultimaGlicemia, setUltimaGlicemia] = useState<number | null>(null);
  const [fuoriSoglia, setFuoriSoglia] = useState(false);
  const [terapieAttive, setTerapieAttive] = useState<number | null>(null);
  const [notificheAperte, setNotificheAperte] = useState<number | null>(null);

  useEffect(() => {
    getProfilo().then((p) => setNome(p.nome)).catch(() => {});
    getGlicemie()
      .then((g) => {
        if (g.length > 0) {
          setUltimaGlicemia(g[0].valore); // già ordinate desc dal backend
          setFuoriSoglia(g[0].fuori_soglia);
        }
      })
      .catch(() => {});
    getTerapie()
      .then((t) => setTerapieAttive(t.filter((x) => x.is_active).length))
      .catch(() => {});
    getNotifiche(true)
      .then((n) => setNotificheAperte(n.length))
      .catch(() => {});
  }, []);

  const caricato =
    terapieAttive !== null && notificheAperte !== null;

  return (
    <div>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Ciao{nome ? `, ${nome}` : ''} 👋</h1>
        <p className={styles.pageSubtitle}>Ecco un riepilogo del tuo stato di salute.</p>
      </div>

      {!caricato ? (
        <Loading />
      ) : (
        <div className={styles.stack}>
          <div className={styles.statGrid}>
            <div className={styles.statTile}>
              <p className={styles.statLabel}>Ultima glicemia</p>
              <p className={styles.statValue}>
                {ultimaGlicemia !== null ? `${ultimaGlicemia} mg/dL` : '—'}
              </p>
              {ultimaGlicemia !== null && (
                <div style={{ marginTop: 'var(--space-2)' }}>
                  {fuoriSoglia ? (
                    <Badge tone="critical">Fuori soglia</Badge>
                  ) : (
                    <Badge tone="success">Nella norma</Badge>
                  )}
                </div>
              )}
            </div>

            <div className={styles.statTile}>
              <p className={styles.statLabel}>Terapie attive</p>
              <p className={styles.statValue}>{terapieAttive}</p>
            </div>

            <div className={styles.statTile}>
              <p className={styles.statLabel}>Avvisi da leggere</p>
              <p className={styles.statValue}>{notificheAperte}</p>
            </div>
          </div>

          <div className={styles.quickLinks}>
            <Button onClick={() => navigate('/patient/glicemie')}>
              + Registra glicemia
            </Button>
            <Button variant="secondary" onClick={() => navigate('/patient/terapie')}>
              + Registra assunzione
            </Button>
            <Button variant="secondary" onClick={() => navigate('/patient/messaggi')}>
              Scrivi al medico
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
