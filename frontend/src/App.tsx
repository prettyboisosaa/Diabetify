import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import DoctorHome from './pages/DoctorHome';
import PatientHome from './pages/PatientHome';
import AdminHome from './pages/AdminHome';
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
        <Route
          path="/doctor"
          element={
            <ProtectedRoute role="doctor">
              <DoctorHome />
            </ProtectedRoute>
          }
        />
        <Route
          path="/patient"
          element={
            <ProtectedRoute role="patient">
              <PatientHome />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute role="admin">
              <AdminHome />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
