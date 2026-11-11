/*
File Name: AiSourcesList.jsx
Description: Collapsible "reference sources" list for AI-generated exercises (SGK pages and teacher documents).
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent
*/
import React from 'react';

const API_BASE = (import.meta.env && import.meta.env.VITE_API_BASE_URL) || '';

const badgeStyle = (isSgk) => ({
  fontSize: 11,
  fontWeight: 600,
  padding: '1px 8px',
  borderRadius: 10,
  color: '#fff',
  background: isSgk ? '#2563eb' : '#059669',
  whiteSpace: 'nowrap',
});

/**
 * Render a collapsible list of reference sources.
 * @param {{sources: Array<{source: string, label: string, page?: number, image_url?: string, document_id?: string}>}} props
 */
export default function AiSourcesList({ sources }) {
  if (!Array.isArray(sources) || sources.length === 0) return null;

  return (
    <details style={{ textAlign: 'left', margin: '12px 0', fontSize: 13 }}>
      <summary style={{ cursor: 'pointer', fontWeight: 600 }}>
        Nguồn tham khảo ({sources.length})
      </summary>
      <ul style={{ listStyle: 'none', padding: 0, margin: '8px 0 0', display: 'grid', gap: 8 }}>
        {sources.map((s, i) => {
          const isSgk = s.source === 'sgk';
          return (
            <li key={`${s.document_id || 'src'}-${i}`} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={badgeStyle(isSgk)}>{isSgk ? 'SGK' : 'Tài liệu GV'}</span>
              <span>
                {s.label}
                {s.page ? ` - trang ${s.page}` : ''}
              </span>
              {s.image_url && (
                <a href={`${API_BASE}${s.image_url}`} target="_blank" rel="noreferrer">
                  <img
                    src={`${API_BASE}${s.image_url}`}
                    alt={s.label || 'Hình minh họa'}
                    loading="lazy"
                    style={{ height: 40, borderRadius: 4, border: '1px solid #ddd' }}
                  />
                </a>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
}
