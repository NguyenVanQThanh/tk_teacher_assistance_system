// File Name: ProtectedRoute.jsx
// Description: Route guard middleware requiring valid authentication and authorized roles before accessing protected pages.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-27
// Updated By: Tam Khang

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#F8F7FA',
        color: '#4D308D',
        fontFamily: 'Be Vietnam Pro, sans-serif',
        gap: '16px'
      }}>
        <div style={{
          width: '36px',
          height: '36px',
          border: '3px solid #E9DDFF',
          borderTopColor: '#4D308D',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite'
        }} />
        <span style={{ fontSize: '14px', fontWeight: 600 }}>Checking access permissions...</span>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page and save previous location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role-based access control
  if (allowedRoles && allowedRoles.length > 0 && user?.role) {
    if (!allowedRoles.includes(user.role)) {
      if (user.role === 'Student') {
        return <Navigate to="/student" replace />;
      }
      if (user.role === 'Admin') {
        return <Navigate to="/admin" replace />;
      }
      return <Navigate to="/teacher" replace />;
    }
  }

  return children;
}

