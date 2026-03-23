# OBSIDIAN CORPORATION
### Human Resource Management System — v3.0

> The Corporate Management Platform  
> Dual-interface HRMS: **Web Portal** (`obsidian_web.py`) + **Desktop App** (`obsidian_desktop.py`)  
> Shared live data via `obsidian_data.json`

---

## Quick Start

### 1. Install dependencies
```bash
pip install flask openpyxl customtkinter matplotlib pillow
```

### 2. Run the Web Portal
```bash
python obsidian_web.py
# Opens at http://localhost:5001
```

### 3. Run the Desktop App
```bash
python obsidian_desktop.py
```

Both apps read and write the **same** `obsidian_data.json` — run either or both simultaneously.

---

## Default Credentials

| Username | Password | Role | Level | Visibility |
|---|---|---|---|---|
| `admin` | `admin123` | System Administrator | 4 | All employees · All data · User management |
| `hr_manager` | `hr123` | HR Manager | 3 | All employees · Payroll · Audit log |
| `manager1` | `mgr123` | Department Manager | 2 | Own department only |
| `staff1` | `staff123` | Staff Member | 1 | Own record only |

---

## File Reference

| File | Purpose |
|---|---|
| `obsidian_web.py` | Flask web application (2 267 lines) |
| `obsidian_desktop.py` | CustomTkinter desktop application (1 436 lines) |
| `obsidian_shared.py` | Shared data layer — auth, exports, role & dept definitions |
| `obsidian_data.json` | Live data — employees, users, audit log, leave requests |
| `obsidian_us_employees.json` | 33 US-based employees ready to import |

---

## Role System

Six access levels. Higher levels include all capabilities of levels below.

| Role | Level | Icon | Colour | Access Summary |
|---|---|---|---|---|
| **CEO** | 6 | 👑 | `#f5c518` Gold | Full read — all departments, payroll, audit |
| **Director General (DG)** | 5 | 🎖️ | `#c084fc` Purple | Full read — second in command |
| **Admin** | 4 | 🛡️ | `#e05252` Red | Full read + write + system user management |
| **HR Manager** | 3 | 👔 | `#4f8ef7` Blue | All employees, payroll, audit, approvals |
| **Manager** | 2 | 📋 | `#e09a30` Amber | Own department employees only |
| **Staff** | 1 | 🧑‍💼 | `#3dba7a` Green | Own record only |

### Permission Matrix

| Feature | Staff | Manager | HR | Admin | DG | CEO |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| View own record | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View dept employees | | ✅ | ✅ | ✅ | ✅ | ✅ |
| View ALL employees | | | ✅ | ✅ | ✅ | ✅ |
| Add / Edit employees | | | ✅ | ✅ | | |
| Delete employees | | | ✅ | ✅ | | |
| View departments | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Add / Edit departments | | | ✅ | ✅ | | |
| Delete departments | | | | ✅ | | |
| Submit promotion request | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Approve / Deny promotions | | | ✅ | ✅ | | |
| Submit own leave | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Submit leave for any employee | | | ✅ | ✅ | | |
| Approve / Deny leave | | | ✅ | ✅ | | |
| View payroll & salary | | | ✅ | ✅ | ✅ | ✅ |
| Edit salary | | | ✅ | ✅ | | |
| View audit log | | | ✅ | ✅ | ✅ | ✅ |
| Manage system users | | | | ✅ | | |
| Change own password | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Department-Scoped Visibility

When adding or editing a system user (Admin only), you can assign a **Department Scope**. Manager and Staff users with a scope set will only ever see employees in that department — enforced server-side, not just client-side.

**Resolution order:**
1. `department` field set directly on the system user record
2. Department of the user's linked employee record (if `emp_id` is set and no explicit dept)
3. No scope + no linked emp → Staff sees only own record; Manager sees nothing

CEO, DG, Admin, and HR always see **all employees** regardless of department scope.

---

## Features

### 📊 Dashboard
- Stat cards: Total · Active · On Leave · Inactive · Pending Promotions · Departments · Pending Leave
- Alert strips: contracts expiring ≤30 days · pending promotions awaiting review
- Contract expiry widget: 90-day window, colour-coded red ≤30d · amber ≤60d · grey ≤90d
- Department pie chart + employment type bar chart (requires matplotlib)
- Recent audit activity feed (last 14 entries)

### 👥 Employees
- Live search: ID, name, email, phone, department, occupation
- Filters: Department · Status
- Employee count label (`Showing X of Y employees`)
- Columns: ID · Name · Phone · Department · Occupation · Type · Status · Start Date
- Double-click → detail modal: all fields, skills chips, promotion history
- Add / Edit / Delete (HR+) · Import JSON or CSV · Export CSV or Excel

### 🏢 Departments
- Cards with icon, colour, KPI tags
- Detail modal: purpose, responsibilities, KPIs, head card, team preview (first 8 members)
- Rename cascades to all linked employee records
- Add / Edit (HR+) · Delete (Admin)

### 🏆 Promotions
- Submit with optional notes / justification field
- Approval updates employee `role` field automatically
- Columns: Employee · Current Role · Requested Role · Notes · Date · Status · Resolved By

### 📅 Leave Management
- Types: Annual · Sick · Maternity/Paternity · Unpaid · Other
- Notes field on submission
- Approval sets employee `status` to `on_leave`
- Columns: Employee · Type · From · To · Days · Notes · Status · Resolved By

### 💰 Payroll & Salary *(HR / Admin / CEO / DG)*
- **Filters**: Department · Currency · Status — all live, cascade the table
- **6 stat cards**: Total Shown · With Salary · Total USD · Avg USD · Highest USD · Lowest USD
- **Salary band chart** (web): `<20k / 20–50k / 50–100k / 100–200k / 200k+`
- **Dept breakdown**: USD total per department with animated progress bars + percentages
- Employee count label (`X of Y employees`)
- Edit salary inline: amount + currency
- Export CSV or Excel

### 📋 Audit Log *(HR / Admin / CEO / DG)*
- **4 filters**: Text search · Action type (12 categories) · User · Date range
- **Action categories with icons**: 🔐 Login · ➕ Added · ✏️ Updated · 🗑 Deleted · 🏆 Promotion · 📅 Leave · 📥 Import · 💰 Salary · 🔑 Password · 💾 Saved · 🏢 Department · 👤 System User
- **Date ranges**: Today · This Week · This Month
- **4 stat cards**: Total Events · Showing · Unique Users · Today
- Event count label
- Action badges colour-coded · User badges coloured by role
- Export CSV

### 🔑 Role Guide
- Cards for all 6 roles with icon, level, purpose, responsibilities
- Full permission matrix across all 6 roles
- Department definition cards with KPIs

### 🔐 System Users *(Admin only)*
- **6 roles available**: Staff · Manager · HR · Admin · DG · CEO
- **Department Scope**: restricts Manager/Staff visibility to one department
- Live role preview updates on role selection
- Link user to employee record via Employee ID
- Table: Username · Full Name · Role · Dept Scope · Employee ID · Created

### ⚙️ Profile
- Avatar upload (base64 data URL, shown in header)
- Linked employee card with click-to-navigate
- Role card: purpose + responsibilities
- Change password form (requires current password, min 6 chars)

---

## Web Keyboard Shortcuts

| Key | Action |
|---|---|
| `N` | Toggle notifications panel |
| `Escape` | Close any open modal or panel |
| `Enter` | Submit login form |

---

## API Reference (Web)

Base URL: `http://localhost:5001`. All endpoints (except `/api/login`) require the `obsidian_session` cookie.

### Auth
| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/api/login` | `{username, password}` |
| `POST` | `/api/logout` | — |
| `GET` | `/api/me` | — → current user object |

### Data
| Method | Endpoint | Role | Notes |
|---|---|---|---|
| `GET` | `/api/data` | All | Full payload scoped by role + dept. Includes employees, departments, audit log (HR+), leave, notifications, role/dept definitions, system users (Admin+) |

### Employees
| Method | Endpoint | Role |
|---|---|---|
| `POST` | `/api/employees` | HR+ |
| `PUT` | `/api/employees/<id>` | HR+ |
| `DELETE` | `/api/employees/<id>` | HR+ |

### Departments
| Method | Endpoint | Role |
|---|---|---|
| `POST` | `/api/departments` | HR+ |
| `PUT` | `/api/departments/<name>` | HR+ |
| `DELETE` | `/api/departments/<name>` | Admin |

### Promotions & Leave
| Method | Endpoint | Role | Body |
|---|---|---|---|
| `POST` | `/api/promotions` | All | `{emp_id, requested_role, notes?}` |
| `PUT` | `/api/promotions/<emp_id>/<idx>` | HR+ | `{status: "approved"\|"denied"}` |
| `POST` | `/api/leave` | All | `{emp_id, leave_type, start_date, end_date, notes?}` |
| `PUT` | `/api/leave/<idx>` | HR+ | `{status: "approved"\|"denied"}` |

### Profile
| Method | Endpoint | Body |
|---|---|---|
| `PUT` | `/api/profile` | `{photo}` base64 data URL |
| `POST` | `/api/change-password` | `{current_password, new_password}` |

### System Users *(Admin only)*
| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/api/sysusers` | `{username, full_name, role, password, emp_id?, department?}` |
| `PUT` | `/api/sysusers/<uname>` | Same fields; password optional |
| `DELETE` | `/api/sysusers/<uname>` | — |

### Exports & Import
| Method | Endpoint | Role | Result |
|---|---|---|---|
| `GET` | `/api/export/employees-csv` | HR+ | `obsidian_employees.csv` |
| `GET` | `/api/export/employees-excel` | HR+ | `obsidian_employees.xlsx` |
| `GET` | `/api/export/payroll-csv` | HR+ | `obsidian_payroll.csv` |
| `GET` | `/api/export/payroll-excel` | HR+ | `obsidian_payroll.xlsx` |
| `GET` | `/api/export/audit-csv` | HR+ | `obsidian_audit.csv` |
| `POST` | `/api/import` | HR+ | Multipart `.json` or `.csv` file |

---

## Employee Field Reference

| Field | Type | Notes |
|---|---|---|
| `id` | string | Auto-generated `OBSD-YYYY-NNNN` |
| `full_name` | string | **Required** |
| `email` | string | |
| `phone` | string | |
| `department` | string | Must match an existing department name |
| `occupation` | string | Job title |
| `role` | string | Descriptive role label (not the system access role) |
| `age` | string | |
| `location` | string | City or region |
| `employment_type` | string | `permanent` · `contract` · `probation` · `intern` · `part_time` |
| `status` | string | `active` · `inactive` · `on_leave` |
| `salary` | number | Numeric amount |
| `salary_currency` | string | `USD` · `NGN` · `GBP` · `EUR` · `KES` · `ZAR` · `GHS` |
| `contract_end` | string | `YYYY-MM-DD` — triggers expiry alerts |
| `start_date` | string | `YYYY-MM-DD` |
| `date_added` | string | Set automatically on creation |
| `manager_id` | string | Employee ID of direct manager |
| `skills` | list | Array of skill tag strings |
| `emergency_contact` | string | Name and phone |

---

## Import Formats

### JSON — list
```json
[
  {
    "full_name": "Amina Hassan",
    "email": "amina@obsidiancorp.com",
    "department": "Technology",
    "occupation": "Senior Engineer",
    "employment_type": "permanent",
    "status": "active",
    "salary": 95000,
    "salary_currency": "USD",
    "start_date": "2023-06-01",
    "skills": ["Python", "Django", "PostgreSQL"]
  }
]
```

### JSON — dict keyed by ID
```json
{
  "OBSD-2025-0001": {
    "full_name": "Chidi Okafor",
    "department": "Finance",
    "status": "active"
  }
}
```

### CSV
Header row required. Field names match the table above. For skills, use a comma-separated string in the cell: `"Python, Django, PostgreSQL"`. Existing IDs are overwritten on import.

---

## Design System

### Colours
| Token | Hex | Usage |
|---|---|---|
| Background | `#07091a` | Deep midnight navy |
| Surface | `#0c0f22` | Sidebar, header |
| Card | `#111428` | Content panels |
| Card 2 | `#161a30` | Nested cards |
| Border | `#1e2240` | Dividers, inputs |
| Gold | `#c9a84c` | Primary accent |
| Gold Light | `#e8c56a` | Hover |
| Gold Dark | `#9a7a30` | Muted gold |
| OK / Staff | `#3dba7a` | Success, active |
| Warning / Manager | `#e09a30` | Pending, caution |
| Error / Admin | `#e05252` | Danger, delete |
| Info / HR | `#4f8ef7` | Informational |
| Purple / Tech | `#7c5df9` | Technology dept |
| CEO | `#f5c518` | CEO role accent |
| DG | `#c084fc` | Director General accent |

### Typography
| Interface | Display | Body | Mono |
|---|---|---|---|
| Web | Bebas Neue | DM Sans | DM Mono |
| Desktop | Courier New Bold | Helvetica | Courier New |

---

## Security Notes

- **Session cookie name**: `obsidian_session` — isolated from any other Flask app on the same machine
- **Port**: `5001` — avoids conflicts with the default Flask port 5000
- **Secret key**: fixed string — sessions survive server restarts (change for production)
- **Password hashing**: SHA-256 + 16-byte random hex salt per password
- **Salary visibility**: stripped server-side from `/api/data` for roles below HR (level < 3)
- **Employee list scoping**: filtered server-side by role and department — not client-side only

---

## Changelog

### v3.0 (Current)
- **CEO 👑 and DG 🎖️ roles** — levels 6 and 5, full read-only access to all employees, payroll, and audit
- **Department-scoped visibility** — Manager/Staff see only their assigned department, enforced server-side in `/api/data`
- **Department field on system users** — assignable in Add/Edit User dialog, shown in user table as "Dept Scope"
- **Payroll overhaul** — dept/currency/status filters, 6 stat cards (incl. Highest/Lowest), salary band chart, animated dept progress bars, count label, Status column
- **Audit log overhaul** — user dropdown filter, date-range filter, 12 action categories with icons, 4 stat cards, role-coloured user badges, count label
- **Desktop app full parity** — all v3.0 web features mirrored in `obsidian_desktop.py`
- **Bug fix**: Jinja2 `TemplateSyntaxError: expected token 'end of print statement', got ':'` on startup (JS object literals `${{key:val}[x]}` conflicting with template engine — replaced with `stCls()` / `prCls()` helper functions)
- Port changed to `5001`; `SESSION_COOKIE_NAME = "obsidian_session"` to prevent cookie conflicts with older instances

### v2.0
- Added employee fields: phone, start date, manager ID, emergency contact, skills tags
- Contract expiration dashboard widget (90-day window, colour-coded)
- Promotion notes/justification field + resolver column
- Leave notes field + resolver column
- Audit log action-type filter + CSV export
- Department detail modal: purpose, responsibilities, KPIs, head, team preview
- Per-department payroll breakdown with progress bars
- Inactive employees stat card on dashboard

### v1.0
- Initial release: employees, departments, promotions, leave, payroll, audit log, system users, notifications, profile
