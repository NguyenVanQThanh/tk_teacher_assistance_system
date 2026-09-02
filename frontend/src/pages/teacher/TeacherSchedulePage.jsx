// File Name: TeacherSchedulePage.jsx
// Description: Teaching Schedule page with month calendar grid, daily class timelines, notes/reminders, and add schedule modal.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Clock, 
  MapPin, 
  Pin, 
  Calendar as CalendarIcon, 
  Users, 
  BookOpen, 
  CheckCircle2, 
  Sparkles, 
  Filter, 
  X, 
  Trash2,
  AlertCircle
} from 'lucide-react';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import './TeacherSchedulePage.css';

export default function TeacherSchedulePage() {
  // State for filters
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState('all');

  // State for selected calendar day (default: Oct 15, 2023 as shown in image)
  const [currentYear, setCurrentYear] = useState(2023);
  const [currentMonth, setCurrentMonth] = useState(9); // 0-indexed, 9 = October
  const [selectedDay, setSelectedDay] = useState(15);

  // Notes state
  const [notes, setNotes] = useState([
    { id: 1, date: '2023-10-15', text: 'Nhắc học sinh 12A1 nộp bài tập ôn tập Đạo hàm trước 22:00' },
    { id: 2, date: '2023-10-15', text: 'Chuẩn bị đề kiểm tra 15p cho lớp 10A3' }
  ]);
  const [newNoteInput, setNewNoteInput] = useState('');

  // Modal for adding schedule
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // New schedule form state
  const [newScheduleForm, setNewScheduleForm] = useState({
    title: 'Toán nâng cao',
    className: '12A1',
    grade: '12',
    subject: 'math',
    startTime: '07:30',
    endTime: '09:00',
    room: 'Phòng 302',
    type: 'teaching', // 'teaching' | 'ai' | 'meeting'
    date: 15
  });

  // Mock schedule database
  const [scheduleList, setScheduleList] = useState([
    // October 15
    {
      id: 1,
      year: 2023,
      month: 9,
      day: 15,
      title: 'Toán nâng cao',
      className: '12A1',
      grade: '12',
      subject: 'math',
      startTime: '07:30',
      endTime: '09:00',
      room: 'Phòng 302',
      accentColor: '#3B82F6',
      badgeColor: '#F3E8FF',
      badgeTextColor: '#7C3AED',
      type: 'teaching'
    },
    {
      id: 2,
      year: 2023,
      month: 9,
      day: 15,
      title: 'Toán cơ bản',
      className: '10A3',
      grade: '10',
      subject: 'math',
      startTime: '09:15',
      endTime: '10:45',
      room: 'Phòng 101',
      accentColor: '#EC4899',
      badgeColor: '#FCE7F3',
      badgeTextColor: '#DB2777',
      type: 'teaching'
    },
    {
      id: 3,
      year: 2023,
      month: 9,
      day: 15,
      title: 'Luyện tập AI',
      className: '11B2',
      grade: '11',
      subject: 'math',
      startTime: '14:00',
      endTime: '15:30',
      room: 'Phòng 405',
      accentColor: '#6366F1',
      badgeColor: '#EDE9FE',
      badgeTextColor: '#6D28D9',
      type: 'ai'
    },
    // October 3
    {
      id: 4,
      year: 2023,
      month: 9,
      day: 3,
      title: 'Hình học không gian',
      className: '11A1',
      grade: '11',
      subject: 'math',
      startTime: '08:00',
      endTime: '09:30',
      room: 'Phòng 204',
      accentColor: '#3B82F6',
      badgeColor: '#EFF6FF',
      badgeTextColor: '#2563EB',
      type: 'teaching'
    },
    // October 5
    {
      id: 5,
      year: 2023,
      month: 9,
      day: 5,
      title: 'Họp khoa Toán - Tin',
      className: 'Tổ bộ môn',
      grade: 'all',
      subject: 'math',
      startTime: '14:00',
      endTime: '16:00',
      room: 'Phòng Hội đồng',
      accentColor: '#7C3AED',
      badgeColor: '#F5F3FF',
      badgeTextColor: '#7C3AED',
      type: 'meeting',
      isDepartmentMeeting: true
    },
    // October 19
    {
      id: 6,
      year: 2023,
      month: 9,
      day: 19,
      title: 'Kiểm tra 1 tiết Đại số',
      className: '10A1',
      grade: '10',
      subject: 'math',
      startTime: '07:30',
      endTime: '08:15',
      room: 'Phòng 102',
      accentColor: '#EF4444',
      badgeColor: '#FEE2E2',
      badgeTextColor: '#DC2626',
      type: 'teaching',
      hasAlertDot: true
    }
  ]);

  const monthNames = [
    'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
    'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
  ];

  // Calendar matrix calculation for current Month
  const calendarCells = useMemo(() => {
    // Days in October 2023: 31 days. Oct 1 is Sunday (CN).
    // In Vietnam standard (T2, T3, T4, T5, T6, T7, CN):
    // T2=1, T3=2, T4=3, T5=4, T6=5, T7=6, CN=7 (0 in JS Date)
    
    // For October 2023:
    // Sep 25, 26, 27, 28, 29, 30 are padding from Sep
    // Oct 1 to Oct 31
    // Nov 1, 2, 3, 4, 5 padding
    const firstDay = new Date(currentYear, currentMonth, 1).getDay(); // 0 is Sun
    const shift = firstDay === 0 ? 6 : firstDay - 1; // 6 padding days before Oct 1

    const daysInCurrentMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const daysInPrevMonth = new Date(currentYear, currentMonth, 0).getDate();

    const cells = [];

    // Prev month padding
    for (let i = shift - 1; i >= 0; i--) {
      cells.push({
        day: daysInPrevMonth - i,
        isCurrentMonth: false,
        month: currentMonth - 1,
        year: currentYear
      });
    }

    // Current month days
    for (let d = 1; d <= daysInCurrentMonth; d++) {
      cells.push({
        day: d,
        isCurrentMonth: true,
        month: currentMonth,
        year: currentYear
      });
    }

    // Next month padding (make standard 35 or 42 cells)
    const remaining = 35 - cells.length > 0 ? 35 - cells.length : (42 - cells.length > 0 ? 42 - cells.length : 0);
    for (let n = 1; n <= remaining; n++) {
      cells.push({
        day: n,
        isCurrentMonth: false,
        month: currentMonth + 1,
        year: currentYear
      });
    }

    return cells;
  }, [currentYear, currentMonth]);

  // Navigate months
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
    setCurrentYear(2023);
    setCurrentMonth(9);
    setSelectedDay(15);
  };

  // Filtered daily schedules for selected day
  const dailySchedules = useMemo(() => {
    return scheduleList.filter(item => {
      if (item.year !== currentYear || item.month !== currentMonth || item.day !== selectedDay) {
        return false;
      }
      if (selectedGrade !== 'all' && item.grade !== selectedGrade && item.grade !== 'all') {
        return false;
      }
      if (selectedSubject !== 'all' && item.subject !== selectedSubject) {
        return false;
      }
      return true;
    });
  }, [scheduleList, currentYear, currentMonth, selectedDay, selectedGrade, selectedSubject]);

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
    const newEntry = {
      id: Date.now(),
      year: currentYear,
      month: currentMonth,
      day: parseInt(newScheduleForm.date) || selectedDay,
      title: newScheduleForm.title,
      className: classNameDisplay,
      grade: newScheduleForm.grade || 'all',
      subject: newScheduleForm.subject || 'all',
      startTime: newScheduleForm.startTime,
      endTime: newScheduleForm.endTime,
      room: '',
      accentColor: newScheduleForm.type === 'ai' ? '#6366F1' : (newScheduleForm.type === 'meeting' ? '#7C3AED' : '#3B82F6'),
      badgeColor: newScheduleForm.type === 'ai' ? '#EDE9FE' : (newScheduleForm.type === 'meeting' ? '#F5F3FF' : '#EFF6FF'),
      badgeTextColor: newScheduleForm.type === 'ai' ? '#6D28D9' : (newScheduleForm.type === 'meeting' ? '#7C3AED' : '#2563EB'),
      type: newScheduleForm.type
    };

    setScheduleList(prev => [...prev, newEntry]);
    setSelectedDay(newEntry.day);
    setIsAddModalOpen(false);
    const targetLabel = classNameDisplay ? `cho lớp ${classNameDisplay}` : '';
    setToastMessage(`Đã thêm lịch "${newEntry.title}" ${targetLabel}!`);
    setTimeout(() => setToastMessage(null), 3500);
  };

  return (
    <div className="teacher-schedule-layout">
      {/* Sidebar navigation */}
      <TeacherSidebar activeNav="schedule" />

      {/* Main Content Area */}
      <div className="teacher-schedule-main">
        <Header />

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

          {/* Filter Bar & Add Schedule Action */}
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

              {/* Filter Subject */}
              <div className="custom-select-wrapper">
                <select 
                  value={selectedSubject} 
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  className="filter-select-input"
                >
                  <option value="all">Tất cả môn học</option>
                  <option value="math">Toán học</option>
                  <option value="physics">Vật lý</option>
                  <option value="chemistry">Hóa học</option>
                  <option value="literature">Ngữ văn</option>
                  <option value="english">Tiếng Anh</option>
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

              {/* Days Grid */}
              <div className="calendar-month-days-grid">
                {calendarCells.map((cell, idx) => {
                  const isWeekend = (idx % 7 === 5) || (idx % 7 === 6);
                  const isSelected = cell.isCurrentMonth && cell.day === selectedDay;

                  // Find events for this cell
                  const cellEvents = scheduleList.filter(
                    s => s.year === cell.year && s.month === cell.month && s.day === cell.day
                  );

                  const isDay3 = cell.isCurrentMonth && cell.day === 3;
                  const isDay5 = cell.isCurrentMonth && cell.day === 5;
                  const isDay15 = cell.isCurrentMonth && cell.day === 15;
                  const isDay19 = cell.isCurrentMonth && cell.day === 19;

                  return (
                    <div 
                      key={idx}
                      className={`calendar-day-cell ${!cell.isCurrentMonth ? 'other-month' : ''} ${isWeekend ? 'weekend-cell' : ''} ${isSelected ? 'selected-day-cell' : ''}`}
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

                      {/* Day 3 blue dot */}
                      {isDay3 && (
                        <div className="day-dot-indicator dot-blue" />
                      )}

                      {/* Day 5: Họp khoa badge */}
                      {isDay5 && (
                        <div className="day-pill-event-badge purple">
                          Họp khoa
                        </div>
                      )}

                      {/* Day 15: 2 Schedule Bars (as in screenshot) */}
                      {isDay15 && (
                        <div className="day-event-bars-stack">
                          <div className="event-bar bar-purple" />
                          <div className="event-bar bar-blue" />
                        </div>
                      )}

                      {/* Day 19 red dot */}
                      {isDay19 && (
                        <div className="day-dot-indicator dot-red" />
                      )}

                      {/* Additional dynamic event badges if created */}
                      {cell.isCurrentMonth && !isDay3 && !isDay5 && !isDay15 && !isDay19 && cellEvents.length > 0 && (
                        <div className="day-event-bars-stack">
                          {cellEvents.slice(0, 2).map((ev, evIdx) => (
                            <div 
                              key={evIdx} 
                              className="event-bar" 
                              style={{ backgroundColor: ev.accentColor }} 
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
                    {selectedDay === 15 ? 'Lịch dạy hôm nay' : `Lịch dạy ngày ${selectedDay}`}
                  </h3>
                  <span className="date-badge-pill">
                    {selectedDay} Thg {currentMonth + 1}
                  </span>
                </div>

                <div className="daily-schedule-items-list">
                  {dailySchedules.length > 0 ? (
                    dailySchedules.map((item) => (
                      <div 
                        key={item.id}
                        className="schedule-item-card"
                        style={{ borderLeftColor: item.accentColor }}
                      >
                        <div className="item-top-row">
                          <h4 className="item-title">{item.title}</h4>
                          {item.className && (
                            <span 
                              className="item-class-badge"
                              style={{ 
                                backgroundColor: item.badgeColor, 
                                color: item.badgeTextColor 
                              }}
                            >
                              {item.className}
                            </span>
                          )}
                        </div>

                        <div className="item-details-row">
                          <div className="item-meta-info">
                            <Clock size={13} className="meta-icon" />
                            <span>{item.startTime} - {item.endTime}</span>
                          </div>
                          {item.room && (
                            <div className="item-meta-info">
                              <MapPin size={13} className="meta-icon" />
                              <span>{item.room}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))
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
                        + Thêm lịch cho ngày {selectedDay}
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Notes & Reminders Card */}
              <div className="notes-reminders-card">
                <div className="notes-header">
                  <Pin size={16} className="text-purple-accent" />
                  <h3 className="notes-title">Ghi chú & Nhắc nhở</h3>
                </div>

                <form onSubmit={handleAddNote} className="add-note-form">
                  <input
                    type="text"
                    value={newNoteInput}
                    onChange={(e) => setNewNoteInput(e.target.value)}
                    placeholder="Thêm ghi chú cho ngày hôm nay..."
                    className="note-text-input"
                  />
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
      </div>

      {/* Add Schedule Modal */}
      {isAddModalOpen && (
        <div className="add-schedule-modal-overlay" onClick={() => setIsAddModalOpen(false)}>
          <div className="add-schedule-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-top-bar">
              <div className="modal-title-group">
                <CalendarIcon size={20} className="text-purple" />
                <h3 className="modal-heading">Thêm lịch giảng dạy mới</h3>
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
                <label className="field-label">Tên môn học / Tiết dạy</label>
                <input 
                  type="text" 
                  required
                  value={newScheduleForm.title}
                  onChange={(e) => setNewScheduleForm({ ...newScheduleForm, title: e.target.value })}
                  className="form-input-text"
                  placeholder="Ví dụ: Toán nâng cao, Luyện tập AI..."
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
                    placeholder="Ví dụ: 12A1, 10A3 hoặc để trống..."
                  />
                </div>

                <div className="form-field-group">
                  <label className="field-label">Loại lịch</label>
                  <select 
                    value={newScheduleForm.type}
                    onChange={(e) => setNewScheduleForm({ ...newScheduleForm, type: e.target.value })}
                    className="form-input-text"
                  >
                    <option value="teaching">Giảng dạy chính khóa</option>
                    <option value="ai">Luyện tập AI</option>
                    <option value="meeting">Họp khoa / Chuyên môn</option>
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
