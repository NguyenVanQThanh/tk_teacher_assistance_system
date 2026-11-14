/*
File Name: MathFieldNode.jsx
Description: TipTap inline atom node hosting a MathLive <math-field> for in-place WYSIWYG formula editing.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent
*/
import React, { useEffect, useRef } from 'react';
import { Node, InputRule } from '@tiptap/core';
import { NodeViewWrapper, ReactNodeViewRenderer } from '@tiptap/react';
import { NodeSelection, TextSelection } from '@tiptap/pm/state';
import { MathfieldElement } from 'mathlive';
import 'mathlive/fonts.css';

// One-time global init: no keypress sounds.
MathfieldElement.soundsDirectory = null;

/** Focus the math-field rendered for the node at `pos`. */
function focusFieldAt(editor, pos, atEnd = false) {
  requestAnimationFrame(() => {
    const dom = editor.view.nodeDOM(pos);
    const mf = dom?.querySelector?.('math-field');
    if (!mf) return;
    mf.focus();
    try {
      mf.position = atEnd ? mf.lastOffset : 0;
    } catch (e) {
      /* position not settable before the field is ready */
    }
  });
}

function MathFieldView({ node, updateAttributes, editor, getPos, deleteNode, selected }) {
  const mfRef = useRef(null);
  const { latex, display } = node.attrs;
  // Latest props for stable event handlers.
  const live = useRef({});
  live.current = { node, editor, getPos, deleteNode, updateAttributes };

  const exit = (side) => {
    const { node: n, editor: ed, getPos: gp, deleteNode: del } = live.current;
    const pos = gp();
    if (typeof pos !== 'number') return;
    const empty = !stripEmpty(mfRef.current?.value);
    if (empty) {
      del();
      ed.chain().focus().setTextSelection(Math.min(pos, ed.state.doc.content.size)).run();
      return;
    }
    const target = side === 'after' ? pos + n.nodeSize : pos;
    ed.chain().focus().setTextSelection(target).run();
  };

  useEffect(() => {
    const mf = mfRef.current;
    if (!mf) return undefined;
    mf.defaultMode = display ? 'math' : 'inline-math';
    mf.smartFence = true;
    mf.mathVirtualKeyboardPolicy = 'auto';
    mf.menuItems = [];
    mf.value = latex;

    const onInput = () => live.current.updateAttributes({ latex: mf.value });
    const onMoveOut = (e) => {
      e.preventDefault();
      const dir = e.detail?.direction;
      exit(dir === 'forward' || dir === 'downward' ? 'after' : 'before');
    };
    const onKeyDown = (e) => {
      if (e.key === 'Escape' || e.key === 'Enter') {
        e.preventDefault();
        e.stopPropagation();
        exit('after');
      } else if (e.key === ' ' && mf.position === mf.lastOffset && mf.selectionIsCollapsed !== false) {
        e.preventDefault();
        e.stopPropagation();
        exit('after');
        live.current.editor.commands.insertContent(' ');
      } else if (e.key === 'Backspace' && !mf.value) {
        e.preventDefault();
        e.stopPropagation();
        exit('before');
      }
    };
    mf.addEventListener('input', onInput);
    mf.addEventListener('move-out', onMoveOut);
    mf.addEventListener('keydown', onKeyDown, true);
    return () => {
      mf.removeEventListener('input', onInput);
      mf.removeEventListener('move-out', onMoveOut);
      mf.removeEventListener('keydown', onKeyDown, true);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync external changes without resetting the caret while typing.
  useEffect(() => {
    const mf = mfRef.current;
    if (mf && mf.value !== latex && document.activeElement !== mf) mf.value = latex;
  }, [latex]);

  useEffect(() => {
    if (selected) mfRef.current?.focus();
  }, [selected]);

  return (
    <NodeViewWrapper as="span" className={display ? 'mf-node mf-display' : 'mf-node'}>
      <math-field ref={mfRef} />
    </NodeViewWrapper>
  );
}

const stripEmpty = (v) => String(v ?? '').replace(/\\placeholder(?:\[[^\]]*\])?\{[^{}]*\}/g, '').trim();

export const MathFieldNode = Node.create({
  name: 'mathField',
  group: 'inline',
  inline: true,
  atom: true,
  selectable: true,
  draggable: false,

  addAttributes() {
    return {
      latex: { default: '' },
      display: { default: false },
    };
  },

  parseHTML() {
    return [{ tag: 'span[data-math]' }];
  },

  renderHTML({ node }) {
    return ['span', { 'data-math': '', 'data-latex': node.attrs.latex, 'data-display': String(node.attrs.display) }];
  },

  addNodeView() {
    return ReactNodeViewRenderer(MathFieldView, {
      stopEvent: () => true,
      ignoreMutation: () => true,
    });
  },

  addCommands() {
    return {
      insertMathField:
        ({ latex = '', display = false } = {}) =>
        ({ state, tr, dispatch, editor }) => {
          const type = state.schema.nodes.mathField;
          const from = state.selection.from;
          if (dispatch) {
            tr.replaceSelectionWith(type.create({ latex, display }), false);
            dispatch(tr.scrollIntoView());
            focusFieldAt(editor, from);
          }
          return true;
        },
    };
  },

  addKeyboardShortcuts() {
    const enter = (dir) => () => {
      const { state } = this.editor;
      const sel = state.selection;
      if (!sel.empty) return false;
      const node = dir > 0 ? sel.$from.nodeAfter : sel.$from.nodeBefore;
      if (node?.type.name !== 'mathField') return false;
      const pos = dir > 0 ? sel.from : sel.from - node.nodeSize;
      focusFieldAt(this.editor, pos, dir < 0);
      return true;
    };
    return {
      'Alt-=': () => this.editor.commands.insertMathField({ latex: '', display: false }),
      ArrowRight: enter(1),
      ArrowLeft: enter(-1),
    };
  },

  addInputRules() {
    // Typing "$" (not after "$" or a digit) opens a new empty formula.
    return [
      new InputRule({
        find: /(?:^|[^$\d])\$$/,
        handler: ({ state, range, chain }) => {
          const from = range.to - 1;
          const type = state.schema.nodes.mathField;
          chain()
            .command(({ tr }) => {
              tr.replaceWith(from, range.to, type.create({ latex: '', display: false }));
              tr.setSelection(TextSelection.near(tr.doc.resolve(from)));
              return true;
            })
            .run();
          focusFieldAt(this.editor, from);
        },
      }),
    ];
  },
});

export { NodeSelection };
export default MathFieldNode;
