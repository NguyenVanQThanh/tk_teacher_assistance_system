// File Name: StudentTranscriptPrintModal.jsx
// Description: Printable A4 portrait student semester report card modal conforming to Ministry of Education guidelines with 4 assessment sections, subject remarks column, conduct & academic evaluations, and school signatures.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React from 'react';
import { X, Printer, Download } from 'lucide-react';
import './StudentTranscriptPrintModal.css';

export default function StudentTranscriptPrintModal({ 
  isOpen, 
  onClose, 
  student, 
  classInfo 
}) {
  if (!isOpen || !student) return null;

  const handlePrint = () => {
    window.print();
  };

  const className = classInfo?.name?.split(' - ')[0] || '12A1';
  const schoolName = 'TRƯỜNG THPT NGUYỄN THƯỢNG HIỀN';
  const academicYear = '2023 – 2024';

  // 13 standard subjects list with detailed scores matching Vietnam curriculum
  const transcriptSubjects = [
    { tt: 1, name: 'TOÁN', mieng: '10', tx1: '10.0', tx2: '10.0', tx3: '10.0', tx4: '9.5', gk: '10.0', ck: '10.0', tbm: '9.9', note: '' },
    { tt: 2, name: 'VẬT LÝ', mieng: '10', tx1: '10.0', tx2: '10.0', tx3: '9.0', tx4: '9.0', gk: '8.7', ck: '9.0', tbm: '9.3', note: '' },
    { tt: 3, name: 'HOÁ HỌC', mieng: '10', tx1: '9.5', tx2: '10.0', tx3: '10.0', tx4: '9.5', gk: '10.0', ck: '9.8', tbm: '9.8', note: '' },
    { tt: 4, name: 'SINH HỌC', mieng: '10', tx1: '10.0', tx2: '9.5', tx3: '9.0', tx4: '9.0', gk: '9.5', ck: '8.8', tbm: '9.4', note: '' },
    { tt: 5, name: 'TIN HỌC', mieng: '10', tx1: '10.0', tx2: '10.0', tx3: '10.0', tx4: '10.0', gk: '10.0', ck: '10.0', tbm: '10.0', note: '' },
    { tt: 6, name: 'NGỮ VĂN', mieng: '10', tx1: '10.0', tx2: '10.0', tx3: '10.0', tx4: '8.5', gk: '9.5', ck: '9.3', tbm: '9.4', note: '' },
    { tt: 7, name: 'LỊCH SỬ', mieng: '10', tx1: '9.0', tx2: '9.0', tx3: '9.5', tx4: '9.0', gk: '9.3', ck: '9.8', tbm: '9.5', note: '' },
    { tt: 8, name: 'ĐỊA LÝ', mieng: '9', tx1: '9.0', tx2: '8.5', tx3: '9.0', tx4: '8.5', gk: '9.8', ck: '8.3', tbm: '8.9', note: '' },
    { tt: 9, name: 'NGOẠI NGỮ', mieng: '10', tx1: '9.7', tx2: '9.7', tx3: '9.0', tx4: '9.5', gk: '9.8', ck: '9.8', tbm: '9.7', note: '' },
    { tt: 10, name: 'GDCD', mieng: '10', tx1: '9.0', tx2: '9.5', tx3: '9.0', tx4: '9.5', gk: '9.5', ck: '9.5', tbm: '9.5', note: '' },
    { tt: 11, name: 'CÔNG NGHỆ', mieng: '9', tx1: '10.0', tx2: '10.0', tx3: '10.0', tx4: '9.5', gk: '10.0', ck: '10.0', tbm: '9.9', note: '' },
    { tt: 12, name: 'THỂ DỤC', mieng: 'Đ', tx1: 'Đ', tx2: 'Đ', tx3: 'Đ', tx4: 'Đ', gk: 'Đ', ck: 'Đ', tbm: 'Đ', note: '' },
    { tt: 13, name: 'GD QP-AN', mieng: '10', tx1: '10.0', tx2: '10.0', tx3: '10.0', tx4: '9.5', gk: '9.0', ck: '10.0', tbm: '9.8', note: '' },
  ];

  return (
    <div className="transcript-print-overlay" onClick={onClose}>
      <div className="transcript-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Floating Modal Action Bar (Hidden when printing) */}
        <div className="transcript-toolbar-bar no-print">
          <div className="toolbar-left-info">
            <span className="toolbar-doc-title">Phiếu điểm học kỳ A4 • Xem trước khi in</span>
            <span className="toolbar-student-tag">{student.name} ({student.code})</span>
          </div>
          <div className="toolbar-right-actions">
            <button 
              type="button" 
              className="btn-toolbar-print" 
              onClick={handlePrint}
            >
              <Printer size={16} />
              <span>In phiếu điểm (A4)</span>
            </button>
            <button 
              type="button" 
              className="btn-toolbar-close" 
              onClick={onClose}
              title="Đóng xem trước"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* The Printable A4 Sheet Paper */}
        <div className="a4-sheet-wrapper">
          <div className="a4-paper-sheet printable-document" id="printable-transcript-page">
            {/* Header: School & Title */}
            <div className="a4-school-header">
              <div className="school-org-name">{schoolName}</div>
              <div className="sheet-main-title">PHIẾU ĐIỂM HỌC KỲ 1</div>
              <div className="sheet-sub-title">Năm học: {academicYear}</div>
            </div>

            {/* Section 1: Student Information (Phần 1) */}
            <div className="a4-section-student-info">
              <div className="info-grid-row">
                <div className="info-item">
                  <span className="info-lbl">Họ và tên:</span>
                  <span className="info-val font-bold text-uppercase">{student.name}</span>
                </div>
                <div className="info-item">
                  <span className="info-lbl">Giới tính:</span>
                  <span className="info-val">{student.gender || 'Nam'}</span>
                </div>
              </div>
              <div className="info-grid-row">
                <div className="info-item">
                  <span className="info-lbl">Mã Học sinh:</span>
                  <span className="info-val font-bold">{student.code}</span>
                </div>
                <div className="info-item">
                  <span className="info-lbl">Lớp học:</span>
                  <span className="info-val font-bold">{className}</span>
                </div>
              </div>
            </div>

            {/* Section 2: Academic Results Table with Blank Remarks Column (Phần 2) */}
            <div className="a4-section-table-results">
              <div className="table-heading-banner">KẾT QUẢ HỌC TẬP</div>

              <table className="a4-transcript-table">
                <thead>
                  <tr>
                    <th rowSpan="2" className="th-col-tt">TT</th>
                    <th rowSpan="2" className="th-col-subj">MÔN HỌC</th>
                    <th colSpan="5" className="th-group-hs1">HỆ SỐ 1</th>
                    <th className="th-group-hs2">HỆ SỐ 2</th>
                    <th rowSpan="2" className="th-col-kthk">KT HK</th>
                    <th rowSpan="2" className="th-col-tbm">TB Môn</th>
                    <th rowSpan="2" className="th-col-note">NHẬN XÉT CỦA GIÁO VIÊN BỘ MÔN</th>
                  </tr>
                  <tr>
                    <th className="th-sub-m">MIỆNG</th>
                    <th colSpan="4" className="th-sub-15p">15 PHÚT (TX)</th>
                    <th className="th-sub-1t">GIỮA KỲ</th>
                  </tr>
                </thead>
                <tbody>
                  {transcriptSubjects.map((sub) => (
                    <tr key={sub.tt} className="tr-subject-row">
                      <td className="td-tt">{sub.tt}</td>
                      <td className="td-subj-name">{sub.name}</td>
                      <td className="td-score">{sub.mieng}</td>
                      <td className="td-score">{sub.tx1}</td>
                      <td className="td-score">{sub.tx2}</td>
                      <td className="td-score">{sub.tx3}</td>
                      <td className="td-score">{sub.tx4}</td>
                      <td className="td-score">{sub.gk}</td>
                      <td className="td-score">{sub.ck}</td>
                      <td className="td-score td-tbm-bold">{sub.tbm}</td>
                      <td className="td-blank-note">{/* Chừa trống để giáo viên nhận xét */}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Section 3: Evaluation, Conduct, Rank & Teacher Remarks (Phần 3) */}
            <div className="a4-section-summary-evaluation">
              <div className="summary-left-stats">
                <div className="stat-line">
                  <span className="stat-lbl">Điểm TBCM:</span>
                  <span className="stat-val font-bold">{student.avgScore ? student.avgScore.toFixed(1) : '9.6'}</span>
                </div>
                <div className="stat-line">
                  <span className="stat-lbl">Học lực:</span>
                  <span className="stat-val font-bold">Giỏi</span>
                </div>
                <div className="stat-line">
                  <span className="stat-lbl">Hạnh kiểm:</span>
                  <span className="stat-val font-bold">TỐT</span>
                </div>
                <div className="stat-line">
                  <span className="stat-lbl">Danh hiệu:</span>
                  <span className="stat-val font-bold">HỌC SINH GIỎI</span>
                </div>
                <div className="stat-line">
                  <span className="stat-lbl">Thứ hạng:</span>
                  <span className="stat-val font-bold">1 / 45</span>
                </div>
                <div className="stat-line stat-attendance">
                  <span className="stat-lbl">Chuyên cần:</span>
                  <span className="stat-val">Nghỉ có phép: <strong>0</strong> / K.phép: <strong>0</strong> / Trễ học: <strong>0</strong></span>
                </div>
              </div>

              <div className="summary-right-remarks">
                <div className="remarks-box-title">Nhận xét của giáo viên chủ nhiệm:</div>
                <div className="remarks-blank-space">{/* Chừa trống để giáo viên ghi nhận xét bằng tay */}</div>
              </div>
            </div>

            {/* Section 4: Signatures & Validations (Phần 4) */}
            <div className="a4-section-signatures">
              <div className="signature-date-row">
                <em>Ngày ...... tháng ...... năm 2024</em>
              </div>
              <div className="signatures-grid">
                {/* Giáo viên chủ nhiệm on Left */}
                <div className="signature-col sig-homeroom">
                  <div className="sig-role">GIÁO VIÊN CHỦ NHIỆM</div>
                  <div className="sig-sub-role">(Ký và ghi rõ họ tên)</div>
                  <div className="sig-space"></div>
                </div>

                {/* Xác nhận của nhà trường on Right */}
                <div className="signature-col sig-school">
                  <div className="sig-role">XÁC NHẬN CỦA NHÀ TRƯỜNG</div>
                  <div className="sig-sub-role">HIỆU TRƯỞNG</div>
                  <div className="sig-space"></div>
                  <div className="sig-instruction">(Ký và đóng dấu)</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
