"""
File Name: user_import_service.py
Description: Bulk user import for the Admin portal. Parses CSV/XLSX by header name, validates every row
    (optionally as a dry run) and creates accounts through AdminUserService.create_user. Also builds the
    downloadable template files.
Created At: 2026-11-14
Created By: AI Agent
Updated At: 2026-11-14
Updated By: AI Agent
"""
import csv
import io
import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.modules.admin.repository import AdminUserRepository
from app.modules.admin.schemas import AdminUserCreateRequest
from app.modules.admin.services.user_service import AdminUserService

logger = logging.getLogger("smartlms.admin.user_import")

MAX_IMPORT_BYTES = 2 * 1024 * 1024  # 2 MiB is far above 1000 user rows
MAX_IMPORT_ROWS = 1000

# Canonical field -> accepted header aliases (compared after normalization: lowercase, no accents/spaces).
_HEADER_ALIASES: Dict[str, Tuple[str, ...]] = {
    "full_name": ("fullname", "hovaten", "hoten", "ten", "name"),
    "role": ("role", "vaitro"),
    "phone": ("phone", "sodienthoai", "sdt", "dienthoai"),
    "email": ("email", "thudientu"),
    "birthday": ("birthday", "ngaysinh", "dob", "birthdate"),
    "code": ("code", "ma", "mahocsinh", "magiaovien", "mahs", "magv"),
    "class_name": ("classname", "class", "lop", "tenlop"),
    "department": ("department", "to", "tobomon", "bomon"),
}

TEMPLATE_HEADERS = ["full_name", "role", "phone", "email", "birthday", "code", "class_name", "department"]
TEMPLATE_LABELS = ["Họ và tên", "Vai trò", "Số điện thoại", "Email", "Ngày sinh", "Mã (HS/GV)", "Lớp", "Tổ bộ môn"]
TEMPLATE_SAMPLE_ROWS = [
    ["Nguyễn Văn An", "Student", "0912345678", "an.nguyen@school.edu.vn", "2008-05-20", "HS2025001", "10A1", ""],
    ["Trần Thị Bình", "Teacher", "0987654321", "binh.tran@school.edu.vn", "1990-09-01", "GV2025001", "", "Toán học"],
]

_ROLE_ALIASES = {
    "student": "Student", "hocsinh": "Student", "hs": "Student",
    "teacher": "Teacher", "giaovien": "Teacher", "gv": "Teacher",
}  # Admin is intentionally absent: admin accounts cannot be imported.


def _norm(text: Any) -> str:
    """Lowercase, strip Vietnamese accents and every non-alphanumeric character."""
    import unicodedata
    s = unicodedata.normalize("NFD", str(text or "").strip().lower().replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)


def _error(code: str, message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def _cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d") if isinstance(value, date) and not isinstance(value, datetime) \
            else value.date().isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _parse_birthday(raw: str) -> Optional[date]:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError("Ngày sinh không hợp lệ (dùng YYYY-MM-DD hoặc DD/MM/YYYY).")


def _normalize_phone(raw: str) -> str:
    """Excel drops the leading zero of numeric phone cells; restore it for 9-digit values."""
    digits = re.sub(r"[\s\-\.]", "", raw)
    if re.fullmatch(r"[1-9]\d{8}", digits):
        return "0" + digits
    return digits


class UserImportService:
    @staticmethod
    def read_rows(filename: str, contents: bytes) -> List[Dict[str, str]]:
        """Parse a CSV/XLSX upload into canonical-field dicts. Raises HTTPException on bad files."""
        if len(contents) > MAX_IMPORT_BYTES:
            raise _error("ERR-ADMIN-FILE_TOO_LARGE", "File is too large (max 2 MB).", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        name = (filename or "").lower()
        if name.endswith(".xlsx"):
            raw_rows = UserImportService._read_xlsx(contents)
        elif name.endswith(".csv"):
            raw_rows = UserImportService._read_csv(contents)
        else:
            raise _error("ERR-ADMIN-FILE_TYPE", "Only .xlsx and .csv files are supported.", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        raw_rows = [r for r in raw_rows if any(_cell_text(c) for c in r)]
        if not raw_rows:
            raise _error("ERR-ADMIN-EMPTY_FILE", "Uploaded file is empty.")

        header_map: Dict[int, str] = {}
        for idx, cell in enumerate(raw_rows[0]):
            key = _norm(cell)
            for field, aliases in _HEADER_ALIASES.items():
                if key and key in aliases + (_norm(field),) and field not in header_map.values():
                    header_map[idx] = field
                    break
        if "full_name" not in header_map.values():
            raise _error("ERR-ADMIN-MISSING_COLUMN", "Missing required column: full_name (Họ và tên).")
        if "role" not in header_map.values():
            raise _error("ERR-ADMIN-MISSING_COLUMN", "Missing required column: role (Vai trò).")

        data_rows = raw_rows[1:]
        if len(data_rows) > MAX_IMPORT_ROWS:
            raise _error("ERR-ADMIN-TOO_MANY_ROWS", f"Too many rows (max {MAX_IMPORT_ROWS}).")
        rows = []
        for r in data_rows:
            item = {field: "" for field in header_map.values()}
            for idx, field in header_map.items():
                if idx < len(r):
                    item[field] = _cell_text(r[idx])
            rows.append(item)
        return rows

    @staticmethod
    def _read_csv(contents: bytes) -> List[List[Any]]:
        try:
            text = contents.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = contents.decode("cp1258", errors="replace")
        sample = text[:2048]
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        return [list(r) for r in csv.reader(io.StringIO(text), delimiter=delimiter)]

    @staticmethod
    def _read_xlsx(contents: bytes) -> List[List[Any]]:
        from openpyxl import load_workbook
        if not contents.startswith(b"PK"):
            raise _error("ERR-ADMIN-FILE_TYPE", "The file is not a valid .xlsx workbook.", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        try:
            wb = load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
            sheet = wb.active
            return [list(r) for r in sheet.iter_rows(values_only=True)]
        except Exception as exc:  # corrupt zip, unsupported features, etc.
            logger.warning("XLSX parse failed: %s", exc)
            raise _error("ERR-ADMIN-FILE_TYPE", "Cannot read the .xlsx file.", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    @classmethod
    def build_payload(cls, row: Dict[str, str]) -> AdminUserCreateRequest:
        """Convert one raw row into a validated create request. Raises ValueError/ValidationError."""
        role_key = _norm(row.get("role", ""))
        role = _ROLE_ALIASES.get(role_key)
        if not role:
            raise ValueError(f"Vai trò '{row.get('role', '')}' không hợp lệ (Student hoặc Teacher).")
        return AdminUserCreateRequest(
            full_name=row.get("full_name", ""),
            role=role,
            phone=_normalize_phone(row["phone"]) if row.get("phone") else None,
            email=row.get("email") or None,
            birthday=_parse_birthday(row.get("birthday", "")),
            code=row.get("code") or None,
            class_name=row.get("class_name") or None,
            department=row.get("department") or None,
            is_active_immediately=True,
        )

    @classmethod
    def import_users(cls, db: Session, filename: str, contents: bytes, dry_run: bool = False) -> Dict[str, Any]:
        """
        Validate (and, unless dry_run, create) every row. One bad row never blocks the others.
        Returns counts, per-row errors and the temporary passwords of created accounts.
        """
        rows = cls.read_rows(filename, contents)
        errors: List[Dict[str, Any]] = []
        created: List[Dict[str, Any]] = []
        seen_phone, seen_email, seen_code = set(), set(), set()
        valid = 0

        for line, row in enumerate(rows, start=2):
            label = row.get("full_name") or f"dòng {line}"
            try:
                payload = cls.build_payload(row)
                # Duplicates inside the same file (the DB check only sees rows already committed)
                for value, seen, field in ((payload.phone, seen_phone, "Số điện thoại"),
                                           ((payload.email or "").lower() or None, seen_email, "Email"),
                                           ((payload.code or "").lower() or None, seen_code, "Mã")):
                    if value and value in seen:
                        raise ValueError(f"{field} bị trùng trong file.")
                    if value:
                        seen.add(value)
                if dry_run:
                    cls._precheck(db, payload)
                else:
                    result = AdminUserService.create_user(db=db, payload=payload)
                    created.append({
                        "row": line, "full_name": result.full_name, "role": result.role,
                        "phone": result.phone, "email": result.email,
                        "temporary_password": result.temporary_password,
                    })
                valid += 1
            except ValidationError as exc:
                msg = "; ".join(e["msg"].replace("Value error, ", "") for e in exc.errors())
                errors.append({"row": line, "name": label, "error": msg})
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, dict) else {}
                errors.append({"row": line, "name": label, "error": detail.get("message", str(exc.detail)),
                               "code": detail.get("code")})
            except ValueError as exc:
                errors.append({"row": line, "name": label, "error": str(exc)})
            except Exception as exc:
                db.rollback()
                logger.exception("Unexpected failure importing row %s", line)
                errors.append({"row": line, "name": label, "error": "Lỗi hệ thống khi tạo tài khoản."})

        return {
            "dry_run": dry_run,
            "total_processed": len(rows),
            "valid_count": valid,
            "successful_count": 0 if dry_run else len(created),
            "failed_count": len(errors),
            "errors": errors,
            "created": created,
        }

    @staticmethod
    def _precheck(db: Session, payload: AdminUserCreateRequest) -> None:
        """Dry-run checks that mirror create_user without writing anything."""
        if not AdminUserRepository.get_role_by_name(db, payload.role):
            raise _error("ERR-ADMIN-INVALID_ROLE", f"Role '{payload.role}' does not exist.", 422)
        if payload.phone and AdminUserRepository.get_user_by_phone(db, payload.phone):
            raise _error("ERR-ADMIN-DUPLICATE_PHONE", f"Số điện thoại '{payload.phone}' đã được đăng ký.")
        if payload.email and AdminUserRepository.get_user_by_email(db, payload.email):
            raise _error("ERR-ADMIN-DUPLICATE_EMAIL", f"Email '{payload.email}' đã được đăng ký.")
        if payload.code and AdminUserRepository.check_code_exists(db, payload.code):
            raise _error("ERR-ADMIN-DUPLICATE_CODE", f"Mã '{payload.code}' đã được sử dụng.")
        AdminUserService.validate_user_age(payload.role, payload.birthday)

    @staticmethod
    def build_template_xlsx() -> bytes:
        """Template workbook: data sheet (header + 2 sample rows) and an instructions sheet."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        wb = Workbook()
        ws = wb.active
        ws.title = "Users"
        ws.append(TEMPLATE_HEADERS)
        for r in TEMPLATE_SAMPLE_ROWS:
            ws.append(r)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="4F46E5")
        for col, width in zip("ABCDEFGH", (24, 12, 16, 30, 14, 14, 10, 16)):
            ws.column_dimensions[col].width = width
        for row in ws.iter_rows(min_row=2, min_col=3, max_col=3):
            for cell in row:
                cell.number_format = "@"  # keep the leading zero of phone numbers
        guide = wb.create_sheet("Instructions")
        for line in (
            ["Column", "Required", "Notes"],
            ["full_name", "Yes", "Họ và tên, 2-100 ký tự, không chứa số hoặc ký tự đặc biệt"],
            ["role", "Yes", "Student hoặc Teacher"],
            ["phone", "No", "10 chữ số bắt đầu bằng 0 (định dạng ô là Text để giữ số 0)"],
            ["email", "No", "Email hợp lệ, không trùng"],
            ["birthday", "No", "YYYY-MM-DD hoặc DD/MM/YYYY. Học sinh >= 16 tuổi, giáo viên >= 22 tuổi"],
            ["code", "No", "Mã học sinh / giáo viên, không trùng"],
            ["class_name", "No", "Tên lớp đã tồn tại (dành cho học sinh)"],
            ["department", "No", "Tổ bộ môn (dành cho giáo viên)"],
            [],
            ["Mật khẩu được hệ thống tự tạo; sau khi nhập sẽ hiển thị danh sách mật khẩu tạm thời một lần."],
        ):
            guide.append(line)
        guide.column_dimensions["A"].width = 14
        guide.column_dimensions["C"].width = 80
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    @staticmethod
    def build_template_csv() -> bytes:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(TEMPLATE_HEADERS)
        writer.writerows(TEMPLATE_SAMPLE_ROWS)
        return buf.getvalue().encode("utf-8-sig")
