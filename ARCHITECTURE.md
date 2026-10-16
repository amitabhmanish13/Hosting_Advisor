# Architecture

Diagrams render natively on GitHub (Mermaid) — no external tool needed to view or edit them.
For the narrative behind these decisions (why SQLite, why OIDC-pluggable, what must not
break), see [CLAUDE.md](CLAUDE.md).

## 1. System context

Who and what talks to this system.

```mermaid
flowchart LR
    assessor["Assessor<br/>(domain-scoped)"]
    approver["Approver<br/>(Hosting Advisory Group)"]
    admin["Admin"]
    viewer["Viewer<br/>(Management Board)"]

    subgraph DHA["DHL Hosting Decision Advisor"]
        app["Portal"]
    end

    idp["Identity Provider<br/>(mock locally, Azure AD in prod)"]
    ipp["IPP<br/>(infrastructure provisioning)"]

    assessor -- "answer questionnaire,<br/>submit" --> app
    approver -- "endorse, record<br/>Board decision" --> app
    admin -- "edit/publish questions,<br/>manage users & domains" --> app
    viewer -- "read dashboards" --> app

    app <-- "OIDC login" --> idp
    app -- "deep-link handoff<br/>(app, target, assessmentId)" --> ipp
```

## 2. Containers

Three images, no external database service — SQLite lives on a volume/PVC next to the
backend.

```mermaid
flowchart TB
    browser(["Browser"])

    subgraph runtime["docker compose / OpenShift namespace"]
        frontend["frontend<br/>nginx + React SPA<br/>:8080 (:3000 on compose)"]
        backend["backend<br/>FastAPI<br/>:8000"]
        mockidp["mock-idp<br/>FastAPI (same image as backend,<br/>different command)<br/>:8100"]
        data[("SQLite<br/>/data/dha.db<br/>(volume / PVC)")]
    end

    ipp_ext["IPP"]

    browser -- "static assets" --> frontend
    browser -- "REST API<br/>(direct, cross-origin)" --> backend
    browser -- "OIDC login page<br/>(AUTH_PROVIDER=mock)" --> mockidp
    backend -- "token exchange<br/>(server-to-server)" --> mockidp
    backend --- data
    browser -. "Proceed in IPP →<br/>deep-link" .-> ipp_ext
```

On OpenShift each box above is a `Deployment` + `Service` + edge-TLS `Route`
(`helm/dhl-hosting-advisor/`); on `docker compose` they're the three services in
`docker-compose.yml`. The backend is pinned to **1 replica** everywhere — SQLite is
single-writer (see CLAUDE.md § Key Invariants).

## 3. Auth flow (OIDC, provider-agnostic)

Same sequence whether `AUTH_PROVIDER` is `mock` or `azuread` — only which issuer is contacted
changes (`app/auth/oidc.py` branches once, no other code cares).

```mermaid
sequenceDiagram
    actor U as Browser
    participant FE as Frontend
    participant BE as Backend
    participant IDP as Identity Provider

    U->>FE: Click "Sign in"
    FE->>BE: GET /auth/login
    BE-->>U: 302 → IdP authorize URL (+ state cookie)
    U->>IDP: GET /login (or /oauth2/v2.0/authorize)
    IDP-->>U: 302 → /auth/callback?code=...&state=...
    U->>BE: GET /auth/callback
    BE->>BE: verify state cookie
    BE->>IDP: POST /token (server-to-server)
    IDP-->>BE: id_token (JWT: sub, email, name, roles, domain)
    BE->>BE: JIT-provision UserAccount + UserRole<br/>(app/auth/provisioning.py)
    BE-->>U: Set-Cookie (session) + 302 → frontend
    U->>FE: GET /  (now authenticated)
```

`/auth/logout` deliberately returns plain JSON, not a redirect — see the CORS note in
CLAUDE.md if you're touching that route.

## 4. Assessment workflow (state machine)

```mermaid
stateDiagram-v2
    [*] --> Draft: Assessor creates assessment
    Draft --> Submitted: Assessor submits<br/>(only when all 20 answers complete)
    Submitted --> Endorsed: Approver endorses<br/>(Hosting Advisory Group)
    Endorsed --> Decided: Approver records<br/>Board decision
    Decided --> [*]

    note right of Draft
        Only the Assessor (their domain)
        or an Admin can edit answers here.
    end note
    note right of Decided
        Locked. If the recommendation is a
        clear Private/Public call, the
        IPP handoff link appears.
    end note
```

Every transition is written to `workflow_event` (actor, timestamp, notes) — the audit trail
shown on each assessment's detail page.

## 5. Decision engine

The actual rule order in `backend/app/engine/scoring.py::compute_result` — a direct port of
the source workbook's own decision rules, not something designed from scratch. See CLAUDE.md
for why each step is ordered the way it is.

```mermaid
flowchart TD
    start(["20 answers submitted"]) --> complete{"All 6 knock-outs +<br/>14 scoring answered?"}
    complete -- No --> pending["Pending"]
    complete -- Yes --> knockout{"Any knock-out = Yes?"}

    knockout -- "Private + Public both Yes" --> conflict["Conflict —<br/>escalate to Hosting<br/>Advisory Group"]
    knockout -- "Private only" --> privateKO["Private Cloud / On-Prem<br/>(High confidence)"]
    knockout -- "Public only" --> publicKO["Public Cloud<br/>(High confidence)"]
    knockout -- "None" --> score["Sum 14 scoring answers<br/>(band A–E → 4/0 … 0/4 points,<br/>zero-sum, no weighting)"]

    score --> gap{"Fit gap ≥ 10pp?"}
    gap -- No --> neartie["Near-tie —<br/>architecture review required<br/>(Low confidence)"]
    gap -- Yes --> winner["Higher-fit side wins<br/>(Medium: 10–30pp, High: ≥30pp)"]

    winner --> robust{"Points gap > 8?"}
    robust -- Yes --> robustYes["Robust:<br/>no single answer<br/>could flip this"]
    robust -- No --> robustNo["Fragile:<br/>one answer could<br/>flip this"]
```

Every answered question (knock-out Yes, or any scored band) is also checked for a
non-empty evidence reference — `evidence_complete=false` flags it on the result without
changing the recommendation itself.

## 6. Data model (versioning invariant)

The one relationship that makes "admin edits a question" safe: an `Assessment` points at the
exact `QuestionnaireVersion` it was scored against, forever.

```mermaid
erDiagram
    QuestionnaireVersion ||--o{ KnockoutQuestion : contains
    QuestionnaireVersion ||--o{ ScoringQuestion : contains
    QuestionnaireVersion ||--o{ Assessment : "scored against (frozen FK)"
    Assessment ||--o{ KnockoutAnswer : has
    Assessment ||--o{ ScoringAnswer : has
    Assessment ||--|| AssessmentResult : "computed into"
    Assessment ||--o{ WorkflowEvent : "audit trail"
    Domain ||--o{ Assessment : scopes
    UserAccount ||--o{ UserRole : "role grants (role + optional domain)"

    QuestionnaireVersion {
        string version_label
        string status "draft | published"
        string changelog
    }
    Assessment {
        string status "draft|submitted|endorsed|decided"
        int questionnaire_version_id "never changes after creation"
    }
```

Publishing a new version never touches rows on an existing `QuestionnaireVersion` — it
inserts a new one and flips which version *new* assessments start from. See CLAUDE.md §
Key Invariants before changing anything here.
