import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import DoctorLayout from './pages/doctor/DoctorLayout';
import PatientListPage from './pages/doctor/PatientListPage';
import PatientDetailPage from './pages/doctor/PatientDetailPage';
import DoctorNotifichePage from './pages/doctor/NotifichePage';
import DoctorMessaggiPage from './pages/doctor/MessaggiPage';
import PatientLayout from './pages/patient/PatientLayout';
import DashboardPage from './pages/patient/DashboardPage';
import GlicemiePage from './pages/patient/GlicemiePage';
import TerapiePage from './pages/patient/TerapiePage';
import DiarioPage from './pages/patient/DiarioPage';
import PatientMessaggiPage from './pages/patient/MessaggiPage';
import PatientNotifichePage from './pages/patient/NotifichePage';
import AdminLayout from './pages/admin/AdminLayout';
import UtentiPage from './pages/admin/UtentiPage';
import CreaUtentePage from './pages/admin/CreaUtentePage';
import AuditLogPage from './pages/admin/AuditLogPage';
import ControlliSistemaPage from './pages/admin/ControlliSistemaPage';
import { ProtectedRoute } from './components/ProtectedRoute';
import { getRole, isAuthenticated } from './lib/auth';

function RootRedirect() {
  if (isAuthenticated()) {
    const role = getRole();
    if (role) return <Navigate to={`/${role}`} replace />;
  }
  return <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/login" element={<Login />} />

        {/* Area Medico: rotte annidate sotto il layout, protette dal ruolo doctor */}
        <Route
          path="/doctor"
          element={
            <ProtectedRoute role="doctor">
              <DoctorLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<PatientListPage />} />
          <Route path="pazienti/:id" element={<PatientDetailPage />} />
          <Route path="notifiche" element={<DoctorNotifichePage />} />
          <Route path="messaggi" element={<DoctorMessaggiPage />} />
        </Route>

        {/* Area Paziente: rotte annidate sotto il layout, protette dal ruolo patient */}
        <Route
          path="/patient"
          element={
            <ProtectedRoute role="patient">
              <PatientLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="glicemie" element={<GlicemiePage />} />
          <Route path="terapie" element={<TerapiePage />} />
          <Route path="diario" element={<DiarioPage />} />
          <Route path="messaggi" element={<PatientMessaggiPage />} />
          <Route path="notifiche" element={<PatientNotifichePage />} />
        </Route>
        {/* Area Amministratore: rotte annidate sotto il layout, protette dal ruolo admin */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute role="admin">
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<UtentiPage />} />
          <Route path="crea" element={<CreaUtentePage />} />
          <Route path="audit" element={<AuditLogPage />} />
          <Route path="controlli" element={<ControlliSistemaPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
