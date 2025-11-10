# Cline Rules — High-Accuracy, Low-Friction

## 0) Agent Contract

* Always show a short **PLAN** first (bulleted, ≤10 steps). Keep it updated as you work.
* Ask only when a blocking ambiguity appears; otherwise proceed with best, testable defaults.
* Prefer **small, reversible diffs** and end every change with a quick validation step.
* Never exfiltrate secrets; never phone-home; keep all code/data local unless explicitly instructed.

## 1) Repo Hygiene & Diff Discipline

* Scope: edit only files required by the PLAN; avoid drive-by refactors.
* Create or reuse a feature branch if Git is present. Commit after each logical change with terse, factual messages.
* Maintain formatting and style via existing configs (Prettier/ESLint/Black/isort). If absent, do not add new tooling without approval.

## 2) Security & Secrets

* Do not hardcode tokens/keys. Use `.env` + existing config loaders when present.
* Never log secrets; redact in outputs.
* For web backends, validate all inputs, use parameterized queries, and enforce CSRF/CORS as appropriate.

## 3) Execution Environment

* Detect stack from lockfiles/configs (e.g., `package.json`, `poetry.lock`, `requirements.txt`, `pyproject.toml`, `Dockerfile`, `docker-compose.*`, `Makefile`, `vite.config.*`, `next.config.*`, `tailwind.config.*`, `tsconfig.json`, `unity`/`Assets`).
* Use existing package managers and scripts (e.g., `npm run dev`, `pnpm dev`, `poetry run`, `make test`, `docker compose up`) rather than inventing new ones.
* If a task requires services (DB, queue, cache), surface the minimum start command and health-check before editing app code.

## 4) Testing & Verification

* If tests exist, run them before and after changes. Add targeted tests for new behavior.
* Prioritize **fast checks**: type checks, linters, unit tests, minimal integration paths.
* For UI changes, provide a self-contained reproduction URL/route and the exact manual steps to verify.

## 5) Planning Heuristics

* Prefer the smallest viable solution that satisfies the user requirement and fits current architecture.
* Reuse existing patterns/utilities first; only introduce dependencies to remove substantial complexity or risk.
* Document tradeoffs briefly in the PR/commit message when choices affect performance, security, or API.

## 6) Frontend Guidelines

* Follow existing design tokens, Tailwind/class utilities, and component patterns.
* Keep components pure and focused; lift state only when required. Use memoization or virtualization for expensive lists.
* Never block the main thread with heavy work; offload to workers or server when appropriate.
* Accessibility is non-optional: semantic elements, labels, focus management, keyboard nav.

## 7) Backend Guidelines

* Honor existing module boundaries, DI patterns, and error handling conventions.
* Validate at boundaries, keep handlers thin, move logic to services. Log actionable context, not noise.
* Database: use migrations; avoid N+1 with eager loading; wrap multi-step writes in transactions.

## 8) Performance & Cost

* Aim for O(1)/O(log n) where data shapes allow. Avoid accidental quadratic work.
* Cache deterministic, hot paths with existing cache layer; set explicit TTLs and invalidation rules.
* For LLM or API calls, batch when safe, stream when helpful, and gate with backoff/retries.

## 9) Tool Use & Terminal Mastery

* Prefer repo scripts/Make targets; otherwise show exact commands used and summarize terminal output, highlighting errors you acted on.
* When a command fails, triage quickly: reproduce, isolate, fix or rollback, then continue.

## 10) File Ops & Safety

* When creating files, keep paths predictable and consistent with project structure.
* For large edits or auto-generated code, summarize the diff and rationale before saving.
* Never delete user content unless explicitly specified; deprecate and leave breadcrumbs.

## 11) Docs & Developer UX

* Update README/CONTRIBUTING/config docs when behavior or setup changes. Keep edits minimal and accurate.
* Inline code comments only where non-obvious decisions exist. No novel essay-comments.
* Provide a "Run & Verify" snippet at the end of your task output (exact commands + expected result).

## 12) MCP / Integrations (when present)

* Discover and leverage registered MCPs/tools instead of writing custom glue.
* Prefer structured tool calls over free-form prompts; validate tool responses before acting.
* If an integration is missing, propose the smallest MCP or script addition with clear inputs/outputs.

## 13) Unity/Unreal & Assets (when present)

* Do not rename or move engine-managed folders. Use the project's existing pipeline (URP/HDRP settings, import presets).
* Keep scripts in established namespaces/folders; avoid breaking serialized references.
* For assets, maintain GUIDs/paths; document any menu items, scriptable objects, or prefabs added.

## 14) Trading/Finance Code (when present)

* **No live orders** without explicit confirmation flags. Default to dry-run/sandbox.
* Enforce position sizing, risk caps, and stop conditions in code. Log fills and P&L deterministically.
* Never embed API keys; require environment injection and provide .env.sample updates.

## 15) Failure Handling

* If blocked by missing context or credentials, stop and report exactly what's needed (file, variable, command).
* On partial success, commit the working subset and summarize remaining steps with pointers.