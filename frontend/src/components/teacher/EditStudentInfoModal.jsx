// File Name: EditStudentInfoModal.jsx
// Description: Dedicated modal for editing student demographic and profile information.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { X, Save, Check } from 'lucide-react';
import './EditStudentInfoModal.css';

export default function EditStudentInfoModal({ isOpen, onClose, student, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    status: 'good',
    statusLabel: 'Tốt',
    dateOfBirth: '15/05/2006',
    gender: 'Nam',
    phone: '0912 345 678',
    address: 'Hà Nội',
  });

  const [savedSuccess, setSavedSuccess] = useState(false);
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

  useEffect(() => {
    if (student) {
      setFormData({
        name: student.name || '',
        code: student.code || '',
        status: student.status || 'good',
        statusLabel: student.statusLabel || 'Tốt',
        dateOfBirth: student.dateOfBirth || '15/05/2006',
        gender: student.gender || 'Nam',
        phone: student.phone || '0912 345 678',
        address: student.address || 'Hà Nội',
      });
      setSavedSuccess(false);
      setErrors({});
    }
  }, [student]);

  if (!isOpen || !student) return null;

  const handleChange = (field, value) => {
    let newStatusLabel = formData.statusLabel;
    if (field === 'status') {
      if (value === 'excellent') newStatusLabel = 'Xuất sắc';
      else if (value === 'good') newStatusLabel = 'Tốt';
      else if (value === 'fair') newStatusLabel = 'Khá';
      else newStatusLabel = 'Trung bình';
    }
    setFormData(prev => ({
      ...prev,
      [field]: value,
      statusLabel: field === 'status' ? newStatusLabel : prev.statusLabel
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
      newErrors.name = 'Vui lòng nhập họ và tên';
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

    const updatedStudent = {
      ...student,
      name: formData.name,
      code: formData.code,
      status: formData.status,
      statusLabel: formData.statusLabel,
      dateOfBirth: formData.dateOfBirth,
      gender: formData.gender,
      phone: formData.phone,
      address: formData.address,
    };

    if (onSave) {
      onSave(updatedStudent);
    }

    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 600);
  };

  return (
    <div className="edit-info-overlay" onClick={onClose}>
      <div className="edit-info-window" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="edit-info-header">
          <div className="edit-info-title-group">
            <h2 className="edit-info-title">Chỉnh sửa thông tin học sinh</h2>
            <span className="edit-info-subtitle">
              {student.name} • Mã HS: {student.code}
            </span>
          </div>
          <button type="button" className="btn-info-close" onClick={onClose} title="Đóng">
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="edit-info-form">
          <div className="edit-info-body">
            <div className="form-row-2">
              <div className="form-group">
                <label className="form-label">Họ và tên <span className="req">*</span></label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="Nhập họ và tên..."
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Mã học sinh <span className="req">*</span></label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.code}
                  onChange={(e) => handleChange('code', e.target.value)}
                  placeholder="HS2023..."
                  required
                />
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label className="form-label">Ngày sinh</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.dateOfBirth}
                  onChange={(e) => handleChange('dateOfBirth', e.target.value)}
                  placeholder="DD/MM/YYYY"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Giới tính</label>
                <select
                  className="form-select"
                  value={formData.gender}
                  onChange={(e) => handleChange('gender', e.target.value)}
                >
                  <option value="Nam">Nam</option>
                  <option value="Nữ">Nữ</option>
                </select>
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label className="form-label">Trạng thái rèn luyện / Học tập</label>
                <select
                  className="form-select"
                  value={formData.status}
                  onChange={(e) => handleChange('status', e.target.value)}
                >
                  <option value="excellent">Xuất sắc</option>
                  <option value="good">Tốt</option>
                  <option value="fair">Khá</option>
                  <option value="average">Trung bình</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Số điện thoại liên lạc</label>
                <input
                  type="tel"
                  className={`form-input ${errors.phone ? 'input-error' : ''}`}
                  value={formData.phone}
                  onChange={handlePhoneChange}
                  placeholder="0912 345 678"
                  maxLength={15}
                />
                {errors.phone && <span className="add-student-error-text">{errors.phone}</span>}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Địa chỉ</label>
              <input
                type="text"
                className="form-input"
                value={formData.address}
                onChange={(e) => handleChange('address', e.target.value)}
                placeholder="Nhập địa chỉ..."
              />
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="edit-info-footer">
            <button
              type="button"
              className="btn-cancel-action"
              onClick={onClose}
            >
              Hủy
            </button>
            <button
              type="submit"
              className={`btn-submit-action ${savedSuccess ? 'saved' : ''}`}
            >
              {savedSuccess ? (
                <>
                  <Check size={16} />
                  <span>Đã lưu thành công!</span>
                </>
              ) : (
                <>
                  <Save size={16} />
                  <span>Lưu thay đổi</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
