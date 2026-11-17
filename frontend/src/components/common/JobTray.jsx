// File Name: JobTray.jsx
// Description: Floating tray showing the signed-in user's running background jobs with stage, progress and ETA.
// Created At: 2026-11-17
// Created By: AI Agent
// Updated At: 2026-11-17
// Updated By: AI Agent

import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

const STAGES = {
  STARTING: 'Đang khởi động',
  RETRIEVING_CONTEXT: 'Đang tìm tài liệu liên quan',
  GENERATING: 'AI đang tạo câu hỏi',
  SAVING: 'Đang lưu kết quả',
};
const KINDS = {
  STUDENT_AI_EXERCISE: 'Tạo bài tập AI',
  TEACHER_AI_EXERCISE: 'Tạo đề AI',
  QUESTION_IMPORT: 'Nhập câu hỏi từ tệp',
};

const fmt = (s) => (s >= 60 ? `${Math.ceil(s / 60)} phút` : `${s} giây`);

export default function JobTray() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    if (!user) return undefined;
    let alive = true;
    const tick = async () => {
      try {
        const { data } = await api.get('/api/v1/jobs', { params: { active: true } });
        if (alive) setJobs(Array.isArray(data) ? data : data.items || []);
      } catch {
        /* best effort: the tray is informational */
      }
    };
    tick();
    const id = setInterval(tick, 4000);
    return () => { alive = false; clearInterval(id); };
  }, [user]);

  if (!jobs.length) return null;
  return (
    <div style={{ position: 'fixed', right: 16, bottom: 16, zIndex: 9999, width: 300, display: 'grid', gap: 8 }}>
      {jobs.map((j) => (
        <div key={j.job_id} style={{ background: '#fff', border: '1px solid #E5E0F0', borderRadius: 12,
          padding: 12, boxShadow: '0 4px 16px rgba(77,48,141,.15)', fontSize: 13, color: '#2D2342' }}>
          <div style={{ fontWeight: 600 }}>{KINDS[j.kind] || 'Tác vụ nền'}</div>
          <div style={{ margin: '2px 0 8px', color: '#6B6480' }}>
            {j.status === 'queued' ? `Đang chờ (vị trí ${j.queue_position})` : STAGES[j.stage] || 'Đang xử lý'}
            {j.eta_seconds != null ? ` · còn khoảng ${fmt(j.eta_seconds)}` : ''}
          </div>
          <div style={{ height: 6, background: '#EFEAF8', borderRadius: 3 }}>
            <div style={{ width: `${j.progress || 0}%`, height: '100%', background: '#4D308D',
              borderRadius: 3, transition: 'width .4s' }} />
          </div>
          <div style={{ marginTop: 6, fontSize: 12, color: '#6B6480' }}>Bạn có thể rời trang, hệ thống sẽ thông báo khi xong.</div>
        </div>
      ))}
    </div>
  );
}
