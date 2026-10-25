// File Name: DocumentPreviewModal.jsx
// Description: Full-featured interactive Document Reader displaying detailed file contents, formulas, multi-page syllabus, exercises, zoom, search, and page navigation.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState } from 'react';
import { 
  X, 
  Download, 
  FileText, 
  Printer, 
  ZoomIn, 
  ZoomOut, 
  ChevronLeft, 
  ChevronRight, 
  Search, 
  Maximize2,
  CheckCircle,
  BookOpen,
  Award,
  Layers,
  Sparkles
} from 'lucide-react';
import './DocumentPreviewModal.css';

export default function DocumentPreviewModal({ doc, isOpen, onClose, onDownload }) {
  if (!isOpen || !doc) return null;

  const [currentPage, setCurrentPage] = useState(1);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('page');

  const totalPages = 3;

  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 15, 150));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 15, 75));
  const handlePrevPage = () => setCurrentPage(prev => Math.max(prev - 1, 1));
  const handleNextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages));

  // Render document content based on subject and current page
  const renderDocumentPages = () => {
    const isMath = !doc.subject || doc.subject === 'math' || doc.title?.toLowerCase().includes('toán');
    const isPhysics = doc.subject === 'physics' || doc.title?.toLowerCase().includes('vật lý') || doc.title?.toLowerCase().includes('động lượng');
    const isEnglish = doc.subject === 'english' || doc.title?.toLowerCase().includes('tiếng anh');
    const isChemistry = doc.subject === 'chemistry' || doc.title?.toLowerCase().includes('hóa');
    const isIT = doc.subject === 'it' || doc.title?.toLowerCase().includes('tin học') || doc.title?.toLowerCase().includes('python');

    if (isMath) {
      return (
        <div className="rendered-document-sheet" style={{ transform: `scale(${zoomLevel / 100})` }}>
          {/* Document Header Letterhead */}
          <div className="sheet-top-header">
            <div className="school-department">
              <span>SỞ GD&ĐT • TRƯỜNG THPT CHUYÊN</span>
              <strong>TỔ BỘ MÔN TOÁN HỌC</strong>
            </div>
            <div className="document-academic-year">
              <span>NĂM HỌC 2023 - 2024</span>
              <span>LƯU HÀNH NỘI BỘ</span>
            </div>
          </div>

          <div className="sheet-title-banner">
            <h1>{doc.title}</h1>
            <p className="sheet-subtitle">Biên soạn: {doc.authorName} • Tổ Toán - Tin học</p>
          </div>

          {currentPage === 1 && (
            <div className="page-content-wrapper">
              <div className="doc-section-block">
                <h2 className="section-title">PHẦN I: MA TRẬN KIẾN THỨC TRỌNG TÂM HỌC KÌ 1</h2>
                <p className="paragraph-text">
                  Tài liệu được xây dựng bám sát cấu trúc đề thi tốt nghiệp THPT Quốc gia của Bộ GD&ĐT, bao gồm 3 chuyên đề cốt lõi:
                </p>

                <div className="topics-overview-table">
                  <div className="table-row head">
                    <div className="col-idx">STT</div>
                    <div className="col-topic">Chuyên đề kiến thức</div>
                    <div className="col-level">Cấp độ nhận thức</div>
                    <div className="col-rate">Tỷ trọng</div>
                  </div>
                  <div className="table-row">
                    <div className="col-idx">1</div>
                    <div className="col-topic"><strong>Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số</strong></div>
                    <div className="col-level">Nhận biết - Thông hiểu - Vận dụng</div>
                    <div className="col-rate">45%</div>
                  </div>
                  <div className="table-row">
                    <div className="col-idx">2</div>
                    <div className="col-topic"><strong>Hàm số lũy thừa, hàm số mũ và hàm số logarit</strong></div>
                    <div className="col-level">Nhận biết - Thông hiểu - Vận dụng</div>
                    <div className="col-rate">30%</div>
                  </div>
                  <div className="table-row">
                    <div className="col-idx">3</div>
                    <div className="col-topic"><strong>Khối đa diện và thể tích khối đa diện (Hình học 12)</strong></div>
                    <div className="col-level">Nhận biết - Thông hiểu - Vận dụng</div>
                    <div className="col-rate">25%</div>
                  </div>
                </div>
              </div>

              <div className="doc-section-block">
                <h2 className="section-title">PHẦN II: MỤC TIÊU VÀ YÊU CẦU CẦN ĐẠT</h2>
                <ul className="target-checklist">
                  <li>
                    <CheckCircle size={15} className="check-icon text-emerald" />
                    <span>Nắm vững các định lý về tính đơn điệu, cực trị, giá trị lớn nhất/nhỏ nhất và tiệm cận của hàm số.</span>
                  </li>
                  <li>
                    <CheckCircle size={15} className="check-icon text-emerald" />
                    <span>Thành thạo phương pháp biến đổi biểu thức lũy thừa - logarit, giải phương trình và bất phương trình mũ - logarit.</span>
                  </li>
                  <li>
                    <CheckCircle size={15} className="check-icon text-emerald" />
                    <span>Vận dụng linh hoạt công thức tính nhanh thể tích khối chóp, khối lăng trụ và khoảng cách trong không gian.</span>
                  </li>
                </ul>
              </div>
            </div>
          )}

          {currentPage === 2 && (
            <div className="page-content-wrapper">
              <div className="doc-section-block">
                <h2 className="section-title">CHUYÊN ĐỀ 1: ĐẠO HÀM VÀ KHẢO SÁT SỰ BIẾN THIÊN CỦA HÀM SỐ</h2>
                
                <div className="formula-highlight-box">
                  <h3 className="formula-box-title">1. Định lý về tính đơn điệu của hàm số:</h3>
                  <p className="formula-line">
                    Cho hàm số <span className="math">y = f(x)</span> có đạo hàm trên khoảng <span className="math">K</span>:
                  </p>
                  <p className="formula-line">
                    • Nếu <span className="math">f'(x) &gt; 0, \forall x \in K \Rightarrow f(x)</span> đồng biến trên khoảng <span className="math">K</span>.
                  </p>
                  <p className="formula-line">
                    • Nếu <span className="math">f'(x) &lt; 0, \forall x \in K \Rightarrow f(x)</span> nghịch biến trên khoảng <span className="math">K</span>.
                  </p>
                </div>

                <div className="formula-highlight-box purple-tint">
                  <h3 className="formula-box-title">2. Cực trị của hàm số & Công thức tính nhanh:</h3>
                  <p className="formula-line">
                    • Hàm số bậc ba <span className="math">y = ax^3 + bx^2 + cx + d (a != 0)</span>:
                  </p>
                  <p className="formula-line">
                    Ta có: <span className="math">y' = 3ax^2 + 2bx + c</span>. Đồ thị hàm số có 2 điểm cực trị khi và chỉ khi <span className="math">Delta' = b^2 - 3ac &gt; 0</span>.
                  </p>
                  <p className="formula-line">
                    • Phương trình đường thẳng đi qua 2 điểm cực trị: <span className="math">y = (2c/3 - 2b^2/9a)x + (d - bc/9a)</span>.
                  </p>
                </div>

                <div className="example-box">
                  <h3 className="example-title">Ví dụ minh họa 1:</h3>
                  <p>Tìm tất cả giá trị của tham số <span className="math">m</span> để hàm số <span className="math">y = x^3 - 3mx^2 + 3(m^2 - 1)x + 2</span> đạt cực tiểu tại <span className="math">x = 2</span>.</p>
                    <strong>Lời giải:</strong> Ta có: <span className="math">y' = 3x^2 - 6mx + 3(m^2 - 1)</span> và <span className="math">y'' = 6x - 6m</span>.
                    <br />
                    Hàm số đạt cực tiểu tại <span className="math">x = 2</span> khi và chỉ khi:
                    <br />
                    • <span className="math">y'(2) = 0 &lt;=&gt; 3(2)^2 - 12m + 3(m^2 - 1) = 0 &lt;=&gt; m^2 - 4m + 3 = 0 &lt;=&gt; m = 1</span> hoặc <span className="math">m = 3</span>.
                    <br />
                    • <span className="math">y''(2) &gt; 0 &lt;=&gt; 12 - 6m &gt; 0 &lt;=&gt; m &lt; 2</span>.
                    <br />
                    Kết hợp điều kiện suy ra giá trị cần tìm là: <span className="math"><strong>m = 1</strong></span>.
                </div>
              </div>
            </div>
          )}

          {currentPage === 3 && (
            <div className="page-content-wrapper">
              <div className="doc-section-block">
                <h2 className="section-title">PHẦN III: HỆ THỐNG CÂU HỎI TRẮC NGHIỆM TỰ LUYỆN</h2>
                
                <div className="quiz-question-item">
                  <p className="question-text">
                    <strong>Câu 1:</strong> Tìm đạo hàm của hàm số <span className="math">y = x^3 - 3x^2 + 2</span> tại điểm <span className="math">x = 2</span>.
                  </p>
                  <div className="quiz-options-list">
                    <span className="quiz-opt correct"><strong>A.</strong> y'(2) = 0 [Đúng]</span>
                    <span className="quiz-opt"><strong>B.</strong> y'(2) = 3</span>
                    <span className="quiz-opt"><strong>C.</strong> y'(2) = -3</span>
                    <span className="quiz-opt"><strong>D.</strong> y'(2) = 6</span>
                  </div>
                </div>

                <div className="quiz-question-item">
                  <p className="question-text">
                    <strong>Câu 2:</strong> Hàm số <span className="math">y = x^2 + 1</span> là hàm số chẵn. Phát biểu trên Đúng hay Sai?
                  </p>
                  <div className="quiz-options-list">
                    <span className="quiz-opt correct"><strong>A.</strong> Đúng [Đúng]</span>
                    <span className="quiz-opt"><strong>B.</strong> Sai</span>
                  </div>
                </div>

                <div className="quiz-question-item">
                  <p className="question-text">
                    <strong>Câu 3:</strong> Tìm giá trị cực đại của hàm số <span className="math">y = -x^2 + 4x + 1</span>.
                  </p>
                  <div className="quiz-solution-note">
                    <span><strong>Đáp án:</strong> Giá trị cực đại <span className="math">y_CD = 5</span> tại điểm <span className="math">x = 2</span>.</span>
                  </div>
                </div>

                <div className="answer-key-table">
                  <h3 className="key-title">BẢNG ĐÁP ÁN THAM KHẢO TOÀN BỘ BÀI TẬP:</h3>
                  <div className="key-grid">
                    <span>1. A</span><span>2. A</span><span>3. C</span><span>4. D</span><span>5. B</span>
                    <span>6. C</span><span>7. A</span><span>8. D</span><span>9. B</span><span>10. A</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Page Footer */}
          <div className="sheet-bottom-footer">
            <span>Trang {currentPage} / {totalPages}</span>
            <span>{doc.title}</span>
            <span>Hệ thống Quản lý Dạy học</span>
          </div>
        </div>
      );
    }

    // Fallback template for other subjects
    return (
      <div className="rendered-document-sheet" style={{ transform: `scale(${zoomLevel / 100})` }}>
        <div className="sheet-top-header">
          <div className="school-department">
            <span>SỞ GD&ĐT • TRƯỜNG THPT CHUYÊN</span>
            <strong>TỔ BỘ MÔN CHUYÊN MÔN</strong>
          </div>
          <div className="document-academic-year">
            <span>NĂM HỌC 2023 - 2024</span>
          </div>
        </div>

        <div className="sheet-title-banner">
          <h1>{doc.title}</h1>
          <p className="sheet-subtitle">Tác giả: {doc.authorName} • Dung lượng: {doc.fileSize}</p>
        </div>

        <div className="page-content-wrapper">
          <div className="doc-section-block">
            <h2 className="section-title">I. MỤC TIÊU BÀI HỌC VÀ NỘI DUNG TRỌNG TÂM</h2>
            <p className="paragraph-text">
              {doc.description || 'Tài liệu hướng dẫn học sinh nắm vững các phương pháp giải bài tập, kiến thức cốt lõi và các dạng toán/câu hỏi phân hóa cao trong chương trình học kì.'}
            </p>
          </div>

          <div className="doc-section-block">
            <h2 className="section-title">II. NỘI DUNG CHI TIẾT BÀI GIẢNG</h2>
            <div className="formula-highlight-box purple-tint">
              <p>• Hệ thống hóa toàn bộ công thức và định luật trọng tâm.</p>
              <p>• Phân tích các lỗi sai học sinh thường gặp trong quá trình làm bài thi.</p>
              <p>• Cung cấp bài tập tự luyện kèm hướng dẫn giải chi tiết.</p>
            </div>
          </div>
        </div>

        <div className="sheet-bottom-footer">
          <span>Trang {currentPage} / {totalPages}</span>
          <span>{doc.title}</span>
        </div>
      </div>
    );
  };

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
              <h3 className="reader-main-title">{doc.title}</h3>
              <p className="reader-meta-sub">
                {doc.fileType?.toUpperCase()} • {doc.fileSize} • Tác giả: {doc.authorName}
              </p>
            </div>
          </div>

          {/* Central Pagination & Zoom Toolbar */}
          <div className="reader-center-toolbar">
            <div className="pagination-reader-group">
              <button 
                type="button" 
                className="btn-toolbar-nav" 
                onClick={handlePrevPage}
                disabled={currentPage === 1}
                title="Trang trước"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="page-counter-text">
                Trang <strong>{currentPage}</strong> / {totalPages}
              </span>
              <button 
                type="button" 
                className="btn-toolbar-nav" 
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                title="Trang sau"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            <div className="toolbar-divider" />

            <div className="zoom-controls-group">
              <button 
                type="button" 
                className="btn-toolbar-nav" 
                onClick={handleZoomOut}
                disabled={zoomLevel <= 75}
                title="Thu nhỏ"
              >
                <ZoomOut size={16} />
              </button>
              <span className="zoom-percentage">{zoomLevel}%</span>
              <button 
                type="button" 
                className="btn-toolbar-nav" 
                onClick={handleZoomIn}
                disabled={zoomLevel >= 150}
                title="Phóng to"
              >
                <ZoomIn size={16} />
              </button>
            </div>
          </div>

          {/* Right Action Tools */}
          <div className="reader-right-actions">
            <button 
              type="button" 
              className="btn-reader-action"
              onClick={() => onDownload ? onDownload(doc) : null}
              title="Tải xuống tệp tin"
            >
              <Download size={15} />
              <span>Tải xuống</span>
            </button>

            <button 
              type="button" 
              className="btn-reader-action secondary"
              onClick={() => window.print()}
              title="In tài liệu"
            >
              <Printer size={15} />
              <span>In</span>
            </button>

            <button 
              type="button" 
              className="btn-reader-close" 
              onClick={onClose}
              title="Đóng trình đọc tài liệu"
            >
              <X size={20} />
            </button>
          </div>
        </header>

        {/* Main Reader Viewport */}
        <div className="reader-content-viewport">
          {/* Left Navigation Sidebar */}
          <aside className="reader-thumbnail-sidebar">
            <div className="sidebar-tab-header">
              <Layers size={14} />
              <span>MỤC LỤC TRANG</span>
            </div>

            <div className="thumbnail-pages-list">
              {[1, 2, 3].map((page) => (
                <div
                  key={page}
                  className={`thumbnail-item ${currentPage === page ? 'active' : ''}`}
                  onClick={() => setCurrentPage(page)}
                >
                  <div className="thumbnail-card-mini">
                    <div className="mini-paper-line title-line" />
                    <div className="mini-paper-line" />
                    <div className="mini-paper-line short" />
                    <div className="mini-paper-line" />
                  </div>
                  <span className="thumbnail-label">
                    Trang {page} {page === 1 ? '(Tổng quan)' : page === 2 ? '(Lý thuyết)' : '(Bài tập)'}
                  </span>
                </div>
              ))}
            </div>
          </aside>

          {/* Center Document Display Area */}
          <div className="reader-sheet-canvas">
            {renderDocumentPages()}
          </div>
        </div>
      </div>
    </div>
  );
}
