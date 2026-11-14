/*
File Name: MathTextEditor.jsx
Description: TipTap rich-text editor with inline MathLive formula nodes. Reads and writes the stored string format ($...$, $$...$$, ![alt](url), newline).
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent
*/
import React, { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import Document from '@tiptap/extension-document';
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import Image from '@tiptap/extension-image';
import { UndoRedo, Placeholder } from '@tiptap/extensions';
import { Extension } from '@tiptap/core';
import MathFieldNode from './MathFieldNode';
import { parseToDoc, serializeDoc } from './mathDocSerializer';
import { buildTableTemplate } from './tableMarkdown';
import { resolveMediaUrl } from './MathRenderer';
import './MathTextEditor.css';

// Keep the raw relative src in the attribute; resolve only for display.
const InlineImage = Image.extend({
  addAttributes() {
    const parent = this.parent?.() || {};
    return {
      ...parent,
      src: {
        default: null,
        renderHTML: (attrs) => ({ src: resolveMediaUrl(attrs.src) }),
      },
    };
  },
});

const SingleLineKeys = Extension.create({
  name: 'singleLineKeys',
  addKeyboardShortcuts() {
    return { Enter: () => true };
  },
});

const MathTextEditor = forwardRef(function MathTextEditor(
  { value, onChange, onFocus, placeholder, singleLine = false, className = '', ariaLabel },
  ref
) {
  const lastEmitted = useRef(value ?? '');
  const cb = useRef({});
  cb.current = { onChange, onFocus };

  const editor = useEditor({
    extensions: [
      singleLine ? Document.extend({ content: 'paragraph' }) : Document,
      Paragraph,
      Text,
      UndoRedo,
      Placeholder.configure({ placeholder: placeholder || '' }),
      InlineImage.configure({ inline: true, allowBase64: false }),
      MathFieldNode,
      ...(singleLine ? [SingleLineKeys] : []),
    ],
    content: parseToDoc(value, { singleLine }),
    immediatelyRender: true,
    shouldRerenderOnTransaction: false,
    editorProps: {
      attributes: { class: 'math-text-editor-content', 'aria-label': ariaLabel || '', spellcheck: 'false' },
      handlePaste: (view, event) => {
        const text = event.clipboardData?.getData('text/plain') || '';
        if (!text.includes('$') && !text.includes('![')) return false;
        const doc = parseToDoc(text, { singleLine });
        const inline = doc.content.flatMap((p, i) =>
          i < doc.content.length - 1 ? [...(p.content || []), { type: 'text', text: '\n' }] : p.content || []
        );
        // Multi-line paste keeps paragraph structure via insertContent of paragraphs.
        const content = singleLine ? inline : doc.content;
        editorRef.current?.commands.insertContent(content);
        return true;
      },
      clipboardTextSerializer: (slice) =>
        serializeDoc({ type: 'doc', content: slice.content.toJSON() || [] }),
    },
    onUpdate: ({ editor: ed }) => {
      const s = serializeDoc(ed.getJSON());
      lastEmitted.current = s;
      cb.current.onChange?.(s);
    },
    onFocus: () => cb.current.onFocus?.(),
  });

  const editorRef = useRef(null);
  editorRef.current = editor;

  // Sync external value changes (e.g. question switching).
  useEffect(() => {
    // Never reset content while the user is typing here: it would jump the caret to the start
    if (editor && !editor.isFocused && (value ?? '') !== lastEmitted.current) {
      lastEmitted.current = value ?? '';
      editor.commands.setContent(parseToDoc(value, { singleLine }), { emitUpdate: false });
    }
  }, [value, editor, singleLine]);

  useImperativeHandle(
    ref,
    () => ({
      focus: () => editorRef.current?.commands.focus(),
      insertImage: (alt, src) => editorRef.current?.chain().focus().setImage({ src, alt }).run(),
      insertTable: (rows, cols) => {
        const ed = editorRef.current;
        if (!ed || singleLine) return;
        // One paragraph per markdown row; start on a fresh line when the cursor sits in text
        const { $from } = ed.state.selection;
        const chain = ed.chain().focus();
        if ($from.parent.content.size > 0) chain.splitBlock();
        chain.insertContent(buildTableTemplate(rows, cols).map((line) => ({
          type: 'paragraph', content: [{ type: 'text', text: line }],
        }))).run();
      },
      insertMath: (template, { display = false } = {}) => {
        const ed = editorRef.current;
        if (!ed) return;
        const opts = { selectionMode: 'placeholder', format: 'latex', focus: true };
        const active = ed.view.dom.querySelector('math-field:focus-within');
        if (active) {
          active.insert(template, opts);
          return;
        }
        if (display && !singleLine) {
          const { $from } = ed.state.selection;
          if ($from.parent.content.size > 0) ed.chain().focus().splitBlock().run();
        }
        ed.chain().focus().insertMathField({ latex: '', display }).run();
        // Wait for the node view to mount and the field to take focus.
        const tryInsert = (n = 0) => {
          const mf = ed.view.dom.querySelector('math-field:focus-within') || ed.view.dom.querySelector('math-field:focus');
          if (mf && typeof mf.insert === 'function') mf.insert(template, opts);
          else if (n < 10) setTimeout(() => tryInsert(n + 1), 30);
        };
        setTimeout(() => tryInsert(), 30);
      },
    }),
    [singleLine]
  );

  return (
    <EditorContent
      editor={editor}
      className={`math-text-editor ${singleLine ? 'is-single-line' : ''} ${className}`}
    />
  );
});

export default MathTextEditor;
