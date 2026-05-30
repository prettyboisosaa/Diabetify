import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../lib/auth';
import styles from './Login.module.css';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const role = await login(email, password);
      navigate(`/${role}`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login fallito');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <header className={styles.header}>
          <div className={styles.logoMark} aria-hidden="true">D</div>
          <h1 className={styles.title}>Diabetify</h1>
          <p className={styles.subtitle}>Piattaforma di telemedicina</p>
        </header>

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="email">Email</label>
            <input
              id="email"
              className={styles.input}
              type="email"
              autoComplete="email"
              placeholder="nome@esempio.it"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
              required
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="password">Password</label>
            <input
              id="password"
              className={styles.input}
              type="password"
              autoComplete="current-password"
              placeholder="La tua password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isSubmitting}
              required
            />
          </div>

          {error && <p className={styles.error} role="alert">{error}</p>}

          <button
            type="submit"
            className={styles.submit}
            disabled={isSubmitting || !email || !password}
          >
            {isSubmitting ? 'Accesso in corso...' : 'Accedi'}
          </button>
        </form>

        <p className={styles.footer}>Accesso riservato al personale autorizzato</p>
      </section>
    </main>
  );
}
