// File Name: DocumentPreviewModal.jsx
// Description: Interactive Document Preview Modal for viewing materials with mock content viewer.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React from 'react';
import { X, Download, FileText, ExternalLink, Calendar, HardDrive, User } from 'lucide-react';
import './DocumentPreviewModal.css';

export default function DocumentPreviewModal({ doc, isOpen, onClose }) {
  if (!isOpen || !doc) return null;

  return (
    <div className="modal-backdrop-overlay" onClick={onClose}>
      <div className="preview-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="preview-modal-header">
          <div className="preview-title-box">
            <FileText size={20} className="preview-header-icon" />
            <div>
              <h3 className="preview-modal-title">{doc.title}</h3>
              <p className="preview-modal-subtitle">
                {doc.fileSize} • Tải lên ngày {doc.uploadDate} bởi {doc.authorName}
              </p>
            </div>
          </div>
          <div className="preview-header-actions">
            <button 
              type="button" 
              className="btn-preview-download"
              onClick={() => alert(`Đang tải xuống tài liệu: ${doc.title}`)}
            >
              <Download size={16} />
              <span>Tải xuống</span>
            </button>
            <button type="button" className="btn-modal-close" onClick={onClose}>
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content Viewer Body */}
        <div className="preview-modal-body">
          <div className="document-sheet-mockup">
            <div className="mockup-header-banner">
              <h2>{doc.title}</h2>
              <span className="mockup-sub">HỆ THỐNG QUẢN LÝ DẠY HỌC THÔNG MINH - SMART LMS</span>
            </div>

            <div className="mockup-content-paragraphs">
              <h3>I. MỤC TIÊU VÀ YÊU CẦU CẦN ĐẠT</h3>
              <p>
                1. Nắm vững toàn bộ kiến thức trọng tâm trong chương trình, vận dụng linh hoạt các phương pháp giải bài tập cơ bản và nâng cao.
              </p>
              <p>
                2. Rèn luyện kỹ năng phân tích đề thi, tư duy logic và khả năng làm việc độc lập cũng như thảo luận nhóm hiệu quả.
              </p>

              <h3>II. NỘI DUNG CHI TIẾT VÀ BÀI TẬP VẬN DỤNG</h3>
              <p>
                Học sinh cần hoàn thiện các câu hỏi trắc nghiệm khách quan và các bài toán tự luận theo từng phần chuyên đề đã phân bổ.
              </p>
              <div className="mockup-code-block">
                <span>[Tài liệu đính kèm: {doc.title}]</span>
                <br />
                <span>• Định dạng: {doc.fileType?.toUpperCase()} | Kích thước: {doc.fileSize}</span>
                <br />
                <span>• Đã được kiểm duyệt bởi tổ bộ môn chuyên môn.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
