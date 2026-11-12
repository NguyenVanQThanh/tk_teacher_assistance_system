// File Name: AssignExercisesDialog.jsx
// Description: Popup listing exercises of a class grade with checkboxes; assigns the selected ones to the class without leaving the page.
// Created At: 2026-11-12
// Created By: AI Agent
// Updated At: 2026-11-12
// Updated By: AI Agent

import React, { useEffect, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { exercisesApi, assignmentsApi } from '../../services/api';

const S = {
  overlay: { position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16, background: 'rgba(51,43,79,0.45)', fontFamily: 'Be Vietnam Pro, sans-serif' },
  box: { width: 'min(560px,100%)', maxHeight: '85vh', display: 'flex', flexDirection: 'column', background: '#fff', borderRadius: 14, padding: 24, border: '1px solid #DCD6E8' },
  head: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  list: { overflowY: 'auto', flex: 1, border: '1px solid #DCD6E8', borderRadius: 10 },
  item: { display: 'flex', gap: 10, alignItems: 'center', padding: '10px 12px', borderBottom: '1px solid #EEE9F6', cursor: 'pointer', fontSize: 14, color: '#332B4F' },
  row: { display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 },
  cancel: { padding: '9px 18px', borderRadius: 10, border: '1px solid #DCD6E8', background: '#fff', color: '#4D308D', fontWeight: 600, cursor: 'pointer' },
  ok: { padding: '9px 18px', borderRadius: 10, border: 'none', background: '#4D308D', color: '#fff', fontWeight: 600, cursor: 'pointer' },
};

// Same grade resolution as the exercise repository page
const gradeOf = (ex) => String(ex.ai_metadata?.grade ?? (ex.title.match(/\b(10|11|12)\b/)?.[1] || '12')).replace(/\D/g, '');

export default function AssignExercisesDialog({ isOpen, onClose, classId, grade, onAssigned }) {
  const [items, setItems] = useState([]);
  const [picked, setPicked] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen) return;
    setPicked([]);
    setError('');
    setLoading(true);
    exercisesApi.getExercises({ page_size: 100 })
      .then((res) => {
        const all = Array.isArray(res) ? res : res?.items || [];
        setItems(all.filter((ex) => !grade || gradeOf(ex) === String(grade)));
      })
      .catch((e) => setError(e.response?.data?.detail?.message || 'Could not load exercises.'))
      .finally(() => setLoading(false));
  }, [isOpen, grade]);

  if (!isOpen) return null;

  const toggle = (id) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));

  const submit = async () => {
    setSaving(true);
    setError('');
    const due = new Date();
    due.setDate(due.getDate() + 7);
    due.setHours(23, 59, 0, 0);
    const results = await Promise.allSettled(picked.map((exercise_id) =>
      assignmentsApi.createAssignment(classId, { exercise_id, due_at: due.toISOString(), duration_minutes: 45, max_attempts: 1 })));
    setSaving(false);
    const failed = results.filter((r) => r.status === 'rejected');
    if (failed.length) {
      const d = failed[0].reason?.response?.data?.detail;
      setError(`${failed.length} assignment(s) failed: ${typeof d === 'string' ? d : d?.message || 'unknown error'}`);
    }
    if (failed.length < picked.length) onAssigned?.();
    if (!failed.length) onClose();
  };

  return (
    <div style={S.overlay} onClick={onClose} role="presentation">
      <div style={S.box} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div style={S.head}>
          <h3 style={{ margin: 0, color: '#332B4F' }}>Assign exercises (Grade {grade})</h3>
          <button type="button" aria-label="Close" onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer' }}><X size={18} /></button>
        </div>
        <div style={S.list}>
          {loading && <div style={{ padding: 16 }}><Loader2 size={16} /> Loading...</div>}
          {!loading && !items.length && <div style={{ padding: 16, color: '#6E6784' }}>No exercises for this grade.</div>}
          {items.map((ex) => (
            <label key={ex.exercise_id} style={S.item}>
              <input type="checkbox" checked={picked.includes(ex.exercise_id)} onChange={() => toggle(ex.exercise_id)} />
              <span>{ex.title}</span>
            </label>
          ))}
        </div>
        {error && <p role="alert" style={{ color: '#B91C1C', fontSize: 13 }}>{error}</p>}
        <div style={S.row}>
          <button type="button" style={S.cancel} onClick={onClose}>Cancel</button>
          <button type="button" style={{ ...S.ok, opacity: picked.length && !saving ? 1 : 0.5 }} disabled={!picked.length || saving} onClick={submit}>
            {saving ? 'Assigning...' : `Assign (${picked.length})`}
          </button>
        </div>
      </div>
    </div>
  );
}
