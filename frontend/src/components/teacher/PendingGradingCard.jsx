// File Name: PendingGradingCard.jsx
// Description: Card component displaying exercises waiting for teacher grading with direct action triggers.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import { Clock, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getTeacherSubjectInfo } from '../../utils/teacherSubjectHelper';
import './PendingGradingCard.css';

export default function PendingGradingCard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { shortName } = getTeacherSubjectInfo(user);

  const pendingItems = [
    {
      id: 'pg-1',
      count: 12,
      variant: 'danger',
      title: `Đề kiểm tra 15p - ${shortName} 10A1`,
      deadline: 'Hạn chót: Hôm qua',
      link: '/teacher/grading',
    },
    {
      id: 'pg-2',
      count: 35,
      variant: 'neutral',
      title: `Bài tập về nhà tuần 4 - ${shortName} 11B2`,
      deadline: 'Hạn chót: Hôm nay, 23:59',
      link: '/teacher/grading',
    },
  ];

  return (
    <div className="pending-grading-card">
      <div className="pending-card-header">
        <h2 className="pending-card-title">Bài tập chờ chấm</h2>
        <button 
          type="button" 
          className="pending-view-all-btn"
          onClick={() => navigate('/teacher/grading')}
        >
          Xem tất cả
        </button>
      </div>

      <div className="pending-items-list">
        {pendingItems.map((item) => (
          <div 
            key={item.id} 
            className="pending-item-row"
            onClick={() => navigate(item.link)}
          >
            <div className={`pending-count-box ${item.variant}`}>
              {item.count}
            </div>

            <div className="pending-info">
              <h4 className="pending-item-title">{item.title}</h4>
              <div className="pending-deadline-row">
                <Clock size={12} className="deadline-icon" />
                <span>{item.deadline}</span>
              </div>
            </div>

            <button 
              type="button" 
              className="pending-action-circle"
              aria-label="Chấm bài tập này"
              onClick={(e) => {
                e.stopPropagation();
                navigate(item.link);
              }}
            >
              <ArrowRight size={15} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
