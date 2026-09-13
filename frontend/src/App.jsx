// File Name: App.jsx
// Description: Main application router with AuthProvider, ProtectedRoute, TeacherLayout, StudentLayout, and standalone exam taking mode.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import TeacherLayout from './components/layout/TeacherLayout';
import StudentLayout from './components/layout/StudentLayout';
import LoginPage from './pages/LoginPage';

// Teacher Pages
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

// Student Pages
import StudentDashboard from './pages/student/StudentDashboard';
import StudentExercisesPage from './pages/student/StudentExercisesPage';
import StudentExerciseTakingPage from './pages/student/StudentExerciseTakingPage';

function RootRedirector() {
  const { user } = useAuth();
  if (user?.role === 'Student') {
    return <Navigate to="/student" replace />;
  }
  return <Navigate to="/teacher" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Root Role Dispatcher */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <RootRedirector />
              </ProtectedRoute>
            }
          />

          {/* Standalone Fullscreen Exam Taking Interface */}
          <Route
            path="/student/exercises/:exerciseId/taking"
            element={
              <ProtectedRoute>
                <StudentExerciseTakingPage />
              </ProtectedRoute>
            }
          />

          {/* Protected Teacher Module Routes with Shared Persistent TeacherLayout */}
          <Route
            element={
              <ProtectedRoute>
                <TeacherLayout />
              </ProtectedRoute>
            }
          >
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

          {/* Protected Student Module Routes with Shared Persistent StudentLayout */}
          <Route
            element={
              <ProtectedRoute>
                <StudentLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/student" element={<StudentDashboard />} />
            <Route path="/student/dashboard" element={<StudentDashboard />} />
            <Route path="/student/exercises" element={<StudentExercisesPage />} />
          </Route>

          {/* Catch-all Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
