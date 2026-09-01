// File Name: AddStudentModal.jsx
// Description: Modal for adding a new student to the homeroom class roster with full demographic and contact fields.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState } from 'react';
import { X, ChevronDown } from 'lucide-react';
import './AddStudentModal.css';

export default function AddStudentModal({ isOpen, onClose, onAddStudent, nextStudentCode }) {
  const [formData, setFormData] = useState({
    name: '',
    code: nextStudentCode || 'HS2023046',
    dateOfBirth: '',
    gender: '',
    phone: '',
    address: '',
  });

  const [errors, setErrors] = useState({});

  const validatePhoneNumber = (phone) => {
    if (!phone || !phone.trim()) return '';
    const cleaned = phone.replace(/[\s.-]/g, '');
    const phoneRegex = /^(0|\+84)(3[2-9]|5[6|8|9]|7[0|6-9]|8[0-6|8|9]|9[0-4|6-9])[0-9]{7}$/;
    if (!phoneRegex.test(cleaned)) {
      return 'Số điện thoại không hợp lệ (10 số, bắt đầu bằng 03, 05, 07, 08, 09 hoặc +84)';
    }
    return '';
  };

  if (!isOpen) return null;

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handlePhoneChange = (e) => {
    const rawVal = e.target.value;
    if (/^[0-9+\s-]*$/.test(rawVal)) {
      handleChange('phone', rawVal);
      if (rawVal.trim()) {
        const error = validatePhoneNumber(rawVal);
        setErrors(prev => ({ ...prev, phone: error || null }));
      } else {
        setErrors(prev => ({ ...prev, phone: null }));
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Vui lòng nhập họ và tên học sinh';
    }
    if (!formData.code.trim()) {
      newErrors.code = 'Vui lòng nhập mã học sinh';
    }
    if (formData.phone && formData.phone.trim()) {
      const phoneError = validatePhoneNumber(formData.phone);
      if (phoneError) {
        newErrors.phone = phoneError;
      }
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Generate initials & color
    const nameParts = formData.name.trim().split(' ');
    const initials = nameParts.length >= 2
      ? (nameParts[nameParts.length - 2][0] + nameParts[nameParts.length - 1][0]).toUpperCase()
      : formData.name.substring(0, 2).toUpperCase();

    const avatarColors = ['#10B981', '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#6366F1'];
    const randomColor = avatarColors[Math.floor(Math.random() * avatarColors.length)];

    const newStudent = {
      id: Date.now(),
      code: formData.code.trim(),
      name: formData.name.trim(),
      initials,
      avatarColor: randomColor,
      avgScore: 8.0,
      status: 'good',
      statusLabel: 'Tốt',
      gender: formData.gender || 'Nam',
      dateOfBirth: formData.dateOfBirth || '2006-05-15',
      phone: formData.phone || '',
      address: formData.address || '',
      subjectScores: {
        math: 8.0,
        physics: 8.0,
        chemistry: 8.0,
        literature: 8.0,
        english: 8.0,
        biology: 8.0,
        history: 8.0,
        informatics: 8.0,
      }
    };

    onAddStudent(newStudent);
    onClose();
  };

  return (
    <div className="add-student-modal-overlay" onClick={onClose}>
      <div className="add-student-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="add-student-modal-header">
          <h2 className="add-student-modal-title">Thêm học sinh mới</h2>
          <button 
            type="button" 
            className="add-student-btn-close" 
            onClick={onClose}
            title="Đóng"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Form Body */}
        <form onSubmit={handleSubmit} className="add-student-modal-form">
          <div className="add-student-form-body">
            {/* Full Name */}
            <div className="add-student-form-group full-width">
              <label className="add-student-label">Họ và tên</label>
              <input 
                type="text" 
                className={`add-student-input ${errors.name ? 'input-error' : ''}`}
                placeholder="Nhập họ và tên học sinh"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                autoFocus
              />
              {errors.name && <span className="add-student-error-text">{errors.name}</span>}
            </div>

            {/* Code and Date of Birth */}
            <div className="add-student-form-row">
              <div className="add-student-form-group">
                <label className="add-student-label">Mã học sinh</label>
                <input 
                  type="text" 
                  className={`add-student-input add-student-code-input ${errors.code ? 'input-error' : ''}`}
                  placeholder="HS2023046"
                  value={formData.code}
                  onChange={(e) => handleChange('code', e.target.value)}
                />
                {errors.code && <span className="add-student-error-text">{errors.code}</span>}
              </div>

              <div className="add-student-form-group">
                <label className="add-student-label">Ngày sinh</label>
                <input 
                  type="date" 
                  className="add-student-input"
                  value={formData.dateOfBirth}
                  onChange={(e) => handleChange('dateOfBirth', e.target.value)}
                />
              </div>
            </div>

            {/* Gender and Phone */}
            <div className="add-student-form-row">
              <div className="add-student-form-group">
                <label className="add-student-label">Giới tính</label>
                <div className="add-student-select-wrapper">
                  <select 
                    className="add-student-select"
                    value={formData.gender}
                    onChange={(e) => handleChange('gender', e.target.value)}
                  >
                    <option value="">Chọn giới tính</option>
                    <option value="Nam">Nam</option>
                    <option value="Nữ">Nữ</option>
                    <option value="Khác">Khác</option>
                  </select>
                  <ChevronDown size={16} className="add-student-select-arrow" />
                </div>
              </div>

              <div className="add-student-form-group">
                <label className="add-student-label">Số điện thoại</label>
                <input 
                  type="tel" 
                  className={`add-student-input ${errors.phone ? 'input-error' : ''}`}
                  placeholder="Nhập số điện thoại (vd: 0912345678)"
                  value={formData.phone}
                  onChange={handlePhoneChange}
                  maxLength={15}
                />
                {errors.phone && <span className="add-student-error-text">{errors.phone}</span>}
              </div>
            </div>

            {/* Address */}
            <div className="add-student-form-group full-width">
              <label className="add-student-label">Địa chỉ</label>
              <textarea 
                className="add-student-textarea"
                rows="3"
                placeholder="Nhập địa chỉ thường trú"
                value={formData.address}
                onChange={(e) => handleChange('address', e.target.value)}
              ></textarea>
            </div>
          </div>

          {/* Modal Footer */}
          <div className="add-student-modal-footer">
            <button 
              type="button" 
              className="add-student-btn-cancel" 
              onClick={onClose}
            >
              Hủy bỏ
            </button>
            <button 
              type="submit" 
              className="add-student-btn-submit"
            >
              Lưu thông tin
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
