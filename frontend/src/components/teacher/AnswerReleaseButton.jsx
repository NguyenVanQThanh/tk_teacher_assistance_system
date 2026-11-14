// File Name: AnswerReleaseButton.jsx
// Description: Teacher toggle to reveal/hide exam answers for all students of an assignment.
// Created At: 2026-11-13
// Created By: AI Agent
// Updated At: 2026-11-13
// Updated By: AI Agent

import React, { useState, useEffect } from 'react';
import { Flag } from 'lucide-react';
import { assignmentsApi, exercisesApi } from '../../services/api';
import confirmDialog from '../common/confirmDialog';
import toast from '../common/toast';

// Pass assignmentId (one class) or exerciseId (every class the exercise was assigned to).
export default function AnswerReleaseButton({ assignmentId, exerciseId, released, onChanged, compact = false }) {
  const [value, setValue] = useState(Boolean(released));
  const [busy, setBusy] = useState(false);

  useEffect(() => setValue(Boolean(released)), [released]);

  const toggle = async (e) => {
    e.stopPropagation();
    if (busy || !(assignmentId || exerciseId)) return;
    const next = !value;
    if (next && !(await confirmDialog('Công bố đáp án cho toàn bộ học sinh của bài thi này?', { title: 'Công bố đáp án', confirmText: 'Công bố' }))) return;
    setBusy(true);
    try {
      if (exerciseId) await exercisesApi.setAnswerRelease(exerciseId, next);
      else await assignmentsApi.setAnswerRelease(assignmentId, next);
      setValue(next);
      toast.success(next ? 'Đã công bố đáp án cho học sinh.' : 'Đã ẩn đáp án với học sinh.');
      if (onChanged) onChanged(assignmentId || exerciseId, next);
    } catch (err) {
      toast.error('Không thể cập nhật trạng thái công bố đáp án.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <button
      type="button"
      className="btn-grade-outline"
      onClick={toggle}
      disabled={busy}
      title={value ? 'Đáp án đang hiển thị với học sinh. Bấm để ẩn.' : 'Đáp án đang ẩn. Bấm để công bố cho học sinh.'}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4, cursor: 'pointer',
        border: '1px solid #16A34A',
        // Released = solid green, hidden = light green outline.
        background: value ? '#16A34A' : '#F0FDF4',
        color: value ? '#FFFFFF' : '#15803D',
      }}
    >
      <Flag size={13} />
      {!compact && <span>{value ? 'Đã công bố' : 'Công bố đáp án'}</span>}
    </button>
  );
}
