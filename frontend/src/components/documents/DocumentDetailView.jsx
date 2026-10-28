// File Name: DocumentDetailView.jsx
// Description: Document detail view displaying metadata, description, action buttons (view, download, edit), and analytics metrics.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React from 'react';
import { 
  ArrowLeft, 
  MoreVertical, 
  Eye, 
  Download, 
  Edit3, 
  User, 
  Calendar, 
  FileText, 
  Folder, 
  Check, 
  Star 
} from 'lucide-react';
import './DocumentDetailView.css';

export default function DocumentDetailView({ 
  doc, 
  onBack, 
  onViewDocument, 
  onDownloadDocument, 
  onEditDocument, 
  onMoreOptions 
}) {
  if (!doc) return null;

  const defaultDescription = doc.description || 
    'Tài liệu tổng hợp các kiến thức trọng tâm học kì 1 môn Toán lớp 12, bao gồm các chuyên đề: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số, Hàm số lũy thừa, hàm số mũ và hàm số logarit. Kèm theo hệ thống bài tập tự luyện từ cơ bản đến nâng cao có đáp án chi tiết, phù hợp cho học sinh ôn thi THPT Quốc gia.';

  const folderName = doc.folder || `Toán ${doc.grade || '12'}`;
  const viewsCount = doc.viewsCount || '0';
  const downloadsCount = doc.downloadsCount !== undefined && doc.downloadsCount !== null ? String(doc.downloadsCount) : '0';
  const ratingScore = doc.ratingScore || '5.0/5';
  const ratingsCount = doc.ratingsCount || '1';

  return (
    <div className="doc-detail-view-container">
      {/* Back Button Link */}
      <button 
        type="button" 
        className="btn-back-repo"
        onClick={onBack}
      >
        <ArrowLeft size={16} />
        <span>Quay lại Kho tài liệu</span>
      </button>

      {/* Main Document Details Card */}
      <div className="doc-detail-main-card">
        {/* Top Header Section */}
        <div className="doc-detail-header-row">
          {/* Big PDF Icon Badge */}
          <div className="doc-large-type-badge pdf">
            <div className="pdf-icon-frame">
              <svg width="34" height="42" viewBox="0 0 34 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 0C1.79086 0 0 1.79086 0 4V38C0 40.2091 1.79086 42 4 42H30C32.2091 42 34 40.2091 34 38V12L22 0H4Z" fill="#FEE2E2" />
                <path d="M22 0L34 12H26C23.7909 12 22 10.2091 22 8V0Z" fill="#FECDD3" />
                <path d="M5 24C5 22.3431 6.34315 21 8 21H11C12.6569 21 14 22.3431 14 24V25C14 26.6569 12.6569 28 11 28H8V32H5V24ZM8 24V25H11V24H8Z" fill="#E11D48" />
                <path d="M16 21H19C21.2091 21 23 22.7909 23 25V28C23 30.2091 21.2091 32 19 32H16V21ZM19 29C19.5523 29 20 28.5523 20 28V25C20 24.4477 19.5523 24 19 24H19V29Z" fill="#E11D48" />
                <path d="M25 21H31V24H28V26H31V29H28V32H25V21Z" fill="#E11D48" />
              </svg>
            </div>
          </div>

          {/* Title & Metadata Details */}
          <div className="doc-header-info-col">
            <h1 className="doc-main-title">{doc.title}</h1>

            <div className="doc-meta-info-grid">
              <div className="meta-info-item">
                <User size={15} className="meta-icon text-slate" />
                <span className="meta-label">Tác giả:</span>
                <span className="meta-value">{doc.authorName}</span>
              </div>

              <div className="meta-info-item">
                <Calendar size={15} className="meta-icon text-slate" />
                <span className="meta-label">Ngày tải lên:</span>
                <span className="meta-value">{doc.uploadDate}</span>
              </div>

              <div className="meta-info-item">
                <FileText size={15} className="meta-icon text-slate" />
                <span className="meta-label">Dung lượng:</span>
                <span className="meta-value">{doc.fileSize}</span>
              </div>

              <div className="meta-info-item">
                <Folder size={15} className="meta-icon text-purple" />
                <span className="meta-label">Thư mục:</span>
                <span className="meta-value text-purple-bold">{folderName}</span>
              </div>
            </div>
          </div>

          {/* More Options Button */}
          <button 
            type="button" 
            className="btn-doc-more-options"
            onClick={() => onMoreOptions && onMoreOptions(doc)}
            aria-label="Tùy chọn khác"
          >
            <MoreVertical size={20} />
          </button>
        </div>

        {/* Description Box */}
        <div className="doc-description-container">
          <h2 className="description-heading">Mô tả tài liệu:</h2>
          <p className="description-paragraph">{defaultDescription}</p>
        </div>

        {/* Action Buttons Row */}
        <div className="doc-actions-toolbar">
          <button 
            type="button" 
            className="btn-action-primary"
            onClick={() => onViewDocument ? onViewDocument(doc) : alert(`Đang mở xem tài liệu: ${doc.title}`)}
          >
            <Eye size={16} />
            <span>Xem tài liệu</span>
          </button>

          <button 
            type="button" 
            className="btn-action-download"
            onClick={() => onDownloadDocument ? onDownloadDocument(doc) : alert(`Bắt đầu tải xuống: ${doc.title}`)}
          >
            <Download size={16} />
            <span>Tải xuống</span>
          </button>

          <button 
            type="button" 
            className="btn-action-edit"
            onClick={() => onEditDocument ? onEditDocument(doc) : alert(`Chỉnh sửa tài liệu: ${doc.title}`)}
          >
            <Edit3 size={16} />
            <span>Chỉnh sửa</span>
          </button>
        </div>
      </div>

      {/* Metric / Statistics Cards Row */}
      <div className="doc-analytics-cards-grid">
        {/* Metric 1: Views */}
        <div className="doc-stat-card">
          <div className="stat-icon-wrap blue">
            <Eye size={22} />
          </div>
          <div className="stat-number">{viewsCount}</div>
          <div className="stat-label">Lượt xem</div>
        </div>

        {/* Metric 2: Downloads */}
        <div className="doc-stat-card">
          <div className="stat-icon-wrap green">
            <Check size={22} strokeWidth={2.5} />
          </div>
          <div className="stat-number">{downloadsCount}</div>
          <div className="stat-label">Lượt tải về</div>
        </div>

        {/* Metric 3: Ratings */}
        <div className="doc-stat-card">
          <div className="stat-icon-wrap purple">
            <Star size={22} />
          </div>
          <div className="stat-number">{ratingScore}</div>
          <div className="stat-label">Đánh giá ({ratingsCount})</div>
        </div>
      </div>
    </div>
  );
}
