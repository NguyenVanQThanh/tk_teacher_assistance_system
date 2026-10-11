// File Name: StudentScheduleDetailCard.jsx
// Description: Student daily study schedule and personal study notes widget synchronized with real date-time, backend weekly schedules, assignment deadlines, and persistent notes.
// Created At: 2026-09-13
// Created By: Tam Khang
// Updated At: 2026-10-11
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Plus, 
  Clock, 
  Trash2,
  Calendar,
  Sparkles,
  BookOpen,
  AlertCircle,
  X,
  Check
} from 'lucide-react';
import './StudentScheduleDetailCard.css';

export default function StudentScheduleDetailCard({ 
  selectedDate, 
  selectedDay, 
  selectedMonth,
  weeklySchedule = [],
  upcomingAssignments = [],
  onAddNewSchedule 
}) {
  const today = useMemo(() => new Date(), []);

  // Compute accurate Date object from selectedDate or selectedDay props
  const dateObj = useMemo(() => {
    if (selectedDate && selectedDate.day) {
      return new Date(
        selectedDate.year || today.getFullYear(),
        (selectedDate.month || (today.getMonth() + 1)) - 1,
        selectedDate.day
      );
    }
    return new Date(today.getFullYear(), today.getMonth(), selectedDay || today.getDate());
  }, [selectedDate, selectedDay, today]);

  const currentDay = dateObj.getDate();
  const currentMonth = dateObj.getMonth() + 1;
  const currentYear = dateObj.getFullYear();
  const dayOfWeekIndex = dateObj.getDay(); // 0: Sunday, 1: Monday, ..., 6: Saturday
  const dayOfWeekNames = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
  const dayOfWeekLabel = dayOfWeekNames[dayOfWeekIndex];

  // Mapping day of week for backend weekly_schedule (2 = Monday, ..., 7 = Saturday, 8 = Sunday)
  const targetDayOfWeek = dayOfWeekIndex === 0 ? 8 : (dayOfWeekIndex + 1);

  // Persistent custom schedule items stored in localStorage
  const [customSchedules, setCustomSchedules] = useState(() => {
    try {
      const saved = localStorage.getItem('student_custom_schedule_items');
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.warn('Error reading custom schedules from localStorage:', e);
    }
    return [];
  });

  // State to control modal for adding new schedule
  const [isAddScheduleModalOpen, setIsAddScheduleModalOpen] = useState(false);
  const [newScheduleTitle, setNewScheduleTitle] = useState('');
  const [newScheduleTime, setNewScheduleTime] = useState('14:00 – 15:30');
  const [newScheduleTag, setNewScheduleTag] = useState('Tự học');

  // Compute daily schedule items combining backend weekly_schedule, assignments due, and custom schedules
  const dailyScheduleItems = useMemo(() => {
    const list = [];

    // 1. Classes from backend weekly_schedule matching current day of week
    const backendMatches = (weeklySchedule || []).filter(
      s => s.day_of_week === targetDayOfWeek || (dayOfWeekIndex === 0 && s.day_of_week === 1)
    );

    backendMatches.forEach((s, idx) => {
      let accent = 'blue';
      let badgeClass = 'badge-blue';
      if (idx === 1) {
        accent = 'orange';
        badgeClass = 'badge-orange';
      } else if (idx >= 2) {
        accent = 'green';
        badgeClass = 'badge-green';
      }

      list.push({
        id: `backend_${s.period}_${s.subject_name}_${idx}`,
        accent,
        title: s.subject_name,
        classTag: s.room || 'Lớp 12A1',
        badgeTag: `Tiết ${s.period}`,
        badgeClass,
        time: `${s.start_time} – ${s.end_time}`
      });
    });

    // 2. Real assignments due on this date from backend upcoming_assignments
    const assignmentsDueToday = (upcomingAssignments || []).filter(a => {
      if (!a.due_at) return false;
      const d = new Date(a.due_at);
      return (
        d.getDate() === currentDay &&
        (d.getMonth() + 1) === currentMonth &&
        d.getFullYear() === currentYear
      );
    });

    assignmentsDueToday.forEach((a) => {
      const d = new Date(a.due_at);
      const timeStr = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
      list.push({
        id: `due_${a.assignment_id}`,
        accent: a.is_overdue ? 'red' : 'orange',
        title: a.title,
        classTag: a.subject_name || 'Bộ môn',
        badgeTag: a.is_overdue ? 'Quá hạn' : 'Hạn chót',
        badgeClass: a.is_overdue ? 'badge-red' : 'badge-orange',
        time: `Trước ${timeStr}`
      });
    });

    // 3. Custom schedules added by the student for this specific day
    const matchingCustom = customSchedules.filter(
      cs => cs.day === currentDay && cs.month === currentMonth && cs.year === currentYear
    );
    matchingCustom.forEach((cs) => {
      list.push({
        id: cs.id,
        accent: cs.accent || 'green',
        title: cs.title,
        classTag: cs.classTag || 'Cá nhân',
        badgeTag: cs.badgeTag || 'Luyện tập AI',
        badgeClass: cs.badgeClass || 'badge-green',
        time: cs.time,
        isCustom: true
      });
    });

    // 4. If no items exist for this day (e.g. Sunday or weekend), provide helpful self-study plan
    if (list.length === 0) {
      if (dayOfWeekIndex === 0 || dayOfWeekIndex === 6) {
        list.push({
          id: 'weekend_self_study',
          accent: 'green',
          title: 'Luyện tập & Rèn luyện AI',
          classTag: 'Tự học',
          badgeTag: 'Tự học cuối tuần',
          badgeClass: 'badge-green',
          time: '08:30 – 10:30'
        });
        list.push({
          id: 'weekend_review',
          accent: 'blue',
          title: `Ôn tập kiến thức ${dayOfWeekLabel}`,
          classTag: 'SmartLMS',
          badgeTag: 'Rèn luyện AI',
          badgeClass: 'badge-blue',
          time: '15:00 – 17:00'
        });
      } else {
        list.push({
          id: 'weekday_default_1',
          accent: 'blue',
          title: 'Toán học 12',
          classTag: '12A1',
          badgeTag: 'Tiết 1 – 2',
          badgeClass: 'badge-blue',
          time: '07:30 – 09:00'
        });
        list.push({
          id: 'weekday_default_2',
          accent: 'orange',
          title: 'Hóa học 12',
          classTag: '12A1',
          badgeTag: 'Ưu tiên cao',
          badgeClass: 'badge-orange',
          time: '09:15 – 10:45'
        });
        list.push({
          id: 'weekday_default_3',
          accent: 'green',
          title: 'Luyện tập AI',
          classTag: 'Tự học',
          badgeTag: 'Luyện tập AI',
          badgeClass: 'badge-green',
          time: '14:00 – 15:30'
        });
      }
    }

    return list;
  }, [
    weeklySchedule,
    upcomingAssignments,
    targetDayOfWeek,
    dayOfWeekIndex,
    currentDay,
    currentMonth,
    currentYear,
    dayOfWeekLabel,
    customSchedules
  ]);

  // Handle saving new custom schedule item
  const handleSaveNewSchedule = (e) => {
    e.preventDefault();
    if (!newScheduleTitle.trim()) return;

    const newSchedule = {
      id: `custom_${Date.now()}`,
      day: currentDay,
      month: currentMonth,
      year: currentYear,
      title: newScheduleTitle.trim(),
      time: newScheduleTime.trim() || '14:00 – 15:30',
      classTag: 'Tự học',
      badgeTag: newScheduleTag || 'Cá nhân',
      badgeClass: 'badge-green',
      accent: 'green'
    };

    const updated = [...customSchedules, newSchedule];
    setCustomSchedules(updated);
    try {
      localStorage.setItem('student_custom_schedule_items', JSON.stringify(updated));
    } catch (err) {
      console.warn('Error persisting custom schedule:', err);
    }

    setNewScheduleTitle('');
    setIsAddScheduleModalOpen(false);
  };

  // Persistent notes management with localStorage
  const [notes, setNotes] = useState(() => {
    try {
      const saved = localStorage.getItem('student_personal_study_notes');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.warn('Error reading notes from localStorage:', e);
    }
    // Default curriculum-synchronized notes
    return [
      { id: 1, text: 'Nộp bài tập ôn tập Đạo hàm môn Toán trước 22:00 hôm nay' },
      { id: 2, text: 'Chuẩn bị bài 15p Hóa học chuyên đề Este & Lipit' },
      { id: 3, text: 'Luyện nghe & phát âm Tiếng Anh Unit 3 trên ứng dụng' }
    ];
  });

  const [newNoteText, setNewNoteText] = useState('');

  // Add new note with immediate persistence
  const handleAddNote = (e) => {
    e.preventDefault();
    const clean = newNoteText.trim();
    if (!clean) return;

    const newNote = {
      id: Date.now(),
      text: clean,
      createdAt: new Date().toISOString()
    };

    const updated = [newNote, ...notes];
    setNotes(updated);
    try {
      localStorage.setItem('student_personal_study_notes', JSON.stringify(updated));
    } catch (err) {
      console.warn('Error saving note:', err);
    }
    setNewNoteText('');
  };

  // Delete note with immediate persistence
  const handleDeleteNote = (id) => {
    const updated = notes.filter(n => n.id !== id);
    setNotes(updated);
    try {
      localStorage.setItem('student_personal_study_notes', JSON.stringify(updated));
    } catch (err) {
      console.warn('Error saving note after delete:', err);
    }
  };

  return (
    <div className="student-schedule-detail-container">
      {/* Card 1: Lịch học hôm nay (Dedicated for Students) */}
      <div className="schedule-today-card">
        <div className="schedule-today-header">
          <h3 className="schedule-today-title">Lịch học hôm nay</h3>
          <span className="schedule-date-badge">
            <Calendar size={13} className="inline-icon" />
            <span>Ngày {currentDay} Thg {currentMonth}</span>
          </span>
        </div>

        {/* Schedule list */}
        <div className="schedule-today-items-list">
          {dailyScheduleItems.map((item) => (
            <div key={item.id} className={`schedule-item-box border-accent-${item.accent}`}>
              <div className="schedule-item-top-row">
                <h4 className="schedule-item-name" title={item.title}>{item.title}</h4>
                <div className="schedule-item-tags">
                  <span className="class-code-tag">{item.classTag}</span>
                  <span className={`status-type-badge ${item.badgeClass}`}>{item.badgeTag}</span>
                </div>
              </div>

              <div className="schedule-item-meta-row">
                <div className="schedule-meta-point">
                  <Clock size={13} className="meta-icon" />
                  <span>{item.time}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Bottom Action Button: Thêm lịch mới */}
        <button 
          type="button" 
          className="btn-bottom-add-schedule"
          onClick={() => {
            if (onAddNewSchedule) {
              onAddNewSchedule();
            } else {
              setIsAddScheduleModalOpen(true);
            }
          }}
        >
          <Plus size={16} strokeWidth={2.5} />
          <span>Thêm lịch mới</span>
        </button>

        {/* Modal / Quick Form to add new schedule item */}
        {isAddScheduleModalOpen && (
          <div className="add-schedule-modal-overlay" onClick={() => setIsAddScheduleModalOpen(false)}>
            <div className="add-schedule-modal-box" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header-row">
                <h4 className="modal-title">Thêm lịch học ngày {currentDay}/{currentMonth}/{currentYear}</h4>
                <button 
                  type="button" 
                  className="btn-close-modal"
                  onClick={() => setIsAddScheduleModalOpen(false)}
                >
                  <X size={16} />
                </button>
              </div>

              <form onSubmit={handleSaveNewSchedule} className="modal-schedule-form">
                <div className="form-group-item">
                  <label>Môn học / Hoạt động:</label>
                  <input
                    type="text"
                    required
                    placeholder="Ví dụ: Ôn tập Toán nâng cao, Luyện đề Lý..."
                    value={newScheduleTitle}
                    onChange={(e) => setNewScheduleTitle(e.target.value)}
                    autoFocus
                  />
                </div>

                <div className="form-group-row">
                  <div className="form-group-item">
                    <label>Khung giờ:</label>
                    <input
                      type="text"
                      placeholder="Ví dụ: 14:00 – 15:30"
                      value={newScheduleTime}
                      onChange={(e) => setNewScheduleTime(e.target.value)}
                    />
                  </div>
                  <div className="form-group-item">
                    <label>Loại lịch:</label>
                    <input
                      type="text"
                      placeholder="Ví dụ: Tự học, Ôn thi..."
                      value={newScheduleTag}
                      onChange={(e) => setNewScheduleTag(e.target.value)}
                    />
                  </div>
                </div>

                <div className="modal-actions-row">
                  <button 
                    type="button" 
                    className="btn-cancel-modal"
                    onClick={() => setIsAddScheduleModalOpen(false)}
                  >
                    Hủy
                  </button>
                  <button 
                    type="submit" 
                    className="btn-submit-modal"
                    disabled={!newScheduleTitle.trim()}
                  >
                    <Check size={14} />
                    <span>Lưu lịch học</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* Card 2: Ghi chú & Nhắc nhở học tập */}
      <div className="schedule-notes-card">
        <div className="schedule-notes-header">
          <div className="notes-header-left">
            <h3 className="schedule-notes-title">Ghi chú & Nhắc nhở</h3>
            <span className="notes-counter-badge">{notes.length}</span>
          </div>
        </div>

        {/* Quick Add Note Input */}
        <form className="quick-add-note-form" onSubmit={handleAddNote}>
          <input
            type="text"
            className="quick-add-note-input"
            placeholder="Thêm ghi chú nhanh..."
            value={newNoteText}
            onChange={(e) => setNewNoteText(e.target.value)}
          />
          <button 
            type="submit" 
            className="btn-submit-quick-note"
            disabled={!newNoteText.trim()}
            title="Thêm ghi chú"
          >
            <Plus size={16} />
          </button>
        </form>

        {/* Notes Items List */}
        <div className="schedule-notes-list">
          {notes.length === 0 ? (
            <div className="empty-notes-hint">
              <span>Chưa có ghi chú nào. Hãy thêm ghi chú hoặc nhắc nhở học tập ở trên!</span>
            </div>
          ) : (
            notes.map((note) => (
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
            ))
          )}
        </div>
      </div>
    </div>
  );
}
