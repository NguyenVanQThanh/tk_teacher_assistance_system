// File Name: DocumentRepositoryPage.jsx
// Description: Teacher Document Repository Page featuring filtering, search, pagination, centered toast notifications, and soft delete.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-12
// Updated By: Tam Khang

import React, { useState, useMemo, useRef } from 'react';
import { 
  ChevronRight, 
  Upload, 
  ChevronLeft, 
  CheckCircle2, 
  AlertCircle, 
  AlertTriangle,
  Info, 
  X,
  Trash2
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import DocumentFilterBar from '../../components/documents/DocumentFilterBar';
import DocumentCard from '../../components/documents/DocumentCard';
import DocumentDetailView from '../../components/documents/DocumentDetailView';
import UploadDocumentModal from '../../components/documents/UploadDocumentModal';
import DocumentPreviewModal from '../../components/documents/DocumentPreviewModal';
import EditDocumentModal from '../../components/documents/EditDocumentModal';
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
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [editingDoc, setEditingDoc] = useState(null);

  // Centered Confirmation Dialog & Toast States
  const [deleteConfirmDoc, setDeleteConfirmDoc] = useState(null);
  const [toast, setToast] = useState(null);
  const toastTimeoutRef = useRef(null);

  const showToast = (message, type = 'info', title = '') => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }
    setToast({ message, type, title });
    toastTimeoutRef.current = setTimeout(() => {
      setToast(null);
    }, 2800);
  };

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
      folder: 'Toán 12',
      description: 'Tài liệu tổng hợp các kiến thức trọng tâm học kì 1 môn Toán lớp 12, bao gồm các chuyên đề: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số, Hàm số lũy thừa, hàm số mũ và hàm số logarit. Kèm theo hệ thống bài tập tự luyện từ cơ bản đến nâng cao có đáp án chi tiết, phù hợp cho học sinh ôn thi THPT Quốc gia.',
      viewsCount: '1,245',
      downloadsCount: '342',
      ratingScore: '4.8/5',
      ratingsCount: '56'
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
      folder: 'Vật lý 10',
      description: 'Video bài giảng chi tiết về khái niệm động lượng, định luật bảo toàn động lượng và ứng dụng giải bài toán va chạm đàn hồi.',
      viewsCount: '980',
      downloadsCount: '215',
      ratingScore: '4.9/5',
      ratingsCount: '42'
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
      folder: 'Hóa học 11',
      description: 'Bảng đặc tả ma trận đề kiểm tra giữa kì 1 môn Hóa học 11 bám sát chương trình GDPT 2018 mới.',
      viewsCount: '620',
      downloadsCount: '145',
      ratingScore: '4.7/5',
      ratingsCount: '28'
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
      folder: 'Vật lý 10',
      description: 'Bộ 50 câu hỏi trắc nghiệm và bài tập định lượng chương Chuyển động thẳng đều và chuyển động biến đổi đều.',
      viewsCount: '850',
      downloadsCount: '310',
      ratingScore: '4.8/5',
      ratingsCount: '35'
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
      folder: 'Tiếng Anh 11',
      description: 'Đề kiểm tra 45 phút Unit 3 Global Success có kèm file nghe MP3 và hướng dẫn chấm chi tiết.',
      viewsCount: '1,120',
      downloadsCount: '430',
      ratingScore: '4.9/5',
      ratingsCount: '60'
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
      folder: 'Tin học 10',
      description: 'Sổ tay hướng dẫn thực hành lập trình Python từ cơ bản đến cấu trúc điều khiển và mảng 1 chiều.',
      viewsCount: '790',
      downloadsCount: '260',
      ratingScore: '4.8/5',
      ratingsCount: '31'
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
    showToast(`Đã tải lên tài liệu "${newDoc.title}" thành công!`, 'success', 'Tải lên hoàn tất');
  };

  const handleSaveEditedDoc = (updatedDoc) => {
    setDocuments((prev) => prev.map((d) => (d.id === updatedDoc.id ? updatedDoc : d)));
    if (selectedDoc && selectedDoc.id === updatedDoc.id) {
      setSelectedDoc(updatedDoc);
    }
    showToast(`Đã cập nhật thông tin tài liệu "${updatedDoc.title}" thành công!`, 'success', 'Cập nhật thành công');
  };

  const requestDeleteDocument = (doc) => {
    setDeleteConfirmDoc(doc);
  };

  const confirmDeleteDocument = () => {
    if (!deleteConfirmDoc) return;
    const doc = deleteConfirmDoc;
    setDeleteConfirmDoc(null);
    // Soft Delete Policy: filter out from active view list and show confirmation toast
    setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    showToast(`Đã xóa tài liệu "${doc.title}" thành công!`, 'success', 'Xóa tài liệu');
  };

  const handleNavSelect = (navId) => {
    setSelectedDoc(null);
    if (navId === 'dashboard') {
      navigate('/teacher');
    } else if (navId === 'classes') {
      navigate('/teacher/classes');
    } else if (navId === 'grading') {
      navigate('/teacher/grading');
    } else if (navId === 'documents') {
      navigate('/teacher/documents');
    } else if (navId === 'exercises') {
      navigate('/teacher/exercises');
    }
  };

  return (
    <div className="doc-repository-main">
          {selectedDoc ? (
            /* Document Detail View (Image 1) */
            <DocumentDetailView
              doc={selectedDoc}
              onBack={() => setSelectedDoc(null)}
              onViewDocument={(d) => setPreviewDoc(d)}
              onDownloadDocument={(d) => showToast(`Bắt đầu tải xuống: ${d.title}`, 'info', 'Tải xuống')}
              onEditDocument={(d) => setEditingDoc(d)}
              onMoreOptions={(d) => showToast(`Tùy chọn khác cho: ${d.title}`, 'info', 'Tùy chọn')}
            />
          ) : (
            /* Document List View */
            <>
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
                      onPreview={(d) => setSelectedDoc(d)}
                      onDownload={(d) => showToast(`Bắt đầu tải xuống: ${d.title}`, 'info', 'Tải tài liệu')}
                      onEdit={(d) => setEditingDoc(d)}
                      onDelete={(d) => requestDeleteDocument(d)}
                      onMore={(d) => requestDeleteDocument(d)}
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
            </>
          )}

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
        onDownload={(d) => showToast(`Bắt đầu tải xuống: ${d.title}`, 'info', 'Tải tài liệu')}
      />

      {/* Create Exercise Modal */}
      <CreateExerciseModal
        isOpen={isCreateExerciseOpen}
        onClose={() => setIsCreateExerciseOpen(false)}
        onCreateSuccess={(newEx) => {
          showToast(`Đã tạo thành công bài tập: ${newEx.title}`, 'success', 'Tạo bài tập');
          navigate('/teacher/exercises');
        }}
      />

      {/* Full-screen Edit Document Dialog Modal */}
      <EditDocumentModal
        isOpen={!!editingDoc}
        doc={editingDoc}
        onClose={() => setEditingDoc(null)}
        onSave={handleSaveEditedDoc}
      />

      {/* ============================================================ */}
      {/* CENTERED DELETE CONFIRMATION MODAL */}
      {/* ============================================================ */}
      {deleteConfirmDoc && (
        <div className="center-confirm-overlay" onClick={() => setDeleteConfirmDoc(null)}>
          <div className="center-confirm-card" onClick={(e) => e.stopPropagation()}>
            <div className="confirm-icon-badge">
              <AlertTriangle size={26} />
            </div>
            <div className="confirm-content-col">
              <h3 className="confirm-title-text">Xác nhận xóa tài liệu</h3>
              <p className="confirm-message-text">
                Bạn có chắc chắn muốn xóa tài liệu <strong>"{deleteConfirmDoc.title}"</strong> không? Hành động này sẽ chuyển trạng thái tài liệu sang đã xóa (xóa mềm).
              </p>
            </div>
            <div className="confirm-actions-row">
              <button 
                type="button" 
                className="btn-confirm-cancel"
                onClick={() => setDeleteConfirmDoc(null)}
              >
                Hủy bỏ
              </button>
              <button 
                type="button" 
                className="btn-confirm-delete"
                onClick={confirmDeleteDocument}
              >
                <Trash2 size={15} />
                <span>Xác nhận xóa</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* CENTERED TOAST NOTIFICATION MODAL */}
      {/* ============================================================ */}
      {toast && (
        <div className="center-toast-overlay" onClick={() => setToast(null)}>
          <div 
            className={`center-toast-card toast-type-${toast.type || 'info'}`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="toast-icon-badge">
              {toast.type === 'success' && <CheckCircle2 size={24} />}
              {toast.type === 'error' && <AlertCircle size={24} />}
              {toast.type === 'info' && <Info size={24} />}
            </div>
            <div className="toast-content-col">
              {toast.title && <h4 className="toast-title-text">{toast.title}</h4>}
              <p className="toast-message-text">{toast.message}</p>
            </div>
            <button 
              type="button" 
              className="toast-close-btn"
              onClick={() => setToast(null)}
              aria-label="Đóng thông báo"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
