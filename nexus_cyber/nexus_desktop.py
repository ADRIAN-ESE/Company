"""
NEXUS CYBER — Desktop Edition v1.0
Cyber Security Workforce Management Platform
CustomTkinter single-file application

pip install customtkinter openpyxl matplotlib pillow
python nexus_desktop.py

Shares nexus_data.json with nexus_web.py.

Default credentials:
  admin / admin123  |  sec_lead / lead123  |  team_lead1 / tl123  |  analyst1 / analyst123
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, csv, io
from datetime import datetime, date, timedelta

from nexus_shared import (
    load_data, save_data, gen_emp_id, audit, notify,
    hash_pw, verify_pw, export_csv_bytes, export_excel_bytes,
    export_audit_csv_bytes,
    ROLE_LEVEL, ROLE_LABEL, ROLE_DEFINITIONS, DEPT_DEFINITIONS,
    get_dept_definition, EMP_FIELDS,
)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL_OK = True
except ImportError:
    MPL_OK = False

# ─── CYBER THEME ──────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Cyber color palette
BG      = "#0a0f1a"      # Deep navy background
SURFACE = "#0d1420"      # Slightly lighter surface
CARD    = "#111827"      # Card background
CARD2   = "#1a2332"      # Secondary card
BORDER  = "#1e3a5f"      # Border color (cyber blue)
CYAN    = "#00d4ff"      # Primary cyan accent
CYAN_L  = "#80ecff"      # Light cyan
CYAN_D  = "#0099cc"      # Dark cyan
OK      = "#00ff88"      # Success green
WARN    = "#ffaa00"      # Warning orange
ERR     = "#ff4757"      # Error red
INFO    = "#3b82f6"      # Info blue
PURPLE  = "#a855f7"      # Purple accent
TX      = "#e2e8f0"      # Primary text
TXM     = "#64748b"      # Muted text
TXD     = "#334155"      # Dark text

# Employment type labels
ET_LABELS = {
    "permanent": "Permanent",
    "contract": "Contract",
    "probation": "Probation",
    "intern": "Intern",
    "part_time": "Part Time",
}

# Leave type labels
LT_LABELS = {
    "annual": "Annual Leave",
    "sick": "Sick Leave",
    "certification": "Certification Study",
    "conference": "Security Conference",
    "unpaid": "Unpaid Leave",
    "other": "Other",
}

# Clearance levels
CLEARANCE_LEVELS = ["Public", "Confidential", "Secret", "Top Secret", "TS/SCI"]

STATUS_COLORS = {"active": OK, "inactive": TXM, "on_leave": WARN}
ROLE_COLORS   = {"admin": CYAN, "security_lead": INFO, "team_lead": WARN, "analyst": PURPLE}


# ─── LOGIN WINDOW ─────────────────────────────────────────────────────────────
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NEXUS CYBER — Secure Access")
        self.geometry("520x640")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.logged_in_user = None
        self._build()

    def _build(self):
        # Logo area
        ctk.CTkLabel(self, text="🔒",
                     font=ctk.CTkFont("Segoe UI", 48),
                     text_color=CYAN).pack(pady=(40, 0))
        
        ctk.CTkLabel(self, text="NEXUS",
                     font=ctk.CTkFont("Consolas", 52, "bold"),
                     text_color=CYAN).pack(pady=(10, 0))
        ctk.CTkLabel(self, text="CYBER",
                     font=ctk.CTkFont("Consolas", 24),
                     text_color=TXM).pack()
        
        # Decorative line
        line_frame = ctk.CTkFrame(self, fg_color="transparent", height=2)
        line_frame.pack(fill="x", padx=80, pady=(10, 5))
        ctk.CTkFrame(line_frame, fg_color=CYAN_D, height=2).pack(fill="x")
        
        ctk.CTkLabel(self, text="Security Workforce Management Platform",
                     font=ctk.CTkFont(size=11),
                     text_color=CYAN_D).pack()

        # Login card
        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=50, pady=30)

        ctk.CTkLabel(card, text="🔐 SECURE PORTAL",
                     font=ctk.CTkFont("Consolas", 12, "bold"),
                     text_color=CYAN).pack(pady=(20, 16))

        for label, attr, show in [("Username", "uvar", None), ("Password", "pvar", "●")]:
            ctk.CTkLabel(card, text=label,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=TXM).pack(anchor="w", padx=24)
            var = tk.StringVar()
            setattr(self, attr, var)
            ctk.CTkEntry(card, textvariable=var, height=40, show=show,
                         fg_color=BG, border_color=BORDER,
                         font=ctk.CTkFont("Consolas", 12)
                         ).pack(fill="x", padx=24, pady=(4, 12))

        self.err_lbl = ctk.CTkLabel(card, text="",
                                    font=ctk.CTkFont(size=11), text_color=ERR)
        self.err_lbl.pack()
        
        ctk.CTkButton(card, text="AUTHENTICATE", height=46,
                      fg_color=CYAN, hover_color=CYAN_L, text_color=BG,
                      font=ctk.CTkFont("Consolas", 16, "bold"),
                      command=self._login).pack(fill="x", padx=24, pady=(4, 24))
        self.bind("<Return>", lambda _: self._login())

        # Security notice
        ctk.CTkLabel(self, text="⚡ Authorized Personnel Only ⚡",
                     font=ctk.CTkFont(size=9),
                     text_color=TXD).pack(pady=(5, 10))

    def _login(self):
        uname = self.uvar.get().strip()
        pw = self.pvar.get()
        if not uname or not pw:
            self.err_lbl.configure(text="Please enter both credentials.")
            return
        data = load_data()
        u = data["system_users"].get(uname)
        if not u or not verify_pw(pw, u.get("password_hash", "")):
            self.err_lbl.configure(text="Authentication failed.")
            return
        audit(data, uname, "Login", uname)
        save_data(data)
        self.logged_in_user = {"username": uname,
                               **{k: v for k, v in u.items() if k != "password_hash"}}
        self.destroy()


# ─── MAIN APP ─────────────────────────────────────────────────────────────────
class NexusApp(ctk.CTk):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.data = load_data()
        self.lvl = ROLE_LEVEL.get(user.get("role", "analyst"), 1)
        self.sel_emp = None
        self.sel_promo = None
        self.sel_leave = None
        self.sel_pay = None

        self.title("NEXUS CYBER — Security Workforce Management v1.0")
        self.geometry("1500x900")
        self.minsize(1200, 720)
        self.configure(fg_color=BG)
        self._fonts()
        self._build()

    def _fonts(self):
        self.F_BRAND = ctk.CTkFont("Consolas", 26, "bold")
        self.F_TITLE = ctk.CTkFont("Consolas", 24, "bold")
        self.F_HEAD = ctk.CTkFont("Consolas", 15, "bold")
        self.F_BODY = ctk.CTkFont("Segoe UI", 13)
        self.F_SMALL = ctk.CTkFont("Segoe UI", 11)
        self.F_MONO = ctk.CTkFont("Consolas", 11)
        self.F_TAG = ctk.CTkFont("Segoe UI", 10, "bold")

    # ── LAYOUT ────────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Logo in header
        logo_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        logo_frame.pack(side="left", padx=(20, 0))
        ctk.CTkLabel(logo_frame, text="🔒", font=ctk.CTkFont(size=24)).pack(side="left")
        ctk.CTkLabel(logo_frame, text="NEXUS", font=self.F_BRAND, text_color=CYAN
                     ).pack(side="left", padx=(4, 2))
        ctk.CTkLabel(logo_frame, text="CYBER",
                     font=ctk.CTkFont("Segoe UI", 10), text_color=TXM
                     ).pack(side="left")

        # Sign out button
        ctk.CTkButton(hdr, text="Sign Out", width=90, height=32,
                      fg_color=ERR, hover_color="#cc0000",
                      font=self.F_SMALL, command=self._logout
                      ).pack(side="right", padx=(4, 20))

        # User info
        rdef = ROLE_DEFINITIONS.get(self.user.get("role", "analyst"), {})
        role_color = ROLE_COLORS.get(self.user.get("role", "analyst"), CYAN_D)
        ctk.CTkLabel(hdr,
                     text=f"{rdef.get('icon', '🔍')}  {self.user.get('full_name', '')}  ·  {ROLE_LABEL.get(self.user.get('role', ''), 'Analyst')}",
                     font=self.F_SMALL,
                     text_color=role_color
                     ).pack(side="right", padx=10)

        # Main body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar
        self._sb = ctk.CTkFrame(body, fg_color=SURFACE, width=260, corner_radius=0)
        self._sb.pack(side="left", fill="y")
        self._sb.pack_propagate(False)
        self._build_sidebar()

        # Content area
        self._content = ctk.CTkFrame(body, fg_color="transparent")
        self._content.pack(side="right", fill="both", expand=True, padx=24, pady=20)

        # Build tabs
        self._tabs: dict = {}
        self._build_tab_dashboard()
        self._build_tab_analysts()
        self._build_tab_teams()
        self._build_tab_clearance()
        self._build_tab_leave()
        if self.lvl >= 3:
            self._build_tab_compensation()
            self._build_tab_audit()
        self._build_tab_roles()
        if self.lvl >= 4:
            self._build_tab_sysusers()
        self._build_tab_profile()
        self._show("Dashboard")

    def _build_sidebar(self):
        def sec(t):
            ctk.CTkLabel(self._sb, text=t,
                         font=ctk.CTkFont("Segoe UI", 9, "bold"),
                         text_color=TXD).pack(anchor="w", padx=20, pady=(16, 6))

        sec("OPERATIONS")
        nav = [
            ("📊", "Dashboard"),
            ("👥", "Analysts"),
            ("🏢", "Teams"),
            ("🔐", "Clearance Upgrades"),
            ("📅", "Leave"),
        ]
        
        if self.lvl >= 3:
            sec("SECURITY OPERATIONS")
            nav += [
                ("💰", "Compensation"),
                ("📋", "Audit Log"),
            ]
        
        sec("SYSTEM")
        nav += [("🔑", "Role Guide")]
        
        if self.lvl >= 4:
            nav += [("🔐", "System Users")]
        
        nav += [("⚙️", "Profile")]

        self._nb: dict = {}
        for icon, name in nav:
            btn = ctk.CTkButton(
                self._sb, text=f"  {icon}  {name}",
                width=230, height=40, anchor="w",
                fg_color="transparent", text_color=TXM,
                hover_color=CARD2, font=self.F_BODY,
                command=lambda n=name: self._show(n))
            btn.pack(pady=2, padx=12)
            self._nb[name] = btn

        # Version info at bottom
        ctk.CTkLabel(self._sb, text="v1.0  Secure Edition",
                     font=ctk.CTkFont("Consolas", 9),
                     text_color=TXD).pack(side="bottom", pady=16)

    def _show(self, name: str):
        for f in self._tabs.values():
            f.pack_forget()
        self._tabs[name].pack(fill="both", expand=True)
        for k, btn in self._nb.items():
            btn.configure(fg_color=(CYAN_D if k == name else "transparent"),
                          text_color=(BG if k == name else TXM))
        
        refresh_map = {
            "Dashboard": self._refresh_dashboard,
            "Analysts": self._refresh_analysts,
            "Teams": self._refresh_teams,
            "Clearance Upgrades": self._refresh_clearance,
            "Leave": self._refresh_leave,
            "Role Guide": self._refresh_roles,
            "Compensation": self._refresh_compensation if self.lvl >= 3 else None,
            "Audit Log": self._refresh_audit if self.lvl >= 3 else None,
            "System Users": self._refresh_sysusers if self.lvl >= 4 else None,
        }
        fn = refresh_map.get(name)
        if fn:
            fn()

    def _reload(self):
        self.data = load_data()

    # ── WIDGET HELPERS ─────────────────────────────────────────────────────────
    def _tab(self, name):
        f = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._tabs[name] = f
        return f

    def _page_title(self, parent, title, subtitle=""):
        h = ctk.CTkFrame(parent, fg_color="transparent")
        h.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(h, text=title, font=self.F_TITLE, text_color=CYAN).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(h, text=subtitle, font=self.F_SMALL, text_color=TXM).pack(anchor="w")

    def _stat_row(self, parent, stats):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 16))
        for label, val, color in stats:
            c = ctk.CTkFrame(row, fg_color=CARD, corner_radius=10,
                             border_width=2, border_color=color)
            c.pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(c, text=str(val),
                         font=ctk.CTkFont("Consolas", 32, "bold"),
                         text_color=color).pack(pady=(14, 2))
            ctk.CTkLabel(c, text=label, font=self.F_SMALL, text_color=TXM).pack(pady=(0, 14))

    def _tree(self, parent, cols, widths=None, height=18):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
        card.pack(fill="both", expand=True)
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("N.Treeview", background=CARD, foreground=TX,
                    fieldbackground=CARD, rowheight=32, font=("Segoe UI", 12))
        s.configure("N.Treeview.Heading", background=SURFACE, foreground=TXM,
                    font=("Segoe UI", 10, "bold"), relief="flat")
        s.map("N.Treeview", background=[("selected", CYAN_D)],
              foreground=[("selected", "#fff")])
        tree = ttk.Treeview(card, columns=cols, show="headings",
                            selectmode="browse", style="N.Treeview", height=height)
        for col in cols:
            w = (widths or {}).get(col, 130)
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=40)
        vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(card, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        card.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)
        return tree

    def _frow(self, parent, label, value, lc=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, width=180, anchor="w",
                     font=self.F_SMALL, text_color=lc or TXM).pack(side="left")
        ctk.CTkLabel(row, text=str(value or "—"), anchor="w",
                     font=self.F_BODY, text_color=TX).pack(side="left", fill="x", expand=True)

    def _sec(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=self.F_HEAD, text_color=CYAN
                     ).pack(anchor="w", pady=(14, 8))

    # ── DASHBOARD ─────────────────────────────────────────────────────────────
    def _build_tab_dashboard(self):
        f = self._tab("Dashboard")
        self._page_title(f, "Security Dashboard", "NEXUS CYBER — Workforce Overview")
        self._d_alerts = ctk.CTkFrame(f, fg_color="transparent")
        self._d_alerts.pack(fill="x")
        self._d_stats = ctk.CTkFrame(f, fg_color="transparent")
        self._d_stats.pack(fill="x")
        
        if MPL_OK:
            self._d_charts = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
            self._d_charts.pack(fill="x", pady=(12, 0))
        
        bot = ctk.CTkFrame(f, fg_color="transparent")
        bot.pack(fill="x", pady=(14, 0))
        
        self._d_exp = ctk.CTkFrame(bot, fg_color=CARD, corner_radius=10)
        self._d_exp.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(self._d_exp, text="⚠️  Contract Expirations (90 days)",
                     font=self.F_HEAD, text_color=WARN).pack(anchor="w", padx=16, pady=(14, 8))
        self._d_exp_inner = ctk.CTkFrame(self._d_exp, fg_color="transparent")
        self._d_exp_inner.pack(fill="x", padx=16, pady=(0, 14))
        
        self._d_aud = ctk.CTkFrame(bot, fg_color=CARD, corner_radius=10)
        self._d_aud.pack(side="right", fill="both", expand=True, padx=(8, 0))
        ctk.CTkLabel(self._d_aud, text="📋  Recent Security Activity",
                     font=self.F_HEAD, text_color=TX).pack(anchor="w", padx=16, pady=(14, 8))
        self._d_aud_tb = ctk.CTkTextbox(self._d_aud, height=200, font=self.F_MONO,
                                         fg_color="transparent", state="disabled")
        self._d_aud_tb.pack(fill="x", padx=16, pady=(0, 14))

    def _refresh_dashboard(self):
        self._reload()
        emps = list(self.data["employees"].values())
        active = sum(1 for e in emps if e.get("status") == "active")
        onleave = sum(1 for e in emps if e.get("status") == "on_leave")
        inactive = sum(1 for e in emps if e.get("status") == "inactive")
        pend_p = sum(len([r for r in e.get("promotion_requests", []) if r["status"] == "pending"]) for e in emps)
        pend_l = len([r for r in self.data.get("leave_requests", []) if r.get("status") == "pending"])
        
        for w in self._d_stats.winfo_children():
            w.destroy()
        
        self._stat_row(self._d_stats, [
            ("Total Analysts", len(emps), INFO),
            ("Active", active, OK),
            ("On Leave", onleave, WARN),
            ("Inactive", inactive, ERR),
            ("Pending Clearance Upgrades", pend_p, CYAN),
            ("Security Teams", len(self.data["departments"]), CYAN_D),
            ("Pending Leave", pend_l, WARN),
        ])
        
        # Contract expirations
        today = date.today()
        d90 = today + timedelta(days=90)
        expiring = [(eid, e) for eid, e in self.data["employees"].items()
                    if e.get("contract_end") and
                    today <= date.fromisoformat(e["contract_end"]) <= d90]
        soon = [x for x in expiring
                if (date.fromisoformat(x[1]["contract_end"]) - today).days <= 30]
        
        for w in self._d_alerts.winfo_children():
            w.destroy()
        
        if soon:
            af = ctk.CTkFrame(self._d_alerts, fg_color="#2a1a0a",
                              corner_radius=8, border_width=1, border_color=WARN)
            af.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(af, text=f"⚠️  {len(soon)} contract(s) expiring within 30 days.",
                         font=self.F_SMALL, text_color=WARN).pack(anchor="w", padx=14, pady=8)
        
        if pend_p:
            af2 = ctk.CTkFrame(self._d_alerts, fg_color="#0a1a2a",
                               corner_radius=8, border_width=1, border_color=CYAN)
            af2.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(af2, text=f"🔐  {pend_p} pending clearance upgrade request(s).",
                         font=self.F_SMALL, text_color=CYAN).pack(anchor="w", padx=14, pady=8)
        
        for w in self._d_exp_inner.winfo_children():
            w.destroy()
        
        if not expiring:
            ctk.CTkLabel(self._d_exp_inner, text="No contracts expiring in 90 days.",
                         font=self.F_SMALL, text_color=TXM).pack(anchor="w")
        else:
            for eid, e in sorted(expiring, key=lambda x: x[1]["contract_end"]):
                days = (date.fromisoformat(e["contract_end"]) - today).days
                col = ERR if days <= 30 else WARN if days <= 60 else TXM
                row = ctk.CTkFrame(self._d_exp_inner, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=e.get("full_name", eid), font=self.F_SMALL,
                             text_color=TX, width=200, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=f"{days}d — {e['contract_end']}",
                             font=self.F_MONO, text_color=col).pack(side="right")
        
        if MPL_OK:
            for w in self._d_charts.winfo_children():
                w.destroy()
            self._draw_charts()
        
        lines = self.data.get("audit_log", [])[:14]
        self._d_aud_tb.configure(state="normal")
        self._d_aud_tb.delete("1.0", "end")
        for a in lines:
            self._d_aud_tb.insert("end", f"  {a['ts']}  {a['user']}  {a['action']}  {a['target']}\n")
        self._d_aud_tb.configure(state="disabled")

    def _draw_charts(self):
        emps = list(self.data["employees"].values())
        GCOLS = [CYAN, INFO, OK, WARN, ERR, PURPLE, "#2dd4bf", "#f472b6"]
        
        dmap = {}
        for e in emps:
            d = e.get("department", "Unknown") or "Unknown"
            dmap[d] = dmap.get(d, 0) + 1
        
        tmap = {}
        for e in emps:
            t = ET_LABELS.get(e.get("employment_type", ""), "Unknown")
            tmap[t] = tmap.get(t, 0) + 1
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 2.8), facecolor=CARD)
        for ax in (ax1, ax2):
            ax.set_facecolor(CARD)
            for sp in ax.spines.values():
                sp.set_edgecolor(BORDER)
        
        if dmap:
            ax1.pie(list(dmap.values()), labels=list(dmap.keys()),
                    colors=GCOLS[:len(dmap)], textprops={"color": TX, "fontsize": 9}, startangle=90)
        ax1.set_title("By Security Team", color=TX, fontsize=10, pad=8)
        
        if tmap:
            ax2.bar(list(tmap.keys()), list(tmap.values()), color=GCOLS[:len(tmap)], edgecolor="none")
        ax2.set_title("Employment Types", color=TX, fontsize=10, pad=8)
        ax2.tick_params(colors=TXM, labelsize=9)
        
        fig.tight_layout(pad=1.5)
        canvas = FigureCanvasTkAgg(fig, master=self._d_charts)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=14, pady=10)
        plt.close(fig)

    # ── ANALYSTS ───────────────────────────────────────────────────────────────
    def _build_tab_analysts(self):
        f = self._tab("Analysts")
        self._page_title(f, "Security Analysts", "Workforce management and records")
        
        tb = ctk.CTkFrame(f, fg_color="transparent")
        tb.pack(fill="x", pady=(0, 10))
        
        self._emp_srch = tk.StringVar()
        self._emp_srch.trace_add("write", lambda *_: self._refresh_analysts())
        ctk.CTkEntry(tb, textvariable=self._emp_srch, width=300, height=38,
                     placeholder_text="🔍  Name, ID, email, team, specialization...",
                     font=self.F_BODY).pack(side="left")
        
        self._emp_dept_var = tk.StringVar(value="All Teams")
        self._emp_dept_menu = ctk.CTkOptionMenu(
            tb, variable=self._emp_dept_var, values=["All Teams"],
            command=lambda _: self._refresh_analysts(), width=180, font=self.F_SMALL)
        self._emp_dept_menu.pack(side="left", padx=10)
        
        self._emp_st_var = tk.StringVar(value="All Status")
        ctk.CTkOptionMenu(tb, variable=self._emp_st_var,
                          values=["All Status", "active", "inactive", "on_leave"],
                          command=lambda _: self._refresh_analysts(),
                          width=130, font=self.F_SMALL).pack(side="left")
        
        if self.lvl >= 3:
            for txt, cmd, col in [
                ("+ Add Analyst", lambda: self._analyst_dialog(), CYAN),
                ("📥 Import", self._import_analysts, CARD2),
                ("📤 Excel", self._export_xl, CYAN_D),
                ("📤 CSV", self._export_csv, CYAN_D),
            ]:
                ctk.CTkButton(tb, text=txt, width=100, height=38,
                              fg_color=col, hover_color=CYAN_L if col == CYAN else BORDER,
                              text_color=BG if col in (CYAN, CYAN_D) else TX,
                              font=self.F_SMALL, command=cmd).pack(side="right", padx=3)
        
        self._emp_cnt = ctk.CTkLabel(f, text="", font=self.F_SMALL, text_color=TXM)
        self._emp_cnt.pack(anchor="w", pady=(0, 6))
        
        cols = ("ID", "Name", "Phone", "Team", "Specialization", "Clearance", "Type", "Status", "Start Date")
        widths = {"ID": 130, "Name": 170, "Phone": 130, "Team": 150,
                  "Specialization": 160, "Clearance": 100, "Type": 100, "Status": 90, "Start Date": 110}
        self._emp_tree = self._tree(f, cols, widths)
        self._emp_tree.bind("<Double-1>", lambda _: self._analyst_view(next(iter(self._emp_tree.selection()), None)))
        self._emp_tree.bind("<<TreeviewSelect>>",
                            lambda _: setattr(self, "sel_emp", next(iter(self._emp_tree.selection()), None)))
        
        if self.lvl >= 3:
            act = ctk.CTkFrame(f, fg_color="transparent")
            act.pack(fill="x", pady=10)
            ctk.CTkButton(act, text="✏️ Edit", width=120, height=36, fg_color=INFO,
                          font=self.F_SMALL, command=lambda: self._analyst_dialog(self.sel_emp)).pack(side="left", padx=4)
            ctk.CTkButton(act, text="🗑 Delete", width=120, height=36, fg_color=ERR,
                          font=self.F_SMALL, command=self._del_analyst).pack(side="left", padx=4)
            ctk.CTkButton(act, text="👁 View Details", width=140, height=36, fg_color=CYAN_D,
                          font=self.F_SMALL, command=lambda: self._analyst_view(self.sel_emp)).pack(side="left", padx=4)

    def _refresh_analysts(self):
        self._reload()
        depts = ["All Teams"] + list(self.data["departments"].keys())
        self._emp_dept_menu.configure(values=depts)
        
        q = self._emp_srch.get().lower()
        fd = self._emp_dept_var.get()
        fs = self._emp_st_var.get()
        
        for row in self._emp_tree.get_children():
            self._emp_tree.delete(row)
        
        shown = 0
        for eid, e in self.data["employees"].items():
            if self.lvl < 2 and eid != self.user.get("emp_id"):
                continue
            if fd not in ("All Teams", "") and e.get("department") != fd:
                continue
            if fs not in ("All Status", "") and e.get("status") != fs:
                continue
            if q and not any(q in str(v).lower() for v in
                             [eid, e.get("full_name", ""), e.get("email", ""),
                              e.get("department", ""), e.get("specialization", ""), e.get("phone", "")]):
                continue
            
            self._emp_tree.insert("", "end", iid=eid, values=(
                eid, e.get("full_name", ""), e.get("phone", "—"),
                e.get("department", ""), e.get("specialization", ""),
                e.get("clearance_level", "—"),
                ET_LABELS.get(e.get("employment_type", ""), e.get("employment_type", "")),
                e.get("status", ""), e.get("start_date", e.get("date_added", ""))
            ))
            shown += 1
        
        self._emp_cnt.configure(text=f"Showing {shown} of {len(self.data['employees'])} analysts")

    def _analyst_view(self, eid):
        if not eid:
            messagebox.showwarning("No selection", "Select an analyst first.")
            return
        e = self.data["employees"].get(eid, {})
        
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Analyst — {eid}")
        dlg.geometry("560x680")
        dlg.grab_set()
        dlg.configure(fg_color=BG)
        
        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=22, pady=18)
        
        # Header
        hb = ctk.CTkFrame(sf, fg_color=CARD, corner_radius=10)
        hb.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(hb, text=e.get("full_name", ""),
                     font=ctk.CTkFont("Consolas", 18, "bold"), text_color=CYAN
                     ).pack(anchor="w", padx=16, pady=(16, 0))
        ctk.CTkLabel(hb, text=f"{e.get('specialization', '—')}  ·  {e.get('clearance_level', '—')}",
                     font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=16)
        ctk.CTkLabel(hb, text=eid, font=self.F_MONO, text_color=CYAN_D
                     ).pack(anchor="w", padx=16, pady=(2, 16))
        
        # Info rows
        for k, v in [
            ("Email", e.get("email", "")),
            ("Phone", e.get("phone", "")),
            ("Security Team", e.get("department", "")),
            ("Employment Type", ET_LABELS.get(e.get("employment_type", ""), e.get("employment_type", ""))),
            ("Status", e.get("status", "")),
            ("Location", e.get("location", "")),
            ("Age", e.get("age", "")),
            ("Start Date", e.get("start_date", "")),
            ("Contract End", e.get("contract_end", "")),
            ("Date Added", e.get("date_added", "")),
            ("Team Lead ID", e.get("team_lead_id", "")),
            ("Emergency Contact", e.get("emergency_contact", ""))
        ]:
            self._frow(sf, k, v)
        
        if self.lvl >= 3 and e.get("salary"):
            self._frow(sf, "Compensation", f"{e.get('salary_currency', 'USD')} {float(e['salary']):,.0f}")
        
        # Certifications
        certs = e.get("certifications", [])
        if certs:
            ctk.CTkLabel(sf, text="Certifications", font=self.F_SMALL, text_color=TXM).pack(anchor="w", pady=(10, 4))
            sw = ctk.CTkFrame(sf, fg_color="transparent")
            sw.pack(fill="x")
            for c in certs:
                ctk.CTkLabel(sw, text=c, font=self.F_TAG, fg_color=CARD2,
                             corner_radius=20, text_color=CYAN, padx=10, pady=3
                             ).pack(side="left", padx=4, pady=3)
        
        ctk.CTkButton(dlg, text="Close", command=dlg.destroy,
                      fg_color=CYAN_D, height=38).pack(pady=12)

    def _analyst_dialog(self, eid=None):
        if eid and eid not in self.data["employees"]:
            messagebox.showwarning("No selection", "Select an analyst first.")
            return
        
        e = self.data["employees"].get(eid, {}) if eid else {}
        
        dlg = ctk.CTkToplevel(self)
        dlg.title("Edit Analyst" if eid else "Add Analyst")
        dlg.geometry("660x840")
        dlg.grab_set()
        dlg.configure(fg_color=BG)
        
        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=24, pady=16)
        
        fields = [
            ("Full Name *", "full_name", None),
            ("Email", "email", None),
            ("Phone", "phone", None),
            ("Security Team", "department", list(self.data["departments"].keys())),
            ("Specialization", "specialization", None),
            ("Clearance Level", "clearance_level", CLEARANCE_LEVELS),
            ("Age", "age", None),
            ("Location", "location", None),
            ("Employment Type", "employment_type", list(ET_LABELS.keys())),
            ("Status", "status", ["active", "inactive", "on_leave"]),
            ("Start Date (YYYY-MM-DD)", "start_date", None),
            ("Contract End (YYYY-MM-DD)", "contract_end", None),
            ("Salary", "salary", None),
            ("Currency", "salary_currency", ["USD", "EUR", "GBP", "CAD", "AUD"]),
            ("Team Lead ID (optional)", "team_lead_id", None),
            ("Emergency Contact", "emergency_contact", None),
        ]
        
        vars_ = {}
        for label, key, opts in fields:
            ctk.CTkLabel(sf, text=label, anchor="w", font=self.F_SMALL,
                         text_color=TXM).pack(anchor="w", pady=(8, 2))
            var = tk.StringVar(value=str(e.get(key, "") or ""))
            if opts:
                ctk.CTkOptionMenu(sf, variable=var, values=opts or [""],
                                  font=self.F_BODY).pack(fill="x", pady=(0, 4))
            else:
                ctk.CTkEntry(sf, textvariable=var, height=36,
                             font=self.F_BODY).pack(fill="x", pady=(0, 4))
            vars_[key] = var
        
        ctk.CTkLabel(sf, text="Certifications (comma-separated)", anchor="w",
                     font=self.F_SMALL, text_color=TXM).pack(anchor="w", pady=(8, 2))
        sk_var = tk.StringVar(value=", ".join(e.get("certifications", []) if isinstance(e.get("certifications"), list) else []))
        ctk.CTkEntry(sf, textvariable=sk_var, height=36,
                     placeholder_text="CISSP, CEH, OSCP, Security+...",
                     font=self.F_BODY).pack(fill="x", pady=(0, 4))

        def _save():
            fn = vars_["full_name"].get().strip()
            if not fn:
                messagebox.showerror("Error", "Full name required.")
                return
            self._reload()
            eid_ = eid or gen_emp_id(self.data)
            emp = {k: v.get().strip() for k, v in vars_.items()}
            raw = sk_var.get().strip()
            emp["certifications"] = [s.strip() for s in raw.split(",") if s.strip()] if raw else []
            emp["date_added"] = e.get("date_added", datetime.now().strftime("%Y-%m-%d"))
            emp["promotion_requests"] = e.get("promotion_requests", [])
            emp["photo"] = e.get("photo")
            if not emp.get("team_lead_id"):
                emp["team_lead_id"] = None
            self.data["employees"][eid_] = emp
            audit(self.data, self.user["username"],
                  "Updated analyst" if eid else "Added analyst", eid_, fn)
            if not eid:
                notify(self.data, "success", f"New analyst: {fn} ({eid_})")
            save_data(self.data)
            dlg.destroy()
            self._refresh_analysts()
            messagebox.showinfo("Saved", f"Analyst {eid_} saved.")

        ctk.CTkButton(dlg, text="💾 Save Analyst",
                      fg_color=CYAN, hover_color=CYAN_L, text_color=BG,
                      height=44, font=self.F_HEAD, command=_save
                      ).pack(pady=16, fill="x", padx=24)

    def _del_analyst(self):
        sel = self._emp_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select an analyst.")
            return
        eid = sel[0]
        if not messagebox.askyesno("Confirm", f"Delete {eid}? Cannot be undone."):
            return
        self._reload()
        name = self.data["employees"].get(eid, {}).get("full_name", "")
        del self.data["employees"][eid]
        audit(self.data, self.user["username"], "Deleted analyst", eid, name)
        save_data(self.data)
        self._refresh_analysts()
        messagebox.showinfo("Deleted", f"{eid} deleted.")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            initialfile="nexus_analysts.csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        self._reload()
        with open(path, "wb") as f:
            f.write(export_csv_bytes(self.data["employees"]))
        messagebox.showinfo("Exported", f"Saved → {path}")

    def _export_xl(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            initialfile="nexus_analysts.xlsx",
                                            filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        b = export_excel_bytes(self.data["employees"])
        if not b:
            messagebox.showerror("Error", "pip install openpyxl")
            return
        with open(path, "wb") as f:
            f.write(b)
        messagebox.showinfo("Exported", f"Saved → {path}")

    def _import_analysts(self):
        path = filedialog.askopenfilename(filetypes=[("JSON/CSV", "*.json *.csv")])
        if not path:
            return
        self._reload()
        count = 0
        try:
            if path.lower().endswith(".json"):
                with open(path) as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    for eid, emp in raw.items():
                        emp.setdefault("promotion_requests", [])
                        self.data["employees"][eid] = emp
                        count += 1
                elif isinstance(raw, list):
                    for emp in raw:
                        eid = emp.pop("id", None) or gen_emp_id(self.data)
                        emp.setdefault("promotion_requests", [])
                        self.data["employees"][eid] = emp
                        count += 1
            elif path.lower().endswith(".csv"):
                with open(path, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        eid = row.pop("id", None) or gen_emp_id(self.data)
                        row.setdefault("promotion_requests", [])
                        if "certifications" in row and isinstance(row["certifications"], str):
                            row["certifications"] = [s.strip() for s in row["certifications"].split(",") if s.strip()]
                        self.data["employees"][eid] = dict(row)
                        count += 1
            audit(self.data, self.user["username"], "Imported analysts", f"count={count}")
            save_data(self.data)
            self._refresh_analysts()
            messagebox.showinfo("Imported", f"Imported {count} analysts.")
        except Exception as exc:
            messagebox.showerror("Import Error", str(exc))

    # ── TEAMS (DEPARTMENTS) ────────────────────────────────────────────────────
    def _build_tab_teams(self):
        f = self._tab("Teams")
        self._page_title(f, "Security Teams", "Organizational structure and responsibilities")
        
        if self.lvl >= 3:
            tb = ctk.CTkFrame(f, fg_color="transparent")
            tb.pack(fill="x", pady=(0, 12))
            ctk.CTkButton(tb, text="+ Add Security Team", fg_color=CYAN, hover_color=CYAN_L,
                          text_color=BG, height=38, width=180, font=self.F_SMALL,
                          command=lambda: self._team_dialog()).pack(side="right")
        
        cols = ("Team", "Purpose / Description", "Lead ID", "Analysts", "KPIs")
        widths = {"Team": 160, "Purpose / Description": 320, "Lead ID": 130, "Analysts": 90, "KPIs": 240}
        self._dept_tree = self._tree(f, cols, widths)
        self._dept_tree.bind("<Double-1>", lambda _: self._team_view(next(iter(self._dept_tree.selection()), None)))
        
        if self.lvl >= 3:
            act = ctk.CTkFrame(f, fg_color="transparent")
            act.pack(fill="x", pady=10)
            ctk.CTkButton(act, text="✏️ Edit", width=120, height=36, fg_color=INFO,
                          font=self.F_SMALL, command=self._edit_team).pack(side="left", padx=4)
            ctk.CTkButton(act, text="🗑 Delete", width=120, height=36, fg_color=ERR,
                          font=self.F_SMALL, command=self._del_team).pack(side="left", padx=4)
        
        ctk.CTkButton(f, text="👁 View Details", width=140, height=36, fg_color=CYAN_D, font=self.F_SMALL,
                      command=lambda: self._team_view(next(iter(self._dept_tree.selection()), None))
                      ).pack(anchor="w", padx=4, pady=6)

    def _refresh_teams(self):
        self._reload()
        for row in self._dept_tree.get_children():
            self._dept_tree.delete(row)
        
        for name, d in self.data["departments"].items():
            cnt = sum(1 for e in self.data["employees"].values() if e.get("department") == name)
            ddef = get_dept_definition(name)
            kpis = ", ".join(ddef.get("kpis", []))
            self._dept_tree.insert("", "end", iid=name, values=(
                f"{ddef.get('icon', '🔒')}  {name}",
                d.get("description", "") or ddef.get("purpose", ""),
                d.get("head_id", "") or "—", cnt, kpis))

    def _team_view(self, name):
        if not name:
            messagebox.showwarning("No selection", "Select a team.")
            return
        
        d = self.data["departments"].get(name, {})
        ddef = get_dept_definition(name)
        emps = [(eid, e) for eid, e in self.data["employees"].items() if e.get("department") == name]
        head = self.data["employees"].get(d.get("head_id", ""), {})
        
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Team — {name}")
        dlg.geometry("600x680")
        dlg.grab_set()
        dlg.configure(fg_color=BG)
        
        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=22, pady=18)
        
        ctk.CTkLabel(sf, text=f"{ddef.get('icon', '🔒')}  {name}",
                     font=ctk.CTkFont("Consolas", 20, "bold"), text_color=CYAN).pack(anchor="w", pady=(0, 6))
        
        pc = ctk.CTkFrame(sf, fg_color=CARD2, corner_radius=8)
        pc.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(pc, text=ddef.get("purpose", d.get("description", "")),
                     font=self.F_SMALL, text_color=TXM, wraplength=500, justify="left", anchor="w"
                     ).pack(anchor="w", padx=16, pady=12)
        
        self._sec(sf, "Key Responsibilities")
        for r in ddef.get("responsibilities", []):
            row = ctk.CTkFrame(sf, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text="→", width=24, font=self.F_MONO, text_color=CYAN).pack(side="left")
            ctk.CTkLabel(row, text=r, font=self.F_SMALL, text_color=TX, anchor="w").pack(side="left", fill="x", expand=True)
        
        if ddef.get("kpis"):
            self._sec(sf, "Performance Indicators")
            kr = ctk.CTkFrame(sf, fg_color="transparent")
            kr.pack(fill="x")
            for k in ddef["kpis"]:
                ctk.CTkLabel(kr, text=k, font=self.F_TAG, fg_color=CARD2, corner_radius=20,
                             text_color=CYAN, padx=10, pady=3).pack(side="left", padx=5, pady=3)
        
        self._sec(sf, "Team Lead")
        if head:
            self._frow(sf, "Name", head.get("full_name", ""))
            self._frow(sf, "Specialization", head.get("specialization", ""))
        else:
            ctk.CTkLabel(sf, text="No lead assigned.", font=self.F_SMALL, text_color=TXM).pack(anchor="w")
        
        self._sec(sf, f"Team Members ({len(emps)})")
        for eid, e in emps[:8]:
            row = ctk.CTkFrame(sf, fg_color=CARD2, corner_radius=6)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=e.get("full_name", ""), font=self.F_BODY, text_color=TX).pack(side="left", padx=12, pady=5)
            ctk.CTkLabel(row, text=e.get("specialization", ""), font=self.F_SMALL, text_color=TXM).pack(side="left")
            ctk.CTkLabel(row, text=e.get("status", ""), font=self.F_SMALL,
                         text_color=STATUS_COLORS.get(e.get("status", ""), TXM)).pack(side="right", padx=12)
        
        if len(emps) > 8:
            ctk.CTkLabel(sf, text=f"+{len(emps) - 8} more", font=self.F_SMALL, text_color=TXM).pack(anchor="w", pady=3)
        
        ctk.CTkButton(dlg, text="Close", command=dlg.destroy, fg_color=CYAN_D, height=38).pack(pady=12)

    def _team_dialog(self, name=None):
        d = self.data["departments"].get(name, {}) if name else {}
        
        dlg = ctk.CTkToplevel(self)
        dlg.title("Edit Security Team" if name else "Add Security Team")
        dlg.geometry("500x360")
        dlg.grab_set()
        dlg.configure(fg_color=BG)
        
        nm_v = tk.StringVar(value=name or "")
        ds_v = tk.StringVar(value=d.get("description", ""))
        hd_v = tk.StringVar(value=d.get("head_id", "") or "")
        
        for label, var in [
            ("Team Name *", nm_v),
            ("Description", ds_v),
            ("Lead Analyst ID (optional)", hd_v)
        ]:
            ctk.CTkLabel(dlg, text=label, font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=24, pady=(12, 2))
            ctk.CTkEntry(dlg, textvariable=var, height=36, font=self.F_BODY).pack(fill="x", padx=24)
        
        def _save():
            nn = nm_v.get().strip()
            if not nn:
                messagebox.showerror("Error", "Name required.")
                return
            self._reload()
            dept = {"description": ds_v.get().strip(), "head_id": hd_v.get().strip() or None}
            if name and name != nn:
                del self.data["departments"][name]
                for e in self.data["employees"].values():
                    if e.get("department") == name:
                        e["department"] = nn
            self.data["departments"][nn] = dept
            audit(self.data, self.user["username"], "Saved team", nn)
            save_data(self.data)
            dlg.destroy()
            self._refresh_teams()
            messagebox.showinfo("Saved", f"Team '{nn}' saved.")
        
        ctk.CTkButton(dlg, text="💾 Save", fg_color=CYAN, hover_color=CYAN_L,
                      text_color=BG, height=42, command=_save).pack(pady=18, padx=24, fill="x")

    def _edit_team(self):
        sel = self._dept_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a team.")
            return
        self._team_dialog(sel[0])

    def _del_team(self):
        sel = self._dept_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a team.")
            return
        name = sel[0]
        if not messagebox.askyesno("Confirm", f"Delete team '{name}'?"):
            return
        self._reload()
        del self.data["departments"][name]
        audit(self.data, self.user["username"], "Deleted team", name)
        save_data(self.data)
        self._refresh_teams()

    # ── CLEARANCE UPGRADES (PROMOTIONS) ────────────────────────────────────────
    def _build_tab_clearance(self):
        f = self._tab("Clearance Upgrades")
        self._page_title(f, "Clearance Upgrades", "Security clearance advancement workflow")
        
        card = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
        card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(card, text="Submit Clearance Upgrade Request", font=self.F_HEAD, text_color=CYAN
                     ).pack(anchor="w", padx=18, pady=(16, 10))
        
        r1 = ctk.CTkFrame(card, fg_color="transparent")
        r1.pack(fill="x", padx=18, pady=(0, 8))
        self._p_eid = tk.StringVar()
        self._p_clearance = tk.StringVar()
        
        ctk.CTkLabel(r1, text="Analyst ID:", font=self.F_SMALL, text_color=TXM).pack(side="left")
        ctk.CTkEntry(r1, textvariable=self._p_eid, width=180, height=36,
                     placeholder_text="NXS-2026-0001", font=self.F_MONO).pack(side="left", padx=(8, 16))
        ctk.CTkLabel(r1, text="Requested Clearance:", font=self.F_SMALL, text_color=TXM).pack(side="left")
        ctk.CTkOptionMenu(r1, variable=self._p_clearance, values=CLEARANCE_LEVELS,
                          width=160, font=self.F_BODY).pack(side="left", padx=8)
        
        r2 = ctk.CTkFrame(card, fg_color="transparent")
        r2.pack(fill="x", padx=18, pady=(0, 16))
        self._p_notes = tk.StringVar()
        ctk.CTkLabel(r2, text="Justification:", font=self.F_SMALL, text_color=TXM).pack(side="left")
        ctk.CTkEntry(r2, textvariable=self._p_notes, width=420, height=36, font=self.F_BODY).pack(side="left", padx=8)
        ctk.CTkButton(r2, text="Submit", width=100, height=36, fg_color=CYAN, hover_color=CYAN_L,
                      text_color=BG, command=self._sub_clearance).pack(side="left", padx=8)
        
        cols = ("Analyst ID", "Name", "Current Clearance", "Requested Clearance", "Justification", "Date", "Status", "Resolved By")
        widths = {"Analyst ID": 120, "Name": 160, "Current Clearance": 130, "Requested Clearance": 140,
                  "Justification": 200, "Date": 100, "Status": 100, "Resolved By": 120}
        self._promo_tree = self._tree(f, cols, widths)
        self._promo_tree.bind("<<TreeviewSelect>>", lambda _: self._on_clearance_sel())
        
        if self.lvl >= 3:
            act = ctk.CTkFrame(f, fg_color="transparent")
            act.pack(fill="x", pady=10)
            ctk.CTkButton(act, text="✅ Approve", fg_color=OK, hover_color="#00cc6a", width=130, height=38,
                          command=lambda: self._res_clearance("approved")).pack(side="left", padx=4)
            ctk.CTkButton(act, text="❌ Deny", fg_color=ERR, hover_color="#cc0000", width=130, height=38,
                          command=lambda: self._res_clearance("denied")).pack(side="left", padx=4)

    def _refresh_clearance(self):
        self._reload()
        for row in self._promo_tree.get_children():
            self._promo_tree.delete(row)
        
        for eid, e in self.data["employees"].items():
            for i, req in enumerate(e.get("promotion_requests", [])):
                self._promo_tree.insert("", "end", iid=f"{eid}::{i}", values=(
                    eid, e.get("full_name", ""), req.get("current_role", ""),
                    req.get("requested_role", ""), (req.get("notes", "") or "")[:40],
                    req.get("date", ""), req.get("status", "").capitalize(),
                    req.get("resolved_by", "") or "—"))

    def _on_clearance_sel(self):
        sel = self._promo_tree.selection()
        self.sel_promo = sel[0] if sel else None

    def _sub_clearance(self):
        eid = self._p_eid.get().strip()
        clearance = self._p_clearance.get()
        notes = self._p_notes.get().strip()
        
        if not eid or not clearance:
            messagebox.showerror("Error", "Analyst ID and clearance level required.")
            return
        
        self._reload()
        if eid not in self.data["employees"]:
            messagebox.showerror("Not Found", f"'{eid}' not found.")
            return
        
        e = self.data["employees"][eid]
        req = {
            "requested_role": clearance,
            "current_role": e.get("clearance_level", ""),
            "notes": notes,
            "status": "pending",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "submitted_by": self.user["username"],
            "resolved_by": None,
            "resolved_at": None
        }
        e.setdefault("promotion_requests", []).append(req)
        audit(self.data, self.user["username"], "Clearance upgrade request", eid, f"→ {clearance}")
        notify(self.data, "warning", f"Clearance request: {e.get('full_name', eid)} → {clearance}")
        save_data(self.data)
        self._p_eid.set("")
        self._p_clearance.set("")
        self._p_notes.set("")
        self._refresh_clearance()
        messagebox.showinfo("Submitted", "Clearance upgrade request submitted.")

    def _res_clearance(self, resolution):
        if not self.sel_promo:
            messagebox.showwarning("No selection", "Select a request.")
            return
        
        eid, idx_s = self.sel_promo.split("::")
        self._reload()
        req = self.data["employees"][eid]["promotion_requests"][int(idx_s)]
        
        if req["status"] != "pending":
            messagebox.showwarning("Already Resolved", "Already resolved.")
            return
        
        req["status"] = resolution
        req["resolved_by"] = self.user["username"]
        req["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if resolution == "approved":
            self.data["employees"][eid]["clearance_level"] = req["requested_role"]
        
        audit(self.data, self.user["username"], f"Clearance {resolution}", eid, req["requested_role"])
        save_data(self.data)
        self._refresh_clearance()
        messagebox.showinfo("Done", f"Clearance upgrade {resolution}.")

    # ── LEAVE ──────────────────────────────────────────────────────────────────
    def _build_tab_leave(self):
        f = self._tab("Leave")
        self._page_title(f, "Leave Management", "Absence tracking and approval")
        
        card = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
        card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(card, text="Submit Leave Request", font=self.F_HEAD, text_color=CYAN
                     ).pack(anchor="w", padx=18, pady=(16, 10))
        
        sf = ctk.CTkFrame(card, fg_color="transparent")
        sf.pack(fill="x", padx=18, pady=(0, 16))
        
        self._lv_eid = tk.StringVar()
        self._lv_type = tk.StringVar(value="annual")
        self._lv_start = tk.StringVar()
        self._lv_end = tk.StringVar()
        self._lv_notes = tk.StringVar()
        
        r1 = ctk.CTkFrame(sf, fg_color="transparent")
        r1.pack(fill="x", pady=4)
        
        if self.lvl >= 3:
            ctk.CTkLabel(r1, text="Analyst ID:", font=self.F_SMALL, text_color=TXM, width=100).pack(side="left")
            ctk.CTkEntry(r1, textvariable=self._lv_eid, width=180, height=34,
                         placeholder_text="NXS-2026-0001 or blank=self", font=self.F_MONO).pack(side="left", padx=(6, 18))
        
        ctk.CTkLabel(r1, text="Type:", font=self.F_SMALL, text_color=TXM).pack(side="left")
        ctk.CTkOptionMenu(r1, variable=self._lv_type, values=list(LT_LABELS.keys()),
                          width=180, font=self.F_SMALL).pack(side="left", padx=6)
        
        r2 = ctk.CTkFrame(sf, fg_color="transparent")
        r2.pack(fill="x", pady=4)
        for lbl, var, ph in [("Start:", self._lv_start, "YYYY-MM-DD"), ("End:", self._lv_end, "YYYY-MM-DD")]:
            ctk.CTkLabel(r2, text=lbl, font=self.F_SMALL, text_color=TXM, width=50).pack(side="left")
            ctk.CTkEntry(r2, textvariable=var, width=140, height=34, placeholder_text=ph,
                         font=self.F_MONO).pack(side="left", padx=(6, 16))
        
        r3 = ctk.CTkFrame(sf, fg_color="transparent")
        r3.pack(fill="x", pady=4)
        ctk.CTkLabel(r3, text="Notes:", font=self.F_SMALL, text_color=TXM, width=60).pack(side="left")
        ctk.CTkEntry(r3, textvariable=self._lv_notes, width=440, height=34, font=self.F_BODY).pack(side="left", padx=6)
        ctk.CTkButton(r3, text="Submit Request", fg_color=CYAN, hover_color=CYAN_L, text_color=BG,
                      height=34, command=self._sub_leave).pack(side="left", padx=12)
        
        cols = ("Analyst ID", "Name", "Type", "From", "To", "Days", "Notes", "Status", "Resolved By")
        widths = {"Analyst ID": 120, "Name": 160, "Type": 140, "From": 100, "To": 100,
                  "Days": 60, "Notes": 180, "Status": 100, "Resolved By": 120}
        self._leave_tree = self._tree(f, cols, widths)
        self._leave_tree.bind("<<TreeviewSelect>>", lambda _: self._on_leave_sel())
        
        if self.lvl >= 3:
            act = ctk.CTkFrame(f, fg_color="transparent")
            act.pack(fill="x", pady=10)
            ctk.CTkButton(act, text="✅ Approve", fg_color=OK, hover_color="#00cc6a", width=130, height=38,
                          command=lambda: self._res_leave("approved")).pack(side="left", padx=4)
            ctk.CTkButton(act, text="❌ Deny", fg_color=ERR, hover_color="#cc0000", width=130, height=38,
                          command=lambda: self._res_leave("denied")).pack(side="left", padx=4)

    def _refresh_leave(self):
        self._reload()
        for row in self._leave_tree.get_children():
            self._leave_tree.delete(row)
        
        for i, req in enumerate(self.data.get("leave_requests", [])):
            if self.lvl < 3 and req.get("emp_id") != self.user.get("emp_id"):
                continue
            e = self.data["employees"].get(req.get("emp_id", ""), {})
            s = req.get("start_date", "")
            e2 = req.get("end_date", "")
            try:
                days = str((datetime.strptime(e2, "%Y-%m-%d") - datetime.strptime(s, "%Y-%m-%d")).days + 1)
            except:
                days = "—"
            
            self._leave_tree.insert("", "end", iid=str(i), values=(
                req.get("emp_id", ""), e.get("full_name", ""),
                LT_LABELS.get(req.get("leave_type", ""), req.get("leave_type", "")),
                s, e2, days, (req.get("notes", "") or "")[:30],
                req.get("status", "").capitalize(), req.get("resolved_by", "") or "—"))

    def _on_leave_sel(self):
        sel = self._leave_tree.selection()
        self.sel_leave = int(sel[0]) if sel else None

    def _sub_leave(self):
        eid = self._lv_eid.get().strip() or self.user.get("emp_id", "")
        ltype = self._lv_type.get()
        s = self._lv_start.get().strip()
        e2 = self._lv_end.get().strip()
        notes = self._lv_notes.get().strip()
        
        if not s or not e2:
            messagebox.showerror("Error", "Start and end dates required.")
            return
        if not eid:
            messagebox.showerror("Error", "No analyst ID found.")
            return
        
        self._reload()
        if eid not in self.data["employees"]:
            messagebox.showerror("Error", f"'{eid}' not found.")
            return
        
        req = {
            "emp_id": eid,
            "leave_type": ltype,
            "start_date": s,
            "end_date": e2,
            "notes": notes,
            "status": "pending",
            "submitted_by": self.user["username"],
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "resolved_by": None
        }
        self.data.setdefault("leave_requests", []).append(req)
        name = self.data["employees"][eid].get("full_name", eid)
        audit(self.data, self.user["username"], "Leave submitted", eid, ltype)
        notify(self.data, "info", f"Leave request: {name} — {ltype} ({s} to {e2})")
        save_data(self.data)
        self._lv_eid.set("")
        self._lv_start.set("")
        self._lv_end.set("")
        self._lv_notes.set("")
        self._refresh_leave()
        messagebox.showinfo("Submitted", "Leave request submitted.")

    def _res_leave(self, resolution):
        if self.sel_leave is None:
            messagebox.showwarning("No selection", "Select a request.")
            return
        
        self._reload()
        reqs = self.data.get("leave_requests", [])
        if self.sel_leave >= len(reqs):
            return
        
        req = reqs[self.sel_leave]
        if req["status"] != "pending":
            messagebox.showwarning("Already Resolved", "Already resolved.")
            return
        
        req["status"] = resolution
        req["resolved_by"] = self.user["username"]
        req["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if resolution == "approved":
            eid = req.get("emp_id", "")
            if eid in self.data["employees"]:
                self.data["employees"][eid]["status"] = "on_leave"
        
        audit(self.data, self.user["username"], f"Leave {resolution}", req.get("emp_id", ""), req.get("leave_type", ""))
        save_data(self.data)
        self.sel_leave = None
        self._refresh_leave()
        messagebox.showinfo("Done", f"Leave {resolution}.")

    # ── COMPENSATION (PAYROLL) ─────────────────────────────────────────────────
    def _build_tab_compensation(self):
        f = self._tab("Compensation")
        self._page_title(f, "Compensation & Salary", "Salary management — Security Leads & Admin only")
        
        tb = ctk.CTkFrame(f, fg_color="transparent")
        tb.pack(fill="x", pady=(0, 10))
        
        self._pr_srch = tk.StringVar()
        self._pr_srch.trace_add("write", lambda *_: self._refresh_compensation())
        ctk.CTkEntry(tb, textvariable=self._pr_srch, width=300, height=38,
                     placeholder_text="🔍  Search...", font=self.F_BODY).pack(side="left")
        
        ctk.CTkButton(tb, text="📤 Excel", fg_color=CYAN_D, width=100, height=38,
                      command=self._export_pay_xl).pack(side="right", padx=4)
        ctk.CTkButton(tb, text="📤 CSV", fg_color=CYAN_D, width=90, height=38,
                      command=self._export_pay_csv).pack(side="right", padx=4)
        
        self._pr_stats = ctk.CTkFrame(f, fg_color="transparent")
        self._pr_stats.pack(fill="x", pady=(0, 10))
        
        self._pr_dept = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
        self._pr_dept.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(self._pr_dept, text="USD Compensation by Security Team", font=self.F_HEAD, text_color=CYAN
                     ).pack(anchor="w", padx=16, pady=(14, 6))
        self._pr_dept_inner = ctk.CTkFrame(self._pr_dept, fg_color="transparent")
        self._pr_dept_inner.pack(fill="x", padx=16, pady=(0, 14))
        
        cols = ("ID", "Name", "Team", "Specialization", "Clearance", "Salary", "Currency", "Type")
        widths = {"ID": 130, "Name": 170, "Team": 150, "Specialization": 160, "Clearance": 100,
                  "Salary": 120, "Currency": 80, "Type": 120}
        self._pay_tree = self._tree(f, cols, widths)
        self._pay_tree.bind("<Double-1>", lambda _: self._pay_dialog(next(iter(self._pay_tree.selection()), None)))
        
        act = ctk.CTkFrame(f, fg_color="transparent")
        act.pack(fill="x", pady=10)
        ctk.CTkButton(act, text="✏️ Edit Salary", fg_color=INFO, width=140, height=38,
                      command=self._pay_dialog).pack(side="left")

    def _refresh_compensation(self):
        self._reload()
        q = self._pr_srch.get().lower()
        
        rows = [(eid, e) for eid, e in self.data["employees"].items()
                if not q or any(q in str(v).lower() for v in [eid, e.get("full_name", ""), e.get("department", "")])]
        
        tot_usd = sum(float(e.get("salary", "0") or 0) for _, e in rows if e.get("salary_currency") == "USD")
        w_sal = sum(1 for _, e in rows if e.get("salary"))
        
        for w in self._pr_stats.winfo_children():
            w.destroy()
        
        self._stat_row(self._pr_stats, [
            ("Total Analysts", len(rows), INFO),
            ("With Salary Set", w_sal, OK),
            ("Total USD Payroll", f"${tot_usd:,.0f}", CYAN_D),
            ("Avg USD Salary", f"${tot_usd / max(w_sal, 1):,.0f}", CYAN_D)
        ])
        
        for w in self._pr_dept_inner.winfo_children():
            w.destroy()
        
        dmap = {}
        for _, e in rows:
            if e.get("salary") and e.get("salary_currency") == "USD":
                d = e.get("department", "Unknown") or "Unknown"
                dmap[d] = dmap.get(d, 0) + float(e["salary"])
        
        for dept, val in sorted(dmap.items(), key=lambda x: -x[1]):
            ddef = get_dept_definition(dept)
            pct = round(val / tot_usd * 100) if tot_usd else 0
            row = ctk.CTkFrame(self._pr_dept_inner, fg_color="transparent")
            row.pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkLabel(row, text=f"{ddef.get('icon', '🔒')}  {dept}", font=self.F_SMALL, text_color=TXM).pack(anchor="w")
            ctk.CTkLabel(row, text=f"${val:,.0f}", font=ctk.CTkFont("Consolas", 18, "bold"), text_color=CYAN).pack(anchor="w")
            ctk.CTkLabel(row, text=f"{pct}%", font=self.F_MONO, text_color=TXM).pack(anchor="w")
        
        for row in self._pay_tree.get_children():
            self._pay_tree.delete(row)
        
        for eid, e in rows:
            self._pay_tree.insert("", "end", iid=eid, values=(
                eid, e.get("full_name", ""), e.get("department", ""), e.get("specialization", ""),
                e.get("clearance_level", "—"),
                f"{float(e['salary']):,.0f}" if e.get("salary") else "—",
                e.get("salary_currency", "—"),
                ET_LABELS.get(e.get("employment_type", ""), e.get("employment_type", ""))
            ))

    def _pay_dialog(self, eid=None):
        if not eid:
            sel = self._pay_tree.selection()
            if not sel:
                messagebox.showwarning("No selection", "Select an analyst.")
                return
            eid = sel[0]
        
        e = self.data["employees"].get(eid, {})
        
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Edit Salary — {eid}")
        dlg.geometry("400x260")
        dlg.grab_set()
        dlg.configure(fg_color=BG)
        
        sal_v = tk.StringVar(value=str(e.get("salary", "") or ""))
        cur_v = tk.StringVar(value=e.get("salary_currency", "USD"))
        
        ctk.CTkLabel(dlg, text="Salary Amount", font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkEntry(dlg, textvariable=sal_v, height=40, font=self.F_MONO).pack(fill="x", padx=24)
        
        ctk.CTkLabel(dlg, text="Currency", font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=24, pady=(14, 2))
        ctk.CTkOptionMenu(dlg, variable=cur_v, values=["USD", "EUR", "GBP", "CAD", "AUD"],
                          font=self.F_BODY).pack(fill="x", padx=24)
        
        def _save():
            self._reload()
            self.data["employees"][eid]["salary"] = sal_v.get().strip()
            self.data["employees"][eid]["salary_currency"] = cur_v.get()
            audit(self.data, self.user["username"], "Updated salary", eid)
            save_data(self.data)
            dlg.destroy()
            self._refresh_compensation()
        
        ctk.CTkButton(dlg, text="💾 Save", fg_color=CYAN, hover_color=CYAN_L,
                      text_color=BG, height=42, command=_save).pack(pady=18, fill="x", padx=24)

    def _export_pay_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            initialfile="nexus_compensation.csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        emps = {k: v for k, v in self.data["employees"].items() if v.get("salary")}
        with open(path, "wb") as f:
            f.write(export_csv_bytes(emps))
        messagebox.showinfo("Exported", f"Saved → {path}")

    def _export_pay_xl(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            initialfile="nexus_compensation.xlsx",
                                            filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        emps = {k: v for k, v in self.data["employees"].items() if v.get("salary")}
        b = export_excel_bytes(emps)
        if not b:
            messagebox.showerror("Error", "pip install openpyxl")
            return
        with open(path, "wb") as f:
            f.write(b)
        messagebox.showinfo("Exported", f"Saved → {path}")

    # ── AUDIT LOG ──────────────────────────────────────────────────────────────
    def _build_tab_audit(self):
        f = self._tab("Audit Log")
        self._page_title(f, "Security Audit Log", "System activity trail — Security Leads & Admin only")
        
        tb = ctk.CTkFrame(f, fg_color="transparent")
        tb.pack(fill="x", pady=(0, 10))
        
        self._aud_srch = tk.StringVar()
        self._aud_srch.trace_add("write", lambda *_: self._refresh_audit())
        ctk.CTkEntry(tb, textvariable=self._aud_srch, width=340, height=38,
                     placeholder_text="🔍  Search user, action, target...", font=self.F_BODY).pack(side="left")
        
        ctk.CTkButton(tb, text="📤 Export CSV", fg_color=CYAN_D, width=130, height=38,
                      command=self._export_audit_csv).pack(side="right", padx=4)
        
        cols = ("Timestamp", "User", "Action", "Target", "Detail")
        widths = {"Timestamp": 160, "User": 130, "Action": 200, "Target": 150, "Detail": 300}
        self._audit_tree = self._tree(f, cols, widths)

    def _refresh_audit(self):
        self._reload()
        q = self._aud_srch.get().lower()
        
        for row in self._audit_tree.get_children():
            self._audit_tree.delete(row)
        
        for a in self.data.get("audit_log", []):
            if q and not any(q in str(v).lower() for v in a.values()):
                continue
            self._audit_tree.insert("", "end", values=(
                a.get("ts", ""), a.get("user", ""), a.get("action", ""),
                a.get("target", ""), a.get("detail", "")
            ))

    def _export_audit_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            initialfile="nexus_audit.csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        self._reload()
        with open(path, "wb") as f:
            f.write(export_audit_csv_bytes(self.data.get("audit_log", [])))
        messagebox.showinfo("Exported", f"Audit log saved → {path}")

    # ── ROLE GUIDE ─────────────────────────────────────────────────────────────
    def _build_tab_roles(self):
        f = self._tab("Role Guide")
        self._page_title(f, "Role Guide", "System access levels and responsibilities")
        self._roles_f = ctk.CTkFrame(f, fg_color="transparent")
        self._roles_f.pack(fill="both", expand=True)

    def _refresh_roles(self):
        for w in self._roles_f.winfo_children():
            w.destroy()
        
        f = self._roles_f
        
        # Role cards
        r1 = ctk.CTkFrame(f, fg_color="transparent")
        r1.pack(fill="x", pady=(0, 16))
        
        for rk in ["admin", "security_lead", "team_lead", "analyst"]:
            rdef = ROLE_DEFINITIONS.get(rk, {})
            color = rdef.get("color", CYAN)
            card = ctk.CTkFrame(r1, fg_color=CARD, corner_radius=10, border_width=2, border_color=color)
            card.pack(side="left", fill="both", expand=True, padx=6)
            
            ctk.CTkLabel(card, text=f"{rdef.get('icon', '🔍')}  {rdef.get('label', rk)}",
                         font=self.F_HEAD, text_color=color).pack(anchor="w", padx=16, pady=(16, 2))
            ctk.CTkLabel(card, text=f"Level {rdef.get('level', '?')} Access",
                         font=ctk.CTkFont("Segoe UI", 9, "bold"), text_color=TXM).pack(anchor="w", padx=16)
            ctk.CTkLabel(card, text=rdef.get("purpose", ""), font=self.F_SMALL, text_color=TXM,
                         wraplength=260, justify="left").pack(anchor="w", padx=16, pady=(6, 10))
            
            for resp in rdef.get("responsibilities", []):
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=1)
                ctk.CTkLabel(row, text="•", width=16, font=self.F_MONO, text_color=color).pack(side="left")
                ctk.CTkLabel(row, text=resp, font=self.F_SMALL, text_color=TX, anchor="w",
                             wraplength=240).pack(side="left", fill="x", expand=True)
            ctk.CTkFrame(card, fg_color="transparent", height=14).pack()
        
        # Team definitions
        self._sec(f, "Security Team Definitions")
        r2 = ctk.CTkFrame(f, fg_color="transparent")
        r2.pack(fill="x")
        
        for dname, ddef in DEPT_DEFINITIONS.items():
            color = ddef.get("color", CYAN)
            card = ctk.CTkFrame(r2, fg_color=CARD, corner_radius=10, border_width=1, border_color=color)
            card.pack(side="left", fill="both", expand=True, padx=5)
            
            ctk.CTkLabel(card, text=f"{ddef.get('icon', '🔒')}  {dname}",
                         font=ctk.CTkFont("Consolas", 12, "bold"), text_color=color
                         ).pack(anchor="w", padx=14, pady=(14, 6))
            ctk.CTkLabel(card, text=", ".join(ddef.get("kpis", [])),
                         font=self.F_SMALL, text_color=TXM, wraplength=220, justify="left"
                         ).pack(anchor="w", padx=14, pady=(0, 12))

    # ── SYSTEM USERS ───────────────────────────────────────────────────────────
    def _build_tab_sysusers(self):
        f = self._tab("System Users")
        self._page_title(f, "System Users", "Portal access and authentication — Admin only")
        
        tb = ctk.CTkFrame(f, fg_color="transparent")
        tb.pack(fill="x", pady=(0, 12))
        ctk.CTkButton(tb, text="+ Add System User", fg_color=CYAN, hover_color=CYAN_L, text_color=BG,
                      height=40, width=200, font=self.F_SMALL, command=lambda: self._su_dialog()
                      ).pack(side="right")
        
        cols = ("Username", "Full Name", "Role", "Analyst ID", "Created")
        widths = {"Username": 150, "Full Name": 200, "Role": 150, "Analyst ID": 140, "Created": 120}
        self._su_tree = self._tree(f, cols, widths)
        
        act = ctk.CTkFrame(f, fg_color="transparent")
        act.pack(fill="x", pady=10)
        ctk.CTkButton(act, text="✏️ Edit", width=120, height=38, fg_color=INFO,
                      command=self._edit_su).pack(side="left", padx=4)
        ctk.CTkButton(act, text="🗑 Delete", width=120, height=38, fg_color=ERR,
                      command=self._del_su).pack(side="left", padx=4)

    def _refresh_sysusers(self):
        self._reload()
        for row in self._su_tree.get_children():
            self._su_tree.delete(row)
        
        for uname, d in self.data["system_users"].items():
            rdef = ROLE_DEFINITIONS.get(d.get("role", "analyst"), {})
            rlabel = f"{rdef.get('icon', '🔍')}  {ROLE_LABEL.get(d.get('role', ''), d.get('role', ''))}"
            self._su_tree.insert("", "end", iid=uname, values=(
                uname, d.get("full_name", ""), rlabel, d.get("emp_id", "") or "—", d.get("created", "")
            ))

    def _su_dialog(self, uname=None):
        d = self.data["system_users"].get(uname, {}) if uname else {}
        
        dlg = ctk.CTkToplevel(self)
        dlg.title("Edit System User" if uname else "Add System User")
        dlg.geometry("480x520")
        dlg.grab_set()
        dlg.configure(fg_color=BG)
        
        un_v = tk.StringVar(value=uname or "")
        fn_v = tk.StringVar(value=d.get("full_name", ""))
        rl_v = tk.StringVar(value=d.get("role", "analyst"))
        eid_v = tk.StringVar(value=d.get("emp_id", "") or "")
        pw_v = tk.StringVar()
        
        for label, var, opts, show in [
            ("Username *", un_v, None, None),
            ("Full Name", fn_v, None, None),
            ("Role", rl_v, ["analyst", "team_lead", "security_lead", "admin"], None),
            ("Analyst ID (optional)", eid_v, None, None),
            ("Password (blank = keep current)", pw_v, None, "●")
        ]:
            ctk.CTkLabel(dlg, text=label, font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=24, pady=(12, 2))
            if opts:
                ctk.CTkOptionMenu(dlg, variable=var, values=opts, font=self.F_BODY).pack(fill="x", padx=24)
            else:
                ctk.CTkEntry(dlg, textvariable=var, height=36, show=show, font=self.F_BODY).pack(fill="x", padx=24)
        
        rp_lbl = ctk.CTkLabel(dlg, text="", font=self.F_SMALL, text_color=TXM, wraplength=400, justify="left")
        rp_lbl.pack(anchor="w", padx=24, pady=6)
        
        def _upd(*_):
            rdef = ROLE_DEFINITIONS.get(rl_v.get(), {})
            rp_lbl.configure(text=f"{rdef.get('icon', '🔍')}  {rdef.get('label', rl_v.get())} — {rdef.get('purpose', '')}")
        
        rl_v.trace_add("write", _upd)
        _upd()
        
        def _save():
            nu = un_v.get().strip()
            fn = fn_v.get().strip()
            role = rl_v.get()
            eid_ = eid_v.get().strip() or None
            pw = pw_v.get()
            
            if not nu:
                messagebox.showerror("Error", "Username required.")
                return
            
            self._reload()
            if not uname and nu in self.data["system_users"]:
                messagebox.showerror("Error", "Username exists.")
                return
            if not uname and len(pw) < 6:
                messagebox.showerror("Error", "Password min 6 chars.")
                return
            
            ex = self.data["system_users"].get(uname or nu, {})
            entry = {
                "password_hash": ex.get("password_hash", hash_pw(pw)),
                "photo": ex.get("photo"),
                "created": ex.get("created", datetime.now().strftime("%Y-%m-%d")),
                "full_name": fn,
                "role": role,
                "emp_id": eid_
            }
            if pw and len(pw) >= 6:
                entry["password_hash"] = hash_pw(pw)
            if uname and uname != nu:
                del self.data["system_users"][uname]
            self.data["system_users"][nu] = entry
            audit(self.data, self.user["username"], "Saved system user", nu)
            save_data(self.data)
            dlg.destroy()
            self._refresh_sysusers()
            messagebox.showinfo("Saved", "System user saved.")
        
        ctk.CTkButton(dlg, text="💾 Save", fg_color=CYAN, hover_color=CYAN_L,
                      text_color=BG, height=42, command=_save).pack(pady=16, fill="x", padx=24)

    def _edit_su(self):
        sel = self._su_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a user.")
            return
        self._su_dialog(sel[0])

    def _del_su(self):
        sel = self._su_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a user.")
            return
        uname = sel[0]
        if uname == self.user["username"]:
            messagebox.showerror("Error", "Cannot delete yourself.")
            return
        if not messagebox.askyesno("Confirm", f"Delete '{uname}'?"):
            return
        self._reload()
        del self.data["system_users"][uname]
        audit(self.data, self.user["username"], "Deleted system user", uname)
        save_data(self.data)
        self._refresh_sysusers()

    # ── PROFILE ────────────────────────────────────────────────────────────────
    def _build_tab_profile(self):
        f = self._tab("Profile")
        self._page_title(f, "My Profile", "Account settings and role details")
        
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.pack(fill="x", pady=(0, 14))
        
        rdef = ROLE_DEFINITIONS.get(self.user.get("role", "analyst"), {})
        color = rdef.get("color", CYAN)
        
        # Account card
        acc = ctk.CTkFrame(top, fg_color=CARD, corner_radius=10)
        acc.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(acc, text=f"{rdef.get('icon', '🔍')}  {self.user.get('full_name', '—')}",
                     font=ctk.CTkFont("Consolas", 20, "bold"), text_color=color).pack(anchor="w", padx=18, pady=(18, 2))
        ctk.CTkLabel(acc, text=f"@{self.user.get('username', '')}",
                     font=self.F_MONO, text_color=TXM).pack(anchor="w", padx=18)
        ctk.CTkLabel(acc, text=ROLE_LABEL.get(self.user.get("role", ""), "Analyst"),
                     font=self.F_SMALL, text_color=color).pack(anchor="w", padx=18, pady=(2, 12))
        
        emp_id = self.user.get("emp_id")
        if emp_id and emp_id in self.data["employees"]:
            e = self.data["employees"][emp_id]
            self._frow(acc, "Analyst ID", emp_id)
            self._frow(acc, "Security Team", e.get("department", ""))
            self._frow(acc, "Specialization", e.get("specialization", ""))
        else:
            ctk.CTkLabel(acc, text="No analyst record linked.", font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=18)
        
        ctk.CTkFrame(acc, fg_color="transparent", height=16).pack()
        
        # Role card
        rc = ctk.CTkFrame(top, fg_color=CARD, corner_radius=10, border_width=2, border_color=color)
        rc.pack(side="right", fill="both", expand=True)
        
        ctk.CTkLabel(rc, text="Your Role", font=self.F_HEAD, text_color=TX).pack(anchor="w", padx=16, pady=(16, 6))
        ctk.CTkLabel(rc, text=rdef.get("purpose", ""), font=self.F_SMALL, text_color=TXM,
                     wraplength=380, justify="left").pack(anchor="w", padx=16, pady=(0, 10))
        
        for resp in rdef.get("responsibilities", []):
            row = ctk.CTkFrame(rc, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=1)
            ctk.CTkLabel(row, text="•", width=16, font=self.F_MONO, text_color=color).pack(side="left")
            ctk.CTkLabel(row, text=resp, font=self.F_SMALL, text_color=TX, anchor="w").pack(side="left")
        
        ctk.CTkFrame(rc, fg_color="transparent", height=16).pack()
        
        # Password change
        pw_c = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
        pw_c.pack(fill="x")
        
        ctk.CTkLabel(pw_c, text="Change Password", font=self.F_HEAD, text_color=CYAN).pack(anchor="w", padx=20, pady=(16, 10))
        
        self._pw_cur = tk.StringVar()
        self._pw_new = tk.StringVar()
        self._pw_conf = tk.StringVar()
        
        for label, var in [("Current Password", "_pw_cur"), ("New Password", "_pw_new"), ("Confirm New", "_pw_conf")]:
            ctk.CTkLabel(pw_c, text=label, font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=20, pady=(6, 2))
            ctk.CTkEntry(pw_c, textvariable=getattr(self, var), height=36, show="●",
                         font=self.F_BODY).pack(fill="x", padx=20, pady=(0, 4))
        
        ctk.CTkButton(pw_c, text="Update Password", fg_color=CYAN, hover_color=CYAN_L, text_color=BG,
                      height=42, command=self._change_pw).pack(pady=16, fill="x", padx=20)

    def _change_pw(self):
        c = self._pw_cur.get()
        n = self._pw_new.get()
        cf = self._pw_conf.get()
        
        if not c or not n:
            messagebox.showerror("Error", "Fill all fields.")
            return
        if n != cf:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        if len(n) < 6:
            messagebox.showerror("Error", "Min 6 characters.")
            return
        
        self._reload()
        u = self.data["system_users"].get(self.user["username"], {})
        if not verify_pw(c, u.get("password_hash", "")):
            messagebox.showerror("Error", "Current password incorrect.")
            return
        
        u["password_hash"] = hash_pw(n)
        audit(self.data, self.user["username"], "Changed password", self.user["username"])
        save_data(self.data)
        self._pw_cur.set("")
        self._pw_new.set("")
        self._pw_conf.set("")
        messagebox.showinfo("Updated", "Password updated successfully.")

    def _logout(self):
        if messagebox.askyesno("Sign Out", "Sign out of NEXUS CYBER?"):
            self.destroy()


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    login = LoginWindow()
    login.mainloop()
    if login.logged_in_user:
        app = NexusApp(login.logged_in_user)
        app.mainloop()
