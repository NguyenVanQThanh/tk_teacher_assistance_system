// File Name: UploadDocumentModal.jsx
// Description: Modal dialog for uploading new educational materials and documents.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-27
// Updated By: Tam Khang

import React, { useState } from 'react';
import { X, UploadCloud, File, CheckCircle2, AlertCircle } from 'lucide-react';
import './UploadDocumentModal.css';

export default function UploadDocumentModal({ isOpen, onClose, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [grade, setGrade] = useState('12');
  const [subject, setSubject] = useState('math');
  const [docType, setDocType] = useState('lecture');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      if (!title) {
        setTitle(droppedFile.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg('Vui lòng chọn tập tin tài liệu cần tải lên.');
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setErrorMsg('Dung lượng tập tin vượt quá giới hạn 50MB.');
      return;
    }
    if (!title.trim()) {
      setErrorMsg('Vui lòng nhập tên tài liệu.');
      return;
    }

    setIsUploading(true);
    setErrorMsg('');

    // Simulate upload
    setTimeout(() => {
      setIsUploading(false);
      const newDoc = {
        id: Date.now(),
        title: title.trim(),
        fileSize: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        uploadDate: new Date().toLocaleDateString('vi-VN'),
        fileType: docType,
        grade: grade,
        subject: subject,
        authorName: 'GV. Sample Teacher',
        authorInitial: 'ST',
      };
      if (onUploadSuccess) {
        onUploadSuccess(newDoc);
      }
      onClose();
    }, 600);
  };

  return (
    <div className="modal-backdrop-overlay" onClick={onClose}>
      <div className="upload-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="upload-modal-header">
          <div className="header-title-box">
            <div className="upload-icon-box">
              <UploadCloud size={20} />
            </div>
            <h3 className="modal-title">Tải lên tài liệu mới</h3>
          </div>
          <button type="button" className="btn-modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="upload-modal-body">
          {errorMsg && (
            <div className="modal-alert-error">
              <AlertCircle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Drag & Drop File Zone */}
          <div
            className={`file-drop-zone ${isDragging ? 'is-dragging' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-input-upload"
              className="hidden-file-input"
              onChange={handleFileChange}
              accept=".pdf,.doc,.docx,.xlsx"
            />
            <label htmlFor="file-input-upload" className="drop-zone-label">
              {file ? (
                <div className="file-selected-preview">
                  <File size={32} className="selected-file-icon" />
                  <div className="selected-file-info">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                  </div>
                  <span className="change-file-tag">Đổi file</span>
                </div>
              ) : (
                <>
                  <UploadCloud size={38} className="cloud-drop-icon" />
                  <p className="drop-main-text">
                    Kéo thả tập tin vào đây hoặc <span className="browse-link">Chọn từ máy tính</span>
                  </p>
                  <p className="drop-sub-text">Hỗ trợ: PDF, Word (DOC/DOCX), Excel (XLSX) (Tối đa 50MB)</p>
                </>
              )}
            </label>
          </div>

          {/* Form Field: Tên tài liệu */}
          <div className="modal-form-group">
            <label className="modal-form-label">Tên tài liệu *</label>
            <input
              type="text"
              className="modal-form-input"
              placeholder="Nhập tên tài liệu chi tiết..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          {/* Form Row: Khối lớp & Môn học & Định dạng */}
          <div className="modal-form-row">
            <div className="modal-form-group">
              <label className="modal-form-label">Khối lớp</label>
              <select 
                className="modal-form-select"
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
              >
                <option value="10">Khối 10</option>
                <option value="11">Khối 11</option>
                <option value="12">Khối 12</option>
              </select>
            </div>

            <div className="modal-form-group">
              <label className="modal-form-label">Môn học</label>
              <select 
                className="modal-form-select"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              >
                <option value="math">Toán học</option>
                <option value="physics">Vật lý</option>
                <option value="chemistry">Hóa học</option>
                <option value="biology">Sinh học</option>
                <option value="history">Lịch sử</option>
                <option value="english">Tiếng Anh</option>
                <option value="it">Tin học</option>
              </select>
            </div>

            <div className="modal-form-group">
              <label className="modal-form-label">Loại tài liệu</label>
              <select 
                className="modal-form-select"
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
              >
                <option value="lecture">Bài giảng</option>
                <option value="exam">Đề kiểm tra</option>
                <option value="reference">Tài liệu tham khảo</option>
              </select>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="upload-modal-footer">
            <button type="button" className="btn-modal-cancel" onClick={onClose}>
              Hủy bỏ
            </button>
            <button type="submit" className="btn-modal-submit" disabled={isUploading}>
              {isUploading ? (
                <span>Đang tải lên...</span>
              ) : (
                <>
                  <UploadCloud size={16} />
                  <span>Tải lên ngay</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
