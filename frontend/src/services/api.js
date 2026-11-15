// File Name: api.js
// Description: Centralized Axios API client configuration with token management, academic, assignment, admin, and schedule service APIs.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-11-14
// Updated By: Tam Khang

import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
    }
    return Promise.reject(error);
  }
);

// Response interceptor: forward the X-Data-Version header of every GET response to dataSync.
// Lazy dynamic import avoids a circular dependency (dataSync imports syncApi from this file).
api.interceptors.response.use(
  (response) => {
    try {
      const v = response?.headers?.['x-data-version'];
      if (v) {
        import('./dataSync')
          .then((m) => {
            const ds = m.default || m;
            ds.notifyHeaderVersion?.(v);
          })
          .catch(() => {});
      }
    } catch (e) {}
    return response;
  },
  (error) => Promise.reject(error)
);

export const authApi = {
  login: async (credentials) => {
    const response = await api.post('/api/v1/auth/login', credentials);
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/api/v1/auth/me');
    return response.data;
  },
  changePassword: async (passwords) => {
    const response = await api.post('/api/v1/auth/change-password', passwords);
    return response.data;
  },
  updateProfile: async (profileData) => {
    const response = await api.put('/api/v1/auth/profile', profileData);
    return response.data;
  },
  logout: async () => {
    try {
      await api.post('/api/v1/auth/logout');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
    }
  },
};

export const classesApi = {
  getClasses: async (params = {}) => {
    const response = await api.get('/api/v1/classes', { params });
    return response.data;
  },
  getClassDetail: async (classId) => {
    const response = await api.get(`/api/v1/classes/${classId}`);
    return response.data;
  },
  createClass: async (data) => {
    const response = await api.post('/api/v1/classes', data);
    return response.data;
  },
  updateClass: async (classId, data) => {
    const response = await api.put(`/api/v1/classes/${classId}`, data);
    return response.data;
  },
  deleteClass: async (classId) => {
    const response = await api.delete(`/api/v1/classes/${classId}`);
    return response.data;
  },
  restoreClass: async (classId) => {
    const response = await api.post(`/api/v1/classes/${classId}/restore`);
    return response.data;
  },
  getStudentsInClass: async (classId, params = {}) => {
    const response = await api.get(`/api/v1/classes/${classId}/students`, { params });
    return response.data;
  },
  getClassStudents: async (classId, params = {}) => {
    const response = await api.get(`/api/v1/classes/${classId}/students`, { params });
    return response.data;
  },
  getTeacherSubjects: async (classId, params = {}) => {
    const response = await api.get(`/api/v1/classes/${classId}/teacher-subjects`, { params });
    return response.data;
  },
  enrollStudent: async (classId, data) => {
    const response = await api.post(`/api/v1/classes/${classId}/students`, data);
    return response.data;
  },
  unenrollStudent: async (classId, studentId) => {
    const response = await api.delete(`/api/v1/classes/${classId}/students/${studentId}`);
    return response.data;
  },
  getAvailableStudents: async (classId) => {
    const response = await api.get('/api/v1/classes/available-students', {
      params: classId ? { class_id: classId } : {},
    });
    return response.data;
  },
  importStudentsExcel: async (classId, file) => {
    const fd = new FormData();
    fd.append('file', file);
    const response = await api.post(`/api/v1/classes/${classId}/students/import-excel`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  exportClassesCsv: async () => {
    const response = await api.get('/api/v1/classes/export-csv', {
      responseType: 'blob',
    });
    return response.data;
  },
};

export const subjectsApi = {
  getSubjects: async (params = {}) => {
    const response = await api.get('/api/v1/subjects', { params });
    return response.data;
  },
  getSubjectDetail: async (subjectId) => {
    const response = await api.get(`/api/v1/subjects/${subjectId}`);
    return response.data;
  },
  getHeadCandidates: async (subjectId) => {
    const response = await api.get(`/api/v1/subjects/${subjectId}/head-teacher-candidates`);
    return response.data;
  },
  assignHeadTeacher: async (subjectId, teacherId) => {
    const response = await api.put(`/api/v1/subjects/${subjectId}/head-teacher`, { teacher_id: teacherId });
    return response.data;
  },
};

export const exercisesApi = {
  getExercises: async (params = {}) => {
    const response = await api.get('/api/v1/exercises', { params });
    return response.data;
  },
  getExerciseDetail: async (exerciseId) => {
    const response = await api.get(`/api/v1/exercises/${exerciseId}`);
    return response.data;
  },
  createExercise: async (data) => {
    const response = await api.post('/api/v1/exercises', data);
    return response.data;
  },
  updateExercise: async (exerciseId, data) => {
    const response = await api.put(`/api/v1/exercises/${exerciseId}`, data);
    return response.data;
  },
  setAnswerRelease: async (exerciseId, released) => {
    const response = await api.put(`/api/v1/exercises/${exerciseId}/answer-release`, { released });
    return response.data;
  },
  deleteExercise: async (exerciseId) => {
    await api.delete(`/api/v1/exercises/${exerciseId}`);
  },
  exportPdf: async (exerciseId) => {
    const response = await api.get(`/api/v1/exercises/${exerciseId}/export/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },
  importQuestions: async (exerciseId, formData) => {
    const response = await api.post(`/api/v1/exercises/${exerciseId}/questions/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    const data = response.data;
    // Backend reports questions skipped during import via headers; attach them to
    // the returned array so callers can warn the user without breaking `.length`.
    if (Array.isArray(data)) {
      data.skippedCount = parseInt(response.headers?.['x-import-skipped-count'] || '0', 10) || 0;
    }
    return data;
  },
  addQuestion: async (exerciseId, data) => {
    const response = await api.post(`/api/v1/exercises/${exerciseId}/questions`, data);
    return response.data;
  },
  generateAiExercise: async (data) => {
    const response = await api.post('/api/v1/exercises/ai-generate', data);
    return response.data;
  },
};

export const aiExercisesApi = {
  // Chapters available for a subject (grade resolved server-side from the student's class)
  getChapters: async (subjectId) => {
    const response = await api.get('/api/v1/ai-exercises/chapters', { params: { subject_id: subjectId } });
    return response.data;
  },
  // Multipart: `payload` JSON string + optional `file`
  generateForStudent: async (payload, file = null) => {
    const formData = new FormData();
    formData.append('payload', JSON.stringify(payload));
    if (file) formData.append('file', file);
    const response = await api.post('/api/v1/ai-exercises/student', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000,
    });
    return response.data;
  },
};

export const questionsApi = {
  uploadImage: async (formData) => {
    const response = await api.post('/api/v1/questions/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  updateQuestion: async (questionId, data) => {
    const response = await api.put(`/api/v1/questions/${questionId}`, data);
    return response.data;
  },
  deleteQuestion: async (questionId) => {
    await api.delete(`/api/v1/questions/${questionId}`);
  },
};

export const assignmentsApi = {
  createAssignment: async (classId, data) => {
    const response = await api.post(`/api/v1/classes/${classId}/assignments`, data);
    return response.data;
  },
  assignToMultipleClasses: async (classIds, data) => {
    const promises = classIds.map((cid) =>
      api.post(`/api/v1/classes/${cid}/assignments`, data)
        .then((res) => ({ classId: cid, success: true, data: res.data }))
        .catch((err) => ({
          classId: cid,
          success: false,
          error: err.response?.data?.detail?.message || err.message,
          code: err.response?.data?.detail?.code,
        }))
    );
    return Promise.all(promises);
  },
  getAssignments: async (params = {}) => {
    try {
      const response = await api.get('/api/v1/assignments', { params });
      return response.data;
    } catch (err) {
      if (err.response?.status === 404) {
        const classesRes = await api.get('/api/v1/classes');
        const classes = Array.isArray(classesRes.data) ? classesRes.data : [];
        const promises = classes.map(c => api.get(`/api/v1/classes/${c.class_id}/assignments`).then(r => r.data).catch(() => []));
        const res = await Promise.all(promises);
        return res.flat();
      }
      throw err;
    }
  },
  getClassAssignments: async (classId) => {
    const response = await api.get(`/api/v1/classes/${classId}/assignments`);
    return response.data;
  },
  deleteAssignment: async (assignmentId) => {
    await api.delete(`/api/v1/assignments/${assignmentId}`);
  },
  setAnswerRelease: async (assignmentId, released) => {
    const response = await api.put(`/api/v1/assignments/${assignmentId}/answer-release`, { released });
    return response.data;
  },
  restoreAssignment: async (assignmentId) => {
    const response = await api.post(`/api/v1/assignments/${assignmentId}/restore`);
    return response.data;
  },
  getAssignmentResult: async (assignmentId, params = {}) => {
    const response = await api.get(`/api/v1/assignments/${assignmentId}/result`, { params });
    return response.data;
  },
};

export const attemptsApi = {
  getAttempts: async (params = {}) => {
    const response = await api.get('/api/v1/attempts', { params });
    return response.data;
  },
  getGradingDashboard: async (params = {}) => {
    const response = await api.get('/api/v1/attempts/dashboard', { params });
    return response.data;
  },
  getAttemptDetail: async (attemptId) => {
    const response = await api.get(`/api/v1/attempts/${attemptId}`);
    return response.data;
  },
  getAttempt: async (attemptId) => {
    const response = await api.get(`/api/v1/attempts/${attemptId}`);
    return response.data;
  },
  startAttempt: async (assignmentId) => {
    const response = await api.post(`/api/v1/assignments/${assignmentId}/attempts`);
    return response.data;
  },
  submitAttempt: async (attemptId, data) => {
    const response = await api.put(`/api/v1/attempts/${attemptId}/submit`, data);
    return response.data;
  },
  updateGrade: async (attemptId, data) => {
    const response = await api.put(`/api/v1/attempts/${attemptId}/grade`, data);
    return response.data;
  },
  updateAnswerKey: async (exerciseId, data) => {
    const response = await api.put(`/api/v1/exercises/${exerciseId}/answer-key`, data);
    return response.data;
  },
  exportReport: async (params = {}) => {
    const response = await api.get('/api/v1/attempts/export', { params, responseType: 'blob' });
    return response.data;
  },
  getAssignmentAttempts: async (assignmentId, params = {}) => {
    const response = await api.get(`/api/v1/assignments/${assignmentId}/attempts`, { params });
    return response.data;
  },
};

export const documentsApi = {
  getDocuments: async (params = {}) => {
    const response = await api.get('/api/v1/documents', { params });
    return response.data;
  },
  // Teacher's own uploaded documents that finished RAG ingestion (usable as AI context)
  getUsableDocuments: async (params = {}) => {
    const response = await api.get('/api/v1/documents', {
      params: { mine: true, status: 'Uploaded', ready_only: true, page_size: 100, ...params },
    });
    return response.data;
  },
  getDocumentDashboard: async () => {
    const response = await api.get('/api/v1/documents/dashboard');
    return response.data;
  },
  uploadDocument: async (formData) => {
    const response = await api.post('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  viewDocument: async (documentId) => {
    const response = await api.get('/api/v1/documents/' + documentId + '/view', {
      responseType: 'blob',
    });
    return response.data;
  },
  downloadDocument: async (documentId) => {
    const response = await api.get(`/api/v1/documents/${documentId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
  getDocumentDetail: async (documentId) => {
    const response = await api.get(`/api/v1/documents/${documentId}`);
    return response.data;
  },
  updateDocument: async (documentId, data) => {
    const response = await api.put(`/api/v1/documents/${documentId}`, data);
    return response.data;
  },
  deleteDocument: async (documentId) => {
    await api.delete(`/api/v1/documents/${documentId}`);
  },
  restoreDocument: async (documentId) => {
    const response = await api.post(`/api/v1/documents/${documentId}/restore`);
    return response.data;
  },
};

export const adminUsersApi = {
  getUsers: async (params = {}) => {
    const response = await api.get('/api/v1/admin/users', { params });
    return response.data;
  },
  getUserDetail: async (userId) => {
    const response = await api.get(`/api/v1/admin/users/${userId}`);
    return response.data;
  },
  createUser: async (data) => {
    const response = await api.post('/api/v1/admin/users', data);
    return response.data;
  },
  updateUser: async (userId, data) => {
    const response = await api.put(`/api/v1/admin/users/${userId}`, data);
    return response.data;
  },
  updateStatus: async (userId, status, reason = '') => {
    const response = await api.patch(`/api/v1/admin/users/${userId}/status`, { status, reason });
    return response.data;
  },
  deleteUser: async (userId) => {
    const response = await api.delete(`/api/v1/admin/users/${userId}`);
    return response.data;
  },
  restoreUser: async (userId) => {
    const response = await api.post(`/api/v1/admin/users/${userId}/restore`);
    return response.data;
  },
  resetPassword: async (userId, newPassword = null) => {
    const payload = newPassword ? { new_password: newPassword } : {};
    const response = await api.post(`/api/v1/admin/users/${userId}/reset-password`, payload);
    return response.data;
  },
  exportExcel: async (params = {}) => {
    const response = await api.get('/api/v1/admin/users/export-excel', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
  downloadImportTemplate: async (format = 'xlsx') => {
    const response = await api.get('/api/v1/admin/users/import-template', {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },
  importExcel: async (formData) => {
    const response = await api.post('/api/v1/admin/users/import-excel', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  generateCode: async (role = 'student') => {
    const response = await api.get('/api/v1/admin/users/generate-code', { params: { role } });
    return response.data;
  },
  checkCode: async (code) => {
    const response = await api.get('/api/v1/admin/users/check-code', { params: { code } });
    return response.data;
  },
};

export const adminDashboardApi = {
  getStats: async () => {
    const response = await api.get('/api/v1/admin/dashboard/stats');
    return response.data;
  },
  getActivityChart: async (timeframe = 'week') => {
    const response = await api.get('/api/v1/admin/dashboard/activity-chart', {
      params: { timeframe },
    });
    return response.data;
  },
  getApprovalRequests: async () => {
    const response = await api.get('/api/v1/admin/dashboard/requests');
    return response.data;
  },
  approveRequest: async (requestId) => {
    const response = await api.post(`/api/v1/admin/dashboard/requests/${requestId}/approve`);
    return response.data;
  },
  rejectRequest: async (requestId) => {
    const response = await api.post(`/api/v1/admin/dashboard/requests/${requestId}/reject`);
    return response.data;
  },
  getAuditLogs: async (limit = 10) => {
    const response = await api.get('/api/v1/admin/dashboard/audit-logs', {
      params: { limit },
    });
    return response.data;
  },
};

export const adminRolesApi = {
  getRoles: async () => {
    const response = await api.get('/api/v1/admin/roles');
    return response.data;
  },
  createRole: async (data) => {
    const response = await api.post('/api/v1/admin/roles', data);
    return response.data;
  },
  updatePermissions: async (roleCode, permissions) => {
    const response = await api.put(`/api/v1/admin/roles/${roleCode}/permissions`, { permissions });
    return response.data;
  },
  getRoleMembers: async (roleCode) => {
    const response = await api.get(`/api/v1/admin/roles/${roleCode}/members`);
    return response.data;
  },
  assignRoleMember: async (roleCode, userId) => {
    const response = await api.post(`/api/v1/admin/roles/${roleCode}/members`, { user_id: userId });
    return response.data;
  },
  exportRoles: async (format = 'json') => {
    const response = await api.get('/api/v1/admin/roles/export', {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },
};

// Admin-only realtime monitoring API. The SSE stream is consumed with fetch() in
// AdminMonitoringPage because EventSource cannot attach the Authorization header.
export const monitoringApi = {
  getSummary: async (windowSeconds = 300) => (await api.get('/api/v1/admin/monitoring/summary', { params: { window_seconds: windowSeconds } })).data,
  getRequests: async (params = {}) => (await api.get('/api/v1/admin/monitoring/requests', { params })).data,
  getHealth: async () => (await api.get('/api/v1/admin/monitoring/health')).data,
};

export const studentApi = {
  getDashboard: async () => {
    const response = await api.get('/api/v1/student/dashboard');
    return response.data;
  },
};

// Data version sync API: backend exposes GET /api/v1/sync/version -> { version, tables }
// and an SSE stream GET /api/v1/sync/stream that emits { version } on change.
export const syncApi = {
  getVersion: async () => {
    const response = await api.get('/api/v1/sync/version');
    return response.data;
  },
  // Optional SSE subscription. EventSource cannot set the Authorization header, so a
  // 30s single-purpose ticket (never the access token) goes in the query string.
  // The ticket is fetched per (re)connect. Returns a close() function.
  // Primary mechanism remains polling in dataSync.js; this is best-effort.
  subscribeVersionStream: (onVersion) => {
    if (typeof EventSource === 'undefined') return () => {};
    const base = api.defaults.baseURL || '';
    let es = null;
    let closed = false;
    let retryTimer = null;
    const connect = async () => {
      if (closed) return;
      try {
        const { data } = await api.post('/api/v1/sync/stream-ticket');
        if (closed) return;
        es = new EventSource(`${base}/api/v1/sync/stream?ticket=${encodeURIComponent(data.ticket)}`);
      } catch (e) {
        retryTimer = setTimeout(connect, 10000);
        return;
      }
      es.onmessage = (ev) => {
        try {
          const d = JSON.parse(ev.data);
          if (d?.version && typeof onVersion === 'function') onVersion(d.version);
        } catch (e) {}
      };
      // Native auto-reconnect would reuse the expired ticket: close and fetch a new one.
      es.onerror = () => {
        try { es.close(); } catch (e) {}
        if (!closed) retryTimer = setTimeout(connect, 5000);
      };
    };
    connect();
    return () => {
      closed = true;
      clearTimeout(retryTimer);
      try { es && es.close(); } catch (e) {}
    };
  },
};

export const teacherApi = {
  getNotifications: async () => {
    const response = await api.get('/api/v1/teacher/notifications');
    return response.data;
  },
  getDashboard: async (params = {}) => {
    const response = await api.get('/api/v1/teacher/dashboard', { params });
    return response.data;
  },
  getLearningQuality: async (params = {}) => {
    const response = await api.get('/api/v1/teacher/learning-quality', { params });
    return response.data;
  },
  getSchedule: async () => {
    const response = await api.get('/api/v1/teacher/schedule');
    return response.data;
  },
  getScheduleNotes: async () => {
    const response = await api.get('/api/v1/teacher/schedule/notes');
    return response.data;
  },
  createScheduleNote: async (data) => {
    const response = await api.post('/api/v1/teacher/schedule/notes', data);
    return response.data;
  },
  deleteScheduleNote: async (noteId) => {
    const response = await api.delete(`/api/v1/teacher/schedule/notes/${noteId}`);
    return response.data;
  },
};

export default api;



