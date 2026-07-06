/**
 * Shell dell'area medico: header con brand + nome medico + logout, navigazione
 * (Pazienti · Notifiche · Messaggi con badge conteggio) e <Outlet> per le pagine.
 */

import { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { logout } from '../../lib/auth';
import { getProfiloMedico, getNotifiche, getMessaggi } from '../../lib/medico';
import styles from './DoctorLayout.module.css';

export default function DoctorLayout() {
  const navigate = useNavigate();
  const [nomeMedico, setNomeMedico] = useState<string>('');
  const [notificheAperte, setNotificheAperte] = useState(0);
  const [messaggiNonLetti, setMessaggiNonLetti] = useState(0);

  // Carica dati per l'header e i contatori della navigazione
  useEffect(() => {
    getProfiloMedico()
      .then((m) => setNomeMedico(`Dr. ${m.nome} ${m.cognome}`))
      .catch(() => setNomeMedico(''));
    getNotifiche(true)
      .then((n) => setNotificheAperte(n.length))
      .catch(() => {});
    getMessaggi()
      .then((m) => setMessaggiNonLetti(m.filter((x) => x.letto_at === null).length))
      .catch(() => {});
  }, []);

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  // Classe attiva/inattiva per i NavLink
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`;

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <div className={styles.logoMark} aria-hidden="true">D</div>
          <div className={styles.brandText}>
            <span className={styles.brandName}>Diabetify</span>
            <span className={styles.brandRole}>Area Medico</span>
          </div>
        </div>
        <div className={styles.headerRight}>
          {nomeMedico && <span className={styles.doctorName}>{nomeMedico}</span>}
          <button className={styles.logout} onClick={handleLogout}>
            Esci
          </button>
        </div>
      </header>

      <div className={styles.body}>
        <nav className={styles.nav} aria-label="Navigazione area medico">
          <NavLink to="/doctor" end className={linkClass}>
            Pazienti
          </NavLink>
          <NavLink to="/doctor/notifiche" className={linkClass}>
            Notifiche
            {notificheAperte > 0 && (
              <span className={styles.navCount}>{notificheAperte}</span>
            )}
          </NavLink>
          <NavLink to="/doctor/messaggi" className={linkClass}>
            Messaggi
            {messaggiNonLetti > 0 && (
              <span className={styles.navCount}>{messaggiNonLetti}</span>
            )}
          </NavLink>
        </nav>

        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
