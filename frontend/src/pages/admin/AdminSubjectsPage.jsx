// File Name: AdminSubjectsPage.jsx
// Description: Admin page to assign the head of each subject department (head sees department-wide resources).
// Created At: 2026-11-13
// Created By: AI Agent
// Updated At: 2026-11-13
// Updated By: AI Agent

import React, { useCallback, useEffect, useState } from 'react';
import { subjectsApi } from '../../services/api';

const errorText = (err) =>
  err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Không thể cập nhật tổ trưởng bộ môn.';

export default function AdminSubjectsPage() {
  const [subjects, setSubjects] = useState([]);
  const [candidates, setCandidates] = useState({});
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState(null);
  const [message, setMessage] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await subjectsApi.getSubjects();
      setSubjects(list);
      const entries = await Promise.all(
        list.map(async (s) => [s.subject_id, await subjectsApi.getHeadCandidates(s.subject_id).catch(() => [])])
      );
      setCandidates(Object.fromEntries(entries));
    } catch (err) {
      setMessage({ type: 'error', text: errorText(err) });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onChange = async (subject, teacherId) => {
    setSavingId(subject.subject_id);
    setMessage(null);
    try {
      const updated = await subjectsApi.assignHeadTeacher(subject.subject_id, teacherId || null);
      setSubjects((prev) => prev.map((s) => (s.subject_id === updated.subject_id ? updated : s)));
      setMessage({ type: 'success', text: `Đã cập nhật tổ trưởng môn ${subject.subject_name}.` });
    } catch (err) {
      setMessage({ type: 'error', text: errorText(err) });
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="admin-subjects-page" data-testid="admin-subjects-page" style={{ padding: 24 }}>
      <h2>Môn học &amp; Tổ trưởng bộ môn</h2>
      <p>Tổ trưởng chỉ có thể là giáo viên đang dạy môn đó. Giáo viên trong tổ xem được tài liệu và bài tập của tổ trưởng.</p>
      {message && (
        <div role="status" style={{ color: message.type === 'error' ? '#b91c1c' : '#047857', margin: '8px 0' }}>
          {message.text}
        </div>
      )}
      {loading ? (
        <p>Đang tải...</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Môn học</th>
              <th style={{ textAlign: 'left' }}>Tổ trưởng bộ môn</th>
            </tr>
          </thead>
          <tbody>
            {subjects.map((s) => (
              <tr key={s.subject_id} data-testid="subject-row">
                <td>{s.subject_name}</td>
                <td>
                  <select
                    aria-label={`Tổ trưởng môn ${s.subject_name}`}
                    value={s.head_teacher_id || ''}
                    disabled={savingId === s.subject_id}
                    onChange={(e) => onChange(s, e.target.value)}
                  >
                    <option value="">Chưa chỉ định</option>
                    {(candidates[s.subject_id] || []).map((t) => (
                      <option key={t.user_id} value={t.user_id}>
                        {t.full_name} {t.phone ? `(${t.phone})` : ''}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
