// File Name: DocumentRepositoryPage.jsx
// Description: Teacher Document Repository Page featuring filtering, search, pagination, centered toast notifications, real metrics, and full CRUD.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-10-28
// Updated By: Tam Khang

import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import { 
  ChevronRight, 
  Upload, 
  CheckCircle2, 
  AlertCircle, 
  AlertTriangle,
  Info, 
  X,
  Trash2,
  FileText,
  DownloadCloud,
  HardDrive
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { documentsApi } from '../../services/api';
import DocumentFilterBar from '../../components/documents/DocumentFilterBar';
import DocumentCard from '../../components/documents/DocumentCard';
import DocumentDetailView from '../../components/documents/DocumentDetailView';
import UploadDocumentModal from '../../components/documents/UploadDocumentModal';
import DocumentPreviewModal from '../../components/documents/DocumentPreviewModal';
import EditDocumentModal from '../../components/documents/EditDocumentModal';
import CreateExerciseModal from '../../components/exercises/CreateExerciseModal';
import './DocumentRepositoryPage.css';

const isUuid = (str) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(String(str || ''));

const formatFileSize = (bytes) => {
  if (!bytes || bytes <= 0) return '0 KB';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Backend returns subject names; filter, preview and edit components work with these keys.
const SUBJECT_KEY_BY_NAME = {
  'toán học': 'math',
  'vật lý': 'physics',
  'hóa học': 'chemistry',
  'sinh học': 'biology',
  'lịch sử': 'history',
  'tiếng anh': 'english',
  'tin học': 'it',
};

const mapBackendDoc = (doc) => ({
  id: doc.document_id,
  title: doc.title,
  fileType: doc.document_type || 'lecture',
  fileSize: formatFileSize(doc.file_size),
  uploadDate: doc.created_at ? new Date(doc.created_at).toLocaleDateString('vi-VN') : '',
  grade: doc.grade || '12',
  subject: SUBJECT_KEY_BY_NAME[(doc.subject_name || '').trim().toLowerCase()] || 'other',
  subjectName: doc.subject_name || 'Chung',
  authorName: doc.author_name || doc.uploader_name || 'GV. Tam Khang',
  authorInitial: (doc.author_name || 'TK').split(' ').map(n => n[0]).join('').slice(-2).toUpperCase(),
  folder: `${doc.subject_name || 'Tài liệu'} ${doc.grade || ''}`.trim(),
  description: doc.description || 'Tài liệu học tập được chia sẻ cho học sinh và giáo viên.',
  downloadsCount: `${doc.download_count || 0}`,
  fileUrl: doc.file_url,
});

export default function DocumentRepositoryPage() {
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isCreateExerciseOpen, setIsCreateExerciseOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [editingDoc, setEditingDoc] = useState(null);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [documents, setDocuments] = useState([]);

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

  const reloadData = useCallback(async () => {
    try {
      const [dashRes, docsRes] = await Promise.allSettled([
        documentsApi.getDocumentDashboard(),
        documentsApi.getDocuments({ status: 'ALL', page_size: 100 })
      ]);
      if (dashRes.status === 'fulfilled' && dashRes.value) {
        setDashboardStats(dashRes.value);
      }
      if (docsRes.status === 'fulfilled' && docsRes.value) {
        const items = Array.isArray(docsRes.value) ? docsRes.value : (docsRes.value.items || []);
        setDocuments(items.map(mapBackendDoc));
      }
    } catch (err) {
      console.error('Failed to reload documents:', err);
    }
  }, []);

  useEffect(() => {
    reloadData();
  }, [reloadData]);

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
        const matchesTitle = (doc.title || '').toLowerCase().includes(q);
        const matchesAuthor = (doc.authorName || '').toLowerCase().includes(q);
        return matchesTitle || matchesAuthor;
      }
      return true;
    });
  }, [documents, selectedGrade, selectedSubject, selectedType, searchQuery]);

  const handleUploadSuccess = async (newDoc) => {
    await reloadData();
    showToast(`Đã tải lên tài liệu "${newDoc.title}" thành công!`, 'success', 'Tải lên hoàn tất');
  };

  const handleSaveEditedDoc = async (updatedDoc) => {
    try {
      if (updatedDoc.id && isUuid(updatedDoc.id)) {
        await documentsApi.updateDocument(updatedDoc.id, {
          title: updatedDoc.title,
          grade: updatedDoc.grade,
          document_type: updatedDoc.fileType,
          description: updatedDoc.description,
        });
      }
      setDocuments((prev) => prev.map((d) => (d.id === updatedDoc.id ? { ...d, ...updatedDoc } : d)));
      if (selectedDoc && selectedDoc.id === updatedDoc.id) {
        setSelectedDoc((prev) => ({ ...prev, ...updatedDoc }));
      }
      showToast(`Đã cập nhật thông tin tài liệu "${updatedDoc.title}" thành công!`, 'success', 'Cập nhật thành công');
      // Refresh dashboard in background
      documentsApi.getDocumentDashboard().then(stats => stats && setDashboardStats(stats)).catch(() => {});
    } catch (err) {
      console.error('Failed to update document in backend:', err);
      showToast('Có lỗi xảy ra khi cập nhật tài liệu.', 'error', 'Lỗi cập nhật');
    }
  };

  const handleDownloadDocument = async (doc) => {
    showToast(`Bắt đầu tải xuống: ${doc.title}`, 'info', 'Tải tài liệu');
    try {
      if (doc.id && isUuid(doc.id)) {
        const blob = await documentsApi.downloadDocument(doc.id);
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${doc.title}.${doc.fileType || 'pdf'}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);

        // Update real download counter locally and sync dashboard
        setDocuments((prev) => prev.map((d) => d.id === doc.id ? { ...d, downloadsCount: String(Number(d.downloadsCount || 0) + 1) } : d));
        if (selectedDoc && selectedDoc.id === doc.id) {
          setSelectedDoc((prev) => ({ ...prev, downloadsCount: String(Number(prev.downloadsCount || 0) + 1) }));
        }
        documentsApi.getDocumentDashboard().then(stats => stats && setDashboardStats(stats)).catch(() => {});
      }
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  const requestDeleteDocument = (doc) => {
    setDeleteConfirmDoc(doc);
  };

  const confirmDeleteDocument = async () => {
    if (!deleteConfirmDoc) return;
    const doc = deleteConfirmDoc;
    setDeleteConfirmDoc(null);
    try {
      if (doc.id && isUuid(doc.id)) {
        await documentsApi.deleteDocument(doc.id);
      }
    } catch (err) {
      console.error('Failed to soft delete document:', err);
    }
    // Soft Delete Policy: filter out from active view list and show confirmation toast
    setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    if (selectedDoc && selectedDoc.id === doc.id) {
      setSelectedDoc(null);
    }
    showToast(`Đã xóa tài liệu "${doc.title}" thành công!`, 'success', 'Xóa tài liệu');
    // Refresh stats
    documentsApi.getDocumentDashboard().then(stats => stats && setDashboardStats(stats)).catch(() => {});
  };

  return (
    <div className="doc-repository-main">
      {selectedDoc ? (
        /* Document Detail View (Image 1) */
        <DocumentDetailView
          doc={selectedDoc}
          onBack={() => setSelectedDoc(null)}
          onViewDocument={(d) => setPreviewDoc(d)}
          onDownloadDocument={(d) => handleDownloadDocument(d)}
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
          
          {/* Document Repository Dashboard Real Stats */}
          <div className="doc-dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px', marginBottom: '16px' }}>
            <div style={{ background: '#FFFFFF', borderRadius: '10px', padding: '14px 18px', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', gap: '14px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ width: '42px', height: '42px', borderRadius: '8px', background: '#F5F3FF', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#7C3AED' }}>
                <FileText size={20} />
              </div>
              <div>
                <span style={{ fontSize: '12px', color: '#64748B', fontWeight: 500, display: 'block' }}>Tổng số tài liệu</span>
                <strong style={{ fontSize: '20px', color: '#1E293B', fontWeight: 700 }}>
                  {dashboardStats?.total_documents !== undefined ? dashboardStats.total_documents : documents.length}
                </strong>
              </div>
            </div>

            <div style={{ background: '#FFFFFF', borderRadius: '10px', padding: '14px 18px', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', gap: '14px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ width: '42px', height: '42px', borderRadius: '8px', background: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2563EB' }}>
                <DownloadCloud size={20} />
              </div>
              <div>
                <span style={{ fontSize: '12px', color: '#64748B', fontWeight: 500, display: 'block' }}>Lượt tải xuống</span>
                <strong style={{ fontSize: '20px', color: '#1E293B', fontWeight: 700 }}>
                  {dashboardStats?.total_downloads !== undefined ? dashboardStats.total_downloads : 0}
                </strong>
              </div>
            </div>

            <div style={{ background: '#FFFFFF', borderRadius: '10px', padding: '14px 18px', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', gap: '14px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ width: '42px', height: '42px', borderRadius: '8px', background: '#ECFDF5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669' }}>
                <HardDrive size={20} />
              </div>
              <div>
                <span style={{ fontSize: '12px', color: '#64748B', fontWeight: 500, display: 'block' }}>Dung lượng lưu trữ</span>
                <strong style={{ fontSize: '20px', color: '#1E293B', fontWeight: 700 }}>
                  {dashboardStats?.storage_formatted || dashboardStats?.storage_used_formatted || '0 MB'}
                </strong>
              </div>
            </div>
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
                  onDownload={(d) => handleDownloadDocument(d)}
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
              Hiển thị <strong>{filteredDocuments.length}</strong> trong số <strong>{documents.length}</strong> tài liệu
            </span>
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
        onDownload={(d) => handleDownloadDocument(d)}
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
