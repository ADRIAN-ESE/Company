# 🔒 NEXUS CYBER
## Security Workforce Management Platform v1.0

A comprehensive cyber security company workforce management system featuring a modern dark cyber-themed UI, role-based access control, and dual interface options (Desktop and Web).

---

## 🚀 Quick Start

### Prerequisites
```bash
pip install customtkinter flask openpyxl matplotlib pillow
```

### Desktop Application
```bash
cd nexus_cyber
python nexus_desktop.py
```

### Web Application
```bash
cd nexus_cyber
python nexus_web.py
```
Then open http://localhost:5000 in your browser.

---

## 🔑 Default Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Security Administrator |
| `sec_lead` | `lead123` | Security Lead |
| `team_lead1` | `tl123` | Team Lead |
| `analyst1` | `analyst123` | Security Analyst |

---

## 🏢 Security Teams (Departments)

The system comes pre-configured with six cyber security teams:

| Team | Icon | Focus |
|------|------|-------|
| **Threat Intelligence** | 🎯 | Threat monitoring, dark web analysis, IOC databases |
| **Security Operations (SOC)** | 📡 | 24/7 monitoring, SIEM, incident triage |
| **Incident Response** | 🚨 | Breach response, digital forensics, playbooks |
| **Penetration Testing** | 🎭 | Ethical hacking, vulnerability assessment, red team |
| **Compliance & Risk** | 📋 | SOC2/ISO 27001 audits, policy management |
| **Security Engineering** | ⚙️ | Security tools, automation, SOAR platforms |

---

## 👥 Role-Based Access Control

### Security Administrator (Level 4)
- Full system control
- Manage all users and security policies
- Access all audit logs and incident reports
- Configure access roles and clearance levels

### Security Lead (Level 3)
- Manage analyst lifecycle
- Approve/deny clearance upgrades
- View and manage compensation data
- Run team analytics and export reports
- Coordinate training and compliance

### Team Lead (Level 2)
- View all team data and analyst records
- Submit clearance requests for team members
- Monitor team availability and workload
- Collaborate on hiring and performance reviews

### Security Analyst (Level 1)
- View own profile and records
- Submit personal certification requests
- Request clearance upgrades
- Update profile photo and password

---

## ✨ Features

### Core Functionality
- **Analyst Management** — Full CRUD operations for security analysts
- **Team Management** — Organize by security teams with custom descriptions
- **Clearance Upgrades** — Workflow for security clearance advancement
- **Leave Management** — Absence tracking with approval workflow
- **Compensation** — Salary management (Security Leads & Admin only)
- **Audit Logging** — Complete activity trail
- **Notifications** — Real-time alerts for important events

### Data Operations
- **Import/Export** — JSON and CSV support
- **Excel Export** — Full-featured spreadsheet generation
- **Photo Upload** — Profile pictures with base64 encoding

### User Interface
- **Cyber Theme** — Dark navy background with cyan/electric blue accents
- **Responsive Design** — Works on all screen sizes
- **Keyboard Shortcuts** — `Enter` to login, `Escape` to close modals, `N` for notifications
- **Animated Login** — Particle effects and smooth transitions
- **Charts** — Visual analytics with Chart.js

---

## 🎨 Color Palette

```css
--bg: #0a0f1a          /* Deep navy background */
--sur: #0d1420         /* Surface background */
--card: #111827        /* Card background */
--bdr: #1e3a5f         /* Border color */
--cyan: #00d4ff        /* Primary accent */
--ok: #00ff88          /* Success green */
--warn: #ffaa00        /* Warning orange */
--err: #ff4757         /* Error red */
--info: #3b82f6        /* Info blue */
--purple: #a855f7      /* Purple accent */
```

---

## 📁 File Structure

```
nexus_cyber/
├── nexus_shared.py      # Shared data layer and utilities
├── nexus_desktop.py     # Desktop application (customtkinter)
├── nexus_web.py         # Web application (Flask)
├── nexus_logo.png       # Cyber-themed logo
├── nexus_data.json      # Data file (auto-created)
└── README.md            # This file
```

---

## 🔧 Configuration

### Clearance Levels
- Public
- Confidential
- Secret
- Top Secret
- TS/SCI

### Employment Types
- Permanent
- Contract
- Probation
- Intern
- Part Time

### Leave Types
- Annual Leave
- Sick Leave
- Certification Study
- Security Conference
- Unpaid Leave
- Other

---

## 🛡️ Security Features

- Password hashing with salt (SHA-256)
- Session-based authentication
- Role-based access control
- Audit logging for all sensitive operations
- CSRF protection via SameSite cookies

---

## 📊 API Endpoints

### Authentication
- `POST /api/login` — Authenticate user
- `POST /api/logout` — Sign out
- `GET /api/me` — Get current user info

### Analysts
- `GET /api/data` — Get all data
- `POST /api/employees` — Add analyst
- `PUT /api/employees/<id>` — Update analyst
- `DELETE /api/employees/<id>` — Delete analyst

### Teams
- `POST /api/departments` — Add team
- `PUT /api/departments/<name>` — Update team
- `DELETE /api/departments/<name>` — Delete team

### Clearance Upgrades
- `POST /api/promotions` — Request upgrade
- `PUT /api/promotions/<id>/<idx>` — Approve/Deny

### Leave
- `POST /api/leave` — Submit leave request
- `PUT /api/leave/<idx>` — Approve/Deny

### System Users
- `POST /api/sysusers` — Create user
- `PUT /api/sysusers/<uname>` — Update user
- `DELETE /api/sysusers/<uname>` — Delete user

### Profile
- `PUT /api/profile` — Update profile
- `POST /api/change-password` — Change password

### Export
- `GET /api/export/employees-csv` — Export analysts CSV
- `GET /api/export/employees-excel` — Export analysts Excel
- `GET /api/export/payroll-csv` — Export compensation CSV
- `GET /api/export/payroll-excel` — Export compensation Excel
- `GET /api/export/audit-csv` — Export audit CSV

---

## 📝 License

This project is provided as-is for demonstration and educational purposes.

---

## 🙏 Credits

**NEXUS CYBER** — Rebranded from Obsidian Corporation HR Management System
- Original author: Obsidian Corporation
- Rebranded by: AI Assistant
- Version: 1.0 (2026)

---

*"Securing the future, one analyst at a time."* 🔒
