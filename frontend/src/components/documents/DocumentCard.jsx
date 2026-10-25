// File Name: DocumentCard.jsx
// Description: Reusable card component for displaying educational documents and learning materials.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-12
// Updated By: Tam Khang

import React from 'react';
import { 
  FileText, 
  Video, 
  FileCode, 
  X, 
  Eye, 
  Download, 
  Edit3, 
  HardDrive 
} from 'lucide-react';
import './DocumentCard.css';

export default function DocumentCard({ doc, onPreview, onDownload, onEdit, onMore, onDelete, onRemove }) {
  // Determine icon and color scheme based on file type
  const renderTypeIcon = () => {
    switch (doc.fileType?.toLowerCase()) {
      case 'pdf':
        return (
          <div className="doc-icon-badge pdf-badge">
            <span className="pdf-tag">PDF</span>
          </div>
        );
      case 'video':
        return (
          <div className="doc-icon-badge video-badge">
            <Video size={20} strokeWidth={2.2} />
          </div>
        );
      case 'code':
        return (
          <div className="doc-icon-badge code-badge">
            <FileCode size={20} strokeWidth={2.2} />
          </div>
        );
      case 'exercise':
        return (
          <div className="doc-icon-badge exercise-badge">
            <FileText size={20} strokeWidth={2.2} />
          </div>
        );
      case 'word':
      default:
        return (
          <div className="doc-icon-badge word-badge">
            <FileText size={20} strokeWidth={2.2} />
          </div>
        );
    }
  };

  return (
    <div 
      className="document-card clickable-card"
      onClick={() => onPreview && onPreview(doc)}
    >
      {/* Top Header: Icon & Close / Delete Button */}
      <div className="doc-card-top">
        {renderTypeIcon()}
        <button 
          type="button" 
          className="doc-more-btn doc-close-btn" 
          onClick={(e) => {
            e.stopPropagation();
            if (onDelete) {
              onDelete(doc);
            } else if (onRemove) {
              onRemove(doc);
            } else if (onMore) {
              onMore(doc);
            }
          }}
          aria-label="Xóa tài liệu"
          title="Xóa tài liệu"
        >
          <X size={17} strokeWidth={2.2} />
        </button>
      </div>

      {/* Document Title */}
      <h3 className="doc-title" title={doc.title}>
        {doc.title}
      </h3>

      {/* Meta details: Size & Upload Date */}
      <div className="doc-meta-row">
        <HardDrive size={13} className="meta-icon" />
        <span>{doc.fileSize}</span>
        <span className="meta-dot">•</span>
        <span>{doc.uploadDate}</span>
      </div>

      {/* Teacher Uploader */}
      <div className="doc-author-row">
        <div className="author-avatar-mini">
          {doc.authorInitial || 'GV'}
        </div>
        <span className="author-name">{doc.authorName}</span>
      </div>

      {/* Bottom Actions Bar */}
      <div className="doc-card-footer">
        <button 
          type="button" 
          className="btn-action-preview"
          onClick={(e) => {
            e.stopPropagation();
            onPreview && onPreview(doc);
          }}
        >
          <Eye size={15} />
          <span>Xem</span>
        </button>

        <div className="doc-action-icons">
          <button 
            type="button" 
            className="icon-action-btn"
            onClick={(e) => {
              e.stopPropagation();
              onDownload && onDownload(doc);
            }}
            title="Tải xuống tài liệu"
          >
            <Download size={16} />
          </button>
          <button 
            type="button" 
            className="icon-action-btn"
            onClick={(e) => {
              e.stopPropagation();
              onEdit && onEdit(doc);
            }}
            title="Chỉnh sửa thông tin"
          >
            <Edit3 size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
