// File Name: TeacherDashboard.jsx
// Description: Main Teacher Dashboard module body assembling welcome banner, metrics, radar analytics, submissions, and schedule.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-02
// Updated By: Tam Khang

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LearningQualityCard from '../../components/teacher/LearningQualityCard';
import RecentSubmissionsTable from '../../components/teacher/RecentSubmissionsTable';
import TeachingScheduleCard from '../../components/teacher/TeachingScheduleCard';
import CreateExerciseModal from '../../components/exercises/CreateExerciseModal';
import { ClipboardList, BookOpen } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './TeacherDashboard.css';

export default function TeacherDashboard() {
  const { user } = useAuth();
  const [isCreateExerciseOpen, setIsCreateExerciseOpen] = useState(false);
  const navigate = useNavigate();

  const greetingName = user?.full_name ? `Thầy/Cô ${user.full_name}` : 'Thầy Nguyễn';

  return (
    <div className="dashboard-main-content">
      {/* Welcome and Metric Summary Cards */}
      <div className="dashboard-hero-row">
        <div className="welcome-banner">
          <h1 className="welcome-title">
            Xin chào, {greetingName}! <span className="wave-emoji">👋</span>
          </h1>
          <p className="welcome-subtitle">
            Dưới đây là tổng quan về hoạt động giảng dạy của thầy hôm nay.
          </p>
        </div>

        <div className="summary-metrics-group">
          {/* Metric 1: Bài tập chờ chấm */}
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">BÀI TẬP CHỜ CHẤM</span>
              <span className="metric-value">45</span>
            </div>
            <div className="metric-icon-box red-box">
              <ClipboardList size={22} className="icon-red" />
            </div>
          </div>

          {/* Metric 2: Lớp học hôm nay */}
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">LỚP HỌC HÔM NAY</span>
              <span className="metric-value">3</span>
            </div>
            <div className="metric-icon-box blue-box">
              <BookOpen size={22} className="icon-blue" />
            </div>
          </div>
        </div>
      </div>

      {/* Grid Layout: Left (Analytics + Submissions) vs Right (Schedule) */}
      <div className="dashboard-grid">
        <div className="grid-left-col">
          {/* 1. Radar Chart Analytics Card */}
          <LearningQualityCard />

          {/* 2. Recent Submissions Table Card */}
          <RecentSubmissionsTable />
        </div>

        <div className="grid-right-col">
          {/* 3. Teaching Schedule Card */}
          <TeachingScheduleCard />
        </div>
      </div>

      {/* Create Exercise Modal */}
      <CreateExerciseModal
        isOpen={isCreateExerciseOpen}
        onClose={() => setIsCreateExerciseOpen(false)}
        onCreateSuccess={(newEx) => {
          alert(`Đã tạo thành công bài tập: ${newEx.title}`);
          navigate('/teacher/exercises');
        }}
      />
    </div>
  );
}
