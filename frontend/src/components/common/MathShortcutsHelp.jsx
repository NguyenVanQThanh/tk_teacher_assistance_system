/*
File Name: MathShortcutsHelp.jsx
Description: Popover listing math editor shortcuts (MathLive inline shortcuts read at runtime, structural keys, editor keys).
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent
*/
import React, { useEffect, useMemo } from 'react';
import { MathfieldElement } from 'mathlive';
import MathRenderer from './MathRenderer';
import './MathTextEditor.css';

const CURATED = [
  'sqrt', 'cbrt', 'frac', 'pi', 'alpha', 'beta', 'theta', 'delta', 'lambda', 'omega', 'infty',
  '>=', '<=', '!=', '+-', 'xx', '->', '=>', '<=>', 'in', '!in', 'sum', 'int', 'lim', 'log', 'ln',
  'sin', 'cos', 'tan', 'RR', 'NN', 'ZZ', 'QQ', '...',
];

const STRUCTURAL = [
  ['^', 'Số mũ (a^2)'],
  ['_', 'Chỉ số dưới'],
  ['/', 'Phân số'],
  ['Alt+V', 'Căn bậc hai'],
  ['Alt+Shift+V', 'Căn bậc n'],
  ['Tab / Shift+Tab', 'Ô trống kế tiếp / trước đó'],
  ['Ctrl+Z', 'Hoàn tác'],
];

const EDITOR_KEYS = [
  ['$ hoặc Alt+=', 'Chèn công thức mới'],
  ['Mũi tên phải / Space ở cuối công thức / Esc / Enter', 'Thoát khỏi công thức'],
  ['Mũi tên trái / phải trong văn bản', 'Đi vào công thức liền kề'],
  ['Backspace trong công thức rỗng', 'Xóa công thức'],
];

export default function MathShortcutsHelp({ open, onClose, anchorRef }) {
  const shortcuts = useMemo(() => {
    if (!open) return [];
    try {
      const defs = new MathfieldElement().inlineShortcuts || {};
      return CURATED.filter((k) => k in defs).map((k) => {
        const v = defs[k];
        const latex = (typeof v === 'string' ? v : v?.value || '').replace(/#\?/g, '\\square');
        return [k, latex];
      });
    } catch (e) {
      return [];
    }
  }, [open]);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose();
    const onDown = (e) => {
      if (anchorRef?.current?.contains(e.target)) return;
      if (!e.target.closest?.('.math-shortcuts-popover')) onClose();
    };
    document.addEventListener('keydown', onKey);
    document.addEventListener('mousedown', onDown);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('mousedown', onDown);
    };
  }, [open, onClose, anchorRef]);

  if (!open) return null;
  return (
    <div className="math-shortcuts-popover" role="dialog" aria-label="Hướng dẫn gõ công thức">
      <button type="button" className="math-shortcuts-close" onClick={onClose} aria-label="Đóng">×</button>
      <h4>Gõ tắt (gõ xong tự chuyển thành công thức)</h4>
      <table>
        <tbody>
          {shortcuts.map(([k, latex]) => (
            <tr key={k}>
              <td><kbd>{k}</kbd></td>
              <td><MathRenderer text={`$${latex}$`} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      <h4>Phím cấu trúc</h4>
      <table>
        <tbody>
          {STRUCTURAL.map(([k, d]) => (
            <tr key={k}><td><kbd>{k}</kbd></td><td>{d}</td></tr>
          ))}
        </tbody>
      </table>
      <h4>Phím soạn thảo</h4>
      <table>
        <tbody>
          {EDITOR_KEYS.map(([k, d]) => (
            <tr key={k}><td><kbd>{k}</kbd></td><td>{d}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
