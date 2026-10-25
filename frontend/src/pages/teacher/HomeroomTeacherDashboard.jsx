// File Name: HomeroomTeacherDashboard.jsx
// Description: Specialized Dashboard for Homeroom Teachers (GVCN) featuring top quick stats, learning quality radar chart with qualitative notes, recent submissions table, and weekly teaching schedule.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import { 
  ClipboardCheck,
  BookOpen
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LearningQualityCard from '../../components/teacher/LearningQualityCard';
import RecentSubmissionsTable from '../../components/teacher/RecentSubmissionsTable';
import TeachingScheduleCard from '../../components/teacher/TeachingScheduleCard';
import './TeacherDashboard.css';

export default function HomeroomTeacherDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

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
            onClick={() => navigate('/teacher/grading')}
            title="Xem danh sách bài tập chờ chấm"
          >
            <div className="quick-stat-info">
              <span className="quick-stat-label">BÀI TẬP CHỜ CHẤM</span>
              <span className="quick-stat-value">45</span>
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
              <span className="quick-stat-value">3</span>
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
          <LearningQualityCard />
          <RecentSubmissionsTable />
        </div>

        {/* Right Column: Lịch giảng dạy tuần này */}
        <div className="dashboard-right-column">
          <TeachingScheduleCard />
        </div>
      </div>
    </div>
  );
}
