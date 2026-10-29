// File Name: HomeroomTeacherDashboard.jsx
// Description: Specialized Dashboard for Homeroom Teachers (GVCN) featuring top quick stats, learning quality radar chart with qualitative notes, recent submissions table, and weekly teaching schedule.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-10-29
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { 
  ClipboardCheck,
  BookOpen
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherApi, classesApi } from '../../services/api';
import LearningQualityCard from '../../components/teacher/LearningQualityCard';
import RecentSubmissionsTable from '../../components/teacher/RecentSubmissionsTable';
import TeachingScheduleCard from '../../components/teacher/TeachingScheduleCard';
import './TeacherDashboard.css';

/**
 * Calculates current academic school year (e.g., '2026-2027' for October 2026).
 * School years in Vietnam typically begin in August/September.
 */
function getCurrentAcademicYear() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;
  return month >= 8 ? `${year}-${year + 1}` : `${year - 1}-${year}`;
}

export default function HomeroomTeacherDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [classesList, setClassesList] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState(
    localStorage.getItem('selected_homeroom_class_id') || ''
  );

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        setLoading(true);
        const currentYear = getCurrentAcademicYear();

        // 1. Fetch classes to know available homeroom options
        const classesRes = await classesApi.getClasses();
        let activeClassId = localStorage.getItem('selected_homeroom_class_id') || '';

        if (Array.isArray(classesRes) && classesRes.length > 0) {
          // Filter classes where current user is the homeroom teacher
          const userHomeroomClasses = classesRes.filter(c => 
            c.homeroom_teacher_id === user?.user_id || 
            (user?.full_name && c.homeroom_teacher_name?.includes(user?.full_name))
          );
          const availableClasses = userHomeroomClasses.length > 0 ? userHomeroomClasses : classesRes;

          // Deduplicate to ensure at most 1 homeroom class per academic year
          const sortedCandidates = [...availableClasses].sort((a, b) => {
            const yearA = a.school_year || a.academic_year || '';
            const yearB = b.school_year || b.academic_year || '';
            if (yearA === currentYear && yearB !== currentYear) return -1;
            if (yearB === currentYear && yearA !== currentYear) return 1;
            if (yearA !== yearB) return yearB.localeCompare(yearA);
            return (a.class_name || '').localeCompare(b.class_name || '');
          });

          const seenYears = new Set();
          const uniqueYearClasses = [];
          for (const c of sortedCandidates) {
            const yr = c.school_year || c.academic_year || 'unknown';
            if (!seenYears.has(yr)) {
              seenYears.add(yr);
              uniqueYearClasses.push(c);
            }
          }

          const sortedClasses = uniqueYearClasses.length > 0 ? uniqueYearClasses : sortedCandidates;

          if (isMounted) setClassesList(sortedClasses);

          // Find preferred class:
          // Check if activeClassId exists in current list
          let target = activeClassId ? sortedClasses.find(c => c.class_id === activeClassId) : null;
          if (!target || (target.school_year !== currentYear && sortedClasses.some(c => (c.school_year === currentYear || c.academic_year === currentYear)))) {
            const userHomeroom = sortedClasses.find(c => 
              (c.school_year === currentYear || c.academic_year === currentYear)
            );
            target = userHomeroom || sortedClasses[0];
          }

          activeClassId = target.class_id;
          if (isMounted) setSelectedClassId(activeClassId);
          localStorage.setItem('selected_homeroom_class_id', activeClassId);
        }

        // 2. Load dashboard with the selected homeroom class
        const data = await teacherApi.getDashboard(activeClassId ? { class_id: activeClassId } : {});
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

  const handleSelectClass = async (classId) => {
    setSelectedClassId(classId);
    localStorage.setItem('selected_homeroom_class_id', classId);
    try {
      setLoading(true);
      const data = await teacherApi.getDashboard({ class_id: classId });
      setDashboardData(data);
    } catch (err) {
      console.error('Failed to reload dashboard for class:', err);
    } finally {
      setLoading(false);
    }
  };

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
            classesList={classesList}
            selectedClassId={selectedClassId}
            onSelectClass={handleSelectClass}
          />
          <RecentSubmissionsTable submissions={dashboardData?.recent_submissions} />
        </div>

        {/* Right Column: Lịch giảng dạy tuần này */}
        <div className="dashboard-right-column">
          <TeachingScheduleCard scheduleItems={dashboardData?.weekly_schedule} />
        </div>
      </div>
    </div>
  );
}
