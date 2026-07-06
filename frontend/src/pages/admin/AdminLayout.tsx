/**
 * Shell dell'area amministratore (Responsabile del Servizio): header + logout e
 * navigazione (Utenti · Crea utente · Registro audit · Controlli sistema).
 */

import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { logout } from '../../lib/auth';
import styles from './AdminLayout.module.css';

export default function AdminLayout() {
  const navigate = useNavigate();

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
            <span className={styles.brandRole}>Area Amministratore</span>
          </div>
        </div>
        <div className={styles.headerRight}>
          <button className={styles.logout} onClick={handleLogout}>
            Esci
          </button>
        </div>
      </header>

      <div className={styles.body}>
        <nav className={styles.nav} aria-label="Navigazione area amministratore">
          <NavLink to="/admin" end className={linkClass}>Utenti</NavLink>
          <NavLink to="/admin/crea" className={linkClass}>Crea utente</NavLink>
          <NavLink to="/admin/audit" className={linkClass}>Registro audit</NavLink>
          <NavLink to="/admin/controlli" className={linkClass}>Controlli sistema</NavLink>
        </nav>

        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
