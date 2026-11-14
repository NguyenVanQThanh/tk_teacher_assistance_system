// File Name: EditDocumentModal.jsx
// Description: Modal dialog for editing document title and document type.
// Created At: 2026-09-12
// Created By: Tam Khang
// Updated At: 2026-11-12
// Updated By: AI Agent

import React, { useState, useEffect } from 'react';
import useUnsavedChangesGuard from '../../hooks/useUnsavedChangesGuard';
import { X, Edit3, Save, ChevronDown } from 'lucide-react';
import './EditDocumentModal.css';

const DOCUMENT_TYPES = [
  { value: 'lecture', label: 'Bài giảng' },
  { value: 'exam', label: 'Đề kiểm tra' },
  { value: 'reference', label: 'Tài liệu tham khảo' },
];

export default function EditDocumentModal({ isOpen, doc, onClose, onSave }) {
  if (!isOpen || !doc) return null;

  const [title, setTitle] = useState(doc.title || '');
  const [docType, setDocType] = useState(doc.document_type || doc.documentType || 'reference');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const guardedClose = useUnsavedChangesGuard({ title, docType }, onClose, !isSubmitting);

  // Sync state whenever doc prop updates
  useEffect(() => {
    if (doc) {
      setTitle(doc.title || '');
      setDocType(doc.document_type || doc.documentType || 'reference');
      setErrorMessage('');
    }
  }, [doc]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || title.trim().length < 3) {
      setErrorMessage('Tên tài liệu phải có ít nhất 3 ký tự.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      await onSave({
        ...doc,
        title: title.trim(),
        document_type: docType,
        documentType: docType,
        fileType: docType, // list mapping uses fileType for document type; file extension lives in fileExtension
      });
      onClose();
    } catch (err) {
      console.error('Error saving document edit:', err);
      setErrorMessage('Không thể lưu thông tin cập nhật. Vui lòng thử lại.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop-overlay" onClick={guardedClose}>
      <div className="edit-doc-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <header className="edit-doc-modal-header">
          <div className="edit-doc-header-title">
            <div className="edit-doc-icon-badge">
              <Edit3 size={18} />
            </div>
            <div>
              <h3 className="modal-title">Chỉnh sửa thông tin tài liệu</h3>
              <p className="modal-subtitle">Chỉnh sửa tên và phân loại tài liệu</p>
            </div>
          </div>
          <button
            type="button"
            className="btn-modal-close"
            onClick={guardedClose}
            aria-label="Đóng"
          >
            <X size={18} />
          </button>
        </header>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="edit-doc-form-body">
          {errorMessage && (
            <div className="edit-doc-error-banner">
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Field 1: Tên tài liệu */}
          <div className="edit-form-field">
            <label className="edit-field-label">
              <span>Tên tài liệu</span>
              <span className="required-star">*</span>
            </label>
            <input
              type="text"
              className="edit-field-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Nhập tên tài liệu..."
              required
              minLength={3}
              autoFocus
            />
          </div>

          {/* Form Row: Loại tài liệu */}
          <div className="edit-form-grid">
            {/* Field 2: Loại tài liệu */}
            <div className="edit-form-field">
              <label className="edit-field-label">
                <span>Loại tài liệu</span>
              </label>
              <div className="edit-select-wrapper">
                <select
                  className="edit-field-select"
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                >
                  {DOCUMENT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
                <ChevronDown size={16} className="select-dropdown-chevron" />
              </div>
            </div>
          </div>

          {/* Footer Action Buttons */}
          <div className="edit-doc-modal-footer">
            <button
              type="button"
              className="btn-modal-cancel"
              onClick={guardedClose}
              disabled={isSubmitting}
            >
              Hủy bỏ
            </button>
            <button
              type="submit"
              className="btn-modal-save"
              disabled={isSubmitting}
            >
              <Save size={15} />
              <span>{isSubmitting ? 'Đang lưu...' : 'Lưu thay đổi'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
