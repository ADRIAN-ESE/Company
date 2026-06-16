# Company

A collection of self-contained corporate / workforce-management system prototypes, each built independently in Python with a Flask web app (and, for two of the three, a matching CustomTkinter desktop app). Every project models the same general problem — employee lifecycle, departments, leave, payroll, promotions, audit logging — but wrapped in a different brand, theme, and feature set.

## Projects

| Project | Description | Interfaces | Version | Docs |
|---|---|---|---|---|
| **[ARCHER PRO](./ARCHER%20PRO/README.md)** (Archer Enterprise) | Corporate management system covering onboarding, departments, contracts, leave, payroll, and promotions, with a navy/gold dark UI. | Web + Desktop | v2.1 | [README](./ARCHER%20PRO/README.md) |
| **[Obsidian](./Obsidian/README.md)** (Obsidian Corporation) | The same employee-lifecycle platform with richer department/role pages, a contract-expiration dashboard widget, and per-department payroll breakdowns. | Web | v3.0 | [README](./Obsidian/README.md) |
| **[nexus_cyber](./nexus_cyber/README.md)** (Nexus Cyber) | A security-team-flavored rebrand of the same platform — "employees" become security analysts, "departments" become security teams (SOC, Threat Intel, Pen Testing, etc.), with a cyan cyber-themed UI. | Web + Desktop | v1.0 | [README](./nexus_cyber/README.md) |

Each folder is independent — its own data file, its own entry points, its own README with full setup instructions, API reference, and credentials. Start with whichever project's README you need; this file just gives the big picture.

## Repository Structure

```
Company/
├── ARCHER PRO/              Archer Enterprise — web + desktop editions (v2.1)
│   ├── archer_web.py
│   ├── archer_desktop.py
│   ├── archer_shared.py
│   ├── archer_data.json
│   ├── archer_workers.json / archer_workers.csv
│   └── README.md
├── Obsidian/                 Obsidian Corporation — web edition (v3.0)
│   ├── obsidian_web.py
│   ├── obsidian_shared.py
│   ├── obsidian_data.json
│   ├── obsidian_us_employees.json
│   ├── ARCHER PRO/           (earlier Archer snapshot, kept for reference)
│   ├── ORB2/                 (earlier dual web + desktop Obsidian build)
│   └── README.md
├── nexus_cyber/               Nexus Cyber — security workforce platform (v1.0)
│   ├── nexus_web.py
│   ├── nexus_desktop.py
│   ├── nexus_shared.py
│   ├── nexus_data.json
│   ├── nexus_logo.png
│   └── README.md
└── README.md                  ← you are here
```

## Shared Architecture

All three projects share the same underlying design, so once you understand one, the others follow the same patterns:

- **Employee/analyst records** with auto-generated IDs, profile photos (base64), employment type, and status tracking
- **Role-based access control** across four permission levels (Staff/Analyst → Manager/Team Lead → HR/Security Lead → Admin)
- **Department or team management**, including head assignment and (in Obsidian and Nexus Cyber) mission statements, KPIs, or focus areas
- **Promotion / clearance-upgrade workflow** with approve-deny resolution and a full audit trail
- **Leave management** with date-range calculation and approval workflow
- **Payroll** with multi-currency support (USD, EUR, GBP, NGN, KES, ZAR, GHS), restricted to HR/Admin roles
- **Audit logging** of every sensitive action, plus a **notifications panel** for promotions, leave, and new hires
- **Import/export** via JSON, CSV, and Excel (`openpyxl`)
- **Dark-themed UI** with a project-specific color palette, dashboard analytics, and charts

## Tech Stack

- **Language:** Python 3
- **Web framework:** Flask
- **Desktop UI:** CustomTkinter (ARCHER PRO, Nexus Cyber, and the `ORB2` build of Obsidian)
- **Charts:** Chart.js (web dashboards), Matplotlib (desktop dashboards)
- **Data export:** `openpyxl` for Excel, built-in `csv`/`json` otherwise
- **Persistence:** flat JSON data files — no external database
- **Auth:** salted SHA-256 password hashing with Flask sessions (web) or native desktop login windows

## Getting Started

```bash
git clone https://github.com/ADRIAN-ESE/Company.git
cd Company

# Pick a project and follow its own Quick Start section
cd "ARCHER PRO"      # or: cd Obsidian   |   cd nexus_cyber
pip install flask openpyxl customtkinter matplotlib pillow   # see that project's README for the exact list
python archer_web.py   # or archer_desktop.py / obsidian_web.py / nexus_web.py / nexus_desktop.py
```

Each web app serves on `http://localhost:5000` by default; check the relevant README if a project uses a different port.

## Default Credentials

Every project ships with the same default admin account for first login:

| Project | Username | Password |
|---|---|---|
| ARCHER PRO | `admin` | `admin123` |
| Obsidian | `admin` | `admin123` |
| nexus_cyber | `admin` | `admin123` |

Additional roles (HR/Security Lead, Manager/Team Lead, Staff/Analyst) are listed in each project's own README. **Change all default passwords immediately after first login** — these are demo credentials only.

## Status & Disclaimer

These are prototype/demo applications built for learning and portfolio purposes, not production systems:

- Data is stored as plaintext JSON files, not a real database
- Sample employees, salaries, and company data are fictional
- Default credentials and a fixed Flask `secret_key` are not safe for real deployment

If you intend to deploy any of these beyond local/demo use, see the **Security Notes** section in the relevant project's README first.

## License

No license has been added to this repository yet. Until one is added, all rights are reserved by the repository owner — open an issue or contact the maintainer if you'd like to use this code beyond personal reference.

---

Maintained by [ADRIAN-ESE](https://github.com/ADRIAN-ESE).
