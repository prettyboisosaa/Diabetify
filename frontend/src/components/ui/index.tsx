/**
 * Piccola libreria di componenti UI riusabili per il lato medico.
 * Tutti consumano gli stili condivisi in `ui.module.css` (token di theme.css).
 */

import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './ui.module.css';

// =========================================================
// Card
// =========================================================
export function Card({
  title,
  children,
  className,
}: {
  title?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`${styles.card} ${className ?? ''}`}>
      {title && <h2 className={styles.cardTitle}>{title}</h2>}
      {children}
    </section>
  );
}

// =========================================================
// Button
// =========================================================
type Variant = 'primary' | 'secondary' | 'danger';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  small?: boolean;
}

export function Button({
  variant = 'primary',
  small = false,
  className,
  children,
  ...rest
}: ButtonProps) {
  const variantClass =
    variant === 'primary'
      ? styles.btnPrimary
      : variant === 'danger'
        ? styles.btnDanger
        : styles.btnSecondary;
  return (
    <button
      className={`${styles.btn} ${variantClass} ${small ? styles.btnSmall : ''} ${className ?? ''}`}
      {...rest}
    >
      {children}
    </button>
  );
}

// =========================================================
// Badge (tono legato alla severita'/stato)
// =========================================================
type Tone = 'info' | 'success' | 'warning' | 'critical' | 'neutral';

export function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  const toneClass = {
    info: styles.badgeInfo,
    success: styles.badgeSuccess,
    warning: styles.badgeWarning,
    critical: styles.badgeCritical,
    neutral: styles.badgeNeutral,
  }[tone];
  return <span className={`${styles.badge} ${toneClass}`}>{children}</span>;
}

// =========================================================
// Field: label + input o textarea o select
// =========================================================
interface FieldProps {
  label: string;
  id: string;
  as?: 'input' | 'textarea' | 'select';
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  disabled?: boolean;
  min?: number;
  step?: string;
  placeholder?: string;
  children?: ReactNode; // per le <option> quando as="select"
}

export function Field({
  label,
  id,
  as = 'input',
  value,
  onChange,
  type = 'text',
  required,
  disabled,
  min,
  step,
  placeholder,
  children,
}: FieldProps) {
  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={id}>
        {label}
      </label>
      {as === 'textarea' ? (
        <textarea
          id={id}
          className={styles.control}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          disabled={disabled}
          placeholder={placeholder}
        />
      ) : as === 'select' ? (
        <select
          id={id}
          className={styles.control}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          disabled={disabled}
        >
          {children}
        </select>
      ) : (
        <input
          id={id}
          className={styles.control}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          disabled={disabled}
          min={min}
          step={step}
          placeholder={placeholder}
        />
      )}
    </div>
  );
}

// =========================================================
// Stati di caricamento / errore / vuoto
// =========================================================
export function Loading({ label = 'Caricamento…' }: { label?: string }) {
  return (
    <p className={styles.state} role="status">
      {label}
    </p>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <p className={`${styles.state} ${styles.stateError}`} role="alert">
      {message}
    </p>
  );
}

export function Empty({ label }: { label: string }) {
  return <p className={styles.state}>{label}</p>;
}
