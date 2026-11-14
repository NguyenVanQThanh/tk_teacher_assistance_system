// File Name: AuthContext.jsx
// Description: Authentication Context Provider managing JWT token, user profile, effective permissions, and login/logout flows.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-10-28
// Updated By: Tam Khang

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [isLoading, setIsLoading] = useState(true);

  // Validate token on mount
  useEffect(() => {
    async function verifyAuth() {
      const storedToken = localStorage.getItem('access_token');
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        const profile = await authApi.getMe();
        setUser(profile);
      } catch (err) {
        console.error('Session expired or invalid token:', err);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_info');
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    verifyAuth();
  }, []);

  const login = async (phoneOrEmail, password) => {
    const data = await authApi.login({
      phone: phoneOrEmail,
      password: password,
    });

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user_info', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data;
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (err) {
      console.warn('Logout API error:', err);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      setToken(null);
      setUser(null);
    }
  };

  const hasPermission = (permissionCode) => {
    if (!user) return false;
    if (user.role === 'Admin') return true;
    return Array.isArray(user.permissions) && user.permissions.includes(permissionCode);
  };

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    logout,
    hasPermission,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
