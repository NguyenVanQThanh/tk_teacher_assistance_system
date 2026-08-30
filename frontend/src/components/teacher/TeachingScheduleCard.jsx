// File Name: TeachingScheduleCard.jsx
// Description: Weekly teaching schedule widget with class times and locations.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React from 'react';
import { ChevronLeft, ChevronRight, Clock, MapPin } from 'lucide-react';
import './TeachingScheduleCard.css';

export default function TeachingScheduleCard() {
  const scheduleItems = [
    {
      id: 'sch-1',
      dayLabel: 'THỨ 2',
      dateNumber: '15',
      title: 'Toán Cao Cấp - Lớp 12A1',
      time: '07:30 - 09:00',
      room: 'Phòng 302, Tòa A',
      theme: 'purple',
    },
    {
      id: 'sch-2',
      dayLabel: 'THỨ 2',
      dateNumber: null,
      title: 'Họp Tổ Bộ Môn',
      time: '14:00 - 15:30',
      room: null,
      theme: 'blue',
    },
    {
      id: 'sch-3',
      dayLabel: 'THỨ 3',
      dateNumber: '16',
      title: 'Đại số - Lớp 11B2',
      time: '09:15 - 10:45',
      room: null,
      theme: 'purple',
    },
  ];

  return (
    <div className="teaching-schedule-card">
      <div className="schedule-header">
        <h2 className="schedule-title">Lịch giảng dạy tuần này</h2>
        <div className="schedule-nav-btns">
          <button className="icon-nav-btn" aria-label="Previous week">
            <ChevronLeft size={16} />
          </button>
          <button className="icon-nav-btn" aria-label="Next week">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div className="schedule-list">
        {scheduleItems.map((item) => (
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
        ))}
      </div>

      <button className="btn-view-full-schedule">
        Xem lịch đầy đủ
      </button>
    </div>
  );
}
