// File Name: QuestionMedia.jsx
// Description: Shared renderer for question media blocks (cropped figures and tables)
// extracted during scan import. Clicking an image opens an inline lightbox on the
// current page instead of a new browser tab.

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, ZoomIn } from 'lucide-react';
import { resolveMediaUrl } from '../common/MathRenderer';
import MarkdownTable from '../common/MarkdownTable';

/**
 * Collect media blocks of a question: the cropped figure (image_url) plus any
 * image/table segments produced by the OCR parser.
 * Returns { images: [{url, alt}], tables: [markdown] }
 */
export function getQuestionMedia(question) {
  const images = [];
  const tables = [];
  if (!question) return { images, tables };

  const mainUrl = question.image_url || question.imageUrl;
  if (mainUrl) {
    images.push({ url: resolveMediaUrl(mainUrl), alt: question.image_metadata?.original_name || 'Hình ảnh câu hỏi' });
  }

  const segments = Array.isArray(question.segments) ? question.segments : [];
  for (const seg of segments) {
    if (!seg || typeof seg !== 'object') continue;
    if (seg.type === 'image' && seg.content) {
      images.push({ url: resolveMediaUrl(seg.content), alt: 'Hình ảnh câu hỏi' });
    } else if (seg.type === 'table' && seg.content) {
      tables.push(String(seg.content));
    }
  }
  return { images, tables };
}

function Lightbox({ src, alt, onClose }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  return createPortal(
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 99999,
        background: 'rgba(15, 23, 42, 0.82)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '32px', cursor: 'zoom-out',
      }}
    >
      <button
        onClick={onClose}
        aria-label="Đóng"
        style={{
          position: 'absolute', top: 16, right: 16,
          background: 'rgba(255,255,255,0.15)', color: '#fff',
          border: 'none', borderRadius: 8, padding: '8px 10px', cursor: 'pointer',
        }}
      >
        <X size={20} />
      </button>
      <img
        src={src}
        alt={alt}
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: 'min(1100px, 92vw)', maxHeight: '88vh',
          borderRadius: 10, boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          cursor: 'default', background: '#fff',
        }}
      />
    </div>,
    document.body
  );
}

/**
 * Renders the media blocks of a question (figure images + tables).
 * `question` may use either snake_case (API) or camelCase (local state) fields.
 */
export default function QuestionMedia({ question, compact = false }) {
  const [lightboxSrc, setLightboxSrc] = useState(null);
  const { images, tables } = getQuestionMedia(question);

  if (images.length === 0 && tables.length === 0) return null;

  return (
    <div className="question-media" style={{ marginTop: compact ? 6 : 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
      {images.map((img, i) => (
        <button
          key={`${img.url}-${i}`}
          type="button"
          onClick={() => setLightboxSrc(img.url)}
          title="Nhấn để xem ảnh lớn ngay tại trang này"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, alignSelf: 'flex-start',
            border: '1px solid #E2E8F0', borderRadius: 8, padding: 0, background: '#fff',
            cursor: 'zoom-in', overflow: 'hidden', maxWidth: '100%',
          }}
        >
          <img
            src={img.url}
            alt={img.alt}
            style={{ maxWidth: compact ? 220 : 320, maxHeight: compact ? 160 : 220, display: 'block', objectFit: 'contain' }}
            loading="lazy"
          />
          <span style={{ padding: '4px 8px', fontSize: 12, color: '#4F46E5', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <ZoomIn size={13} /> Xem lớn
          </span>
        </button>
      ))}
      {tables.map((md, i) => (
        <MarkdownTable key={`tbl-${i}`} markdown={md} />
      ))}
      {lightboxSrc && <Lightbox src={lightboxSrc} alt="Hình ảnh câu hỏi" onClose={() => setLightboxSrc(null)} />}
    </div>
  );
}
