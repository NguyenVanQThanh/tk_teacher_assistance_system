// File Name: StudentDashboard.jsx
// Description: Student Dashboard featuring interactive study schedule synchronization, full-screen dialog for subject cognitive radar analysis matching Image 3, and rich student mock data.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState } from 'react';
import PendingStudentAssignmentsCard from '../../components/student/PendingStudentAssignmentsCard';
import StudentScheduleCard from '../../components/student/StudentScheduleCard';
import StudentRadarCard from '../../components/student/StudentRadarCard';
import TeacherFeedbackNoteCard from '../../components/student/TeacherFeedbackNoteCard';
import StudentScheduleDetailCard from '../../components/student/StudentScheduleDetailCard';
import StudentSubjectRadarModal from '../../components/student/StudentSubjectRadarModal';
import './StudentDashboard.css';

export default function StudentDashboard() {
  // Currently selected calendar day (defaults to 8 matching Image 1)
  const [selectedDay, setSelectedDay] = useState(8);
  
  // Currently selected subject for detailed radar analysis
  const [selectedSubject, setSelectedSubject] = useState('Toán Học');
  
  // State to open full-screen dialog modal for Image 3
  const [isRadarModalOpen, setIsRadarModalOpen] = useState(false);

  // Triggered when a calendar day is clicked in StudentScheduleCard
  const handleSelectDay = (day) => {
    setSelectedDay(day);
  };

  // Triggered when a subject is clicked on either radar chart -> Opens Fullscreen Dialog matching Image 3
  const handleSelectSubject = (subjectName) => {
    setSelectedSubject(subjectName);
    setIsRadarModalOpen(true);
  };

  return (
    <div className="student-dashboard-page">
      <div className="student-dashboard-grid-layout">
        {/* Main 2-Column Matrix (6 Cards) */}
        <div className="student-dashboard-main-columns">
          {/* Row 1: Homework checklist & Monthly Calendar */}
          <PendingStudentAssignmentsCard />
          <StudentScheduleCard 
            selectedDay={selectedDay}
            onSelectDay={handleSelectDay}
          />

          {/* Row 2: Bài tập trên lớp (Interactive Radar - Click to open full dialog modal) */}
          <StudentRadarCard 
            title="Bài tập trên lớp"
            totalLabel="Tổng: 15"
            scores={[8.5, 7.8, 8.2, 7.0, 6.5, 8.0]}
            selectedSubject={selectedSubject}
            onSelectSubject={handleSelectSubject}
          />
          <TeacherFeedbackNoteCard
            title="Nhận xét"
            quote="&ldquo;Kỹ năng giao tiếp và tổ chức đang có sự tiến bộ rõ rệt trong tháng này.&rdquo;"
            authorName="Mr. Anderson"
            authorInitial="M"
            authorBg="#EDE9FE"
            authorColor="#7C3AED"
          />

          {/* Row 3: Bài tập tạo sinh (Interactive Radar - Click to open full dialog modal) */}
          <StudentRadarCard 
            title="Bài tập tạo sinh"
            totalLabel="Tổng: 12"
            scores={[7.8, 8.5, 7.2, 8.0, 6.0, 8.5]}
            selectedSubject={selectedSubject}
            onSelectSubject={handleSelectSubject}
          />
          <TeacherFeedbackNoteCard
            title="Nhận xét"
            quote="&ldquo;Năng lực sáng tạo xuất sắc khi giải quyết các vấn đề phát sinh trong tuần qua.&rdquo;"
            authorName="Ms. Anh"
            authorInitial="A"
            authorBg="#EDE9FE"
            authorColor="#7C3AED"
          />
        </div>

        {/* Right Column: Chi tiết dashboard matching Image 2 */}
        <div className="student-dashboard-right-panel">
          <StudentScheduleDetailCard 
            selectedDay={selectedDay}
            selectedMonth="Thg 3"
          />
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
