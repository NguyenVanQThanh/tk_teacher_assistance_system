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
  // Khung giờ gồm 3 phần: giờ (1-12), phút (00-59), AM/PM theo múi giờ GMT+7
  const [newScheduleHour, setNewScheduleHour] = useState('');
  const [newScheduleMinute, setNewScheduleMinute] = useState('');
  const [newScheduleAmPm, setNewScheduleAmPm] = useState('AM');
  const [scheduleTimeError, setScheduleTimeError] = useState('');

  // Regex kiểm tra khung nhập giờ: giờ 12h (1-12), phút (00-59)
  const HOUR_REGEX = /^(1[0-2]|[1-9])$/;
  const MINUTE_REGEX = /^[0-5][0-9]$/;

  // Đổi giờ 12h + AM/PM sang giờ 24h
  const to24Hour = (h12, ampm) => {
    if (ampm === 'AM') return h12 === 12 ? 0 : h12;
    return h12 === 12 ? 12 : h12 + 12;
  };

  const hourValid = HOUR_REGEX.test(newScheduleHour);
  const minuteValid = MINUTE_REGEX.test(newScheduleMinute);
  const timeInputsValid = hourValid && minuteValid;

  // Instant tương ứng khung giờ đã chọn theo múi giờ GMT+7
  // (Date.UTC của giờ địa phương rồi trừ 7 giờ để về đúng instant)
  const scheduleInstantGMT7 = useMemo(() => {
    if (!timeInputsValid) return null;
    const h24 = to24Hour(Number(newScheduleHour), newScheduleAmPm);
    return Date.UTC(currentYear, currentMonth - 1, currentDay, h24, Number(newScheduleMinute)) - 7 * 60 * 60 * 1000;
  }, [timeInputsValid, newScheduleHour, newScheduleMinute, newScheduleAmPm, currentYear, currentMonth, currentDay]);

  // Không cho tạo lịch trong quá khứ (so sánh theo giờ GMT+7)
  const isPastSchedule = scheduleInstantGMT7 !== null && scheduleInstantGMT7 <= Date.now();

  // Chỉ cho nhập số: khung giờ tối đa 2 chữ số, khung phút tối đa 2 chữ số
  const handleHourChange = (e) => {
    setNewScheduleHour(e.target.value.replace(/[^0-9]/g, '').slice(0, 2));
    setScheduleTimeError('');
  };

  const handleMinuteChange = (e) => {
    setNewScheduleMinute(e.target.value.replace(/[^0-9]/g, '').slice(0, 2));
    setScheduleTimeError('');
  };

  // Mở modal và gợi ý sẵn khung giờ là giờ kế tiếp theo GMT+7
  const openAddScheduleModal = () => {
    const now = new Date();
    const nowGMT7 = new Date(now.getTime() + (now.getTimezoneOffset() + 7 * 60) * 60000);
    const h24next = (nowGMT7.getHours() + 1) % 24;
    const h12 = h24next % 12 === 0 ? 12 : h24next % 12;
    setNewScheduleHour(String(h12));
    setNewScheduleMinute('00');
    setNewScheduleAmPm(h24next >= 12 ? 'PM' : 'AM');
    setScheduleTimeError('');
    setIsAddScheduleModalOpen(true);
  };

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

    if (!timeInputsValid) {
      setScheduleTimeError('Khung giờ không hợp lệ: nhập giờ 1–12 và phút 00–59.');
      return;
    }

    const hourNum = Number(newScheduleHour);
    const minuteNum = Number(newScheduleMinute);
    const h24 = to24Hour(hourNum, newScheduleAmPm);
    // Chuyển khung giờ GMT+7 thành instant để chặn lịch trong quá khứ
    const instantGMT7 = Date.UTC(currentYear, currentMonth - 1, currentDay, h24, minuteNum) - 7 * 60 * 60 * 1000;
    if (instantGMT7 <= Date.now()) {
      setScheduleTimeError('Không thể tạo lịch trong quá khứ (giờ GMT+7). Vui lòng chọn thời điểm ở tương lai.');
      return;
    }

    const timeLabel = `${hourNum}:${String(minuteNum).padStart(2, '0')} ${newScheduleAmPm}`;

    const newSchedule = {
      id: `custom_${Date.now()}`,
      day: currentDay,
      month: currentMonth,
      year: currentYear,
      title: newScheduleTitle.trim(),
      time: timeLabel,
      classTag: 'Tự học',
      badgeTag: 'Cá nhân',
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
    setNewScheduleHour('');
    setNewScheduleMinute('');
    setNewScheduleAmPm('AM');
    setScheduleTimeError('');
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
              openAddScheduleModal();
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

                <div className="form-group-item">
                  <label>Khung giờ (GMT+7):</label>
                  <div className="time-inputs-row">
                    <input
                      type="text"
                      inputMode="numeric"
                      className={`time-input time-input-hour${hourValid || !newScheduleHour ? '' : ' time-input-invalid'}`}
                      placeholder="Giờ (1–12)"
                      value={newScheduleHour}
                      onChange={handleHourChange}
                    />
                    <span className="time-separator">:</span>
                    <input
                      type="text"
                      inputMode="numeric"
                      className={`time-input time-input-minute${minuteValid || !newScheduleMinute ? '' : ' time-input-invalid'}`}
                      placeholder="Phút (00–59)"
                      value={newScheduleMinute}
                      onChange={handleMinuteChange}
                    />
                    <select
                      className="time-input time-input-ampm"
                      value={newScheduleAmPm}
                      onChange={(e) => {
                        setNewScheduleAmPm(e.target.value);
                        setScheduleTimeError('');
                      }}
                    >
                      <option value="AM">AM</option>
                      <option value="PM">PM</option>
                    </select>
                  </div>
                  {(scheduleTimeError || isPastSchedule) && (
                    <span className="form-error-text">
                      {scheduleTimeError || 'Không thể tạo lịch trong quá khứ (giờ GMT+7). Vui lòng chọn thời điểm ở tương lai.'}
                    </span>
                  )}
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
                    disabled={!newScheduleTitle.trim() || !timeInputsValid || isPastSchedule}
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
