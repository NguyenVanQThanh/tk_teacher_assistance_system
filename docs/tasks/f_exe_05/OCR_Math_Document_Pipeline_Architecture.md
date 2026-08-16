# Thiết kế Pipeline OCR Tài Liệu Toán Học → Database → HTML5 → Export LaTeX/PDF

## 1. Mục tiêu hệ thống

Hệ thống cần xử lý tài liệu toán học từ PDF hoặc ảnh scan và thực hiện được các mục tiêu:

1. OCR toàn bộ nội dung tài liệu.
2. Phân biệt được:
   - text thường,
   - công thức toán inline,
   - công thức toán dạng block/display.
3. Chuyển công thức toán sang LaTeX.
4. Lưu dữ liệu vào Database theo cấu trúc rõ ràng.
5. Hiển thị lại nội dung trên web bằng HTML5.
6. Render công thức đúng định dạng toán học bằng KaTeX hoặc MathJax.
7. Có thể xuất lại dữ liệu từ Database thành:
   - HTML,
   - Markdown,
   - LaTeX,
   - PDF,
   - và có thể mở rộng sang DOCX.
8. Giữ được layout, thứ tự đọc, tọa độ và độ tin cậy OCR để phục vụ sửa lỗi hoặc tái dựng tài liệu.

---

# 2. Nhận xét về pipeline ban đầu

Pipeline ban đầu:

```text
PDF
 ↓
scan từng line
 ↓
detect text / formula
 ↓
text → OCR
formula → OCR Math → LaTeX
 ↓
DB
 ↓
HTML + LaTeX renderer
 ↓
Export
```

Ý tưởng này đúng về hướng tiếp cận, nhưng chưa đủ mạnh cho tài liệu toán học thực tế.

Điểm cần thay đổi lớn nhất là:

> Không nên lấy `line` làm đơn vị phân loại chính.

Một dòng trong tài liệu toán có thể chứa cả text và công thức.

Ví dụ:

```text
Câu 1. [NB] Cho hàm số f(x)=x³−3x²+2. Giá trị cực đại...
```

Thực tế nên được chia thành:

```text
[text] Câu 1. [NB] Cho hàm số
[math] f(x)=x^3-3x^2+2
[text] . Giá trị cực đại...
```

Do đó pipeline nên làm việc theo:

```text
Page
 ↓
Layout
 ↓
Block
 ↓
Segment
 ↓
Text / Math / Image
```

thay vì:

```text
Page
 ↓
Line
 ↓
Text hoặc Formula
```

---

# 3. Pipeline đề xuất

Kiến trúc tổng thể:

```text
                     ┌─ Native PDF ─→ PDF text + bbox
PDF ─→ Input detect ─┤
                     └─ Scanned PDF → Image 300 DPI
                                  ↓
                         Layout Detection
                                  ↓
              ┌───────────────────┼────────────────────┐
              ↓                   ↓                    ↓
            TEXT             INLINE MATH          DISPLAY MATH
              ↓                   ↓                    ↓
        Text OCR/parser      Math OCR → LaTeX     Math OCR → LaTeX
              └───────────────────┼────────────────────┘
                                  ↓
                       Reading-order reconstruction
                                  ↓
                         Structured Document JSON
                                  ↓
                              Database
                           ↙             ↘
                     HTML renderer      Exporter
                      KaTeX/MathJax       LaTeX/PDF
```

---

# 4. Stage 1 — Xác định loại PDF

Không phải PDF nào cũng nên OCR toàn bộ.

Có hai trường hợp:

## 4.1. Native PDF

PDF có text layer.

Ví dụ:

- file được export từ Word,
- LaTeX,
- trình soạn thảo PDF,
- tài liệu kỹ thuật điện tử.

Trong trường hợp này nên ưu tiên:

```text
PyMuPDF
```

để lấy:

- text,
- font,
- font size,
- bounding box,
- block,
- word,
- image,
- vị trí trên trang.

Không nên OCR lại toàn bộ trang nếu text layer đã có dữ liệu tốt.

Logic:

```python
if pdf_has_text_layer():
    mode = "native"
else:
    mode = "scan"
```

## 4.2. Scanned PDF

Nếu PDF chỉ chứa ảnh scan:

```text
PDF
 ↓
Render thành ảnh
 ↓
OCR
```

Khuyến nghị render khoảng:

```text
300 DPI
```

Có thể tăng lên:

```text
400 DPI
```

nếu công thức nhỏ hoặc scan chất lượng thấp.

---

# 5. Stage 2 — Layout Detection

Đây là thành phần quan trọng mà pipeline OCR đơn giản thường thiếu.

Layout Detection cần xác định:

```text
title
paragraph
question
answer
text
inline_formula
display_formula
table
image
page_number
header
footer
```

Mục tiêu là xác định:

```text
vùng nào là text
vùng nào là công thức
vùng nào là ảnh
vùng nào thuộc cùng một câu
```

Ví dụ:

```text
+------------------------------------------------+
| Câu 3. Một nguyên hàm của hàm số [ FORMULA ]  |
|                                                |
| A. [FORMULA]               B. [FORMULA]       |
|                                                |
| C. [FORMULA]               D. [FORMULA]       |
+------------------------------------------------+
```

Detector có thể trả:

```json
{
  "class": "formula",
  "bbox": [350, 220, 470, 275],
  "confidence": 0.96
}
```

Sau đó crop riêng vùng formula để đưa vào Mathematical Expression Recognition.

---

# 6. Công cụ Layout Detection

Có thể sử dụng:

## PaddleOCR / PP-Structure

Phù hợp cho:

- text detection,
- OCR,
- document layout,
- table,
- formula recognition.

## Docling

Phù hợp cho:

- document parsing,
- layout,
- reading order,
- structured document,
- formula enrichment.

## YOLO custom

Nếu muốn kiểm soát chính xác loại block riêng cho đề thi toán:

```text
text
inline_math
display_math
answer_option
question_number
figure
table
```

Có thể train YOLO custom dataset.

---

# 7. Stage 3 — Text OCR

Text thường có thể nhận dạng bằng:

```text
PaddleOCR
Tesseract
EasyOCR
```

Tuy nhiên nếu tài liệu chủ yếu tiếng Việt thì nên đánh giá thực tế trên dataset của dự án.

OCR text chỉ nên xử lý các block đã được layout detector xác định là text.

Không nên đưa formula qua OCR text thông thường.

---

# 8. Stage 4 — Mathematical Expression Recognition

Formula cần model riêng.

Không nên dùng duy nhất:

```text
Tesseract
EasyOCR
```

để nhận:

```text
∫
√
x²
lim
fraction
matrix
vector
subscript
superscript
```

Đây là bài toán:

> Mathematical Expression Recognition — MER

Input:

```text
ảnh công thức
```

Output:

```text
LaTeX
```

Ví dụ:

```text
ảnh:
      2x
   --------
    x² + 1
```

Output:

```latex
\frac{2x}{x^2+1}
```

---

# 9. Model Formula OCR nên thử

## 9.1. PaddleOCR Formula Recognition

Ưu điểm:

- tích hợp tốt với hệ sinh thái PaddleOCR,
- phù hợp làm pipeline hoàn chỉnh,
- có model formula riêng.

## 9.2. UniMERNet

Input:

```text
formula image
```

Output:

```latex
\frac{2x}{x^2+1}
```

Phù hợp cho tài liệu toán học thực tế.

## 9.3. pix2tex / LaTeX-OCR

Mục tiêu:

```text
image formula → LaTeX
```

Ví dụ Python:

```python
from pix2tex.cli import LatexOCR

model = LatexOCR()

latex = model(image)
```

Output:

```latex
\frac{2x}{x^2+1}
```

---

# 10. Inline Formula và Display Formula

Hệ thống cần phân biệt:

## Inline formula

Ví dụ:

```text
Cho hàm số f(x)=x²+1.
```

Structured representation:

```json
{
  "type": "math",
  "display": false,
  "latex": "f(x)=x^2+1"
}
```

## Display formula

Ví dụ:

```text
             x² + 1
      y = -----------
              x - 1
```

Structured representation:

```json
{
  "type": "math",
  "display": true,
  "latex": "y=\\frac{x^2+1}{x-1}"
}
```

---

# 11. Không nên lưu `$...$` trực tiếp vào DB

Không nên lưu:

```json
{
  "content": "Cho hàm số $f(x)=x^3-3x^2+2$."
}
```

Lý do:

```text
DATA
+
PRESENTATION
```

đã bị trộn chung.

Các ký hiệu:

```text
$...$
$$...$$
\(...\)
\[...\]
```

nên do renderer hoặc exporter quyết định.

Database chỉ nên lưu:

```json
{
  "type": "math",
  "latex": "f(x)=x^3-3x^2+2",
  "display": false
}
```

---

# 12. Structured Document

Một câu nên được lưu theo segment.

Ví dụ:

```json
{
  "page": 1,
  "type": "question",
  "number": 1,

  "segments": [
    {
      "type": "text",
      "content": "Câu 1. [NB] Cho hàm số "
    },

    {
      "type": "math",
      "display": false,
      "latex": "f(x)=x^3-3x^2+2"
    },

    {
      "type": "text",
      "content": ". Giá trị cực đại của hàm số là:"
    }
  ]
}
```

Ưu điểm:

- dễ render HTML,
- dễ export LaTeX,
- dễ sửa formula,
- dễ version control,
- dễ xử lý AI/RAG,
- không phải OCR lại khi đổi frontend.

---

# 13. Cấu trúc Document đề xuất

```text
Document
 ├── Page
 │    ├── Block
 │    │    ├── Segment TEXT
 │    │    ├── Segment MATH
 │    │    └── Segment TEXT
 │    │
 │    ├── Block
 │    │    └── Segment IMAGE
 │    │
 │    └── Block
 │
 └── Page
```

---

# 14. Database Schema

Có thể dùng PostgreSQL.

## documents

```text
documents
---------
id
filename
original_filename
page_count
mime_type
status
created_at
updated_at
```

## pages

```text
pages
-----
id
document_id
page_number
width
height
image_path
created_at
```

## blocks

```text
blocks
------
id
page_id
block_order
block_type

x0
y0
x1
y1

confidence
created_at
```

Các loại `block_type`:

```text
title
paragraph
question
answer
table
image
formula
header
footer
```

## segments

```text
segments
--------
id
block_id
segment_order

type

content_text
content_latex

display_math
confidence

raw_output
crop_path

created_at
updated_at
```

Các loại segment:

```text
text
math
image
```

---

# 15. Lưu Bounding Box

Mỗi block nên giữ tọa độ:

```json
{
  "bbox": {
    "x0": 102,
    "y0": 242,
    "x1": 470,
    "y1": 286
  }
}
```

Lợi ích:

- highlight vùng OCR trên ảnh,
- sửa lỗi trực quan,
- giữ layout,
- kiểm tra model,
- tạo annotation,
- train lại model sau này.

---

# 16. Lưu Formula Crop

Formula nên giữ ảnh gốc:

```json
{
  "latex": "\\frac{2x}{x^2+1}",
  "confidence": 0.91,
  "crop": "formula/123.png"
}
```

Nếu OCR sai, hệ thống có thể hiển thị:

```text
ảnh gốc
vs
LaTeX OCR
```

để người dùng chỉnh sửa.

---

# 17. RAW / NORMALIZED / VERIFIED

Nên giữ ba layer dữ liệu.

```text
RAW
NORMALIZED
VERIFIED
```

Ví dụ:

```json
{
  "raw": "\\frac { 2 x } { x ^ { 2 } + 1 }",

  "normalized": "\\frac{2x}{x^2+1}",

  "verified": "\\frac{2x}{x^2+1}"
}
```

## RAW

Output trực tiếp từ OCR model.

## NORMALIZED

Output đã được:

- chuẩn hóa spacing,
- chuẩn hóa command,
- fix format,
- normalize LaTeX.

## VERIFIED

Kết quả đã được:

- user sửa,
- hoặc hệ thống xác thực.

Nguyên tắc:

> Không overwrite `verified` khi chạy OCR lại.

---

# 18. Formula Validation

Không nên tin output math OCR 100%.

Sau Formula OCR nên có validator.

Pipeline:

```text
Formula image
 ↓
Math OCR
 ↓
LaTeX
 ↓
Syntax validation
 ↓
Render validation
 ↓
Accept / Review
```

Kiểm tra tối thiểu:

```text
{}
\frac{}{}
\sqrt{}
\left
\right
\begin{}
\end{}
```

---

# 19. Render Validation

Có thể dùng KaTeX để thử parse.

Pseudo logic:

```python
try:
    render_latex(latex)
    valid = True
except:
    valid = False
```

Nếu lỗi:

```text
needs_review = true
```

Database:

```json
{
  "latex": "\\frac{x^2+1}{x-1}",
  "valid": true,
  "confidence": 0.97,
  "needs_review": false
}
```

---

# 20. Visual Validation

Production system nên thêm bước:

```text
Original formula crop
           ↓
       OCR → LaTeX
           ↓
       render LaTeX
           ↓
     rendered image
           ↓
Compare original ↔ rendered
```

Nếu ảnh render từ LaTeX khác quá nhiều ảnh gốc:

```text
confidence ↓
```

và:

```text
needs_review = true
```

Điều này giúp phát hiện các lỗi kiểu:

```text
x² → x³
+ → -
1 → l
0 → O
√ → v
```

---

# 21. Reading Order Reconstruction

OCR tốt nhưng reading order sai vẫn tạo document sai.

Ví dụ trang có:

```text
Câu 1
A        B
C        D
```

nếu chỉ sort theo tọa độ X/Y đơn giản có thể sinh:

```text
Câu 1
A
C
B
D
```

trong khi cần:

```text
Câu 1
A
B
C
D
```

Vì vậy nên có:

```text
reading_order
```

trong block.

Ví dụ:

```json
{
  "block_order": 12
}
```

---

# 22. Document JSON trung gian

Database không nhất thiết là representation duy nhất.

Nên có một format trung gian:

```json
{
  "document_id": "doc_001",

  "pages": [
    {
      "page_number": 1,

      "blocks": [
        {
          "type": "question",
          "order": 1,

          "segments": [
            {
              "type": "text",
              "text": "Cho hàm số "
            },

            {
              "type": "math",
              "latex": "f(x)=x^3-3x^2+2",
              "display": false
            }
          ]
        }
      ]
    }
  ]
}
```

Representation này có thể dùng cho:

```text
API
HTML renderer
LaTeX exporter
Markdown exporter
AI processing
Search indexing
```

---

# 23. Frontend HTML5

Frontend không cần Python render toán.

Có thể dùng:

```text
KaTeX
```

hoặc:

```text
MathJax
```

---

# 24. KaTeX

Phù hợp nếu hệ thống chủ yếu là:

```text
đề thi
bài tập
toán phổ thông
công thức khoa học
```

Ưu điểm:

- nhanh,
- nhẹ,
- đẹp,
- phù hợp web app.

Ví dụ frontend nhận:

```json
{
  "type": "math",
  "display": false,
  "latex": "f(x)=x^3-3x^2+2"
}
```

React pseudo component:

```jsx
<Math
  latex={segment.latex}
  display={segment.display}
/>
```

---

# 25. MathJax

Phù hợp nếu:

- dùng nhiều macro LaTeX,
- cần support TeX rộng,
- cần MathML,
- accessibility phức tạp.

---

# 26. Renderer không nên sửa dữ liệu DB

Database:

```json
{
  "latex": "x^2+1",
  "display": false
}
```

Frontend quyết định render:

```text
inline
```

hoặc:

```text
display
```

Không lưu:

```text
$x^2+1$
```

trừ khi đó là format export Markdown.

---

# 27. Export Pipeline

Không nên lấy HTML rồi screenshot ra PDF nếu mục tiêu là:

```text
định dạng toán đẹp
font chuẩn
vector text
searchable PDF
```

Nên tạo pipeline riêng:

```text
Database
 ↓
Document JSON
 ↓
LaTeX Generator
 ↓
.tex
 ↓
XeLaTeX / LuaLaTeX
 ↓
PDF
```

---

# 28. LaTeX Export

Input:

```json
[
  {
    "type": "text",
    "content": "Cho hàm số "
  },
  {
    "type": "math",
    "latex": "f(x)=x^3-3x^2+2",
    "display": false
  }
]
```

Output:

```latex
Cho hàm số \(f(x)=x^3-3x^2+2\).
```

Display math:

```latex
\[
y=\frac{x^2+1}{x-1}
\]
```

---

# 29. PDF Export

Đề xuất:

```text
Document JSON
 ↓
LaTeX template
 ↓
XeLaTeX
 ↓
PDF
```

Có thể dùng:

```text
xelatex
```

hoặc:

```text
lualatex
```

XeLaTeX phù hợp khi cần:

- Unicode,
- tiếng Việt,
- font hệ thống,
- toán học đẹp.

---

# 30. Markdown Export

Có thể map:

```text
inline math
```

thành:

```markdown
$f(x)=x^2+1$
```

và:

```text
display math
```

thành:

```markdown
$$
y=\frac{x^2+1}{x-1}
$$
```

Nhưng đây chỉ nên là bước export.

Database không nên lưu trực tiếp delimiter Markdown.

---

# 31. HTML Export

Có hai cách.

## Cách 1

Xuất HTML + LaTeX source và dùng KaTeX browser-side.

## Cách 2

Render KaTeX server-side thành HTML trước.

Ví dụ:

```html
<span class="math-inline" data-latex="x^2+1"></span>
```

Sau đó KaTeX render.

---

# 32. Python Stack đề xuất

Nếu build MVP:

```text
PDF
│
├── PyMuPDF
│     ├── PDF parser
│     ├── coordinates
│     └── render page
│
├── OpenCV
│     ├── deskew
│     ├── denoise
│     └── crop
│
├── PaddleOCR
│     ├── text OCR
│     ├── layout
│     └── formula recognition
│
├── UniMERNet / pix2tex
│     └── formula → LaTeX
│
├── Pydantic
│     └── Document schema
│
├── SQLAlchemy
│
├── PostgreSQL
│     └── JSONB
│
├── FastAPI
│
├── Redis
│
└── Celery / RQ
      └── OCR jobs
```

---

# 33. Backend

Đề xuất:

```text
FastAPI
```

Phù hợp cho:

- REST API,
- async,
- upload file,
- OCR service,
- schema validation,
- Swagger/OpenAPI.

---

# 34. ORM

Có thể dùng:

```text
SQLAlchemy
```

hoặc:

```text
SQLModel
```

---

# 35. Database

Khuyến nghị:

```text
PostgreSQL
```

vì:

- relational data,
- JSONB,
- full-text search,
- index tốt,
- transaction tốt.

---

# 36. Object Storage

Không nên lưu toàn bộ ảnh binary trực tiếp vào Database.

Nên lưu file ở:

```text
S3
MinIO
filesystem
```

Database chỉ giữ:

```text
path
URL
metadata
```

Các file nên lưu:

```text
original PDF
page render
formula crops
figure crops
exported PDF
```

---

# 37. Queue OCR

OCR có thể nặng.

Không nên bắt request HTTP chờ OCR hoàn tất.

Kiến trúc:

```text
Upload
 ↓
FastAPI
 ↓
Job Queue
 ↓
OCR Worker
 ↓
Database
```

Có thể dùng:

```text
Redis
+
Celery
```

hoặc:

```text
RQ
```

---

# 38. Document Status

Database nên có:

```text
uploaded
processing
ocr_text
ocr_math
reconstructing
completed
failed
needs_review
```

Ví dụ:

```json
{
  "status": "processing",
  "progress": 63
}
```

---

# 39. Confidence Score

Mỗi segment nên có confidence.

Ví dụ:

```json
{
  "type": "math",
  "latex": "\\sqrt{61}",
  "confidence": 0.82
}
```

Có thể đặt threshold:

```text
>= 0.95 → auto accept
0.80–0.95 → normal
< 0.80 → needs review
```

Threshold thực tế phải tune theo dataset.

---

# 40. Manual Review UI

Một hệ thống production nên có editor.

Ví dụ:

```text
┌──────────────────────┬──────────────────────┐
│ Original PDF crop    │ OCR Result           │
│                      │                      │
│ [formula image]      │ \frac{2x}{x^2+1}     │
│                      │                      │
│                      │ [Rendered formula]    │
└──────────────────────┴──────────────────────┘
```

User có thể sửa LaTeX trực tiếp.

---

# 41. Không nên lưu toàn bộ document trong một field

Không nên:

```text
document.content
```

với nội dung:

```markdown
Câu 3. Cho hàm số $f(x)=\frac{2x}{x^2+1}$ là...
```

Vì sẽ khó:

- edit từng formula,
- lưu confidence,
- giữ bbox,
- thay đổi layout,
- export đa định dạng,
- tìm kiếm semantic.

---

# 42. Data Model đúng hơn

```text
Document
 ↓
Page
 ↓
Block
 ↓
Segment
```

Trong đó:

```text
Segment(TEXT)
Segment(MATH)
Segment(IMAGE)
```

---

# 43. Kiến trúc tổng thể

```text
                   USER UPLOAD
                       │
                       ▼
                ┌───────────────┐
                │   FastAPI     │
                └───────┬───────┘
                        │
                        ▼
                 Object Storage
                  original.pdf
                        │
                        ▼
              ┌─────────────────┐
              │ Document Worker │
              └────────┬────────┘
                       │
              ┌────────┴─────────┐
              │                  │
       Digital PDF          Scanned PDF
              │                  │
          PyMuPDF           Render image
              │                  │
              └────────┬─────────┘
                       ▼
                Layout detector
                       │
            ┌──────────┴───────────┐
            │                      │
          text                   math
            │                      │
        Text OCR            Formula OCR
            │                      │
            │                    LaTeX
            └──────────┬───────────┘
                       ▼
                 Reconstructor
                       │
                       ▼
               Document JSON
                       │
             ┌─────────┴──────────┐
             ▼                    ▼
         PostgreSQL            S3/MinIO
             │
             ▼
           API
             │
        ┌────┴─────┐
        ▼          ▼
      HTML       EXPORT
        │          │
      KaTeX       LaTeX
                   │
                XeLaTeX
                   │
                  PDF
```

---

# 44. Pipeline Processing chi tiết

```text
1. Upload PDF
2. Detect native / scanned
3. Extract page metadata
4. Render page image
5. Layout Detection
6. Detect text/math/image regions
7. Crop regions
8. Text OCR
9. Formula OCR
10. LaTeX normalization
11. Formula validation
12. Reading order reconstruction
13. Build Document JSON
14. Save DB
15. Save crop/image assets
16. Render HTML
17. Manual review nếu cần
18. Export
```

---

# 45. Native PDF Hybrid Pipeline

Với PDF có text layer:

```text
PDF
 ↓
PyMuPDF
 ↓
Text + bbox + font
 ↓
Detect suspicious math regions
 ↓
Render only formula area
 ↓
Formula OCR
 ↓
Merge text + math
```

Điểm quan trọng:

> Không OCR lại tất cả text nếu PDF đã chứa text chuẩn.

Điều này:

- nhanh hơn,
- ít lỗi hơn,
- giữ text Unicode tốt hơn.

---

# 46. Vì sao PDF text extraction vẫn làm vỡ toán học?

PDF không lưu semantic như:

```latex
x^3
```

Nó có thể chỉ lưu:

```text
glyph x tại vị trí A
glyph 3 tại vị trí cao hơn
```

Extractor có thể trả:

```text
x
3
```

thay vì:

```text
x³
```

Tương tự phân số:

```text
2x
────
x²+1
```

có thể extract thành:

```text
2x
x
2 + 1
```

Do đó math recognition vẫn cần thiết.

---

# 47. Font có thể giúp detect formula

Native PDF thường chứa font toán như:

```text
CMR
CMMI
CMSY
STIX
Latin Modern Math
Cambria Math
```

Có thể dùng font metadata như một feature để detect vùng toán.

Ví dụ:

```python
if font_name in math_fonts:
    likely_math = True
```

Nhưng không nên dựa hoàn toàn vào font vì:

- PDF có thể convert font,
- subset font,
- embedded custom font,
- formula có thể dùng font text bình thường.

---

# 48. Segment Detection

Một line:

```text
Cho hàm số f(x)=x²+1 có đạo hàm...
```

nên segment thành:

```json
[
  {
    "type": "text",
    "content": "Cho hàm số "
  },
  {
    "type": "math",
    "latex": "f(x)=x^2+1"
  },
  {
    "type": "text",
    "content": " có đạo hàm..."
  }
]
```

Đây là phần quan trọng hơn việc classify cả line.

---

# 49. Possible Detection Strategy

Có thể kết hợp:

```text
Layout model
+
font metadata
+
symbol heuristics
+
geometry
+
formula OCR confidence
```

Ví dụ symbols gợi ý math:

```text
=
+
−
×
÷
√
∫
∑
π
∞
^
_
<
>
≤
≥
```

Nhưng heuristic chỉ là hỗ trợ.

---

# 50. Normalization LaTeX

Model có thể output:

```latex
\frac { 2 x } { x ^ { 2 } + 1 }
```

Normalize thành:

```latex
\frac{2x}{x^2+1}
```

Có thể chuẩn hóa:

- spaces,
- `{}`,
- unicode operator,
- `\cdot`,
- `\times`,
- `\sqrt`,
- superscript,
- subscript.

---

# 51. Không nên normalize quá mạnh

Ví dụ:

```latex
x(x+1)
```

không nên tự đổi thành:

```latex
x^2+x
```

vì đó là symbolic transformation, không phải normalization.

Mục tiêu normalization:

> giữ nguyên ý nghĩa toán học và chỉ chuẩn hóa representation.

---

# 52. Formula Semantic Parsing — Optional

Sau này có thể bổ sung:

```text
LaTeX
 ↓
SymPy parser
 ↓
Expression Tree
```

Ví dụ:

```latex
x^2+1
```

thành:

```python
Add(Pow(x, 2), 1)
```

Nhưng đây nên là layer phụ.

Database gốc vẫn nên giữ LaTeX.

---

# 53. Search

Text search:

```text
PostgreSQL Full Text Search
```

Formula search có thể:

- search LaTeX,
- normalize LaTeX,
- parse expression,
- symbolic search.

Ví dụ muốn search:

```text
x^2 + 1
```

cần normalize để tránh khác biệt formatting.

---

# 54. RAG / AI về sau

Structured Document giúp AI dễ đọc hơn.

Ví dụ index:

```json
{
  "question": 3,
  "text": "Một nguyên hàm của hàm số",
  "formula": "\\frac{2x}{x^2+1}"
}
```

AI không cần đọc raw OCR bị vỡ.

---

# 55. Các dạng toán nên dùng làm benchmark

Test dataset nên có:

```text
x^3
x_1
log_2(x-1)

\frac{2x}{x^2+1}

\sqrt{61}

\vec{a}

\vec{a}\cdot\vec{b}

A(1;-2;3)

(-\infty;9)

x\in[0;60]

\int f(x)\,dx

\lim_{x\to\infty}

\sum_{i=1}^{n}

matrix

piecewise function
```

---

# 56. Metric cần đo

Không chỉ đo OCR Character Accuracy.

Nên đo:

## Text

```text
CER
WER
```

## Formula

```text
Exact Match
BLEU / Edit Distance
Render similarity
Symbol accuracy
```

## Layout

```text
Detection precision
Detection recall
IoU
Reading order accuracy
```

---

# 57. MVP đề xuất

Version đầu không cần làm tất cả.

## MVP 1

```text
PDF Upload
 ↓
Render pages
 ↓
PaddleOCR layout
 ↓
Text OCR
 ↓
Formula OCR
 ↓
Structured JSON
 ↓
PostgreSQL
 ↓
React + KaTeX
```

## MVP 2

Thêm:

```text
manual correction
confidence
formula crop
```

## MVP 3

Thêm:

```text
LaTeX exporter
XeLaTeX PDF export
```

## MVP 4

Thêm:

```text
visual validation
native PDF optimization
formula search
AI/RAG
```

---

# 58. Stack MVP cụ thể

Backend:

```text
Python 3.11+
FastAPI
Pydantic
SQLAlchemy
PostgreSQL
Redis
Celery
```

Document:

```text
PyMuPDF
OpenCV
Pillow
```

OCR:

```text
PaddleOCR
PaddleOCR Formula Recognition
```

Alternative Math OCR:

```text
UniMERNet
pix2tex
```

Frontend:

```text
React
TypeScript
KaTeX
```

Storage:

```text
MinIO
```

Export:

```text
Jinja2
XeLaTeX
```

---

# 59. Suggested Python Project Structure

```text
app/
│
├── api/
│   ├── documents.py
│   ├── pages.py
│   ├── blocks.py
│   └── export.py
│
├── core/
│   ├── config.py
│   └── logging.py
│
├── db/
│   ├── models/
│   │   ├── document.py
│   │   ├── page.py
│   │   ├── block.py
│   │   └── segment.py
│   │
│   └── session.py
│
├── schemas/
│   ├── document.py
│   ├── block.py
│   └── segment.py
│
├── services/
│   ├── pdf/
│   │   ├── detect.py
│   │   ├── extract.py
│   │   └── render.py
│   │
│   ├── layout/
│   │   └── detector.py
│   │
│   ├── ocr/
│   │   ├── text.py
│   │   └── formula.py
│   │
│   ├── reconstruct/
│   │   └── document.py
│   │
│   ├── latex/
│   │   ├── normalize.py
│   │   └── validate.py
│   │
│   └── export/
│       ├── html.py
│       ├── markdown.py
│       ├── latex.py
│       └── pdf.py
│
├── workers/
│   └── ocr_worker.py
│
└── main.py
```

---

# 60. Ví dụ Pydantic Schema

```python
from typing import Literal
from pydantic import BaseModel


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class Segment(BaseModel):
    type: Literal["text", "math", "image"]

    text: str | None = None
    latex: str | None = None

    display: bool = False

    confidence: float | None = None
    bbox: BoundingBox | None = None


class Block(BaseModel):
    type: str
    order: int
    segments: list[Segment]


class Page(BaseModel):
    page_number: int
    blocks: list[Block]


class Document(BaseModel):
    document_id: str
    pages: list[Page]
```

---

# 61. Ví dụ API Response

```json
{
  "document_id": "doc_123",
  "page_number": 1,

  "blocks": [
    {
      "type": "question",
      "order": 1,

      "segments": [
        {
          "type": "text",
          "text": "Cho hàm số "
        },
        {
          "type": "math",
          "latex": "f(x)=x^3-3x^2+2",
          "display": false,
          "confidence": 0.97
        },
        {
          "type": "text",
          "text": ". Giá trị cực đại của hàm số là:"
        }
      ]
    }
  ]
}
```

---

# 62. Render Logic

Pseudo code frontend:

```javascript
segments.map(segment => {
    if (segment.type === "text") {
        return <span>{segment.text}</span>
    }

    if (segment.type === "math") {
        return (
            <Math
                latex={segment.latex}
                display={segment.display}
            />
        )
    }
})
```

---

# 63. Error Handling

OCR pipeline nên ghi lỗi theo stage.

Ví dụ:

```json
{
  "stage": "formula_ocr",
  "page": 3,
  "block": 18,
  "error": "model inference failed"
}
```

Không nên fail toàn bộ document chỉ vì một formula.

---

# 64. Retry

Queue worker có thể retry:

```text
GPU unavailable
model timeout
temporary storage error
```

Nhưng không nên retry vô hạn.

---

# 65. Logging

Nên log:

```text
document_id
page_id
block_id
stage
model
processing_time
confidence
error
```

Sau này rất hữu ích khi benchmark.

---

# 66. Model Version

Database nên lưu:

```json
{
  "model": "unimernet",
  "model_version": "x.y",
  "ocr_version": 3
}
```

Để biết output nào được tạo bởi model nào.

---

# 67. Re-OCR

Khi model mới tốt hơn:

```text
original crop
 ↓
new model
 ↓
new RAW
 ↓
new NORMALIZED
```

Nhưng nếu đã có:

```text
VERIFIED
```

thì giữ nguyên verified.

---

# 68. Versioning

Một formula có thể có:

```text
OCR v1
OCR v2
User edit
```

Có thể tạo:

```text
segment_revisions
```

Schema:

```text
id
segment_id
revision
raw
normalized
verified
model
created_at
```

---

# 69. Security

Khi render LaTeX hoặc HTML:

Không inject trực tiếp raw HTML do OCR tạo.

Text cần escape.

LaTeX renderer nên chạy với giới hạn command.

Khi compile LaTeX:

```text
disable shell escape
```

Không dùng:

```text
-shell-escape
```

với tài liệu không tin cậy.

---

# 70. Formula Sanitization

Có thể whitelist các command cần dùng:

```text
\frac
\sqrt
\sum
\int
\lim
\vec
\left
\right
\begin
\end
```

Đặc biệt quan trọng nếu LaTeX đi vào server-side compiler.

---

# 71. PDF Export Security

Nên chạy XeLaTeX trong:

```text
Docker sandbox
```

với:

```text
CPU limit
RAM limit
timeout
filesystem isolation
```

---

# 72. Docker Services

Ví dụ:

```text
docker-compose
│
├── api
├── worker
├── postgres
├── redis
├── minio
└── frontend
```

Có thể có riêng:

```text
formula-service
```

nếu model cần GPU.

---

# 73. GPU Service

Nếu Formula OCR dùng GPU:

```text
API
 ↓
Redis Queue
 ↓
GPU Worker
 ↓
Formula Model
```

Không load model lại cho mỗi request.

Model nên load một lần khi worker start.

---

# 74. Batch Processing

Một page có thể chứa nhiều formula.

Nên crop tất cả formula rồi batch inference:

```text
formula_1
formula_2
formula_3
formula_4
 ↓
batch
 ↓
GPU
```

Nhanh hơn inference từng formula một.

---

# 75. Cache

Có thể hash formula crop:

```text
SHA256(image)
```

Nếu gặp lại ảnh giống nhau:

```text
reuse OCR result
```

Không bắt buộc cho MVP.

---

# 76. File Naming

Không nên dùng filename người dùng trực tiếp.

Nên:

```text
document_id/page_001.png

document_id/formulas/formula_000123.png
```

---

# 77. Data Backup

Quan trọng nhất nên backup:

```text
original PDFs
verified formula data
manual corrections
database
```

Raw generated page images có thể regenerate.

---

# 78. Kết luận kiến trúc

Pipeline cuối cùng nên là:

```text
PDF
 ↓
Native / Scan Detection
 ↓
Page Extraction / Rendering
 ↓
Layout Analysis
 ↓
Region Detection
 ↓
Text / Inline Math / Display Math / Image
 ↓
Text OCR            Formula OCR
                         ↓
                       LaTeX
 ↓
Normalization
 ↓
Validation
 ↓
Reading Order Reconstruction
 ↓
Structured Document JSON
 ↓
Database
 ↓
┌────────────────────┬─────────────────────┐
│                    │                     │
HTML              Markdown              LaTeX
│                                          │
KaTeX / MathJax                           XeLaTeX
                                           │
                                          PDF
```

---

# 79. Nguyên tắc kiến trúc quan trọng nhất

## Nguyên tắc 1

Không classify toàn bộ `line` thành text hoặc formula.

Thay vào đó:

```text
line/block
 ↓
segments
 ↓
text + math + text
```

## Nguyên tắc 2

LaTeX là dữ liệu của `math segment`.

Không phải dữ liệu của cả document.

## Nguyên tắc 3

Không lưu presentation delimiter vào Database.

DB:

```latex
x^2+1
```

Renderer quyết định:

```latex
\(x^2+1\)
```

hoặc:

```latex
\[
x^2+1
\]
```

## Nguyên tắc 4

Giữ original crop + bbox + confidence.

Điều này giúp:

```text
debug
manual review
re-OCR
training
validation
```

## Nguyên tắc 5

Giữ:

```text
RAW
NORMALIZED
VERIFIED
```

Không overwrite user correction.

## Nguyên tắc 6

Export nên dựa trên Structured Document.

Không nên lấy HTML screenshot thành PDF nếu yêu cầu chất lượng toán học cao.

---

# 80. Stack cuối cùng đề xuất

```text
Language
    Python

API
    FastAPI

PDF
    PyMuPDF

Image Processing
    OpenCV
    Pillow

Layout
    PaddleOCR
    Docling
    hoặc YOLO custom

Text OCR
    PaddleOCR

Math OCR
    PaddleOCR Formula Recognition
    UniMERNet
    pix2tex

Schema
    Pydantic

ORM
    SQLAlchemy

Database
    PostgreSQL + JSONB

Queue
    Redis + Celery / RQ

Storage
    S3 / MinIO

Frontend
    React + TypeScript

Math Render
    KaTeX
    hoặc MathJax

Export Template
    Jinja2

PDF Export
    XeLaTeX / LuaLaTeX

Deployment
    Docker
```

---

# 81. Recommended MVP Flow

Nếu bắt đầu code ngay, nên đi theo thứ tự:

```text
1. Upload PDF
2. PyMuPDF render page
3. PaddleOCR layout
4. Detect text/math
5. PaddleOCR text
6. Formula Recognition → LaTeX
7. Build Document JSON
8. Save PostgreSQL
9. FastAPI GET document
10. React render
11. KaTeX render math
12. Manual formula editor
13. LaTeX exporter
14. XeLaTeX PDF exporter
15. Confidence + validation
16. Native PDF optimization
17. Visual validation
```

Không nên làm tất cả ngay từ phiên bản đầu.

---

# 82. Final Architecture

```text
                   ┌─────────────────┐
                   │   User Upload   │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │     FastAPI     │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Object Storage  │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Document Worker │
                   └────────┬────────┘
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
      Native PDF                       Scan PDF
             │                             │
          PyMuPDF                     Page Render
             │                             │
             └──────────────┬──────────────┘
                            ▼
                    Layout Detection
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
             TEXT                       MATH
               │                         │
          Text OCR                  Formula OCR
                                         │
                                       LaTeX
               └────────────┬────────────┘
                            ▼
                  Normalization
                            │
                            ▼
                    Validation
                            │
                            ▼
                 Document Rebuild
                            │
                            ▼
                 Structured JSON
                            │
               ┌────────────┴─────────────┐
               ▼                          ▼
          PostgreSQL                  S3 / MinIO
               │
               ▼
              API
               │
        ┌──────┴────────┐
        ▼               ▼
      React           Export
        │               │
      KaTeX          LaTeX
                        │
                     XeLaTeX
                        │
                       PDF
```

---

# 83. Chốt

Pipeline ban đầu:

```text
line → text/formula → OCR → DB
```

nên được nâng thành:

```text
Page
 ↓
Layout
 ↓
Block
 ↓
Segment
 ↓
Text / Formula / Image
 ↓
Specialized Recognition
 ↓
Structured Document
 ↓
Database
 ↓
Renderer / Exporter
```

Đây là cấu trúc phù hợp hơn nếu mục tiêu là xây một hệ thống OCR tài liệu toán học có thể phát triển lâu dài, thay vì chỉ làm một OCR demo.
