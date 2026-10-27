// File Name: TeachingScheduleCard.jsx
// Description: Weekly teaching schedule widget with class times and locations.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-10-25
// Updated By: Tam Khang

import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Clock, MapPin } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './TeachingScheduleCard.css';

export default function TeachingScheduleCard({ scheduleItems: incomingScheduleItems }) {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(0);

  // Only render real timetable data from the API (shared with the Teaching Schedule page)
  const scheduleItems = (incomingScheduleItems || []).map(item => ({
    id: item.id,
    dayLabel: item.day_label || item.dayLabel,
    dateNumber: item.date_number ?? item.dateNumber,
    title: item.title,
    time: item.time,
    room: item.room,
    theme: item.theme || 'purple',
  }));

  const pageSize = 4;
  const totalPages = Math.ceil(scheduleItems.length / pageSize) || 1;
  const displayedItems = scheduleItems.slice(currentPage * pageSize, (currentPage + 1) * pageSize);

  return (
    <div className="teaching-schedule-card">
      <div className="schedule-header">
        <h2 className="schedule-title">Lịch giảng dạy tuần này</h2>
        <div className="schedule-nav-btns">
          <button 
            type="button"
            className="icon-nav-btn" 
            aria-label="Previous week"
            onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
            disabled={currentPage === 0}
            style={{ opacity: currentPage === 0 ? 0.4 : 1, cursor: currentPage === 0 ? 'default' : 'pointer' }}
          >
            <ChevronLeft size={16} />
          </button>
          <button 
            type="button"
            className="icon-nav-btn" 
            aria-label="Next week"
            onClick={() => setCurrentPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={currentPage >= totalPages - 1}
            style={{ opacity: currentPage >= totalPages - 1 ? 0.4 : 1, cursor: currentPage >= totalPages - 1 ? 'default' : 'pointer' }}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div className="schedule-list">
        {displayedItems.length > 0 ? (
          displayedItems.map((item) => (
            <div key={item.id} className="schedule-row">
              {/* Left Date indicator */}
              <div className="day-badge-col">
                <span className="day-name">{item.dayLabel}</span>
                {item.dateNumber && (
                  <span className="day-number">{item.dateNumber}</span>
                )}
              </div>

              {/* Right Event details box */}
              <div className={`event-box ${item.theme}`}>
                <h4 className="event-title">{item.title}</h4>
                <div className="event-meta">
                  <span className="meta-item">
                    <Clock size={13} className="meta-icon" />
                    {item.time}
                  </span>
                  {item.room && (
                    <span className="meta-item">
                      <MapPin size={13} className="meta-icon" />
                      {item.room}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-schedule-state" style={{ padding: '24px', textAlign: 'center', color: '#64748B', fontSize: '13px' }}>
            Không có lịch giảng dạy trong tuần này.
          </div>
        )}
      </div>

      <button 
        type="button" 
        className="btn-view-full-schedule"
        onClick={() => navigate('/teacher/schedule')}
      >
        Xem lịch đầy đủ
      </button>
    </div>
  );
}
