// File Name: StudentScheduleCard.jsx
// Description: Student monthly schedule calendar card widget dynamically synchronized with real dates, interactive month navigation, and assignment deadline indicators.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-10-11
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import './StudentScheduleCard.css';

export default function StudentScheduleCard({ 
  selectedDate: controlledDate,
  onSelectDate,
  selectedDay: controlledDay, 
  onSelectDay,
  isActive = false,
  onClickCard,
  assignments = []
}) {
  const today = useMemo(() => new Date(), []);

  // Standardize the currently selected date: { day, month, year }
  const selectedDate = useMemo(() => {
    if (controlledDate && controlledDate.day) {
      return {
        day: controlledDate.day,
        month: controlledDate.month || (today.getMonth() + 1),
        year: controlledDate.year || today.getFullYear()
      };
    }
    if (controlledDay !== undefined) {
      return {
        day: controlledDay,
        month: today.getMonth() + 1,
        year: today.getFullYear()
      };
    }
    return {
      day: today.getDate(),
      month: today.getMonth() + 1,
      year: today.getFullYear()
    };
  }, [controlledDate, controlledDay, today]);

  // Calendar view navigation state (viewing month and year)
  const [viewMonth, setViewMonth] = useState(selectedDate.month);
  const [viewYear, setViewYear] = useState(selectedDate.year);

  // Synchronize viewing month/year whenever the active date changes externally
  useEffect(() => {
    if (selectedDate.month && selectedDate.year) {
      setViewMonth(selectedDate.month);
      setViewYear(selectedDate.year);
    }
  }, [selectedDate.month, selectedDate.year]);

  const handlePrevMonth = (e) => {
    e.stopPropagation();
    if (viewMonth === 1) {
      setViewMonth(12);
      setViewYear(prev => prev - 1);
    } else {
      setViewMonth(prev => prev - 1);
    }
  };

  const handleNextMonth = (e) => {
    e.stopPropagation();
    if (viewMonth === 12) {
      setViewMonth(1);
      setViewYear(prev => prev + 1);
    } else {
      setViewMonth(prev => prev + 1);
    }
  };

  const handleSelectDay = (item) => {
    const newDate = {
      day: item.day,
      month: item.month,
      year: item.year
    };
    if (item.month !== viewMonth) {
      setViewMonth(item.month);
      setViewYear(item.year);
    }
    if (onSelectDate) {
      onSelectDate(newDate);
    } else if (onSelectDay) {
      onSelectDay(item.day);
    }
    if (onClickCard) onClickCard();
  };

  const handleCardClick = () => {
    if (onClickCard) onClickCard();
  };

  const weekdays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

  // Map assignments deadlines to dates
  const assignmentDateKeys = useMemo(() => {
    const set = new Set();
    if (!assignments || !Array.isArray(assignments)) return set;
    assignments.forEach(a => {
      if (a.due_at) {
        const d = new Date(a.due_at);
        set.add(`${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`);
      }
    });
    return set;
  }, [assignments]);

  // Dynamically compute calendar days for viewMonth and viewYear
  const calendarCells = useMemo(() => {
    const cells = [];
    // 0: Sunday, 1: Monday, ..., 6: Saturday
    const firstDayOfWeek = new Date(viewYear, viewMonth - 1, 1).getDay();
    // Monday as 0, Sunday as 6
    const startOffset = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;

    const prevMonth = viewMonth === 1 ? 12 : viewMonth - 1;
    const prevYear = viewMonth === 1 ? viewYear - 1 : viewYear;
    const prevMonthDaysCount = new Date(viewYear, viewMonth - 1, 0).getDate();

    // Previous month padding days
    for (let i = startOffset - 1; i >= 0; i--) {
      cells.push({
        day: prevMonthDaysCount - i,
        month: prevMonth,
        year: prevYear,
        isMuted: true
      });
    }

    // Current month days
    const currentMonthDaysCount = new Date(viewYear, viewMonth, 0).getDate();
    for (let d = 1; d <= currentMonthDaysCount; d++) {
      cells.push({
        day: d,
        month: viewMonth,
        year: viewYear,
        isMuted: false
      });
    }

    // Next month padding days to complete grid
    const nextMonth = viewMonth === 12 ? 1 : viewMonth + 1;
    const nextYear = viewMonth === 12 ? viewYear + 1 : viewYear;
    const targetCount = cells.length <= 35 ? 35 : 42;
    let nextDay = 1;
    while (cells.length < targetCount) {
      cells.push({
        day: nextDay++,
        month: nextMonth,
        year: nextYear,
        isMuted: true
      });
    }

    return cells;
  }, [viewMonth, viewYear]);

  return (
    <div 
      className={`student-schedule-card ${isActive ? 'is-active-card' : ''}`}
      onClick={handleCardClick}
      title="Nhấn để xem chi tiết Lịch học hôm nay bên phải"
    >
      <div className="schedule-card-header-row">
        <h2 className="schedule-card-title">Lịch trình</h2>
        <div className="schedule-indicator-chip">
          <span>Ngày {selectedDate.day} Thg {selectedDate.month}</span>
        </div>
      </div>

      <div className="schedule-month-nav-row">
        <span className="schedule-month-heading">Tháng {viewMonth}, {viewYear}</span>
        <div className="schedule-nav-arrows">
          <button 
            type="button" 
            className="cal-nav-btn" 
            aria-label="Tháng trước"
            title="Tháng trước"
            onClick={handlePrevMonth}
          >
            <ChevronLeft size={16} />
          </button>
          <button 
            type="button" 
            className="cal-nav-btn" 
            aria-label="Tháng sau"
            title="Tháng sau"
            onClick={handleNextMonth}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div className="schedule-weekdays-row">
        {weekdays.map(wd => (
          <span key={wd} className="schedule-weekday-label">{wd}</span>
        ))}
      </div>

      <div className="schedule-days-grid">
        {calendarCells.map((item, idx) => {
          const isSelected = !item.isMuted &&
            item.day === selectedDate.day &&
            item.month === selectedDate.month &&
            item.year === selectedDate.year;

          const isToday = !item.isMuted &&
            item.day === today.getDate() &&
            item.month === (today.getMonth() + 1) &&
            item.year === today.getFullYear();

          const hasAssignment = assignmentDateKeys.has(`${item.year}-${item.month}-${item.day}`);

          return (
            <div
              key={idx}
              className={`schedule-day-cell ${item.isMuted ? 'muted' : ''} ${isSelected ? 'active' : ''} ${isToday && !isSelected ? 'is-today' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                handleSelectDay(item);
              }}
              title={isToday ? 'Hôm nay' : `Ngày ${item.day}/${item.month}/${item.year}`}
            >
              <span>{item.day}</span>
              {hasAssignment && !isSelected && (
                <span className="cal-assignment-dot" title="Có bài tập đến hạn" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
