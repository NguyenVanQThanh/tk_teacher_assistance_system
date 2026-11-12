// File Name: studentTakingApi.js
// Description: Dedicated axios client for the student exam "taking" flow. Calls the
// sanitized GET /api/v1/assignments/{assignmentId}/taking endpoint (assignment +
// exercise + already-sanitized questions + open_attempt) and provides a client-side
// sanitizer used when falling back to the raw exercise detail endpoint.
// Created At: 2026-11-12
// Created By: AI Agent

import axios from 'axios';

const studentTakingClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT bearer token from localStorage (same pattern as services/api.js)
studentTakingClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Mirror the 401 handling of the central client: drop stale credentials
studentTakingClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
    }
    return Promise.reject(error);
  }
);

export const studentTakingApi = {
  /**
   * GET /api/v1/assignments/{assignmentId}/taking
   * Expected response: { assignment, exercise, questions (sanitized), open_attempt }
   */
  getAssignmentTaking: async (assignmentId) => {
    const response = await studentTakingClient.get(`/api/v1/assignments/${assignmentId}/taking`);
    return response.data;
  },
};

/**
 * Strip answer-leaking fields from questions before they ever reach client state:
 * - question.correct_answer, question.explanation
 * - answer_options[].is_correct
 * - segments[].is_correct
 * Everything else (content, image_url, image_metadata, segments content/type, option
 * content/display_order, question_type, ...) is preserved so the taking UI can render.
 */
export function sanitizeQuestionsForStudent(questions) {
  if (!Array.isArray(questions)) return [];
  return questions.map((q) => {
    if (!q || typeof q !== 'object') return q;
    const { correct_answer, explanation, ...rest } = q;
    const sanitized = { ...rest };
    if (Array.isArray(sanitized.answer_options)) {
      sanitized.answer_options = sanitized.answer_options.map((opt) => {
        if (!opt || typeof opt !== 'object') return opt;
        const { is_correct, ...optRest } = opt;
        return optRest;
      });
    }
    if (Array.isArray(sanitized.segments)) {
      sanitized.segments = sanitized.segments.map((seg) => {
        if (!seg || typeof seg !== 'object') return seg;
        const { is_correct, ...segRest } = seg;
        return segRest;
      });
    }
    return sanitized;
  });
}

export default studentTakingClient;
