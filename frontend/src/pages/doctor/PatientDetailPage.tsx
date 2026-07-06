/**
 * Scheda clinica del paziente, organizzata a tab:
 *  - Panoramica/Anamnesi (RF-10)
 *  - Glicemie (RF-9: dettaglio + aggregato)
 *  - Terapie (RF-8) + assunzioni del paziente
 *  - Clinica (sintomi, patologie concomitanti, terapie parallele - RF-5, lettura)
 *
 * L'apertura della scheda registra un audit lato backend (RF-15).
 */

import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getScheda, type PatientProfile } from '../../lib/medico';
import { ErrorBox, Loading } from '../../components/ui';
import AnamnesiSection from './sections/AnamnesiSection';
import GlicemieSection from './sections/GlicemieSection';
import TerapieSection from './sections/TerapieSection';
import ClinicaSection from './sections/ClinicaSection';
import styles from '../../styles/data.module.css';

type Tab = 'panoramica' | 'glicemie' | 'terapie' | 'clinica';

const TABS: { id: Tab; label: string }[] = [
  { id: 'panoramica', label: 'Panoramica & Anamnesi' },
  { id: 'glicemie', label: 'Glicemie' },
  { id: 'terapie', label: 'Terapie' },
  { id: 'clinica', label: 'Sintomi & Patologie' },
];

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const patientId = Number(id);
  const [paziente, setPaziente] = useState<PatientProfile | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('panoramica');

  useEffect(() => {
    setPaziente(null);
    setErrore(null);
    getScheda(patientId)
      .then(setPaziente)
      .catch((e) => setErrore(e.message));
  }, [patientId]);

  return (
    <div>
      <Link to="/doctor" className={styles.backLink}>
        ← Torna ai pazienti
      </Link>

      {errore && <ErrorBox message={errore} />}
      {!paziente && !errore && <Loading label="Caricamento scheda…" />}

      {paziente && (
        <>
          <div className={styles.pageHeader}>
            <h1 className={styles.pageTitle}>
              {paziente.nome} {paziente.cognome}
            </h1>
            <p className={styles.pageSubtitle}>Scheda clinica del paziente</p>
          </div>

          <div className={styles.tabs} role="tablist">
            {TABS.map((t) => (
              <button
                key={t.id}
                role="tab"
                aria-selected={tab === t.id}
                className={`${styles.tab} ${tab === t.id ? styles.tabActive : ''}`}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === 'panoramica' && (
            <AnamnesiSection paziente={paziente} onUpdated={setPaziente} />
          )}
          {tab === 'glicemie' && <GlicemieSection patientId={patientId} />}
          {tab === 'terapie' && <TerapieSection patientId={patientId} />}
          {tab === 'clinica' && <ClinicaSection patientId={patientId} />}
        </>
      )}
    </div>
  );
}
