// File Name: ExerciseFilterBar.jsx
// Description: Multi-criteria filter and search bar for Exercise Repository.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-11-11
// Updated By: Tam Khang

import React from 'react';
import { Search, ChevronDown } from 'lucide-react';
import './ExerciseFilterBar.css';

export default function ExerciseFilterBar({
  selectedGrade,
  onChangeGrade,
  selectedType,
  onChangeType,
  searchQuery,
  onChangeSearch,
}) {
  return (
    <div className="exercise-filter-bar">
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

      {/* Filter 2: Loại bài tập */}
      <div className="filter-field-group">
        <label className="filter-field-label">Loại bài tập</label>
        <div className="select-container">
          <select 
            value={selectedType} 
            onChange={(e) => onChangeType(e.target.value)}
            className="filter-select"
          >
            <option value="all">Tất cả loại</option>
            <option value="quiz">Kiểm tra 15p / Trắc nghiệm</option>
            <option value="test">Kiểm tra học kỳ / Đề thi</option>
            <option value="homework">Bài tập về nhà tự luận</option>
            <option value="review">Đề cương ôn tập tổng hợp</option>
          </select>
          <ChevronDown size={16} className="select-arrow-icon" />
        </div>
      </div>

      {/* Filter 3: Ô tìm kiếm bài tập */}
      <div className="filter-field-group search-field-group">
        <label className="filter-field-label" style={{ visibility: 'hidden' }}>Tìm kiếm</label>
        <div className="search-input-container">
          <Search size={16} className="search-input-icon" />
          <input
            type="text"
            placeholder="Tìm kiếm bài tập..."
            value={searchQuery}
            onChange={(e) => onChangeSearch(e.target.value)}
            className="exercise-search-input"
          />
        </div>
      </div>
    </div>
  );
}
