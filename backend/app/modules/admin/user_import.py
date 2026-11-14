# File Name: user_import.py
# Description: Shared tabular upload parser utilities for CSV and XLSX imports across admin and academic modules.
# Created At: 2026-11-14
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException, UploadFile, status

from app.modules.admin.services.user_import_service import (
    MAX_IMPORT_BYTES,
    UserImportService,
    _cell_text,
)

logger = logging.getLogger(__name__)


def parse_tabular_bytes(filename: str, contents: bytes) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Parse raw CSV or XLSX file bytes into normalized header names and row dictionaries.
    """
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ERR-ADMIN-EMPTY_FILE", "message": "Uploaded file is empty."},
        )

    if len(contents) > MAX_IMPORT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "ERR-ADMIN-FILE_TOO_LARGE", "message": "Uploaded file exceeds 5 MB limit."},
        )

    ext = Path(filename or "").suffix.lower()
    if ext == ".csv":
        raw_rows = UserImportService._read_csv(contents)
    elif ext in (".xlsx", ".xlsm"):
        raw_rows = UserImportService._read_xlsx(contents)
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": "ERR-ADMIN-FILE_TYPE",
                "message": "Unsupported file format. Only .csv and .xlsx files are accepted.",
            },
        )

    if not raw_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ERR-ADMIN-EMPTY_FILE", "message": "Uploaded table has no rows."},
        )

    header_row = raw_rows[0]
    headers: List[str] = []
    for idx, col in enumerate(header_row):
        header_name = _cell_text(col).strip().lower()
        headers.append(header_name or f"col_{idx}")

    parsed_rows: List[Dict[str, Any]] = []
    for row_idx, row in enumerate(raw_rows[1:], start=2):
        # Skip completely empty rows
        if not any(cell is not None and str(cell).strip() != "" for cell in row):
            continue
        record: Dict[str, Any] = {"__row_num__": row_idx}
        for col_idx, header in enumerate(headers):
            val = row[col_idx] if col_idx < len(row) else None
            record[header] = val
        parsed_rows.append(record)

    logger.info("Parsed %d non-empty tabular rows from file '%s'", len(parsed_rows), filename)
    return headers, parsed_rows


async def parse_tabular_upload(file: UploadFile) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Read an uploaded CSV or XLSX FastAPI UploadFile and parse it into normalized row records.
    """
    contents = await file.read()
    return parse_tabular_bytes(file.filename or "", contents)
