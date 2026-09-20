// File Name: LoginPage.jsx
// Description: Split-screen Login Page component connected to backend authentication API.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { 
  GraduationCap, 
  Mail, 
  Lock, 
  Eye, 
  EyeOff, 
  BookOpen, 
  Sparkles, 
  Layers, 
  CheckCircle2,
  AlertCircle 
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

export default function LoginPage() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});

  const { login, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // If already authenticated, redirect to target or home
  useEffect(() => {
    if (isAuthenticated) {
      let defaultPath = '/teacher';
      if (user?.role === 'Admin') {
        defaultPath = '/admin';
      } else if (user?.role === 'Student') {
        defaultPath = '/student';
      }
      const fromPath = location.state?.from?.pathname || defaultPath;
      navigate(fromPath, { replace: true });
    }
  }, [isAuthenticated, user, navigate, location]);

  // Regex patterns
  const PHONE_REGEX = /^0\d{9}$/;
  const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  const validateInputs = () => {
    const errors = {};
    const cleanId = identifier.trim();

    if (!cleanId) {
      errors.identifier = 'Vui lòng nhập Email hoặc Số điện thoại.';
    } else {
      const isValidPhone = PHONE_REGEX.test(cleanId);
      const isValidEmail = EMAIL_REGEX.test(cleanId);

      if (!isValidPhone && !isValidEmail) {
        errors.identifier = 'Email không hợp lệ hoặc Số điện thoại phải gồm 10 chữ số (bắt đầu bằng số 0).';
      }
    }

    if (!password) {
      errors.password = 'Vui lòng nhập Mật khẩu.';
    } else if (password.length < 6) {
      errors.password = 'Mật khẩu phải có ít nhất 6 ký tự.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!validateInputs()) {
      return;
    }

    setLoading(true);
    try {
      // Authenticate with backend API (supports both phone and email)
      const result = await login(identifier.trim(), password);
      
      setSuccessMsg(`Đăng nhập thành công! Chào mừng ${result.user?.full_name || 'bạn'}. Đang chuyển hướng...`);
      
      setTimeout(() => {
        const userRole = result.user?.role || '';
        let defaultPath = '/teacher';
        if (userRole === 'Admin') {
          defaultPath = '/admin';
        } else if (userRole === 'Student') {
          defaultPath = '/student';
        }
        const fromPath = location.state?.from?.pathname || defaultPath;
        navigate(fromPath, { replace: true });
      }, 500);
    } catch (err) {
      console.error('Login error:', err);
      const detail = err.response?.data?.detail;
      let msg = 'Đăng nhập thất bại. Vui lòng kiểm tra lại tài khoản hoặc mật khẩu.';
      
      if (typeof detail === 'string') {
        msg = detail;
      } else if (typeof detail === 'object' && detail?.message) {
        msg = detail.message;
      } else if (Array.isArray(detail) && detail[0]?.msg) {
        msg = detail[0].msg;
      }
      
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page-container">
      {/* LEFT PANEL - BRANDING & VALUE PROPOSITION */}
      <div className="login-hero-panel">
        {/* Brand Top Header */}
        <div className="brand-header">
          <div className="brand-icon-box">
            <GraduationCap size={26} strokeWidth={2.2} />
          </div>
          <div className="brand-title-group">
            <span className="brand-title">Academic Clarity</span>
            <span className="brand-badge">Smart LMS 2.0</span>
          </div>
        </div>

        {/* Rich Layered 3D Showcase Illustration in Center Background */}
        <div className="hero-illustration-container">
          {/* Background Ambient Glow */}
          <div className="hero-ambient-glow"></div>

          {/* Background Isometric Card 1 (Upper Left) */}
          <div className="isometric-card iso-card-back">
            <div className="iso-header">
              <div className="iso-dots">
                <span></span><span></span><span></span>
              </div>
              <span className="iso-tag">AI Analytics</span>
            </div>
            <div className="iso-chart-mock">
              <div className="chart-bar h-40"></div>
              <div className="chart-bar h-70"></div>
              <div className="chart-bar h-55"></div>
              <div className="chart-bar h-90 active"></div>
              <div className="chart-bar h-65"></div>
              <div className="chart-bar h-85"></div>
            </div>
          </div>

          {/* Main Foreground Isometric Card (Center) */}
          <div className="isometric-card iso-card-main">
            <div className="iso-main-header">
              <div className="iso-avatar-mini">GV</div>
              <div className="iso-main-meta">
                <span className="meta-title">Toán học 12 — Đề kiểm tra số 04</span>
                <span className="meta-sub">Đã nộp 38/40 học sinh • Tỷ lệ đúng 92%</span>
              </div>
            </div>
            <div className="iso-bars-group">
              <div className="iso-bar w-85"></div>
              <div className="iso-bar w-60"></div>
              <div className="iso-bar w-75"></div>
            </div>
            <div className="iso-footer-pills">
              <span className="iso-pill pill-green">Hoàn thành</span>
              <span className="iso-pill pill-blue">Độ khó: Vận dụng</span>
            </div>
          </div>

          {/* Background Isometric Card 2 (Lower Right) */}
          <div className="isometric-card iso-card-bottom">
            <div className="iso-math-preview">
              <span className="math-sym">f(x) = \int_0^\pi \sin(x) dx</span>
              <span className="math-status">Chấm tự động: 10/10</span>
            </div>
          </div>

          {/* Floating Smart Feature Badges */}
          <div className="floating-badge badge-top-right">
            <Sparkles size={16} className="badge-icon-gold" />
            <span>AI Tạo Đề Tự Động</span>
          </div>

          <div className="floating-badge badge-mid-left">
            <Layers size={16} className="badge-icon-blue" />
            <span>Theo Dõi Hành Vi 360°</span>
          </div>

          <div className="floating-badge badge-bot-right">
            <CheckCircle2 size={16} className="badge-icon-green" />
            <span>99.8% Độ Chính Xác</span>
          </div>
        </div>

        {/* Floating Glassmorphic Testimonial Card */}
        <div className="glass-hero-card">
          <div className="glass-card-icon-badge">
            <BookOpen size={22} strokeWidth={2.2} />
          </div>
          <h2 className="glass-card-title">Khơi nguồn cảm hứng học tập</h2>
          <p className="glass-card-desc">
            Nền tảng quản lý học tập hiện đại, giúp giáo viên và học sinh kết nối, tối ưu hóa quá trình giảng dạy và học tập một cách dễ dàng và hiệu quả.
          </p>

          <div className="glass-card-divider"></div>

          <div className="glass-card-social-proof">
            <div className="avatar-stack">
              <div className="avatar-badge avatar-1">HV</div>
              <div className="avatar-badge avatar-2">GV</div>
              <div className="avatar-badge avatar-3">+2k</div>
            </div>
            <span className="proof-label">Người dùng tin tưởng trên toàn quốc</span>
          </div>
        </div>

        {/* Footer Copyright */}
        <div className="hero-footer-copyright">
          © 2026 Academic Clarity. Mọi quyền được bảo lưu.
        </div>
      </div>

      {/* RIGHT PANEL - LOGIN FORM */}
      <div className="login-form-panel">
        <div className="login-form-wrapper">
          <div className="form-header">
            <h1 className="form-title">Chào mừng trở lại!</h1>
            <p className="form-subtitle">
              Vui lòng đăng nhập để tiếp tục hành trình học tập.
            </p>
          </div>

          {errorMsg && (
            <div className="form-alert alert-error">
              <AlertCircle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="form-alert alert-success">
              <CheckCircle2 size={18} />
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            {/* Field 1: Email hoặc Số điện thoại */}
            <div className="form-group">
              <label className="form-label" htmlFor="identifier-input">
                Email hoặc Số điện thoại
              </label>
              <div className="input-container">
                <span className="input-icon-left">
                  <Mail size={18} />
                </span>
                <input
                  id="identifier-input"
                  type="text"
                  className={`form-input ${fieldErrors.identifier ? 'input-error' : ''}`}
                  placeholder="0999000002 hoặc teacher@school.com"
                  value={identifier}
                  onChange={(e) => {
                    setIdentifier(e.target.value);
                    if (fieldErrors.identifier) {
                      setFieldErrors(prev => ({ ...prev, identifier: undefined }));
                    }
                  }}
                  autoComplete="username"
                />
              </div>
              {fieldErrors.identifier && (
                <span className="field-error-text">{fieldErrors.identifier}</span>
              )}
            </div>

            {/* Field 2: Mật khẩu */}
            <div className="form-group">
              <label className="form-label" htmlFor="password-input">
                Mật khẩu
              </label>
              <div className="input-container">
                <span className="input-icon-left">
                  <Lock size={18} />
                </span>
                <input
                  id="password-input"
                  type={showPassword ? 'text' : 'password'}
                  className={`form-input ${fieldErrors.password ? 'input-error' : ''}`}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (fieldErrors.password) {
                      setFieldErrors(prev => ({ ...prev, password: undefined }));
                    }
                  }}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="input-btn-right"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {fieldErrors.password && (
                <span className="field-error-text">{fieldErrors.password}</span>
              )}
            </div>

            {/* Remember Me & Forgot Password */}
            <div className="form-options-row">
              <label className="remember-me-label">
                <input
                  type="checkbox"
                  className="custom-checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span>Ghi nhớ đăng nhập</span>
              </label>
              <a href="#forgot-password" className="forgot-password-link">
                Quên mật khẩu?
              </a>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="btn-submit"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="spinner"></div>
                  <span>Đang xác thực...</span>
                </>
              ) : (
                <span>Đăng nhập</span>
              )}
            </button>
          </form>

          {/* Footer Note */}
          <div className="form-footer">
            <span>Chưa có tài khoản?</span>
            <a href="#contact-admin" className="admin-contact-link">
              Liên hệ quản trị viên trường.
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
