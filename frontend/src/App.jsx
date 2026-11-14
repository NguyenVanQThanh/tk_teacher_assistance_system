// File Name: App.jsx
// Description: Main application router with AuthProvider, ProtectedRoute, TeacherLayout, StudentLayout, and standalone exam taking mode.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-27
// Updated By: Tam Khang

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import TeacherLayout from './components/layout/TeacherLayout';
import StudentLayout from './components/layout/StudentLayout';
import LoginPage from './pages/LoginPage';

// Layouts stay eager (small, needed for every route in the section). Pages are
// code-split with React.lazy so the public login screen does not download the
// teacher/student/admin bundles (KaTeX, MathLive, Tiptap, dashboards, ...).
import AdminLayout from './components/layout/AdminLayout';

// Teacher Pages
const TeacherDashboard = React.lazy(() => import('./pages/teacher/TeacherDashboard'));
const DocumentRepositoryPage = React.lazy(() => import('./pages/teacher/DocumentRepositoryPage'));
const ExerciseRepositoryPage = React.lazy(() => import('./pages/teacher/ExerciseRepositoryPage'));
const CreateExerciseManualPage = React.lazy(() => import('./pages/teacher/CreateExerciseManualPage'));
const TeacherClassesPage = React.lazy(() => import('./pages/teacher/TeacherClassesPage'));
const TeacherClassDetailPage = React.lazy(() => import('./pages/teacher/TeacherClassDetailPage'));
const TeacherHomeroomPage = React.lazy(() => import('./pages/teacher/TeacherHomeroomPage'));
const TeacherGradingPage = React.lazy(() => import('./pages/teacher/TeacherGradingPage'));
const TeacherSchedulePage = React.lazy(() => import('./pages/teacher/TeacherSchedulePage'));
const TeacherProfilePage = React.lazy(() => import('./pages/teacher/TeacherProfilePage'));

// Student Pages
const StudentDashboard = React.lazy(() => import('./pages/student/StudentDashboard'));
const StudentExercisesPage = React.lazy(() => import('./pages/student/StudentExercisesPage'));
const StudentExerciseTakingPage = React.lazy(() => import('./pages/student/StudentExerciseTakingPage'));

// Admin Pages
const AdminDashboard = React.lazy(() => import('./pages/admin/AdminDashboard'));
const AdminUsersPage = React.lazy(() => import('./pages/admin/AdminUsersPage'));
const AdminClassesPage = React.lazy(() => import('./pages/admin/AdminClassesPage'));
const AdminRolesPage = React.lazy(() => import('./pages/admin/AdminRolesPage'));
const AdminSubjectsPage = React.lazy(() => import('./pages/admin/AdminSubjectsPage'));
const AdminReportsPage = React.lazy(() => import('./pages/admin/AdminReportsPage'));
const AdminSettingsPage = React.lazy(() => import('./pages/admin/AdminSettingsPage'));
const AdminMonitoringPage = React.lazy(() => import('./pages/admin/AdminMonitoringPage'));

function RootRedirector() {
  const { user } = useAuth();
  if (user?.role === 'Admin') {
    return <Navigate to="/admin" replace />;
  }
  if (user?.role === 'Student') {
    return <Navigate to="/student" replace />;
  }
  return <Navigate to="/teacher" replace />;
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          backgroundColor: '#F8F7FA',
          color: '#332B4F',
          fontFamily: 'Be Vietnam Pro, sans-serif',
          textAlign: 'center'
        }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            backgroundColor: '#FEE2E2',
            color: '#DC2626',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            marginBottom: '16px'
          }}>
            !
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, margin: '0 0 8px' }}>
            Đã xảy ra lỗi khi tải trang
          </h2>
          <p style={{ fontSize: '14px', color: '#6E6784', maxWidth: '480px', margin: '0 0 20px' }}>
            {this.state.error?.message || 'Không thể hiển thị trang vào lúc này. Vui lòng tải lại hoặc quay về trang chủ.'}
          </p>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="button"
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 20px',
                borderRadius: '10px',
                backgroundColor: '#4D308D',
                color: '#FFFFFF',
                border: 'none',
                fontWeight: 600,
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Tải lại trang
            </button>
            <button
              type="button"
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.href = '/';
              }}
              style={{
                padding: '10px 20px',
                borderRadius: '10px',
                backgroundColor: '#FFFFFF',
                color: '#4D308D',
                border: '1px solid #DCD6E8',
                fontWeight: 600,
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Về trang chủ
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
        <React.Suspense
          fallback={
            <div style={{
              minHeight: '100vh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#F8F7FA',
              color: '#4D308D',
              fontFamily: 'Be Vietnam Pro, sans-serif',
              fontSize: '14px',
              fontWeight: 600,
            }}>
              Đang tải trang…
            </div>
          }
        >
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
              <ProtectedRoute allowedRoles={['Student']}>
                <StudentExerciseTakingPage />
              </ProtectedRoute>
            }
          />

          {/* Protected Teacher Module Routes with Shared Persistent TeacherLayout */}
          <Route
            element={
              <ProtectedRoute allowedRoles={['Teacher']}>
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
              <ProtectedRoute allowedRoles={['Student']}>
                <StudentLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/student" element={<StudentDashboard />} />
            <Route path="/student/dashboard" element={<StudentDashboard />} />
            <Route path="/student/exercises" element={<StudentExercisesPage />} />
          </Route>

          {/* Protected Admin Module Routes with Shared Persistent AdminLayout */}
          <Route
            element={
              <ProtectedRoute allowedRoles={['Admin']}>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/classes" element={<AdminClassesPage />} />
            <Route path="/admin/roles" element={<AdminRolesPage />} />
            <Route path="/admin/subjects" element={<AdminSubjectsPage />} />
            <Route path="/admin/reports" element={<AdminReportsPage />} />
            <Route path="/admin/monitoring" element={<AdminMonitoringPage />} />
            <Route path="/admin/settings" element={<AdminSettingsPage />} />
          </Route>

          {/* Catch-all Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </React.Suspense>
      </BrowserRouter>
    </AuthProvider>
    </ErrorBoundary>
  );
}

