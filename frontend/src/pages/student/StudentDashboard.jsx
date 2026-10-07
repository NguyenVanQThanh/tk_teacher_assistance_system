// File Name: StudentDashboard.jsx
// Description: Student Dashboard featuring interactive study schedule synchronization, categorized pending assignments, flexible right container switching between daily schedule and detailed pending assignments, and full-screen cognitive radar modal.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-27
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import PendingStudentAssignmentsCard from '../../components/student/PendingStudentAssignmentsCard';
import StudentScheduleCard from '../../components/student/StudentScheduleCard';
import StudentRadarCard from '../../components/student/StudentRadarCard';
import TeacherFeedbackNoteCard from '../../components/student/TeacherFeedbackNoteCard';
import StudentScheduleDetailCard from '../../components/student/StudentScheduleDetailCard';
import StudentPendingAssignmentsDetailCard from '../../components/student/StudentPendingAssignmentsDetailCard';
import StudentSubjectRadarModal from '../../components/student/StudentSubjectRadarModal';
import { studentApi } from '../../services/api';
import './StudentDashboard.css';

export default function StudentDashboard() {
  // Currently selected calendar day (defaults to 8 matching Image 1)
  const [selectedDay, setSelectedDay] = useState(8);
  
  // Flexible right container active view: 'schedule' | 'assignments'
  const [activeRightPanel, setActiveRightPanel] = useState('schedule');

  // Currently selected subject for detailed radar analysis
  const [selectedSubject, setSelectedSubject] = useState('Toán Học');
  
  // State to open full-screen dialog modal for Image 3
  const [isRadarModalOpen, setIsRadarModalOpen] = useState(false);

  // Backend dashboard data
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadDashboard() {
      try {
        setLoading(true);
        const data = await studentApi.getDashboard();
        if (isMounted) setDashboardData(data);
      } catch (err) {
        console.error('Failed to load student dashboard:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadDashboard();
    return () => { isMounted = false; };
  }, []);

  // Triggered when a calendar day is clicked in StudentScheduleCard
  const handleSelectDay = (day) => {
    setSelectedDay(day);
    setActiveRightPanel('schedule');
  };

  // Triggered when a subject is clicked on either radar chart -> Opens Fullscreen Dialog matching Image 3
  const handleSelectSubject = (subjectName) => {
    setSelectedSubject(subjectName);
    setIsRadarModalOpen(true);
  };

  const classroomRadarScores = dashboardData?.radar_competency?.length
    ? dashboardData.radar_competency.slice(0, 6).map(r => r.score)
    : [8.5, 7.8, 8.2, 7.0, 6.5, 8.0];

  const feedback1 = dashboardData?.qualitative_feedback?.[0] || {
    title: 'Nhận xét',
    quote: '“Kỹ năng giao tiếp và tổ chức đang có sự tiến bộ rõ rệt trong tháng này.”',
    author_name: 'Thầy Long',
    author_initial: 'L'
  };

  const feedback2 = dashboardData?.qualitative_feedback?.[1] || {
    title: 'Nhận xét',
    quote: '“Năng lực sáng tạo xuất sắc khi giải quyết các vấn đề phát sinh trong tuần qua.”',
    author_name: 'Cô Trang',
    author_initial: 'T'
  };

  return (
    <div className="student-dashboard-page">
      <div className="student-dashboard-grid-layout">
        {/* Main 2-Column Matrix (6 Cards) */}
        <div className="student-dashboard-main-columns">
          {/* Row 1: Homework checklist (Categorized) & Monthly Calendar */}
          <PendingStudentAssignmentsCard 
            isActive={activeRightPanel === 'assignments'}
            onClickCard={() => setActiveRightPanel('assignments')}
            assignments={dashboardData?.upcoming_assignments}
          />
          <StudentScheduleCard 
            selectedDay={selectedDay}
            onSelectDay={handleSelectDay}
            isActive={activeRightPanel === 'schedule'}
            onClickCard={() => setActiveRightPanel('schedule')}
          />

          {/* Row 2: Bài tập trên lớp (Interactive Radar - Click to open full dialog modal) */}
          <StudentRadarCard 
            title="Bài tập trên lớp"
            totalLabel={`Tổng: ${dashboardData?.metrics?.completed_exercises_count ?? 15}`}
            scores={classroomRadarScores}
            selectedSubject={selectedSubject}
            onSelectSubject={handleSelectSubject}
          />
          <TeacherFeedbackNoteCard
            title={feedback1.title}
            quote={feedback1.quote}
            authorName={feedback1.author_name}
            authorInitial={feedback1.author_initial}
            authorBg="#EDE9FE"
            authorColor="#7C3AED"
          />

          {/* Row 3: Bài tập tạo sinh (Interactive Radar - Click to open full dialog modal) */}
          <StudentRadarCard 
            title="Bài tập tạo sinh"
            totalLabel={`Tổng: ${dashboardData?.metrics?.study_time_minutes ? Math.round(dashboardData.metrics.study_time_minutes / 60) : 12}`}
            scores={[7.8, 8.5, 7.2, 8.0, 6.0, 8.5]}
            selectedSubject={selectedSubject}
            onSelectSubject={handleSelectSubject}
          />
          <TeacherFeedbackNoteCard
            title={feedback2.title}
            quote={feedback2.quote}
            authorName={feedback2.author_name}
            authorInitial={feedback2.author_initial}
            authorBg="#EDE9FE"
            authorColor="#7C3AED"
          />
        </div>

        {/* Right Column: Flexible container switching between Schedule and Assignments details */}
        <div className="student-dashboard-right-panel">
          {activeRightPanel === 'schedule' ? (
            <div className="right-panel-content-body">
              <StudentScheduleDetailCard 
                selectedDay={selectedDay}
                selectedMonth="Thg 3"
              />
            </div>
          ) : (
            <div className="right-panel-content-body">
              <StudentPendingAssignmentsDetailCard 
                onSwitchToSchedule={() => setActiveRightPanel('schedule')}
              />
            </div>
          )}
        </div>
      </div>

      {/* Fullscreen Dialog Modal for Subject Radar matching Image 3 */}
      <StudentSubjectRadarModal
        isOpen={isRadarModalOpen}
        subjectName={selectedSubject}
        onClose={() => setIsRadarModalOpen(false)}
      />
    </div>
  );
}
