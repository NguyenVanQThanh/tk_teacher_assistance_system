// File Name: App.jsx
// Description: Main application router with AuthProvider, ProtectedRoute guards, and Exercise Creation views.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-31
// Updated By: Tam Khang

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import TeacherDashboard from './pages/teacher/TeacherDashboard';
import DocumentRepositoryPage from './pages/teacher/DocumentRepositoryPage';
import ExerciseRepositoryPage from './pages/teacher/ExerciseRepositoryPage';
import CreateExerciseManualPage from './pages/teacher/CreateExerciseManualPage';
import TeacherClassesPage from './pages/teacher/TeacherClassesPage';
import TeacherClassDetailPage from './pages/teacher/TeacherClassDetailPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Teacher Dashboard Routes */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <TeacherDashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teacher" 
            element={
              <ProtectedRoute>
                <TeacherDashboard />
              </ProtectedRoute>
            } 
          />

          {/* Protected Teacher Classes Routes */}
          <Route 
            path="/teacher/classes" 
            element={
              <ProtectedRoute>
                <TeacherClassesPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teacher/classes/:classId" 
            element={
              <ProtectedRoute>
                <TeacherClassDetailPage />
              </ProtectedRoute>
            } 
          />

          {/* Protected Teacher Document Repository Route */}
          <Route 
            path="/teacher/documents" 
            element={
              <ProtectedRoute>
                <DocumentRepositoryPage />
              </ProtectedRoute>
            } 
          />

          {/* Protected Teacher Exercise Repository Route */}
          <Route 
            path="/teacher/exercises" 
            element={
              <ProtectedRoute>
                <ExerciseRepositoryPage />
              </ProtectedRoute>
            } 
          />

          {/* Protected Direct Exercise Creation Page */}
          <Route 
            path="/teacher/exercises/create-manual" 
            element={
              <ProtectedRoute>
                <CreateExerciseManualPage />
              </ProtectedRoute>
            } 
          />

          {/* Catch-all Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

