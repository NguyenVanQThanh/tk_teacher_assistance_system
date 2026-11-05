// File Name: EditDocumentModal.jsx
// Description: Modal dialog for editing document title, subject, and document type.
// Created At: 2026-09-12
// Created By: Tam Khang
// Updated At: 2026-11-03
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { X, Edit3, Save, ChevronDown, BookOpen, Layers, Check } from 'lucide-react';
import { subjectsApi } from '../../services/api';
import './EditDocumentModal.css';

const DEFAULT_SUBJECTS = [
  { key: 'math', name: 'Toán học' },
  { key: 'physics', name: 'Vật lý' },
  { key: 'chemistry', name: 'Hóa học' },
  { key: 'biology', name: 'Sinh học' },
  { key: 'history', name: 'Lịch sử' },
  { key: 'english', name: 'Tiếng Anh' },
  { key: 'it', name: 'Tin học' },
];

const DOCUMENT_TYPES = [
  { value: 'lecture', label: 'Bài giảng' },
  { value: 'exam', label: 'Đề kiểm tra' },
  { value: 'reference', label: 'Tài liệu tham khảo' },
];

export default function EditDocumentModal({ isOpen, doc, onClose, onSave }) {
  if (!isOpen || !doc) return null;

  const [title, setTitle] = useState(doc.title || '');
  const [selectedSubjectKey, setSelectedSubjectKey] = useState(doc.subject || 'math');
  const [selectedSubjectId, setSelectedSubjectId] = useState(doc.subject_id || doc.subjectId || null);
  const [docType, setDocType] = useState(doc.document_type || doc.documentType || 'reference');
  const [availableSubjects, setAvailableSubjects] = useState(DEFAULT_SUBJECTS);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch subjects from backend if available
  useEffect(() => {
    let isMounted = true;
    async function loadSubjects() {
      try {
        const res = await subjectsApi.getSubjects();
        if (isMounted && Array.isArray(res) && res.length > 0) {
          const mapped = res.map((s) => ({
            id: s.subject_id,
            name: s.subject_name,
            key: s.subject_name.toLowerCase(),
          }));
          setAvailableSubjects(mapped);

          // Match current subject by ID or name
          const matched = mapped.find(
            (s) => s.id === (doc.subject_id || doc.subjectId) ||
                   s.name.toLowerCase() === (doc.subjectName || '').toLowerCase()
          );
          if (matched) {
            setSelectedSubjectId(matched.id);
            setSelectedSubjectKey(matched.key);
          }
        }
      } catch {
        // ACAD_SUBJECT_VIEW permission may not be available for all roles; fallback to defaults
      }
    }
    loadSubjects();
    return () => {
      isMounted = false;
    };
  }, [doc]);

  // Sync state whenever doc prop updates
  useEffect(() => {
    if (doc) {
      setTitle(doc.title || '');
      setSelectedSubjectKey(doc.subject || 'math');
      setSelectedSubjectId(doc.subject_id || doc.subjectId || null);
      setDocType(doc.document_type || doc.documentType || 'reference');
      setErrorMessage('');
    }
  }, [doc]);

  const handleSubjectChange = (e) => {
    const value = e.target.value;
    const found = availableSubjects.find((s) => (s.id ? s.id === value : s.key === value));
    if (found) {
      setSelectedSubjectId(found.id || null);
      setSelectedSubjectKey(found.key || found.name.toLowerCase());
    } else {
      setSelectedSubjectKey(value);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || title.trim().length < 3) {
      setErrorMessage('Tên tài liệu phải có ít nhất 3 ký tự.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    const matchedSubject = availableSubjects.find(
      (s) => (s.id && s.id === selectedSubjectId) || s.key === selectedSubjectKey
    );
    const subjectName = matchedSubject ? matchedSubject.name : (doc.subjectName || 'Chung');

    try {
      await onSave({
        ...doc,
        title: title.trim(),
        subject_id: selectedSubjectId,
        subjectId: selectedSubjectId,
        subjectName: subjectName,
        subject: selectedSubjectKey,
        folder: `${subjectName} ${doc.grade || '12'}`.trim(),
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
    <div className="modal-backdrop-overlay" onClick={onClose}>
      <div className="edit-doc-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <header className="edit-doc-modal-header">
          <div className="edit-doc-header-title">
            <div className="edit-doc-icon-badge">
              <Edit3 size={18} />
            </div>
            <div>
              <h3 className="modal-title">Chỉnh sửa thông tin tài liệu</h3>
              <p className="modal-subtitle">Chỉnh sửa tên, môn học và phân loại tài liệu</p>
            </div>
          </div>
          <button
            type="button"
            className="btn-modal-close"
            onClick={onClose}
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

          {/* Form Row: Môn học & Loại tài liệu */}
          <div className="edit-form-grid">
            {/* Field 2: Môn học */}
            <div className="edit-form-field">
              <label className="edit-field-label">
                <span>Môn học</span>
              </label>
              <div className="edit-select-wrapper">
                <select
                  className="edit-field-select"
                  value={selectedSubjectId || selectedSubjectKey}
                  onChange={handleSubjectChange}
                >
                  {availableSubjects.map((s) => (
                    <option key={s.id || s.key} value={s.id || s.key}>
                      {s.name}
                    </option>
                  ))}
                </select>
                <ChevronDown size={16} className="select-dropdown-chevron" />
              </div>
            </div>

            {/* Field 3: Loại tài liệu */}
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
              onClick={onClose}
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
