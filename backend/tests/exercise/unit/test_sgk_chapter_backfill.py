# File Name: test_sgk_chapter_backfill.py
# Description: Unit tests for SGK chapter backfill logic on synthetic pages.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

from app.scripts.backfill_sgk_chapters import compute_page_chapters, parse_number


def test_parse_number():
    assert parse_number("IV") == 4 and parse_number("12") == 12 and parse_number("IX") == 9


def test_toc_noise_dropped_and_ranges_filled():
    pages = {
        1: ["Cover"],
        2: ["Chương 2. TOC ENTRY", "x"],          # TOC before chapter 1: must not start chapter 2
        3: ["CHƯƠNG 1 ESTER - LIPID"],
        4: ["body"],
        5: ["CHƯƠNG 2 CARBOHYDRATE"],
        6: ["Chương 1 running header"],          # header noise after chapter 2 must not restart chapter 1
        7: ["CHƯƠNG 3 AMINE"],
    }
    out = compute_page_chapters(pages)
    assert 1 not in out and 2 not in out
    assert out[3] == out[4] == "Chương 1: ESTER - LIPID"
    assert out[5] == out[6] == "Chương 2: CARBOHYDRATE"
    assert out[7] == "Chương 3: AMINE"


def test_roman_numerals_and_chu_de():
    out = compute_page_chapters({1: ["CHỦ ĐỀ I. ABC"], 4: ["CHỦ ĐỀ II. DEF"]})
    assert out[1] == "Chủ đề 1: ABC" and out[4] == "Chủ đề 2: DEF"


def test_fallback_to_bai_and_unit():
    out = compute_page_chapters({1: ["Bài 1 Alpha"], 3: ["Bài 2 Beta"]})
    assert out[3] == "Bài 2: Beta"
    out = compute_page_chapters({2: ["Unit 1 Hello"], 5: ["Unit 2 Bye"]})
    assert out[5] == "Unit 2: Bye"


def test_single_chapter_doc_stays_null():
    assert compute_page_chapters({1: ["Chương 1 Only"], 2: ["text"]}) == {}
