"""
OBSIDIAN CORPORATION — Desktop Edition v3.0
CustomTkinter single-file application

pip install customtkinter openpyxl matplotlib pillow
python obsidian_desktop.py

Shares obsidian_data.json with obsidian_web.py.

Default credentials:
  admin / admin123  |  hr_manager / hr123  |  manager1 / mgr123  |  staff1 / staff123
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, csv, io
from datetime import datetime, date, timedelta

from obsidian_shared import (
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

# ─── THEME ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG      = "#07091a"
SURFACE = "#0c0f22"
CARD    = "#111428"
CARD2   = "#161a30"
BORDER  = "#1e2240"
GOLD    = "#c9a84c"
GOLD_L  = "#e8c56a"
GOLD_D  = "#9a7a30"
OK      = "#3dba7a"
WARN    = "#e09a30"
ERR     = "#e05252"
INFO    = "#4f8ef7"
PURPLE  = "#7c5df9"
TX      = "#d4d8f0"
TXM     = "#5a6080"
TXD     = "#2a3050"

ET_LABELS = {
    "permanent":"Permanent","contract":"Contract",
    "probation":"Probation","intern":"Intern","part_time":"Part Time",
}
LT_LABELS = {
    "annual":"Annual Leave","sick":"Sick Leave",
    "maternity":"Maternity/Paternity","unpaid":"Unpaid Leave","other":"Other",
}
STATUS_COLORS = {"active":OK,"inactive":TXM,"on_leave":WARN}
ROLE_COLORS   = {"admin":ERR,"hr":INFO,"manager":WARN,"staff":OK}


# ─── LOGIN WINDOW ─────────────────────────────────────────────────────────────
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OBSIDIAN CORPORATION — Login")
        self.geometry("480x580")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.logged_in_user = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="OBSIDIAN",
                     font=ctk.CTkFont("Courier New", 52, "bold"),
                     text_color=GOLD).pack(pady=(46, 0))
        ctk.CTkLabel(self, text="CORPORATION",
                     font=ctk.CTkFont("Courier New", 14), text_color=TXM).pack()
        ctk.CTkLabel(self, text="\u2500"*40, text_color=GOLD_D).pack(pady=(6,2))
        ctk.CTkLabel(self, text="The Corporate Management Platform",
                     font=ctk.CTkFont(size=10), text_color=GOLD_D).pack()

        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=44, pady=24)

        ctk.CTkLabel(card, text="CORPORATION PORTAL",
                     font=ctk.CTkFont("Courier New",11,"bold"),
                     text_color=GOLD).pack(pady=(18,14))

        for label, attr, show in [("Username","uvar",None),("Password","pvar","\u2022")]:
            ctk.CTkLabel(card, text=label,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=TXM).pack(anchor="w", padx=22)
            var = tk.StringVar(); setattr(self, attr, var)
            ctk.CTkEntry(card, textvariable=var, height=38, show=show,
                         fg_color=BG, border_color=BORDER,
                         font=ctk.CTkFont("Courier New",12)
                         ).pack(fill="x", padx=22, pady=(3,10))

        self.err_lbl = ctk.CTkLabel(card, text="",
                                    font=ctk.CTkFont(size=11), text_color=ERR)
        self.err_lbl.pack()
        ctk.CTkButton(card, text="SIGN IN", height=44,
                      fg_color=GOLD, hover_color=GOLD_L, text_color=BG,
                      font=ctk.CTkFont("Courier New",16,"bold"),
                      command=self._login).pack(fill="x", padx=22, pady=(4,22))
        self.bind("<Return>", lambda _: self._login())

    def _login(self):
        uname = self.uvar.get().strip()
        pw    = self.pvar.get()
        if not uname or not pw:
            self.err_lbl.configure(text="Please enter both fields."); return
        data = load_data()
        u = data["system_users"].get(uname)
        if not u or not verify_pw(pw, u.get("password_hash","")):
            self.err_lbl.configure(text="Invalid credentials."); return
        audit(data, uname, "Login", uname)
        save_data(data)
        self.logged_in_user = {"username": uname,
                               **{k:v for k,v in u.items() if k!="password_hash"}}
        self.destroy()


# ─── MAIN APP ─────────────────────────────────────────────────────────────────
class ObsidianApp(ctk.CTk):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.data = load_data()
        self.lvl  = ROLE_LEVEL.get(user.get("role","staff"),1)
        self.sel_emp   = None
        self.sel_promo = None
        self.sel_leave = None
        self.sel_pay   = None

        self.title("OBSIDIAN CORPORATION \u2014 Desktop Edition v3.0")
        self.geometry("1400x860")
        self.minsize(1100,680)
        self.configure(fg_color=BG)
        self._fonts()
        self._build()

    def _fonts(self):
        self.F_BRAND = ctk.CTkFont("Courier New",26,"bold")
        self.F_TITLE = ctk.CTkFont("Courier New",24,"bold")
        self.F_HEAD  = ctk.CTkFont("Courier New",15,"bold")
        self.F_BODY  = ctk.CTkFont("Helvetica",13)
        self.F_SMALL = ctk.CTkFont("Helvetica",11)
        self.F_MONO  = ctk.CTkFont("Courier New",11)
        self.F_TAG   = ctk.CTkFont("Helvetica",10,"bold")

    # ── LAYOUT ────────────────────────────────────────────────────────────────
    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=60)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="OBSIDIAN", font=self.F_BRAND, text_color=GOLD
                     ).pack(side="left", padx=(22,4))
        ctk.CTkLabel(hdr, text="CORPORATION",
                     font=ctk.CTkFont("Helvetica",10), text_color=TXM
                     ).pack(side="left")

        ctk.CTkButton(hdr, text="Sign Out", width=80, height=30,
                      fg_color=ERR, hover_color="#c94040",
                      font=self.F_SMALL, command=self._logout
                      ).pack(side="right", padx=(4,18))

        rdef = ROLE_DEFINITIONS.get(self.user.get("role","staff"), {})
        ctk.CTkLabel(hdr,
                     text=f"{rdef.get('icon','')}\u2002{self.user.get('full_name','')}\u2002\u00b7\u2002{ROLE_LABEL.get(self.user.get('role',''),'Staff')}",
                     font=self.F_SMALL,
                     text_color=ROLE_COLORS.get(self.user.get("role","staff"), GOLD_D)
                     ).pack(side="right", padx=6)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        self._sb = ctk.CTkFrame(body, fg_color=SURFACE, width=234, corner_radius=0)
        self._sb.pack(side="left", fill="y"); self._sb.pack_propagate(False)
        self._build_sidebar()

        self._content = ctk.CTkFrame(body, fg_color="transparent")
        self._content.pack(side="right", fill="both", expand=True, padx=22, pady=20)

        self._tabs: dict = {}
        self._build_tab_dashboard()
        self._build_tab_employees()
        self._build_tab_departments()
        self._build_tab_promotions()
        self._build_tab_leave()
        if self.lvl >= 3:
            self._build_tab_payroll()
            self._build_tab_audit()
        self._build_tab_roles()
        if self.lvl >= 4:
            self._build_tab_sysusers()
        self._build_tab_profile()
        self._show("Dashboard")

    def _build_sidebar(self):
        def sec(t):
            ctk.CTkLabel(self._sb, text=t,
                         font=ctk.CTkFont("Helvetica",9,"bold"),
                         text_color=TXD).pack(anchor="w", padx=18, pady=(14,4))

        sec("MAIN")
        nav = [("\U0001f4ca","Dashboard"),("\U0001f465","Employees"),
               ("\U0001f3e2","Departments"),("\U0001f3c6","Promotions"),("\U0001f4c5","Leave")]
        if self.lvl >= 3:
            sec("HR OPERATIONS")
            nav += [("\U0001f4b0","Payroll"),("\U0001f4cb","Audit Log")]
        sec("SYSTEM")
        nav += [("\U0001f511","Role Guide")]
        if self.lvl >= 4:
            nav += [("\U0001f510","System Users")]
        nav += [("\u2699\ufe0f","Profile")]

        self._nb: dict = {}
        for icon, name in nav:
            btn = ctk.CTkButton(
                self._sb, text=f"  {icon}  {name}",
                width=210, height=38, anchor="w",
                fg_color="transparent", text_color=TXM,
                hover_color=CARD2, font=self.F_BODY,
                command=lambda n=name: self._show(n))
            btn.pack(pady=1, padx=10)
            self._nb[name] = btn

        ctk.CTkLabel(self._sb, text="v3.0  Desktop Edition",
                     font=ctk.CTkFont("Courier New",9),
                     text_color=TXD).pack(side="bottom", pady=14)

    def _show(self, name: str):
        for f in self._tabs.values(): f.pack_forget()
        self._tabs[name].pack(fill="both", expand=True)
        for k, btn in self._nb.items():
            btn.configure(fg_color=(GOLD_D if k==name else "transparent"),
                          text_color=(BG if k==name else TXM))
        fn = {"Dashboard":self._refresh_dashboard,"Employees":self._refresh_employees,
              "Departments":self._refresh_departments,"Promotions":self._refresh_promotions,
              "Leave":self._refresh_leave,"Role Guide":self._refresh_roles,
              "Payroll":   self._refresh_payroll   if self.lvl>=3 else None,
              "Audit Log": self._refresh_audit     if self.lvl>=3 else None,
              "System Users":self._refresh_sysusers if self.lvl>=4 else None,
              }.get(name)
        if fn: fn()

    def _reload(self): self.data = load_data()

    # ── WIDGETS ───────────────────────────────────────────────────────────────
    def _tab(self, name):
        f = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._tabs[name] = f; return f

    def _page_title(self, parent, title, subtitle=""):
        h = ctk.CTkFrame(parent, fg_color="transparent"); h.pack(fill="x", pady=(0,16))
        ctk.CTkLabel(h, text=title, font=self.F_TITLE, text_color="#ffffff").pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(h, text=subtitle, font=self.F_SMALL, text_color=TXM).pack(anchor="w")

    def _stat_row(self, parent, stats):
        row = ctk.CTkFrame(parent, fg_color="transparent"); row.pack(fill="x", pady=(0,14))
        for label, val, color in stats:
            c = ctk.CTkFrame(row, fg_color=CARD, corner_radius=10,
                             border_width=2, border_color=color)
            c.pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(c, text=str(val),
                         font=ctk.CTkFont("Courier New",30,"bold"),
                         text_color=color).pack(pady=(12,2))
            ctk.CTkLabel(c, text=label, font=self.F_SMALL, text_color=TXM).pack(pady=(0,12))

    def _tree(self, parent, cols, widths=None, height=18):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
        card.pack(fill="both", expand=True)
        s = ttk.Style(); s.theme_use("clam")
        s.configure("O.Treeview", background=CARD, foreground=TX,
                    fieldbackground=CARD, rowheight=30, font=("Helvetica",12))
        s.configure("O.Treeview.Heading", background=SURFACE, foreground=TXM,
                    font=("Helvetica",10,"bold"), relief="flat")
        s.map("O.Treeview", background=[("selected",GOLD_D)],
              foreground=[("selected","#fff")])
        tree = ttk.Treeview(card, columns=cols, show="headings",
                            selectmode="browse", style="O.Treeview", height=height)
        for col in cols:
            w = (widths or {}).get(col,130)
            tree.heading(col, text=col); tree.column(col, width=w, minwidth=40)
        vsb = ttk.Scrollbar(card, orient="vertical",   command=tree.yview)
        hsb = ttk.Scrollbar(card, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        card.rowconfigure(0, weight=1); card.columnconfigure(0, weight=1)
        return tree

    def _frow(self, parent, label, value, lc=None):
        row = ctk.CTkFrame(parent, fg_color="transparent"); row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, width=160, anchor="w",
                     font=self.F_SMALL, text_color=lc or TXM).pack(side="left")
        ctk.CTkLabel(row, text=str(value or "\u2014"), anchor="w",
                     font=self.F_BODY, text_color=TX).pack(side="left", fill="x", expand=True)

    def _sec(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=self.F_HEAD, text_color=TX
                     ).pack(anchor="w", pady=(12,6))

    # ── DASHBOARD ─────────────────────────────────────────────────────────────
    def _build_tab_dashboard(self):
        f = self._tab("Dashboard")
        self._page_title(f, "Dashboard", "OBSIDIAN CORPORATION \u2014 Corporate Overview")
        self._d_alerts  = ctk.CTkFrame(f, fg_color="transparent"); self._d_alerts.pack(fill="x")
        self._d_stats   = ctk.CTkFrame(f, fg_color="transparent"); self._d_stats.pack(fill="x")
        if MPL_OK:
            self._d_charts = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
            self._d_charts.pack(fill="x", pady=(10,0))
        bot = ctk.CTkFrame(f, fg_color="transparent"); bot.pack(fill="x", pady=(12,0))
        self._d_exp = ctk.CTkFrame(bot, fg_color=CARD, corner_radius=10)
        self._d_exp.pack(side="left", fill="both", expand=True, padx=(0,6))
        ctk.CTkLabel(self._d_exp, text="\u26a0\ufe0f  Contract Expirations (90 days)",
                     font=self.F_HEAD, text_color=WARN).pack(anchor="w", padx=14, pady=(12,6))
        self._d_exp_inner = ctk.CTkFrame(self._d_exp, fg_color="transparent")
        self._d_exp_inner.pack(fill="x", padx=14, pady=(0,12))
        self._d_aud = ctk.CTkFrame(bot, fg_color=CARD, corner_radius=10)
        self._d_aud.pack(side="right", fill="both", expand=True, padx=(6,0))
        ctk.CTkLabel(self._d_aud, text="\U0001f4cb  Recent Activity",
                     font=self.F_HEAD, text_color=TX).pack(anchor="w", padx=14, pady=(12,6))
        self._d_aud_tb = ctk.CTkTextbox(self._d_aud, height=180, font=self.F_MONO,
                                         fg_color="transparent", state="disabled")
        self._d_aud_tb.pack(fill="x", padx=14, pady=(0,12))

    def _refresh_dashboard(self):
        self._reload()
        emps     = list(self.data["employees"].values())
        active   = sum(1 for e in emps if e.get("status")=="active")
        onleave  = sum(1 for e in emps if e.get("status")=="on_leave")
        inactive = sum(1 for e in emps if e.get("status")=="inactive")
        pend_p   = sum(len([r for r in e.get("promotion_requests",[]) if r["status"]=="pending"]) for e in emps)
        pend_l   = len([r for r in self.data.get("leave_requests",[]) if r.get("status")=="pending"])
        for w in self._d_stats.winfo_children(): w.destroy()
        self._stat_row(self._d_stats,[
            ("Total Employees",len(emps),INFO),("Active",active,OK),
            ("On Leave",onleave,WARN),("Inactive",inactive,ERR),
            ("Pending Promotions",pend_p,ERR),
            ("Departments",len(self.data["departments"]),GOLD_D),
            ("Pending Leave",pend_l,WARN),
        ])
        today = date.today(); d90 = today + timedelta(days=90)
        expiring = [(eid,e) for eid,e in self.data["employees"].items()
                    if e.get("contract_end") and
                    today <= date.fromisoformat(e["contract_end"]) <= d90]
        soon = [x for x in expiring
                if (date.fromisoformat(x[1]["contract_end"])-today).days <= 30]
        for w in self._d_alerts.winfo_children(): w.destroy()
        if soon:
            af = ctk.CTkFrame(self._d_alerts, fg_color="#2a1a0a",
                              corner_radius=8, border_width=1, border_color=WARN)
            af.pack(fill="x", pady=(0,6))
            ctk.CTkLabel(af, text=f"\u26a0\ufe0f  {len(soon)} contract(s) expiring within 30 days.",
                         font=self.F_SMALL, text_color=WARN).pack(anchor="w", padx=12, pady=7)
        if pend_p:
            af2 = ctk.CTkFrame(self._d_alerts, fg_color="#1a0a0a",
                               corner_radius=8, border_width=1, border_color=ERR)
            af2.pack(fill="x", pady=(0,6))
            ctk.CTkLabel(af2, text=f"\U0001f3c6  {pend_p} pending promotion request(s).",
                         font=self.F_SMALL, text_color=ERR).pack(anchor="w", padx=12, pady=7)
        for w in self._d_exp_inner.winfo_children(): w.destroy()
        if not expiring:
            ctk.CTkLabel(self._d_exp_inner, text="No contracts expiring in 90 days.",
                         font=self.F_SMALL, text_color=TXM).pack(anchor="w")
        else:
            for eid,e in sorted(expiring, key=lambda x:x[1]["contract_end"]):
                days = (date.fromisoformat(e["contract_end"])-today).days
                col  = ERR if days<=30 else WARN if days<=60 else TXM
                row  = ctk.CTkFrame(self._d_exp_inner, fg_color="transparent"); row.pack(fill="x",pady=2)
                ctk.CTkLabel(row, text=e.get("full_name",eid), font=self.F_SMALL,
                             text_color=TX, width=180, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=f"{days}d \u2014 {e['contract_end']}",
                             font=self.F_MONO, text_color=col).pack(side="right")
        if MPL_OK:
            for w in self._d_charts.winfo_children(): w.destroy()
            self._draw_charts()
        lines = self.data.get("audit_log",[])[:14]
        self._d_aud_tb.configure(state="normal"); self._d_aud_tb.delete("1.0","end")
        for a in lines:
            self._d_aud_tb.insert("end", f"  {a['ts']}  {a['user']}  {a['action']}  {a['target']}\n")
        self._d_aud_tb.configure(state="disabled")

    def _draw_charts(self):
        emps  = list(self.data["employees"].values())
        GCOLS = [GOLD,INFO,OK,WARN,ERR,PURPLE,"#2dd4bf","#f472b6"]
        dmap = {}
        for e in emps:
            d = e.get("department","Unknown") or "Unknown"; dmap[d]=dmap.get(d,0)+1
        tmap = {}
        for e in emps:
            t = ET_LABELS.get(e.get("employment_type",""),"Unknown"); tmap[t]=tmap.get(t,0)+1
        fig,(ax1,ax2) = plt.subplots(1,2,figsize=(12,2.8),facecolor=CARD)
        for ax in (ax1,ax2):
            ax.set_facecolor(CARD)
            for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
        if dmap:
            ax1.pie(list(dmap.values()),labels=list(dmap.keys()),
                    colors=GCOLS[:len(dmap)],textprops={"color":TX,"fontsize":9},startangle=90)
        ax1.set_title("By Department",color=TX,fontsize=10,pad=8)
        if tmap:
            ax2.bar(list(tmap.keys()),list(tmap.values()),color=GCOLS[:len(tmap)],edgecolor="none")
        ax2.set_title("Employment Types",color=TX,fontsize=10,pad=8)
        ax2.tick_params(colors=TXM,labelsize=9)
        fig.tight_layout(pad=1.5)
        canvas = FigureCanvasTkAgg(fig, master=self._d_charts)
        canvas.draw(); canvas.get_tk_widget().pack(fill="x", padx=12, pady=8)
        plt.close(fig)

    # ── EMPLOYEES ─────────────────────────────────────────────────────────────
    def _build_tab_employees(self):
        f = self._tab("Employees")
        self._page_title(f,"Employees","Workforce management and records")
        tb = ctk.CTkFrame(f, fg_color="transparent"); tb.pack(fill="x", pady=(0,8))
        self._emp_srch = tk.StringVar()
        self._emp_srch.trace_add("write", lambda *_: self._refresh_employees())
        ctk.CTkEntry(tb, textvariable=self._emp_srch, width=280, height=36,
                     placeholder_text="\U0001f50d  Name, ID, email, department...",
                     font=self.F_BODY).pack(side="left")
        self._emp_dept_var = tk.StringVar(value="All Departments")
        self._emp_dept_menu = ctk.CTkOptionMenu(
            tb, variable=self._emp_dept_var, values=["All Departments"],
            command=lambda _: self._refresh_employees(), width=160, font=self.F_SMALL)
        self._emp_dept_menu.pack(side="left", padx=8)
        self._emp_st_var = tk.StringVar(value="All Status")
        ctk.CTkOptionMenu(tb, variable=self._emp_st_var,
                          values=["All Status","active","inactive","on_leave"],
                          command=lambda _: self._refresh_employees(),
                          width=120, font=self.F_SMALL).pack(side="left")
        if self.lvl >= 3:
            for txt, cmd, col in [
                ("+ Add", lambda: self._emp_dialog(), GOLD),
                ("\U0001f4e4 Import", self._import_emps, CARD2),
                ("\U0001f4e4 Excel",  self._export_xl,   GOLD_D),
                ("\U0001f4e4 CSV",    self._export_csv,  GOLD_D),
            ]:
                ctk.CTkButton(tb, text=txt, width=90, height=36,
                              fg_color=col, hover_color=GOLD_L if col==GOLD else BORDER,
                              text_color=BG if col in (GOLD,GOLD_D) else TX,
                              font=self.F_SMALL, command=cmd).pack(side="right", padx=3)
        self._emp_cnt = ctk.CTkLabel(f, text="", font=self.F_SMALL, text_color=TXM)
        self._emp_cnt.pack(anchor="w", pady=(0,4))
        cols   = ("ID","Name","Phone","Department","Occupation","Type","Status","Start Date")
        widths = {"ID":130,"Name":160,"Phone":130,"Department":130,
                  "Occupation":150,"Type":100,"Status":80,"Start Date":100}
        self._emp_tree = self._tree(f, cols, widths)
        self._emp_tree.bind("<Double-1>", lambda _: self._emp_view(next(iter(self._emp_tree.selection()),None)))
        self._emp_tree.bind("<<TreeviewSelect>>",
                            lambda _: setattr(self,"sel_emp",next(iter(self._emp_tree.selection()),None)))
        if self.lvl >= 3:
            act = ctk.CTkFrame(f, fg_color="transparent"); act.pack(fill="x", pady=8)
            ctk.CTkButton(act, text="\u270f\ufe0f Edit",   width=110, height=34, fg_color=INFO,
                          font=self.F_SMALL, command=lambda: self._emp_dialog(self.sel_emp)).pack(side="left",padx=4)
            ctk.CTkButton(act, text="\U0001f5d1 Delete",   width=110, height=34, fg_color=ERR,
                          font=self.F_SMALL, command=self._del_emp).pack(side="left",padx=4)
            ctk.CTkButton(act, text="\U0001f441 View Details", width=130, height=34, fg_color=GOLD_D,
                          font=self.F_SMALL, command=lambda: self._emp_view(self.sel_emp)).pack(side="left",padx=4)

    def _refresh_employees(self):
        self._reload()
        depts = ["All Departments"] + list(self.data["departments"].keys())
        self._emp_dept_menu.configure(values=depts)
        q = self._emp_srch.get().lower(); fd = self._emp_dept_var.get(); fs = self._emp_st_var.get()
        for row in self._emp_tree.get_children(): self._emp_tree.delete(row)
        shown = 0
        for eid, e in self.data["employees"].items():
            if self.lvl < 2 and eid != self.user.get("emp_id"): continue
            if fd not in ("All Departments","") and e.get("department")!=fd: continue
            if fs not in ("All Status","") and e.get("status")!=fs: continue
            if q and not any(q in str(v).lower() for v in
                             [eid,e.get("full_name",""),e.get("email",""),
                              e.get("department",""),e.get("occupation",""),e.get("phone","")]): continue
            self._emp_tree.insert("","end",iid=eid,values=(
                eid, e.get("full_name",""), e.get("phone","\u2014"),
                e.get("department",""), e.get("occupation",""),
                ET_LABELS.get(e.get("employment_type",""),e.get("employment_type","")),
                e.get("status",""), e.get("start_date",e.get("date_added","")))); shown+=1
        self._emp_cnt.configure(text=f"Showing {shown} of {len(self.data['employees'])} employees")

    def _emp_view(self, eid):
        if not eid: messagebox.showwarning("No selection","Select an employee first."); return
        e = self.data["employees"].get(eid,{})
        dlg = ctk.CTkToplevel(self); dlg.title(f"Employee \u2014 {eid}")
        dlg.geometry("520x600"); dlg.grab_set(); dlg.configure(fg_color=BG)
        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=20, pady=16)
        hb = ctk.CTkFrame(sf, fg_color=CARD, corner_radius=10); hb.pack(fill="x", pady=(0,12))
        ctk.CTkLabel(hb, text=e.get("full_name",""),
                     font=ctk.CTkFont("Courier New",18,"bold"), text_color=GOLD
                     ).pack(anchor="w", padx=16, pady=(14,0))
        ctk.CTkLabel(hb, text=f"{e.get('occupation','\u2014')}  \u00b7  {e.get('role','\u2014')}",
                     font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=16)
        ctk.CTkLabel(hb, text=eid, font=self.F_MONO, text_color=GOLD_D
                     ).pack(anchor="w", padx=16, pady=(2,14))
        for k,v in [("Email",e.get("email","")),("Phone",e.get("phone","")),
                    ("Department",e.get("department","")),
                    ("Employment Type",ET_LABELS.get(e.get("employment_type",""),e.get("employment_type",""))),
                    ("Status",e.get("status","")),("Location",e.get("location","")),
                    ("Age",e.get("age","")),("Start Date",e.get("start_date","")),
                    ("Contract End",e.get("contract_end","")),("Date Added",e.get("date_added","")),
                    ("Manager ID",e.get("manager_id","")),
                    ("Emergency Contact",e.get("emergency_contact",""))]:
            self._frow(sf, k, v)
        if self.lvl >= 3 and e.get("salary"):
            self._frow(sf, "Salary", f"{e.get('salary_currency','USD')} {float(e['salary']):,.0f}")
        skills = e.get("skills",[])
        if skills:
            ctk.CTkLabel(sf, text="Skills", font=self.F_SMALL, text_color=TXM).pack(anchor="w",pady=(8,3))
            sw = ctk.CTkFrame(sf, fg_color="transparent"); sw.pack(fill="x")
            for s in skills:
                ctk.CTkLabel(sw, text=s, font=self.F_TAG, fg_color=CARD2,
                             corner_radius=20, text_color=GOLD, padx=8, pady=2
                             ).pack(side="left", padx=3, pady=2)
        ctk.CTkButton(dlg, text="Close", command=dlg.destroy,
                      fg_color=GOLD_D, height=36).pack(pady=10)

    def _emp_dialog(self, eid=None):
        if eid and eid not in self.data["employees"]:
            messagebox.showwarning("No selection","Select an employee first."); return
        e = self.data["employees"].get(eid,{}) if eid else {}
        dlg = ctk.CTkToplevel(self); dlg.title("Edit Employee" if eid else "Add Employee")
        dlg.geometry("620x780"); dlg.grab_set(); dlg.configure(fg_color=BG)
        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent"); sf.pack(fill="both",expand=True,padx=22,pady=14)
        fields = [
            ("Full Name *","full_name",None),("Email","email",None),("Phone","phone",None),
            ("Department","department",list(self.data["departments"].keys())),
            ("Occupation","occupation",None),("Role / Level","role",None),
            ("Age","age",None),("Location","location",None),
            ("Employment Type","employment_type",list(ET_LABELS.keys())),
            ("Status","status",["active","inactive","on_leave"]),
            ("Start Date (YYYY-MM-DD)","start_date",None),
            ("Contract End (YYYY-MM-DD)","contract_end",None),
            ("Salary","salary",None),
            ("Currency","salary_currency",["USD","EUR","GBP","NGN","KES","ZAR","GHS"]),
            ("Manager ID (optional)","manager_id",None),
            ("Emergency Contact","emergency_contact",None),
        ]
        vars_ = {}
        for label, key, opts in fields:
            ctk.CTkLabel(sf, text=label, anchor="w", font=self.F_SMALL,
                         text_color=TXM).pack(anchor="w", pady=(6,1))
            var = tk.StringVar(value=str(e.get(key,"") or ""))
            if opts:
                ctk.CTkOptionMenu(sf, variable=var, values=opts or [""],
                                  font=self.F_BODY).pack(fill="x", pady=(0,2))
            else:
                ctk.CTkEntry(sf, textvariable=var, height=34,
                             font=self.F_BODY).pack(fill="x", pady=(0,2))
            vars_[key] = var
        ctk.CTkLabel(sf, text="Skills (comma-separated)", anchor="w",
                     font=self.F_SMALL, text_color=TXM).pack(anchor="w", pady=(6,1))
        sk_var = tk.StringVar(value=", ".join(e.get("skills",[]) if isinstance(e.get("skills"),list) else []))
        ctk.CTkEntry(sf, textvariable=sk_var, height=34,
                     placeholder_text="Python, Leadership, Excel...",
                     font=self.F_BODY).pack(fill="x", pady=(0,2))

        def _save():
            fn = vars_["full_name"].get().strip()
            if not fn: messagebox.showerror("Error","Full name required."); return
            self._reload()
            eid_ = eid or gen_emp_id(self.data)
            emp = {k: v.get().strip() for k,v in vars_.items()}
            raw = sk_var.get().strip()
            emp["skills"] = [s.strip() for s in raw.split(",") if s.strip()] if raw else []
            emp["date_added"] = e.get("date_added", datetime.now().strftime("%Y-%m-%d"))
            emp["promotion_requests"] = e.get("promotion_requests",[])
            emp["photo"] = e.get("photo")
            if not emp.get("manager_id"): emp["manager_id"] = None
            self.data["employees"][eid_] = emp
            audit(self.data, self.user["username"],
                  "Updated employee" if eid else "Added employee", eid_, fn)
            if not eid: notify(self.data,"success",f"New employee: {fn} ({eid_})")
            save_data(self.data); dlg.destroy(); self._refresh_employees()
            messagebox.showinfo("Saved", f"Employee {eid_} saved.")

        ctk.CTkButton(dlg, text="\U0001f4be Save Employee",
                      fg_color=GOLD, hover_color=GOLD_L, text_color=BG,
                      height=42, font=self.F_HEAD, command=_save
                      ).pack(pady=14, fill="x", padx=22)

    def _del_emp(self):
        sel = self._emp_tree.selection()
        if not sel: messagebox.showwarning("No selection","Select an employee."); return
        eid = sel[0]
        if not messagebox.askyesno("Confirm",f"Delete {eid}? Cannot be undone."): return
        self._reload()
        name = self.data["employees"].get(eid,{}).get("full_name","")
        del self.data["employees"][eid]
        audit(self.data, self.user["username"], "Deleted employee", eid, name)
        save_data(self.data); self._refresh_employees()
        messagebox.showinfo("Deleted", f"{eid} deleted.")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            initialfile="obsidian_employees.csv",
                                            filetypes=[("CSV","*.csv")])
        if not path: return
        self._reload()
        with open(path,"wb") as f: f.write(export_csv_bytes(self.data["employees"]))
        messagebox.showinfo("Exported", f"Saved \u2192 {path}")

    def _export_xl(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            initialfile="obsidian_employees.xlsx",
                                            filetypes=[("Excel","*.xlsx")])
        if not path: return
        b = export_excel_bytes(self.data["employees"])
        if not b: messagebox.showerror("Error","pip install openpyxl"); return
        with open(path,"wb") as f: f.write(b)
        messagebox.showinfo("Exported", f"Saved \u2192 {path}")

    def _import_emps(self):
        path = filedialog.askopenfilename(filetypes=[("JSON/CSV","*.json *.csv")])
        if not path: return
        self._reload(); count=0
        try:
            if path.lower().endswith(".json"):
                with open(path) as f: raw=json.load(f)
                if isinstance(raw,dict):
                    for eid,emp in raw.items():
                        emp.setdefault("promotion_requests",[])
                        self.data["employees"][eid]=emp; count+=1
                elif isinstance(raw,list):
                    for emp in raw:
                        eid=emp.pop("id",None) or gen_emp_id(self.data)
                        emp.setdefault("promotion_requests",[])
                        self.data["employees"][eid]=emp; count+=1
            elif path.lower().endswith(".csv"):
                with open(path,encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        eid=row.pop("id",None) or gen_emp_id(self.data)
                        row.setdefault("promotion_requests",[])
                        if "skills" in row and isinstance(row["skills"],str):
                            row["skills"]=[s.strip() for s in row["skills"].split(",") if s.strip()]
                        self.data["employees"][eid]=dict(row); count+=1
            audit(self.data,self.user["username"],"Imported employees",f"count={count}")
            save_data(self.data); self._refresh_employees()
            messagebox.showinfo("Imported",f"Imported {count} employees.")
        except Exception as exc:
            messagebox.showerror("Import Error",str(exc))

    # ── DEPARTMENTS ────────────────────────────────────────────────────────────
    def _build_tab_departments(self):
        f = self._tab("Departments")
        self._page_title(f,"Departments","Organisational structure and purpose")
        if self.lvl>=3:
            tb=ctk.CTkFrame(f,fg_color="transparent"); tb.pack(fill="x",pady=(0,10))
            ctk.CTkButton(tb,text="+ Add Department",fg_color=GOLD,hover_color=GOLD_L,
                          text_color=BG,height=36,width=160,font=self.F_SMALL,
                          command=lambda:self._dept_dialog()).pack(side="right")
        cols=("Department","Purpose / Description","Head ID","Employees","KPIs")
        widths={"Department":140,"Purpose / Description":300,"Head ID":120,"Employees":80,"KPIs":220}
        self._dept_tree=self._tree(f,cols,widths)
        self._dept_tree.bind("<Double-1>",lambda _:self._dept_view(next(iter(self._dept_tree.selection()),None)))
        if self.lvl>=3:
            act=ctk.CTkFrame(f,fg_color="transparent"); act.pack(fill="x",pady=8)
            ctk.CTkButton(act,text="\u270f\ufe0f Edit",width=110,height=34,fg_color=INFO,
                          font=self.F_SMALL,command=self._edit_dept).pack(side="left",padx=4)
            ctk.CTkButton(act,text="\U0001f5d1 Delete",width=110,height=34,fg_color=ERR,
                          font=self.F_SMALL,command=self._del_dept).pack(side="left",padx=4)
        ctk.CTkButton(f,text="\U0001f441 View Details",width=130,height=34,fg_color=GOLD_D,font=self.F_SMALL,
                      command=lambda:self._dept_view(next(iter(self._dept_tree.selection()),None))
                      ).pack(anchor="w",padx=4,pady=4)

    def _refresh_departments(self):
        self._reload()
        for row in self._dept_tree.get_children(): self._dept_tree.delete(row)
        for name,d in self.data["departments"].items():
            cnt=sum(1 for e in self.data["employees"].values() if e.get("department")==name)
            ddef=get_dept_definition(name); kpis=", ".join(ddef.get("kpis",[]))
            self._dept_tree.insert("","end",iid=name,values=(
                f"{ddef.get('icon','')}\u2002{name}",
                d.get("description","") or ddef.get("purpose",""),
                d.get("head_id","") or "\u2014", cnt, kpis))

    def _dept_view(self, name):
        if not name: messagebox.showwarning("No selection","Select a department."); return
        d=self.data["departments"].get(name,{}); ddef=get_dept_definition(name)
        emps=[(eid,e) for eid,e in self.data["employees"].items() if e.get("department")==name]
        head=self.data["employees"].get(d.get("head_id",""),{})
        dlg=ctk.CTkToplevel(self); dlg.title(f"Department \u2014 {name}")
        dlg.geometry("560x620"); dlg.grab_set(); dlg.configure(fg_color=BG)
        sf=ctk.CTkScrollableFrame(dlg,fg_color="transparent"); sf.pack(fill="both",expand=True,padx=20,pady=16)
        ctk.CTkLabel(sf,text=f"{ddef.get('icon','')}\u2002{name}",
                     font=ctk.CTkFont("Courier New",20,"bold"),text_color=GOLD).pack(anchor="w",pady=(0,4))
        pc=ctk.CTkFrame(sf,fg_color=CARD2,corner_radius=8); pc.pack(fill="x",pady=(0,10))
        ctk.CTkLabel(pc,text=ddef.get("purpose",d.get("description","")),
                     font=self.F_SMALL,text_color=TXM,wraplength=480,justify="left",anchor="w"
                     ).pack(anchor="w",padx=14,pady=10)
        self._sec(sf,"Key Responsibilities")
        for r in ddef.get("responsibilities",[]):
            row=ctk.CTkFrame(sf,fg_color="transparent"); row.pack(fill="x",pady=1)
            ctk.CTkLabel(row,text="\u2192",width=20,font=self.F_MONO,text_color=GOLD).pack(side="left")
            ctk.CTkLabel(row,text=r,font=self.F_SMALL,text_color=TX,anchor="w").pack(side="left",fill="x",expand=True)
        if ddef.get("kpis"):
            self._sec(sf,"Performance Indicators")
            kr=ctk.CTkFrame(sf,fg_color="transparent"); kr.pack(fill="x")
            for k in ddef["kpis"]:
                ctk.CTkLabel(kr,text=k,font=self.F_TAG,fg_color=CARD2,corner_radius=20,
                             text_color=GOLD,padx=8,pady=2).pack(side="left",padx=4,pady=2)
        self._sec(sf,"Department Head")
        if head:
            self._frow(sf,"Name",head.get("full_name",""))
            self._frow(sf,"Occupation",head.get("occupation",""))
        else:
            ctk.CTkLabel(sf,text="No head assigned.",font=self.F_SMALL,text_color=TXM).pack(anchor="w")
        self._sec(sf,f"Team Members ({len(emps)})")
        for eid,e in emps[:8]:
            row=ctk.CTkFrame(sf,fg_color=CARD2,corner_radius=6); row.pack(fill="x",pady=2)
            ctk.CTkLabel(row,text=e.get("full_name",""),font=self.F_BODY,text_color=TX).pack(side="left",padx=10,pady=4)
            ctk.CTkLabel(row,text=e.get("occupation",""),font=self.F_SMALL,text_color=TXM).pack(side="left")
            ctk.CTkLabel(row,text=e.get("status",""),font=self.F_SMALL,
                         text_color=STATUS_COLORS.get(e.get("status",""),TXM)).pack(side="right",padx=10)
        if len(emps)>8:
            ctk.CTkLabel(sf,text=f"+{len(emps)-8} more",font=self.F_SMALL,text_color=TXM).pack(anchor="w",pady=2)
        ctk.CTkButton(dlg,text="Close",command=dlg.destroy,fg_color=GOLD_D,height=36).pack(pady=10)

    def _dept_dialog(self, name=None):
        d=self.data["departments"].get(name,{}) if name else {}
        dlg=ctk.CTkToplevel(self); dlg.title("Edit Department" if name else "Add Department")
        dlg.geometry("480x320"); dlg.grab_set(); dlg.configure(fg_color=BG)
        nm_v=tk.StringVar(value=name or ""); ds_v=tk.StringVar(value=d.get("description",""))
        hd_v=tk.StringVar(value=d.get("head_id","") or "")
        for label,var in [("Department Name *",nm_v),("Description",ds_v),("Head Employee ID (optional)",hd_v)]:
            ctk.CTkLabel(dlg,text=label,font=self.F_SMALL,text_color=TXM).pack(anchor="w",padx=22,pady=(10,1))
            ctk.CTkEntry(dlg,textvariable=var,height=34,font=self.F_BODY).pack(fill="x",padx=22)
        def _save():
            nn=nm_v.get().strip()
            if not nn: messagebox.showerror("Error","Name required."); return
            self._reload()
            dept={"description":ds_v.get().strip(),"head_id":hd_v.get().strip() or None}
            if name and name!=nn:
                del self.data["departments"][name]
                for e in self.data["employees"].values():
                    if e.get("department")==name: e["department"]=nn
            self.data["departments"][nn]=dept
            audit(self.data,self.user["username"],"Saved department",nn)
            save_data(self.data); dlg.destroy(); self._refresh_departments()
            messagebox.showinfo("Saved",f"Department '{nn}' saved.")
        ctk.CTkButton(dlg,text="\U0001f4be Save",fg_color=GOLD,hover_color=GOLD_L,
                      text_color=BG,height=40,command=_save).pack(pady=16,padx=22,fill="x")

    def _edit_dept(self):
        sel=self._dept_tree.selection()
        if not sel: messagebox.showwarning("No selection","Select a department."); return
        self._dept_dialog(sel[0])

    def _del_dept(self):
        sel=self._dept_tree.selection()
        if not sel: messagebox.showwarning("No selection","Select a department."); return
        name=sel[0]
        if not messagebox.askyesno("Confirm",f"Delete department '{name}'?"): return
        self._reload(); del self.data["departments"][name]
        audit(self.data,self.user["username"],"Deleted department",name)
        save_data(self.data); self._refresh_departments()

    # ── PROMOTIONS ─────────────────────────────────────────────────────────────
    def _build_tab_promotions(self):
        f=self._tab("Promotions"); self._page_title(f,"Promotions","Career advancement workflow")
        card=ctk.CTkFrame(f,fg_color=CARD,corner_radius=10); card.pack(fill="x",pady=(0,12))
        ctk.CTkLabel(card,text="Submit Promotion Request",font=self.F_HEAD,text_color=TX
                     ).pack(anchor="w",padx=18,pady=(14,8))
        r1=ctk.CTkFrame(card,fg_color="transparent"); r1.pack(fill="x",padx=18,pady=(0,6))
        self._p_eid=tk.StringVar(); self._p_role=tk.StringVar()
        ctk.CTkLabel(r1,text="Employee ID:",font=self.F_SMALL,text_color=TXM).pack(side="left")
        ctk.CTkEntry(r1,textvariable=self._p_eid,width=170,height=34,
                     placeholder_text="OBSD-2026-0001",font=self.F_MONO).pack(side="left",padx=(6,14))
        ctk.CTkLabel(r1,text="Requested Role:",font=self.F_SMALL,text_color=TXM).pack(side="left")
        ctk.CTkEntry(r1,textvariable=self._p_role,width=170,height=34,
                     placeholder_text="e.g. Senior Engineer",font=self.F_BODY).pack(side="left",padx=6)
        ctk.CTkButton(r1,text="Submit",width=90,height=34,fg_color=GOLD,hover_color=GOLD_L,
                      text_color=BG,command=self._sub_promo).pack(side="left",padx=8)
        r2=ctk.CTkFrame(card,fg_color="transparent"); r2.pack(fill="x",padx=18,pady=(0,14))
        self._p_notes=tk.StringVar()
        ctk.CTkLabel(r2,text="Notes (optional):",font=self.F_SMALL,text_color=TXM).pack(side="left")
        ctk.CTkEntry(r2,textvariable=self._p_notes,width=480,height=34,font=self.F_BODY).pack(side="left",padx=6)
        cols=("Employee ID","Name","Current Role","Requested Role","Notes","Date","Status","Resolved By")
        widths={"Employee ID":120,"Name":150,"Current Role":120,"Requested Role":140,
                "Notes":180,"Date":100,"Status":90,"Resolved By":110}
        self._promo_tree=self._tree(f,cols,widths)
        self._promo_tree.bind("<<TreeviewSelect>>",lambda _:self._on_promo_sel())
        if self.lvl>=3:
            act=ctk.CTkFrame(f,fg_color="transparent"); act.pack(fill="x",pady=8)
            ctk.CTkButton(act,text="\u2705 Approve",fg_color=OK,hover_color="#2ea66b",width=120,height=36,
                          command=lambda:self._res_promo("approved")).pack(side="left",padx=4)
            ctk.CTkButton(act,text="\u274c Deny",fg_color=ERR,hover_color="#c94040",width=120,height=36,
                          command=lambda:self._res_promo("denied")).pack(side="left",padx=4)

    def _refresh_promotions(self):
        self._reload()
        for row in self._promo_tree.get_children(): self._promo_tree.delete(row)
        for eid,e in self.data["employees"].items():
            for i,req in enumerate(e.get("promotion_requests",[])):
                self._promo_tree.insert("","end",iid=f"{eid}::{i}",values=(
                    eid,e.get("full_name",""),req.get("current_role",""),
                    req.get("requested_role",""),(req.get("notes","") or "")[:40],
                    req.get("date",""),req.get("status","").capitalize(),
                    req.get("resolved_by","") or "\u2014"))

    def _on_promo_sel(self):
        sel=self._promo_tree.selection(); self.sel_promo=sel[0] if sel else None

    def _sub_promo(self):
        eid=self._p_eid.get().strip(); role=self._p_role.get().strip(); notes=self._p_notes.get().strip()
        if not eid or not role: messagebox.showerror("Error","Employee ID and role required."); return
        self._reload()
        if eid not in self.data["employees"]: messagebox.showerror("Not Found",f"'{eid}' not found."); return
        e=self.data["employees"][eid]
        req={"requested_role":role,"current_role":e.get("role",""),"notes":notes,
             "status":"pending","date":datetime.now().strftime("%Y-%m-%d"),
             "submitted_by":self.user["username"],"resolved_by":None,"resolved_at":None}
        e.setdefault("promotion_requests",[]).append(req)
        audit(self.data,self.user["username"],"Promotion request",eid,f"\u2192 {role}")
        notify(self.data,"warning",f"Promotion request: {e.get('full_name',eid)} \u2192 {role}")
        save_data(self.data); self._p_eid.set(""); self._p_role.set(""); self._p_notes.set("")
        self._refresh_promotions(); messagebox.showinfo("Submitted","Promotion request submitted.")

    def _res_promo(self, resolution):
        if not self.sel_promo: messagebox.showwarning("No selection","Select a request."); return
        eid,idx_s=self.sel_promo.split("::")
        self._reload()
        req=self.data["employees"][eid]["promotion_requests"][int(idx_s)]
        if req["status"]!="pending": messagebox.showwarning("Already Resolved","Already resolved."); return
        req["status"]=resolution; req["resolved_by"]=self.user["username"]
        req["resolved_at"]=datetime.now().strftime("%Y-%m-%d %H:%M")
        if resolution=="approved": self.data["employees"][eid]["role"]=req["requested_role"]
        audit(self.data,self.user["username"],f"Promotion {resolution}",eid,req["requested_role"])
        save_data(self.data); self._refresh_promotions()
        messagebox.showinfo("Done",f"Promotion {resolution}.")

    # ── LEAVE ──────────────────────────────────────────────────────────────────
    def _build_tab_leave(self):
        f=self._tab("Leave"); self._page_title(f,"Leave Management","Absence tracking and approval")
        card=ctk.CTkFrame(f,fg_color=CARD,corner_radius=10); card.pack(fill="x",pady=(0,12))
        ctk.CTkLabel(card,text="Submit Leave Request",font=self.F_HEAD,text_color=TX
                     ).pack(anchor="w",padx=18,pady=(14,8))
        sf=ctk.CTkFrame(card,fg_color="transparent"); sf.pack(fill="x",padx=18,pady=(0,14))
        self._lv_eid=tk.StringVar(); self._lv_type=tk.StringVar(value="annual")
        self._lv_start=tk.StringVar(); self._lv_end=tk.StringVar(); self._lv_notes=tk.StringVar()
        r1=ctk.CTkFrame(sf,fg_color="transparent"); r1.pack(fill="x",pady=3)
        if self.lvl>=3:
            ctk.CTkLabel(r1,text="Employee ID:",font=self.F_SMALL,text_color=TXM,width=100).pack(side="left")
            ctk.CTkEntry(r1,textvariable=self._lv_eid,width=170,height=32,
                         placeholder_text="OBSD-2026-0001 or blank=self",font=self.F_MONO).pack(side="left",padx=(4,16))
        ctk.CTkLabel(r1,text="Type:",font=self.F_SMALL,text_color=TXM).pack(side="left")
        ctk.CTkOptionMenu(r1,variable=self._lv_type,values=list(LT_LABELS.keys()),
                          width=160,font=self.F_SMALL).pack(side="left",padx=4)
        r2=ctk.CTkFrame(sf,fg_color="transparent"); r2.pack(fill="x",pady=3)
        for lbl,var,ph in [("Start:",self._lv_start,"YYYY-MM-DD"),("End:",self._lv_end,"YYYY-MM-DD")]:
            ctk.CTkLabel(r2,text=lbl,font=self.F_SMALL,text_color=TXM,width=42).pack(side="left")
            ctk.CTkEntry(r2,textvariable=var,width=130,height=32,placeholder_text=ph,
                         font=self.F_MONO).pack(side="left",padx=(4,14))
        r3=ctk.CTkFrame(sf,fg_color="transparent"); r3.pack(fill="x",pady=3)
        ctk.CTkLabel(r3,text="Notes:",font=self.F_SMALL,text_color=TXM,width=60).pack(side="left")
        ctk.CTkEntry(r3,textvariable=self._lv_notes,width=400,height=32,font=self.F_BODY).pack(side="left",padx=4)
        ctk.CTkButton(r3,text="Submit Request",fg_color=GOLD,hover_color=GOLD_L,text_color=BG,
                      height=32,command=self._sub_leave).pack(side="left",padx=10)
        cols=("Employee ID","Name","Type","From","To","Days","Notes","Status","Resolved By")
        widths={"Employee ID":120,"Name":150,"Type":130,"From":100,"To":100,
                "Days":50,"Notes":160,"Status":90,"Resolved By":110}
        self._leave_tree=self._tree(f,cols,widths)
        self._leave_tree.bind("<<TreeviewSelect>>",lambda _:self._on_leave_sel())
        if self.lvl>=3:
            act=ctk.CTkFrame(f,fg_color="transparent"); act.pack(fill="x",pady=8)
            ctk.CTkButton(act,text="\u2705 Approve",fg_color=OK,hover_color="#2ea66b",width=120,height=36,
                          command=lambda:self._res_leave("approved")).pack(side="left",padx=4)
            ctk.CTkButton(act,text="\u274c Deny",fg_color=ERR,hover_color="#c94040",width=120,height=36,
                          command=lambda:self._res_leave("denied")).pack(side="left",padx=4)

    def _refresh_leave(self):
        self._reload()
        for row in self._leave_tree.get_children(): self._leave_tree.delete(row)
        for i,req in enumerate(self.data.get("leave_requests",[])):
            if self.lvl<3 and req.get("emp_id")!=self.user.get("emp_id"): continue
            e=self.data["employees"].get(req.get("emp_id",""),{})
            s=req.get("start_date",""); e2=req.get("end_date","")
            try: days=str((datetime.strptime(e2,"%Y-%m-%d")-datetime.strptime(s,"%Y-%m-%d")).days+1)
            except: days="\u2014"
            self._leave_tree.insert("","end",iid=str(i),values=(
                req.get("emp_id",""),e.get("full_name",""),
                LT_LABELS.get(req.get("leave_type",""),req.get("leave_type","")),
                s,e2,days,(req.get("notes","") or "")[:30],
                req.get("status","").capitalize(),req.get("resolved_by","") or "\u2014"))

    def _on_leave_sel(self):
        sel=self._leave_tree.selection(); self.sel_leave=int(sel[0]) if sel else None

    def _sub_leave(self):
        eid=self._lv_eid.get().strip() or self.user.get("emp_id","")
        ltype=self._lv_type.get(); s=self._lv_start.get().strip()
        e2=self._lv_end.get().strip(); notes=self._lv_notes.get().strip()
        if not s or not e2: messagebox.showerror("Error","Start and end dates required."); return
        if not eid: messagebox.showerror("Error","No employee ID found."); return
        self._reload()
        if eid not in self.data["employees"]: messagebox.showerror("Error",f"'{eid}' not found."); return
        req={"emp_id":eid,"leave_type":ltype,"start_date":s,"end_date":e2,"notes":notes,
             "status":"pending","submitted_by":self.user["username"],
             "submitted_at":datetime.now().strftime("%Y-%m-%d %H:%M"),"resolved_by":None}
        self.data.setdefault("leave_requests",[]).append(req)
        name=self.data["employees"][eid].get("full_name",eid)
        audit(self.data,self.user["username"],"Leave submitted",eid,ltype)
        notify(self.data,"info",f"Leave request: {name} \u2014 {ltype} ({s} to {e2})")
        save_data(self.data); self._lv_eid.set(""); self._lv_start.set("")
        self._lv_end.set(""); self._lv_notes.set("")
        self._refresh_leave(); messagebox.showinfo("Submitted","Leave request submitted.")

    def _res_leave(self, resolution):
        if self.sel_leave is None: messagebox.showwarning("No selection","Select a request."); return
        self._reload(); reqs=self.data.get("leave_requests",[])
        if self.sel_leave>=len(reqs): return
        req=reqs[self.sel_leave]
        if req["status"]!="pending": messagebox.showwarning("Already Resolved","Already resolved."); return
        req["status"]=resolution; req["resolved_by"]=self.user["username"]
        req["resolved_at"]=datetime.now().strftime("%Y-%m-%d %H:%M")
        if resolution=="approved":
            eid=req.get("emp_id","")
            if eid in self.data["employees"]: self.data["employees"][eid]["status"]="on_leave"
        audit(self.data,self.user["username"],f"Leave {resolution}",req.get("emp_id",""),req.get("leave_type",""))
        save_data(self.data); self.sel_leave=None; self._refresh_leave()
        messagebox.showinfo("Done",f"Leave {resolution}.")

    # ── PAYROLL ────────────────────────────────────────────────────────────────
    def _build_tab_payroll(self):
        f=self._tab("Payroll"); self._page_title(f,"Payroll & Salary","Compensation \u2014 HR & Admin only")
        tb=ctk.CTkFrame(f,fg_color="transparent"); tb.pack(fill="x",pady=(0,8))
        self._pr_srch=tk.StringVar(); self._pr_srch.trace_add("write",lambda *_:self._refresh_payroll())
        ctk.CTkEntry(tb,textvariable=self._pr_srch,width=280,height=36,
                     placeholder_text="\U0001f50d  Search...",font=self.F_BODY).pack(side="left")
        ctk.CTkButton(tb,text="\U0001f4e4 Excel",fg_color=GOLD_D,width=90,height=36,
                      command=self._export_pay_xl).pack(side="right",padx=3)
        ctk.CTkButton(tb,text="\U0001f4e4 CSV",fg_color=GOLD_D,width=80,height=36,
                      command=self._export_pay_csv).pack(side="right",padx=3)
        self._pr_stats=ctk.CTkFrame(f,fg_color="transparent"); self._pr_stats.pack(fill="x",pady=(0,8))
        self._pr_dept=ctk.CTkFrame(f,fg_color=CARD,corner_radius=10); self._pr_dept.pack(fill="x",pady=(0,10))
        ctk.CTkLabel(self._pr_dept,text="USD Payroll by Department",font=self.F_HEAD,text_color=TX
                     ).pack(anchor="w",padx=14,pady=(12,4))
        self._pr_dept_inner=ctk.CTkFrame(self._pr_dept,fg_color="transparent")
        self._pr_dept_inner.pack(fill="x",padx=14,pady=(0,12))
        cols=("ID","Name","Department","Occupation","Role","Salary","Currency","Type")
        widths={"ID":130,"Name":160,"Department":130,"Occupation":140,"Role":100,"Salary":110,"Currency":70,"Type":110}
        self._pay_tree=self._tree(f,cols,widths)
        self._pay_tree.bind("<Double-1>",lambda _:self._pay_dialog(next(iter(self._pay_tree.selection()),None)))
        act=ctk.CTkFrame(f,fg_color="transparent"); act.pack(fill="x",pady=8)
        ctk.CTkButton(act,text="\u270f\ufe0f Edit Salary",fg_color=INFO,width=130,height=36,
                      command=self._pay_dialog).pack(side="left")

    def _refresh_payroll(self):
        self._reload()
        q=self._pr_srch.get().lower()
        rows=[(eid,e) for eid,e in self.data["employees"].items()
              if not q or any(q in str(v).lower() for v in [eid,e.get("full_name",""),e.get("department","")])]
        tot_usd=sum(float(e.get("salary","0") or 0) for _,e in rows if e.get("salary_currency")=="USD")
        w_sal=sum(1 for _,e in rows if e.get("salary"))
        for w in self._pr_stats.winfo_children(): w.destroy()
        self._stat_row(self._pr_stats,[
            ("Total Employees",len(rows),INFO),("With Salary Set",w_sal,OK),
            ("Total USD Payroll",f"${tot_usd:,.0f}",GOLD_D),
            ("Avg USD Salary",f"${tot_usd/max(w_sal,1):,.0f}",GOLD_D)])
        for w in self._pr_dept_inner.winfo_children(): w.destroy()
        dmap = {}
        for _,e in rows:
            if e.get("salary") and e.get("salary_currency")=="USD":
                d=e.get("department","Unknown") or "Unknown"; dmap[d]=dmap.get(d,0)+float(e["salary"])
        for dept,val in sorted(dmap.items(),key=lambda x:-x[1]):
            ddef=get_dept_definition(dept); pct=round(val/tot_usd*100) if tot_usd else 0
            row=ctk.CTkFrame(self._pr_dept_inner,fg_color="transparent"); row.pack(side="left",padx=8,fill="x",expand=True)
            ctk.CTkLabel(row,text=f"{ddef.get('icon','')}\u2002{dept}",font=self.F_SMALL,text_color=TXM).pack(anchor="w")
            ctk.CTkLabel(row,text=f"${val:,.0f}",font=ctk.CTkFont("Courier New",17,"bold"),text_color=GOLD).pack(anchor="w")
            ctk.CTkLabel(row,text=f"{pct}%",font=self.F_MONO,text_color=TXM).pack(anchor="w")
        for row in self._pay_tree.get_children(): self._pay_tree.delete(row)
        for eid,e in rows:
            self._pay_tree.insert("","end",iid=eid,values=(
                eid,e.get("full_name",""),e.get("department",""),e.get("occupation",""),
                e.get("role",""),f"{float(e['salary']):,.0f}" if e.get("salary") else "\u2014",
                e.get("salary_currency","\u2014"),
                ET_LABELS.get(e.get("employment_type",""),e.get("employment_type",""))))

    def _pay_dialog(self, eid=None):
        if not eid:
            sel=self._pay_tree.selection()
            if not sel: messagebox.showwarning("No selection","Select an employee."); return
            eid=sel[0]
        e=self.data["employees"].get(eid,{})
        dlg=ctk.CTkToplevel(self); dlg.title(f"Edit Salary \u2014 {eid}")
        dlg.geometry("380x240"); dlg.grab_set(); dlg.configure(fg_color=BG)
        sal_v=tk.StringVar(value=str(e.get("salary","") or ""))
        cur_v=tk.StringVar(value=e.get("salary_currency","USD"))
        ctk.CTkLabel(dlg,text="Salary Amount",font=self.F_SMALL,text_color=TXM).pack(anchor="w",padx=22,pady=(20,1))
        ctk.CTkEntry(dlg,textvariable=sal_v,height=38,font=self.F_MONO).pack(fill="x",padx=22)
        ctk.CTkLabel(dlg,text="Currency",font=self.F_SMALL,text_color=TXM).pack(anchor="w",padx=22,pady=(12,1))
        ctk.CTkOptionMenu(dlg,variable=cur_v,values=["USD","EUR","GBP","NGN","KES","ZAR","GHS"],
                          font=self.F_BODY).pack(fill="x",padx=22)
        def _save():
            self._reload(); self.data["employees"][eid]["salary"]=sal_v.get().strip()
            self.data["employees"][eid]["salary_currency"]=cur_v.get()
            audit(self.data,self.user["username"],"Updated salary",eid)
            save_data(self.data); dlg.destroy(); self._refresh_payroll()
        ctk.CTkButton(dlg,text="\U0001f4be Save",fg_color=GOLD,hover_color=GOLD_L,text_color=BG,
                      height=40,command=_save).pack(pady=16,fill="x",padx=22)

    def _export_pay_csv(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="obsidian_payroll.csv",
                                          filetypes=[("CSV","*.csv")])
        if not path: return
        emps={k:v for k,v in self.data["employees"].items() if v.get("salary")}
        with open(path,"wb") as f: f.write(export_csv_bytes(emps))
        messagebox.showinfo("Exported",f"Saved \u2192 {path}")

    def _export_pay_xl(self):
        path=filedialog.asksaveasfilename(defaultextension=".xlsx",initialfile="obsidian_payroll.xlsx",
                                          filetypes=[("Excel","*.xlsx")])
        if not path: return
        emps={k:v for k,v in self.data["employees"].items() if v.get("salary")}
        b=export_excel_bytes(emps)
        if not b: messagebox.showerror("Error","pip install openpyxl"); return
        with open(path,"wb") as f: f.write(b)
        messagebox.showinfo("Exported",f"Saved \u2192 {path}")

    # ── AUDIT ──────────────────────────────────────────────────────────────────
    def _build_tab_audit(self):
        f=self._tab("Audit Log"); self._page_title(f,"Audit Log","System activity trail \u2014 HR & Admin only")
        tb=ctk.CTkFrame(f,fg_color="transparent"); tb.pack(fill="x",pady=(0,8))
        self._aud_srch=tk.StringVar(); self._aud_srch.trace_add("write",lambda *_:self._refresh_audit())
        ctk.CTkEntry(tb,textvariable=self._aud_srch,width=320,height=36,
                     placeholder_text="\U0001f50d  Search user, action, target...",font=self.F_BODY).pack(side="left")
        ctk.CTkButton(tb,text="\U0001f4e4 Export CSV",fg_color=GOLD_D,width=120,height=36,
                      command=self._export_audit_csv).pack(side="right",padx=3)
        cols=("Timestamp","User","Action","Target","Detail")
        widths={"Timestamp":150,"User":120,"Action":180,"Target":140,"Detail":280}
        self._audit_tree=self._tree(f,cols,widths)

    def _refresh_audit(self):
        self._reload(); q=self._aud_srch.get().lower()
        for row in self._audit_tree.get_children(): self._audit_tree.delete(row)
        for a in self.data.get("audit_log",[]):
            if q and not any(q in str(v).lower() for v in a.values()): continue
            self._audit_tree.insert("","end",values=(
                a.get("ts",""),a.get("user",""),a.get("action",""),
                a.get("target",""),a.get("detail","")))

    def _export_audit_csv(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="obsidian_audit.csv",
                                          filetypes=[("CSV","*.csv")])
        if not path: return
        self._reload()
        with open(path,"wb") as f: f.write(export_audit_csv_bytes(self.data.get("audit_log",[])))
        messagebox.showinfo("Exported",f"Audit log saved \u2192 {path}")

    # ── ROLE GUIDE ─────────────────────────────────────────────────────────────
    def _build_tab_roles(self):
        f=self._tab("Role Guide"); self._page_title(f,"Role Guide","System access levels and responsibilities")
        self._roles_f=ctk.CTkFrame(f,fg_color="transparent"); self._roles_f.pack(fill="both",expand=True)

    def _refresh_roles(self):
        for w in self._roles_f.winfo_children(): w.destroy()
        f=self._roles_f
        r1=ctk.CTkFrame(f,fg_color="transparent"); r1.pack(fill="x",pady=(0,14))
        for rk in ["admin","hr","manager","staff"]:
            rdef=ROLE_DEFINITIONS.get(rk,{}); color=rdef.get("color",GOLD)
            card=ctk.CTkFrame(r1,fg_color=CARD,corner_radius=10,border_width=2,border_color=color)
            card.pack(side="left",fill="both",expand=True,padx=5)
            ctk.CTkLabel(card,text=f"{rdef.get('icon','')}\u2002{rdef.get('label',rk)}",
                         font=self.F_HEAD,text_color=color).pack(anchor="w",padx=14,pady=(14,2))
            ctk.CTkLabel(card,text=f"Level {rdef.get('level','?')} Access",
                         font=ctk.CTkFont("Helvetica",9,"bold"),text_color=TXM).pack(anchor="w",padx=14)
            ctk.CTkLabel(card,text=rdef.get("purpose",""),font=self.F_SMALL,text_color=TXM,
                         wraplength=240,justify="left").pack(anchor="w",padx=14,pady=(4,8))
            for resp in rdef.get("responsibilities",[]):
                row=ctk.CTkFrame(card,fg_color="transparent"); row.pack(fill="x",padx=14,pady=1)
                ctk.CTkLabel(row,text="\u2022",width=14,font=self.F_MONO,text_color=color).pack(side="left")
                ctk.CTkLabel(row,text=resp,font=self.F_SMALL,text_color=TX,anchor="w",
                             wraplength=220).pack(side="left",fill="x",expand=True)
            ctk.CTkFrame(card,fg_color="transparent",height=12).pack()
        self._sec(f,"Department Definitions")
        r2=ctk.CTkFrame(f,fg_color="transparent"); r2.pack(fill="x")
        for dname,ddef in DEPT_DEFINITIONS.items():
            color=ddef.get("color",GOLD)
            card=ctk.CTkFrame(r2,fg_color=CARD,corner_radius=10,border_width=1,border_color=color)
            card.pack(side="left",fill="both",expand=True,padx=4)
            ctk.CTkLabel(card,text=f"{ddef.get('icon','')}\u2002{dname}",
                         font=ctk.CTkFont("Courier New",13,"bold"),text_color=color
                         ).pack(anchor="w",padx=12,pady=(12,4))
            ctk.CTkLabel(card,text=", ".join(ddef.get("kpis",[])),
                         font=self.F_SMALL,text_color=TXM,wraplength=200,justify="left"
                         ).pack(anchor="w",padx=12,pady=(0,10))

    # ── SYSTEM USERS ───────────────────────────────────────────────────────────
    def _build_tab_sysusers(self):
        f=self._tab("System Users")
        self._page_title(f,"System Users","Portal access and authentication \u2014 Admin only")
        tb=ctk.CTkFrame(f,fg_color="transparent"); tb.pack(fill="x",pady=(0,10))
        ctk.CTkButton(tb,text="+ Add System User",fg_color=GOLD,hover_color=GOLD_L,text_color=BG,
                      height=36,width=180,font=self.F_SMALL,command=lambda:self._su_dialog()
                      ).pack(side="right")
        cols=("Username","Full Name","Role","Employee ID","Created")
        widths={"Username":140,"Full Name":180,"Role":130,"Employee ID":130,"Created":110}
        self._su_tree=self._tree(f,cols,widths)
        act=ctk.CTkFrame(f,fg_color="transparent"); act.pack(fill="x",pady=8)
        ctk.CTkButton(act,text="\u270f\ufe0f Edit",fg_color=INFO,width=110,height=36,
                      command=self._edit_su).pack(side="left",padx=4)
        ctk.CTkButton(act,text="\U0001f5d1 Delete",fg_color=ERR,width=110,height=36,
                      command=self._del_su).pack(side="left",padx=4)

    def _refresh_sysusers(self):
        self._reload()
        for row in self._su_tree.get_children(): self._su_tree.delete(row)
        for uname,d in self.data["system_users"].items():
            rdef=ROLE_DEFINITIONS.get(d.get("role","staff"),{})
            rlabel=f"{rdef.get('icon','')}\u2002{ROLE_LABEL.get(d.get('role','staff'),d.get('role',''))}"
            self._su_tree.insert("","end",iid=uname,values=(
                uname,d.get("full_name",""),rlabel,d.get("emp_id","") or "\u2014",d.get("created","")))

    def _su_dialog(self, uname=None):
        d=self.data["system_users"].get(uname,{}) if uname else {}
        dlg=ctk.CTkToplevel(self); dlg.title("Edit System User" if uname else "Add System User")
        dlg.geometry("460x460"); dlg.grab_set(); dlg.configure(fg_color=BG)
        un_v=tk.StringVar(value=uname or ""); fn_v=tk.StringVar(value=d.get("full_name",""))
        rl_v=tk.StringVar(value=d.get("role","staff")); eid_v=tk.StringVar(value=d.get("emp_id","") or "")
        pw_v=tk.StringVar()
        for label,var,opts,show in [
            ("Username *",un_v,None,None),("Full Name",fn_v,None,None),
            ("Role",rl_v,["staff","manager","hr","admin"],None),
            ("Employee ID (optional)",eid_v,None,None),
            ("Password (blank = keep current)",pw_v,None,"\u2022")]:
            ctk.CTkLabel(dlg,text=label,font=self.F_SMALL,text_color=TXM).pack(anchor="w",padx=22,pady=(10,1))
            if opts:
                ctk.CTkOptionMenu(dlg,variable=var,values=opts,font=self.F_BODY).pack(fill="x",padx=22)
            else:
                ctk.CTkEntry(dlg,textvariable=var,height=34,show=show,font=self.F_BODY).pack(fill="x",padx=22)
        rp_lbl=ctk.CTkLabel(dlg,text="",font=self.F_SMALL,text_color=TXM,wraplength=380,justify="left")
        rp_lbl.pack(anchor="w",padx=22,pady=4)
        def _upd(*_):
            rdef=ROLE_DEFINITIONS.get(rl_v.get(),{})
            rp_lbl.configure(text=f"{rdef.get('icon','')}\u2002{rdef.get('label',rl_v.get())} \u2014 {rdef.get('purpose','')}")
        rl_v.trace_add("write",_upd); _upd()
        def _save():
            nu=un_v.get().strip(); fn=fn_v.get().strip(); role=rl_v.get()
            eid_=eid_v.get().strip() or None; pw=pw_v.get()
            if not nu: messagebox.showerror("Error","Username required."); return
            self._reload()
            if not uname and nu in self.data["system_users"]:
                messagebox.showerror("Error","Username exists."); return
            if not uname and len(pw)<6:
                messagebox.showerror("Error","Password min 6 chars."); return
            ex=self.data["system_users"].get(uname or nu,{})
            entry={"password_hash":ex.get("password_hash",hash_pw(pw)),
                   "photo":ex.get("photo"),"created":ex.get("created",datetime.now().strftime("%Y-%m-%d")),
                   "full_name":fn,"role":role,"emp_id":eid_}
            if pw and len(pw)>=6: entry["password_hash"]=hash_pw(pw)
            if uname and uname!=nu: del self.data["system_users"][uname]
            self.data["system_users"][nu]=entry
            audit(self.data,self.user["username"],"Saved system user",nu)
            save_data(self.data); dlg.destroy(); self._refresh_sysusers()
            messagebox.showinfo("Saved","System user saved.")
        ctk.CTkButton(dlg,text="\U0001f4be Save",fg_color=GOLD,hover_color=GOLD_L,text_color=BG,
                      height=40,command=_save).pack(pady=14,fill="x",padx=22)

    def _edit_su(self):
        sel=self._su_tree.selection()
        if not sel: messagebox.showwarning("No selection","Select a user."); return
        self._su_dialog(sel[0])

    def _del_su(self):
        sel=self._su_tree.selection()
        if not sel: messagebox.showwarning("No selection","Select a user."); return
        uname=sel[0]
        if uname==self.user["username"]: messagebox.showerror("Error","Cannot delete yourself."); return
        if not messagebox.askyesno("Confirm",f"Delete '{uname}'?"): return
        self._reload(); del self.data["system_users"][uname]
        audit(self.data,self.user["username"],"Deleted system user",uname)
        save_data(self.data); self._refresh_sysusers()

    # ── PROFILE ────────────────────────────────────────────────────────────────
    def _build_tab_profile(self):
        f=self._tab("Profile"); self._page_title(f,"My Profile","Account settings and role details")
        top=ctk.CTkFrame(f,fg_color="transparent"); top.pack(fill="x",pady=(0,12))
        rdef=ROLE_DEFINITIONS.get(self.user.get("role","staff"),{}); color=rdef.get("color",GOLD)
        acc=ctk.CTkFrame(top,fg_color=CARD,corner_radius=10); acc.pack(side="left",fill="both",expand=True,padx=(0,8))
        ctk.CTkLabel(acc,text=f"{rdef.get('icon','')}\u2002{self.user.get('full_name','\u2014')}",
                     font=ctk.CTkFont("Courier New",20,"bold"),text_color=color).pack(anchor="w",padx=18,pady=(18,2))
        ctk.CTkLabel(acc,text=f"@{self.user.get('username','')}",
                     font=self.F_MONO,text_color=TXM).pack(anchor="w",padx=18)
        ctk.CTkLabel(acc,text=ROLE_LABEL.get(self.user.get("role",""),"Staff"),
                     font=self.F_SMALL,text_color=color).pack(anchor="w",padx=18,pady=(2,10))
        emp_id=self.user.get("emp_id")
        if emp_id and emp_id in self.data["employees"]:
            e=self.data["employees"][emp_id]
            self._frow(acc,"Employee ID",emp_id); self._frow(acc,"Department",e.get("department",""))
            self._frow(acc,"Occupation",e.get("occupation",""))
        else:
            ctk.CTkLabel(acc,text="No employee record linked.",font=self.F_SMALL,text_color=TXM).pack(anchor="w",padx=18)
        ctk.CTkFrame(acc,fg_color="transparent",height=14).pack()
        rc=ctk.CTkFrame(top,fg_color=CARD,corner_radius=10,border_width=2,border_color=color)
        rc.pack(side="right",fill="both",expand=True)
        ctk.CTkLabel(rc,text="Your Role",font=self.F_HEAD,text_color=TX).pack(anchor="w",padx=14,pady=(14,4))
        ctk.CTkLabel(rc,text=rdef.get("purpose",""),font=self.F_SMALL,text_color=TXM,
                     wraplength=340,justify="left").pack(anchor="w",padx=14,pady=(0,8))
        for resp in rdef.get("responsibilities",[]):
            row=ctk.CTkFrame(rc,fg_color="transparent"); row.pack(fill="x",padx=14,pady=1)
            ctk.CTkLabel(row,text="\u2022",width=14,font=self.F_MONO,text_color=color).pack(side="left")
            ctk.CTkLabel(row,text=resp,font=self.F_SMALL,text_color=TX,anchor="w").pack(side="left")
        ctk.CTkFrame(rc,fg_color="transparent",height=14).pack()
        pw_c=ctk.CTkFrame(f,fg_color=CARD,corner_radius=10); pw_c.pack(fill="x")
        ctk.CTkLabel(pw_c,text="Change Password",font=self.F_HEAD,text_color=TX).pack(anchor="w",padx=18,pady=(14,8))
        self._pw_cur=tk.StringVar(); self._pw_new=tk.StringVar(); self._pw_conf=tk.StringVar()
        for label,var in [("Current Password","_pw_cur"),("New Password","_pw_new"),("Confirm New","_pw_conf")]:
            ctk.CTkLabel(pw_c,text=label,font=self.F_SMALL,text_color=TXM).pack(anchor="w",padx=18,pady=(4,1))
            ctk.CTkEntry(pw_c,textvariable=getattr(self,var),height=34,show="\u2022",
                         font=self.F_BODY).pack(fill="x",padx=18,pady=(0,3))
        ctk.CTkButton(pw_c,text="Update Password",fg_color=GOLD,hover_color=GOLD_L,text_color=BG,
                      height=40,command=self._change_pw).pack(pady=14,fill="x",padx=18)

    def _change_pw(self):
        c=self._pw_cur.get(); n=self._pw_new.get(); cf=self._pw_conf.get()
        if not c or not n: messagebox.showerror("Error","Fill all fields."); return
        if n!=cf: messagebox.showerror("Error","Passwords do not match."); return
        if len(n)<6: messagebox.showerror("Error","Min 6 characters."); return
        self._reload(); u=self.data["system_users"].get(self.user["username"],{})
        if not verify_pw(c,u.get("password_hash","")): messagebox.showerror("Error","Current password incorrect."); return
        u["password_hash"]=hash_pw(n)
        audit(self.data,self.user["username"],"Changed password",self.user["username"])
        save_data(self.data); self._pw_cur.set(""); self._pw_new.set(""); self._pw_conf.set("")
        messagebox.showinfo("Updated","Password updated successfully.")

    def _logout(self):
        if messagebox.askyesno("Sign Out","Sign out of OBSIDIAN CORPORATION?"):
            self.destroy()


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    login = LoginWindow()
    login.mainloop()
    if login.logged_in_user:
        app = ObsidianApp(login.logged_in_user)
        app.mainloop()
