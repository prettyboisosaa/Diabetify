/**
 * Shell dell'area paziente: header (brand + nome paziente + logout), navigazione
 * (Home · Glicemie · Terapie · Diario · Messaggi · Notifiche con badge non lette)
 * e <Outlet> per le pagine.
 */

import { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { logout } from '../../lib/auth';
import { getProfilo, getNotifiche, getMessaggi } from '../../lib/paziente';
import styles from './PatientLayout.module.css';

export default function PatientLayout() {
  const navigate = useNavigate();
  const [nome, setNome] = useState<string>('');
  const [notificheAperte, setNotificheAperte] = useState(0);
  const [messaggiNonLetti, setMessaggiNonLetti] = useState(0);

  // Dati per header e contatori della navigazione
  useEffect(() => {
    getProfilo()
      .then((p) => setNome(`${p.nome} ${p.cognome}`))
      .catch(() => setNome(''));
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

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`;

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <div className={styles.logoMark} aria-hidden="true">D</div>
          <div className={styles.brandText}>
            <span className={styles.brandName}>Diabetify</span>
            <span className={styles.brandRole}>Area Paziente</span>
          </div>
        </div>
        <div className={styles.headerRight}>
          {nome && <span className={styles.userName}>{nome}</span>}
          <button className={styles.logout} onClick={handleLogout}>
            Esci
          </button>
        </div>
      </header>

      <div className={styles.body}>
        <nav className={styles.nav} aria-label="Navigazione area paziente">
          <NavLink to="/patient" end className={linkClass}>
            Home
          </NavLink>
          <NavLink to="/patient/glicemie" className={linkClass}>
            Glicemie
          </NavLink>
          <NavLink to="/patient/terapie" className={linkClass}>
            Terapie
          </NavLink>
          <NavLink to="/patient/diario" className={linkClass}>
            Diario
          </NavLink>
          <NavLink to="/patient/messaggi" className={linkClass}>
            Messaggi
            {messaggiNonLetti > 0 && (
              <span className={styles.navCount}>{messaggiNonLetti}</span>
            )}
          </NavLink>
          <NavLink to="/patient/notifiche" className={linkClass}>
            Notifiche
            {notificheAperte > 0 && (
              <span className={styles.navCount}>{notificheAperte}</span>
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
