// File Name: DocumentFilterBar.jsx
// Description: Multi-filter and search bar component for Document Repository.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React from 'react';
import { Search, ChevronDown } from 'lucide-react';
import './DocumentFilterBar.css';

export default function DocumentFilterBar({
  selectedGrade,
  onChangeGrade,
  selectedSubject,
  onChangeSubject,
  selectedType,
  onChangeType,
  searchQuery,
  onChangeSearch,
}) {
  return (
    <div className="document-filter-bar">
      {/* Filter 1: Khối lớp */}
      <div className="filter-field-group">
        <label className="filter-field-label">Khối lớp</label>
        <div className="select-container">
          <select 
            value={selectedGrade} 
            onChange={(e) => onChangeGrade(e.target.value)}
            className="filter-select"
          >
            <option value="all">Tất cả khối lớp</option>
            <option value="10">Khối 10</option>
            <option value="11">Khối 11</option>
            <option value="12">Khối 12</option>
          </select>
          <ChevronDown size={16} className="select-arrow-icon" />
        </div>
      </div>

      {/* Filter 2: Môn học */}
      <div className="filter-field-group">
        <label className="filter-field-label">Môn học</label>
        <div className="select-container">
          <select 
            value={selectedSubject} 
            onChange={(e) => onChangeSubject(e.target.value)}
            className="filter-select"
          >
            <option value="all">Tất cả môn học</option>
            <option value="math">Toán học</option>
            <option value="physics">Vật lý</option>
            <option value="chemistry">Hóa học</option>
            <option value="english">Tiếng Anh</option>
            <option value="it">Tin học</option>
            <option value="history">Lịch sử</option>
          </select>
          <ChevronDown size={16} className="select-arrow-icon" />
        </div>
      </div>

      {/* Filter 3: Loại tài liệu */}
      <div className="filter-field-group">
        <label className="filter-field-label">Loại tài liệu</label>
        <div className="select-container">
          <select 
            value={selectedType} 
            onChange={(e) => onChangeType(e.target.value)}
            className="filter-select"
          >
            <option value="all">Tất cả loại</option>
            <option value="pdf">Tài liệu PDF / Đề thi</option>
            <option value="video">Video bài giảng</option>
            <option value="word">Bài tập Word / Văn bản</option>
            <option value="exercise">Bài tập chuyên đề</option>
            <option value="code">Mã nguồn / Thực hành</option>
          </select>
          <ChevronDown size={16} className="select-arrow-icon" />
        </div>
      </div>

      {/* Filter 4: Ô tìm kiếm tài liệu */}
      <div className="filter-field-group search-field-group">
        <label className="filter-field-label" style={{ visibility: 'hidden' }}>Tìm kiếm</label>
        <div className="search-input-container">
          <Search size={16} className="search-input-icon" />
          <input
            type="text"
            placeholder="Tìm kiếm tài liệu..."
            value={searchQuery}
            onChange={(e) => onChangeSearch(e.target.value)}
            className="doc-search-input"
          />
        </div>
      </div>
    </div>
  );
}
