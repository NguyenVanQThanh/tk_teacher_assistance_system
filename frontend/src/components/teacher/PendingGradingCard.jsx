// File Name: PendingGradingCard.jsx
// Description: Card component displaying exercises waiting for teacher grading with direct action triggers.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-10-29
// Updated By: Tam Khang

import React, { useMemo } from 'react';
import { Clock, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getTeacherSubjectInfo } from '../../utils/teacherSubjectHelper';
import './PendingGradingCard.css';

export default function PendingGradingCard({ pendingCount, pendingItems: incomingPendingItems }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { shortName } = getTeacherSubjectInfo(user);

  const pendingItems = useMemo(() => {
    if (incomingPendingItems && incomingPendingItems.length > 0) {
      return incomingPendingItems;
    }
    if (!pendingCount || pendingCount === 0) {
      return [];
    }
    return [
      {
        id: 'pg-1',
        count: pendingCount,
        variant: 'danger',
        title: `Bài tập chờ chấm - ${shortName}`,
        deadline: 'Cần giáo viên chấm thủ công',
        link: '/teacher/grading?status=pending_grading',
      },
    ];
  }, [incomingPendingItems, pendingCount, shortName]);

  return (
    <div className="pending-grading-card">
      <div className="pending-card-header">
        <h2 className="pending-card-title">Bài tập chờ chấm</h2>
        <button 
          type="button" 
          className="pending-view-all-btn"
          onClick={() => navigate('/teacher/grading?status=pending_grading')}
        >
          Xem tất cả
        </button>
      </div>

      <div className="pending-items-list">
        {pendingItems.length === 0 ? (
          <div style={{ padding: '24px 12px', textAlign: 'center', color: '#64748B', fontSize: '13px' }}>
            <Clock size={24} style={{ margin: '0 auto 8px', color: '#94A3B8', display: 'block' }} />
            <span>Không có bài tập nào đang chờ chấm.</span>
          </div>
        ) : (
          pendingItems.map((item) => (
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
          ))
        )}
      </div>
    </div>
  );
}
