/**
 * RF-10 / UC-10: aggiornamento anamnesi (fattori di rischio, patologie
 * pregresse, comorbita'). Mostra i valori correnti e un form per modificarli.
 * Il salvataggio genera un audit lato backend (RF-15).
 */

import { useState, type FormEvent } from 'react';
import {
  aggiornaAnamnesi,
  type PatientProfile,
} from '../../../lib/medico';
import { Card, Button, Field } from '../../../components/ui';
import styles from '../../../styles/data.module.css';

interface Props {
  paziente: PatientProfile;
  onUpdated: (p: PatientProfile) => void;
}

export default function AnamnesiSection({ paziente, onUpdated }: Props) {
  const [fattoriRischio, setFattoriRischio] = useState(paziente.fattori_rischio ?? '');
  const [patologiePregresse, setPatologiePregresse] = useState(
    paziente.patologie_pregresse ?? '',
  );
  const [comorbita, setComorbita] = useState(paziente.comorbita ?? '');
  const [salvataggio, setSalvataggio] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; testo: string } | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvataggio(true);
    setFeedback(null);
    try {
      const aggiornato = await aggiornaAnamnesi(paziente.id, {
        fattori_rischio: fattoriRischio,
        patologie_pregresse: patologiePregresse,
        comorbita,
      });
      onUpdated(aggiornato);
      setFeedback({ ok: true, testo: 'Anamnesi aggiornata correttamente.' });
    } catch (err) {
      setFeedback({
        ok: false,
        testo: err instanceof Error ? err.message : 'Errore durante il salvataggio.',
      });
    } finally {
      setSalvataggio(false);
    }
  }

  return (
    <div className={styles.stack}>
      <Card title="Dati anagrafici">
        <dl className={styles.defList}>
          <div>
            <div className={styles.defTerm}>Nome completo</div>
            <p className={styles.defValue}>
              {paziente.nome} {paziente.cognome}
            </p>
          </div>
        </dl>
      </Card>

      <Card title="Anamnesi e fattori di rischio">
        <form onSubmit={handleSubmit}>
          <div className={styles.formGrid}>
            <Field
              id="fattori_rischio"
              label="Fattori di rischio (fumo, alcol, obesità…)"
              as="textarea"
              value={fattoriRischio}
              onChange={setFattoriRischio}
              disabled={salvataggio}
            />
            <Field
              id="patologie_pregresse"
              label="Patologie pregresse"
              as="textarea"
              value={patologiePregresse}
              onChange={setPatologiePregresse}
              disabled={salvataggio}
            />
            <Field
              id="comorbita"
              label="Comorbità (es. ipertensione)"
              as="textarea"
              value={comorbita}
              onChange={setComorbita}
              disabled={salvataggio}
            />
          </div>

          <div className={styles.formActions}>
            <Button type="submit" disabled={salvataggio}>
              {salvataggio ? 'Salvataggio…' : 'Salva anamnesi'}
            </Button>
          </div>

          {feedback && (
            <p
              className={`${styles.formFeedback} ${
                feedback.ok ? styles.feedbackOk : styles.feedbackErr
              }`}
              role="alert"
            >
              {feedback.testo}
            </p>
          )}
        </form>
      </Card>
    </div>
  );
}
