# Implementation Plan: Inline WYSIWYG Math Editor for EditExerciseModal

```text
File Name: plan.md
Description: Spec-kit style plan to replace the textarea/backdrop LaTeX editor in EditExerciseModal with a TipTap rich-text editor that hosts MathLive inline formula nodes, keeping the stored $...$ / $$...$$ + Markdown string format unchanged.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent
```

---

## 0. Current State (verified in repo)

| Item | Finding |
|---|---|
| Editor | `frontend/src/components/common/MathLiveEditor.jsx` is NOT MathLive. It is a transparent `<textarea>` over a KaTeX-rendered backdrop. Caret is positioned on raw LaTeX characters while the user sees rendered math, so the caret "jumps" and cannot be placed inside/after a formula. This is the root cause of user problems (1) and (3). |
| Answer options | Plain `<input type="text" className="option-choice-input">` (EditExerciseModal.jsx ~L1507). Raw LaTeX shows in the input, rendered only in the preview. Root cause of problem (2). |
| Explanation | Plain `<textarea className="solution-guide-textarea">` (~L1532). |
| Toolbar | `symbolCategoriesBySubject` (~L509-712), `insertSnippet()` (~L751) does string splicing at `selectionStart`, then `setTimeout(...setSelectionRange)` after re-render. PT bac 2/3/4 buttons insert `$$...$$` as a block (~L1289-1317). Image button inserts `![alt](url)` raw via `insertSnippet(..., { raw: true })` (~L796). |
| Active field tracking | `activeFieldRef` = `'content' | 'guide' | 'option:<KEY>'`, `getActiveField()` (~L725). |
| Renderer | `frontend/src/components/common/MathRenderer.jsx` (KaTeX 0.18.5): `MathRenderer`, `MathContent`, `MathInline`, `resolveMediaUrl`. Used read-only across student/teacher pages. Keep unchanged. |
| Stored format | `buildQuestionPayload()` (~L39-108) sends `content`, `content_latex`, `content_markdown` (all the same string), `explanation`, `answer_options[].content`. Backend parses `$$...$$` and `$...$` (`import_parser_service.py` L1745 `r'(\$\$[\s\S]*?\$\$|\$[^\$]+?\$)'`, `pdf_export_service.py` L138/L234/L383). Images are Markdown `![alt](url)`. Lines are separated by `\n`; blank line = block separator (`MathContent`). |
| Deps | React 18.3.1, Vite 5, katex ^0.18.5, lucide-react. No TipTap, no MathLive installed. No unit-test runner (only Playwright e2e). Node 24 available. |

Contract that MUST hold after the change: **the string in `currentContent`, `currentOptions[i].text`, `currentSolutionGuide` keeps the exact same format** (plain text + `$inline$` + `$$display$$` + `![alt](url)`, `\n` line breaks). Backend, DB, and all read-only renderers stay untouched.

---

## 1. Research Summary

Versions checked against npm registry on 2026-11-11.

| Criterion | **MathLive** `<math-field>` 0.111.x | **TipTap 3** + `@tiptap/extension-mathematics` 3.x | **MathQuill** 0.10.1-a | **CKEditor 5** + math plugin | **Lexical** equation node |
|---|---|---|---|---|---|
| Per-token WYSIWYG formula editing (Word-like) | Yes, best-in-class (structural caret, placeholders, sup/sub/frac navigation) | No. KaTeX render; editing = click node then edit raw LaTeX in your own popup | Yes (structural) | No. Opens raw-LaTeX dialog | No. Raw LaTeX in an input, KaTeX preview |
| Rich text around formulas (Vietnamese text, IME) | Weak alone (text mode inside formula is not IME friendly) | Yes (ProseMirror, solid IME/composition handling) | No (math only) | Yes | Yes |
| Exit formula and keep typing | `move-out` event (arrow/tab at boundary, `detail.direction`), Space = move after parent | n/a | Arrow keys | n/a | n/a |
| Auto-convert shortcuts (a^2, sqrt, frac, pi, >=) | Yes: `^` `_` `/` structural keys; `inlineShortcuts` (`sqrt`, `frac`, `pi`, `>=`, `->`, `in`, `infty`...) readable at runtime via `mf.inlineShortcuts` | Input rules only (`$...$`) | Partial (`\` commands, `/`, `^`) | No | No |
| Template insert with cursor in first slot | `mf.insert(latex, { selectionMode: 'placeholder' })`, `#?` = placeholder, Tab = next placeholder | No | Partial | No | No |
| Virtual keyboard | Built-in (`window.mathVirtualKeyboard`) | No | No | No | No |
| LaTeX round-trip | `mf.value` / `getValue('latex-without-placeholders')`, KaTeX-compatible LaTeX | `node.attrs.latex` | LaTeX output | LaTeX | LaTeX |
| React 18/19 | Web component, framework agnostic | `@tiptap/react` peer `^17 || ^18 || ^19` | jQuery dependency, unmaintained since 2022 | Separate React wrapper | Native React |
| License | MIT | MIT | MPL-2.0 | GPL-2.0+ or commercial | MIT |
| Bundle (min) | ~820 KB JS + ~300 KB fonts (lazy-loadable) | ~150-200 KB for minimal set | ~120 KB + jQuery | Large (>1 MB typical) | ~100 KB + custom work |

Sources: mathlive.io guides (shortcuts, interacting, commands, react, API reference), tiptap.dev Mathematics extension docs, npm registry metadata (`npm view`), MathLive 0.111.1 type definitions (`types/mathfield-element.d.ts`, `types/core-types.d.ts`).

Note: `@aarkn/tiptap-math-extension` returns 404 on npm; not an option.

---

## 2. Decision

**TipTap 3 (rich text shell) + a custom inline TipTap node whose node view hosts a MathLive `<math-field>`.**

Why:
- MathLive is the only maintained MIT library giving Word-style per-token editing, placeholders, Tab between slots, `^`/`_`/`/` structural keys, inline shortcuts, and a virtual keyboard. Solves (1), (3), (4).
- MathLive alone cannot host Vietnamese prose well (text mode + IME). TipTap/ProseMirror handles text/IME; formulas live as atomic inline nodes. Solves mixed text + math.
- `@tiptap/extension-mathematics` is NOT used: it is KaTeX click-to-edit (raw LaTeX), which is exactly the current pain. Keep KaTeX only for the read-only preview and other pages.
- No Markdown extension needed: the only Markdown in use is `![alt](url)` and line breaks. A ~80-line pure serializer does the round-trip, which keeps the format byte-identical.

Pinned versions (published more than 2 weeks before 2026-11-11, all MIT):
- `mathlive@0.111.1` (2026-10-09)
- `@tiptap/core@3.32.0`, `@tiptap/pm@3.32.0`, `@tiptap/react@3.32.0`, `@tiptap/extension-document@3.32.0`, `@tiptap/extension-paragraph@3.32.0`, `@tiptap/extension-text@3.32.0`, `@tiptap/extension-image@3.32.0`, `@tiptap/extensions@3.32.0` (2026-10-13; `@tiptap/extensions` provides `UndoRedo`, `Placeholder`)

---

## 3. Requirements Mapped to User Points

| # | User problem | Requirement | How it is met |
|---|---|---|---|
| R1 | Formulas render only in preview; cannot edit per-character | Formulas render in place inside the editor and are edited structurally | Each `$...$` becomes a `mathField` inline node rendered by `<math-field>`; clicking it places a structural caret inside the formula |
| R2 | Answer options show raw `$\ln(x^2+1) + C$` | Options A-D render formulas while editing | Each option uses the same `MathTextEditor` in `singleLine` mode |
| R3 | PT bac 2/3/4 box: erratic caret, cannot exit | Insert template, caret lands in first slot, user can leave the formula and type text | `mf.insert(template, { selectionMode: 'placeholder' })`; Tab cycles slots; Right arrow at end / Space at top level / Esc / Enter exits to text after the node via `move-out` + key handling |
| R4 | "Huong dan" help listing shortcuts | Help popover lists real shortcuts of the chosen library | `MathShortcutsHelp` reads `mf.inlineShortcuts` from a live `MathfieldElement` (filtered curated keys) + static table of MathLive default keybindings + editor-specific keys |

---

## 4. Architecture

```
EditExerciseModal
 ├─ Toolbar (symbol chips, PT bac 2/3/4, Chen hinh anh, [Huong dan] button -> MathShortcutsHelp)
 │     all buttons: onMouseDown={e => e.preventDefault()}  (keeps focus/caret in the active editor)
 │     click -> activeEditorRef.current.insertMath(template) | insertImage(alt,url)
 ├─ MathTextEditor  (content, multi-line)          ─┐
 ├─ MathTextEditor  x4 (options A-D, singleLine)    ├─ value: string  onChange(string)  onFocus()
 ├─ MathTextEditor  (explanation, multi-line)      ─┘  ref -> { insertMath, insertImage, focus }
 └─ Preview (unchanged, KaTeX MathRenderer)  <- final student-view fidelity check

MathTextEditor (TipTap useEditor)
 ├─ Document (multi) | SingleLineDocument (content: 'paragraph')
 ├─ Paragraph, Text, UndoRedo, Placeholder
 ├─ Image (inline: true)                       -> serialized as ![alt](src)
 └─ MathFieldNode (inline, atom, attrs { latex, display })
       └─ ReactNodeViewRenderer(MathFieldView, { stopEvent: () => true, ignoreMutation: () => true })
             └─ <math-field> (MathLive)

mathDocSerializer.js (pure, no React)
   parseToDoc(string)  -> ProseMirror JSON
   serializeDoc(json)  -> string
```

### 4.1 Serialization contract (`mathDocSerializer.js`)

Parse (string -> JSON):
1. `text = value ?? ''`. Pre-pass: inside each `$$...$$` match, replace `\r?\n` with a space (display math must fit in one paragraph).
2. Split by `\n`. Each line -> one `paragraph` (empty line -> empty paragraph). This 1:1 line mapping makes round-trip exact, including blank-line block separators.
3. Tokenize each line with
   `/(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|!\[[^\]]*\]\([^)\s]+(?:\s+"[^"]*")?\))/g`
   - `$$x$$` or `\[x\]` -> `{ type: 'mathField', attrs: { latex: x.trim(), display: true } }`
   - `$x$` or `\(x\)` -> `{ type: 'mathField', attrs: { latex: x.trim(), display: false } }`
   - `![alt](src)` -> `{ type: 'image', attrs: { src, alt } }`
   - other text -> `{ type: 'text', text }` (skip empty strings; ProseMirror rejects empty text nodes)
4. `singleLine` mode: join all lines with a space before step 2.

Serialize (JSON -> string):
- paragraphs joined with `\n`
- text -> as is; image -> `![${alt}](${src})`
- mathField -> `$$${clean}$$` if display else `$${clean}$`, where `clean = stripPlaceholders(latex)`:
  `latex.replace(/\\placeholder(?:\[[^\]]*\])?\{([^{}]*)\}/g, '$1').trim()`
- a mathField with empty `clean` is dropped (no `$$` garbage saved).
- `\(..\)` and `\[..\]` normalize to `$..$` / `$$..$$` on save (backend already accepts both; acceptable normalization).

Round-trip guarantee: `serializeDoc(parseToDoc(s)) === s` for any `s` that uses only `$`/`$$` delimiters, no `\$` escapes, and no empty/whitespace-padded formulas.

### 4.2 MathFieldNode behavior

- Schema: `name: 'mathField'`, `group: 'inline'`, `inline: true`, `atom: true`, `selectable: true`, `draggable: false`, attrs `latex: ''`, `display: false`.
- `parseHTML: [{ tag: 'span[data-math]' }]`, `renderHTML` -> `['span', { 'data-math': '', 'data-latex': latex, 'data-display': display }]` (needed only for copy/paste inside TipTap).
- Command `insertMathField({ latex, display })`: inserts node at selection, then focuses the new field (see 4.3).
- Keyboard shortcuts on the TipTap side (`addKeyboardShortcuts`):
  - `Alt-=` (Word equation shortcut): insert empty inline math and focus it.
  - `ArrowRight`: if node right after the caret is `mathField`, focus it with `mf.position = 0`; return true.
  - `ArrowLeft`: if node right before the caret is `mathField`, focus it with `mf.position = mf.lastOffset`; return true.
- Input rule: typing `$` when the previous char is not `$` and not a digit -> replace with empty `mathField` and focus it. Typing a full `$...$` is covered automatically because the first `$` already opens the field. (Disable if teachers type currency; see Risks.)
- Paste (`editorProps.handlePaste`): if `text/plain` contains `$` or `![`, `insertContent(parseToDoc(text, { singleLine }).content)` and return true.
- `editorProps.clipboardTextSerializer`: `slice => serializeDoc({ type: 'doc', content: slice.content.toJSON() })` so copy gives `$...$` text.

### 4.3 MathFieldView (React node view)

```jsx
<NodeViewWrapper as="span" className={display ? 'mf-node mf-display' : 'mf-node'}>
  <math-field ref={mfRef} />
</NodeViewWrapper>
```
On mount (`useEffect([], ...)`):
- `mf.defaultMode = display ? 'math' : 'inline-math'`, `mf.smartFence = true`, `mf.mathVirtualKeyboardPolicy = 'auto'` (keyboard only on touch devices), `mf.menuItems = []` (hide context menu), `mf.value = node.attrs.latex`.
- `input` -> `updateAttributes({ latex: mf.value })` (keep `\placeholder{}` while editing; stripped only in serializer).
- `move-out` -> `e.preventDefault()`; `direction === 'forward' | 'downward'` -> `exit('after')`; `'backward' | 'upward'` -> `exit('before')`.
- `keydown` (capture on mf):
  - `Escape` or `Enter` -> `preventDefault`, `stopPropagation`, `exit('after')` (overrides MathLive default Esc = toggle LaTeX mode, which confused users).
  - `Space` when `mf.position === mf.lastOffset` and selection collapsed -> `exit('after')` and insert a space in TipTap. (Inside a sub-expression MathLive's own Space = move after parent still applies.)
  - `Backspace` when `mf.value === ''` -> `deleteNode()` then focus editor at that position.
- `exit(side)`: `const pos = getPos(); const target = side === 'after' ? pos + node.nodeSize : pos; editor.chain().focus().setTextSelection(target).run();` then, if latex is empty, delete the node.
- When the node becomes `NodeSelection` (`selected` prop true) -> `mf.focus()`.
- Sync from outside: `useEffect([node.attrs.latex])` sets `mf.value` only if `mf.value !== node.attrs.latex` and `document.activeElement !== mf` (avoids caret reset while typing).
- Imperative helpers exposed on the DOM element for the toolbar: the editor finds the focused field via `editor.view.dom.querySelector('math-field:focus-within')` or tracks `lastFocusedMf` in editor storage on `focusin`.

One-time global init (in `MathFieldNode.js` module scope):
```js
import { MathfieldElement } from 'mathlive';
import 'mathlive/fonts.css';          // Vite bundles fonts; no public/ copy needed
MathfieldElement.soundsDirectory = null; // no keypress sounds
```

### 4.4 Toolbar insertion

`MathTextEditor` exposes via `forwardRef` + `useImperativeHandle`:
- `insertMath(template, { display })`
  - If a `<math-field>` inside this editor has focus: `mf.insert(template, { selectionMode: 'placeholder', format: 'latex', focus: true })`. Symbols become part of the current formula (Word behavior).
  - Else: `editor.commands.insertMathField({ latex: '', display })`, focus the new field, then `mf.insert(template, { selectionMode: 'placeholder', format: 'latex', focus: true })`. Caret lands in the first `#?` slot.
  - `display: true` (PT bac 2/3/4) inserts on its own paragraph: if the current paragraph is not empty, `splitBlock` before and after.
- `insertImage(alt, src)`: `editor.chain().focus().setImage({ src, alt }).run()`.
- `focus()`.

The modal replaces `textareaRef/guideRef/optionInputRefs/getActiveField/insertSnippet/wrapInlineMath` with one `activeEditorRef` (set in each editor's `onFocus`) and a `editorRefs = useRef({})` map keyed `'content' | 'guide' | 'option:A'...`. `activeFieldRef` string stays (used for focus bookkeeping).

Every toolbar button gets `onMouseDown={(e) => e.preventDefault()}` so clicking never blurs the active editor/formula (fixes the caret losing its place).

Templates (add a `tpl` field to items whose `code` has structural slots; other items insert `code` unchanged):

| Item tip | tpl |
|---|---|
| Phan so a/b | `\frac{#?}{#?}` |
| Luy thua x^n | `#@^{#?}` |
| Chi so duoi x_k | `#@_{#?}` |
| Can bac 2 | `\sqrt{#?}` |
| Can bac n | `\sqrt[#?]{#?}` |
| Gia tri tuyet doi | `\left\lvert #? \right\rvert` |
| Logarit co so a | `\log_{#?}{#?}` |
| Tich phan xac dinh | `\int_{#?}^{#?} #? \,dx` |
| Nguyen ham | `\int #? \,dx` |
| Tong sigma | `\sum_{#?}^{#?}` |
| Gioi han lim | `\lim_{#? \to #?}` |
| Vec-to u / Vec-to AB | `\vec{#?}` / `\overrightarrow{#?}` |
| Goc ABC | `\widehat{#?}` |
| PT bac 2 (display) | `#?x^2+#?x+#?=0` |
| PT bac 3 (display) | `#?x^3+#?x^2+#?x+#?=0` |
| PT bac 4 (display) | `#?x^4+#?x^3+#?x^2+#?x+#?=0` |

`#@` = selection / implicit left argument (MathLive), `#?` = placeholder. Chip render keeps `display` field via `MathRenderer`.

### 4.5 Help / shortcuts popover (`MathShortcutsHelp.jsx`)

- Button "Huong dan" (lucide `HelpCircle`) at the end of `.toolbar-bottom-actions`. Toggles a popover (`role="dialog"`, `aria-label`, closes on Esc and outside click).
- Content, built on open:
  1. **Inline shortcuts (from MathLive at runtime)**: `const defs = new MathfieldElement().inlineShortcuts;` filter to curated keys `['sqrt','cbrt','frac','pi','alpha','beta','theta','delta','lambda','omega','infty','>=','<=','!=','+-','xx','->','=>','<=>','in','!in','sum','int','lim','log','ln','sin','cos','tan','RR','NN','ZZ','QQ','...']`, keep only keys present in `defs` (so the list never lies if MathLive changes). Value is a string or `{ value }`; render `value.replace(/#\?/g, '\\square')` with `MathRenderer` (`$...$`).
  2. **Structural keys (MathLive defaults, static)**: `^` superscript (a^2 -> a squared), `_` subscript, `/` fraction, `Alt+V` square root, `Alt+Shift+V` nth root, `Tab` / `Shift+Tab` next / previous placeholder, `Ctrl+Z` undo.
  3. **Editor keys (ours, static)**: `$` or `Alt+=` new formula, `Right arrow` at end / `Space` at end / `Esc` / `Enter` leave formula, `Left/Right arrow` from text enters a formula, `Backspace` on empty formula deletes it.
- All labels in the popover follow the existing UI language of the modal (Vietnamese UI text is already the product language there); code comments in English.

### 4.6 Preview section fate

Keep it unchanged. Editor rendering is MathLive; students see KaTeX. The preview is the only place a teacher can verify the KaTeX output (e.g. MathLive-only macros). No other change.

### 4.7 Image compatibility

- `@tiptap/extension-image` configured `{ inline: true, allowBase64: false }`, `src` resolved for display via `addAttributes` `renderHTML: src -> resolveMediaUrl(src)` while the attr keeps the raw relative `/uploads/...` path so it serializes unchanged.
- `handleImagePick` keeps its upload + `setQuestions(... imageMeta ...)` logic; only the line `insertSnippet(\`![${alt}](${meta.url})\`, ...)` becomes `activeEditorRef.current?.insertImage(alt, meta.url)`.

---

## 5. File-by-file Tasks (ordered checklist)

Run all commands from `d:\Code\tk_teacher_assistance_system\frontend`.

- [ ] **T1. Install**
  ```bash
  npm install --save-exact mathlive@0.111.1 @tiptap/core@3.32.0 @tiptap/pm@3.32.0 @tiptap/react@3.32.0 @tiptap/extension-document@3.32.0 @tiptap/extension-paragraph@3.32.0 @tiptap/extension-text@3.32.0 @tiptap/extension-image@3.32.0 @tiptap/extensions@3.32.0
  ```
  Verify `npm ls @tiptap/core` shows a single version.

- [ ] **T2. Create `frontend/src/components/common/mathDocSerializer.js`** (pure ES module, no React/JSX imports, so plain Node can run it). File header block per coding rules. Exports `parseToDoc(value, { singleLine = false } = {})`, `serializeDoc(docJson)`, `stripPlaceholders(latex)`. Implement exactly section 4.1.

- [ ] **T3. Create `frontend/src/components/common/mathDocSerializer.selfcheck.mjs`** (runnable check, no framework):
  ```js
  import assert from 'node:assert/strict';
  import { parseToDoc, serializeDoc, stripPlaceholders } from './mathDocSerializer.js';
  const rt = (s, o) => serializeDoc(parseToDoc(s, o));
  for (const s of [
    '', 'Cho hàm số $f(x) = x^2$ và $g(x)$.',
    'Dòng 1\n\n$$ax^2 + bx + c = 0$$\nDòng 3',
    'Ảnh: ![hinh](/uploads/questions/a.png) xong',
    '$\\ln(x^2+1) + C$', 'Không có công thức',
  ]) assert.equal(rt(s), s);
  assert.equal(rt('Câu \\(x\\) và \\[y\\]'), 'Câu $x$ và $$y$$');
  assert.equal(rt('a\nb', { singleLine: true }), 'a b');
  assert.equal(stripPlaceholders('\\placeholder{}x^2+\\placeholder{3}'), 'x^2+3');
  assert.equal(serializeDoc({ type: 'doc', content: [{ type: 'paragraph', content: [
    { type: 'text', text: 'A ' }, { type: 'mathField', attrs: { latex: '\\placeholder{}', display: false } } ] }] }), 'A ');
  console.log('mathDocSerializer selfcheck passed');
  ```
  Run: `node src/components/common/mathDocSerializer.selfcheck.mjs`. Optionally add `"test:unit": "node src/components/common/mathDocSerializer.selfcheck.mjs"` to `package.json` scripts.

- [ ] **T4. Create `frontend/src/components/common/MathFieldNode.jsx`**: global MathLive init (4.3 bottom), TipTap `Node.create` per 4.2, `MathFieldView` per 4.3, `ReactNodeViewRenderer(MathFieldView, { stopEvent: () => true, ignoreMutation: () => true })`. Export `MathFieldNode`.

- [ ] **T5. Create `frontend/src/components/common/MathTextEditor.jsx`**: props `{ value, onChange, onFocus, placeholder, singleLine = false, className, ariaLabel }`, `forwardRef` exposing `{ insertMath, insertImage, focus }` (4.4).
  - Extensions: `singleLine ? Document.extend({ content: 'paragraph' }) : Document`, `Paragraph`, `Text`, `UndoRedo`, `Placeholder.configure({ placeholder })`, `Image.configure({ inline: true })` (with resolveMediaUrl renderHTML), `MathFieldNode`.
  - `useEditor({ extensions, content: parseToDoc(value, { singleLine }), immediatelyRender: true, shouldRerenderOnTransaction: false, editorProps: { attributes: { class: 'math-text-editor-content', 'aria-label': ariaLabel, spellcheck: 'false' }, handlePaste, clipboardTextSerializer } , onUpdate, onFocus })`.
  - `onUpdate`: `const s = serializeDoc(editor.getJSON()); lastEmitted.current = s; onChange(s)`.
  - Sync effect: `useEffect(() => { if (editor && value !== lastEmitted.current) { lastEmitted.current = value; editor.commands.setContent(parseToDoc(value, { singleLine }), { emitUpdate: false }); } }, [value, editor])` (question switching).
  - `singleLine`: `addKeyboardShortcuts` on the doc extension: `Enter: () => true`.
  - Render `<EditorContent editor={editor} className={\`math-text-editor ${singleLine ? 'is-single-line' : ''} ${className}\`} />`.

- [ ] **T6. Create `frontend/src/components/common/MathShortcutsHelp.jsx`** per 4.5. Props `{ open, onClose, anchorRef }`. Uses `MathRenderer` for rendering.

- [ ] **T7. Create `frontend/src/components/common/MathTextEditor.css`** (imported by MathTextEditor.jsx):
  - `.math-text-editor .ProseMirror { outline: none; min-height: ...; padding: 10px 12px; font-family: 'Times New Roman', serif; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }`
  - `.math-text-editor.is-single-line .ProseMirror { min-height: auto; padding: 2px 6px; white-space: nowrap; overflow-x: auto; }`
  - `.mf-node math-field { display: inline-block; border: none; padding: 0 2px; background: transparent; font-size: 1em; vertical-align: middle; }`, `.mf-node math-field:focus-within { outline: 1px solid #7C3AED; border-radius: 3px; background: #F5F3FF; }`
  - `.mf-display { display: block; text-align: center; margin: 6px 0; }`
  - `math-field::part(menu-toggle), math-field::part(virtual-keyboard-toggle) { display: none; }`
  - `.ProseMirror p.is-editor-empty:first-child::before { content: attr(data-placeholder); color: #94A3B8; float: left; height: 0; pointer-events: none; }`
  - `.math-text-editor img { max-height: 120px; vertical-align: middle; }`

- [ ] **T8. Edit `frontend/src/components/documents/EditExerciseModal.jsx`** (update header `Updated At/By`):
  1. Imports: remove `MathLiveEditor`; add `MathTextEditor`, `MathShortcutsHelp`, `HelpCircle` from lucide-react.
  2. Replace `textareaRef`, `guideRef`, `optionInputRefs` with `const editorRefs = useRef({}); const activeEditorRef = useRef(null);` and `const setActive = (key) => { activeFieldRef.current = key; activeEditorRef.current = editorRefs.current[key]; };`. Default `activeEditorRef` to content editor.
  3. Delete `wrapInlineMath`, `getActiveField`, `insertSnippet` (~L716-778). Add:
     ```js
     const insertMath = (tpl, opts = {}) => (activeEditorRef.current || editorRefs.current.content)?.insertMath(tpl, opts);
     ```
  4. Symbol items: add `tpl` per table in 4.4; chip `onClick={() => insertMath(item.tpl || item.code)}`, add `onMouseDown={(e) => e.preventDefault()}`.
  5. PT bac 2/3/4: `onClick={() => insertMath('#?x^2+#?x+#?=0', { display: true })}` etc., plus `onMouseDown` preventDefault. Same `onMouseDown` on the image button.
  6. `handleImagePick`: replace `insertSnippet(...raw)` with `(activeEditorRef.current || editorRefs.current.content)?.insertImage(alt, meta.url);`.
  7. Content editor (~L1468): `<MathTextEditor ref={(r) => { editorRefs.current.content = r; }} className="question-latex-textarea" value={currentContent} onChange={setCurrentContent} onFocus={() => setActive('content')} placeholder="..." ariaLabel="Question content" />`.
  8. Options (~L1507): replace `<input>` with `<MathTextEditor singleLine ref={(r) => { editorRefs.current[\`option:${opt.key}\`] = r; }} className="option-choice-input" value={opt.text} onChange={(v) => handleOptionTextChange(opt.key, v)} onFocus={() => setActive(\`option:${opt.key}\`)} placeholder={...} ariaLabel={\`Answer option ${opt.key}\`} />` wrapped in `<div onClick={(e) => e.stopPropagation()} style={{ flex: 1, minWidth: 0 }}>` so clicking the editor does not toggle the correct answer.
  9. Explanation (~L1532): replace `<textarea>` with `<MathTextEditor ref=... className="solution-guide-textarea" value={currentSolutionGuide} onChange={setCurrentSolutionGuide} onFocus={() => setActive('guide')} ... />`.
  10. Help: `const [isHelpOpen, setIsHelpOpen] = useState(false); const helpBtnRef = useRef(null);` button at end of `.toolbar-bottom-actions`; render `<MathShortcutsHelp open={isHelpOpen} onClose={() => setIsHelpOpen(false)} anchorRef={helpBtnRef} />`.
  11. `.katex-support-hint` text: "Alt+= or $ to insert a formula" style hint (keep product UI language consistent).
  12. Remove the now-unused `MathContent` import if unused after edits (check with grep).

- [ ] **T9. Edit `frontend/src/components/documents/EditExerciseModal.css`**: delete the `LIVE MATH EDITOR` block (`.question-latex-textarea.math-live-editor`, `.math-live-backdrop`, `.math-live-textarea`, `.math-live-placeholder`, ~L1560-1620). Adjust `.question-latex-textarea`, `.option-choice-input`, `.solution-guide-textarea` to style a `div` container (remove `resize`, keep border/focus styles; use `:focus-within` instead of `:focus`).

- [ ] **T10. Delete `frontend/src/components/common/MathLiveEditor.jsx`** (source file, not data; only importer is EditExerciseModal). Confirm with `grep -rn MathLiveEditor frontend/src` = 0 hits.

- [ ] **T11. Lazy-load the modal** in `frontend/src/pages/teacher/ExerciseRepositoryPage.jsx` (MathLive is ~820 KB): `const EditExerciseModal = React.lazy(() => import('../../components/documents/EditExerciseModal'));` and wrap the `<EditExerciseModal .../>` usage (~L432) in `<React.Suspense fallback={null}>`. Update header.

- [ ] **T12. Verify**: `node src/components/common/mathDocSerializer.selfcheck.mjs`, `npm run build` (no errors), then manual QA per section 6.

---

## 6. Acceptance Criteria

1. Opening a question whose content is `Tính $\int x\,dx$ biết $x^2$` shows rendered formulas inline in the editor; no `$` or `\` visible.
2. Clicking inside a formula gives a caret inside the formula; typing `a^2` shows a superscript 2; Right arrow then leaves the superscript; Right arrow at the end of the formula moves the caret into the text after it; typing continues as plain text.
3. Options A-D with `$\ln(x^2+1) + C$` render as formulas inside the inputs and are editable the same way. Clicking an option editor does not change the selected correct answer; clicking the card outside the editor still does.
4. Clicking "PT bac 2" inserts a display formula on its own line with the caret in the first placeholder; Tab moves to the next placeholder; Esc/Enter or Right arrow at the end returns to text below/after. Saving with unfilled placeholders stores no `\placeholder`.
5. Clicking a symbol chip while inside a formula inserts into that formula; while in text, creates a new inline formula with the caret in its first slot. Focus never leaves the active field when clicking toolbar buttons.
6. Typing `$` or `Alt+=` in text opens a new empty formula; Backspace in an empty formula removes it.
7. "Huong dan" opens a popover listing MathLive inline shortcuts (from `mf.inlineShortcuts`), structural keys, and editor keys, each rendered with KaTeX; Esc / outside click closes it.
8. Image upload inserts the image inline at the caret of the active field; saved string contains `![alt](/uploads/...)` unchanged.
9. Save + reload: the strings sent in `content`, `content_latex`, `content_markdown`, `explanation`, `answer_options[].content` are byte-identical to the originals for unedited questions (round-trip). Student page and PDF export render as before.
10. Vietnamese Telex/VNI typing in text areas works without duplicated characters.
11. Ctrl+S still saves while the caret is inside a formula.
12. `node src/components/common/mathDocSerializer.selfcheck.mjs` passes; `npm run build` succeeds; the editor chunk is lazy (not in the initial bundle).

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| MathLive LaTeX output differs from KaTeX support (e.g. `\placeholder`, `\mathrm` variants, `\left\lvert`) | Strip placeholders in serializer; keep KaTeX preview as fidelity check; if a construct fails in KaTeX, switch that template to a KaTeX-safe form (`|#?|`). |
| Legacy content without `$` delimiters (relies on `MathRenderer.preprocessMathText` auto-wrapping) shows as plain text in the editor | Acceptable: content still saved unchanged. Follow-up (not in scope): offer "convert detected math" using `preprocessMathText` exported from MathRenderer. |
| Escaped `\$` in text (currency) or `$` input rule annoying | Tokenizer treats `$` as delimiter (same as all existing renderers, so no regression). Input rule can be removed in one line if teachers complain. |
| Focus/selection bugs between ProseMirror and the shadow-DOM math-field (stopEvent, NodeSelection loops) | `stopEvent: () => true`, `ignoreMutation: () => true`; only focus mf on explicit arrow/selection; manual QA items 2, 4, 5. |
| Vietnamese IME inside a formula (text mode) | Teachers type prose in the TipTap text; formulas are math-only. Documented in Help. |
| Bundle size (~820 KB JS + fonts) | T11 lazy-loads the modal; fonts via `mathlive/fonts.css` load on demand. |
| Option `display` math inside single-line editors | `singleLine` parse joins lines; display math in options renders inline-block centered; acceptable. |
| `useEditor` re-creating editors when 4 option editors remount on question switch | Editors stay mounted (keys `A`-`D` stable); sync via `setContent({ emitUpdate: false })`. |
| `AddQuestionModal.jsx` still uses a plain textarea | Out of scope; reuse `MathTextEditor` there in a follow-up. |
