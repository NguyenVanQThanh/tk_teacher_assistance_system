// File Name: ExerciseRepositoryPage.jsx
// Description: Teacher Exercise Repository Page connected to backend RESTful APIs with Cursor-based Keyset Pagination (zero OFFSET, max 6 items/page), search, real questions preview, PDF export, and soft deletion.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-02
// Updated By: Tam Khang

import React, { useState, useEffect, useCallback } from 'react';
import { ChevronRight, Plus, ChevronLeft, Loader2, AlertCircle } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import ExerciseFilterBar from '../../components/exercises/ExerciseFilterBar';
import ExerciseCard from '../../components/exercises/ExerciseCard';
import CreateExerciseModal from '../../components/exercises/CreateExerciseModal';
import ExercisePreviewModal from '../../components/exercises/ExercisePreviewModal';
import { exercisesApi, subjectsApi } from '../../services/api';
import './ExerciseRepositoryPage.css';

const PAGE_SIZE = 6;

export default function ExerciseRepositoryPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Cursor-based pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [cursorHistory, setCursorHistory] = useState([null]);
  const [nextCursor, setNextCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [totalItems, setTotalItems] = useState(0);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [previewExercise, setPreviewExercise] = useState(null);

  const [exercises, setExercises] = useState([]);
  const [subjectsList, setSubjectsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  // Load subject list once on mount
  useEffect(() => {
    let isMounted = true;
    async function loadSubjects() {
      try {
        const res = await subjectsApi.getSubjects();
        if (isMounted && Array.isArray(res)) {
          setSubjectsList(res);
        }
      } catch (err) {
        console.error('Failed to load subjects:', err);
      }
    }
    loadSubjects();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch cursor-paginated exercises from Backend (ZERO OFFSET)
  const loadExercises = useCallback(async (cursor = null, direction = 'next', pageNum = 1) => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page_size: PAGE_SIZE,
        direction: direction,
      };

      if (cursor) {
        params.cursor = cursor;
      }

      if (searchQuery && searchQuery.trim()) {
        params.search = searchQuery.trim();
      }

      if (selectedSubject !== 'all' && subjectsList.length > 0) {
        const found = subjectsList.find(
          (s) =>
            s.subject_id === selectedSubject ||
            (selectedSubject === 'math' && s.subject_name.toLowerCase().includes('toán')) ||
            (selectedSubject === 'physics' && s.subject_name.toLowerCase().includes('vật')) ||
            (selectedSubject === 'chemistry' && s.subject_name.toLowerCase().includes('hóa')) ||
            (selectedSubject === 'english' && s.subject_name.toLowerCase().includes('anh'))
        );
        if (found) {
          params.subject_id = found.subject_id;
        }
      }

      const res = await exercisesApi.getExercises(params);

      let rawItems = [];
      let total = 0;

      if (res && res.items !== undefined) {
        rawItems = res.items || [];
        total = res.total || 0;
        setNextCursor(res.next_cursor || null);
        setHasMore(!!res.has_more);

        // Pre-fill cursorHistory for the next page
        if (res.next_cursor) {
          setCursorHistory((prev) => {
            const nextStack = [...prev];
            nextStack[pageNum] = res.next_cursor;
            return nextStack;
          });
        }
      } else if (Array.isArray(res)) {
        rawItems = res;
        total = res.length;
        setNextCursor(null);
        setHasMore(false);
      }

      setTotalItems(total);
      setCurrentPage(pageNum);

      const subjectsMap = {};
      subjectsList.forEach((s) => {
        subjectsMap[s.subject_id] = s.subject_name;
      });

      // Enrich exercises data for card display
      const enriched = rawItems.map((ex) => {
        const meta = ex.ai_metadata || {};
        const subjectName = subjectsMap[ex.subject_id] || 'Toán học';

        let grade = meta.grade || '12';
        if (!meta.grade) {
          const match = ex.title.match(/\b(10|11|12)\b/);
          if (match) grade = match[1];
        }

        let exType = meta.type || 'quiz';
        if (ex.title.toLowerCase().includes('về nhà')) exType = 'homework';
        else if (ex.title.toLowerCase().includes('cuối kỳ') || ex.title.toLowerCase().includes('giữa kỳ')) exType = 'test';

        const createdDate = ex.created_at ? new Date(ex.created_at).toLocaleDateString('vi-VN') : '20/10/2023';

        return {
          id: ex.exercise_id,
          title: ex.title,
          type: exType,
          questionCount: `${ex.total_questions || (ex.questions ? ex.questions.length : 0)} câu hỏi`,
          duration: meta.duration || (exType === 'test' ? '60 phút' : exType === 'quiz' ? '15 phút' : null),
          date: createdDate,
          grade: grade,
          subject: subjectName.toLowerCase().includes('toán') ? 'math' : subjectName.toLowerCase().includes('vật lý') ? 'physics' : subjectName.toLowerCase().includes('hóa') ? 'chemistry' : 'math',
          subjectName: subjectName,
          authorName: 'Thầy Nguyễn Văn A',
          authorInitial: 'NA',
          hasShare: true,
          raw: ex,
        };
      });

      setExercises(enriched);
    } catch (err) {
      setError(err.response?.data?.detail?.message || 'Không thể tải danh sách bài tập.');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedSubject, subjectsList]);

  // Initial and reactive load on filter change
  useEffect(() => {
    setCursorHistory([null]);
    loadExercises(null, 'next', 1);
  }, [selectedGrade, selectedSubject, selectedType, searchQuery, loadExercises]);

  const handleNextPage = () => {
    if (!nextCursor || !hasMore) return;
    const nextPageNum = currentPage + 1;
    loadExercises(nextCursor, 'next', nextPageNum);
  };

  const handlePrevPage = () => {
    if (currentPage <= 1) return;
    const prevPageNum = currentPage - 1;
    const targetCursor = cursorHistory[prevPageNum - 1] || null;
    loadExercises(targetCursor, 'next', prevPageNum);
  };

  const handleGoToPage = (pageNum) => {
    if (pageNum === currentPage) return;
    if (pageNum === 1) {
      loadExercises(null, 'next', 1);
    } else if (pageNum === currentPage + 1 && nextCursor) {
      handleNextPage();
    } else if (pageNum === currentPage - 1) {
      handlePrevPage();
    } else {
      const targetCursor = cursorHistory[pageNum - 1];
      if (targetCursor !== undefined) {
        loadExercises(targetCursor, 'next', pageNum);
      }
    }
  };

  const handleCreateSuccess = () => {
    setCursorHistory([null]);
    loadExercises(null, 'next', 1);
  };

  const handleDownloadPdf = async (exercise) => {
    try {
      const blob = await exercisesApi.exportPdf(exercise.id);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${exercise.title || 'de_bai'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Không thể xuất file PDF cho bài tập này.');
    }
  };

  const handleDeleteExercise = async (exercise) => {
    if (window.confirm(`Bạn có chắc chắn muốn xóa bài tập "${exercise.title}"?`)) {
      try {
        await exercisesApi.deleteExercise(exercise.id);
        const currentCursor = cursorHistory[currentPage - 1] || null;
        loadExercises(currentCursor, 'next', currentPage);
        alert('Đã xóa thành công bài tập.');
      } catch (err) {
        alert('Không thể xóa bài tập này.');
      }
    }
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

  const totalCalculatedPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const endItem = Math.min(currentPage * PAGE_SIZE, totalItems);

  return (
    <div className="exercise-repository-main">
          {/* Top Row: Breadcrumb, Title & Create Button */}
          <div className="exercise-top-bar">
            <div className="exercise-title-group">
              <nav className="breadcrumb-nav" aria-label="Breadcrumb">
                <Link to="/teacher" className="breadcrumb-link">Trang chủ</Link>
                <ChevronRight size={14} className="breadcrumb-separator" />
                <span className="breadcrumb-current">Kho bài tập</span>
              </nav>
              <h1 className="page-heading">Kho bài tập ({totalItems})</h1>
              <p className="page-subheading">
                Quản lý và tạo mới các bài tập, bài kiểm tra cho học sinh.
              </p>
            </div>

            <button 
              type="button" 
              className="btn-create-new-exercise"
              onClick={() => setIsCreateOpen(true)}
            >
              <Plus size={18} />
              <span>Tạo bài tập mới</span>
            </button>
          </div>

          {/* Filter & Search Toolbar */}
          <ExerciseFilterBar
            selectedGrade={selectedGrade}
            onChangeGrade={setSelectedGrade}
            selectedSubject={selectedSubject}
            onChangeSubject={setSelectedSubject}
            selectedType={selectedType}
            onChangeType={setSelectedType}
            searchQuery={searchQuery}
            onChangeSearch={setSearchQuery}
          />

          {/* Error Alert */}
          {error && (
            <div style={{ padding: '12px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#991B1B', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {/* Loading Indicator or Cards Grid */}
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '260px', gap: '12px', color: '#6B7280' }}>
              <Loader2 size={32} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
              <p>Đang tải danh sách bài tập từ hệ thống...</p>
            </div>
          ) : (
            /* Exercise Cards Grid (Maximum 6 items per page container) */
            <div className="exercise-cards-grid">
              {exercises.length > 0 ? (
                exercises.map((exercise) => (
                  <ExerciseCard
                    key={exercise.id}
                    exercise={exercise}
                    onPreview={(item) => setPreviewExercise(item)}
                    onEdit={(item) => alert(`Chỉnh sửa bài tập: ${item.title}`)}
                    onShare={(item) => setPreviewExercise(item)}
                    onDownload={(item) => handleDownloadPdf(item)}
                    onMore={(item) => handleDeleteExercise(item)}
                  />
                ))
              ) : (
                <div className="exercise-empty-state">
                  <p>Không tìm thấy bài tập nào phù hợp với điều kiện tìm kiếm.</p>
                </div>
              )}
            </div>
          )}

          {/* Bottom Pagination Row (Cursor-based Keyset Navigation) */}
          {!loading && totalItems > 0 && (
            <div className="exercise-pagination-row">
              <span className="pagination-info">
                Hiển thị <strong>{startItem}</strong> đến <strong>{endItem}</strong> trong số <strong>{totalItems}</strong> bài tập (Trang {currentPage}/{totalCalculatedPages})
              </span>

              <div className="pagination-controls">
                <button 
                  type="button" 
                  className="pagination-btn arrow-btn"
                  disabled={currentPage <= 1}
                  onClick={handlePrevPage}
                  title="Trang trước"
                >
                  <ChevronLeft size={16} />
                </button>

                {Array.from({ length: totalCalculatedPages }, (_, idx) => idx + 1).map((pageNum) => (
                  <button 
                    key={pageNum}
                    type="button" 
                    className={`pagination-btn page-num-btn ${currentPage === pageNum ? 'active' : ''}`}
                    onClick={() => handleGoToPage(pageNum)}
                  >
                    {pageNum}
                  </button>
                ))}

                <button 
                  type="button" 
                  className="pagination-btn arrow-btn"
                  disabled={currentPage >= totalCalculatedPages || !hasMore}
                  onClick={handleNextPage}
                  title="Trang sau"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}

      {/* Create Exercise Modal */}
      <CreateExerciseModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreateSuccess={handleCreateSuccess}
      />

      {/* Preview & Assign Exercise Modal */}
      <ExercisePreviewModal
        exercise={previewExercise}
        isOpen={!!previewExercise}
        onClose={() => setPreviewExercise(null)}
      />
    </div>
  );
}
