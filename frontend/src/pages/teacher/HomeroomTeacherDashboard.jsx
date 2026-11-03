// File Name: HomeroomTeacherDashboard.jsx
// Description: Specialized Dashboard for Homeroom Teachers (GVCN) featuring top quick stats, learning quality radar chart with qualitative notes, recent submissions table, and weekly teaching schedule.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-10-29
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { 
  ClipboardCheck,
  BookOpen,
  Loader2
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherApi } from '../../services/api';
import LearningQualityCard from '../../components/teacher/LearningQualityCard';
import RecentSubmissionsTable from '../../components/teacher/RecentSubmissionsTable';
import TeachingScheduleCard from '../../components/teacher/TeachingScheduleCard';
import './TeacherDashboard.css';

export default function HomeroomTeacherDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        setLoading(true);
        // Load consolidated dashboard for current academic year homeroom class
        const data = await teacherApi.getDashboard();
        if (isMounted) setDashboardData(data);
      } catch (err) {
        console.error('Failed to load teacher dashboard:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
    return () => { isMounted = false; };
  }, [user]);

  // Derive dynamic greeting title (e.g. "Thầy Nguyễn" or "Cô Mai")
  const getGreetingData = (fullName) => {
    if (!fullName) return { title: 'Thầy', name: 'Thầy Nguyễn' };
    const isFemale = fullName.includes('Cô') || fullName.includes('Thị') || fullName.includes('Mai') || fullName.includes('Trang');
    const title = isFemale ? 'Cô' : 'Thầy';
    
    let cleanName = fullName.replace(/^(Sample Teacher \(|Thầy |Cô |\))/gi, '').trim();
    const parts = cleanName.split(' ');
    const displayPart = parts[0] || parts[parts.length - 1] || 'Nguyễn';
    return {
      title,
      name: `${title} ${displayPart}`
    };
  };

  const { title: teacherTitle, name: greetingName } = getGreetingData(user?.full_name);

  // High-UX Loading State: While BE is returning response, show loading animation instead of empty/placeholder layout
  if (loading && !dashboardData) {
    return (
      <div className="teacher-dashboard-container">
        <div className="dashboard-loading-overlay">
          <div className="dashboard-loading-card">
            <Loader2 className="dashboard-loading-icon" size={38} />
            <h3 className="dashboard-loading-title">Đang đồng bộ dữ liệu giảng dạy...</h3>
            <p className="dashboard-loading-desc">Hệ thống đang tải số liệu lớp học, chất lượng học tập và lịch giảng dạy từ máy chủ.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="teacher-dashboard-container">
      {/* Top Banner Row: Greeting on Left, 2 Quick Stat Cards on Right */}
      <div className="dashboard-top-banner-row">
        <div className="dashboard-greeting-block">
          <h1 className="dashboard-greeting-title">
            Xin chào, {greetingName}! <span className="greeting-wave">👋</span>
          </h1>
          <p className="dashboard-greeting-subtitle">
            Dưới đây là tổng quan về hoạt động giảng dạy của {teacherTitle.toLowerCase()} hôm nay.
          </p>
        </div>

        <div className="dashboard-quick-stats-row">
          {/* Stat Card 1: BÀI TẬP CHỜ CHẤM */}
          <div 
            className="quick-stat-box accent-red"
            onClick={() => navigate('/teacher/grading?status=pending_grading')}
            title="Xem danh sách bài tập chờ chấm"
          >
            <div className="quick-stat-info">
              <span className="quick-stat-label">BÀI TẬP CHỜ CHẤM</span>
              <span className="quick-stat-value">
                {dashboardData?.metrics?.pending_grading_count ?? '—'}
              </span>
            </div>
            <div className="quick-stat-icon-wrapper bg-red">
              <ClipboardCheck size={20} className="stat-icon-red" />
            </div>
          </div>

          {/* Stat Card 2: LỚP HỌC HÔM NAY */}
          <div 
            className="quick-stat-box"
            onClick={() => navigate('/teacher/schedule')}
            title="Xem lịch giảng dạy hôm nay"
          >
            <div className="quick-stat-info">
              <span className="quick-stat-label">LỚP HỌC HÔM NAY</span>
              <span className="quick-stat-value">
                {dashboardData?.metrics?.today_classes_count ?? '—'}
              </span>
            </div>
            <div className="quick-stat-icon-wrapper bg-blue">
              <BookOpen size={20} className="stat-icon-blue" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Two-Column Content Layout */}
      <div className="dashboard-content-layout">
        {/* Left Column: Chất lượng học tập trung bình (Radar + Nhận xét) + Bài nộp gần đây */}
        <div className="dashboard-left-column">
          <LearningQualityCard 
            learningQuality={dashboardData?.learning_quality} 
          />
          <RecentSubmissionsTable 
            submissions={dashboardData?.recent_submissions} 
            loading={loading}
            onGradeSubmission={(attemptId) => navigate(`/teacher/grading?attempt_id=${attemptId}`)}
          />
        </div>

        {/* Right Column: Lịch giảng dạy tuần này */}
        <div className="dashboard-right-column">
          <TeachingScheduleCard scheduleItems={dashboardData?.weekly_schedule} />
        </div>
      </div>
    </div>
  );
}
