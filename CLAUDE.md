# DHL Hosting Decision Advisor — Project Context

Read this before making changes. It covers why this exists, what must never
break, how to run/test/deploy it, and what's deliberately left undone.

## What this is

A portal around DHL's real `DHL_Hosting_Decision_Questionnaire_v1.0`
workbook — a governance instrument the Hosting Advisory Group uses to decide,
per application, whether a workload belongs on Public Cloud or Private
Cloud/On-Prem. The workbook (and a second workbook,
`Hosting_Checklist_Feedback_Consolidation_v6`, recording real pilot feedback
across 7 DHL ITS domains) is the actual source of truth for the domain
logic — not something invented for this app. If a scoring rule or piece of
copy seems arbitrary, it probably isn't; check the workbook's own "Scoring &
Governance Guide" and "Formula Audit" sheets before changing it.

**First step of a larger flow**: assess → get a Public/Private recommendation
→ hand off into IPP to actually provision infrastructure. The handoff today
is a deep-link to `IPP_BASE_URL` (a placeholder — see Known Gaps).

## Architecture

```
backend/   FastAPI + SQLAlchemy + SQLite + Alembic
frontend/  React + TypeScript + Vite, DHL red/yellow design tokens
docker-compose.yml   3 services: backend, frontend, mock-idp
helm/dhl-hosting-advisor/   OpenShift Helm chart (see OPENSHIFT.md)
```

No separate database service — SQLite lives on disk at `/data/dha.db`
(a Docker volume locally, a PVC on OpenShift). See **Key Invariants** below
for what that constrains.

Auth is OIDC end-to-end, provider-swappable via one env var
(`AUTH_PROVIDER=mock|azuread`), never hardcoded to a specific IdP:
- `app/auth/oidc.py` is the provider-agnostic client both branches use.
- `app/auth/mock_idp.py` is a tiny standalone FastAPI app (its own
  container) that plays the role of a real IdP for local dev/demo — a login
  page listing 5 fixed demo identities (one per role), issuing JWTs shaped
  like what Azure AD would actually send.
- JIT user provisioning (`app/auth/provisioning.py`) creates/updates the
  `UserAccount`+`UserRole` rows from OIDC claims on every login — shared by
  the real callback route and the seed script, so seeded demo users and
  real first-logins behave identically.

RBAC (`app/auth/rbac.py`): 4 roles (`admin`, `assessor`, `approver`,
`viewer`). A role grant with `domain_id=None` is global (sees/acts on every
business unit); a grant with a `domain_id` scopes it to just that one.
A user can hold the same role multiple times across different domains.

## The decision engine — the actual domain logic

`backend/app/engine/scoring.py` is a **pure, framework-free port** of the
workbook's rules. No DB or FastAPI imports in that file, on purpose — it's
the one thing in this codebase that must be exactly right, so it's isolated
and heavily tested (`backend/tests/test_scoring_engine.py`, 10 cases
including the real DGFF/FEC reference case and all 7 scenarios from the
workbook's own "Formula Audit" sheet). **Any change to the scoring rules
must keep those tests passing, or deliberately update them with a clear
reason** — they're the contract, not incidental coverage.

Rule order (`compute_result` in `scoring.py`), exactly as the workbook
specifies it:
1. **Completeness gate** — any unanswered question (of 6 knock-outs + 14
   scoring questions) → `"Pending"`, full stop, even if a knock-out is
   already a clear "Yes". Nothing else is evaluated until everything is
   answered.
2. **Knock-out evaluation** — any Private-direction knock-out = Yes sets a
   private flag; any Public-direction = Yes sets a public flag.
3. **Conflict** — both flags set → escalate, no scoring fallback.
4. **Knock-out precedence** — exactly one flag set → that recommendation
   wins outright, regardless of what the 14 scoring answers say.
5. **Symmetric scoring** — no knock-out: each scoring question is worth
   exactly 4 points, split by band (A=4/0 … E=0/4). Zero-sum, no per-question
   weights — that's intentional (see the workbook's own "Why equal weights"
   note), don't add weighting.
6. **Near-tie rule** — fit gap < 10 percentage points → "architecture review
   required", never a forced coin-flip.
7. **Confidence** — High: knock-out, or gap ≥30pp. Medium: 10–30pp. Low:
   near-tie or conflict.
8. **Robustness** — points gap > 8 (the max a single A→E swing is worth) ⇒
   no single changed answer could flip the result.
9. **Evidence gate** — flags `evidence_complete=false` if any Yes knock-out
   or any answered scoring question lacks an evidence reference.

`app/engine/apply.py` bridges the ORM to this pure function and upserts
`AssessmentResult`. **Result is always recomputed server-side from answers
on every read and write — never trust a client-supplied score.**

## Key invariants — don't break these

- **Questionnaire versioning is append-only.** Editing a question creates a
  *draft* `questionnaire_version`; publishing it only changes which version
  *new* assessments start from. Every `Assessment` keeps the
  `questionnaire_version_id` it was created with forever — an admin
  publishing v1.2 must never alter the stored questions/bands/result of an
  assessment scored against v1.0 or v1.1. If you ever find yourself writing
  code that mutates a *published* `QuestionnaireVersion`'s questions in
  place, stop — that's the one thing this whole data model exists to
  prevent.
- **SQLite is single-writer.** `backend/app/db/session.py` enables WAL mode
  so concurrent reads don't block on the one writer, but the backend is
  pinned to **1 replica** everywhere (`docker-compose.yml`,
  `helm/.../values.yaml` with a comment on `backend.replicas`). Don't raise
  that without first moving to a real DB — two pods writing the same SQLite
  file will corrupt it, not queue politely.
- **Enum values written to the DB may come back as plain strings, not enum
  instances**, if read from an object still pending in the same session
  (not yet round-tripped through a fresh `SELECT`). `apply.py` handles this
  deliberately (constructs the pure-engine enums from either representation
  instead of calling `.value`); this bit the seed script once already
  (`AttributeError: 'str' object has no attribute 'value'`) — don't
  "simplify" that back to `.value` calls.
- **OpenShift's restricted SCC overrides `USER` in both Dockerfiles** with
  an arbitrary UID that's always in group 0. Both images are built around
  "group 0, group-writable app dirs" (`chgrp -R 0 ... && chmod -R g=u ...`),
  not a fixed named user's ownership — and the frontend nginx listens on
  **8080**, not 80, because arbitrary non-root UIDs can't bind privileged
  ports. Don't quietly revert either while "simplifying" the Dockerfiles.
- **FastAPI route registration order matters for literal-vs-variable path
  conflicts.** `GET /questionnaires/draft` had to be moved before
  `GET /questionnaires/{version_id}` — Starlette matches routes in
  declaration order and `{version_id}` would otherwise swallow `"draft"` as
  a string before FastAPI's `int` validation rejects it with a 422. If you
  add a new static sub-path alongside an existing `{id}`-shaped route in the
  same router, declare the static one first.
- **A `RedirectResponse` from an endpoint called via `fetch()` (not a
  top-level browser navigation) breaks CORS** if the redirect target is a
  different origin with no CORS headers of its own — this is why
  `/auth/logout` returns plain JSON instead of redirecting (see the comment
  in `app/routers/auth.py`). `/auth/login` and `/auth/callback` ARE real
  top-level navigations (the browser follows the redirect itself), so
  `RedirectResponse` is correct there. Know which kind of call you're
  handling before picking one.

## Running it

```bash
cp .env.example .env
docker compose up --build
```
Frontend `:3000`, backend API docs `:8000/docs`, mock sign-in `:8100/login`.
Seeds automatically on first boot (7 domains, 5 demo identities one per
role, questionnaire v1.0, the real FEC reference case + a synthetic Public
Cloud example) — safe to re-run, no-ops once a questionnaire version exists.

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -v   # engine tests — no DB needed
```

Schema changes: edit `app/db/models/__init__.py`, then regenerate against a
live SQLite target (don't hand-write migrations against this model —
autogenerate and verify, as `alembic/versions/` already was once rewritten
after a Postgres→SQLite switch produced dialect-specific `server_default`
SQL that didn't apply to SQLite):
```bash
DATABASE_URL="sqlite:///$(pwd)/test_local.db" .venv/bin/python -m alembic revision --autogenerate -m "..."
DATABASE_URL="sqlite:///$(pwd)/test_local.db" .venv/bin/python -m alembic upgrade head   # verify it actually applies
rm test_local.db   # *.db is gitignored — never commit one
```

## Deploying

`helm/dhl-hosting-advisor/` targets OpenShift specifically (arbitrary-UID
images, `route.openshift.io/v1` Routes, pulls from the namespace's own slice
of the internal registry). Full walkthrough, including the image build-arg
ordering constraint and the `oc rollout restart` step a redeploy needs:
**[OPENSHIFT.md](OPENSHIFT.md)**.

## Conventions

- **Design tokens** (`frontend/src/theme/tokens.css`): a raw `--dhl-*` brand
  layer (red/yellow, used as accent only — headers, status emphasis, never
  general interactive color) and a semantic `--ds-*` layer components
  actually consume, switched via `[data-theme="dark"]`. If a future sibling
  DHL internal tool shares this pattern, match it rather than inventing a
  third convention.
- **Every answer-bearing UI element carries real governance text**, not
  generic placeholders — e.g. evidence fields say "doc ref, note, or
  estimate" because the source workbook's own feedback explicitly broadened
  what counts as evidence; don't tighten that back to something that implies
  a formal document is required.
- **Both rules the whole UI was built under**: nothing should make the user
  stop and think about what to do next (obvious next action, visible
  progress, errors prevented rather than just handled), and every word of
  UI copy beyond the questionnaire's own designated question text has to
  earn its place — cut it if it's not adding information the reader didn't
  already have.

## Known gaps — good places to pick up work

Roughly priority order, not obligation order:

1. **IPP handoff is a placeholder.** `IPP_BASE_URL` points at
   `localhost:4000`; nothing real is listening there yet. Once the actual
   IPP provisioning endpoint and its expected query params are known, update
   `app/routers/handoff.py` and the `ipp.baseUrl` Helm value.
2. **No audit-log UI.** Every publish, workflow transition, and draft edit
   is already written to the `audit_log` table (`app/audit.py`) — nothing
   in the frontend surfaces it yet. Natural fit as an Admin page.
3. **Azure AD is wired but untested against a real tenant** — the
   `oidc.py` azuread branch (JWKS fetch, RS256 verification) has never run
   against an actual Azure AD app registration. Budget time to debug claim
   shape mismatches (especially the `roles` claim, which needs app roles
   configured on the registration) the first time this is flipped on for
   real.
4. **No frontend automated tests.** Only the backend decision engine has a
   test suite. The frontend has been verified by hand (browser walkthroughs
   per role) but has zero `vitest`/Testing Library coverage.
5. **Evidence is text-only by design** (an earlier explicit decision, not an
   oversight) — no file upload. Revisit only if real usage shows text
   references aren't enough.
6. **Single-admin questionnaire publish** (also a deliberate choice over a
   four-eyes approval step) — revisit if the real governance process
   requires a second sign-off before a new version goes live.
7. **No pagination anywhere** (assessment lists, dashboards) — fine at pilot
   scale, will need it if usage grows past maybe a few hundred assessments.
8. **The workbook's "Information Owner Matrix"** (TCO→FinOps,
   Licensing→SAM/Vendor Mgmt, SLA→Service Owner, etc.) exists in the source
   feedback workbook but isn't surfaced anywhere in-app — could become a
   reference page or, further out, drive per-question "who should answer
   this" routing.
9. **CI only covers the backend.** `.github/workflows/backend-tests.yml` runs the engine
   test suite on push/PR; there's no equivalent for the frontend (see gap 4) or a build/lint
   check, and no CD — deploys are still the manual `oc`/`helm` steps in OPENSHIFT.md.

## Where things live

```
backend/app/engine/scoring.py        the decision rules (pure, framework-free)
backend/app/engine/apply.py          bridges ORM <-> the pure engine
backend/app/db/models/__init__.py    schema (SQLAlchemy ORM)
backend/app/auth/                    OIDC client, mock IdP, RBAC, JIT provisioning
backend/app/routers/                 one file per resource (assessments, workflow,
                                      questionnaires, dashboards, handoff, users, domains)
backend/app/seed/                    the transcribed questionnaire v1.0 + seed data
backend/tests/test_scoring_engine.py the engine's regression suite — run this after
                                      any scoring.py change
frontend/src/pages/assessor/AssessmentDetailPage.tsx   the questionnaire wizard
frontend/src/pages/admin/QuestionEditorPage.tsx        admin draft/publish UI
frontend/src/theme/                  design tokens + shared component CSS
helm/dhl-hosting-advisor/            OpenShift chart
OPENSHIFT.md                         deployment walkthrough
ARCHITECTURE.md                      diagrams (system context, containers, auth flow,
                                      workflow state machine, decision engine, data model)
.github/workflows/                   CI (backend engine tests on push/PR)
```
