// File Name: AllNotificationsModal.jsx
// Description: Fullscreen interactive Notification Center dialog with search, category filtering, master-detail reading view, quick action triggers, and soft delete.
// Created At: 2026-09-13
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { 
  X, 
  Bell, 
  Search, 
  CheckCheck, 
  MessageSquare, 
  FileText, 
  Settings, 
  Clock, 
  Calendar, 
  ChevronRight, 
  Trash2, 
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Inbox,
  Filter
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './AllNotificationsModal.css';

export default function AllNotificationsModal({ isOpen, onClose, onOpenQA }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isTeacher = user?.role !== 'Student';

  // Master initial notification dataset
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'qa',
      category: 'qa',
      categoryLabel: 'Giải đáp thắc mắc',
      title: 'Giải đáp thắc mắc câu hỏi Toán',
      sender: 'Học sinh Hoàng Anh (12A1)',
      content: isTeacher 
        ? 'Học sinh Hoàng Anh (12A1) đã gửi câu hỏi thắc mắc về Câu hỏi 15 trong bài tập tích phân hàm liên tục.' 
        : 'Giáo viên đã phản hồi câu hỏi của bạn về bài tập Toán: Tính tích phân hàm số liên tục.',
      detail: 'Em đặt t = 2-x, suy ra dt = -dx. Đổi cận: x=0 -> t=2; x=2 -> t=0. Khi đó tích phân ∫(từ 0 đến 2)f(2-x)dx = I. Bạn có thể mở bảng Thảo luận để giải đáp chi tiết hơn hoặc chèn gợi ý lời giải.',
      time: '2 phút trước',
      date: 'Hôm nay, 10:50 AM',
      unread: true,
      deleted: false,
      relatedExercise: 'Đề kiểm tra 15p - Giải tích 12 (Lớp 12A1)',
      questionIndex: 15,
      iconTheme: 'purple',
    },
    {
      id: 2,
      type: 'grading',
      category: 'grading',
      categoryLabel: 'Bài tập & Chấm điểm',
      title: 'Bài tập mới nộp cần chấm điểm',
      sender: 'Hệ thống nộp bài tự động',
      content: 'Lớp 12A1 có 15 học sinh vừa hoàn thành bài kiểm tra trực tuyến 15 phút Toán học.',
      detail: 'Hệ thống đã tự động chấm điểm cho 14 câu hỏi trắc nghiệm khách quan. Hiện có 1 câu hỏi tự luận ngắn đang chờ giáo viên nhận xét và xác nhận hoàn tất bảng điểm.',
      time: '25 phút trước',
      date: 'Hôm nay, 10:20 AM',
      unread: true,
      deleted: false,
      relatedExercise: 'Đề kiểm tra 15p - Giải tích 12',
      iconTheme: 'amber',
    },
    {
      id: 3,
      type: 'system',
      category: 'system',
      categoryLabel: 'Hệ thống & Lịch trình',
      title: 'Thông báo bảo trì hệ thống định kỳ',
      sender: 'Quản trị viên Hệ thống EduGlobal',
      content: 'Hệ thống sẽ tiến hành bảo trì máy chủ và tối ưu hóa cơ sở dữ liệu định kỳ vào lúc 23:00 tối nay.',
      detail: 'Thời gian bảo trì dự kiến kéo dài trong khoảng 30 phút. Trong thời gian này, các dịch vụ làm bài thi và tạo sinh tài liệu có thể tạm thời bị gián đoạn. Thầy cô vui lòng lưu dữ liệu trước khung giờ trên.',
      time: '1 giờ trước',
      date: 'Hôm nay, 09:30 AM',
      unread: false,
      deleted: false,
      iconTheme: 'blue',
    },
    {
      id: 4,
      type: 'grading',
      category: 'grading',
      categoryLabel: 'Bài tập & Chấm điểm',
      title: 'Nhắc nhở hạn chót chấm bài tuần 4',
      sender: 'Tổ bộ môn Toán học',
      content: 'Bài tập về nhà tuần 4 - Toán 11B2 sắp đến hạn chót nộp điểm tổng kết.',
      detail: 'Hiện còn 35 bài tập đã được nộp cần phê duyệt và công bố bảng điểm trước 23:59 hôm nay để phục vụ báo cáo định kỳ của tổ chuyên môn.',
      time: '3 giờ trước',
      date: 'Hôm nay, 07:45 AM',
      unread: true,
      deleted: false,
      relatedExercise: 'Bài tập về nhà tuần 4 - Đại số 11',
      iconTheme: 'amber',
    },
    {
      id: 5,
      type: 'qa',
      category: 'qa',
      categoryLabel: 'Giải đáp thắc mắc',
      title: 'Học sinh gửi câu hỏi thảo luận mới',
      sender: 'Học sinh Lan Phương (12A1)',
      content: 'Học sinh Lan Phương đã để lại lời cảm ơn và câu hỏi tiếp nối ở phần đạo hàm cấp 2.',
      detail: 'Lan Phương: "À em hiểu rồi, cảm ơn thầy ạ! Thầy cho em hỏi thêm ở câu 16 nếu lấy đạo hàm hai vế thì cận tích phân có đổi dấu không ạ?"',
      time: 'Hôm qua',
      date: '12/09/2026, 16:30 PM',
      unread: false,
      deleted: false,
      relatedExercise: 'Đề kiểm tra 15p - Giải tích 12',
      iconTheme: 'purple',
    },
    {
      id: 6,
      type: 'system',
      category: 'system',
      categoryLabel: 'Hệ thống & Lịch trình',
      title: 'Lịch giảng dạy tuần mới đã được cập nhật',
      sender: 'Phòng Đào tạo & Khảo thí',
      content: 'Thời khóa biểu giảng dạy tuần 5 đã được đồng bộ lên lịch cá nhân của giáo viên.',
      detail: 'Đã bổ sung 2 tiết phụ đạo môn Toán lớp 12A1 vào sáng Thứ 6 (Tiết 3 - 4 tại phòng A204). Thầy cô vui lòng kiểm tra mục Lịch giảng dạy để nắm chi tiết.',
      time: '2 ngày trước',
      date: '11/09/2026, 14:15 PM',
      unread: false,
      deleted: false,
      iconTheme: 'blue',
    },
  ]);

  const [activeFilter, setActiveFilter] = useState('all'); // 'all', 'unread', 'qa', 'grading', 'system'
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNotifId, setSelectedNotifId] = useState(1);

  // Filter & Search computation
  const filteredNotifications = useMemo(() => {
    return notifications.filter(item => {
      // Strictly ignore soft-deleted items
      if (item.deleted) return false;

      // Filter category
      if (activeFilter === 'unread' && !item.unread) return false;
      if (activeFilter === 'qa' && item.category !== 'qa') return false;
      if (activeFilter === 'grading' && item.category !== 'grading') return false;
      if (activeFilter === 'system' && item.category !== 'system') return false;

      // Search term
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchesTitle = item.title.toLowerCase().includes(query);
        const matchesContent = item.content.toLowerCase().includes(query);
        const matchesSender = item.sender?.toLowerCase().includes(query);
        if (!matchesTitle && !matchesContent && !matchesSender) return false;
      }

      return true;
    });
  }, [notifications, activeFilter, searchTerm]);

  // Active selected notification
  const selectedNotification = useMemo(() => {
    return notifications.find(n => n.id === selectedNotifId && !n.deleted) || filteredNotifications[0] || null;
  }, [notifications, selectedNotifId, filteredNotifications]);

  if (!isOpen) return null;

  // Handler to mark all visible as read
  const handleMarkAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  // Handler to select and automatically mark single item as read
  const handleSelectNotification = (item) => {
    setSelectedNotifId(item.id);
    if (item.unread) {
      setNotifications(prev =>
        prev.map(n => (n.id === item.id ? { ...n, unread: false } : n))
      );
    }
  };

  // Soft delete handler
  const handleSoftDelete = (id, e) => {
    if (e) e.stopPropagation();
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, deleted: true } : n))
    );
    if (selectedNotifId === id) {
      const remaining = notifications.filter(n => n.id !== id && !n.deleted);
      if (remaining.length > 0) {
        setSelectedNotifId(remaining[0].id);
      }
    }
  };

  // Toggle read/unread for selected item
  const handleToggleRead = (id) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, unread: !n.unread } : n))
    );
  };

  // Navigate directly to contextual target
  const handleActionNavigate = (item) => {
    if (item.type === 'qa' && onOpenQA) {
      onClose();
      onOpenQA();
    } else if (item.type === 'grading') {
      onClose();
      navigate('/teacher/grading');
    } else if (item.type === 'system') {
      onClose();
      navigate('/teacher/schedule');
    }
  };

  const unreadCount = notifications.filter(n => !n.deleted && n.unread).length;
  const qaCount = notifications.filter(n => !n.deleted && n.category === 'qa').length;
  const gradingCount = notifications.filter(n => !n.deleted && n.category === 'grading').length;
  const systemCount = notifications.filter(n => !n.deleted && n.category === 'system').length;

  return (
    <div className="notif-modal-backdrop" onClick={onClose}>
      <div className="notif-modal-dialog" onClick={(e) => e.stopPropagation()}>
        
        {/* ==========================================
            1. FULLSCREEN DIALOG HEADER
            ========================================== */}
        <div className="notif-dialog-header">
          <div className="notif-dialog-header-left">
            <div className="notif-header-icon-box">
              <Bell size={22} className="notif-icon-primary" />
              {unreadCount > 0 && <span className="notif-badge-bubble">{unreadCount}</span>}
            </div>
            <div>
              <h2 className="notif-dialog-title">Trung tâm thông báo</h2>
              <p className="notif-dialog-subtitle">
                Xem toàn bộ thông báo hệ thống, tiến độ bài tập và giải đáp thắc mắc học sinh
              </p>
            </div>
          </div>

          <div className="notif-dialog-header-actions">
            <button 
              type="button" 
              className="btn-mark-all-read" 
              onClick={handleMarkAllRead}
              title="Đánh dấu tất cả là đã đọc"
            >
              <CheckCheck size={16} />
              <span>Đánh dấu tất cả đã đọc</span>
            </button>

            <button 
              type="button" 
              className="notif-dialog-close-btn" 
              onClick={onClose}
              aria-label="Đóng dialog"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* ==========================================
            2. FILTER TABS & SEARCH BAR STRIP
            ========================================== */}
        <div className="notif-dialog-filter-bar">
          <div className="notif-filter-tabs">
            <button 
              type="button" 
              className={`filter-tab-pill ${activeFilter === 'all' ? 'active' : ''}`}
              onClick={() => setActiveFilter('all')}
            >
              <span>Tất cả</span>
              <span className="pill-count">{notifications.filter(n => !n.deleted).length}</span>
            </button>

            <button 
              type="button" 
              className={`filter-tab-pill ${activeFilter === 'unread' ? 'active' : ''}`}
              onClick={() => setActiveFilter('unread')}
            >
              <span>Chưa đọc</span>
              {unreadCount > 0 && <span className="pill-count unread">{unreadCount}</span>}
            </button>

            <button 
              type="button" 
              className={`filter-tab-pill ${activeFilter === 'qa' ? 'active' : ''}`}
              onClick={() => setActiveFilter('qa')}
            >
              <MessageSquare size={13} />
              <span>Giải đáp thắc mắc</span>
              <span className="pill-count">{qaCount}</span>
            </button>

            <button 
              type="button" 
              className={`filter-tab-pill ${activeFilter === 'grading' ? 'active' : ''}`}
              onClick={() => setActiveFilter('grading')}
            >
              <FileText size={13} />
              <span>Bài tập & Chấm điểm</span>
              <span className="pill-count">{gradingCount}</span>
            </button>

            <button 
              type="button" 
              className={`filter-tab-pill ${activeFilter === 'system' ? 'active' : ''}`}
              onClick={() => setActiveFilter('system')}
            >
              <Settings size={13} />
              <span>Hệ thống</span>
              <span className="pill-count">{systemCount}</span>
            </button>
          </div>

          <div className="notif-search-wrapper">
            <Search size={16} className="search-icon-inside" />
            <input
              type="text"
              className="notif-search-input"
              placeholder="Tìm kiếm nội dung thông báo..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button 
                type="button" 
                className="btn-clear-search" 
                onClick={() => setSearchTerm('')}
              >
                <X size={13} />
              </button>
            )}
          </div>
        </div>

        {/* ==========================================
            3. MASTER-DETAIL BODY LAYOUT
            ========================================== */}
        <div className="notif-dialog-body-split">
          
          {/* LEFT LIST COLUMN */}
          <div className="notif-list-sidebar">
            {filteredNotifications.length === 0 ? (
              <div className="notif-empty-state">
                <Inbox size={42} strokeWidth={1.5} className="empty-state-icon" />
                <h4 className="empty-state-title">Không tìm thấy thông báo</h4>
                <p className="empty-state-desc">
                  {searchTerm 
                    ? 'Không có thông báo nào khớp với từ khóa tìm kiếm của bạn.' 
                    : 'Không có thông báo nào trong danh mục này.'}
                </p>
              </div>
            ) : (
              <div className="notif-scroll-items">
                {filteredNotifications.map((item) => {
                  const isSelected = selectedNotification?.id === item.id;
                  let IconComponent = Bell;
                  if (item.type === 'qa') IconComponent = MessageSquare;
                  if (item.type === 'grading') IconComponent = FileText;
                  if (item.type === 'system') IconComponent = Settings;

                  return (
                    <div 
                      key={item.id} 
                      className={`notif-card-item ${item.unread ? 'unread' : ''} ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleSelectNotification(item)}
                    >
                      <div className={`notif-avatar-circle ${item.iconTheme}`}>
                        <IconComponent size={18} />
                      </div>

                      <div className="notif-card-info">
                        <div className="notif-card-top-row">
                          <span className={`notif-category-badge ${item.iconTheme}`}>
                            {item.categoryLabel}
                          </span>
                          <span className="notif-card-time">{item.time}</span>
                        </div>

                        <h4 className="notif-card-title">{item.title}</h4>
                        <p className="notif-card-snippet">{item.content}</p>

                        <div className="notif-card-bottom-row">
                          <span className="notif-card-sender">{item.sender}</span>
                          <button
                            type="button"
                            className="btn-delete-card-notif"
                            title="Xóa thông báo này"
                            onClick={(e) => handleSoftDelete(item.id, e)}
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </div>

                      {item.unread && <span className="notif-card-dot" />}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* RIGHT DETAIL COLUMN */}
          <div className="notif-detail-view-pane">
            {selectedNotification ? (
              <div className="notif-detail-card">
                {/* Detail Top Header */}
                <div className="notif-detail-header">
                  <div className="notif-detail-category-row">
                    <span className={`notif-detail-badge ${selectedNotification.iconTheme}`}>
                      {selectedNotification.categoryLabel}
                    </span>
                    <span className="notif-detail-date">
                      <Clock size={13} />
                      <span>{selectedNotification.date}</span>
                    </span>
                    {selectedNotification.unread ? (
                      <span className="status-pill-unread">Chưa đọc</span>
                    ) : (
                      <span className="status-pill-read">Đã đọc</span>
                    )}
                  </div>

                  <h3 className="notif-detail-main-title">{selectedNotification.title}</h3>
                  <div className="notif-detail-sender-row">
                    <span>Gửi từ: <strong>{selectedNotification.sender}</strong></span>
                  </div>
                </div>

                {/* Detail Content Box */}
                <div className="notif-detail-body">
                  <div className="notif-body-highlight-card">
                    <p className="notif-body-primary-text">{selectedNotification.content}</p>
                  </div>

                  <div className="notif-body-section">
                    <h5 className="section-subtitle">Nội dung chi tiết</h5>
                    <p className="section-detail-text">{selectedNotification.detail}</p>
                  </div>

                  {selectedNotification.relatedExercise && (
                    <div className="notif-related-context-card">
                      <span className="context-label">Bài tập liên quan:</span>
                      <span className="context-value">{selectedNotification.relatedExercise}</span>
                    </div>
                  )}
                </div>

                {/* Detail Footer Actions */}
                <div className="notif-detail-footer">
                  <div className="footer-left-actions">
                    <button
                      type="button"
                      className="btn-toggle-read"
                      onClick={() => handleToggleRead(selectedNotification.id)}
                    >
                      {selectedNotification.unread ? (
                        <>
                          <CheckCircle2 size={15} />
                          <span>Đánh dấu đã đọc</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle size={15} />
                          <span>Đánh dấu chưa đọc</span>
                        </>
                      )}
                    </button>

                    <button
                      type="button"
                      className="btn-delete-detail"
                      onClick={() => handleSoftDelete(selectedNotification.id)}
                    >
                      <Trash2 size={15} />
                      <span>Xóa thông báo</span>
                    </button>
                  </div>

                  <div className="footer-right-actions">
                    {selectedNotification.type === 'qa' && (
                      <button
                        type="button"
                        className="btn-primary-action"
                        onClick={() => handleActionNavigate(selectedNotification)}
                      >
                        <MessageSquare size={16} />
                        <span>Mở bảng Giải đáp thắc mắc</span>
                        <ExternalLink size={14} />
                      </button>
                    )}

                    {selectedNotification.type === 'grading' && (
                      <button
                        type="button"
                        className="btn-primary-action"
                        onClick={() => handleActionNavigate(selectedNotification)}
                      >
                        <FileText size={16} />
                        <span>Đi tới Chấm bài ngay</span>
                        <ExternalLink size={14} />
                      </button>
                    )}

                    {selectedNotification.type === 'system' && (
                      <button
                        type="button"
                        className="btn-primary-action"
                        onClick={() => handleActionNavigate(selectedNotification)}
                      >
                        <Calendar size={16} />
                        <span>Xem Lịch giảng dạy</span>
                        <ExternalLink size={14} />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="notif-detail-empty">
                <Inbox size={48} className="empty-icon" />
                <h4>Chọn một thông báo để xem chi tiết</h4>
                <p>Nội dung chi tiết và các tùy chọn hành động sẽ hiển thị ở đây.</p>
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
