"""
File Name: smoke_rbac_ai.py
Description: End-to-end smoke test for RBAC + student AI exercise generation against a running API.
             Credentials come ONLY from CLI args or environment variables (never from .env files).
Created At: 2026-11-13
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent

Prepare (dev stack):
    docker exec smartlms_backend alembic upgrade head
    docker exec smartlms_backend python -m app.scripts.backfill_sgk_chapters
    # optionally set a head teacher: PUT /api/v1/subjects/{id} {"head_teacher_id": "<teacher uuid>"}

Run:
    python backend/scripts/smoke_rbac_ai.py --base-url http://localhost:8000 \
        --student-phone P --student-password P --teacher-a-phone P --teacher-a-password P \
        --teacher-b-phone P --teacher-b-password P --subject-name "Hóa"

Env fallbacks: SMOKE_BASE_URL, SMOKE_STUDENT_PHONE/PASSWORD, SMOKE_TEACHER_A_PHONE/PASSWORD,
SMOKE_TEACHER_B_PHONE/PASSWORD, SMOKE_CLASSMATE_PHONE/PASSWORD (optional), SMOKE_SUBJECT_NAME.
Teacher A and B must be in different classes (B has no access to A's resources).
Exit code 0 = all checks passed.
"""

import argparse
import json
import os
import sys
import uuid

import httpx

RESULTS = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not ok else ""))
    return ok


def login(client: httpx.Client, phone: str, password: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"phone": phone, "password": password})
    resp.raise_for_status()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def items(resp: httpx.Response):
    """Unwrap list or {items: [...]} payloads."""
    data = resp.json()
    return data.get("items", data) if isinstance(data, dict) else data


def main() -> int:
    env = os.environ.get
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=env("SMOKE_BASE_URL", "http://localhost:8000"))
    for who in ("student", "teacher-a", "teacher-b", "classmate"):
        key = who.upper().replace("-", "_")
        ap.add_argument(f"--{who}-phone", default=env(f"SMOKE_{key}_PHONE"))
        ap.add_argument(f"--{who}-password", default=env(f"SMOKE_{key}_PASSWORD"))
    ap.add_argument("--subject-name", default=env("SMOKE_SUBJECT_NAME", "Hóa"),
                    help="Substring of the subject name to generate for (default: Hóa)")
    ap.add_argument("--timeout", type=float, default=180.0, help="HTTP timeout seconds (LLM call is slow)")
    args = ap.parse_args()

    missing = [n for n in ("student_phone", "student_password", "teacher_a_phone", "teacher_a_password",
                           "teacher_b_phone", "teacher_b_password") if not getattr(args, n)]
    if missing:
        print("Missing credentials: " + ", ".join(missing), file=sys.stderr)
        return 2

    client = httpx.Client(base_url=args.base_url, timeout=args.timeout)
    stu = login(client, args.student_phone, args.student_password)
    ta = login(client, args.teacher_a_phone, args.teacher_a_password)
    tb = login(client, args.teacher_b_phone, args.teacher_b_password)

    # ---- Subject + chapters -------------------------------------------------------------
    subjects = items(client.get("/api/v1/subjects", headers=stu))
    subject = next((s for s in subjects if args.subject_name.lower() in s["subject_name"].lower()), None)
    if not check("student sees target subject", subject is not None, f"no subject like {args.subject_name!r}"):
        return 1
    sid = subject["subject_id"]

    r = client.get("/api/v1/ai-exercises/chapters", params={"subject_id": sid}, headers=stu)
    chapters = r.json() if r.status_code == 200 else []
    check("chapters non-empty for subject", r.status_code == 200 and len(chapters) > 0, r.text[:200])
    r = client.get("/api/v1/ai-exercises/chapters", params={"subject_id": str(uuid.uuid4())}, headers=stu)
    check("chapters for unknown/untaught subject -> 404", r.status_code == 404, str(r.status_code))
    if not chapters:
        return 1
    chapter = chapters[0]["chapter"]

    # ---- Student role restrictions ------------------------------------------------------
    check("student GET /documents -> 403", client.get("/api/v1/documents", headers=stu).status_code == 403)

    # ---- Upload guards ------------------------------------------------------------------
    def gen(payload: dict, file_tuple=None):
        files = {"file": file_tuple} if file_tuple else None
        return client.post("/api/v1/ai-exercises/student", data={"payload": json.dumps(payload)},
                           files=files, headers=stu)

    base = {"subject_id": sid, "chapters": [chapter], "topic_prompt": "smoke test", "duration_minutes": 15,
            "matrix": {"mcq": {"NhanBiet": 2, "ThongHieu": 0, "VanDung": 0},
                       "tf": {"NhanBiet": 1, "ThongHieu": 0, "VanDung": 0},
                       "short": {"NhanBiet": 1, "ThongHieu": 0, "VanDung": 0}}}
    r = gen(base, ("big.txt", b"a" * (1_100_000), "text/plain"))
    check("1.1 MB upload -> 413", r.status_code == 413, f"{r.status_code} {r.text[:150]}")
    r = gen(base, ("fake.pdf", b"not a pdf at all", "application/pdf"))
    check("fake .pdf -> 415", r.status_code == 415, f"{r.status_code} {r.text[:150]}")
    r = gen({**base, "chapters": []})
    check("empty chapters -> 422", r.status_code == 422, str(r.status_code))
    r = gen({**base, "chapters": ["__no_such_chapter__"]})
    check("unknown chapter -> 422", r.status_code == 422, str(r.status_code))
    r = gen({**base, "matrix": {"mcq": {"NhanBiet": 0, "ThongHieu": 0, "VanDung": 0}}})
    check("empty matrix -> 422", r.status_code == 422, str(r.status_code))
    r = gen({**base, "topic_prompt": "x" * 301})
    check("topic_prompt > 300 -> 422", r.status_code == 422, str(r.status_code))

    # ---- Real generation (2 MCQ + 1 TF + 1 short) ---------------------------------------
    note = ("Ester la hop chat huu co tao ra khi thay nhom OH cua carboxylic acid bang nhom OR. "
            "Phan ung este hoa la phan ung thuan nghich giua acid va alcohol voi xuc tac H2SO4 dac.\n").encode()
    r = gen(base, ("notes.txt", note, "text/plain"))
    if not check("student generation -> 201", r.status_code == 201, f"{r.status_code} {r.text[:300]}"):
        return summary()
    out = r.json()
    exercise_id = out.get("exercise_id") or (out.get("exercise") or {}).get("exercise_id")
    assignment_id = out.get("assignment_id") or (out.get("assignment") or {}).get("assignment_id")

    # Students read questions via /taking only (answer key hidden until submission)
    r = client.get(f"/api/v1/assignments/{assignment_id}/taking", headers=stu)
    check("student taking -> 200", r.status_code == 200, str(r.status_code))
    questions = r.json().get("questions", []) if r.status_code == 200 else []
    check("answer key hidden in taking payload",
          all("is_correct" not in o for q in questions for o in q.get("answer_options", [])))
    by_type = {}
    for q in questions:
        by_type.setdefault(q["question_type"], []).append(q)
    check("question counts 2 MCQ / 1 TF / 1 Short",
          len(by_type.get("MultipleChoice", [])) == 2 and len(by_type.get("TrueFalse", [])) == 1
          and len(by_type.get("ShortAnswer", [])) == 1, str({k: len(v) for k, v in by_type.items()}))
    tf = (by_type.get("TrueFalse") or [{}])[0]
    check("TF stored with 4 answer options", len(tf.get("answer_options", [])) == 4)
    for mcq in by_type.get("MultipleChoice", []):
        check("MCQ has 4 options", len(mcq["answer_options"]) == 4)

    # Assignment id: fall back to the student's feed if the response omitted it
    feed = items(client.get("/api/v1/assignments", headers=stu))
    if not assignment_id:
        assignment_id = next((a["assignment_id"] for a in feed if a["exercise_id"] == exercise_id), None)
    check("personal assignment in student's feed", any(a["assignment_id"] == assignment_id for a in feed))

    # ---- Isolation ----------------------------------------------------------------------
    if args.classmate_phone and args.classmate_password:
        mate = login(client, args.classmate_phone, args.classmate_password)
        mate_feed = items(client.get("/api/v1/assignments", headers=mate))
        check("classmate feed excludes personal assignment", all(a["assignment_id"] != assignment_id for a in mate_feed))
        check("classmate taking -> 404",
              client.get(f"/api/v1/assignments/{assignment_id}/taking", headers=mate).status_code == 404)
        check("classmate GET exercise -> 403/404", client.get(f"/api/v1/exercises/{exercise_id}", headers=mate).status_code in (403, 404))
    else:
        print("[SKIP] classmate checks (no --classmate-phone/--classmate-password)")
    for label, hdr in (("teacher A", ta), ("teacher B", tb)):
        check(f"{label} GET student's exercise -> 404", client.get(f"/api/v1/exercises/{exercise_id}", headers=hdr).status_code == 404)
        check(f"{label} cannot delete personal assignment",
              client.delete(f"/api/v1/assignments/{assignment_id}", headers=hdr).status_code in (403, 404))

    # ---- Cross-teacher 404s on teacher A's own exercise ---------------------------------
    r = client.post("/api/v1/exercises", json={"title": f"smoke-{uuid.uuid4().hex[:6]}", "subject_id": sid}, headers=ta)
    if check("teacher A creates exercise", r.status_code == 201, r.text[:200]):
        ex_a = r.json()["exercise_id"]
        check("teacher B GET A's exercise -> 404", client.get(f"/api/v1/exercises/{ex_a}", headers=tb).status_code == 404)
        check("teacher B PUT A's exercise -> 404/403",
              client.put(f"/api/v1/exercises/{ex_a}", json={"title": "hacked"}, headers=tb).status_code in (403, 404))
        check("teacher B DELETE A's exercise -> 404/403",
              client.delete(f"/api/v1/exercises/{ex_a}", headers=tb).status_code in (403, 404))
        check("teacher A GET own exercise -> 200", client.get(f"/api/v1/exercises/{ex_a}", headers=ta).status_code == 200)
        client.delete(f"/api/v1/exercises/{ex_a}", headers=ta)  # soft delete cleanup
    docs_a = items(client.get("/api/v1/documents", headers=ta))
    doc_ids_a = {d["document_id"] for d in docs_a}
    docs_b = items(client.get("/api/v1/documents", headers=tb))
    foreign = [d for d in docs_b if d["document_id"] not in doc_ids_a and d.get("uploaded_by")]
    mine_a = [d for d in docs_a if d["document_id"] not in {x["document_id"] for x in docs_b}]
    if mine_a:
        did = mine_a[0]["document_id"]
        check("teacher B GET A's document -> 404", client.get(f"/api/v1/documents/{did}", headers=tb).status_code == 404)
    else:
        print("[SKIP] cross-teacher document check (teacher A has no private document)")
    del foreign

    # ---- Attempt start + submit, TF grading ---------------------------------------------
    r = client.post(f"/api/v1/assignments/{assignment_id}/attempts", headers=stu)
    if check("attempt start -> 201", r.status_code == 201, r.text[:200]):
        attempt_id = r.json()["attempt_id"]
        answers = [{"question_id": q["question_id"], "answer_option_id": q["answer_options"][0]["option_id"]}
                   for q in by_type.get("MultipleChoice", [])]
        answers.append({"question_id": tf["question_id"], "answer_text": "a:true;b:true;c:true;d:true"})
        short = (by_type.get("ShortAnswer") or [{}])[0]
        answers.append({"question_id": short["question_id"], "answer_text": "x"})
        r = client.put(f"/api/v1/attempts/{attempt_id}/submit", json={"answers": answers}, headers=stu)
        check("attempt submit -> 200", r.status_code == 200, r.text[:200])
        if r.status_code == 200:
            res = {d["question_id"]: d for d in r.json()["detailed_results"]["questions"]}
            check("all 4 questions graded", len(res) == 4)


    return summary()


def summary() -> int:
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
