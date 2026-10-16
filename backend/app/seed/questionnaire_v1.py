"""Transcription of DHL_Hosting_Decision_Questionnaire_v1.0 — the single source of
truth for the initial questionnaire_version row. Used by the seed script and
referenced by engine tests for realistic fixtures.
"""

KNOCKOUTS = [
    dict(
        code="KO1",
        direction="private",
        dimension="Legal & sovereignty mandate",
        question_text=(
            "Does a binding law, regulation or customer contract require this workload to run on "
            "DHL-controlled physical infrastructure, in a named location, or operated exclusively by "
            "DHL-vetted personnel?"
        ),
        evidence_hint="Contract clause, regulator citation or legal register entry (document ID)",
        dhl_ref="G7",
    ),
    dict(
        code="KO2",
        direction="private",
        dimension="Contractual hosting SLA",
        question_text=(
            "Has DHL contractually committed to an end-to-end hosting-level resolution SLA that a "
            "public cloud provider's published service terms verifiably cannot meet?"
        ),
        evidence_hint="Signed customer SLA + documented gap analysis against provider service terms",
        dhl_ref="G2",
    ),
    dict(
        code="KO3",
        direction="private",
        dimension="Non-portable infrastructure",
        question_text=(
            "Does the workload require physical components that no approved public cloud can provide "
            "— dedicated appliances, hardware dongles, or a stack the vendor does not support in public "
            "cloud?"
        ),
        evidence_hint="Vendor compatibility/support statement + hardware inventory",
        dhl_ref="G-ADD-F6",
    ),
    dict(
        code="KO4",
        direction="public",
        dimension="Platform-exclusive capability",
        question_text=(
            "Does the workload depend on a capability available only as a public cloud service, with "
            "an approved gap analysis showing no feasible private build within the required time and "
            "budget?"
        ),
        evidence_hint="Architecture-approved service-catalog gap analysis incl. build cost/time estimate",
        dhl_ref="G3",
    ),
    dict(
        code="KO5",
        direction="public",
        dimension="Certified government / sovereign cloud",
        question_text=(
            "Does a law, regulation or customer contract specifically require a certified public cloud "
            "environment (e.g. FedRAMP / DoD IL authorization, sovereign cloud region)?"
        ),
        evidence_hint="Contract or authorization citation naming the required certification",
        dhl_ref="G-NEW-B3",
    ),
    dict(
        code="KO6",
        direction="public",
        dimension="Capacity beyond private limits",
        question_text=(
            "Does the signed demand forecast exceed what DHL private capacity can physically deliver in "
            "the required timeframe (e.g. peak demand above approved data-centre power/space/compute "
            "expansion limits)?"
        ),
        evidence_hint="Capacity management statement + demand forecast signed by infrastructure owner",
        dhl_ref="G4",
    ),
]

SCORING = [
    dict(
        code="Q1",
        dimension="Elasticity & demand variance",
        question_text=(
            "What is the measured variance between baseline and peak demand over the last "
            "representative 90 days (or the approved demand model for new builds)?"
        ),
        evidence_hint="90-day CPU/memory/transaction telemetry, or approved demand model",
        band_a_text="< 10% variance — flat, continuous demand",
        band_b_text="10–30% variance, predictable pattern",
        band_c_text="30–50% variance with predictable peaks",
        band_d_text="50–100% variance, or peaks lasting < 25% of monthly runtime",
        band_e_text="> 100% variance or unpredictable bursts",
        dhl_ref="G4",
    ),
    dict(
        code="Q2",
        dimension="Utilization & lifespan",
        question_text=(
            "What sustained average utilization and remaining committed lifespan does capacity "
            "planning show for this workload?"
        ),
        evidence_hint="12-month utilization telemetry + approved application roadmap / decommission plan",
        band_a_text="≥ 60% sustained utilization and ≥ 36 months committed lifespan",
        band_b_text="40–60% utilization and ≥ 24 months lifespan",
        band_c_text="25–40% utilization, or lifespan not yet committed",
        band_d_text="10–25% utilization, or decommission planned < 24 months",
        band_e_text="< 10% average utilization, or short-lived / experimental workload",
        dhl_ref="G9",
    ),
    dict(
        code="Q3",
        dimension="Latency to immovable systems",
        question_text=(
            "What sustained p95 round-trip latency is required between the workload and dependent "
            "systems/data that cannot move?"
        ),
        evidence_hint="Measured p95/p99 latency requirement + dependency map + traffic flows",
        band_a_text="< 2 ms — same-site synchronous dependency",
        band_b_text="2–10 ms sustained to fixed on-prem systems",
        band_c_text="10–30 ms, achievable over hybrid connectivity",
        band_d_text="30–80 ms tolerable",
        band_e_text="> 80 ms tolerable, or no immovable dependency exists",
        dhl_ref="G-ADD-F5",
    ),
    dict(
        code="Q4",
        dimension="Data gravity & egress volume",
        question_text=(
            "How much data must move daily between this workload and systems that must remain "
            "on-premises?"
        ),
        evidence_hint="Network telemetry / data-flow inventory + egress cost model",
        band_a_text="> 5 TB/day sustained exchange with fixed on-prem systems",
        band_b_text="1–5 TB/day",
        band_c_text="100 GB–1 TB/day, or batching can optimize flows",
        band_d_text="10–100 GB/day",
        band_e_text="< 10 GB/day or no on-prem data exchange",
        dhl_ref="G-ADD-F5",
    ),
    dict(
        code="Q5",
        dimension="3-year like-for-like TCO",
        question_text=(
            "What does the approved 3-year TCO model show for equivalent availability, security, "
            "support and recovery (incl. licences, labour, network, egress, DR)?"
        ),
        evidence_hint="Approved TCO model built per FinOps method (all cost drivers included)",
        band_a_text="Private ≥ 15% lower total cost",
        band_b_text="Private 5–15% lower",
        band_c_text="Parity — within ± 5%",
        band_d_text="Public 5–15% lower",
        band_e_text="Public ≥ 15% lower total cost",
        dhl_ref="G9 / G-ADD-F10",
    ),
    dict(
        code="Q6",
        dimension="Managed platform dependency",
        question_text=(
            "How many required capabilities exist only as managed cloud services (managed DB, API "
            "mgmt, eventing, analytics, AI/ML, serverless, managed Kubernetes) versus the private "
            "catalog?"
        ),
        evidence_hint="Target architecture + service-catalog gap analysis",
        band_a_text="0 — private platform fully covers all required capabilities",
        band_b_text="1–2 services; private alternatives exist at comparable cost",
        band_c_text="3–5 services with a funded rebuild plan",
        band_d_text="> 5 services, or one core capability impractical to rebuild privately",
        band_e_text="Architecture is designed around cloud-native managed services",
        dhl_ref="G3 / G-ADD-F4",
    ),
    dict(
        code="Q7",
        dimension="Provisioning & environment lifecycle",
        question_text=(
            "What environment lead time and change frequency does the delivery plan require (create, "
            "clone, change, delete)?"
        ),
        evidence_hint="Release plan + IaC pipeline evidence + provisioning history",
        band_a_text="> 30 business days acceptable; environment changes < 1× per quarter",
        band_b_text="15–30 business days; changes < 1× per month",
        band_c_text="5–15 business days; roughly monthly changes",
        band_d_text="< 5 business days; weekly changes needed",
        band_e_text="Same-day, on-demand; multiple ephemeral environments per week via IaC",
        dhl_ref="G-ADD-F1 / F9",
    ),
    dict(
        code="Q8",
        dimension="Data classification & residency",
        question_text="What do the data classification record and legal register require for this workload's data?",
        evidence_hint="Data classification record, DPIA, legal/privacy register",
        band_a_text="Highest classification with residency/operator constraints that approved cloud regions cannot meet",
        band_b_text="Sensitive data where private hosting materially reduces compliance scope (documented)",
        band_c_text="Sensitive data fully covered by approved cloud controls and EU regions",
        band_d_text="Internal data with standard controls",
        band_e_text="Public / non-sensitive data",
        dhl_ref="G7",
    ),
    dict(
        code="Q9",
        dimension="Geographic distribution",
        question_text=(
            "Where must the workload serve users/systems in the next 24 months, relative to DHL's "
            "existing data-centre footprint?"
        ),
        evidence_hint="Business rollout plan + measured user latency per location",
        band_a_text="Users/systems concentrated at DHL DC locations; single geography",
        band_b_text="Single geography with minor remote usage",
        band_c_text="2 geographies, servable from DHL DCs or CDN within latency targets",
        band_d_text="2–3 geographies beyond the DHL DC footprint",
        band_e_text="≥ 3 geographies / global user base within 12 months",
        dhl_ref="G-ADD-F3",
    ),
    dict(
        code="Q10",
        dimension="Portability & modernization readiness",
        question_text=(
            "What share of application components can run containerized / refactored without major "
            "rewrite (7R disposition)?"
        ),
        evidence_hint="Application assessment + dependency inventory + 7R disposition",
        band_a_text="< 25% portable — legacy/monolith or unsupported stack",
        band_b_text="25–50% portable; high remediation cost",
        band_c_text="50–80% portable with a funded modernization plan",
        band_d_text="> 80% containerized / 12-factor ready",
        band_e_text="Already cloud-native, or vendor's strategic successor is SaaS/cloud-only",
        dhl_ref="G6",
    ),
    dict(
        code="Q11",
        dimension="Licensing portability",
        question_text="What do the vendor licence terms say about hosting this software in public cloud?",
        evidence_hint="Vendor licence terms / contract (clause reference)",
        band_a_text="Licence prohibits public cloud or requires dedicated physical hosts",
        band_b_text="Cloud hosting raises licence cost > 25% (per-core/host penalties)",
        band_c_text="BYOL portable at broadly equal cost",
        band_d_text="Cloud-based licensing 5–25% cheaper, or bundled with platform",
        band_e_text="Subscription/marketplace licensing only, or on-prem licence being phased out by vendor",
        dhl_ref="G-ADD-F6",
    ),
    dict(
        code="Q12",
        dimension="Continuity & recovery",
        question_text="What recovery capability do the BIA-approved RTO/RPO and continuity requirements demand?",
        evidence_hint="Business impact analysis, RTO/RPO targets, tested DR results",
        band_a_text="Isolated / air-gapped recovery or DHL-controlled alternate site contractually required",
        band_b_text="Private alternate site meets RTO/RPO at documented lower cost",
        band_c_text="RTO/RPO achievable in either model at comparable cost",
        band_d_text="RTO < 4 h / RPO < 15 min requiring automated multi-site recovery, cheaper in cloud per DR cost model",
        band_e_text="Near-zero RTO/RPO or cross-region active-active beyond private capability",
        dhl_ref="G8",
    ),
    dict(
        code="Q13",
        dimension="Operating model readiness",
        question_text=(
            "Which operating model demonstrably meets this workload's control requirements today "
            "(tested runbooks, monitoring coverage, certified staff, landing zone status)?"
        ),
        evidence_hint="Runbook test results, monitoring coverage %, certification counts, landing-zone status",
        band_a_text="Private operations fully compliant today; no production cloud landing zone or certified team",
        band_b_text="Private operations mature; cloud capability partial (landing zone in build)",
        band_c_text="Both models demonstrably supported with evidence",
        band_d_text="Production landing zone + certified team in place; private platform has documented gaps",
        band_e_text="Required capability absent from private platform roadmap; cloud operations are the DHL standard for this class",
        dhl_ref="G10",
    ),
    dict(
        code="Q14",
        dimension="Concentration & exit risk",
        question_text=(
            "What does the documented exit / substitutability analysis show for the intended hosting "
            "model?"
        ),
        evidence_hint="Exit plan, substitutability analysis, modeled exit cost vs 3-year run cost",
        band_a_text="No substitutable provider; modeled exit cost > 20% of 3-year run cost",
        band_b_text="Exit feasible but > 6 months effort and 10–20% of run cost",
        band_c_text="Documented exit plan, standardized stack, exit < 10% of run cost",
        band_d_text="Fully portable design (containers/OSS), multi-provider capable, exit tested",
        band_e_text=(
            "Current private setup is itself the concentration risk (single DC / single skill pool) "
            "and provider placement diversifies it, with a tested exit plan"
        ),
        dhl_ref="G5",
    ),
]
