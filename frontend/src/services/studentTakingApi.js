// File Name: studentTakingApi.js
// Description: Dedicated axios client for the student exam "taking" flow. Calls the
// sanitized GET /api/v1/assignments/{assignmentId}/taking endpoint (assignment +
// exercise + already-sanitized questions + open_attempt) and provides a client-side
// sanitizer used when falling back to the raw exercise detail endpoint.
// Created At: 2026-11-12
// Created By: AI Agent
// Updated At: 2026-11-13
// Updated By: AI Agent

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

// In-flight de-duplication for the GET taking endpoint. Only signal-less, non-forced
// calls share a promise: an aborted caller must never cancel another caller's request,
// and a forced call (e.g. the refetch that runs right after an attempt is started) must
// always hit the network because the backend re-shuffles the paper for the new seed.
const inFlightTakingRequests = new Map();

export const studentTakingApi = {
  /**
   * GET /api/v1/assignments/{assignmentId}/taking
   * Expected response: { assignment, exercise, questions (sanitized), open_attempt }
   *
   * @param {string} assignmentId
   * @param {{ signal?: AbortSignal, force?: boolean }} [options]
   *   signal — abort the HTTP request (axios CanceledError is rejected to the caller).
   *   force  — bypass the in-flight de-dupe map; use after starting an attempt so the
   *            response reflects that attempt's shuffle seed instead of the preview one.
   */
  getAssignmentTaking: async (assignmentId, { signal, force = false } = {}) => {
    const cacheKey = String(assignmentId);
    const canShare = !force && !signal;

    if (canShare && inFlightTakingRequests.has(cacheKey)) {
      return inFlightTakingRequests.get(cacheKey);
    }

    const request = studentTakingClient
      .get(`/api/v1/assignments/${assignmentId}/taking`, { signal })
      .then((response) => response.data);

    if (canShare) {
      inFlightTakingRequests.set(cacheKey, request);
      const release = () => {
        if (inFlightTakingRequests.get(cacheKey) === request) {
          inFlightTakingRequests.delete(cacheKey);
        }
      };
      // Both handlers release the slot; the derived promise always resolves so it
      // never becomes an unhandled rejection.
      request.then(release, release);
    }

    return request;
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
