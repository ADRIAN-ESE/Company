# OBSIDIAN CORPORATION
### The Corporate Management Platform
**v3.0 — Web Edition**

---

## Overview

OBSIDIAN CORPORATION is a full-featured corporate management system built as a self-contained **Flask web application** backed by a single `obsidian_data.json` data file. The system covers the complete employee lifecycle: onboarding, department assignment, contract tracking, leave management, payroll, promotions, and offboarding — all from a sleek dark-themed portal.

---

## Quick Start

### Web Edition
```bash
pip install flask openpyxl
python obsidian_web.py
# Open: http://localhost:5000
```

> `obsidian_data.json` is auto-created on first run with default users and departments.

---

## Default Credentials

| Username     | Password   | Role         | Access Level   |
|--------------|------------|--------------|----------------|
| `admin`      | admin123   | Admin        | Full (Level 4) |
| `hr_manager` | hr123      | HR Manager   | Level 3        |
| `manager1`   | mgr123     | Manager      | Level 2        |
| `staff1`     | staff123   | Staff        | Level 1        |

> **Change all default passwords immediately after first login.**

---

## Features

### Authentication & Security
- Animated splash screen with particle network (Web)
- Session-based authentication with salted SHA-256 password hashing
- Role-based access control with 4 permission levels
- Keyboard shortcut: `N` toggles notifications, `Esc` closes modals

### Employee Management
- Auto-generated employee IDs: `OBSD-YYYY-NNNN` (e.g. `OBSD-2026-0001`)
- Profile photos (base64-encoded, stored in `obsidian_data.json`)
- **New in v3.0:** Phone number, Start Date, Direct Manager (linked by ID), Emergency Contact, Skills (multi-tag chip input)
- Employment types: Permanent, Contract, Probation, Intern, Part Time
- Statuses: Active, Inactive, On Leave
- Contract end date tracking
- Employee count label with live filter feedback
- Import from JSON or CSV; Export to JSON, CSV, or Excel (.xlsx)

### Department Management
- 5 pre-defined departments with full purpose definitions, responsibility lists, and KPI tags
- **New in v3.0:** Rich department cards with icon, colour accent, and KPI badges
- **New in v3.0:** Department detail modal — purpose statement, responsibilities, KPIs, department head card, and team member preview
- Create, edit, and delete departments
- Assign department heads by employee ID

### Role Guide *(new in v3.0)*
- Dedicated sidebar page accessible to all roles
- Each of the 4 system roles (Admin, HR Manager, Manager, Staff) displays: purpose, icon, colour, access level, and responsibility list
- Full permission matrix table

### Promotion Workflow
- Any user can submit a promotion request for an employee
- **New in v3.0:** Justification/notes field on submission
- **New in v3.0:** Resolver column shows who approved or denied
- HR and Admin can approve or deny; approved promotions auto-update the employee's role
- Full history per employee

### Leave Management
- Staff can submit leave requests (annual, sick, maternity/paternity, unpaid, other)
- HR / Admin can submit on behalf of any employee
- Approve / Deny workflow with resolver tracking
- Days calculated automatically from date range
- **New in v3.0:** Notes and resolver columns visible in leave table
- Approved leave auto-sets employee status to "On Leave"

### Payroll & Salary
- Salary and currency fields per employee (HR and Admin only)
- Multi-currency support: USD, EUR, GBP, NGN, KES, ZAR, GHS
- **New in v3.0:** Per-department USD payroll breakdown with progress bars and percentages
- Export payroll to CSV or Excel
- Access restricted to HR and Admin roles

### Dashboard & Analytics
- Live stats: total employees, active, on leave, inactive, pending promotions, pending leave, departments
- **New in v3.0:** Contract Expiration widget — all contracts ending within 90 days, colour-coded by urgency (red ≤30 days, amber ≤60, gray ≤90)
- **New in v3.0:** Alert strips for imminent contract expirations and pending promotions
- Department distribution chart (doughnut)
- Employment type breakdown chart (bar)
- Recent audit activity feed

### Audit Log
- Every action is logged: who, what, target, detail, timestamp
- **New in v3.0:** Action-type filter dropdown
- **New in v3.0:** Export Audit Log to CSV
- Up to 1,000 most recent entries retained
- Colour-coded action badges (Login, Added, Updated, Deleted, Imported)

### Notifications Panel
- Slide-out panel (keyboard shortcut: `N`)
- **New in v3.0:** Type icons per notification (✅ success, ❌ error, ⚠️ warning, ℹ️ info)
- Notifications triggered by: new employees, promotion requests, leave requests
- Per-user read/unread tracking; mark one or all as read

### System User Management (Admin only)
- Create, edit, delete portal login accounts
- **New in v3.0:** Live role preview in the user modal — shows icon, label, and purpose of selected role
- Assign roles: Staff, Manager, HR Manager, Admin
- Link system users to employee records by ID
- Password management (hashed, never shown)

### Profile & Settings
- View own details and linked employee record
- **New in v3.0:** Role card on profile page — shows your role's purpose and responsibilities
- Upload profile photo (Web edition)
- Change password

---

## Role Definitions

### 🛡️ Admin — Level 4
Full system control and governance.
- Create, edit, and delete system user accounts
- Configure access roles and permission levels
- Approve or override any HR decision
- Access all audit logs and system settings
- Manage department structure and org-wide policies

### 👔 HR Manager — Level 3
Manages the complete employee lifecycle.
- Add, edit, and remove employee records
- Approve or deny promotion and leave requests
- View and manage payroll and salary data
- Run workforce analytics and export reports
- Coordinate training, benefits, and compliance

### 📋 Manager — Level 2
Oversees team performance and day-to-day operations.
- View all employee records and department data
- Submit and track promotion requests for team members
- Submit leave requests on behalf of direct reports
- Monitor team attendance, status, and workload

### 🧑‍💼 Staff — Level 1
Standard self-service portal access.
- View own employee profile and records
- Submit personal leave requests
- Request a promotion or role change
- Update profile photo and change password

---

## Department Definitions

### 🏛️ Administration
Serves as the operational backbone of the organisation, ensuring smooth corporate governance, executive support, and facility management.
- **KPIs:** Document turnaround time · Facilities uptime · Compliance adherence

### 👥 Human Resources
Drives talent strategy, employee engagement, and people operations to build and sustain a high-performing workforce.
- **KPIs:** Time-to-hire · Employee retention rate · Training completion rate

### 💰 Finance
Safeguards the financial health of the organisation through rigorous planning, reporting, and treasury management.
- **KPIs:** Budget variance · Audit findings count · Cash flow coverage ratio

### ⚙️ Operations
Delivers core business services with operational excellence, ensuring quality, efficiency, and continuous improvement.
- **KPIs:** Service delivery rate · Process cycle time · Customer satisfaction score

### 💻 Technology
Powers the organisation's digital infrastructure, software systems, and cybersecurity posture.
- **KPIs:** System uptime · Incident resolution time · Security vulnerability count

---

## Role Permissions Matrix

| Feature                           | Staff | Manager | HR  | Admin |
|-----------------------------------|-------|---------|-----|-------|
| View own employee record          | ✅    | ✅      | ✅  | ✅    |
| View all employee records         |       | ✅      | ✅  | ✅    |
| Add / Edit / Delete employees     |       |         | ✅  | ✅    |
| View departments                  | ✅    | ✅      | ✅  | ✅    |
| Add / Edit departments            |       |         | ✅  | ✅    |
| Delete departments                |       |         |     | ✅    |
| Submit promotion request          | ✅    | ✅      | ✅  | ✅    |
| Approve / Deny promotions         |       |         | ✅  | ✅    |
| Submit own leave request          | ✅    | ✅      | ✅  | ✅    |
| Submit leave for any employee     |       |         | ✅  | ✅    |
| Approve / Deny leave              |       |         | ✅  | ✅    |
| View payroll / salary             |       |         | ✅  | ✅    |
| Edit salary                       |       |         | ✅  | ✅    |
| Export payroll                    |       |         | ✅  | ✅    |
| Export audit log                  |       |         | ✅  | ✅    |
| View audit log                    |       |         | ✅  | ✅    |
| View Role Guide                   | ✅    | ✅      | ✅  | ✅    |
| Manage system users               |       |         |     | ✅    |
| Change own password               | ✅    | ✅      | ✅  | ✅    |

---

## Importing Employees

Go to **Employees → Import** and upload a `.json` or `.csv` file.

### JSON Format
```json
[
  {
    "full_name": "Jane Smith",
    "email": "jane@company.com",
    "phone": "+1 212 555 0100",
    "department": "Technology",
    "occupation": "Software Engineer",
    "role": "Senior",
    "age": "31",
    "location": "New York, NY",
    "employment_type": "permanent",
    "status": "active",
    "salary": "115000",
    "salary_currency": "USD",
    "contract_end": "",
    "start_date": "2023-03-01",
    "manager_id": "",
    "emergency_contact": "John Smith — +1 212 555 0101",
    "skills": ["Python", "React", "AWS"]
  }
]
```

### CSV Format
```
full_name,email,phone,department,occupation,role,age,location,employment_type,status,salary,salary_currency,contract_end,start_date,manager_id,emergency_contact,skills
Jane Smith,jane@co.com,+1 212 555 0100,Technology,Engineer,Senior,31,"New York, NY",permanent,active,115000,USD,,,,"John Smith — +1 212 555 0101","Python, React, AWS"
```

> A sample import file `obsidian_us_employees.json` is included — 33 US-based employees across all 5 departments, with full skills, emergency contacts, and role assignments.

---

## Data Structure (`obsidian_data.json`)

```json
{
  "meta": { "last_emp_num": 33 },
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
    "OBSD-2026-0001": {
      "full_name": "Jane Smith",
      "email": "jane@company.com",
      "phone": "+1 212 555 0100",
      "department": "Technology",
      "occupation": "Software Engineer",
      "role": "Senior",
      "age": "31",
      "location": "New York, NY",
      "employment_type": "permanent",
      "status": "active",
      "salary": "115000",
      "salary_currency": "USD",
      "contract_end": "",
      "start_date": "2023-03-01",
      "date_added": "2026-03-22",
      "manager_id": null,
      "emergency_contact": "John Smith — +1 212 555 0101",
      "skills": ["Python", "React", "AWS"],
      "photo": null,
      "promotion_requests": []
    }
  },
  "departments": {
    "Technology": {
      "description": "IT infrastructure and software",
      "head_id": "OBSD-2026-0001"
    }
  },
  "audit_log": [],
  "notifications": [],
  "leave_requests": []
}
```

---

## Web Edition API Reference

All endpoints require an active session. Authenticate via `POST /api/login` first.

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/login` | `{username, password}` → session + user object |
| `POST` | `/api/logout` | Clear session |
| `GET`  | `/api/me` | Current user info |

### Data
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `GET`  | `/api/data` | All | Full data bundle (role-filtered). Now includes `role_definitions` and `dept_definitions`. |

### Employees
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `POST`   | `/api/employees` | HR+ | Add employee |
| `PUT`    | `/api/employees/<id>` | HR+ | Update employee |
| `DELETE` | `/api/employees/<id>` | HR+ | Delete employee |

### Departments
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `POST`   | `/api/departments` | HR+ | Add department |
| `PUT`    | `/api/departments/<name>` | HR+ | Update department |
| `DELETE` | `/api/departments/<name>` | Admin | Delete department |

### Promotions
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `POST` | `/api/promotions` | All | Submit `{emp_id, requested_role, notes}` |
| `PUT`  | `/api/promotions/<id>/<idx>` | HR+ | Resolve `{resolution: approved\|denied}` |

### Leave
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `POST` | `/api/leave` | All | Submit request |
| `PUT`  | `/api/leave/<idx>` | HR+ | Resolve `{resolution: approved\|denied}` |

### Profile
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `PUT`  | `/api/profile` | All | Update photo |
| `POST` | `/api/change-password` | All | Change password |

### System Users (Admin only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST`   | `/api/sysusers` | Create user |
| `PUT`    | `/api/sysusers/<username>` | Update user |
| `DELETE` | `/api/sysusers/<username>` | Delete user |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/notifications/read` | Mark one read `{id}` |
| `POST` | `/api/notifications/read-all` | Mark all read |

### Export / Import
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `GET`  | `/api/export/employees-csv` | All | Download employees CSV |
| `GET`  | `/api/export/employees-excel` | All | Download employees Excel |
| `GET`  | `/api/export/payroll-csv` | HR+ | Download payroll CSV |
| `GET`  | `/api/export/payroll-excel` | HR+ | Download payroll Excel |
| `GET`  | `/api/export/audit-csv` | HR+ | Download audit log CSV *(new)* |
| `POST` | `/api/import` | HR+ | Upload JSON or CSV |

---

## File Structure

```
obsidian_web.py              — Flask web application (v3.0, ~2000 lines)
obsidian_shared.py           — Shared data layer, auth, role/dept definitions, exports (~260 lines)
obsidian_data.json           — Shared data file (auto-created on first run)
obsidian_us_employees.json   — Sample import file: 33 US employees across 5 departments
README.md                  — This file
```

---

## Design Language

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#07091a` | Deep midnight navy |
| Surface | `#0c0f22` | Sidebar, header |
| Card | `#111428` | Content panels |
| Gold | `#c9a84c` | Primary accent — branding, highlights |
| OK | `#3dba7a` | Success states, Staff role |
| Warning | `#e09a30` | Pending states, Manager role |
| Error | `#e05252` | Danger, denied states, Admin role |
| Info | `#4f8ef7` | Informational, HR role |
| Purple | `#7c5df9` | Technology department accent |
| Body font | DM Sans | General text |
| Display font | Bebas Neue | Headers, titles |
| Mono font | DM Mono | IDs, timestamps, code |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `N` | Toggle notifications panel |
| `Esc` | Close open modal or panel |
| `Enter` (login screen) | Submit login |

---

## Security Notes

- All passwords are hashed with a random 32-character salt and SHA-256. The hash is never reversible.
- The web edition uses Flask server-side sessions. Set `app.secret_key` to a fixed value in `obsidian_web.py` for production deployments.
- `obsidian_data.json` is stored as plaintext JSON. In production, use proper file permissions or migrate to a database (SQLite, PostgreSQL, etc.).
- Photos are stored as base64 strings. Compress images before upload to keep the data file size manageable.

---

## Requirements

| Package | Purpose |
|---------|---------|
| `flask` | HTTP server and routing |
| `openpyxl` | Excel export (optional — CSV still works without it) |

```bash
pip install flask openpyxl
```

---

## Changelog

### v3.0 (2026-03-22)
- **Role Guide page** — dedicated view for all 4 system roles with purpose, responsibilities, and permission matrix
- **Department detail modal** — full purpose, responsibilities, KPIs, head, and team preview per department
- **Role and department definitions** — full structured metadata served via `/api/data`
- **New employee fields** — Phone, Start Date, Direct Manager, Emergency Contact, Skills (tag chips)
- **Contract expiration widget** on dashboard with colour-coded urgency
- **Dashboard alert strips** for imminent expirations and pending promotions
- **Per-department payroll breakdown** with progress bars on Payroll page
- **Role card on profile page** — shows your role's purpose and responsibilities
- **Audit log export to CSV** (`GET /api/export/audit-csv`)
- **Action-type filter** on Audit Log page
- **Promotion notes field** and resolver column
- **Leave notes and resolver columns** in leave table
- **Export dropdown** on Employees page (CSV / Excel)
- **Employment type filter** on Employees page
- Employee count label with live filter feedback
- Live role preview in System User modal
- Notification type icons (✅ ❌ ⚠️ ℹ️)
- Keyboard shortcuts: `N` for notifications, `Esc` for modals
- `obsidian_shared.py` upgraded: new fields in `EMP_FIELDS`, audit CSV export helper, `export_audit_csv_bytes()`

### v2.0
- Initial web edition with Flask + CustomTkinter desktop app
- Employee management, departments, promotions, leave, payroll, audit log
- Role-based access control (4 levels)
- Import/export (JSON, CSV, Excel)

---

*OBSIDIAN CORPORATION v3.0 — Built with Python and Flask*
