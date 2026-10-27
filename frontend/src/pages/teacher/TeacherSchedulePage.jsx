// File Name: TeacherSchedulePage.jsx
// Description: Examination and Teaching Schedule interface with interactive calendar, urgency color bars, equal-sized grid cells, horizontal urgency legend, and detailed daily timeline.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-27
// Updated By: Tam Khang

import React, { useState, useMemo, useEffect } from 'react';
import { 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Clock, 
  Calendar as CalendarIcon, 
  BookOpen, 
  CheckCircle2, 
  Sparkles, 
  Filter, 
  X, 
  Check,
  AlertCircle,
  Trash2
} from 'lucide-react';
import { teacherApi } from '../../services/api';
import './TeacherSchedulePage.css';

export default function TeacherSchedulePage() {
  const today = useMemo(() => new Date(), []);
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(today.getMonth()); // 0-indexed month
  const [selectedDay, setSelectedDay] = useState(today.getDate());
  const [selectedGrade, setSelectedGrade] = useState('all'); // 'all' | '10' | '11' | '12'
  const [notes, setNotes] = useState([
    { id: 1, text: 'Chuẩn bị đề kiểm tra 15 phút Giải tích 12' },
    { id: 2, text: 'Nộp báo cáo chuyên môn cho Tổ trưởng trước thứ 6' }
  ]);
  const [newNoteInput, setNewNoteInput] = useState('');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // New schedule modal state
  const [newScheduleForm, setNewScheduleForm] = useState({
    title: '',
    className: '',
    grade: '10',
    startTime: '07:30',
    endTime: '09:00',
    urgency: 'teaching', // 'critical' | 'high' | 'teaching'
    date: today.getDate()
  });

  // Urgency configuration dictionary (3 standardized levels)
  const urgencyConfig = {
    critical: { label: 'Khẩn cấp / Kiểm tra', color: '#EF4444', badgeBg: '#FEE2E2', badgeText: '#DC2626' },
    high: { label: 'Ưu tiên cao', color: '#F59E0B', badgeBg: '#FEF3C7', badgeText: '#D97706' },
    teaching: { label: 'Lịch giảng dạy', color: '#3B82F6', badgeBg: '#EFF6FF', badgeText: '#2563EB' }
  };

  // Synced teaching schedule items (Monday to Saturday, no classes on Sunday)
  const [scheduleList, setScheduleList] = useState([

    {
      id: 4,
      year: 2026,
      month: 9,
      day: 26,
      title: 'Toán Cao Cấp - Lớp 12A1 (P.302, Tòa A)',
      className: '12A1',
      grade: '12',
      startTime: '07:30',
      endTime: '09:00',
      urgency: 'teaching',
      accentColor: '#3B82F6',
      badgeColor: '#EFF6FF',
      badgeTextColor: '#2563EB'
    },
    {
      id: 5,
      year: 2026,
      month: 9,
      day: 26,
      title: 'Họp Tổ Bộ Môn (Phòng Hội đồng)',
      className: 'Tổ Toán',
      grade: 'all',
      startTime: '14:00',
      endTime: '15:30',
      urgency: 'high',
      accentColor: '#F59E0B',
      badgeColor: '#FEF3C7',
      badgeTextColor: '#D97706'
    },
    {
      id: 6,
      year: 2026,
      month: 9,
      day: 27,
      title: 'Đại số - Lớp 11B2 (P.204, Tòa B)',
      className: '11B2',
      grade: '11',
      startTime: '09:15',
      endTime: '10:45',
      urgency: 'teaching',
      accentColor: '#3B82F6',
      badgeColor: '#EFF6FF',
      badgeTextColor: '#2563EB'
    },
    {
      id: 7,
      year: 2026,
      month: 9,
      day: 27,
      title: 'Luyện thi TN THPT Toán (P.304, Tòa A)',
      className: '12A2',
      grade: '12',
      startTime: '14:00',
      endTime: '15:30',
      urgency: 'critical',
      accentColor: '#EF4444',
      badgeColor: '#FEE2E2',
      badgeTextColor: '#DC2626'
    },
    {
      id: 8,
      year: 2026,
      month: 9,
      day: 28,
      title: 'Hình học Không gian - Lớp 12A1 (P.302, Tòa A)',
      className: '12A1',
      grade: '12',
      startTime: '07:30',
      endTime: '09:00',
      urgency: 'critical',
      accentColor: '#EF4444',
      badgeColor: '#FEE2E2',
      badgeTextColor: '#DC2626'
    },
    {
      id: 9,
      year: 2026,
      month: 9,
      day: 28,
      title: 'Giải tích nâng cao - Lớp 10A3 (P.105, Tòa C)',
      className: '10A3',
      grade: '10',
      startTime: '10:00',
      endTime: '11:30',
      urgency: 'teaching',
      accentColor: '#3B82F6',
      badgeColor: '#EFF6FF',
      badgeTextColor: '#2563EB'
    },
    {
      id: 10,
      year: 2026,
      month: 9,
      day: 29,
      title: 'Kiểm tra 45p Đại số 11 (P.204, Tòa B)',
      className: '11B2',
      grade: '11',
      startTime: '08:00',
      endTime: '09:30',
      urgency: 'critical',
      accentColor: '#EF4444',
      badgeColor: '#FEE2E2',
      badgeTextColor: '#DC2626'
    },
    {
      id: 11,
      year: 2026,
      month: 9,
      day: 29,
      title: 'Chuyên đề Đạo hàm & Cực trị (P.302, Tòa A)',
      className: '12A1',
      grade: '12',
      startTime: '10:00',
      endTime: '11:30',
      urgency: 'teaching',
      accentColor: '#3B82F6',
      badgeColor: '#EFF6FF',
      badgeTextColor: '#2563EB'
    },
    {
      id: 12,
      year: 2026,
      month: 9,
      day: 30,
      title: 'Sinh hoạt Lớp Chủ nhiệm - 12A1 (P.302, Tòa A)',
      className: '12A1',
      grade: '12',
      startTime: '07:30',
      endTime: '08:15',
      urgency: 'teaching',
      accentColor: '#3B82F6',
      badgeColor: '#EFF6FF',
      badgeTextColor: '#2563EB'
    },
    {
      id: 13,
      year: 2026,
      month: 9,
      day: 30,
      title: 'Ôn tập cuối tuần Toán 12 (P.302, Tòa A)',
      className: '12A1',
      grade: '12',
      startTime: '09:15',
      endTime: '10:45',
      urgency: 'high',
      accentColor: '#F59E0B',
      badgeColor: '#FEF3C7',
      badgeTextColor: '#D97706'
    },
    {
      id: 14,
      year: 2026,
      month: 9,
      day: 31,
      title: 'Thi thử ĐGNL Khối 12 (Hội trường lớn)',
      className: 'Khối 12',
      grade: '12',
      startTime: '08:00',
      endTime: '11:00',
      urgency: 'critical',
      accentColor: '#EF4444',
      badgeColor: '#FEE2E2',
      badgeTextColor: '#DC2626'
    }
  ]);

  useEffect(() => {
    let isMounted = true;
    async function loadSchedule() {
      try {
        const data = await teacherApi.getSchedule();
        if (isMounted && data?.items?.length) {
          const mapped = data.items.map((item, idx) => {
            const urgency = item.urgency || 'teaching';
            const urgencyData = urgencyConfig[urgency] || urgencyConfig.teaching;
            const cls = item.class_name || '';
            const grade = cls.startsWith('12') ? '12' : cls.startsWith('11') ? '11' : cls.startsWith('10') ? '10' : 'all';
            const parsedDay = item.day_number || (item.date_str ? parseInt(item.date_str.split('-')[2], 10) : (item.day_of_week === 8 ? 25 : item.day_of_week + 24));
            const parsedMonth = item.month !== undefined ? item.month : (item.date_str ? parseInt(item.date_str.split('-')[1], 10) - 1 : 9);
            const parsedYear = item.year || (item.date_str ? parseInt(item.date_str.split('-')[0], 10) : 2026);

            return {
              id: item.id || 100 + idx,
              year: parsedYear,
              month: parsedMonth,
              day: parsedDay,
              title: item.room ? `${item.subject_name} (${item.room})` : item.subject_name,
              className: cls,
              grade,
              startTime: item.start_time,
              endTime: item.end_time,
              urgency,
              accentColor: urgencyData.color,
              badgeColor: urgencyData.badgeBg,
              badgeTextColor: urgencyData.badgeText,
            };
          });
          setScheduleList(mapped);
        }
      } catch (err) {
        console.warn('Teacher schedule fetched fallback to defaults:', err);
      }
    }
    loadSchedule();
    return () => { isMounted = false; };
  }, []);

  const monthNames = [
    'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
    'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
  ];

  // Calendar matrix calculation for current Month
  const calendarCells = useMemo(() => {
    const firstDayIndex = new Date(currentYear, currentMonth, 1).getDay();
    const leadingOffset = firstDayIndex === 0 ? 6 : firstDayIndex - 1;
    const daysInCurrentMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const prevMonthDaysCount = new Date(currentYear, currentMonth, 0).getDate();

    const cells = [];

    // 1. Previous month trailing days
    for (let i = leadingOffset - 1; i >= 0; i--) {
      cells.push({
        day: prevMonthDaysCount - i,
        month: currentMonth === 0 ? 11 : currentMonth - 1,
        year: currentMonth === 0 ? currentYear - 1 : currentYear,
        isCurrentMonth: false,
      });
    }

    // 2. Current month days
    for (let d = 1; d <= daysInCurrentMonth; d++) {
      cells.push({
        day: d,
        month: currentMonth,
        year: currentYear,
        isCurrentMonth: true,
      });
    }

    // 3. Next month leading days to complete grid (multiples of 7)
    const totalCells = Math.ceil(cells.length / 7) * 7;
    const remaining = totalCells - cells.length;
    for (let nextDay = 1; nextDay <= remaining; nextDay++) {
      cells.push({
        day: nextDay,
        month: currentMonth === 11 ? 0 : currentMonth + 1,
        year: currentMonth === 11 ? currentYear + 1 : currentYear,
        isCurrentMonth: false,
      });
    }

    return cells;
  }, [currentYear, currentMonth]);

  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(prev => prev - 1);
    } else {
      setCurrentMonth(prev => prev - 1);
    }
  };

  const handleNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(prev => prev + 1);
    } else {
      setCurrentMonth(prev => prev + 1);
    }
  };

  const handleGoToday = () => {
    const now = new Date();
    setCurrentYear(now.getFullYear());
    setCurrentMonth(now.getMonth());
    setSelectedDay(now.getDate());
  };

  const handlePrevDay = () => {
    if (selectedDay > 1) {
      setSelectedDay(prev => prev - 1);
    } else {
      if (currentMonth === 0) {
        setCurrentMonth(11);
        setCurrentYear(prev => prev - 1);
        setSelectedDay(31);
      } else {
        const prevMonthDays = new Date(currentYear, currentMonth, 0).getDate();
        setCurrentMonth(prev => prev - 1);
        setSelectedDay(prevMonthDays);
      }
    }
  };

  const handleNextDay = () => {
    const daysInCurrentMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    if (selectedDay < daysInCurrentMonth) {
      setSelectedDay(prev => prev + 1);
    } else {
      if (currentMonth === 11) {
        setCurrentMonth(0);
        setCurrentYear(prev => prev + 1);
        setSelectedDay(1);
      } else {
        setCurrentMonth(prev => prev + 1);
        setSelectedDay(1);
      }
    }
  };

  const isTodaySelected = useMemo(() => {
    const now = new Date();
    return selectedDay === now.getDate() && currentMonth === now.getMonth() && currentYear === now.getFullYear();
  }, [selectedDay, currentMonth, currentYear]);

  // Filtered daily schedules for selected day
  const dailySchedules = useMemo(() => {
    return scheduleList.filter(item => {
      if (item.year !== currentYear || item.month !== currentMonth || item.day !== selectedDay) {
        return false;
      }
      if (selectedGrade !== 'all' && item.grade !== selectedGrade && item.grade !== 'all') {
        return false;
      }
      return true;
    });
  }, [scheduleList, currentYear, currentMonth, selectedDay, selectedGrade]);

  // Add new note
  const handleAddNote = (e) => {
    e.preventDefault();
    if (!newNoteInput.trim()) return;
    const newNote = {
      id: Date.now(),
      date: `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(selectedDay).padStart(2, '0')}`,
      text: newNoteInput.trim()
    };
    setNotes(prev => [newNote, ...prev]);
    setNewNoteInput('');
    setToastMessage('Đã thêm ghi chú mới thành công!');
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleDeleteNote = (id) => {
    setNotes(prev => prev.filter(n => n.id !== id));
  };

  // Add new schedule handler
  const handleCreateSchedule = (e) => {
    e.preventDefault();
    const classNameDisplay = newScheduleForm.className?.trim() || '';
    const urgencyData = urgencyConfig[newScheduleForm.urgency] || urgencyConfig.teaching;

    const newEntry = {
      id: Date.now(),
      year: currentYear,
      month: currentMonth,
      day: parseInt(newScheduleForm.date) || selectedDay,
      title: newScheduleForm.title,
      className: classNameDisplay,
      grade: newScheduleForm.grade || 'all',
      startTime: newScheduleForm.startTime,
      endTime: newScheduleForm.endTime,
      urgency: newScheduleForm.urgency,
      accentColor: urgencyData.color,
      badgeColor: urgencyData.badgeBg,
      badgeTextColor: urgencyData.badgeText
    };

    setScheduleList(prev => [...prev, newEntry]);
    setSelectedDay(newEntry.day);
    setIsAddModalOpen(false);
    const targetLabel = classNameDisplay ? `cho lớp ${classNameDisplay}` : '';
    setToastMessage(`Đã thêm lịch "${newEntry.title}" ${targetLabel}!`);
    setTimeout(() => setToastMessage(null), 3500);
  };

  return (
    <div className="teacher-schedule-page-wrapper">
      <div className="schedule-content-container">
        {/* Toast Notification */}
        {toastMessage && (
          <div className="schedule-toast-alert">
            <CheckCircle2 size={16} />
            <span>{toastMessage}</span>
          </div>
        )}

        {/* Top Breadcrumb & Page Title */}
        <div className="schedule-page-header">
          <div className="schedule-breadcrumb">
            <span className="crumb-root">Trang chủ</span>
            <span className="crumb-sep">›</span>
            <span className="crumb-current">Lịch giảng dạy</span>
          </div>
          <h1 className="schedule-main-title">Lịch giảng dạy</h1>
        </div>

        {/* Horizontal Urgency Level Legend Bar */}
        <div className="schedule-legend-horizontal-card">
          <span className="legend-main-title">Mức độ ưu tiên / Khẩn cấp:</span>
          <div className="legend-items-horizontal">
            <div className="legend-chip">
              <span className="legend-chip-dot" style={{ backgroundColor: '#EF4444' }} />
              <span className="legend-chip-text">Khẩn cấp (Kiểm tra / Thi)</span>
            </div>
            <div className="legend-chip">
              <span className="legend-chip-dot" style={{ backgroundColor: '#F59E0B' }} />
              <span className="legend-chip-text">Ưu tiên cao (Lưu ý / Ôn tập)</span>
            </div>
            <div className="legend-chip">
              <span className="legend-chip-dot" style={{ backgroundColor: '#3B82F6' }} />
              <span className="legend-chip-text">Lịch giảng dạy</span>
            </div>
          </div>
        </div>

        {/* Filter Bar (Grade only) & Add Schedule Action */}
        <div className="schedule-filter-bar">
          <div className="filter-select-group">
            {/* Filter Grade */}
            <div className="custom-select-wrapper">
              <select 
                value={selectedGrade} 
                onChange={(e) => setSelectedGrade(e.target.value)}
                className="filter-select-input"
              >
                <option value="all">Tất cả khối lớp</option>
                <option value="10">Khối 10</option>
                <option value="11">Khối 11</option>
                <option value="12">Khối 12</option>
              </select>
            </div>
          </div>

          <button 
            type="button" 
            className="btn-add-schedule-primary"
            onClick={() => setIsAddModalOpen(true)}
          >
            <Plus size={18} strokeWidth={2.5} />
            <span>Thêm lịch mới</span>
          </button>
        </div>

        {/* Main 2-Column Schedule Grid */}
        <div className="schedule-grid-layout">
          {/* Left Column: Interactive Month Calendar */}
          <div className="calendar-grid-card">
            {/* Month Header & Controls */}
            <div className="calendar-header-row">
              <div className="month-picker-wrap">
                <span className="month-title-text">
                  {monthNames[currentMonth]}, {currentYear}
                </span>
                <div className="month-nav-arrows">
                  <button 
                    type="button" 
                    className="nav-arrow-btn" 
                    onClick={handlePrevMonth}
                    title="Tháng trước"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <button 
                    type="button" 
                    className="nav-arrow-btn" 
                    onClick={handleNextMonth}
                    title="Tháng sau"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>

              <button 
                type="button" 
                className="btn-today-pill" 
                onClick={handleGoToday}
              >
                Hôm nay
              </button>
            </div>

            {/* Weekday Header */}
            <div className="calendar-weekdays-row">
              <span className="weekday-col">T2</span>
              <span className="weekday-col">T3</span>
              <span className="weekday-col">T4</span>
              <span className="weekday-col">T5</span>
              <span className="weekday-col">T6</span>
              <span className="weekday-col weekend-col">T7</span>
              <span className="weekday-col weekend-col">CN</span>
            </div>

            {/* Days Grid - All cells strictly equal sized */}
            <div className="calendar-month-days-grid">
              {calendarCells.map((cell, idx) => {
                const isWeekend = (idx % 7 === 5) || (idx % 7 === 6);
                const isSelected = cell.isCurrentMonth && cell.day === selectedDay;
                const isTodayCell = cell.isCurrentMonth && cell.day === today.getDate() && cell.month === today.getMonth() && cell.year === today.getFullYear();

                // Find events for this cell
                const cellEvents = scheduleList.filter(
                  s => s.year === cell.year && s.month === cell.month && s.day === cell.day
                );

                return (
                  <div 
                    key={idx}
                    className={`calendar-day-cell ${!cell.isCurrentMonth ? 'other-month' : ''} ${isWeekend ? 'weekend-cell' : ''} ${isSelected ? 'selected-day-cell' : ''} ${isTodayCell ? 'today-cell' : ''}`}
                    onClick={() => {
                      if (cell.isCurrentMonth) {
                        setSelectedDay(cell.day);
                      }
                    }}
                  >
                    {/* Day Number / Active Circle Badge */}
                    <div className="day-header-number">
                      {isSelected ? (
                        <span className="selected-day-badge">{cell.day}</span>
                      ) : (
                        <span className="day-number-text">{cell.day}</span>
                      )}
                    </div>

                    {/* Urgency Color Bars Indicator */}
                    {cell.isCurrentMonth && cellEvents.length > 0 && (
                      <div className="day-urgency-bars-stack">
                        {cellEvents.map((ev, evIdx) => (
                          <div 
                            key={evIdx} 
                            className="day-urgency-bar" 
                            style={{ backgroundColor: ev.accentColor || '#3B82F6' }}
                            title={`${ev.title} (${ev.startTime} - ${ev.endTime})`}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Daily Schedule Details & Notes */}
          <div className="schedule-side-panel">
            {/* Daily Schedule Card */}
            <div className="daily-schedule-card">
              <div className="daily-schedule-header">
                <h3 className="daily-title">
                  {isTodaySelected ? 'Lịch dạy hôm nay' : `Lịch dạy ngày ${selectedDay}`}
                </h3>
                <div className="daily-date-controls">
                  <button
                    type="button"
                    className="day-nav-arrow-btn"
                    onClick={handlePrevDay}
                    title="Ngày trước"
                  >
                    <ChevronLeft size={14} />
                  </button>
                  <span className="date-badge-pill">
                    {selectedDay} Thg {currentMonth + 1}
                  </span>
                  <button
                    type="button"
                    className="day-nav-arrow-btn"
                    onClick={handleNextDay}
                    title="Ngày sau"
                  >
                    <ChevronRight size={14} />
                  </button>
                </div>
              </div>

              <div className="daily-schedule-items-list">
                {dailySchedules.length > 0 ? (
                  dailySchedules.map((item) => {
                    const urgencyInfo = urgencyConfig[item.urgency] || urgencyConfig.teaching;
                    return (
                      <div 
                        key={item.id}
                        className="schedule-item-card"
                        style={{ borderLeftColor: item.accentColor }}
                      >
                        <div className="item-top-row">
                          <h4 className="item-title">{item.title}</h4>
                          <div className="item-badges-group">
                            {item.className && (
                              <span className="item-class-badge">
                                {item.className}
                              </span>
                            )}
                            <span 
                              className="item-urgency-badge"
                              style={{ 
                                backgroundColor: item.badgeColor || urgencyInfo.badgeBg, 
                                color: item.badgeTextColor || urgencyInfo.badgeText 
                              }}
                            >
                              {urgencyInfo.label}
                            </span>
                          </div>
                        </div>

                        <div className="item-details-row">
                          <div className="item-meta-info">
                            <Clock size={13} className="meta-icon" />
                            <span>{item.startTime} - {item.endTime}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="no-schedules-box">
                    <CalendarIcon size={28} className="text-gray-400" />
                    <p className="no-schedule-text">Không có lịch giảng dạy trong ngày này.</p>
                    <button 
                      type="button" 
                      className="btn-quick-add"
                      onClick={() => {
                        setNewScheduleForm(prev => ({ ...prev, date: selectedDay }));
                        setIsAddModalOpen(true);
                      }}
                    >
                      <Plus size={14} />
                      <span>Thêm lịch cho ngày {selectedDay}</span>
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Notes & Reminders Widget */}
            <div className="notes-card-widget">
              <div className="notes-card-header">
                <div className="notes-header-left">
                  <h4 className="notes-heading">Ghi chú & Nhắc nhở</h4>
                  <span className="notes-counter">{notes.length}</span>
                </div>
              </div>

              {/* Add note inline form */}
              <form onSubmit={handleAddNote} className="add-note-inline-form">
                <input 
                  type="text" 
                  value={newNoteInput}
                  onChange={(e) => setNewNoteInput(e.target.value)}
                  placeholder="Thêm ghi chú nhanh..."
                  className="input-note-text"
                />
                <button type="submit" className="btn-add-note-inline" title="Thêm ghi chú">
                  <Plus size={16} />
                </button>
              </form>

              {/* Notes List */}
              <div className="notes-items-list">
                {notes.map((note) => (
                  <div key={note.id} className="single-note-item">
                    <div className="note-bullet" />
                    <span className="note-text">{note.text}</span>
                    <button 
                      type="button" 
                      className="btn-delete-note"
                      onClick={() => handleDeleteNote(note.id)}
                      title="Xóa ghi chú"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Add Schedule Modal */}
      {isAddModalOpen && (
        <div className="add-schedule-modal-overlay" onClick={() => setIsAddModalOpen(false)}>
          <div className="add-schedule-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-top-bar">
              <div className="modal-title-group">
                <CalendarIcon size={20} className="text-purple" />
                <h3 className="modal-heading">Thêm lịch kiểm tra mới</h3>
              </div>
              <button 
                type="button" 
                className="btn-close-modal" 
                onClick={() => setIsAddModalOpen(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateSchedule} className="schedule-form-body">
              <div className="form-field-group">
                <label className="field-label">Tên môn học / Bài kiểm tra</label>
                <input 
                  type="text" 
                  required
                  value={newScheduleForm.title}
                  onChange={(e) => setNewScheduleForm({ ...newScheduleForm, title: e.target.value })}
                  className="form-input-text"
                  placeholder="Ví dụ: Kiểm tra 15p Giải tích, Kiểm tra giữa kì..."
                />
              </div>

              <div className="form-row-2col">
                <div className="form-field-group">
                  <label className="field-label">Lớp học <span className="field-optional-tag">(Tùy chọn)</span></label>
                  <input 
                    type="text" 
                    value={newScheduleForm.className}
                    onChange={(e) => setNewScheduleForm({ ...newScheduleForm, className: e.target.value })}
                    className="form-input-text"
                    placeholder="Ví dụ: 12A1, 10A3..."
                  />
                </div>

                <div className="form-field-group">
                  <label className="field-label">Mức độ ưu tiên / Loại lịch</label>
                  <select 
                    value={newScheduleForm.urgency}
                    onChange={(e) => setNewScheduleForm({ ...newScheduleForm, urgency: e.target.value })}
                    className="form-input-text"
                  >
                    <option value="critical">🔴 Khẩn cấp (Kiểm tra / Thi cử)</option>
                    <option value="high">🟠 Ưu tiên cao (Lưu ý / Ôn tập)</option>
                    <option value="teaching">🔵 Lịch giảng dạy chính khóa</option>
                  </select>
                </div>
              </div>

              <div className="form-row-3col">
                <div className="form-field-group">
                  <label className="field-label">Ngày dạy (Tháng {currentMonth + 1})</label>
                  <input 
                    type="number" 
                    min="1" 
                    max="31"
                    required
                    value={newScheduleForm.date}
                    onChange={(e) => setNewScheduleForm({ ...newScheduleForm, date: e.target.value })}
                    className="form-input-text"
                  />
                </div>

                <div className="form-field-group">
                  <label className="field-label">Giờ bắt đầu</label>
                  <input 
                    type="time" 
                    required
                    value={newScheduleForm.startTime}
                    onChange={(e) => setNewScheduleForm({ ...newScheduleForm, startTime: e.target.value })}
                    className="form-input-text"
                  />
                </div>

                <div className="form-field-group">
                  <label className="field-label">Giờ kết thúc</label>
                  <input 
                    type="time" 
                    required
                    value={newScheduleForm.endTime}
                    onChange={(e) => setNewScheduleForm({ ...newScheduleForm, endTime: e.target.value })}
                    className="form-input-text"
                  />
                </div>
              </div>

              <div className="modal-actions-footer">
                <button 
                  type="button" 
                  className="btn-modal-cancel"
                  onClick={() => setIsAddModalOpen(false)}
                >
                  Hủy
                </button>
                <button 
                  type="submit" 
                  className="btn-modal-submit"
                >
                  <CheckCircle2 size={16} />
                  <span>Lưu lịch dạy</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
