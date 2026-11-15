// File Name: useAcademicYear.js
// Description: Shared helper/hook returning the system current academic year (YYYY-YYYY) from the signed-in user profile.
// Created At: 2026-11-15
// Created By: AI Agent
// Updated At: 2026-11-15
// Updated By: AI Agent

import { useAuth } from '../context/AuthContext';

/** Fallback when the profile has no value: school year starts in September. */
export function fallbackAcademicYear(now = new Date()) {
  const start = now.getMonth() >= 8 ? now.getFullYear() : now.getFullYear() - 1;
  return `${start}-${start + 1}`;
}

/** Years current-2 .. current+2 as 'YYYY-YYYY' values. */
export function academicYearOptions(current) {
  const start = parseInt(String(current).slice(0, 4), 10) || new Date().getFullYear();
  return [-2, -1, 0, 1, 2].map((d) => `${start + d}-${start + d + 1}`);
}

/** Returns { value: 'YYYY-YYYY', label: 'YYYY - YYYY' }. */
export default function useAcademicYear() {
  const { currentAcademicYear } = useAuth();
  const value = currentAcademicYear || fallbackAcademicYear();
  return { value, label: value.replace('-', ' - ') };
}
