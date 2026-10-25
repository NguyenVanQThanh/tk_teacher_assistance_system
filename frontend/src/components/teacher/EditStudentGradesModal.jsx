// File Name: EditStudentGradesModal.jsx
// Description: Dedicated modal for editing student gradebook scores across all subjects with 4 regular assessment columns (TX1, TX2, TX3, TX4), Midterm, Final, and live GPA calculation.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { X, Save, Check, CheckCircle2 } from 'lucide-react';
import './EditStudentGradesModal.css';

export default function EditStudentGradesModal({ isOpen, onClose, student, onSave }) {
  const defaultSubjectsGrades = [
    { id: 'math', name: 'Toán học', tx1: 8.5, tx2: 9.0, tx3: 8.8, tx4: 9.2, gk: 9.5, ck: 8.7, tbm: 9.0, final: 9.2, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'physics', name: 'Vật lý', tx1: 8.0, tx2: 8.5, tx3: 8.5, tx4: 9.0, gk: 9.0, ck: 8.8, tbm: 8.7, final: 8.8, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'chemistry', name: 'Hóa học', tx1: 8.0, tx2: 8.2, tx3: 8.5, tx4: 8.0, gk: 8.5, ck: 8.6, tbm: 8.4, final: 8.5, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'english', name: 'Tiếng Anh', tx1: 9.0, tx2: 9.5, tx3: 9.2, tx4: 9.0, gk: 9.6, ck: 9.4, tbm: 9.3, final: 9.4, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'literature', name: 'Ngữ văn', tx1: 7.5, tx2: 8.0, tx3: 7.8, tx4: 8.0, gk: 8.2, ck: 8.5, tbm: 8.1, final: 8.2, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'biology', name: 'Sinh học', tx1: 8.0, tx2: 8.0, tx3: 8.2, tx4: 8.0, gk: 8.4, ck: 8.2, tbm: 8.2, final: 8.2, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'history', name: 'Lịch sử', tx1: 8.5, tx2: 8.5, tx3: 8.5, tx4: 8.6, gk: 8.6, ck: 8.8, tbm: 8.6, final: 8.7, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'informatics', name: 'Tin học', tx1: 9.5, tx2: 9.5, tx3: 9.5, tx4: 9.6, gk: 9.8, ck: 9.5, tbm: 9.6, final: 9.6, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'geography', name: 'Địa lý', tx1: 7.0, tx2: 7.5, tx3: 7.5, tx4: 8.0, gk: 8.0, ck: 7.8, tbm: 7.7, final: 7.8, rating: 'Đạt chuẩn khá', ratingCode: 'good' },
    { id: 'civics', name: 'GDCD', tx1: 9.0, tx2: 9.0, tx3: 9.0, tx4: 9.2, gk: 9.2, ck: 9.0, tbm: 9.1, final: 9.1, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
  ];

  const [gradesTable, setGradesTable] = useState(defaultSubjectsGrades);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (student) {
      if (student.gradesTable && student.gradesTable.length > 0) {
        setGradesTable(student.gradesTable);
      } else {
        const initialGrades = defaultSubjectsGrades.map(g => {
          const studentSubScore = student.subjectScores?.[g.id];
          if (studentSubScore !== undefined) {
            const diff = studentSubScore - g.final;
            const newTx1 = Math.min(10, Math.max(0, parseFloat((g.tx1 + diff * 0.8).toFixed(1))));
            const newTx2 = Math.min(10, Math.max(0, parseFloat((g.tx2 + diff * 0.8).toFixed(1))));
            const newTx3 = Math.min(10, Math.max(0, parseFloat((g.tx3 + diff * 0.8).toFixed(1))));
            const newTx4 = Math.min(10, Math.max(0, parseFloat((g.tx4 + diff * 0.8).toFixed(1))));
            const newGk = Math.min(10, Math.max(0, parseFloat((g.gk + diff * 0.9).toFixed(1))));
            const newCk = Math.min(10, Math.max(0, parseFloat((g.ck + diff * 0.9).toFixed(1))));
            const newTbm = parseFloat(((newTx1 + newTx2 + newTx3 + newTx4 + newGk * 2 + newCk * 3) / 9).toFixed(1));
            return {
              ...g,
              tx1: newTx1,
              tx2: newTx2,
              tx3: newTx3,
              tx4: newTx4,
              gk: newGk,
              ck: newCk,
              tbm: newTbm,
              final: studentSubScore,
              rating: studentSubScore >= 8.0 ? 'Đạt chuẩn giỏi' : studentSubScore >= 6.5 ? 'Đạt chuẩn khá' : 'Đạt chuẩn TB',
              ratingCode: studentSubScore >= 8.0 ? 'excellent' : 'good'
            };
          }
          return g;
        });
        setGradesTable(initialGrades);
      }
      setSavedSuccess(false);
    }
  }, [student]);

  if (!isOpen || !student) return null;

  const handleCellChange = (subjectId, field, rawValue) => {
    const numVal = parseFloat(rawValue);
    const validVal = isNaN(numVal) ? 0 : Math.min(10, Math.max(0, numVal));

    setGradesTable(prev => prev.map(row => {
      if (row.id === subjectId) {
        const updatedRow = { ...row, [field]: validVal };
        // Formula: TBM = (TX1 + TX2 + TX3 + TX4 + GK*2 + CK*3) / 9
        const tbmCalc = parseFloat((
          (updatedRow.tx1 + updatedRow.tx2 + updatedRow.tx3 + updatedRow.tx4 + updatedRow.gk * 2 + updatedRow.ck * 3) / 9
        ).toFixed(1));

        updatedRow.tbm = tbmCalc;
        updatedRow.final = tbmCalc;
        updatedRow.rating = tbmCalc >= 8.0 ? 'Đạt chuẩn giỏi' : tbmCalc >= 6.5 ? 'Đạt chuẩn khá' : 'Đạt chuẩn TB';
        updatedRow.ratingCode = tbmCalc >= 8.0 ? 'excellent' : tbmCalc >= 6.5 ? 'good' : 'fair';
        return updatedRow;
      }
      return row;
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const newSubjectScores = {};
    gradesTable.forEach(row => {
      newSubjectScores[row.id] = row.final;
    });

    const finalValues = Object.values(newSubjectScores);
    const newAvg = finalValues.length > 0
      ? parseFloat((finalValues.reduce((sum, v) => sum + v, 0) / finalValues.length).toFixed(1))
      : student.avgScore;

    const updatedStudent = {
      ...student,
      avgScore: newAvg,
      subjectScores: newSubjectScores,
      gradesTable: gradesTable
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
    <div className="edit-grades-overlay" onClick={onClose}>
      <div className="edit-grades-window" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="edit-grades-header">
          <div className="edit-grades-title-group">
            <h2 className="edit-grades-title">Chỉnh sửa bảng điểm học sinh</h2>
            <span className="edit-grades-subtitle">
              {student.name} • Mã HS: {student.code} • Lớp 12A1
            </span>
          </div>
          <button type="button" className="btn-grades-close" onClick={onClose} title="Đóng">
            <X size={18} />
          </button>
        </div>

        {/* Body Content */}
        <form onSubmit={handleSubmit} className="edit-grades-form">
          <div className="edit-grades-body">
            <div className="grades-instruction-card">
              <p className="grades-instruction-text">
                Nhập điểm các đợt <strong>Kiểm tra thường xuyên (TX1 - TX4)</strong>, <strong>Giữa kỳ</strong> và <strong>Cuối kỳ</strong>. Điểm Trung bình môn, Điểm Tổng kết và Đánh giá xếp loại sẽ tự động được tính toán lại.
              </p>
            </div>

            <div className="grades-table-scroll-wrapper">
              <table className="edit-grades-table">
                <thead>
                  <tr>
                    <th className="th-subj-header" rowSpan="2">Môn học</th>
                    <th className="th-regular-header" colSpan="4">Kiểm tra thường xuyên</th>
                    <th className="th-midterm-header" rowSpan="2">Điểm Giữa kỳ</th>
                    <th className="th-final-header" rowSpan="2">Điểm Cuối kỳ</th>
                    <th className="th-tbm-header" rowSpan="2">Điểm TB môn</th>
                    <th className="th-total-header" rowSpan="2">Điểm Tổng kết</th>
                    <th className="th-rating-header" rowSpan="2">Đánh giá</th>
                  </tr>
                  <tr>
                    <th className="th-tx-sub">TX1</th>
                    <th className="th-tx-sub">TX2</th>
                    <th className="th-tx-sub">TX3</th>
                    <th className="th-tx-sub">TX4</th>
                  </tr>
                </thead>
                <tbody>
                  {gradesTable.map((row) => (
                    <tr key={row.id} className="edit-grade-row">
                      <td className="td-subj-cell">
                        <strong>{row.name}</strong>
                      </td>
                      <td>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="10"
                          className="grade-cell-input"
                          value={row.tx1}
                          onChange={(e) => handleCellChange(row.id, 'tx1', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="10"
                          className="grade-cell-input"
                          value={row.tx2}
                          onChange={(e) => handleCellChange(row.id, 'tx2', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="10"
                          className="grade-cell-input"
                          value={row.tx3}
                          onChange={(e) => handleCellChange(row.id, 'tx3', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="10"
                          className="grade-cell-input"
                          value={row.tx4}
                          onChange={(e) => handleCellChange(row.id, 'tx4', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="10"
                          className="grade-cell-input highlight-mid"
                          value={row.gk}
                          onChange={(e) => handleCellChange(row.id, 'gk', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="10"
                          className="grade-cell-input highlight-fin"
                          value={row.ck}
                          onChange={(e) => handleCellChange(row.id, 'ck', e.target.value)}
                        />
                      </td>
                      <td className="td-calc-cell">
                        <span className="grade-pill-purple">
                          {row.tbm.toFixed(1)}
                        </span>
                      </td>
                      <td className="td-calc-cell">
                        <span className="grade-pill-purple bold-total">
                          {row.final.toFixed(1)}
                        </span>
                      </td>
                      <td className="td-rating-cell">
                        <span className={`grade-rating-badge ${row.ratingCode === 'excellent' ? 'rating-good' : 'rating-fair'}`}>
                          <CheckCircle2 size={12} className="badge-icon" />
                          <span>{row.rating}</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="edit-grades-footer">
            <button
              type="button"
              className="btn-grades-cancel"
              onClick={onClose}
            >
              Hủy
            </button>
            <button
              type="submit"
              className={`btn-grades-save ${savedSuccess ? 'saved' : ''}`}
            >
              {savedSuccess ? (
                <>
                  <Check size={16} />
                  <span>Đã lưu bảng điểm!</span>
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
