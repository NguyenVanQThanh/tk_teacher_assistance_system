// File Name: App.jsx
// Description: Main application router with AuthProvider, ProtectedRoute, and unified TeacherLayout wrapper.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-02
// Updated By: Tam Khang

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import TeacherLayout from './components/layout/TeacherLayout';
import LoginPage from './pages/LoginPage';
import TeacherDashboard from './pages/teacher/TeacherDashboard';
import DocumentRepositoryPage from './pages/teacher/DocumentRepositoryPage';
import ExerciseRepositoryPage from './pages/teacher/ExerciseRepositoryPage';
import CreateExerciseManualPage from './pages/teacher/CreateExerciseManualPage';
import TeacherClassesPage from './pages/teacher/TeacherClassesPage';
import TeacherClassDetailPage from './pages/teacher/TeacherClassDetailPage';
import TeacherHomeroomPage from './pages/teacher/TeacherHomeroomPage';
import TeacherGradingPage from './pages/teacher/TeacherGradingPage';
import TeacherSchedulePage from './pages/teacher/TeacherSchedulePage';
import TeacherProfilePage from './pages/teacher/TeacherProfilePage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Teacher Module Routes with Shared Persistent TeacherLayout */}
          <Route
            element={
              <ProtectedRoute>
                <TeacherLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<TeacherDashboard />} />
            <Route path="/teacher" element={<TeacherDashboard />} />
            <Route path="/teacher/classes" element={<TeacherClassesPage />} />
            <Route path="/teacher/classes/:classId" element={<TeacherClassDetailPage />} />
            <Route path="/teacher/homeroom" element={<TeacherHomeroomPage />} />
            <Route path="/teacher/grading" element={<TeacherGradingPage />} />
            <Route path="/teacher/schedule" element={<TeacherSchedulePage />} />
            <Route path="/teacher/profile" element={<TeacherProfilePage />} />
            <Route path="/teacher/documents" element={<DocumentRepositoryPage />} />
            <Route path="/teacher/exercises" element={<ExerciseRepositoryPage />} />
            <Route path="/teacher/exercises/create-manual" element={<CreateExerciseManualPage />} />
          </Route>

          {/* Catch-all Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
