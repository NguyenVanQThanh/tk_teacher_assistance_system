// File Name: TeacherClassDetailPage.jsx
// Description: Detailed class view with student roster, average scores, and full-screen student performance analytics modal.
// Created At: 2026-08-31
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { 
  ChevronRight, 
  Search, 
  ArrowLeft
} from 'lucide-react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import StudentDetailModal from '../../components/teacher/StudentDetailModal';
import './TeacherClassDetailPage.css';

export default function TeacherClassDetailPage() {
  const { classId } = useParams();
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchStudent, setSearchStudent] = useState('');
  const [showAll, setShowAll] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const navigate = useNavigate();

  // Class metadata dictionary
  const classesInfo = {
    '12a1': {
      name: '12A1 - Toán nâng cao',
      subjectName: 'Toán học',
      gradeText: 'Khối 12',
      term: 'Kì 1, 2023–2024',
      currentStudents: 45,
      maxStudents: 45,
    },
    '11b2': {
      name: '11B2 - Toán cơ bản',
      subjectName: 'Toán học',
      gradeText: 'Khối 11',
      term: 'Kì 1, 2023–2024',
      currentStudents: 42,
      maxStudents: 45,
    },
    '10a3': {
      name: '10A3 - Toán cơ bản',
      subjectName: 'Toán học',
      gradeText: 'Khối 10',
      term: 'Kì 1, 2023–2024',
      currentStudents: 40,
      maxStudents: 40,
    }
  };

  const currentClass = classesInfo[classId] || {
    name: '12A1 - Toán nâng cao',
    subjectName: 'Toán học',
    gradeText: 'Khối 12',
    term: 'Kì 1, 2023–2024',
    currentStudents: 45,
    maxStudents: 45,
  };

  // Mock student list matching design screenshot
  const initialStudents = [
    { id: 1, name: 'Nguyễn Hoàng Nam', code: 'HS00124', avgScore: 9.2 },
    { id: 2, name: 'Trần Thị Mai Anh', code: 'HS00125', avgScore: 8.8 },
    { id: 3, name: 'Lê Văn Đức', code: 'HS00126', avgScore: 7.5 },
    { id: 4, name: 'Phạm Minh Tuấn', code: 'HS00127', avgScore: 9.5 },
    { id: 5, name: 'Đặng Thu Thảo', code: 'HS00128', avgScore: 8.0 },
    { id: 6, name: 'Vũ Hoàng Long', code: 'HS00129', avgScore: 8.5 },
    { id: 7, name: 'Bùi Phương Linh', code: 'HS00130', avgScore: 9.0 },
    { id: 8, name: 'Hoàng Quốc Bảo', code: 'HS00131', avgScore: 7.8 },
  ];

  const filteredStudents = useMemo(() => {
    let list = initialStudents;
    if (searchStudent.trim()) {
      const q = searchStudent.toLowerCase().trim();
      list = list.filter(
        (s) => s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q)
      );
    }
    return showAll ? list : list.slice(0, 5);
  }, [initialStudents, searchStudent, showAll]);

  return (
    <div className="class-detail-layout">
      {/* Top Header */}
      <Header onToggleSidebar={() => setShowSidebar(!showSidebar)} />

      <div className="class-detail-body">
        {/* Left Sidebar */}
        {showSidebar && (
          <TeacherSidebar 
            activeNav="classes" 
            createButtonText="Tạo lớp học mới"
            onCreateAction={() => alert('Tạo lớp học mới')}
          />
        )}

        {/* Main Content Area */}
        <main className="class-detail-main">
          {/* Breadcrumb & Title Section */}
          <div className="class-detail-header-section">
            <nav className="breadcrumb-nav" aria-label="Breadcrumb">
              <Link to="/teacher" className="breadcrumb-link">Trang chủ</Link>
              <ChevronRight size={14} className="breadcrumb-separator" />
              <Link to="/teacher/classes" className="breadcrumb-link">Lớp học của tôi</Link>
              <ChevronRight size={14} className="breadcrumb-separator" />
              <span className="breadcrumb-current">{currentClass.name}</span>
            </nav>

            <div className="class-detail-title-group">
              <h1 className="class-detail-heading">{currentClass.name}</h1>
              <p className="class-detail-subheading">
                {currentClass.gradeText} • {currentClass.term} • Sĩ số: {currentClass.currentStudents}/{currentClass.maxStudents}
              </p>
            </div>
          </div>

          {/* Student Roster Card */}
          <div className="students-roster-card">
            {/* Card Header */}
            <div className="roster-card-header">
              <h2 className="roster-card-title">Danh sách học sinh</h2>
              <div className="roster-search-box">
                <Search size={16} className="roster-search-icon" />
                <input
                  type="text"
                  className="roster-search-input"
                  placeholder="Tìm học sinh..."
                  value={searchStudent}
                  onChange={(e) => setSearchStudent(e.target.value)}
                />
              </div>
            </div>

            {/* Students Table */}
            <div className="roster-table-container">
              <table className="roster-table">
                <thead>
                  <tr>
                    <th className="th-name">Họ và tên</th>
                    <th className="th-code">Mã học sinh</th>
                    <th className="th-score">Điểm trung bình</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.length > 0 ? (
                    filteredStudents.map((student) => (
                      <tr 
                        key={student.id} 
                        className="roster-row clickable-row"
                        onClick={() => setSelectedStudent(student)}
                        title={`Bấm để xem chi tiết học sinh ${student.name}`}
                      >
                        <td className="td-name">{student.name}</td>
                        <td className="td-code">{student.code}</td>
                        <td className="td-score">
                          <span className="score-badge">{student.avgScore.toFixed(1)}</span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="3" className="empty-roster-row">
                        Không tìm thấy học sinh phù hợp.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Card Footer: Expand all students */}
            <div className="roster-card-footer">
              <button 
                type="button" 
                className="btn-view-all-students"
                onClick={() => setShowAll(!showAll)}
              >
                {showAll ? 'Thu gọn danh sách' : `Xem tất cả ${currentClass.currentStudents} học sinh`}
              </button>
            </div>
          </div>
        </main>
      </div>

      {/* Full-screen Student Performance Analytics Modal */}
      <StudentDetailModal
        isOpen={!!selectedStudent}
        onClose={() => setSelectedStudent(null)}
        student={selectedStudent}
        classInfo={currentClass}
      />
    </div>
  );
}

