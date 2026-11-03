// File Name: DocumentPreviewModal.jsx
// Description: Interactive PDF Document Viewer modal with complete function toolbar (Download, Print, Close) and native PDF controls.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-11-03
// Updated By: Tam Khang

import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  Download,
  Printer,
  FileText, 
  Loader2, 
  AlertCircle,
  FileQuestion
} from 'lucide-react';
import { documentsApi } from '../../services/api';
import './DocumentPreviewModal.css';

export default function DocumentPreviewModal({ doc, isOpen, onClose, onDownload }) {
  if (!isOpen || !doc) return null;

  const [pdfBlobUrl, setPdfBlobUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isNotPdf, setIsNotPdf] = useState(false);
  const iframeRef = useRef(null);

  // Check file type
  const fileExt = (
    doc.fileExtension ||
    doc.rawFileType ||
    (doc.fileUrl ? doc.fileUrl.split('.').pop() : '') ||
    (doc.title && doc.title.includes('.') ? doc.title.split('.').pop() : 'pdf')
  ).toLowerCase();

  const isPdf = fileExt === 'pdf' || (doc.title && doc.title.toLowerCase().endsWith('.pdf'));

  useEffect(() => {
    if (!isOpen || !doc) {
      setPdfBlobUrl(null);
      setError(null);
      setIsNotPdf(false);
      return;
    }

    let isMounted = true;
    let createdUrl = null;

    if (!isPdf) {
      setIsNotPdf(true);
      setLoading(false);
      return;
    }

    setIsNotPdf(false);

    async function fetchPdfFile() {
      try {
        setLoading(true);
        setError(null);

        if (!doc.id) {
          throw new Error('Tài liệu không có mã định danh hợp lệ.');
        }

        const blob = await documentsApi.viewDocument(doc.id);
        if (!isMounted) return;

        const pdfBlob = new Blob([blob], { type: 'application/pdf' });
        createdUrl = URL.createObjectURL(pdfBlob);
        setPdfBlobUrl(createdUrl);
      } catch (err) {
        if (!isMounted) return;
        console.error('Failed to load PDF preview:', err);
        const detailMsg = err.response?.data?.detail;
        const msg = typeof detailMsg === 'string' ? detailMsg : detailMsg?.message;
        setError(msg || 'Không thể tải tệp PDF để xem trực tiếp. Tệp có thể đã bị di chuyển hoặc định dạng không hợp lệ.');
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchPdfFile();

    return () => {
      isMounted = false;
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [isOpen, doc?.id, isPdf]);

  const handlePrint = () => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      try {
        iframeRef.current.contentWindow.print();
        return;
      } catch (e) {
        console.warn('Could not print via iframe contentWindow:', e);
      }
    }
    if (pdfBlobUrl) {
      const printWindow = window.open(pdfBlobUrl, '_blank');
      if (printWindow) {
        printWindow.focus();
        printWindow.print();
      }
    } else {
      window.print();
    }
  };

  const displayFormat = isPdf ? 'PDF' : fileExt.toUpperCase();

  return (
    <div className="document-reader-overlay" onClick={onClose}>
      <div className="document-reader-window" onClick={(e) => e.stopPropagation()}>
        {/* Top Control Bar */}
        <header className="reader-top-bar">
          <div className="reader-info-left">
            <div className="reader-type-icon">
              <FileText size={20} className="text-purple" />
            </div>
            <div className="reader-doc-titles">
              <h3 className="reader-main-title" title={doc.title}>{doc.title}</h3>
              <p className="reader-meta-sub">
                {displayFormat} • {doc.fileSize || 'N/A'} • Tác giả: {doc.authorName || 'Giáo viên'}
              </p>
            </div>
          </div>

          {/* Right Action Tools: Download, Print, Close */}
          <div className="reader-right-actions">
            {/* <button 
              type="button" 
              className="btn-reader-action"
              onClick={() => onDownload ? onDownload(doc) : null}
              title="Tải xuống tệp tin"
            >
              <Download size={15} />
              <span>Tải xuống</span>
            </button>

            {isPdf && !error && (
              <button 
                type="button" 
                className="btn-reader-action secondary"
                onClick={handlePrint}
                title="In tài liệu"
                disabled={loading || !pdfBlobUrl}
              >
                <Printer size={15} />
                <span>In</span>
              </button>
            )} */}

            <button 
              type="button" 
              className="btn-reader-close" 
              onClick={onClose}
              aria-label="Đóng"
              title="Đóng trình đọc tài liệu"
            >
              <X size={20} />
            </button>
          </div>
        </header>

        {/* Main Reader Viewport */}
        <div className="reader-content-viewport">
          {loading && (
            <div className="pdf-state-box">
              <Loader2 size={38} className="pdf-spinner-icon" />
              <h4 className="pdf-state-title">Đang tải tệp PDF...</h4>
              <p className="pdf-state-desc">Vui lòng đợi giây lát trong khi tài liệu đang được chuẩn bị để hiển thị.</p>
            </div>
          )}

          {!loading && isNotPdf && (
            <div className="pdf-state-box">
              <FileQuestion size={44} className="text-amber" />
              <h4 className="pdf-state-title">Định dạng {displayFormat} không hỗ trợ xem trực tiếp</h4>
              <p className="pdf-state-desc">
                Trình xem tài liệu trực tiếp chỉ hỗ trợ hiển thị tệp <strong>PDF</strong> để đảm bảo tính bảo mật và toàn vẹn của tài liệu (không sử dụng trình soạn thảo bên thứ ba).
              </p>
              <div className="pdf-state-actions">
                <button 
                  type="button" 
                  className="btn-reader-action"
                  onClick={() => onDownload && onDownload(doc)}
                >
                  <Download size={15} />
                  <span>Tải xuống</span>
                </button>
                <button 
                  type="button" 
                  className="btn-reader-action secondary"
                  onClick={onClose}
                >
                  <span>Đóng</span>
                </button>
              </div>
            </div>
          )}

          {!loading && !isNotPdf && error && (
            <div className="pdf-state-box">
              <AlertCircle size={44} className="text-rose" />
              <h4 className="pdf-state-title">Không thể xem trực tiếp tài liệu</h4>
              <p className="pdf-state-desc">{error}</p>
              <div className="pdf-state-actions">
                <button 
                  type="button" 
                  className="btn-reader-action"
                  onClick={() => onDownload && onDownload(doc)}
                >
                  <Download size={15} />
                  <span>Tải xuống</span>
                </button>
                <button 
                  type="button" 
                  className="btn-reader-action secondary"
                  onClick={onClose}
                >
                  <span>Đóng</span>
                </button>
              </div>
            </div>
          )}

          {!loading && !isNotPdf && !error && pdfBlobUrl && (
            <div className="pdf-viewer-container">
              <iframe
                ref={iframeRef}
                src={`${pdfBlobUrl}#toolbar=1&navpanes=1`}
                title={doc.title}
                className="pdf-viewer-frame"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
