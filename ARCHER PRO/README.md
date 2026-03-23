# ARCHER ENTERPRISE
### Your Corporate Management & Service Agency
**v2.1 — Web Edition & Desktop Edition**

---

## Overview

ARCHER ENTERPRISE is a full-featured corporate management system delivered as two standalone applications — a **Flask web app** and a **CustomTkinter desktop app** — that share a single `archer_data.json` data file. The system covers the complete employee lifecycle: onboarding, department assignment, contract tracking, leave management, payroll, promotions, and offboarding.

Each employee record includes a **Purpose / Job Description** field that captures what the employee does, their responsibilities, and their place in the team. Each department carries a **mission statement** and **strategic goals** that give organisational context to every person within it.

---

## Quick Start

### Web Edition
```bash
pip install flask openpyxl
python archer_web.py
# Open: http://localhost:5000
```

### Desktop Edition
```bash
pip install customtkinter openpyxl matplotlib pillow
python archer_desktop.py
```

> Both editions read and write the same `archer_data.json` file and can run simultaneously.

---

## Default Credentials

| Username | Password | Role | Access Level |
|---|---|---|---|
| `admin` | admin123 | Admin | Full (Level 4) |
| `hr_manager` | hr123 | HR Manager | Level 3 |
| `manager1` | mgr123 | Manager | Level 2 |
| `staff1` | staff123 | Staff | Level 1 — own record only |

> **Change all default passwords immediately after first login.**

---

## Sample Data — Importing Workers

Two ready-to-import files are included with 25 workers, 5 per department:

| File | Format | Use |
|---|---|---|
| `archer_workers.json` | JSON | Full import including department metadata |
| `archer_workers.csv` | CSV | Lightweight employee-only import |

**To import:** Log in as `admin` or `hr_manager` → **Employees** → **Import** → select either file.

Each worker includes a full **Purpose / Job Description** and a detailed **Role title**. The JSON file also embeds department mission statements and strategic goals.

### Workers by Department

| Department | Roles Included |
|---|---|
| Administration | Senior Executive Assistant, Head of Office Operations, Junior Records Officer, Senior Corporate Secretary, Mid-Level Admin Coordinator |
| Human Resources | Senior HR Business Partner, Mid-Level Talent Acquisition Specialist, Lead L&D & Culture, Junior HR Data Analyst, Mid-Level Compensation & Benefits Officer |
| Finance | Head of Finance & Accounting, Mid-Level FP&A Analyst, Senior Internal Auditor, Mid-Level Budget & Cost Control Officer, Junior Treasury Analyst |
| Operations | Head of Operations & Service Delivery, Mid-Level Logistics Coordinator, Senior Process Improvement Analyst, Mid-Level Client Service Delivery Officer, Senior QA & Compliance Specialist |
| Technology | Senior Full-Stack Software Engineer, Mid-Level DevOps & Cloud Engineer, Mid-Level Data & BI Analyst, Senior Cybersecurity Analyst, Junior Frontend UI/UX Developer |

---

## Features

### Authentication & Security
- Animated splash screen with particle network background + slide-in login card (Web)
- Native login window with password masking (Desktop)
- Role-based access control with 4 permission levels
- Salted SHA-256 password hashing — passwords never stored in plaintext
- Session-based auth (Web) / window-based auth (Desktop)

### Employee Management
- Auto-generated employee IDs: `ARCH-YYYY-NNNN` (e.g. `ARCH-2026-0001`)
- **Purpose / Job Description** — freetext field describing role responsibilities and organisational context
- **Role title** — full seniority-aware title (e.g. "Senior Full-Stack Software Engineer")
- Employment type: Permanent, Contract, Probation, Intern, Part Time
- Status: Active, Inactive, On Leave
- Contract end date tracking
- Profile photos (base64, stored in `archer_data.json`)
- Import from JSON or CSV; Export to CSV and Excel

### Department Management
- Create, edit and delete departments
- **Mission statement** — defines the department's overarching purpose
- **Strategic goals** — up to 4 measurable objectives per department
- Assign department heads by employee ID
- Live employee count per department

### Promotion Workflow
- Any user can submit a promotion request for an employee
- HR and Admin approve or deny with full audit trail
- Full history per employee — current role, requested role, date, resolver

### Leave Management
- Types: Annual, Sick, Maternity/Paternity, Unpaid, Other
- Staff submit for themselves; HR/Admin can submit for any employee
- Approve / Deny workflow with resolver and timestamp
- Days calculated automatically from date range
- Approved leave auto-sets employee status to On Leave

### Payroll & Salary
- Salary and currency fields per employee (HR and Admin only)
- Multi-currency: USD, EUR, GBP, NGN, KES, ZAR, GHS
- Payroll overview with totals; export to CSV or Excel

### Dashboard & Analytics
- Live stats: total employees, active, on leave, pending promotions, pending leave, departments
- Department distribution chart (doughnut)
- Employment type breakdown chart (bar)
- Recent audit activity feed

### Notifications Panel
- Slide-out panel (Web) with unread badge counter
- Notifications triggered by: new employees, promotion requests, leave requests
- Per-user read/unread tracking; mark individual or all as read

### Audit Log
- Every action logged — who, what, target, detail, timestamp
- Up to 1,000 most recent entries retained
- Searchable (HR and Admin only)

### System User Management (Admin only)
- Create, edit, delete portal login accounts
- Assign roles: Staff, Manager, HR Manager, Admin
- Link system users to employee records by ID
- Hashed password management

### Profile & Settings
- View own details and linked employee ID
- Upload profile photo (Web)
- Change password (both editions)

---

## Role Permissions Matrix

| Feature | Staff | Manager | HR | Admin |
|---|---|---|---|---|
| View own employee record | ✅ | ✅ | ✅ | ✅ |
| View all employee records | | ✅ | ✅ | ✅ |
| Add / Edit / Delete employees | | | ✅ | ✅ |
| View departments | ✅ | ✅ | ✅ | ✅ |
| Add / Edit departments | | | ✅ | ✅ |
| Delete departments | | | | ✅ |
| Submit promotion request | ✅ | ✅ | ✅ | ✅ |
| Approve / Deny promotions | | | ✅ | ✅ |
| Submit own leave request | ✅ | ✅ | ✅ | ✅ |
| Submit leave for any employee | | | ✅ | ✅ |
| Approve / Deny leave | | | ✅ | ✅ |
| View payroll / salary | | | ✅ | ✅ |
| Edit salary | | | ✅ | ✅ |
| Export payroll | | | ✅ | ✅ |
| View audit log | | | ✅ | ✅ |
| Manage system users | | | | ✅ |
| Change own password | ✅ | ✅ | ✅ | ✅ |

---

## Data Structure (`archer_data.json`)

```json
{
  "meta": { "last_emp_num": 25 },

  "system_users": {
    "admin": {
      "password_hash": "salt:sha256hash",
      "role": "admin",
      "full_name": "System Administrator",
      "emp_id": null,
      "photo": null,
      "created": "2026-03-22"
    }
  },

  "employees": {
    "ARCH-2026-0001": {
      "full_name": "Chidi Okeke",
      "email": "c.okeke@archerco.com",
      "department": "Technology",
      "occupation": "Software Engineer",
      "role": "Senior Full-Stack Software Engineer",
      "purpose": "Designs, builds, and maintains enterprise web applications and internal tools. Leads technical architecture decisions, conducts code reviews, and mentors junior engineers.",
      "age": "33",
      "location": "Lagos, Nigeria",
      "employment_type": "permanent",
      "status": "active",
      "contract_end": "",
      "salary": "105000",
      "salary_currency": "USD",
      "photo": null,
      "promotion_requests": [],
      "date_added": "2022-06-01"
    }
  },

  "departments": {
    "Technology": {
      "description": "IT infrastructure, software engineering, and digital systems",
      "mission": "To power the digital backbone of ARCHER ENTERPRISE by building robust systems, securing data assets, and delivering technology solutions that accelerate business growth.",
      "goals": [
        "Develop, maintain, and scale enterprise software and digital platforms",
        "Ensure 99.9% uptime for critical infrastructure and internal systems",
        "Protect company data and networks through proactive cybersecurity measures",
        "Drive digital transformation initiatives across all business units"
      ],
      "head_id": "ARCH-2026-0001"
    }
  },

  "audit_log": [
    {
      "ts": "2026-03-22 10:45:00",
      "user": "admin",
      "action": "Added employee",
      "target": "ARCH-2026-0001",
      "detail": "Chidi Okeke"
    }
  ],

  "notifications": [
    {
      "id": "abc123",
      "ts": "2026-03-22 10:45:00",
      "type": "success",
      "message": "New employee added: Chidi Okeke (ARCH-2026-0001)",
      "read_by": [],
      "roles": ["admin", "hr"]
    }
  ],

  "leave_requests": [
    {
      "emp_id": "ARCH-2026-0001",
      "leave_type": "annual",
      "start_date": "2026-04-01",
      "end_date": "2026-04-07",
      "notes": "Family vacation",
      "status": "pending",
      "submitted_by": "admin",
      "submitted_at": "2026-03-22 11:00"
    }
  ]
}
```

---

## Employee Fields Reference

| Field | Type | Description |
|---|---|---|
| `full_name` | string | Employee's full name |
| `email` | string | Work email address |
| `department` | string | Department name (must match a department in the system) |
| `occupation` | string | Job category / occupation type |
| `role` | string | Full role title including seniority (e.g. "Senior Full-Stack Software Engineer") |
| `purpose` | string | Job description — responsibilities, scope, and organisational context |
| `age` | string | Age in years |
| `location` | string | City and country |
| `employment_type` | enum | `permanent` `contract` `probation` `intern` `part_time` |
| `status` | enum | `active` `inactive` `on_leave` |
| `contract_end` | date | Contract end date (YYYY-MM-DD); blank for permanent staff |
| `salary` | number | Gross salary amount |
| `salary_currency` | enum | `USD` `EUR` `GBP` `NGN` `KES` `ZAR` `GHS` |
| `photo` | string | Base64-encoded profile image (null if not set) |
| `promotion_requests` | array | History of promotion requests for this employee |
| `date_added` | date | Date the employee was added to the system |

---

## Department Fields Reference

| Field | Type | Description |
|---|---|---|
| `description` | string | Short one-line description of the department's function |
| `mission` | string | Mission statement — the department's overarching purpose |
| `goals` | array | Up to 4 strategic goals or measurable objectives |
| `head_id` | string | Employee ID of the department head (optional) |

---

## Import File Formats

### JSON (array of employees — recommended)
```json
[
  {
    "full_name": "Jane Doe",
    "email": "jane@archerco.com",
    "department": "Technology",
    "occupation": "Software Engineer",
    "role": "Senior Full-Stack Software Engineer",
    "purpose": "Leads development of the core platform and mentors the frontend team.",
    "age": "31",
    "location": "Lagos, Nigeria",
    "employment_type": "permanent",
    "status": "active",
    "salary": "95000",
    "salary_currency": "USD",
    "contract_end": "",
    "date_added": "2026-01-10"
  }
]
```

### CSV (employees)
```
full_name,email,department,occupation,role,purpose,age,location,employment_type,status,salary,salary_currency,contract_end,date_added
Jane Doe,jane@archerco.com,Technology,Software Engineer,Senior Full-Stack Software Engineer,"Leads development...",31,Lagos,permanent,active,95000,USD,,2026-01-10
```

> Wrap the `purpose` field in double quotes in CSV if it contains commas.

---

## Web Edition API Reference

All endpoints require an active session. Authenticate first via `POST /api/login`.

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/login` | `{username, password}` → session + user object |
| `POST` | `/api/logout` | Clear session |
| `GET` | `/api/me` | Current user info |
| `GET` | `/api/data` | Full data bundle (filtered by role) |

### Employees
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/employees` | HR+ | Add employee |
| `PUT` | `/api/employees/<id>` | HR+ | Update employee |
| `DELETE` | `/api/employees/<id>` | HR+ | Delete employee |

### Departments
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/departments` | HR+ | Add department |
| `PUT` | `/api/departments/<name>` | HR+ | Update department |
| `DELETE` | `/api/departments/<name>` | Admin | Delete department |

### Promotions
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/promotions` | All | Submit `{emp_id, requested_role}` |
| `PUT` | `/api/promotions/<id>/<idx>` | HR+ | Resolve `{resolution: approved\|denied}` |

### Leave
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/leave` | All | Submit leave request |
| `PUT` | `/api/leave/<idx>` | HR+ | Resolve `{resolution: approved\|denied}` |

### Profile & Password
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `PUT` | `/api/profile` | All | Update photo |
| `POST` | `/api/change-password` | All | Change password |

### System Users (Admin only)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/sysusers` | Create user |
| `PUT` | `/api/sysusers/<username>` | Update user |
| `DELETE` | `/api/sysusers/<username>` | Delete user |

### Notifications
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/notifications/read` | Mark one read `{id}` |
| `POST` | `/api/notifications/read-all` | Mark all read |

### Export / Import
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/export/employees-csv` | All | Download employees CSV |
| `GET` | `/api/export/employees-excel` | All | Download employees Excel |
| `GET` | `/api/export/payroll-csv` | HR+ | Download payroll CSV |
| `GET` | `/api/export/payroll-excel` | HR+ | Download payroll Excel |
| `POST` | `/api/import` | HR+ | Upload JSON or CSV |

---

## File Structure

```
archer_web.py            — Flask web application (self-contained, ~1,500 lines)
archer_desktop.py        — CustomTkinter desktop application (~1,050 lines)
archer_shared.py         — Shared data layer, auth helpers, export utilities
archer_data.json         — Shared data file (auto-created on first run)
archer_workers.json      — 25 sample workers with purpose, roles, dept metadata
archer_workers.csv       — 25 sample workers in CSV format
README.md                — This file
README.docx              — Word document version
```

---

## Design Language

| Token | Value | Usage |
|---|---|---|
| Background | `#07091a` | Deep midnight navy |
| Surface | `#0c0f22` | Sidebar, header |
| Card | `#111428` | Content panels |
| Gold | `#c9a84c` | Primary accent — branding, highlights |
| OK | `#3dba7a` | Success states |
| Warning | `#e09a30` | Pending states |
| Error | `#e05252` | Danger, denied |
| Info | `#4f8ef7` | Informational |
| Body font (web) | DM Sans | General text |
| Display font (web) | Bebas Neue | Headers, titles |
| Mono font (web) | DM Mono | IDs, timestamps, code |

---

## Requirements

| Package | Required By | Purpose |
|---|---|---|
| `flask` | Web Edition | HTTP server and routing |
| `customtkinter` | Desktop Edition | Modern Tkinter UI widgets |
| `openpyxl` | Both (optional) | Excel export |
| `matplotlib` | Desktop (optional) | Dashboard charts |
| `pillow` | Desktop (optional) | Photo handling |

---

## Security Notes

- Passwords are hashed with a random 32-character salt + SHA-256. The hash is irreversible.
- The web edition uses Flask server-side sessions. Set `app.secret_key` to a fixed value in production.
- `archer_data.json` is stored as plaintext. In production, use proper file permissions or a database.
- Photos are stored as base64 strings inside `archer_data.json`. Compress images before uploading.

---

## Changelog

### v2.1
- Added **Purpose / Job Description** field to every employee record
- Roles upgraded to full seniority-aware titles (e.g. "Senior Full-Stack Software Engineer")
- Departments now include **mission statements** and **strategic goals**
- `archer_workers.json` and `archer_workers.csv` — 25 ready-to-import sample workers across 5 departments
- `archer_shared.py` — `purpose` added to CSV/Excel export field list
- Both apps updated: purpose field in Add/Edit forms and employee detail views

### v2.0
- Full rewrite from `user_manager_pro.py` / `user_manager_web.py`
- ARCHER ENTERPRISE branding — deep navy + gold design language
- Login screen with animated particle network and splash sequence
- Role-based access control (Admin, HR, Manager, Staff)
- Employee IDs auto-generated as `ARCH-YYYY-NNNN`
- Leave management module with approve/deny workflow
- Payroll & salary module with multi-currency support
- Notifications panel with per-user read/unread tracking
- Audit log with full action history
- System user management (Admin only)

---

*ARCHER ENTERPRISE v2.1 — Built with Python, Flask, and CustomTkinter*
