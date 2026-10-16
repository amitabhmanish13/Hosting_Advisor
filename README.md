# DHL Hosting Decision Advisor

A containerized portal around DHL's `DHL_Hosting_Decision_Questionnaire_v1.0`: assess an
application against 6 knock-out questions and 14 evidence-banded scoring questions, get an
unbiased Public Cloud / Private Cloud recommendation with confidence and robustness, run it
through a Draft → Submitted → Endorsed → Decided governance workflow, and hand off a decided
assessment into IPP to provision infrastructure.

## Run it

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Mock sign-in page (local dev identity provider): http://localhost:8100/login

On first boot the backend seeds: the 7 ITS domains, 5 demo identities (one per role), the
published questionnaire v1.0, and two example assessments — the real DGFF/FEC reference case
(73% Private, High confidence, Robust) and a synthetic greenfield Public Cloud example.

Sign in as any of the demo identities shown on the mock sign-in page to explore each role:
Admin, Assessor (Digital Solutions or DGFF/FEC), Approver (Hosting Advisory Group), Viewer
(Management Board).

## Architecture

- **backend/** — FastAPI + SQLite. `app/engine/scoring.py` is a framework-free, unit-tested
  port of the workbook's decision rules (knock-out precedence → conflict → near-tie →
  confidence → robustness). `app/engine/scoring_engine` tests include the exact 7 scenarios
  from the workbook's own "Formula Audit" sheet plus the real FEC reference case.
- **frontend/** — React + TypeScript, DHL red/yellow design tokens, role-based navigation
  (Assessor wizard, Approver queues, Admin question editor + version history, Dashboards).
- Auth is OIDC-pluggable: `AUTH_PROVIDER=mock` runs a local identity provider for dev
  (`app/auth/mock_idp.py`); switching to `AUTH_PROVIDER=azuread` with real tenant/client
  credentials requires no code changes.
- **Versioning invariant**: editing questions creates a draft `questionnaire_version`; publishing
  it only changes which version *new* assessments use. Every assessment keeps the
  `questionnaire_version_id` it was created with forever, so admin edits can never alter an
  already-completed assessment's questions or score.

## Deploying to OpenShift

A Helm chart lives at `helm/dhl-hosting-advisor/`. Full build-and-install walkthrough: [OPENSHIFT.md](OPENSHIFT.md).

## Development

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -v
```

## IPP hand-off

Once an assessment is `Decided` with a clear (non-conflict, non-near-tie) recommendation, the
UI exposes `GET /assessments/{id}/handoff`, which returns a deep-link into IPP
(`{IPP_BASE_URL}/provision/new?app=...&target=private|public&assessmentId=...`) so the workload
lands directly in IPP's provisioning flow with context prefilled.
