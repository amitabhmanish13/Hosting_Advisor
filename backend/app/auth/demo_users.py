"""Identities offered by the local mock IdP (AUTH_PROVIDER=mock).

Each entry has the same claim shape a real Azure AD id_token would carry after
role/group-to-app-role mapping, so JIT provisioning in app/routers/auth.py
needs no branching between providers.
"""

DOMAINS = [
    "Digital Solutions",
    "DSC",
    "Ecommerce / DeC",
    "Express",
    "GF",
    "GFS",
    "DGFF / FEC",
]

DEMO_USERS = [
    {
        "sub": "mock|admin",
        "email": "admin@dhl-demo.local",
        "name": "Alex Admin",
        "roles": ["admin"],
        "domain": None,
        "label": "Alex Admin — Admin (global)",
    },
    {
        "sub": "mock|assessor-dgff",
        "email": "dana.assessor@dhl-demo.local",
        "name": "Dana Assessor",
        "roles": ["assessor"],
        "domain": "DGFF / FEC",
        "label": "Dana Assessor — Assessor (DGFF / FEC)",
    },
    {
        "sub": "mock|assessor-digital",
        "email": "priya.assessor@dhl-demo.local",
        "name": "Priya Assessor",
        "roles": ["assessor"],
        "domain": "Digital Solutions",
        "label": "Priya Assessor — Assessor (Digital Solutions)",
    },
    {
        "sub": "mock|approver",
        "email": "jordan.approver@dhl-demo.local",
        "name": "Jordan Approver",
        "roles": ["approver"],
        "domain": None,
        "label": "Jordan Approver — Approver (Hosting Advisory Group, global)",
    },
    {
        "sub": "mock|viewer",
        "email": "morgan.viewer@dhl-demo.local",
        "name": "Morgan Viewer",
        "roles": ["viewer"],
        "domain": None,
        "label": "Morgan Viewer — Viewer (Management Board, global)",
    },
]
