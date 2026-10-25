// File Name: DailyScheduleDetailCard.jsx
// Description: Right sidebar details card showing detailed schedule for the selected date with period info.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React from 'react';
import { Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getTeacherSubjectInfo } from '../../utils/teacherSubjectHelper';
import './DailyScheduleDetailCard.css';

export default function DailyScheduleDetailCard({ selectedDay = 5 }) {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Determine teacher's single subject specialization
  const teacherSubject = getTeacherSubjectInfo(user).subjectName;

  // Day schedules mapped by date or fallback to default
  const scheduleData = {
    5: {
      dayTitle: 'Thứ 5, Ngày 5/10',
      classes: [
        {
          id: 'cls-1',
          title: `${teacherSubject} 10A1`,
          time: '07:30 - 09:00',
          period: 'Tiết 2 - 3',
          dotColor: '#3B82F6',
          timeBadgeVariant: 'blue',
        },
        {
          id: 'cls-2',
          title: `${teacherSubject} 11B2`,
          time: '10:15 - 11:00',
          period: 'Tiết 5',
          dotColor: '#7C3AED',
          timeBadgeVariant: 'purple',
        },
        {
          id: 'cls-3',
          title: `Bồi dưỡng Đội tuyển ${teacherSubject}`,
          time: '14:00 - 16:30',
          period: 'Tiết 7 - 9',
          dotColor: '#7C3AED',
          timeBadgeVariant: 'purple',
        },
      ],
    },
    2: {
      dayTitle: 'Thứ 2, Ngày 2/10',
      classes: [
        {
          id: 'cls-2-1',
          title: `${teacherSubject} 10A2`,
          time: '07:30 - 09:00',
          period: 'Tiết 1 - 2',
          dotColor: '#3B82F6',
          timeBadgeVariant: 'blue',
        },
        {
          id: 'cls-2-2',
          title: `${teacherSubject} 12A1`,
          time: '09:15 - 10:45',
          period: 'Tiết 3 - 4',
          dotColor: '#7C3AED',
          timeBadgeVariant: 'purple',
        },
      ],
    },
    4: {
      dayTitle: 'Thứ 4, Ngày 4/10',
      classes: [
        {
          id: 'cls-4-1',
          title: `${teacherSubject} 11B1`,
          time: '08:15 - 09:45',
          period: 'Tiết 2 - 3',
          dotColor: '#3B82F6',
          timeBadgeVariant: 'blue',
        },
        {
          id: 'cls-4-2',
          title: `Thực hành ${teacherSubject} 10A1`,
          time: '14:00 - 16:30',
          period: 'Tiết 7 - 9',
          dotColor: '#7C3AED',
          timeBadgeVariant: 'purple',
        },
      ],
    },
    6: {
      dayTitle: 'Thứ 6, Ngày 6/10',
      classes: [
        {
          id: 'cls-6-1',
          title: `${teacherSubject} 10A1`,
          time: '07:30 - 09:00',
          period: 'Tiết 1 - 2',
          dotColor: '#3B82F6',
          timeBadgeVariant: 'blue',
        },
        {
          id: 'cls-6-2',
          title: 'Họp Tổ Bộ Môn',
          time: '10:15 - 11:30',
          period: 'Tiết 5',
          dotColor: '#7C3AED',
          timeBadgeVariant: 'purple',
        },
      ],
    },
  };

  const currentSchedule = scheduleData[selectedDay] || {
    dayTitle: `Ngày ${selectedDay}/10`,
    classes: [
      {
        id: `cls-def-${selectedDay}`,
        title: `${teacherSubject} 10A1`,
        time: '08:00 - 09:30',
        period: 'Tiết 2 - 3',
        dotColor: '#3B82F6',
        timeBadgeVariant: 'blue',
      },
    ],
  };

  return (
    <div className="daily-schedule-detail-card">
      <div className="detail-panel-top">
        {/* Info Header */}
        <div className="detail-header-badge">
          <Info size={16} className="detail-info-icon" />
          <span className="detail-header-text">Chi tiết</span>
        </div>

        {/* Date & Subtitle */}
        <div className="detail-day-heading">
          <h3 className="detail-day-title">{currentSchedule.dayTitle}</h3>
          <p className="detail-day-subtitle">Lịch trình giảng dạy trong ngày</p>
        </div>

        {/* Class Items Stack */}
        <div className="detail-class-list">
          {currentSchedule.classes.map((cls) => (
            <div key={cls.id} className="detail-class-item">
              <div className="class-item-top">
                <div className="class-name-row">
                  <span 
                    className="class-indicator-dot" 
                    style={{ backgroundColor: cls.dotColor }}
                  />
                  <span className="class-name-text">{cls.title}</span>
                </div>
                <span className={`class-time-pill ${cls.timeBadgeVariant}`}>
                  {cls.time}
                </span>
              </div>

              <div className="class-period-text">
                {cls.period}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Button at Bottom */}
      <button 
        type="button" 
        className="btn-manage-schedule"
        onClick={() => navigate('/teacher/schedule')}
      >
        Quản lý lịch học
      </button>
    </div>
  );
}
