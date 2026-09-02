> Path: `docs/tasks/f_exe_05/f_exe_05_marker_pdf_latex_pipeline.md`
> Slice: `SL-EXE-05-AI` · Type: `feature` · Size: `large` · SP: `5`
> Depends on: `F-EXE-05`
> Status: `draft`
> Created At: `2026-09-01`
> Updated At: `2026-09-01`

# Task — `F-EXE-05-AI` Marker-PDF AI LaTeX OCR Pipeline for Math Question Import

**Author:** Tam Khang  
**Updated By:** Tam Khang  

---

## 1. Task Objective & Context
Currently, standard PDF text extraction via `pdfplumber` extracts flat raw text and loses 2D mathematical layouts (e.g., multi-level fractions $\frac{a}{b}$, exponents $x^2, x^3$, radicals $\sqrt{x}$, vectors $\vec{v}$). This task integrates deep learning OCR via `marker-pdf` (and underlying Surya/PyTorch models) into `ImportParserService.extract_pdf_content` to accurately parse full LaTeX mathematical formulas from uploaded exam PDFs, while gracefully distinguishing `.docx` (via native OMML parser) and `.pdf` files.

---

## 2. Scope & Implementation Requirements

### 1. Environment & Dependencies Setup
- Add `marker-pdf`, `torch`, `torchvision`, `transformers`, `surya-ocr` to `requirements.txt` / virtual environment.
- Configure offline model caching directory (`MARKER_MODEL_DIR` / Hugging Face cache) and CPU/GPU device selection (`TORCH_DEVICE=cpu` or `cuda`).

### 2. PDF & DOCX Routing / Distinction
- Ensure `ImportParserService.parse_document` and routers explicitly detect MIME type / file extensions (`.docx` vs `.pdf`):
  - **`.docx` Files**: Processed via internal `extract_docx_content` and `omml_to_latex` converter without AI overhead.
  - **`.pdf` Files**: Routed to `marker-pdf` model worker for deep LaTeX OCR extraction; fallback to `pdfplumber` with warning flag if worker is unavailable.

### 3. Asynchronous / Background Worker Execution
- Because `marker-pdf` OCR conversion takes several seconds per PDF document, introduce a background task or worker queue (e.g. Celery / FastAPI `BackgroundTasks` / async job) with status polling or websocket notification to avoid blocking HTTP request timeouts.

### 4. LaTeX Normalization & Validation
- Pass extracted Markdown/LaTeX text from `marker-pdf` through `ImportParserService.normalize_latex` and `validate_latex`.
- Store structured segments (`SegmentSchema`: text/math/image) and `content_latex` in database.
- Maintain soft-delete policy (`status = 'DELETED'`) for existing questions during re-import.

### 5. Frontend Dynamic LaTeX Preview
- `MathRenderer.jsx`: Render standard KaTeX LaTeX formulas (`$...$`, `$$...$$`, `\(...\)`, `\[...\]`) seamlessly.
- Exercise preview modal: Strip duplicate option prefixes and display clear mathematical formula cards.

---

## 3. Technical Workflow

```
Step 1: AI Dependencies & Environment Setup
  └── requirements.txt: marker-pdf, torch, torchvision, transformers, surya-ocr
  └── .env: TORCH_DEVICE=cpu, MARKER_CACHE_DIR

Step 2: PDF Math Extraction Optimization
  └── app/modules/exercise/services/import_parser_service.py:
        - extract_pdf_content: load marker models, convert PDF pages to LaTeX markdown
        - clean & sanitize OCR artifacts, extract inline math delimiters ($...$)
        - extract_docx_content: continue using OMML-to-LaTeX converter for Word

Step 3: Document Routing & Import API Integration
  └── app/modules/exercise/routers/exercises.py:
        - Validate file extension (.docx vs .pdf)
        - Route to appropriate extraction engine
        - Save Question entities with content_latex and segments

Step 4: Automated Verification & Unit Tests
  └── tests/exercise/unit/test_marker_pdf_import.py:
        - Test PDF math extraction with sample 12th grade Math exam PDF
        - Verify LaTeX formula accuracy ($y = \frac{x^2+1}{x-1}$, exponents, vectors)
```

---

## 4. Acceptance Criteria
1. Successfully parses 2D math formulas, fractions, radicals, powers, and vectors from `.pdf` files into standard LaTeX.
2. `.docx` files continue to be parsed fast and accurately via `omml_to_latex`.
3. All unit and integration test suites pass 100%.
