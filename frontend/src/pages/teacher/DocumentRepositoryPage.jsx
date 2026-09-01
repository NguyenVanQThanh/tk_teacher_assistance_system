// File Name: DocumentRepositoryPage.jsx
// Description: Teacher Document Repository Page featuring filtering, search, pagination, and upload modal.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { ChevronRight, Upload, ChevronLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import DocumentFilterBar from '../../components/documents/DocumentFilterBar';
import DocumentCard from '../../components/documents/DocumentCard';
import UploadDocumentModal from '../../components/documents/UploadDocumentModal';
import DocumentPreviewModal from '../../components/documents/DocumentPreviewModal';
import CreateExerciseModal from '../../components/exercises/CreateExerciseModal';
import './DocumentRepositoryPage.css';

export default function DocumentRepositoryPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isCreateExerciseOpen, setIsCreateExerciseOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);

  const navigate = useNavigate();

  // Initial mock documents matching Figma design
  const [documents, setDocuments] = useState([
    {
      id: 1,
      title: 'Đề cương ôn tập Toán 12 - Học kì 1 (Nâng cao)',
      fileType: 'pdf',
      fileSize: '2.4 MB',
      uploadDate: '15/10/2023',
      grade: '12',
      subject: 'math',
      authorName: 'GV. Nguyễn Văn A',
      authorInitial: 'NA',
    },
    {
      id: 2,
      title: 'Bài giảng: Động lượng và Định luật bảo toàn động lượng',
      fileType: 'video',
      fileSize: '45.8 MB',
      uploadDate: '12/10/2023',
      grade: '10',
      subject: 'physics',
      authorName: 'GV. Trần Thị B',
      authorInitial: 'TB',
    },
    {
      id: 3,
      title: 'Ma trận đề thi Giữa kì 1 - Hóa học 11',
      fileType: 'word',
      fileSize: '1.2 MB',
      uploadDate: '10/10/2023',
      grade: '11',
      subject: 'chemistry',
      authorName: 'GV. Nguyễn Văn A',
      authorInitial: 'NA',
    },
    {
      id: 4,
      title: 'Bài tập về nhà Vật lý 10 - Chương 1',
      fileType: 'exercise',
      fileSize: '1.5 MB',
      uploadDate: '08/10/2023',
      grade: '10',
      subject: 'physics',
      authorName: 'GV. Trần Thị B',
      authorInitial: 'TB',
    },
    {
      id: 5,
      title: 'Đề kiểm tra Tiếng Anh - Unit 3 (Global Success)',
      fileType: 'pdf',
      fileSize: '3.2 MB',
      uploadDate: '05/10/2023',
      grade: '11',
      subject: 'english',
      authorName: 'GV. Nguyễn Văn A',
      authorInitial: 'NA',
    },
    {
      id: 6,
      title: 'Tài liệu ôn tập Tin học - Lập trình Python cơ bản',
      fileType: 'word',
      fileSize: '4.1 MB',
      uploadDate: '01/10/2023',
      grade: '10',
      subject: 'it',
      authorName: 'GV. Nguyễn Văn A',
      authorInitial: 'NA',
    },
  ]);

  // Filter logic
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      // Grade filter
      if (selectedGrade !== 'all' && doc.grade !== selectedGrade) {
        return false;
      }
      // Subject filter
      if (selectedSubject !== 'all' && doc.subject !== selectedSubject) {
        return false;
      }
      // Type filter
      if (selectedType !== 'all' && doc.fileType !== selectedType) {
        return false;
      }
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesTitle = doc.title.toLowerCase().includes(q);
        const matchesAuthor = doc.authorName.toLowerCase().includes(q);
        return matchesTitle || matchesAuthor;
      }
      return true;
    });
  }, [documents, selectedGrade, selectedSubject, selectedType, searchQuery]);

  const handleUploadSuccess = (newDoc) => {
    setDocuments((prev) => [newDoc, ...prev]);
  };

  const handleNavSelect = (navId) => {
    if (navId === 'dashboard') {
      navigate('/teacher');
    } else if (navId === 'classes') {
      navigate('/teacher/classes');
    } else if (navId === 'documents') {
      navigate('/teacher/documents');
    } else if (navId === 'exercises') {
      navigate('/teacher/exercises');
    }
  };

  return (
    <div className="doc-repository-layout">
      {/* Top Global Header */}
      <Header onToggleSidebar={() => setShowSidebar(!showSidebar)} />

      <div className="doc-repository-body">
        {/* Left Teacher Sidebar */}
        {showSidebar && (
          <TeacherSidebar 
            activeNav="documents" 
            onSelectNav={handleNavSelect} 
            onCreateExercise={() => setIsCreateExerciseOpen(true)}
          />
        )}

        {/* Main Content Area */}
        <main className="doc-repository-main">
          {/* Breadcrumb & Action Row */}
          <div className="doc-top-bar">
            <div className="doc-title-group">
              <nav className="breadcrumb-nav" aria-label="Breadcrumb">
                <Link to="/teacher" className="breadcrumb-link">Trang chủ</Link>
                <ChevronRight size={14} className="breadcrumb-separator" />
                <span className="breadcrumb-current">Kho tài liệu</span>
              </nav>
              <h1 className="page-heading">Kho tài liệu</h1>
            </div>

            <button 
              type="button" 
              className="btn-upload-new"
              onClick={() => setIsUploadOpen(true)}
            >
              <Upload size={16} />
              <span>Tải lên tài liệu mới</span>
            </button>
          </div>

          {/* Filter & Search Toolbar */}
          <DocumentFilterBar
            selectedGrade={selectedGrade}
            onChangeGrade={setSelectedGrade}
            selectedSubject={selectedSubject}
            onChangeSubject={setSelectedSubject}
            selectedType={selectedType}
            onChangeType={setSelectedType}
            searchQuery={searchQuery}
            onChangeSearch={setSearchQuery}
          />

          {/* Document Cards Grid */}
          <div className="doc-cards-grid">
            {filteredDocuments.length > 0 ? (
              filteredDocuments.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  doc={doc}
                  onPreview={(d) => setPreviewDoc(d)}
                  onDownload={(d) => alert(`Bắt đầu tải xuống: ${d.title}`)}
                  onEdit={(d) => alert(`Chỉnh sửa tài liệu: ${d.title}`)}
                  onMore={(d) => alert(`Tùy chọn: ${d.title}`)}
                />
              ))
            ) : (
              <div className="doc-empty-state">
                <p>Không tìm thấy tài liệu phù hợp với bộ lọc hiện tại.</p>
              </div>
            )}
          </div>

          {/* Bottom Pagination Row */}
          <div className="doc-pagination-row">
            <span className="pagination-info">
              Hiển thị <strong>1</strong> đến <strong>{filteredDocuments.length}</strong> trong số <strong>24</strong> tài liệu
            </span>

            <div className="pagination-controls">
              <button 
                type="button" 
                className="pagination-btn arrow-btn"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              >
                <ChevronLeft size={16} />
              </button>

              <button 
                type="button" 
                className={`pagination-btn page-num-btn ${currentPage === 1 ? 'active' : ''}`}
                onClick={() => setCurrentPage(1)}
              >
                1
              </button>

              <button 
                type="button" 
                className={`pagination-btn page-num-btn ${currentPage === 2 ? 'active' : ''}`}
                onClick={() => setCurrentPage(2)}
              >
                2
              </button>

              <button 
                type="button" 
                className="pagination-btn arrow-btn"
                disabled={currentPage === 2}
                onClick={() => setCurrentPage(prev => prev + 1)}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </main>
      </div>

      {/* Upload Document Modal */}
      <UploadDocumentModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Document Preview Modal */}
      <DocumentPreviewModal
        doc={previewDoc}
        isOpen={!!previewDoc}
        onClose={() => setPreviewDoc(null)}
      />

      {/* Create Exercise Modal */}
      <CreateExerciseModal
        isOpen={isCreateExerciseOpen}
        onClose={() => setIsCreateExerciseOpen(false)}
        onCreateSuccess={(newEx) => {
          alert(`Đã tạo thành công bài tập: ${newEx.title}`);
          navigate('/teacher/exercises');
        }}
      />
    </div>
  );
}
