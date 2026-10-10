from pathlib import Path

content = r'''# Swasthya Reader — Team Implementation Plan
## FastAPI + PostgreSQL + React-based Mobile App + AI Short-Term Memory

> **Purpose:** Turn the existing Swasthya Reader hackathon prototype into a team-built mobile application while preserving its lab-report extraction, deterministic reference-range checking, Nepali explanations/audio, and medical safety boundaries. Use coding agents for focused tasks, tests, reviews, and small meaningful Git commits.
>
> **Architecture:** React-based mobile client → FastAPI REST API → PostgreSQL. A vision model extracts structured report data; deterministic Python code validates and evaluates supported tests; an AI assistant may use short-term memory (STM) scoped to a conversation session.
>
> **Important:** Swasthya Reader is an informational decision-support/demo tool, not a diagnosis system. Do not tell users to start/stop treatment. Reference ranges vary by laboratory and patient context. Preserve uncertainty, show units and source/context, and recommend discussing results with a qualified clinician.

---

## 0. Team agreement: one product, clear ownership

Use these ownership labels throughout the plan. Replace the labels with teammates' names in the repository README once the team agrees.

| Role | Primary ownership | Must coordinate on |
|---|---|---|
| **Backend teammate A — API & auth/session** | FastAPI app structure, configuration, authentication if included, session lifecycle, API contracts, error responses | Shared Pydantic schemas, mobile API integration |
| **Backend teammate B — data & AI pipeline** | PostgreSQL schema/migrations, report persistence, extraction-provider adapter, deterministic checker integration, STM service and safety controls | API contracts, privacy, schema changes |
| **Mobile teammate — React-based app** | Mobile navigation/screens, upload/camera or file picker, API client, session UX, results, Nepali explanations/audio playback, loading/error states | OpenAPI contract, auth/session behavior, supported upload format |
| **Whole team / rotating reviewer** | Product scope, safety review, integration tests, demo, README, PR review | Every milestone and release |

**If one person is the only backend developer:** keep the same workstreams but do them sequentially. Do not have two coding agents edit the same files or database migrations at the same time.

### Ownership rules

- One person owns each file/module at a time.
- Agree on API contracts and database migrations before the mobile teammate integrates.
- Backend teammate A owns API naming and HTTP semantics; backend teammate B owns data integrity and AI pipeline behavior.
- Mobile work can proceed against mocked responses while backend endpoints are built.
- Every PR/commit should have one purpose, a test or verification step, and a reviewer.
- No teammate or agent should paste `.env` values, patient records, access tokens, or private report images into prompts, issues, screenshots, or logs.

---

## 1. Preserve the existing Swasthya Reader functionality

The current prototype is a Streamlit app plus a Python skill module. Keep the working behavior, but move responsibilities into testable backend services and mobile screens.

### Existing flow to preserve

1. User selects a synthetic sample report or uploads a JPG/PNG lab-report image.
2. A vision-capable model extracts patient/report metadata and test names, values, and units into structured data.
3. The backend validates the extracted structure before using it.
4. `skills/swasthyalabchecker/checker.py` compares supported tests against configured ranges from `reference_ranges.py`.
5. The UI shows extracted values, units, status (`High`, `Low`, `Normal`, `Unverified`), and cautious explanations.
6. Nepali explanations are shown and, when available, can be converted to speech and played.
7. Unknown tests, missing units, low-confidence extraction, or unsupported ranges remain unverified rather than guessed.

### Existing project files noted in the archive

```text
swastha-reader/
├── app.py
├── requirements.txt
├── generate_file.py
├── sample_sugar_high.png
├── sample_cbc_anemia.png
└── skills/
    └── swasthyalabchecker/
        ├── __init__.py
        ├── SKILL.md
        ├── checker.py
        └── reference_ranges.py
```

The new implementation may reorganize files, but first record the existing behavior and port it in small slices. Keep synthetic sample reports for automated tests and demos.

### Known cleanup items from the prototype

- The archive appeared to contain `.env` and `.venv/`. Do not commit them. Inspect secret files locally without exposing their contents; rotate any API key that may have been exposed.
- The old app imports `gTTS`, while its dependency list used `edge-tts`; choose one implementation and align imports/dependencies.
- `ollama` was imported but not listed in the old dependency file. Decide explicitly whether local Ollama support is in the MVP.
- Verify the selected Gemini model identifier and SDK response shape against the actual account/SDK. Hide provider-specific details behind an adapter.
- Existing reference ranges are a small demo set, not universal clinical facts. Unknown or ambiguous tests must stay unverified.

---

## 2. MVP scope and non-goals

### Required for the hackathon MVP

- [ ] React-based mobile app can create/reopen a conversation session.
- [ ] User can upload/select a lab report image.
- [ ] FastAPI accepts the image securely and returns a report/job identifier.
- [ ] Backend extracts structured data and validates it against a schema.
- [ ] Deterministic checker evaluates only explicitly supported tests.
- [ ] App shows original extracted values and units, configured range/context, status, and cautious Nepali-friendly explanation.
- [ ] A short-term-memory assistant can refer to recent turns within the same session without mixing different sessions or users.
- [ ] User can see loading, success, empty, partial, and error states.
- [ ] Nepali audio is offered only when generation succeeds; otherwise text remains available.
- [ ] Automated tests run without a paid AI API key for checker, validation, session isolation, and core API behavior.
- [ ] Medical disclaimer and privacy handling are visible.
- [ ] Setup and demo instructions are documented.

### Defer until core behavior is stable

- Complex multi-agent orchestration, long-term personalized memory, fine-tuning, public patient sharing, doctor diagnosis, treatment recommendations, complex analytics, and elaborate infrastructure.
- Avoid adding Redis/vector databases solely to label the project “AI.” PostgreSQL plus bounded session history is enough for a hackathon STM baseline. Add another store only after measuring a concrete need.
- Do not make the client call AI providers directly; API keys and clinical pipeline logic stay on the backend.

---

## 3. Recommended repository layout

Start by inspecting the repository and then introduce this structure incrementally; do not move everything in one huge refactor.

```text
swasthya-reader/
├── backend/
│   ├── pyproject.toml                 # or requirements.txt; choose one
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py                    # FastAPI app + router registration
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py            # only if authentication is implemented
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   ├── session.py
│   │   │   ├── message.py
│   │   │   └── report.py
│   │   ├── api/v1/
│   │   │   ├── health.py
│   │   │   ├── sessions.py
│   │   │   ├── messages.py
│   │   │   └── reports.py
│   │   ├── services/
│   │   │   ├── extraction.py
│   │   │   ├── lab_checker.py
│   │   │   ├── assistant.py
│   │   │   ├── short_term_memory.py
│   │   │   └── speech.py
│   │   └── providers/
│   │       ├── vision_base.py
│   │       └── vision_provider.py
│   └── tests/
│       ├── unit/
│       ├── api/
│       └── integration/
├── mobile/
│   ├── package.json
│   ├── src/
│   │   ├── api/
│   │   ├── navigation/
│   │   ├── screens/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── state/
│   │   └── types/
│   └── ...
├── shared-contracts/
│   └── api-examples.md                # temporary human-readable contract
├── samples/                           # synthetic reports only
├── .gitignore
└── README.md
```

**Mobile framework is intentionally left open:** the team said “another React-based mobile framework,” not React Native/Expo specifically. Before scaffolding, identify the chosen framework (for example, Ionic React with Capacitor, or another React-based mobile framework) and record the decision in `README.md`. Keep the API client and TypeScript data types framework-independent so the backend contract does not depend on that choice.

---

## 4. Architecture and data flow

```text
React-based mobile app
  ├── Session list / current conversation
  ├── Upload report image
  ├── Results + Nepali explanation + audio
  └── Chat messages for the current session
            │ HTTPS JSON + multipart upload
            ▼
FastAPI
  ├── request validation + authentication/ownership checks
  ├── report orchestration
  ├── vision provider adapter → structured extraction
  ├── schema validation
  ├── deterministic lab checker (existing skill logic)
  ├── STM service (recent messages scoped to one session)
  └── speech service
            │ SQLAlchemy/async database layer + migrations
            ▼
PostgreSQL
  ├── users (optional for MVP; recommended for real multi-user use)
  ├── chat_sessions
  ├── chat_messages
  ├── reports
  └── lab_results
```

### Design boundaries

- **Vision model:** reads the image and extracts data; it does not decide what is medically normal.
- **Validator:** rejects or flags malformed values and missing/ambiguous units.
- **Lab checker:** deterministic code compares supported tests against explicitly configured ranges.
- **Assistant:** explains already-validated findings in plain language; it cannot change the checker status, invent reference ranges, or diagnose.
- **STM:** supplies a bounded number of recent messages from one session. It is not a clinical record and must not silently merge sessions.
- **PostgreSQL:** stores session/report/message metadata and validated results. Avoid storing raw report images permanently by default; use temporary processing or explicit retention/consent.
- **Mobile app:** presents API results and state; it must not embed provider API keys or implement its own clinical classification.

---

## 5. API contracts — agree before parallel implementation

Prefix endpoints with `/api/v1`. Use JSON for normal requests and `multipart/form-data` for image uploads. Keep field names stable; generate OpenAPI docs from FastAPI and let the mobile teammate use those schemas as the source of truth.

### 5.1 Health check

`GET /api/v1/health`

**200 response**
```json
{
  "status": "ok",
  "database": "ok"
}
```

Do not return secrets, connection strings, or internal exception details. If the database is unavailable, return a controlled unhealthy status or appropriate service error.

### 5.2 Create a session

`POST /api/v1/sessions`

**Request**
```json
{
  "title": "Blood report discussion"
}
```

`title` is optional; server may generate a safe default.

**201 response**
```json
{
  "id": "uuid",
  "title": "Blood report discussion",
  "created_at": "2026-10-10T08:00:00Z",
  "updated_at": "2026-10-10T08:00:00Z"
}
```

### 5.3 List the current user's sessions

`GET /api/v1/sessions?limit=20&cursor=...`

**200 response**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Blood report discussion",
      "created_at": "2026-10-10T08:00:00Z",
      "updated_at": "2026-10-10T08:00:00Z"
    }
  ],
  "next_cursor": null
}
```

Every query must be scoped to the authenticated user if accounts are enabled. If the hackathon demo temporarily uses anonymous sessions, use an unguessable session token and clearly document the limitation; never assume a UUID alone is authorization.

### 5.4 Read session history

`GET /api/v1/sessions/{session_id}/messages?limit=50&before=...`

**200 response**
```json
{
  "session_id": "uuid",
  "items": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Can you explain these results?",
      "created_at": "2026-10-10T08:05:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "I can explain the extracted values, but this is not a diagnosis.",
      "created_at": "2026-10-10T08:05:02Z"
    }
  ],
  "next_cursor": null
}
```

Return only messages belonging to a session the requester is allowed to access.

### 5.5 Send a chat message with STM

`POST /api/v1/sessions/{session_id}/messages`

**Request**
```json
{
  "content": "Explain the high result in simple Nepali.",
  "language": "ne"
}
```

**201 response**
```json
{
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "Explain the high result in simple Nepali.",
    "created_at": "2026-10-10T08:06:00Z"
  },
  "assistant_message": {
    "id": "uuid",
    "role": "assistant",
    "content": "म रिपोर्टमा देखिएका मानहरू बुझाउन सक्छु। यो निदान होइन।",
    "created_at": "2026-10-10T08:06:02Z"
  },
  "session_id": "uuid",
  "memory": {
    "mode": "recent_messages",
    "messages_used": 6
  }
}
```

`memory` is optional diagnostic metadata. Never return hidden chain-of-thought, provider prompts, internal reasoning traces, or sensitive data unrelated to the session. Use a bounded recent-message window, not the full database history. If the provider fails, return a controlled error or a clearly marked fallback; do not fabricate an AI answer.

### 5.6 Upload and analyze a report

`POST /api/v1/sessions/{session_id}/reports`

**Request:** `multipart/form-data` with `file` (JPG/PNG; define max size, e.g. 10 MB) and optional `language=ne`.

**201 response** (synchronous MVP)
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "status": "completed",
  "extraction": {
    "patient_name": null,
    "test_date": null,
    "results": [
      {
        "test_name": "Fasting Blood Sugar",
        "value": 138.0,
        "unit": "mg/dL",
        "confidence": null
      }
    ]
  },
  "findings": [
    {
      "test_name": "Fasting Blood Sugar",
      "value": 138.0,
      "unit": "mg/dL",
      "status": "unverified",
      "reference_range": null,
      "explanation": "This result could not be safely classified with the configured range."
    }
  ],
  "disclaimer": "Informational only; not a diagnosis. Discuss results with a qualified clinician."
}
```

The values above illustrate shape only. Do not hardcode this example as a medical classification. Actual `status` must come from the deterministic checker. If processing is too slow, later change to `202 Accepted` plus a job-status endpoint; do not implement asynchronous jobs until the synchronous pipeline is tested.

### 5.7 List reports in a session

`GET /api/v1/sessions/{session_id}/reports`

Return report metadata and status, not raw image bytes. The response should include `id`, `status`, `created_at`, and safe summary metadata.

### 5.8 Speech generation (optional after text works)

`POST /api/v1/reports/{report_id}/audio`

**Request**
```json
{
  "language": "ne"
}
```

Return either a short-lived audio URL or an audio response according to the implementation decision. Do not store generated audio forever by default. The mobile app must show text even if audio fails.

### Shared HTTP behavior

- `400` malformed request; `401` unauthenticated if auth is enabled; `403` access denied; `404` unknown or inaccessible resource; `413` upload too large; `415` unsupported media type; `422` schema validation error; `429` rate limit; `502` upstream AI/TTS provider error; `503` required dependency unavailable.
- Use a consistent error body:
```json
{
  "error": {
    "code": "unsupported_file_type",
    "message": "Please upload a JPG or PNG image."
  }
}
```
- Do not leak stack traces, secrets, raw provider responses, or patient report contents in error messages.
- Include a request/correlation ID in logs and error metadata, but not raw image or report text.
- Document every endpoint in FastAPI OpenAPI docs; keep example requests in `shared-contracts/api-examples.md`.

---

## 6. PostgreSQL schema and data ownership

Use UUID primary keys, UTC timestamps (`timestamptz`), foreign keys, indexes, and migrations (Alembic is a reasonable default). Do not rely on manual production schema edits. Start with the smallest schema and add columns only when a feature requires them.

### 6.1 Suggested tables

#### `users` (recommended when more than one person can use the service)

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | generated server-side |
| `email` | CITEXT or normalized `varchar` UNIQUE | optional if using another login identifier |
| `password_hash` | text nullable | only if password auth is implemented; never store raw passwords |
| `created_at` | timestamptz | UTC |

For a short hackathon demo, anonymous sessions can be a temporary choice, but the backend must still enforce access with an unguessable token. Do not use a client-provided `user_id` as proof of identity.

#### `chat_sessions`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | session identifier |
| `user_id` | UUID FK nullable | nullable only for the explicitly designed anonymous mode |
| `anonymous_token_hash` | text nullable | store a hash, not the raw bearer token, if anonymous mode is used |
| `title` | varchar(160) | optional display title |
| `created_at` | timestamptz | UTC |
| `updated_at` | timestamptz | update on new message/report |
| `expires_at` | timestamptz nullable | optional expiry for anonymous/demo sessions |

Indexes: `(user_id, updated_at DESC)` and `expires_at` if cleanup uses it. Add a constraint requiring either an authenticated owner or an anonymous token hash according to the chosen mode.

#### `chat_messages`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | message ID |
| `session_id` | UUID FK → `chat_sessions.id` ON DELETE CASCADE | required |
| `role` | enum/check | only `user`, `assistant`, optionally `system` for trusted server-generated messages |
| `content` | text | length limit at API layer |
| `created_at` | timestamptz | UTC |
| `metadata` | JSONB nullable | minimal safe metadata only; no secrets or hidden reasoning |

Indexes: `(session_id, created_at DESC, id DESC)`. Use keyset pagination for history.

#### `reports`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | report ID |
| `session_id` | UUID FK → `chat_sessions.id` ON DELETE CASCADE | session ownership boundary |
| `status` | enum/check | `uploaded`, `processing`, `completed`, `failed`, `needs_review` |
| `original_filename` | varchar(255) nullable | sanitize; do not trust user path |
| `mime_type` | varchar(100) | allowlist JPG/PNG |
| `file_sha256` | char(64) nullable | optional duplicate/integrity aid; not authorization |
| `storage_key` | text nullable | only if external/private object storage is used |
| `extraction_json` | JSONB nullable | validated extraction only; restrict access |
| `error_code` | varchar(80) nullable | safe code, not raw provider error |
| `created_at` | timestamptz | UTC |
| `updated_at` | timestamptz | UTC |
| `retention_until` | timestamptz nullable | optional cleanup policy |

**Privacy default:** process the image in memory or use temporary private storage; delete it after processing unless the product explicitly requires persistence and the user has been informed. Do not store public image URLs.

#### `lab_results`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | result ID |
| `report_id` | UUID FK → `reports.id` ON DELETE CASCADE | required |
| `test_name_original` | text | exact extracted name |
| `test_code` | varchar(80) nullable | only a supported normalized key |
| `value_numeric` | numeric nullable | numeric result when parsed |
| `value_text` | text nullable | preserve a non-numeric value rather than coercing it |
| `unit` | varchar(80) nullable | extracted unit; never silently invent one |
| `reference_low` | numeric nullable | configured range used for this evaluation |
| `reference_high` | numeric nullable | configured range used for this evaluation |
| `reference_unit` | varchar(80) nullable | unit for the configured range |
| `status` | enum/check | `high`, `low`, `normal`, `unverified`, `needs_review` |
| `explanation` | text nullable | cautious, non-diagnostic text |
| `created_at` | timestamptz | UTC |

Indexes: `(report_id)`. Store the exact range/config version or source identifier used for the evaluation (for example `range_source` and `range_version`) before using results beyond a demo. If a value's unit is incompatible or unclear, mark it unverified.

### 6.2 Schema/migration rules

- Use one migration owner at a time; merge schema changes sequentially.
- Create the first migration for sessions/messages/reports/results, then add users/auth only when the auth decision is settled.
- Test both upgrade from an empty database and migration application to a clean local database.
- Use database constraints for referential integrity and application validation for richer error messages.
- Never use `DROP TABLE` or destructive migrations as a shortcut without explicit team review and a backup plan.
- Keep report data access scoped through the session's authorized owner. Add tests that prove one session cannot read another session's messages/reports.
- Store only what the product needs. Set a deletion/retention policy before storing actual health information.

---

## 7. Short-term memory (STM) session design

**Definition for this project:** STM is the AI assistant's bounded memory of recent conversation turns within one active chat session. It is not long-term memory, a global profile, or a source of medical truth.

### Initial implementation: PostgreSQL-backed recent-message window

1. Client creates or opens a session.
2. Client sends a message to that session.
3. API authenticates/authorizes access to the session.
4. Backend saves the user message.
5. STM service loads the latest **N messages** from that same session (start with a small configurable window such as 8–12 messages, then test token budget).
6. Sort loaded messages into chronological order before sending them to the assistant.
7. Include only trusted server instructions plus the recent conversation and the current validated report context the user is authorized to access.
8. Generate the response, apply output checks/safety framing, then save the assistant message.
9. Return the answer and optionally a safe count of messages used.
10. If the provider fails, do not save a fabricated assistant answer; return a controlled error/fallback.

### STM boundaries and safeguards

- **Session isolation:** never load messages from other sessions. Add an automated cross-session isolation test.
- **User isolation:** authorize every session/report request; do not trust a `session_id` supplied by the client alone.
- **Bounded memory:** cap both number of messages and total prompt/token budget. Truncate or summarize only with explicit tests and clear semantics.
- **No hidden chain-of-thought storage:** save visible user/assistant messages only. Do not persist provider reasoning traces.
- **No untrusted instruction execution:** messages and extracted report text are data, not trusted instructions. Prompt-injection text inside an uploaded report must not override backend policy.
- **Medical truth boundary:** STM may recall what was said earlier, but cannot upgrade `Unverified` to `Normal` or invent a reference range. The deterministic checker remains the only component assigning status.
- **Clear/delete:** provide a way to start a new session and, if feasible, delete a session and its related messages/reports. Explain what deletion does.
- **Privacy:** avoid logging message contents. Set retention rules, especially for health-related information. Do not send real patient data to third-party providers without the appropriate consent and policy review.
- **Concurrency:** if two messages are submitted to the same session at once, preserve ordering or return a conflict/retry response. For MVP, a per-session lock or database transaction strategy can be documented; do not assume concurrent messages arrive in order.
- **No STM dependency on Redis:** PostgreSQL is the source of truth for persisted session turns. Add Redis only if later needed for caching/locks and after designing failure behavior.

### Prompt composition (conceptual, not a prompt to blindly trust)

- Trusted server instruction: explain, do not diagnose; do not prescribe or advise treatment changes; respect the checker output; ask for clarification when extraction is uncertain.
- Current authorized report findings from backend.
- Recent visible messages from the same session, within budget.
- Current user message.

Never allow the model to change a finding's `status`, `reference_range`, unit, or source. Validate any structured assistant output before returning it.

---

## 8. Agent operating rules

Use one coding agent at a time for a task unless work is genuinely independent. Human teammates own architecture and accept all changes.

### Required workflow for every task

1. **Inspect:** read relevant files and report current behavior; do not edit yet.
2. **Plan:** propose the smallest change, affected files, and a verification command.
3. **Implement:** only the requested slice; avoid unrelated refactors.
4. **Test:** run the specified tests and report exact commands and actual outcomes.
5. **Review:** inspect `git diff --check`, `git diff`, and test output; explain trade-offs and remaining risks.
6. **Commit:** human reviews and commits one logical change.

### Global agent prompt

> You are helping our team build Swasthya Reader as a React-based mobile app backed by FastAPI and PostgreSQL. The existing prototype extracts lab results from report images, validates structured data, deterministically classifies only supported tests, explains findings in Nepali, and can generate speech. Preserve this behavior and all medical-safety requirements.
>
> Work on only the task I assign. First inspect the relevant files and propose a minimal plan; do not rewrite the repository. Respect teammate ownership and do not edit files owned by another workstream without coordination. Keep API contracts and migrations stable. Add focused tests, run them, and report actual results only. Never invent medical ranges, claim unverified data is normal, diagnose, or advise starting/stopping treatment. Never expose secrets or log report/message contents. Do not commit. Finish with a diff summary, tests run, limitations, and one next step.

### Commit discipline

- One commit = one understandable change.
- Prefer 1–5 files per commit where practical.
- Avoid mixing feature work, formatting, refactoring, and dependency upgrades.
- Before committing: `git status --short`, `git diff --check`, `git diff`, and relevant tests.
- Do not claim a test passed unless it was run.
- Agents should not commit or push unless the team explicitly changes this rule.
- If an agent produces a large diff, ask it to split the change into smaller reviewable pieces.

---

## 9. Incremental milestones, tests, and suggested commits

Follow in order. Each step should leave the repository in a runnable or clearly documented state. Commit messages are examples; adapt to the actual diff.

### Milestone 0 — Baseline, secrets, and team decisions

**Task 0.1 — Inventory the current app (no edits)**  
Owner: whole team / backend A coordinates.

- [ ] Trace upload → extraction → checker → display → Nepali audio.
- [ ] List imports, dependencies, external services, and known failures.
- [ ] Identify which sample reports are synthetic.
- [ ] Decide mobile framework and write it down; do not assume React Native/Expo.
- [ ] Decide synchronous analysis for MVP and whether accounts are required.

**Verify:** team walkthrough; record findings in `docs/current-behavior.md`.

Commit: `docs: record existing Swasthya Reader pipeline`

**Task 0.2 — Protect the repository**

- [ ] Add `.gitignore` for `.env`, `.env.*` except `.env.example`, `.venv/`, `venv/`, `node_modules/`, build outputs, `__pycache__/`, `.pytest_cache/`, `.DS_Store`, mobile secrets, local audio and uploaded reports.
- [ ] Add `backend/.env.example` with placeholder names only.
- [ ] Check whether any secrets have already been committed. Rotate exposed keys; removing a key from the latest commit does not remove it from Git history.
- [ ] Never include real patient reports in Git.

Verify:
```bash
git status --short
git check-ignore .env backend/.env .venv/ mobile/node_modules/
```

Commit: `chore: ignore secrets, uploads, and generated files`

**Task 0.3 — Fix the legacy dependency mismatch**  
Owner: backend B.

- [ ] Choose `gTTS` or `edge-tts`; align code and dependency list.
- [ ] Decide whether Ollama is supported now or deferred.
- [ ] Verify the vision provider SDK/model configuration.
- [ ] Create a clean virtual environment and install only declared dependencies.

Commit: `chore: align dependencies with current imports`

### Milestone 1 — Make the checker safe and testable before moving it

Owner: backend B.

**Task 1.1 — Add deterministic checker tests**

Test known high/low/normal values, exact boundaries, unknown test, unsupported unit, missing results, empty results, missing/non-numeric value, boolean-as-number, malformed JSON, non-object input, and malformed entries. Use synthetic values only.

Verify:
```bash
cd backend
python -m pytest tests/unit -q
```

Commit: `test: cover lab checker boundaries and invalid inputs`

**Task 1.2 — Validate extraction schema**

Define Pydantic models for report extraction and lab result values. Handle nullable metadata, unknown tests, invalid numeric values, and missing units without guessing. Keep raw extracted name separate from any normalized supported test key.

Commit: `feat: validate extracted lab report schema`

**Task 1.3 — Make test matching explicit**

Use a small explicit alias map. Avoid broad substring matching. Unknown or ambiguous test names stay `unverified`.

Commit: `fix: prevent ambiguous lab test matching`

**Task 1.4 — Document range provenance and disclaimers**

Document source, population/context, units, and version for each configured reference range. If provenance is not verified, label the values as demo ranges and do not imply universal applicability.

Commit: `docs: clarify demo ranges and medical limitations`

### Milestone 2 — Scaffold FastAPI and database access

Owner: backend A for app/config; backend B for DB/migrations. Coordinate before shared files.

**Task 2.1 — Minimal FastAPI app**

- Add app factory/entry point, configuration from environment, versioned router, and `GET /api/v1/health`.
- Do not add all endpoints at once.
- Add a stable error response shape and request ID middleware if feasible.

Verify:
```bash
cd backend
uvicorn app.main:app --reload
curl -i http://127.0.0.1:8000/api/v1/health
```

Commit: `feat: scaffold versioned FastAPI application`

**Task 2.2 — PostgreSQL connection and migration tool**

- Configure connection string via environment variable.
- Add a database health check that does not leak connection details.
- Add Alembic and one small first migration for `chat_sessions` and `chat_messages`.
- Choose SQLAlchemy (sync or async) and use it consistently; do not mix multiple ORM/data-access approaches without a reason.

Verify: migration upgrades an empty local database and a test can create/read a session.

Commit: `feat: configure PostgreSQL and initial migrations`

**Task 2.3 — Add report/result tables**

Add `reports` and `lab_results` with foreign keys, constraints, timestamps, status fields, and indexes. Use JSONB only for validated extraction payloads, not as a substitute for all relational data.

Verify: migration applies cleanly; foreign-key and cascade behavior are tested.

Commit: `feat: persist reports and validated lab results`

### Milestone 3 — Lock API contracts before mobile integration

Owner: backend A writes contracts; mobile teammate reviews.

**Task 3.1 — Publish endpoint examples**

Add request/response examples for health, create/list session, message history, send message, upload/analyze report, list reports, and optional audio. Include error bodies and upload limits.

Commit: `docs: define mobile API contracts`

**Task 3.2 — Add Pydantic request/response schemas**

Create schemas separately from ORM models. Ensure response schemas never serialize secret fields or internal provider responses.

Verify: OpenAPI endpoint docs show the intended shapes.

Commit: `feat: define typed API request and response schemas`

**Task 3.3 — API contract tests**

Test status codes, required fields, validation failures, consistent error format, and inaccessible session IDs.

Commit: `test: cover session and report API contracts`

### Milestone 4 — Session lifecycle and ownership

Owner: backend A.

**Task 4.1 — Create and list sessions**

Implement `POST /api/v1/sessions` and `GET /api/v1/sessions`. Decide and document authenticated vs anonymous session mode. Do not treat an arbitrary UUID as authorization.

Tests:
- session can be created and listed;
- limit/cursor inputs are validated;
- one user/token cannot list another user's sessions.

Commit: `feat: create and list authorized chat sessions`

**Task 4.2 — Read session messages**

Implement paginated `GET /api/v1/sessions/{session_id}/messages`.

Tests:
- chronological order is stable;
- pagination has no duplicates/gaps for the test dataset;
- inaccessible session cannot be read.

Commit: `feat: retrieve paginated session history`

**Task 4.3 — Delete session (if time permits)**

Delete a session and cascade its messages/reports/results according to the documented retention policy. Verify deletion behavior with tests before enabling it in the UI.

Commit: `feat: delete a session and its stored history`

### Milestone 5 — Port extraction and deterministic analysis to the backend

Owner: backend B.

**Task 5.1 — Extract a provider interface**

Wrap the current vision SDK behind a small function/interface that accepts an image and returns an extraction candidate. Keep provider config in environment variables; never expose provider keys to mobile.

Commit: `refactor: isolate vision extraction provider`

**Task 5.2 — Parse and validate model output**

Validate schema before passing data to the checker. Treat malformed/partial output as a controlled failure or `needs_review`, not a successful result.

Tests must use a fake provider response and require no external API key.

Commit: `feat: validate vision extraction responses`

**Task 5.3 — Expose upload/analyze endpoint**

Implement multipart upload with file type/size validation, safe temporary handling, controlled errors, and session ownership check. Run extraction → validation → deterministic checker → persistence. Do not make an AI-generated status authoritative.

Tests:
- reject unsupported file type and oversized upload;
- accept a valid synthetic sample;
- malformed provider output does not crash the endpoint;
- unsupported test returns `unverified`;
- session access is enforced;
- provider failure returns controlled error.

Commit: `feat: analyze uploaded lab report images`

**Task 5.4 — Add report history endpoint**

Implement `GET /api/v1/sessions/{session_id}/reports`, returning safe metadata and findings. Do not return raw image bytes or storage secrets.

Commit: `feat: list reports for an authorized session`

### Milestone 6 — Short-term memory and assistant behavior

Owner: backend B implements STM service; backend A owns message endpoint integration. Pair-review prompt/safety behavior.

**Task 6.1 — Implement recent-message retrieval**

Create a service that retrieves the last configurable N messages for one authorized session and reorders them chronologically. Add a token/character budget. Avoid any provider call at this stage.

Tests:
- only same-session messages are returned;
- messages are chronological;
- limit is respected;
- empty session works;
- user A cannot load user B's history.

Commit: `feat: load bounded recent messages for session memory`

**Task 6.2 — Build the assistant provider boundary**

Separate prompt construction from provider call. Provide a fake assistant in tests. The assistant may explain validated findings but must not reclassify them or produce treatment instructions.

Commit: `refactor: isolate assistant generation provider`

**Task 6.3 — Send message endpoint**

Implement `POST /api/v1/sessions/{session_id}/messages`: validate input, authorize session, persist user message, load STM, include only authorized report context, generate response, apply basic output safeguards, persist assistant response, and return both messages.

Tests:
- a follow-up can refer to a prior turn in the same session;
- separate sessions do not share history;
- provider error produces a controlled response and no fake success;
- messages are not duplicated on retries if idempotency is supported;
- simultaneous messages have a documented ordering strategy.

Commit: `feat: add session-aware assistant messaging`

**Task 6.4 — Medical safety tests for assistant context**

Use mocked provider output and synthetic reports to verify:
- unknown test remains unverified;
- assistant cannot overwrite checker status or range;
- no diagnosis or start/stop medication advice is presented;
- uncertainty/disclaimer remains visible;
- report text that looks like an instruction is treated as untrusted input.

Commit: `test: enforce assistant session and medical safety boundaries`

### Milestone 7 — React-based mobile app, built against the contract

Owner: mobile teammate. Framework selection is a team decision; keep network/data types independent of the framework.

**Task 7.1 — Scaffold and navigation**

- Create app shell and navigation: Session list, Session chat, Upload report, Report results/settings.
- Add environment-based API base URL. On a physical device, `localhost` points to the device, not the developer's laptop; document the correct development host.
- Add a single typed API client rather than calling `fetch` from every screen.

Commit: `feat: scaffold mobile app navigation`

**Task 7.2 — Create/reopen sessions**

Implement session list/create and empty/loading/error states. Store only the minimum local session identifier/token required by the chosen auth design, using secure platform storage for credentials/tokens when available.

Commit: `feat: connect mobile session lifecycle to API`

**Task 7.3 — Chat UI and STM experience**

Implement message list, composer, pending state, retry, and history loading. The client should send the current session ID; the backend decides which messages are valid STM. Do not implement clinical interpretation in mobile code.

Commit: `feat: add session chat interface`

**Task 7.4 — Upload report**

Use the chosen framework's file picker/camera support. Validate size/type on client for UX, but always repeat validation on the backend. Show progress, preview, retry/error state, and success.

Commit: `feat: upload report images from mobile`

**Task 7.5 — Display report results safely**

Show extracted test name, exact value/unit, configured reference range and source when available, status, and cautious explanation. Distinguish `Unverified` and `Needs review` visually. Keep disclaimer accessible. Do not use color alone to communicate status.

Commit: `feat: display validated lab report findings`

**Task 7.6 — Nepali explanation and audio**

Display Nepali text and add audio playback only after text/results are stable. If TTS fails or the device is offline, keep the text available and show a helpful message.

Commit: `feat: add Nepali explanation audio playback`

### Milestone 8 — Integration, hardening, and demo

Shared ownership; assign one integration lead.

**Task 8.1 — Local end-to-end smoke test**

Test from the actual mobile device/emulator against local FastAPI + PostgreSQL:
1. create session;
2. send message;
3. upload synthetic report;
4. verify extraction and deterministic findings;
5. ask a follow-up question that uses only that session's recent turns;
6. reopen session and read history;
7. play audio or verify graceful fallback;
8. confirm a second session cannot access the first session's data.

Commit: `test: add end-to-end Swasthya Reader smoke coverage`

**Task 8.2 — Security and privacy pass**

- [ ] Validate MIME type and file signature where practical; do not trust extension alone.
- [ ] Limit upload bytes, request size, message length, and rate of expensive provider calls.
- [ ] Keep secrets server-side and use environment configuration.
- [ ] Avoid raw report/message logging.
- [ ] Ensure all database access is parameterized/ORM-safe.
- [ ] Verify session ownership for every nested endpoint.
- [ ] Add retention/deletion behavior and document it.
- [ ] Use HTTPS for deployed builds; restrict CORS to required origins.
- [ ] Review third-party AI/TTS data handling before sending real health information.

Commit: `fix: harden upload and session access controls`

**Task 8.3 — Final documentation and demo script**

Document setup, environment variables (names only), migrations, test commands, mobile API URL configuration, framework choice, supported tests/ranges, known limitations, and demo steps. Use synthetic reports only.

Commit: `docs: document setup, safety, and hackathon demo`

---

## 10. Test strategy and test matrix

Use multiple layers. Most tests should not require network access or a paid model key.

| Layer | What to test | External AI required? |
|---|---|---|
| Unit: checker | boundaries, aliases, unknown tests, unit mismatch, invalid values | No |
| Unit: extraction schema | valid/invalid JSON, missing fields, wrong types | No |
| Unit: STM | same-session retrieval, ordering, limits, empty history | No |
| Unit: prompt/context builder | only authorized context included, bounded history | No |
| API: sessions | create/list/history/delete, validation, access control | No |
| API: reports | MIME/size validation, fake provider, failure handling | No |
| API: messages | fake assistant, persistence, errors, session isolation | No |
| Database integration | migrations, FK behavior, transactions, cleanup | Local PostgreSQL |
| Mobile | loading/error/success/empty states, session navigation, upload validation | Mock API for most tests |
| End-to-end | complete synthetic report workflow | Real model optional; use fake provider in CI |

### Minimum regression checklist after each relevant change

- [ ] Checker unit tests pass.
- [ ] Extraction validation tests pass.
- [ ] Session isolation tests pass.
- [ ] API contract tests pass.
- [ ] `git diff --check` passes.
- [ ] Mobile typecheck/lint/tests pass when mobile files change.
- [ ] No `.env`, API keys, private report images, or generated audio were added to Git.

---

## 11. Small-commit Git workflow

Start with a clean branch and make commits in this order where possible:

```bash
git status --short
git switch -c feat/api-foundation
# implement one small task
git diff --check
git diff
# run the task's tests
git add <specific-files>
git commit -m "feat: scaffold versioned FastAPI application"
```

Do not use `git add .` blindly when secrets, sample uploads, or generated files may exist. Prefer specific file paths.

### Example commit sequence

1. `docs: record existing Swasthya Reader pipeline`
2. `chore: ignore secrets, uploads, and generated files`
3. `chore: align dependencies with current imports`
4. `test: cover lab checker boundaries and invalid inputs`
5. `feat: validate extracted lab report schema`
6. `feat: scaffold versioned FastAPI application`
7. `feat: configure PostgreSQL and initial migrations`
8. `feat: persist reports and validated lab results`
9. `docs: define mobile API contracts`
10. `test: cover session and report API contracts`
11. `feat: create and list authorized chat sessions`
12. `feat: retrieve paginated session history`
13. `refactor: isolate vision extraction provider`
14. `feat: analyze uploaded lab report images`
15. `feat: load bounded recent messages for session memory`
16. `feat: add session-aware assistant messaging`
17. `feat: scaffold mobile app navigation`
18. `feat: upload report images from mobile`
19. `feat: display validated lab report findings`
20. `test: add end-to-end Swasthya Reader smoke coverage`
21. `docs: document setup, safety, and hackathon demo`

A task may require more than one commit; split it if the diff stops being easy to explain. Do not make commits merely to hit a number.

---

## 12. Coordination cadence

At the start of each work session, share:

- **Task:** one sentence describing the current change.
- **Owner:** one teammate.
- **Contract impact:** endpoint/schema/table changes or none.
- **Files likely to change:** short list.
- **Acceptance test:** exact command or manual steps.
- **Commit message:** one proposed message.

Before merging a PR, the owner provides:

- Summary of the behavior changed.
- Exact tests run and results.
- Screenshot or short recording for mobile UI changes, using synthetic data.
- Migration notes if schema changed.
- Any known limitation or follow-up.

### Parallel work that is safe

- Mobile teammate builds navigation and screens against mocked API data while backend builds endpoints.
- Backend B adds checker/schema unit tests while backend A scaffolds health/session endpoints, provided they do not edit the same files.
- One reviewer audits safety/privacy while another writes API examples.

### Parallel work to avoid

- Two people editing the same Alembic migration or ORM model simultaneously.
- Mobile and backend independently inventing field names.
- Two agents refactoring the same service.
- Integrating an AI assistant before session authorization and checker behavior are tested.

---

## 13. Definition of done

A feature is not done merely because the screen renders or the API returns `200`.

- [ ] The task has one clear behavior and a small diff.
- [ ] Input is validated and errors are predictable.
- [ ] Tests cover the success path and at least one failure/edge case.
- [ ] Session and user ownership are enforced.
- [ ] The mobile UI handles loading, empty, failure, and retry states where relevant.
- [ ] Medical statuses come from deterministic checker logic, not free-form model output.
- [ ] Unknown/ambiguous tests remain unverified.
- [ ] No secrets or real patient data are committed or logged.
- [ ] The owner can explain the code and the trade-offs.
- [ ] Commit message accurately describes the change.

---

## 14. Demo story

Use only synthetic reports. Suggested sequence:

1. Open the app and create a new session.
2. Upload one sample report.
3. Show extraction output and point out that values and units are retained.
4. Show deterministic status and clearly identify any unsupported result as `Unverified`.
5. Ask a follow-up in the same session: “Explain this in simple Nepali.”
6. Show that the assistant uses recent session context but does not replace the checker or diagnose.
7. Play Nepali audio, or demonstrate the graceful fallback if TTS is unavailable.
8. Start a separate session and demonstrate that the previous session's messages are not present.
9. End with the limitation: the tool supports understanding a report; a qualified clinician interprets results in personal context.

---

## 15. First task to start now

Do not ask an agent to build the entire app. Start with **Task 0.1: inventory the current project without editing**. Then agree on the mobile framework and authentication/anonymous-session approach. Once the API contract and session ownership decision are written down, proceed to repository hygiene and checker tests.

**Recommended first agent request:**

> Inspect the current Swasthya Reader repository without editing files. Summarize the existing upload → extraction → checker → Nepali explanation/audio pipeline, list dependencies and known mismatches, identify files that must be preserved, and propose the smallest next task. Do not expose `.env` values or private report contents. Do not implement the mobile app yet.
'''

path = Path("/mnt/data/Swasthya_Reader_Team_Implementation_Plan.md")
path.write_text(content, encoding="utf-8")
print(f"Created {path} ({len(content.splitlines())} lines, {path.stat().st_size:,} bytes)")
