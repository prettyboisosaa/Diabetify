import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { getRole, isAuthenticated, type Role } from '../lib/auth';

interface ProtectedRouteProps {
  role: Role;
  children: ReactNode;
}

export function ProtectedRoute({ role, children }: ProtectedRouteProps) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  const currentRole = getRole();
  if (currentRole !== role) {
    return <Navigate to={currentRole ? `/${currentRole}` : '/login'} replace />;
  }

  return <>{children}</>;
}
