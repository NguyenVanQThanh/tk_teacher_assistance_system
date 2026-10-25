// File Name: TeacherDashboard.jsx
// Description: Dynamic Dashboard Router dispatching between Homeroom Teacher Dashboard and Subject Teacher Dashboard based on teacher role.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { getTeacherProfileDefaults } from '../../utils/teacherSubjectHelper';
import HomeroomTeacherDashboard from './HomeroomTeacherDashboard';
import SubjectTeacherDashboard from './SubjectTeacherDashboard';

export default function TeacherDashboard() {
  const { user } = useAuth();
  const profileDefaults = getTeacherProfileDefaults(user);

  // Check if teacher is assigned as a Homeroom Teacher (GVCN)
  const isHomeroomTeacher = user?.role === 'HomeroomTeacher' || profileDefaults.isHomeroom;

  if (isHomeroomTeacher) {
    return <HomeroomTeacherDashboard />;
  }

  return <SubjectTeacherDashboard />;
}
