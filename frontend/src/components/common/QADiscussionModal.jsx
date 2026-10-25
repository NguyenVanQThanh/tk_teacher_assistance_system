// File Name: QADiscussionModal.jsx
// Description: Interactive Q&A discussion, detailed exercise explanation, question review, and teacher-student chat modal matching Image 2 visual mockup.
// Created At: 2026-09-13
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState } from 'react';
import { 
  X, 
  MessageSquare, 
  Lightbulb, 
  CheckCircle, 
  Send, 
  ArrowLeft, 
  ArrowRight,
  BadgeCheck,
  Sparkles
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './QADiscussionModal.css';

export default function QADiscussionModal({ isOpen, onClose }) {
  const { user } = useAuth();
  const isTeacher = user?.role !== 'Student';

  // Teacher display title & name (defaults to 'Thầy Tuấn (GV)' to match Image 2)
  const teacherDisplayName = user?.full_name 
    ? (user.full_name.startsWith('Thầy') || user.full_name.startsWith('Cô')
        ? `${user.full_name} (GV)`
        : `Thầy ${user.full_name} (GV)`)
    : 'Thầy Tuấn (GV)';

  const [activeQuestion, setActiveQuestion] = useState(15);
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 1,
      author: 'Hoàng Anh',
      role: 'student',
      avatar: 'H',
      avatarClass: 'purple-light',
      time: '10:45 AM',
      text: 'Thầy ơi, tại sao ∫f(2-x)dx lại bằng I vậy ạ?'
    },
    {
      id: 2,
      author: 'Thầy Tuấn (GV)',
      role: 'teacher',
      isTeacher: true,
      avatar: '👨‍🏫',
      avatarClass: 'teacher-avatar',
      time: '10:50 AM',
      text: 'Em đặt t = 2-x, suy ra dt = -dx. Đổi cận: x=0 -> t=2; x=2 -> t=0. Khi đó ∫(từ 0 đến 2)f(2-x)dx = -∫(từ 2 đến 0)f(t)dt = ∫(từ 0 đến 2)f(t)dt = I nhé.'
    },
    {
      id: 3,
      author: 'Lan Phương',
      role: 'student',
      avatar: 'L',
      avatarClass: 'purple-dark',
      time: '11:02 AM',
      text: 'À em hiểu rồi, cảm ơn thầy ạ!'
    }
  ]);

  if (!isOpen) return null;

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    // As a Teacher in this interface, new messages are posted with verified Teacher credentials
    setMessages(prev => [
      ...prev,
      {
        id: Date.now(),
        author: teacherDisplayName,
        role: 'teacher',
        isTeacher: true,
        avatar: '👨‍🏫',
        avatarClass: 'teacher-avatar',
        time: 'Vừa xong',
        text: inputMessage.trim()
      }
    ]);
    setInputMessage('');
  };

  return (
    <div className="qa-modal-backdrop" onClick={onClose}>
      <div className="qa-modal-container" onClick={(e) => e.stopPropagation()}>
        
        {/* ==========================================
            1. LEFT COLUMN: Danh sách câu hỏi
            ========================================== */}
        <aside className="qa-sidebar-palette">
          <h3 className="qa-palette-title">Danh sách câu hỏi</h3>
          
          <div className="qa-legend-row">
            <div className="qa-legend-item">
              <span className="qa-dot green" />
              <span>Đã làm</span>
            </div>
            <div className="qa-legend-item">
              <span className="qa-dot blue" />
              <span>Đang làm</span>
            </div>
            <div className="qa-legend-item">
              <span className="qa-dot red" />
              <span>Xem lại</span>
            </div>
          </div>

          <div className="qa-numbers-grid">
            {Array.from({ length: 20 }, (_, idx) => {
              const qNum = idx + 1;
              let statusClass = '';
              if (qNum === activeQuestion) {
                statusClass = 'active';
              } else if (qNum <= 12) {
                statusClass = 'completed';
              } else if (qNum === 13 || qNum === 14) {
                statusClass = 'review';
              }

              return (
                <button
                  key={qNum}
                  type="button"
                  className={`qa-num-cell ${statusClass}`}
                  onClick={() => setActiveQuestion(qNum)}
                >
                  {qNum}
                </button>
              );
            })}
          </div>
        </aside>

        {/* ==========================================
            2. CENTER COLUMN: Nội dung câu hỏi & Giải thích
            ========================================== */}
        <main className="qa-center-viewport">
          <div className="qa-question-card">
            <div className="qa-question-header">
              <h2 className="qa-question-title">Câu hỏi {activeQuestion}</h2>
              <span className="qa-subject-pill">Toán Học - Đại Số</span>
            </div>

            <p className="qa-statement-text">
              Cho hàm số f(x) liên tục trên đoạn [0; 2] thỏa mãn f(x) + f(2 - x) = x^2 - 2x + 3. Tính tích phân I = ∫(từ 0 đến 2) f(x)dx.
            </p>

            {/* Parabola Graph Window Frame */}
            <div className="qa-graph-window-card">
              <div className="qa-graph-window-header">
                <span className="qa-graph-back-link">&lt; Chi tiết bài tập</span>
                <span className="qa-graph-window-title">Đồ thị hàm số y = x²</span>
                <span className="qa-graph-window-dot" />
              </div>
              <div className="qa-graph-canvas-box">
                <svg width="320" height="150" viewBox="0 0 320 150">
                  {/* Background grid */}
                  <defs>
                    <pattern id="qa-grid" width="20" height="20" patternUnits="userSpaceOnUse">
                      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#F1F5F9" strokeWidth="1" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#qa-grid)" />

                  {/* Axes */}
                  <line x1="30" y1="120" x2="290" y2="120" stroke="#94A3B8" strokeWidth="1.2" />
                  <line x1="160" y1="140" x2="160" y2="15" stroke="#94A3B8" strokeWidth="1.2" />
                  
                  {/* Axis arrows */}
                  <polygon points="290,120 284,117 284,123" fill="#94A3B8" />
                  <polygon points="160,15 157,21 163,21" fill="#94A3B8" />

                  {/* Labels */}
                  <text x="292" y="124" fontSize="11" fill="#64748B" fontWeight="600">x</text>
                  <text x="155" y="12" fontSize="11" fill="#64748B" fontWeight="600">y</text>
                  
                  {/* Coordinate numbers */}
                  <text x="100" y="132" fontSize="9" fill="#94A3B8">-2</text>
                  <text x="130" y="132" fontSize="9" fill="#94A3B8">-1</text>
                  <text x="152" y="132" fontSize="9" fill="#94A3B8">0</text>
                  <text x="190" y="132" fontSize="9" fill="#94A3B8">1</text>
                  <text x="220" y="132" fontSize="9" fill="#94A3B8">2</text>

                  {/* Parabola Curve y = x^2 */}
                  <path 
                    d="M 90,25 Q 160,120 230,25" 
                    fill="none" 
                    stroke="#7C3AED" 
                    strokeWidth="2.2" 
                  />
                  <text x="228" y="20" fontSize="10" fill="#7C3AED" fontWeight="600" fontStyle="italic">y = x²</text>
                </svg>
              </div>
            </div>

            {/* 4 Multiple Choice Options */}
            <div className="qa-options-list">
              <div className="qa-option-row">
                <div className="qa-option-left">
                  <div className="qa-radio-circle" />
                  <span className="qa-option-label">A. &nbsp; I = 2/3</span>
                </div>
              </div>

              <div className="qa-option-row correct">
                <div className="qa-option-left">
                  <div className="qa-radio-circle checked">
                    <div className="qa-radio-dot" />
                  </div>
                  <span className="qa-option-label">B. &nbsp; I = 8/3</span>
                </div>
                <CheckCircle size={19} className="qa-check-icon" />
              </div>

              <div className="qa-option-row">
                <div className="qa-option-left">
                  <div className="qa-radio-circle" />
                  <span className="qa-option-label">C. &nbsp; I = 4/3</span>
                </div>
              </div>

              <div className="qa-option-row">
                <div className="qa-option-left">
                  <div className="qa-radio-circle" />
                  <span className="qa-option-label">D. &nbsp; I = 10/3</span>
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Explanation Box */}
          <div className="qa-explanation-card">
            <div className="qa-explanation-header">
              <Lightbulb size={18} />
              <span>Giải thích chi tiết</span>
            </div>
            <div className="qa-explanation-body">
              {`Ta có: f(x) + f(2 - x) = x² - 2x + 3.
Lấy tích phân hai vế từ 0 đến 2, ta được:
∫f(x)dx + ∫f(2-x)dx = ∫(x² - 2x + 3)dx
<=> I + I = (x³/3 - x² + 3x)|(0 to 2) = 8/3 - 4 + 6 = 14/3
=> 2I = 14/3 => I = 8/3.`}
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="qa-nav-buttons-row">
            <button 
              type="button" 
              className="qa-btn-prev"
              disabled={activeQuestion <= 1}
              onClick={() => setActiveQuestion(prev => Math.max(prev - 1, 1))}
            >
              <ArrowLeft size={15} />
              <span>Câu trước</span>
            </button>
            <button 
              type="button" 
              className="qa-btn-next"
              disabled={activeQuestion >= 20}
              onClick={() => setActiveQuestion(prev => Math.min(prev + 1, 20))}
            >
              <span>Câu tiếp theo</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </main>

        {/* ==========================================
            3. RIGHT COLUMN: Thảo luận (Chat Drawer)
            ========================================== */}
        <aside className="qa-discussion-drawer">
          <div className="qa-drawer-header">
            <div className="qa-drawer-title-group">
              <MessageSquare size={18} color="#4D308D" />
              <span>Thảo luận ({messages.length})</span>
              {isTeacher && <span className="qa-teacher-tag">Giáo viên</span>}
            </div>
            <button type="button" className="qa-btn-close" onClick={onClose} aria-label="Close">
              <X size={16} />
            </button>
          </div>

          <div className="qa-messages-thread">
            {messages.map((msg) => (
              <div key={msg.id} className="qa-message-item">
                <div className={`qa-msg-avatar ${msg.avatarClass}`}>
                  {msg.isTeacher ? (
                    <span className="qa-teacher-avatar-badge">👨‍🏫</span>
                  ) : (
                    msg.avatar
                  )}
                </div>
                <div className="qa-msg-content-block">
                  <div className="qa-msg-author-row">
                    <span className="qa-msg-author-name">
                      {msg.author}
                      {msg.isTeacher && <BadgeCheck size={14} className="qa-verified-badge" />}
                    </span>
                    <span className="qa-msg-time">{msg.time}</span>
                  </div>
                  <div className={`qa-msg-bubble ${msg.isTeacher ? 'teacher-highlight' : ''}`}>
                    {msg.text}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Chat Input Box */}
          <div className="qa-drawer-input-footer">
            <div className="qa-teacher-composer-tools">
              <button
                type="button"
                className="qa-btn-insert-solution"
                onClick={() => setInputMessage(prev => (prev ? `${prev}\n\n` : '') + 'Em tham khảo lời giải chi tiết: Lấy tích phân 2 vế từ 0 đến 2, ta có ∫f(x)dx + ∫f(2-x)dx = 14/3 => 2I = 14/3 => I = 8/3 nhé.')}
                title="Chèn lời giải tóm tắt vào khung phản hồi"
              >
                <Sparkles size={12} />
                <span>Chèn gợi ý lời giải</span>
              </button>
            </div>
            <form className="qa-chat-composer" onSubmit={handleSendMessage}>
              <textarea
                className="qa-chat-textarea"
                placeholder={isTeacher ? "Nhập nội dung giải đáp cho học sinh..." : "Đặt câu hỏi hoặc thảo luận..."}
                rows={2}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                  }
                }}
              />
              <div className="qa-composer-actions">
                <button 
                  type="submit" 
                  className="qa-btn-send-msg" 
                  aria-label="Send message"
                  title="Gửi phản hồi cho học sinh"
                >
                  <Send size={14} />
                </button>
              </div>
            </form>
          </div>
        </aside>

      </div>
    </div>
  );
}
