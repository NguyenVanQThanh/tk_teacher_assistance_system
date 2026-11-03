// File Name: SubjectTeacherDashboard.jsx
// Description: Specialized Dashboard for Subject Teachers featuring calendar schedule selector, pending grading, and daily schedule details.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-10-25
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { getTeacherSubjectInfo } from '../../utils/teacherSubjectHelper';
import { teacherApi } from '../../services/api';
import TeacherScheduleCalendarCard from '../../components/teacher/TeacherScheduleCalendarCard';
import PendingGradingCard from '../../components/teacher/PendingGradingCard';
import RecentSubmissionsSummaryCard from '../../components/teacher/RecentSubmissionsSummaryCard';
import DailyScheduleDetailCard from '../../components/teacher/DailyScheduleDetailCard';
import './SubjectTeacherDashboard.css';

export default function SubjectTeacherDashboard() {
  const { user } = useAuth();
  const [selectedDay, setSelectedDay] = useState(new Date().getDate()); // Default to today
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadDashboard() {
      try {
        setLoading(true);
        const data = await teacherApi.getDashboard();
        if (isMounted) setDashboardData(data);
      } catch (err) {
        console.error('Failed to load subject teacher dashboard:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadDashboard();
    return () => { isMounted = false; };
  }, []);

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

  // High-UX Loading State: While BE response is loading, render clear loading animation
  if (loading && !dashboardData) {
    return (
      <div className="subject-dashboard-container">
        <div className="dashboard-loading-overlay">
          <div className="dashboard-loading-card">
            <Loader2 className="dashboard-loading-icon" size={38} />
            <h3 className="dashboard-loading-title">Đang đồng bộ dữ liệu giảng dạy...</h3>
            <p className="dashboard-loading-desc">Hệ thống đang tải dữ liệu lịch giảng dạy và bài nộp từ máy chủ.</p>
          </div>
        </div>
      </div>
    );
  }

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
            scheduleItems={dashboardData?.weekly_schedule}
          />

          <div className="subject-dashboard-bottom-row">
            <PendingGradingCard pendingCount={dashboardData?.metrics?.pending_grading_count} />
            <RecentSubmissionsSummaryCard recentSubmissions={dashboardData?.recent_submissions} />
          </div>
        </div>

        {/* Right Column: Daily Schedule Details */}
        <div className="subject-dashboard-right-column">
          <DailyScheduleDetailCard 
            selectedDay={selectedDay} 
            scheduleItems={dashboardData?.weekly_schedule}
          />
        </div>
      </div>
    </div>
  );
}
