<!-- File Name: README.md
Description: Guide for the .vibe/ project harness (Mistral Vibe) — structure, config sources and skills
Created At: 2026-11-08
Created By: Tam Khang
Updated At: 2026-11-08
Updated By: Tam Khang -->

# `.vibe/` — Mistral Vibe project harness

Thư mục này biến repo thành một project của **Mistral Vibe** (`vibe` CLI). Khi chạy
`vibe` trong thư mục gốc của repo, Vibe tự động load cấu hình project-local ở
`./.vibe/config.toml` (đè lên `~/.vibe/config.toml` của user).

## Cấu trúc

```text
.vibe/
├── config.toml                  # Project config: agent, model, system prompt, skills, tool rules
├── README.md                    # File này
├── prompts/
│   ├── project-rules.md         # System prompt — tổng hợp từ .agents/AGENTS.md + .claude/rules/
│   └── reviewer.md              # System prompt cho subagent reviewer
├── agents/
│   └── reviewer.toml            # Subagent review code read-only theo rules của repo
└── skills/
    ├── using-superpowers/       # Entry point của bộ superpowers (đã adapt cho Vibe)
    ├── brainstorming/           # Thiết kế tính năng trước khi code
    ├── writing-plans/           # Viết plan theo bite-sized tasks
    ├── executing-plans/         # Thực thi plan trong session
    ├── subagent-driven-development/  # Thực thi plan bằng subagent (task tool)
    ├── systematic-debugging/    # Debug 4 pha tìm root cause
    ├── test-driven-development/ # TDD: red -> green -> refactor
    ├── verification-before-completion/ # Verify trước khi báo xong
    ├── requesting-code-review/  # Yêu cầu review code
    ├── receiving-code-review/   # Tiếp nhận và xử lý feedback review
    ├── using-git-worktrees/     # Làm việc cô lập bằng git worktree
    ├── finishing-a-development-branch/ # Hoàn tất branch đúng quy trình
    └── repo-rules/              # Tóm tắt rules của repo (load bất cứ khi nào cần)
```

Mỗi skill là một thư mục chứa `SKILL.md` theo chuẩn **Agent Skills**
(YAML frontmatter + Markdown instructions), nên dùng được cả với các harness khác.

## Config lấy từ đâu

- `.agents/AGENTS.md` và `.claude/rules/coding_rules.md`,
  `.claude/rules/memory_and_completion_rules.md` được chuyển thành
  `.vibe/prompts/project-rules.md` (system prompt) và `.vibe/skills/repo-rules/`.
- Các rule chính: code/comments/UI bằng tiếng Anh, header file có
  `Created By`/`Updated By = Tam Khang`, soft delete only, không đụng `.env`,
  mỗi thay đổi schema phải có Alembic migration mới, task file trong
  `docs/tasks/` có header + status, memory file trong `.claude/memory/` sau khi
  user xác nhận.
- Rule "không đọc `.env`" còn được ép bằng `denylist` trong `config.toml`.
- Rule git: agent **không bao giờ tự `git commit`** — chỉ `git add` và đưa
  message mẫu để user tự commit.

## Skills (superpowers đã improve)

Bộ skill `superpowers` (obra/superpowers) được port và **improve** cho harness này:

- dùng đúng tool của Vibe (`task` với `config_name`, `read_file`, `edit`,
  `bash`, `grep`, `todo`, `ask_user_question`);
- invocation bằng `/<skill-name>` trong session interactive;
- lồng ghép với rules của repo (English-only, header `Tam Khang`, soft delete,
  workflow `docs/tasks/`, memory `.claude/memory/`).

Workflow chuẩn: `/brainstorming` -> `/writing-plans` ->
`/subagent-driven-development` (hoặc `/executing-plans`) ->
`/systematic-debugging` khi có bug -> `/requesting-code-review` ->
`/verification-before-completion`.

## Cách dùng

```bash
vibe                          # interactive, tự nhận .vibe/config.toml
vibe --agent reviewer         # chạy agent reviewer (top-level nếu cần)
/skill brainstorming          # hoặc gõ /<skill-name> để invoke skill
```

Subagent `reviewer` được spawn bằng tool `task` với `config_name = "reviewer"`.
