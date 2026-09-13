// File Name: SubjectTeacherDashboard.jsx
// Description: Specialized Dashboard for Subject Teachers featuring calendar schedule selector, pending grading, and daily schedule details.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getTeacherSubjectInfo } from '../../utils/teacherSubjectHelper';
import TeacherScheduleCalendarCard from '../../components/teacher/TeacherScheduleCalendarCard';
import PendingGradingCard from '../../components/teacher/PendingGradingCard';
import RecentSubmissionsSummaryCard from '../../components/teacher/RecentSubmissionsSummaryCard';
import DailyScheduleDetailCard from '../../components/teacher/DailyScheduleDetailCard';
import './SubjectTeacherDashboard.css';

export default function SubjectTeacherDashboard() {
  const { user } = useAuth();
  const [selectedDay, setSelectedDay] = useState(5); // Default to Thursday 5th

  const teacherSubject = getTeacherSubjectInfo(user);

  // Derive dynamic greeting title (e.g. "Thầy Long" or "Cô Trang")
  const getGreetingData = (fullName) => {
    if (!fullName) return { title: 'Thầy', name: 'Thầy Lê' };
    const isFemale = fullName.includes('Cô') || fullName.includes('Thị') || fullName.includes('Mai') || fullName.includes('Trang');
    const title = isFemale ? 'Cô' : 'Thầy';
    
    let cleanName = fullName.replace(/^(Sample Teacher \(|Thầy |Cô |\))/gi, '').trim();
    const parts = cleanName.split(' ');
    const displayPart = parts[0] || parts[parts.length - 1] || 'Lê';
    return {
      title,
      name: `${title} ${displayPart}`
    };
  };

  const { title: teacherTitle, name: greetingName } = getGreetingData(user?.full_name);

  return (
    <div className="subject-dashboard-container">
      {/* Top Breadcrumbs & Greeting Header */}
      <div className="subject-dashboard-header">
        <nav className="subject-dashboard-breadcrumbs" aria-label="Breadcrumb">
          <Link to="/teacher" className="subject-breadcrumb-link">Trang chủ</Link>
          <span className="subject-breadcrumb-slash">/</span>
          <span className="subject-breadcrumb-current">Bảng điều khiển</span>
        </nav>
        <h1 className="subject-dashboard-title">
          Xin chào, {greetingName}! <span className="subject-greeting-wave">👋</span>
        </h1>
        <p className="subject-dashboard-subtitle">
          Dưới đây là tổng quan về hoạt động giảng dạy bộ môn {teacherSubject.subjectName} của {teacherTitle.toLowerCase()} hôm nay.
        </p>
      </div>

      {/* Main Two-Column Layout Grid */}
      <div className="subject-dashboard-content-layout">
        {/* Left Column: Interactive Schedule Calendar + 2 Bottom Cards */}
        <div className="subject-dashboard-left-column">
          <TeacherScheduleCalendarCard 
            selectedDay={selectedDay} 
            onSelectDay={(day) => setSelectedDay(day)} 
          />

          <div className="subject-dashboard-bottom-row">
            <PendingGradingCard />
            <RecentSubmissionsSummaryCard />
          </div>
        </div>

        {/* Right Column: Daily Schedule Details */}
        <div className="subject-dashboard-right-column">
          <DailyScheduleDetailCard selectedDay={selectedDay} />
        </div>
      </div>
    </div>
  );
}
