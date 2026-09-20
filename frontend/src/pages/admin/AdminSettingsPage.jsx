// File Name: AdminSettingsPage.jsx
// Description: Comprehensive System Settings screen for Admin portal with modular use cases: General, AI Assistant, Grading, Security, Notifications, and Backup.
// Created At: 2026-09-20
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React, { useState } from 'react';
import { 
  Settings, 
  Building2, 
  Sparkles, 
  Award, 
  ShieldCheck, 
  Mail, 
  Database, 
  Save, 
  RotateCw, 
  CheckCircle2, 
  AlertCircle, 
  Eye, 
  EyeOff, 
  Lock, 
  Sliders, 
  Server, 
  Clock, 
  Key, 
  Send, 
  Download, 
  Power, 
  FileText,
  HelpCircle,
  Cpu
} from 'lucide-react';
import './AdminSettingsPage.css';

export default function AdminSettingsPage() {
  const [activeTab, setActiveTab] = useState('general'); // 'general' | 'ai' | 'grading' | 'security' | 'notifications' | 'maintenance'
  const [toastMessage, setToastMessage] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [pingStatus, setPingStatus] = useState(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [isTestingSmtp, setIsTestingSmtp] = useState(false);

  // 1. General Settings State
  const [generalSettings, setGeneralSettings] = useState({
    schoolName: 'Trường THPT Chuyên Khoa học & Ứng dụng',
    schoolCode: 'THPT-CKHUD-01',
    address: 'Số 123 Đường Sáng Tạo, Quận Tri Thức, TP. Hồ Chí Minh',
    phone: '028 3822 1234',
    email: 'contact@school.edu.vn',
    academicYear: '2024 - 2025',
    semester: 'Học kỳ II',
    semesterStartDate: '2025-01-15',
    semesterEndDate: '2025-05-30',
    gradeLockDeadline: '2025-05-25'
  });

  // 2. AI Services State
  const [aiSettings, setAiSettings] = useState({
    provider: 'Google Gemini AI',
    defaultModel: 'gemini-1.5-pro-latest',
    apiKey: 'AIzaSyA8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q',
    dailyTokenLimitPerTeacher: 150000,
    enableAutoGrading: true,
    enableBloomGenerator: true,
    enableVisionOcr: true,
    enableEarlyAlertAnalysis: true,
    temperature: 0.4
  });

  // 3. Grading Rules State
  const [gradingSettings, setGradingSettings] = useState({
    gradingScale: 'scale10', // scale10 | gpa4
    weightRegular: 20, // 20%
    weightMidterm: 30, // 30%
    weightFinal: 50,   // 50%
    roundingPrecision: '0.1', // '0.1' | '0.01'
    thresholdExcellent: 9.0,
    thresholdGood: 8.0,
    thresholdAverage: 6.5,
    thresholdPass: 5.0,
    allowTeacherScoreAdjustment: true
  });

  // 4. Security State
  const [securitySettings, setSecuritySettings] = useState({
    sessionTimeoutMinutes: 60,
    minPasswordLength: 8,
    requireUppercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
    enableTwoFactorAdmin: true,
    enableTwoFactorTeachers: false,
    maxFailedLogins: 5,
    lockoutDurationMinutes: 15
  });

  // 5. Notifications & SMTP State
  const [smtpSettings, setSmtpSettings] = useState({
    smtpHost: 'smtp.gmail.com',
    smtpPort: 587,
    senderEmail: 'notifications@school.edu.vn',
    senderName: 'SmartLMS System',
    smtpPassword: '••••••••••••••••',
    enableSsl: true,
    notifyExamResults: true,
    notifyWeeklyAttendance: true,
    notifyEarlyRiskAlerts: true
  });

  // 6. Maintenance & Backup State
  const [maintenanceSettings, setMaintenanceSettings] = useState({
    maintenanceMode: false,
    maintenanceMessage: 'Hệ thống đang được nâng cấp bảo trì định kỳ. Quý thầy cô và học sinh vui lòng quay lại sau 06:00 AM.',
    autoBackupDaily: true,
    autoBackupTime: '02:00',
    backupStorageLocation: 'AWS S3 Cold Storage'
  });

  const [backupSnapshots, setBackupSnapshots] = useState([
    { id: 'snap-01', filename: 'smartlms_db_snapshot_2026-09-20.sql.gz', size: '142 MB', createdAt: '2026-09-20 02:00:15', status: 'completed' },
    { id: 'snap-02', filename: 'smartlms_db_snapshot_2026-09-19.sql.gz', size: '139 MB', createdAt: '2026-09-19 02:00:10', status: 'completed' },
    { id: 'snap-03', filename: 'smartlms_db_snapshot_2026-09-18.sql.gz', size: '138 MB', createdAt: '2026-09-18 02:00:12', status: 'completed' }
  ]);

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  const handleSaveSettings = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      showToast('Đã lưu cấu hình cài đặt hệ thống thành công!');
    }, 600);
  };

  const handlePingAi = () => {
    setPingStatus('testing');
    setTimeout(() => {
      setPingStatus({
        status: 'online',
        latency: '115ms',
        model: aiSettings.defaultModel
      });
      showToast('Kiểm tra API AI Gemini thành công! Độ trễ: 115ms (Ổn định)');
    }, 800);
  };

  const handleTestSmtp = () => {
    setIsTestingSmtp(true);
    setTimeout(() => {
      setIsTestingSmtp(false);
      showToast('Đã gửi email thử nghiệm thành công đến địa chỉ người gửi!');
    }, 900);
  };

  const handleCreateBackupNow = () => {
    showToast('Đang tạo bản sao lưu dữ liệu toàn hệ thống...');
    setTimeout(() => {
      const now = new Date();
      const newSnap = {
        id: `snap-${Date.now()}`,
        filename: `smartlms_db_snapshot_manual_${now.toISOString().slice(0, 10)}.sql.gz`,
        size: '144 MB',
        createdAt: `${now.toISOString().slice(0, 10)} ${now.toLocaleTimeString('vi-VN')}`,
        status: 'completed'
      };
      setBackupSnapshots(prev => [newSnap, ...prev]);
      showToast('Tạo bản sao lưu dữ liệu thành công!');
    }, 1200);
  };

  return (
    <div className="admin-settings-container">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="admin-toast">
          <CheckCircle2 size={18} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 1. Header Section */}
      <section className="settings-page-header">
        <div className="settings-header-title-block">
          <div className="settings-tag">
            <span className="settings-status-dot purple"></span>
            <span>TRUNG TÂM CẤU HÌNH & QUẢN TRỊ HỆ THỐNG</span>
            <span className="dot">•</span>
            <span className="tag-accent">SMARTLMS V2.4</span>
          </div>
          <div className="settings-title-row">
            <h1 className="settings-page-title">Cài đặt hệ thống</h1>
            <Settings size={24} className="settings-title-icon" />
          </div>
          <p className="settings-page-subtitle">
            Cấu hình tham số vận hành toàn trường, tích hợp AI Gemini, quy chuẩn thang điểm, chính sách bảo mật và sao lưu dữ liệu.
          </p>
        </div>

        <div className="settings-header-actions">
          <button 
            type="button" 
            className="btn-settings-save"
            onClick={handleSaveSettings}
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <RotateCw size={16} className="spinner" />
                <span>Đang lưu...</span>
              </>
            ) : (
              <>
                <Save size={16} />
                <span>Lưu tất cả thay đổi</span>
              </>
            )}
          </button>
        </div>
      </section>

      {/* 2. Navigation Tabs */}
      <section className="settings-tabs-bar">
        <button 
          type="button" 
          className={`settings-tab-item ${activeTab === 'general' ? 'active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          <Building2 size={17} />
          <span>Cấu hình chung</span>
        </button>

        <button 
          type="button" 
          className={`settings-tab-item ${activeTab === 'ai' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai')}
        >
          <Sparkles size={17} />
          <span>Trợ lý AI & Dịch vụ</span>
        </button>

        <button 
          type="button" 
          className={`settings-tab-item ${activeTab === 'grading' ? 'active' : ''}`}
          onClick={() => setActiveTab('grading')}
        >
          <Award size={17} />
          <span>Quy chế Điểm & Thang đo</span>
        </button>

        <button 
          type="button" 
          className={`settings-tab-item ${activeTab === 'security' ? 'active' : ''}`}
          onClick={() => setActiveTab('security')}
        >
          <ShieldCheck size={17} />
          <span>Bảo mật & Xác thực</span>
        </button>

        <button 
          type="button" 
          className={`settings-tab-item ${activeTab === 'notifications' ? 'active' : ''}`}
          onClick={() => setActiveTab('notifications')}
        >
          <Mail size={17} />
          <span>Email & Thông báo</span>
        </button>

        <button 
          type="button" 
          className={`settings-tab-item ${activeTab === 'maintenance' ? 'active' : ''}`}
          onClick={() => setActiveTab('maintenance')}
        >
          <Database size={17} />
          <span>Sao lưu & Bảo trì</span>
        </button>
      </section>

      {/* 3. Main Settings Panels Content */}
      <div className="settings-content-area">
        {/* ================= TAB 1: CẤU HÌNH CHUNG ================= */}
        {activeTab === 'general' && (
          <div className="settings-card-panel">
            <div className="settings-panel-header">
              <div className="panel-title-group">
                <h3 className="panel-main-title">Thông tin cơ sở giáo dục & Niên khóa</h3>
                <p className="panel-sub-desc">Cấu hình thông tin đại diện của nhà trường, niên khóa kích hoạt và chu kỳ khóa sổ điểm.</p>
              </div>
            </div>

            <div className="settings-form-grid">
              <div className="settings-form-group span-2">
                <label className="settings-label">Tên trường học *</label>
                <input 
                  type="text" 
                  className="settings-input"
                  value={generalSettings.schoolName}
                  onChange={e => setGeneralSettings(p => ({ ...p, schoolName: e.target.value }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Mã định danh trường học *</label>
                <input 
                  type="text" 
                  className="settings-input"
                  value={generalSettings.schoolCode}
                  onChange={e => setGeneralSettings(p => ({ ...p, schoolCode: e.target.value }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Số điện thoại liên hệ</label>
                <input 
                  type="text" 
                  className="settings-input"
                  value={generalSettings.phone}
                  onChange={e => setGeneralSettings(p => ({ ...p, phone: e.target.value }))}
                />
              </div>

              <div className="settings-form-group span-2">
                <label className="settings-label">Địa chỉ trụ sở</label>
                <input 
                  type="text" 
                  className="settings-input"
                  value={generalSettings.address}
                  onChange={e => setGeneralSettings(p => ({ ...p, address: e.target.value }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Email liên hệ chính thức</label>
                <input 
                  type="email" 
                  className="settings-input"
                  value={generalSettings.email}
                  onChange={e => setGeneralSettings(p => ({ ...p, email: e.target.value }))}
                />
              </div>
            </div>

            <hr className="settings-divider" />

            <div className="settings-panel-header">
              <div className="panel-title-group">
                <h4 className="panel-section-title">Niên khóa & Học kỳ hoạt động</h4>
                <p className="panel-sub-desc">Thiết lập học kỳ hiện tại đang giảng dạy và thời hạn giáo viên hoàn tất nộp điểm.</p>
              </div>
            </div>

            <div className="settings-form-grid">
              <div className="settings-form-group">
                <label className="settings-label">Niên khóa hiện tại</label>
                <select 
                  className="settings-select"
                  value={generalSettings.academicYear}
                  onChange={e => setGeneralSettings(p => ({ ...p, academicYear: e.target.value }))}
                >
                  <option value="2024 - 2025">Năm học 2024 - 2025</option>
                  <option value="2023 - 2024">Năm học 2023 - 2024</option>
                  <option value="2025 - 2026">Năm học 2025 - 2026</option>
                </select>
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Học kỳ hiện tại</label>
                <select 
                  className="settings-select"
                  value={generalSettings.semester}
                  onChange={e => setGeneralSettings(p => ({ ...p, semester: e.target.value }))}
                >
                  <option value="Học kỳ II">Học kỳ II</option>
                  <option value="Học kỳ I">Học kỳ I</option>
                  <option value="Học kỳ Hè">Học kỳ Hè</option>
                </select>
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Ngày bắt đầu học kỳ</label>
                <input 
                  type="date" 
                  className="settings-input"
                  value={generalSettings.semesterStartDate}
                  onChange={e => setGeneralSettings(p => ({ ...p, semesterStartDate: e.target.value }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Ngày kết thúc học kỳ</label>
                <input 
                  type="date" 
                  className="settings-input"
                  value={generalSettings.semesterEndDate}
                  onChange={e => setGeneralSettings(p => ({ ...p, semesterEndDate: e.target.value }))}
                />
              </div>

              <div className="settings-form-group span-2">
                <label className="settings-label">Hạn chót khóa sổ điểm học kỳ (Deadline giáo viên)</label>
                <input 
                  type="date" 
                  className="settings-input"
                  value={generalSettings.gradeLockDeadline}
                  onChange={e => setGeneralSettings(p => ({ ...p, gradeLockDeadline: e.target.value }))}
                />
                <span className="settings-help-text">
                  Sau thời điểm này, hệ thống sẽ tự động khóa chức năng chỉnh sửa điểm của giáo viên bộ môn.
                </span>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 2: TRỢ LÝ AI & DỊCH VỤ ================= */}
        {activeTab === 'ai' && (
          <div className="settings-card-panel">
            <div className="settings-panel-header">
              <div className="panel-title-group">
                <h3 className="panel-main-title">Cấu hình mô hình ngôn ngữ lớn (LLM) & Trợ lý AI</h3>
                <p className="panel-sub-desc">Quản lý tích hợp Google Gemini API, định mức sinh bài tập tự động và phân tích học tập.</p>
              </div>

              <div className="panel-action-box">
                <button 
                  type="button" 
                  className="btn-ping-ai"
                  onClick={handlePingAi}
                  disabled={pingStatus === 'testing'}
                >
                  <Sparkles size={16} />
                  <span>{pingStatus === 'testing' ? 'Đang kiểm tra...' : 'Kiểm tra kết nối API'}</span>
                </button>
              </div>
            </div>

            {/* Ping status display badge */}
            {pingStatus && pingStatus !== 'testing' && (
              <div className="ai-status-banner">
                <div className="ai-banner-left">
                  <CheckCircle2 size={18} className="text-green" />
                  <div>
                    <h5 className="ai-banner-title">Kết nối API Gemini hoạt động tốt</h5>
                    <p className="ai-banner-desc">Độ trễ máy chủ: <strong>{pingStatus.latency}</strong> • Model phản hồi: <strong>{pingStatus.model}</strong></p>
                  </div>
                </div>
                <span className="status-pill green">Sẵn sàng</span>
              </div>
            )}

            <div className="settings-form-grid">
              <div className="settings-form-group">
                <label className="settings-label">Nhà cung cấp Dịch vụ AI</label>
                <select 
                  className="settings-select"
                  value={aiSettings.provider}
                  onChange={e => setAiSettings(p => ({ ...p, provider: e.target.value }))}
                >
                  <option value="Google Gemini AI">Google Gemini AI (Khuyến nghị)</option>
                  <option value="OpenAI GPT-4o">OpenAI GPT-4o / GPT-4o-mini</option>
                  <option value="Anthropic Claude">Anthropic Claude 3.5 Sonnet</option>
                </select>
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Model AI mặc định</label>
                <select 
                  className="settings-select"
                  value={aiSettings.defaultModel}
                  onChange={e => setAiSettings(p => ({ ...p, defaultModel: e.target.value }))}
                >
                  <option value="gemini-1.5-pro-latest">Gemini 1.5 Pro (Độ chính xác cao, phân tích sâu)</option>
                  <option value="gemini-1.5-flash-latest">Gemini 1.5 Flash (Tốc độ cực nhanh, tiết kiệm chi phí)</option>
                </select>
              </div>

              <div className="settings-form-group span-2">
                <label className="settings-label">API Key bảo mật *</label>
                <div className="password-input-wrapper">
                  <input 
                    type={showApiKey ? 'text' : 'password'}
                    className="settings-input"
                    value={aiSettings.apiKey}
                    onChange={e => setAiSettings(p => ({ ...p, apiKey: e.target.value }))}
                  />
                  <button 
                    type="button" 
                    className="btn-toggle-eye"
                    onClick={() => setShowApiKey(!showApiKey)}
                  >
                    {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                <span className="settings-help-text">API Key được mã hóa lưu trữ bằng chuẩn bảo mật AES-256 trên máy chủ.</span>
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Hạn mức Token / Ngày / Giáo viên</label>
                <input 
                  type="number" 
                  className="settings-input"
                  value={aiSettings.dailyTokenLimitPerTeacher}
                  onChange={e => setAiSettings(p => ({ ...p, dailyTokenLimitPerTeacher: Number(e.target.value) }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Nhiệt độ sáng tạo (Temperature: 0.0 - 1.0)</label>
                <input 
                  type="number" 
                  step="0.1" 
                  min="0" 
                  max="1" 
                  className="settings-input"
                  value={aiSettings.temperature}
                  onChange={e => setAiSettings(p => ({ ...p, temperature: Number(e.target.value) }))}
                />
              </div>
            </div>

            <hr className="settings-divider" />

            <h4 className="panel-section-title">Kích hoạt các tính năng AI trong hệ thống</h4>
            
            <div className="settings-toggle-list">
              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Tự động chấm bài & Gợi ý nhận xét (AI Auto-Grading)</h5>
                  <p className="toggle-desc">Tự động đối soát đáp án trắc nghiệm và gợi ý khung điểm, chấm bài tự luận cho giáo viên.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={aiSettings.enableAutoGrading}
                    onChange={e => setAiSettings(p => ({ ...p, enableAutoGrading: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>

              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Sinh bài tập & Đề thi phân hóa theo chuẩn Bloom</h5>
                  <p className="toggle-desc">Cho phép giáo viên dùng AI tạo nhanh câu hỏi trắc nghiệm/tự luận theo 4 bậc nhận thức.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={aiSettings.enableBloomGenerator}
                    onChange={e => setAiSettings(p => ({ ...p, enableBloomGenerator: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>

              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Quét ảnh & Nhận diện chữ viết tay học sinh (Gemini Vision OCR)</h5>
                  <p className="toggle-desc">Chuyển đổi bài làm chụp từ điện thoại thành văn bản và công thức toán học LaTeX tự động.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={aiSettings.enableVisionOcr}
                    onChange={e => setAiSettings(p => ({ ...p, enableVisionOcr: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>

              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Phân tích hành vi & Cảnh báo học sinh nguy cơ sa sút</h5>
                  <p className="toggle-desc">AI định kỳ quét điểm và tần suất nộp bài để gửi cảnh báo can thiệp sớm tới GVCN và BGH.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={aiSettings.enableEarlyAlertAnalysis}
                    onChange={e => setAiSettings(p => ({ ...p, enableEarlyAlertAnalysis: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 3: QUY CHẾ ĐIỂM & THANG ĐO ================= */}
        {activeTab === 'grading' && (
          <div className="settings-card-panel">
            <div className="settings-panel-header">
              <div className="panel-title-group">
                <h3 className="panel-main-title">Quy chế tính điểm & Xếp loại học lực</h3>
                <p className="panel-sub-desc">Cấu hình thang điểm chuẩn GDPT 2018, tỷ trọng trọng số điểm thành phần và ngưỡng xếp loại.</p>
              </div>
            </div>

            <div className="settings-form-grid">
              <div className="settings-form-group">
                <label className="settings-label">Thang điểm áp dụng</label>
                <select 
                  className="settings-select"
                  value={gradingSettings.gradingScale}
                  onChange={e => setGradingSettings(p => ({ ...p, gradingScale: e.target.value }))}
                >
                  <option value="scale10">Thang điểm 10 (Chuẩn Bộ Giáo dục & Đào tạo)</option>
                  <option value="gpa4">Thang điểm GPA 4.0 (Chuẩn quốc tế)</option>
                </select>
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Quy chuẩn làm tròn điểm</label>
                <select 
                  className="settings-select"
                  value={gradingSettings.roundingPrecision}
                  onChange={e => setGradingSettings(p => ({ ...p, roundingPrecision: e.target.value }))}
                >
                  <option value="0.1">Làm tròn đến 1 chữ số thập phân (Ví dụ: 7.8)</option>
                  <option value="0.01">Làm tròn đến 2 chữ số thập phân (Ví dụ: 7.85)</option>
                </select>
              </div>
            </div>

            <hr className="settings-divider" />

            <h4 className="panel-section-title">Tỷ trọng trọng số điểm thành phần (%)</h4>
            <div className="settings-weights-row">
              <div className="weight-card">
                <span className="weight-badge purple">Hệ số 1</span>
                <h5 className="weight-title">Đánh giá thường xuyên</h5>
                <div className="weight-input-group">
                  <input 
                    type="number" 
                    className="settings-input text-center font-bold"
                    value={gradingSettings.weightRegular}
                    onChange={e => setGradingSettings(p => ({ ...p, weightRegular: Number(e.target.value) }))}
                  />
                  <span className="weight-unit">%</span>
                </div>
                <p className="weight-hint">Bài tập hàng ngày & Kiểm tra 15p</p>
              </div>

              <div className="weight-card">
                <span className="weight-badge blue">Hệ số 2</span>
                <h5 className="weight-title">Đánh giá giữa kỳ</h5>
                <div className="weight-input-group">
                  <input 
                    type="number" 
                    className="settings-input text-center font-bold"
                    value={gradingSettings.weightMidterm}
                    onChange={e => setGradingSettings(p => ({ ...p, weightMidterm: Number(e.target.value) }))}
                  />
                  <span className="weight-unit">%</span>
                </div>
                <p className="weight-hint">Bài kiểm tra giữa học kỳ</p>
              </div>

              <div className="weight-card">
                <span className="weight-badge green">Hệ số 3</span>
                <h5 className="weight-title">Đánh giá cuối kỳ</h5>
                <div className="weight-input-group">
                  <input 
                    type="number" 
                    className="settings-input text-center font-bold"
                    value={gradingSettings.weightFinal}
                    onChange={e => setGradingSettings(p => ({ ...p, weightFinal: Number(e.target.value) }))}
                  />
                  <span className="weight-unit">%</span>
                </div>
                <p className="weight-hint">Bài thi khảo sát kết thúc kỳ</p>
              </div>
            </div>

            <div className="weights-sum-banner">
              <span>Tổng tỷ trọng hiện tại: <strong>{gradingSettings.weightRegular + gradingSettings.weightMidterm + gradingSettings.weightFinal}%</strong></span>
              {gradingSettings.weightRegular + gradingSettings.weightMidterm + gradingSettings.weightFinal === 100 ? (
                <span className="status-pill green">Hợp lệ (Đạt 100%)</span>
              ) : (
                <span className="status-pill red">Chưa đạt 100% (Vui lòng cân bằng lại)</span>
              )}
            </div>

            <hr className="settings-divider" />

            <h4 className="panel-section-title">Ngưỡng điểm xếp loại học lực học kỳ</h4>
            <div className="settings-form-grid">
              <div className="settings-form-group">
                <label className="settings-label">Mức Xuất sắc (Điểm TB ≥)</label>
                <input 
                  type="number" 
                  step="0.1" 
                  className="settings-input"
                  value={gradingSettings.thresholdExcellent}
                  onChange={e => setGradingSettings(p => ({ ...p, thresholdExcellent: Number(e.target.value) }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Mức Giỏi (Điểm TB ≥)</label>
                <input 
                  type="number" 
                  step="0.1" 
                  className="settings-input"
                  value={gradingSettings.thresholdGood}
                  onChange={e => setGradingSettings(p => ({ ...p, thresholdGood: Number(e.target.value) }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Mức Khá (Điểm TB ≥)</label>
                <input 
                  type="number" 
                  step="0.1" 
                  className="settings-input"
                  value={gradingSettings.thresholdAverage}
                  onChange={e => setGradingSettings(p => ({ ...p, thresholdAverage: Number(e.target.value) }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Mức Đạt / Trung bình (Điểm TB ≥)</label>
                <input 
                  type="number" 
                  step="0.1" 
                  className="settings-input"
                  value={gradingSettings.thresholdPass}
                  onChange={e => setGradingSettings(p => ({ ...p, thresholdPass: Number(e.target.value) }))}
                />
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 4: BẢO MẬT & XÁC THỰC ================= */}
        {activeTab === 'security' && (
          <div className="settings-card-panel">
            <div className="settings-panel-header">
              <div className="panel-title-group">
                <h3 className="panel-main-title">Chính sách bảo mật, phiên làm việc & xác thực</h3>
                <p className="panel-sub-desc">Quy định độ phức tạp mật khẩu, thời gian hết hạn phiên và biện pháp phòng chống tấn công brute-force.</p>
              </div>
            </div>

            <div className="settings-form-grid">
              <div className="settings-form-group">
                <label className="settings-label">Thời gian hết hạn phiên đăng nhập (Session Timeout)</label>
                <select 
                  className="settings-select"
                  value={securitySettings.sessionTimeoutMinutes}
                  onChange={e => setSecuritySettings(p => ({ ...p, sessionTimeoutMinutes: Number(e.target.value) }))}
                >
                  <option value={15}>15 phút không hoạt động</option>
                  <option value={30}>30 phút không hoạt động</option>
                  <option value={60}>60 phút không hoạt động (Mặc định)</option>
                  <option value={120}>120 phút không hoạt động</option>
                </select>
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Giới hạn số lần đăng nhập sai tối đa</label>
                <input 
                  type="number" 
                  className="settings-input"
                  value={securitySettings.maxFailedLogins}
                  onChange={e => setSecuritySettings(p => ({ ...p, maxFailedLogins: Number(e.target.value) }))}
                />
                <span className="settings-help-text">Tự động tạm khóa tài khoản sau số lần nhập sai liên tiếp.</span>
              </div>
            </div>

            <hr className="settings-divider" />

            <h4 className="panel-section-title">Chính sách mật khẩu bắt buộc</h4>
            <div className="settings-toggle-list">
              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Yêu cầu độ dài tối thiểu 8 ký tự</h5>
                  <p className="toggle-desc">Ngăn chặn người dùng đặt mật khẩu quá ngắn hoặc dễ đoán.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={securitySettings.minPasswordLength >= 8}
                    onChange={e => setSecuritySettings(p => ({ ...p, minPasswordLength: e.target.checked ? 8 : 6 }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>

              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Bắt buộc chứa chữ hoa và chữ số</h5>
                  <p className="toggle-desc">Mật khẩu phải có ít nhất 1 chữ cái in hoa (A-Z) và 1 chữ số (0-9).</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={securitySettings.requireUppercase && securitySettings.requireNumbers}
                    onChange={e => setSecuritySettings(p => ({ ...p, requireUppercase: e.target.checked, requireNumbers: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>

              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Bắt buộc chứa ký tự đặc biệt (!@#$%^&*)</h5>
                  <p className="toggle-desc">Tăng cường khả năng chống bẻ khóa từ điển hoặc vét cạn mật khẩu.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={securitySettings.requireSpecialChars}
                    onChange={e => setSecuritySettings(p => ({ ...p, requireSpecialChars: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>

              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Bắt buộc xác thực 2 bước (2FA) cho Ban Giám Hiệu & Admin</h5>
                  <p className="toggle-desc">Yêu cầu nhập mã OTP bảo mật gửi qua email khi đăng nhập tài khoản có quyền quản trị cao.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={securitySettings.enableTwoFactorAdmin}
                    onChange={e => setSecuritySettings(p => ({ ...p, enableTwoFactorAdmin: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 5: EMAIL & THÔNG BÁO ================= */}
        {activeTab === 'notifications' && (
          <div className="settings-card-panel">
            <div className="settings-panel-header">
              <div className="panel-title-group">
                <h3 className="panel-main-title">Cấu hình máy chủ gửi Email SMTP & Tự động thông báo</h3>
                <p className="panel-sub-desc">Thiết lập thông số kết nối gửi email tự động tới phụ huynh, giáo viên và học sinh.</p>
              </div>

              <div className="panel-action-box">
                <button 
                  type="button" 
                  className="btn-test-smtp"
                  onClick={handleTestSmtp}
                  disabled={isTestingSmtp}
                >
                  <Send size={16} />
                  <span>{isTestingSmtp ? 'Đang gửi test...' : 'Gửi email thử nghiệm'}</span>
                </button>
              </div>
            </div>

            <div className="settings-form-grid">
              <div className="settings-form-group span-2">
                <label className="settings-label">Máy chủ SMTP Host</label>
                <input 
                  type="text" 
                  className="settings-input"
                  value={smtpSettings.smtpHost}
                  onChange={e => setSmtpSettings(p => ({ ...p, smtpHost: e.target.value }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Cổng SMTP Port</label>
                <input 
                  type="number" 
                  className="settings-input"
                  value={smtpSettings.smtpPort}
                  onChange={e => setSmtpSettings(p => ({ ...p, smtpPort: Number(e.target.value) }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Tên hiển thị người gửi</label>
                <input 
                  type="text" 
                  className="settings-input"
                  value={smtpSettings.senderName}
                  onChange={e => setSmtpSettings(p => ({ ...p, senderName: e.target.value }))}
                />
              </div>

              <div className="settings-form-group span-2">
                <label className="settings-label">Địa chỉ Email người gửi</label>
                <input 
                  type="email" 
                  className="settings-input"
                  value={smtpSettings.senderEmail}
                  onChange={e => setSmtpSettings(p => ({ ...p, senderEmail: e.target.value }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Mật khẩu ứng dụng SMTP</label>
                <input 
                  type="password" 
                  className="settings-input"
                  value={smtpSettings.smtpPassword}
                  onChange={e => setSmtpSettings(p => ({ ...p, smtpPassword: e.target.value }))}
                />
              </div>
            </div>

            <hr className="settings-divider" />

            <h4 className="panel-section-title">Kịch bản kích hoạt email tự động</h4>
            <div className="settings-toggle-list">
              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Gửi thông báo kết quả bài thi & bài tập lớn</h5>
                  <p className="toggle-desc">Tự động gửi phiếu điểm tổng kết bài thi kèm nhận xét của giáo viên tới email học sinh.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={smtpSettings.notifyExamResults}
                    onChange={e => setSmtpSettings(p => ({ ...p, notifyExamResults: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>

              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Báo cáo chuyên cần & mức độ tương tác hàng tuần</h5>
                  <p className="toggle-desc">Gửi bảng tổng hợp tỷ lệ tham gia lớp học và hoàn thành bài tập vào sáng thứ Hai.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={smtpSettings.notifyWeeklyAttendance}
                    onChange={e => setSmtpSettings(p => ({ ...p, notifyWeeklyAttendance: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>

              <div className="settings-toggle-item">
                <div className="toggle-info">
                  <h5 className="toggle-title">Cảnh báo học sinh nguy cơ sa sút đến GVCN</h5>
                  <p className="toggle-desc">Gửi thông báo tức thời khi phát hiện học sinh bị dưới 5.0 liên tiếp hoặc nghỉ học không phép.</p>
                </div>
                <label className="settings-switch">
                  <input 
                    type="checkbox" 
                    checked={smtpSettings.notifyEarlyRiskAlerts}
                    onChange={e => setSmtpSettings(p => ({ ...p, notifyEarlyRiskAlerts: e.target.checked }))}
                  />
                  <span className="switch-slider"></span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 6: SAO LƯU & BẢO TRÌ ================= */}
        {activeTab === 'maintenance' && (
          <div className="settings-card-panel">
            <div className="settings-panel-header">
              <div className="panel-title-group">
                <h3 className="panel-main-title">Sao lưu dữ liệu tự động & Chế độ bảo trì hệ thống</h3>
                <p className="panel-sub-desc">Quản lý snapshot cơ sở dữ liệu PostgreSQL và kích hoạt chế độ bảo trì toàn trường khi nâng cấp.</p>
              </div>

              <div className="panel-action-box">
                <button 
                  type="button" 
                  className="btn-backup-now"
                  onClick={handleCreateBackupNow}
                >
                  <Database size={16} />
                  <span>Tạo bản sao lưu ngay</span>
                </button>
              </div>
            </div>

            {/* Maintenance Mode Warning Card */}
            <div className={`maintenance-alert-box ${maintenanceSettings.maintenanceMode ? 'active' : ''}`}>
              <div className="maintenance-box-left">
                <Power size={22} className={maintenanceSettings.maintenanceMode ? 'text-amber' : 'text-gray'} />
                <div>
                  <h4 className="maintenance-box-title">Chế độ bảo trì hệ thống (Maintenance Mode)</h4>
                  <p className="maintenance-box-desc">
                    Khi kích hoạt, chỉ tài khoản Admin mới có thể đăng nhập. Học sinh và giáo viên sẽ nhận được thông báo bảo trì.
                  </p>
                </div>
              </div>
              <label className="settings-switch">
                <input 
                  type="checkbox" 
                  checked={maintenanceSettings.maintenanceMode}
                  onChange={e => setMaintenanceSettings(p => ({ ...p, maintenanceMode: e.target.checked }))}
                />
                <span className="switch-slider"></span>
              </label>
            </div>

            {maintenanceSettings.maintenanceMode && (
              <div className="settings-form-group" style={{ marginTop: '16px' }}>
                <label className="settings-label">Thông điệp bảo trì hiển thị trên màn hình đăng nhập</label>
                <textarea 
                  className="settings-textarea"
                  rows={3}
                  value={maintenanceSettings.maintenanceMessage}
                  onChange={e => setMaintenanceSettings(p => ({ ...p, maintenanceMessage: e.target.value }))}
                />
              </div>
            )}

            <hr className="settings-divider" />

            <div className="settings-form-grid">
              <div className="settings-form-group">
                <label className="settings-label">Thời điểm tự động sao lưu Database hàng ngày</label>
                <input 
                  type="time" 
                  className="settings-input"
                  value={maintenanceSettings.autoBackupTime}
                  onChange={e => setMaintenanceSettings(p => ({ ...p, autoBackupTime: e.target.value }))}
                />
              </div>

              <div className="settings-form-group">
                <label className="settings-label">Vị trí lưu trữ bản sao lưu</label>
                <select 
                  className="settings-select"
                  value={maintenanceSettings.backupStorageLocation}
                  onChange={e => setMaintenanceSettings(p => ({ ...p, backupStorageLocation: e.target.value }))}
                >
                  <option value="AWS S3 Cold Storage">AWS S3 Cold Storage (An toàn cao)</option>
                  <option value="Google Cloud Storage">Google Cloud Storage Archive</option>
                  <option value="Local Server">Bộ nhớ cục bộ máy chủ trường học</option>
                </select>
              </div>
            </div>

            <hr className="settings-divider" />

            <h4 className="panel-section-title">Danh sách các bản sao lưu gần nhất</h4>
            <div className="backups-table-container">
              <table className="backups-table">
                <thead>
                  <tr>
                    <th>TÊN BẢN SAO LƯU</th>
                    <th>DUNG LƯỢNG</th>
                    <th>THỜI ĐIỂM TẠO</th>
                    <th className="text-center">TRẠNG THÁI</th>
                    <th className="text-right">THAO TÁC</th>
                  </tr>
                </thead>
                <tbody>
                  {backupSnapshots.map(snap => (
                    <tr key={snap.id}>
                      <td className="font-semibold text-dark">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <FileText size={16} className="text-purple" />
                          <span>{snap.filename}</span>
                        </div>
                      </td>
                      <td>{snap.size}</td>
                      <td className="text-muted">{snap.createdAt}</td>
                      <td className="text-center">
                        <span className="status-pill green">Thành công</span>
                      </td>
                      <td className="text-right">
                        <button 
                          type="button" 
                          className="btn-download-backup"
                          onClick={() => showToast(`Bắt đầu tải xuống bản sao lưu ${snap.filename}...`)}
                        >
                          <Download size={14} />
                          <span>Tải xuống</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
