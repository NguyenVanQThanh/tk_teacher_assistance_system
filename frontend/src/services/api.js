// File Name: api.js
// Description: Centralized Axios API client configuration with token management and academic service APIs.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-01
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
  getStudentsInClass: async (classId, params = {}) => {
    const response = await api.get(`/api/v1/classes/${classId}/students`, { params });
    return response.data;
  },
  getTeacherSubjects: async (classId, params = {}) => {
    const response = await api.get(`/api/v1/classes/${classId}/teacher-subjects`, { params });
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
    return response.data;
  },
  addQuestion: async (exerciseId, data) => {
    const response = await api.post(`/api/v1/exercises/${exerciseId}/questions`, data);
    return response.data;
  },
};

export const questionsApi = {
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
  getClassAssignments: async (classId) => {
    const response = await api.get(`/api/v1/classes/${classId}/assignments`);
    return response.data;
  },
  deleteAssignment: async (assignmentId) => {
    await api.delete(`/api/v1/assignments/${assignmentId}`);
  },
  restoreAssignment: async (assignmentId) => {
    const response = await api.post(`/api/v1/assignments/${assignmentId}/restore`);
    return response.data;
  },
};

export const attemptsApi = {
  getAttempts: async (params = {}) => {
    const response = await api.get('/api/v1/attempts', { params });
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
};

export default api;


