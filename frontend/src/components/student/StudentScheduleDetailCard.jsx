// File Name: StudentScheduleDetailCard.jsx
// Description: Student daily study schedule and personal study notes widget matching Image 2 mockup.
// Created At: 2026-09-13
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState } from 'react';
import { 
  Plus, 
  Clock, 
  MapPin, 
  Trash2,
  Calendar,
  Sparkles,
  BookOpen
} from 'lucide-react';
import './StudentScheduleDetailCard.css';

// Rich mock data for student study schedules across different days
const STUDENT_DAILY_SCHEDULES = {
  8: {
    items: [
      {
        id: 1,
        accent: 'blue',
        title: 'Toán nâng cao',
        classTag: '12A1',
        badgeTag: 'Tiết 1 – 2',
        badgeClass: 'badge-blue',
        time: '07:30 – 09:00',
        room: 'Phòng 302'
      },
      {
        id: 2,
        accent: 'orange',
        title: 'Hóa học 12',
        classTag: '12A1',
        badgeTag: 'Ưu tiên cao',
        badgeClass: 'badge-orange',
        time: '09:15 – 10:45',
        room: 'Phòng 101'
      },
      {
        id: 3,
        accent: 'green',
        title: 'Luyện tập AI',
        classTag: 'Tự học',
        badgeTag: 'Luyện tập AI',
        badgeClass: 'badge-green',
        time: '14:00 – 15:30',
        room: 'Phòng 405'
      }
    ],
    notes: [
      { id: 1, text: 'Nộp bài tập ôn tập Đạo hàm môn Toán trước 22:00 hôm nay' },
      { id: 2, text: 'Chuẩn bị bài 15p Hóa học chuyên đề Este & Lipit' },
      { id: 3, text: 'Luyện nghe & phát âm Tiếng Anh Unit 3 trên ứng dụng' }
    ]
  },
  9: {
    items: [
      {
        id: 1,
        accent: 'blue',
        title: 'Vật lý 12',
        classTag: '12A1',
        badgeTag: 'Tiết 1 – 2',
        badgeClass: 'badge-blue',
        time: '07:30 – 09:00',
        room: 'Phòng 204'
      },
      {
        id: 2,
        accent: 'green',
        title: 'Tiếng Anh nâng cao',
        classTag: '12A1',
        badgeTag: 'Tiết 3 – 4',
        badgeClass: 'badge-green',
        time: '09:15 – 10:45',
        room: 'Phòng 305'
      },
      {
        id: 3,
        accent: 'orange',
        title: 'Sinh hoạt CLB Khoa học',
        classTag: '12A1',
        badgeTag: 'Hoạt động ngoại khóa',
        badgeClass: 'badge-orange',
        time: '14:30 – 16:00',
        room: 'Hội trường A'
      }
    ],
    notes: [
      { id: 1, text: 'Tham gia buổi sinh hoạt CLB Khoa học lúc 14:30' },
      { id: 2, text: 'Hoàn thành bài tập trắc nghiệm Vật lý chương Dao động cơ' }
    ]
  },
  10: {
    items: [
      {
        id: 1,
        accent: 'green',
        title: 'Tự học & Luyện thi AI',
        classTag: 'Cá nhân',
        badgeTag: 'Tự học cuối tuần',
        badgeClass: 'badge-green',
        time: '08:30 – 10:30',
        room: 'Phòng học online'
      },
      {
        id: 2,
        accent: 'blue',
        title: 'Ôn thi thử THPT: Toán – Lý – Hóa',
        classTag: 'SmartLMS',
        badgeTag: 'Rèn luyện AI',
        badgeClass: 'badge-blue',
        time: '15:00 – 17:00',
        room: 'Hệ thống SmartLMS'
      }
    ],
    notes: [
      { id: 1, text: 'Làm đề thi thử tạo sinh AI môn Toán đạt mục tiêu 8.5+' },
      { id: 2, text: 'Nghỉ ngơi và sắp xếp tài liệu học tập cho tuần mới' }
    ]
  },
  15: {
    items: [
      {
        id: 1,
        accent: 'blue',
        title: 'Toán nâng cao',
        classTag: '12A1',
        badgeTag: 'Tiết 1 – 2',
        badgeClass: 'badge-blue',
        time: '07:30 – 09:00',
        room: 'Phòng 302'
      },
      {
        id: 2,
        accent: 'orange',
        title: 'Tin học lập trình',
        classTag: '12A1',
        badgeTag: 'Ưu tiên cao',
        badgeClass: 'badge-orange',
        time: '09:15 – 10:45',
        room: 'Phòng máy 102'
      },
      {
        id: 3,
        accent: 'green',
        title: 'Luyện tập AI',
        classTag: '12A1',
        badgeTag: 'Luyện tập AI',
        badgeClass: 'badge-green',
        time: '14:00 – 15:30',
        room: 'Phòng 405'
      }
    ],
    notes: [
      { id: 1, text: 'Nộp bài tập code thuật toán sắp xếp môn Tin học' },
      { id: 2, text: 'Ôn tập hình học không gian Oxyz chuẩn bị thi giữa kỳ' }
    ]
  }
};

export default function StudentScheduleDetailCard({ 
  selectedDay = 8, 
  selectedMonth = 'Thg 3',
  onAddNewSchedule 
}) {
  // Get mock day data or fallback to a standard day
  const daySchedule = STUDENT_DAILY_SCHEDULES[selectedDay] || {
    items: [
      {
        id: 1,
        accent: 'blue',
        title: 'Toán học 12',
        classTag: '12A1',
        badgeTag: 'Tiết 1 – 2',
        badgeClass: 'badge-blue',
        time: '07:30 – 09:00',
        room: 'Phòng 302'
      },
      {
        id: 2,
        accent: 'orange',
        title: 'Ngữ văn 12',
        classTag: '12A1',
        badgeTag: 'Tiết 3 – 4',
        badgeClass: 'badge-orange',
        time: '09:15 – 10:45',
        room: 'Phòng 201'
      },
      {
        id: 3,
        accent: 'green',
        title: 'Luyện tập AI',
        classTag: 'Tự học',
        badgeTag: 'Luyện tập AI',
        badgeClass: 'badge-green',
        time: '14:00 – 15:30',
        room: 'Phòng 405'
      }
    ],
    notes: [
      { id: 1, text: `Hoàn thành bài tập về nhà cho ngày ${selectedDay} ${selectedMonth}` },
      { id: 2, text: 'Ôn lại các câu hỏi sai trong lần làm bài tập gần nhất' }
    ]
  };

  const [newNoteText, setNewNoteText] = useState('');
  const [notes, setNotes] = useState(daySchedule.notes);

  // Sync notes when selectedDay changes
  React.useEffect(() => {
    setNotes(daySchedule.notes);
  }, [selectedDay]);

  const handleAddNote = (e) => {
    e.preventDefault();
    const clean = newNoteText.trim();
    if (!clean) return;

    const newNote = {
      id: Date.now(),
      text: clean
    };
    setNotes(prev => [newNote, ...prev]);
    setNewNoteText('');
  };

  const handleDeleteNote = (id) => {
    setNotes(prev => prev.filter(n => n.id !== id));
  };

  return (
    <div className="student-schedule-detail-container">
      {/* Top Action Button matching Image 2 */}
      <div className="schedule-detail-top-action-bar">
        <button 
          type="button" 
          className="btn-add-schedule-purple"
          onClick={() => {
            const promptText = prompt('Nhập môn học hoặc hoạt động cần thêm vào lịch học:', 'Ôn tập tiếng Anh Unit 4');
            if (promptText) {
              alert(`Đã thêm lịch học: "${promptText}" vào ngày ${selectedDay} ${selectedMonth}!`);
            }
          }}
        >
          <Plus size={18} strokeWidth={2.5} />
          <span>Thêm lịch mới</span>
        </button>
      </div>

      {/* Card 1: Lịch học hôm nay matching Image 2 (Dedicated for Students) */}
      <div className="schedule-today-card">
        <div className="schedule-today-header">
          <h3 className="schedule-today-title">Lịch học hôm nay</h3>
          <span className="schedule-date-badge">
            {selectedDay} {selectedMonth}
          </span>
        </div>

        <div className="schedule-today-items-list">
          {daySchedule.items.map((item) => (
            <div key={item.id} className={`schedule-item-box border-accent-${item.accent}`}>
              <div className="schedule-item-top-row">
                <h4 className="schedule-item-name">{item.title}</h4>
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
                <div className="schedule-meta-point">
                  <MapPin size={13} className="meta-icon" />
                  <span>{item.room}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Card 2: Ghi chú & Nhắc nhở học tập matching Image 2 */}
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
            aria-label="Thêm ghi chú"
            disabled={!newNoteText.trim()}
          >
            <Plus size={16} strokeWidth={2.5} />
          </button>
        </form>

        {/* Notes List */}
        <div className="notes-items-list">
          {notes.length === 0 ? (
            <div className="notes-empty-state">
              <span>Chưa có ghi chú nào cho ngày này.</span>
            </div>
          ) : (
            notes.map((note) => (
              <div key={note.id} className="note-item-row">
                <div className="note-item-left">
                  <span className="note-purple-bullet">•</span>
                  <p className="note-text-content">{note.text}</p>
                </div>
                <button
                  type="button"
                  className="btn-delete-note"
                  onClick={() => handleDeleteNote(note.id)}
                  title="Xóa ghi chú"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
