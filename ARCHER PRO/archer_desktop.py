"""
ARCHER ENTERPRISE — Desktop Edition v2.0
CustomTkinter single-file application

pip install customtkinter openpyxl matplotlib pillow
python archer_desktop.py

Shares archer_data.json with archer_web.py.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, csv, io, base64, threading
from datetime import datetime
from PIL import Image, ImageTk

from archer_shared import (load_data, save_data, gen_emp_id, audit, notify,
                            hash_pw, verify_pw, export_csv_bytes, export_excel_bytes,
                            ROLE_LEVEL, ROLE_LABEL, EMP_FIELDS)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL_OK = True
except ImportError:
    MPL_OK = False

# ─── THEME ───────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG       = "#07091a"
SURFACE  = "#0c0f22"
CARD     = "#111428"
BORDER   = "#1e2240"
GOLD     = "#c9a84c"
GOLD_L   = "#e8c56a"
GOLD_D   = "#9a7a30"
OK       = "#3dba7a"
WARN     = "#e09a30"
ERR      = "#e05252"
INFO     = "#4f8ef7"
TX       = "#d4d8f0"
TXM      = "#5a6080"

ET_LABELS = {"permanent":"Permanent","contract":"Contract","probation":"Probation",
             "intern":"Intern","part_time":"Part Time"}
LT_LABELS = {"annual":"Annual Leave","sick":"Sick Leave","maternity":"Maternity/Paternity",
             "unpaid":"Unpaid Leave","other":"Other"}

# ─── LOGIN WINDOW ─────────────────────────────────────────────────────────────
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ARCHER ENTERPRISE — Login")
        self.geometry("460x560")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.logged_in_user = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        # Logo
        ctk.CTkLabel(self, text="ARCHER", font=ctk.CTkFont("Courier New", 52, "bold"),
                     text_color=GOLD).pack(pady=(50, 2))
        ctk.CTkLabel(self, text="ENTERPRISE", font=ctk.CTkFont("Courier New", 14),
                     text_color=TXM).pack()
        ctk.CTkLabel(self, text="─" * 36, text_color=GOLD_D).pack(pady=(8, 16))
        ctk.CTkLabel(self, text="Your Corporate Management & Service Agency",
                     font=ctk.CTkFont(size=10), text_color=GOLD_D).pack()

        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=44, pady=28)

        ctk.CTkLabel(card, text="ENTERPRISE PORTAL",
                     font=ctk.CTkFont("Courier New", 11, "bold"), text_color=GOLD).pack(pady=(18, 14))

        for label, attr, show in [("Username", "uvar", None), ("Password", "pvar", "•")]:
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=TXM).pack(anchor="w", padx=22)
            var = tk.StringVar()
            setattr(self, attr, var)
            ctk.CTkEntry(card, textvariable=var, height=38, show=show,
                         fg_color=BG, border_color=BORDER,
                         font=ctk.CTkFont("Courier New", 12)).pack(fill="x", padx=22, pady=(3, 10))

        self.err_lbl = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11), text_color=ERR)
        self.err_lbl.pack()

        ctk.CTkButton(card, text="SIGN IN", height=42, fg_color=GOLD, hover_color=GOLD_L,
                      text_color=BG, font=ctk.CTkFont("Courier New", 16, "bold"),
                      command=self._login).pack(fill="x", padx=22, pady=(4, 20))

        self.bind("<Return>", lambda _: self._login())

    def _login(self):
        uname = self.uvar.get().strip()
        pw    = self.pvar.get()
        data  = load_data()
        u = data["system_users"].get(uname)
        if not u or not verify_pw(pw, u.get("password_hash","")):
            self.err_lbl.configure(text="Invalid credentials.")
            return
        audit(data, uname, "Login", uname)
        save_data(data)
        self.logged_in_user = {"username": uname, **{k: v for k, v in u.items() if k != "password_hash"}}
        self.destroy()


# ─── MAIN APP ─────────────────────────────────────────────────────────────────
class ArcherApp(ctk.CTk):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.data = load_data()
        self.sel_emp    = None
        self.sel_promo  = None
        self.sel_leave  = None
        self.lvl        = ROLE_LEVEL.get(user.get("role","staff"), 1)

        self.title("ARCHER ENTERPRISE — Desktop Edition")
        self.geometry("1340x840")
        self.minsize(1100, 680)
        self.configure(fg_color=BG)

        self._fonts()
        self._build()

    def _fonts(self):
        self.F_TITLE   = ctk.CTkFont("Courier New", 28, "bold")
        self.F_HEAD    = ctk.CTkFont("Courier New", 17, "bold")
        self.F_BODY    = ctk.CTkFont("Helvetica",   13)
        self.F_SMALL   = ctk.CTkFont("Helvetica",   11)
        self.F_MONO    = ctk.CTkFont("Courier New", 12)

    # ── BUILD ─────────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=58)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="ARCHER", font=ctk.CTkFont("Courier New", 20, "bold"),
                     text_color=GOLD).pack(side="left", padx=22)
        ctk.CTkLabel(hdr, text="ENTERPRISE", font=ctk.CTkFont("Helvetica", 10),
                     text_color=TXM).pack(side="left")
        ctk.CTkLabel(hdr, text=f"  {self.user.get('full_name','')}  ·  {ROLE_LABEL.get(self.user.get('role',''),'Staff')}",
                     font=self.F_SMALL, text_color=GOLD).pack(side="right", padx=22)
        ctk.CTkButton(hdr, text="Sign Out", width=80, height=30, fg_color=ERR,
                      hover_color="#c94040", font=self.F_SMALL,
                      command=self._logout).pack(side="right", padx=4)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar
        self._sb = ctk.CTkFrame(body, fg_color=SURFACE, width=226, corner_radius=0)
        self._sb.pack(side="left", fill="y"); self._sb.pack_propagate(False)
        self._build_sidebar()

        # Content
        self._content = ctk.CTkFrame(body, fg_color="transparent")
        self._content.pack(side="right", fill="both", expand=True, padx=20, pady=18)

        self._tabs = {}
        self._build_tab_dashboard()
        self._build_tab_employees()
        self._build_tab_departments()
        self._build_tab_promotions()
        self._build_tab_leave()
        if self.lvl >= 3: self._build_tab_payroll()
        if self.lvl >= 3: self._build_tab_audit()
        if self.lvl >= 4: self._build_tab_sysusers()
        self._build_tab_profile()

        self._show("Dashboard")

    def _build_sidebar(self):
        ctk.CTkLabel(self._sb, text="NAVIGATION",
                     font=ctk.CTkFont("Helvetica", 9, "bold"), text_color=TXM
                     ).pack(anchor="w", padx=18, pady=(18, 4))

        self._nb: dict[str, ctk.CTkButton] = {}
        nav = [("📊","Dashboard"), ("👥","Employees"), ("🏢","Departments"),
               ("🏆","Promotions"), ("📅","Leave")]
        if self.lvl >= 3:
            nav += [("💰","Payroll"), ("📋","Audit Log")]
        if self.lvl >= 4:
            nav += [("🔐","System Users")]
        nav += [("⚙️","Profile")]

        for icon, name in nav:
            btn = ctk.CTkButton(self._sb, text=f"  {icon}  {name}", width=208, height=38,
                                anchor="w", fg_color="transparent", text_color=TXM,
                                hover_color="#1a1f38", font=self.F_BODY,
                                command=lambda n=name: self._show(n))
            btn.pack(pady=1, padx=8)
            self._nb[name] = btn

    def _show(self, name: str):
        for f in self._tabs.values(): f.pack_forget()
        self._tabs[name].pack(fill="both", expand=True)
        for k, btn in self._nb.items():
            btn.configure(fg_color=(GOLD_D if k == name else "transparent"),
                          text_color=(BG if k == name else TXM))
        refresh = {
            "Dashboard": self._refresh_dashboard,
            "Employees": self._refresh_employees,
            "Departments": self._refresh_departments,
            "Promotions": self._refresh_promotions,
            "Leave": self._refresh_leave,
            "Payroll": self._refresh_payroll if self.lvl >= 3 else None,
            "Audit Log": self._refresh_audit if self.lvl >= 3 else None,
            "System Users": self._refresh_sysusers if self.lvl >= 4 else None,
        }
        fn = refresh.get(name)
        if fn: fn()

    def _reload(self):
        from archer_shared import _normalize
        self.data = _normalize(load_data())

    # ── COMMON WIDGETS ────────────────────────────────────────────────────────
    def _tab(self, name: str) -> ctk.CTkScrollableFrame:
        f = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._tabs[name] = f
        return f

    def _title(self, parent, text: str):
        ctk.CTkLabel(parent, text=text, font=self.F_TITLE, text_color="#ffffff"
                     ).pack(anchor="w", pady=(0, 16))

    def _stat_row(self, parent, stats: list) -> ctk.CTkFrame:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))
        for label, val, color in stats:
            card = ctk.CTkFrame(row, fg_color=color, corner_radius=12)
            card.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(card, text=str(val),
                         font=ctk.CTkFont("Courier New", 36, "bold"),
                         text_color="#fff").pack(pady=(14, 2))
            ctk.CTkLabel(card, text=label, font=self.F_SMALL, text_color="#fff").pack(pady=(0, 14))
        return row

    def _tree(self, parent, cols: list, heights: dict | None = None) -> ttk.Treeview:
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
        card.pack(fill="both", expand=True)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("A.Treeview", background="#111428", foreground=TX,
                        fieldbackground="#111428", rowheight=30,
                        font=("Helvetica", 12))
        style.configure("A.Treeview.Heading", background=SURFACE, foreground=TXM,
                        font=("Helvetica", 10, "bold"), relief="flat")
        style.map("A.Treeview", background=[("selected", GOLD_D)],
                  foreground=[("selected", "#fff")])
        tree = ttk.Treeview(card, columns=cols, show="headings",
                             selectmode="browse", style="A.Treeview")
        for col in cols:
            w = (heights or {}).get(col, 130)
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=50)
        vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(card, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        card.rowconfigure(0, weight=1); card.columnconfigure(0, weight=1)
        return tree

    # ── DASHBOARD ─────────────────────────────────────────────────────────────
    def _build_tab_dashboard(self):
        f = self._tab("Dashboard")
        self._title(f, "Dashboard")
        self._dash_stats_frame = ctk.CTkFrame(f, fg_color="transparent")
        self._dash_stats_frame.pack(fill="x")
        if MPL_OK:
            self._dash_chart_frame = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
            self._dash_chart_frame.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(f, text="Recent Audit Activity",
                     font=self.F_HEAD, text_color=TX).pack(anchor="w", pady=(16, 6))
        self._dash_audit = ctk.CTkTextbox(f, height=200, font=self.F_MONO,
                                          fg_color=CARD, state="disabled")
        self._dash_audit.pack(fill="x")

    def _refresh_dashboard(self):
        self._reload()
        emps   = list(self.data["employees"].values())
        active = sum(1 for e in emps if e.get("status") == "active")
        pend_p = sum(len([r for r in e.get("promotion_requests",[]) if r["status"]=="pending"]) for e in emps)
        pend_l = len([r for r in self.data.get("leave_requests",[]) if r.get("status")=="pending"])
        for w in self._dash_stats_frame.winfo_children(): w.destroy()
        self._stat_row(self._dash_stats_frame, [
            ("Total Employees", len(emps), INFO),
            ("Active", active, OK),
            ("Pending Promotions", pend_p, WARN),
            ("Pending Leave", pend_l, ERR),
            ("Departments", len(self.data["departments"]), GOLD_D),
        ])
        if MPL_OK:
            for w in self._dash_chart_frame.winfo_children(): w.destroy()
            self._draw_charts()
        # audit
        lines = self.data.get("audit_log", [])[:15]
        self._dash_audit.configure(state="normal")
        self._dash_audit.delete("1.0", "end")
        for a in lines:
            self._dash_audit.insert("end", f"  {a['ts']}  {a['user']}  {a['action']}  {a['target']}\n")
        self._dash_audit.configure(state="disabled")

    def _draw_charts(self):
        emps = list(self.data["employees"].values())
        dmap = {}
        for e in emps:
            d = e.get("department","Unknown") or "Unknown"
            dmap[d] = dmap.get(d, 0) + 1

        gold_shades = [GOLD, "#b08540", "#7a5e2c", "#4f3d1a", "#e8c56a", "#c9a84c", "#9a7a30"]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 2.8), facecolor=CARD)
        for ax in (ax1, ax2):
            ax.set_facecolor(CARD)
            for spine in ax.spines.values(): spine.set_edgecolor(BORDER)

        if dmap:
            ax1.pie(list(dmap.values()), labels=list(dmap.keys()),
                    colors=gold_shades[:len(dmap)],
                    textprops={"color": TX, "fontsize": 9}, startangle=90)
        ax1.set_title("By Department", color=TX, fontsize=10)

        tmap = {}
        for e in emps:
            t = ET_LABELS.get(e.get("employment_type",""), e.get("employment_type","Unknown") or "Unknown")
            tmap[t] = tmap.get(t, 0) + 1
        if tmap:
            ax2.bar(list(tmap.keys()), list(tmap.values()),
                    color=gold_shades[:len(tmap)], edgecolor="none")
        ax2.set_title("Employment Types", color=TX, fontsize=10)
        ax2.tick_params(colors=TXM, labelsize=9)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self._dash_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=8)
        plt.close(fig)

    # ── EMPLOYEES ─────────────────────────────────────────────────────────────
    def _build_tab_employees(self):
        f = self._tab("Employees")
        self._title(f, "Employees")
        tb_row = ctk.CTkFrame(f, fg_color="transparent")
        tb_row.pack(fill="x", pady=(0, 10))
        self._emp_search = tk.StringVar()
        self._emp_search.trace_add("write", lambda *_: self._refresh_employees())
        ctk.CTkEntry(tb_row, textvariable=self._emp_search, width=320, height=36,
                     placeholder_text="🔍  Search name, ID, department…",
                     font=self.F_BODY).pack(side="left")
        self._emp_dept_var = tk.StringVar(value="All Departments")
        self._emp_dept_menu = ctk.CTkOptionMenu(tb_row, variable=self._emp_dept_var,
                                                 values=["All Departments"],
                                                 command=lambda _: self._refresh_employees(),
                                                 width=160, font=self.F_SMALL)
        self._emp_dept_menu.pack(side="left", padx=8)
        btns = []
        btns.append(("📤 Export CSV",  lambda: self._export_csv(),  GOLD_D))
        btns.append(("📤 Excel",       lambda: self._export_xl(),   GOLD_D))
        if self.lvl >= 3:
            btns.append(("📥 Import",  lambda: self._import_emps(), BORDER))
            btns.append(("+ Add",      lambda: self._emp_dialog(),  GOLD))
        for txt, cmd, col in btns:
            ctk.CTkButton(tb_row, text=txt, width=100, height=36, fg_color=col,
                          hover_color=GOLD_L if col==GOLD else "#2a2f48",
                          text_color=BG if col==GOLD else TX,
                          font=self.F_SMALL, command=cmd).pack(side="right", padx=3)

        cols = ("ID","Name","Department","Occupation","Type","Status","Added")
        widths = {"ID":130,"Name":170,"Department":130,"Occupation":150,"Type":100,"Status":80,"Added":90}
        self._emp_tree = self._tree(f, cols, widths)
        self._emp_tree.bind("<Double-1>", self._on_emp_dbl)

        if self.lvl >= 3:
            act = ctk.CTkFrame(f, fg_color="transparent")
            act.pack(fill="x", pady=8)
            ctk.CTkButton(act, text="✏️ Edit Selected", width=130, height=36,
                          fg_color=INFO, font=self.F_SMALL,
                          command=lambda: self._emp_dialog(self.sel_emp)).pack(side="left", padx=4)
            ctk.CTkButton(act, text="🗑 Delete Selected", width=130, height=36,
                          fg_color=ERR, font=self.F_SMALL,
                          command=self._del_emp).pack(side="left", padx=4)

    def _refresh_employees(self):
        self._reload()
        depts = ["All Departments"] + list(self.data["departments"].keys())
        self._emp_dept_menu.configure(values=depts)
        q   = self._emp_search.get().lower()
        fd  = self._emp_dept_var.get()
        for row in self._emp_tree.get_children(): self._emp_tree.delete(row)
        for eid, e in self.data["employees"].items():
            if self.lvl < 2 and eid != self.user.get("emp_id"): continue
            if fd not in ("All Departments","") and e.get("department") != fd: continue
            if q and not any(q in str(v).lower() for v in [eid, e.get("full_name",""), e.get("department",""), e.get("occupation","")]):
                continue
            self._emp_tree.insert("", "end", iid=eid, values=(
                eid, e.get("full_name",""), e.get("department",""),
                e.get("occupation",""),
                ET_LABELS.get(e.get("employment_type",""), e.get("employment_type","")),
                e.get("status",""), e.get("date_added",""),
            ))

    def _on_emp_dbl(self, event):
        sel = self._emp_tree.selection()
        if not sel: return
        self.sel_emp = sel[0]
        self._emp_view(self.sel_emp)

    def _emp_view(self, eid: str):
        e = self.data["employees"].get(eid, {})
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Employee — {eid}")
        dlg.geometry("480x520")
        dlg.grab_set()
        rows = [
            ("ID", eid), ("Full Name", e.get("full_name","")), ("Email", e.get("email","")),
            ("Department", e.get("department","")), ("Occupation", e.get("occupation","")),
            ("Role / Level", e.get("role","")), ("Purpose", e.get("purpose","")),
            ("Employment Type", ET_LABELS.get(e.get("employment_type",""),e.get("employment_type",""))),
            ("Status", e.get("status","")), ("Location", e.get("location","")),
            ("Age", e.get("age","")), ("Contract End", e.get("contract_end","")),
            ("Date Added", e.get("date_added","")),
        ]
        if self.lvl >= 3 and e.get("salary"):
            rows.append(("Salary", f"{e.get('salary_currency','USD')} {float(e['salary']):,.0f}"))
        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=20, pady=10)
        for k, v in rows:
            row = ctk.CTkFrame(sf, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=k, width=130, anchor="w", font=self.F_SMALL, text_color=TXM).pack(side="left")
            ctk.CTkLabel(row, text=str(v), anchor="w", font=self.F_BODY).pack(side="left")
        ctk.CTkButton(dlg, text="Close", command=dlg.destroy, fg_color=GOLD_D).pack(pady=10)

    def _emp_dialog(self, eid: str = None):
        e = self.data["employees"].get(eid, {}) if eid else {}
        dlg = ctk.CTkToplevel(self)
        dlg.title("Edit Employee" if eid else "Add Employee")
        dlg.geometry("580x660")
        dlg.grab_set()
        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=20, pady=10)
        fields = [
            ("Full Name *", "full_name", None),
            ("Email", "email", None),
            ("Department", "department", list(self.data["departments"].keys())),
            ("Occupation", "occupation", None),
            ("Role / Level", "role", None),
            ("Purpose / Job Description", "purpose", None),
            ("Age", "age", None),
            ("Location", "location", None),
            ("Employment Type", "employment_type",
             list(ET_LABELS.keys())),
            ("Status", "status", ["active","inactive","on_leave"]),
            ("Contract End Date (YYYY-MM-DD)", "contract_end", None),
            ("Salary", "salary", None),
            ("Currency", "salary_currency", ["USD","EUR","GBP","NGN","KES","ZAR","GHS"]),
        ]
        vars_: dict[str, tk.StringVar] = {}
        for label, key, opts in fields:
            ctk.CTkLabel(sf, text=label, anchor="w", font=self.F_SMALL, text_color=TXM).pack(anchor="w", pady=(5,1))
            var = tk.StringVar(value=str(e.get(key,"") or ""))
            if opts:
                ctk.CTkOptionMenu(sf, variable=var, values=opts, font=self.F_BODY).pack(fill="x", pady=(0,2))
            else:
                ctk.CTkEntry(sf, textvariable=var, height=34, font=self.F_BODY).pack(fill="x", pady=(0,2))
            vars_[key] = var

        def _save():
            fn = vars_["full_name"].get().strip()
            if not fn: messagebox.showerror("Error", "Full name is required."); return
            self._reload()
            eid_ = eid or gen_emp_id(self.data)
            emp = {k: v.get().strip() for k, v in vars_.items()}
            emp["date_added"] = e.get("date_added", datetime.now().strftime("%Y-%m-%d"))
            emp.setdefault("promotion_requests", e.get("promotion_requests", []))
            emp.setdefault("photo", e.get("photo"))
            self.data["employees"][eid_] = emp
            audit(self.data, self.user["username"], "Updated employee" if eid else "Added employee", eid_, fn)
            if not eid:
                notify(self.data, "success", f"New employee: {fn} ({eid_})")
            save_data(self.data)
            dlg.destroy()
            self._refresh_employees()
            messagebox.showinfo("Saved", f"Employee {eid_ } saved.")

        ctk.CTkButton(dlg, text="💾 Save Employee", fg_color=GOLD, text_color=BG,
                      hover_color=GOLD_L, height=40, command=_save).pack(pady=12, fill="x", padx=20)

    def _del_emp(self):
        sel = self._emp_tree.selection()
        if not sel: messagebox.showwarning("No selection", "Select an employee first."); return
        eid = sel[0]
        if not messagebox.askyesno("Confirm", f"Delete employee {eid}? This cannot be undone."): return
        self._reload()
        name = self.data["employees"].get(eid, {}).get("full_name","")
        del self.data["employees"][eid]
        audit(self.data, self.user["username"], "Deleted employee", eid, name)
        save_data(self.data)
        self._refresh_employees()
        messagebox.showinfo("Deleted", f"Employee {eid} deleted.")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path: return
        self._reload()
        with open(path, "wb") as f: f.write(export_csv_bytes(self.data["employees"]))
        messagebox.showinfo("Exported", f"Saved → {path}")

    def _export_xl(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not path: return
        self._reload()
        b = export_excel_bytes(self.data["employees"])
        if not b: messagebox.showerror("Error", "Install openpyxl first."); return
        with open(path, "wb") as f: f.write(b)
        messagebox.showinfo("Exported", f"Saved → {path}")

    def _import_emps(self):
        path = filedialog.askopenfilename(filetypes=[("JSON/CSV","*.json *.csv")])
        if not path: return
        self._reload()
        count = 0
        try:
            if path.lower().endswith(".json"):
                with open(path) as f: raw = json.load(f)
                if isinstance(raw, dict) and "employees" in raw:
                    emp_data = raw["employees"]
                    if isinstance(emp_data, list):
                        for emp in emp_data:
                            emp = dict(emp)
                            eid = emp.pop("id", None) or gen_emp_id(self.data)
                            emp.setdefault("promotion_requests", [])
                            self.data["employees"][eid] = emp; count += 1
                    else:
                        for eid, emp in emp_data.items():
                            self.data["employees"][eid] = emp; count += 1
                elif isinstance(raw, dict):
                    for eid, emp in raw.items():
                        self.data["employees"][eid] = emp; count += 1
                elif isinstance(raw, list):
                    for emp in raw:
                        eid = emp.pop("id", None) or gen_emp_id(self.data)
                        self.data["employees"][eid] = emp; count += 1
            elif path.lower().endswith(".csv"):
                with open(path, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        eid = row.pop("id", None) or gen_emp_id(self.data)
                        self.data["employees"][eid] = dict(row); count += 1
            audit(self.data, self.user["username"], "Imported employees", f"count={count}")
            save_data(self.data)
            self._refresh_employees()
            messagebox.showinfo("Imported", f"Imported {count} employees.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # ── DEPARTMENTS ───────────────────────────────────────────────────────────
    def _build_tab_departments(self):
        f = self._tab("Departments")
        self._title(f, "Departments")
        if self.lvl >= 3:
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", pady=(0, 10))
            ctk.CTkButton(row, text="+ Add Department", fg_color=GOLD, text_color=BG,
                          hover_color=GOLD_L, height=36, width=150, font=self.F_SMALL,
                          command=lambda: self._dept_dialog()).pack(side="right")
        cols = ("Department","Description","Head ID","Employees")
        self._dept_tree = self._tree(f, cols, {"Department":160,"Description":300,"Head ID":120,"Employees":80})
        if self.lvl >= 3:
            act = ctk.CTkFrame(f, fg_color="transparent")
            act.pack(fill="x", pady=8)
            ctk.CTkButton(act, text="✏️ Edit Selected", width=130, height=36,
                          fg_color=INFO, font=self.F_SMALL,
                          command=self._edit_dept).pack(side="left", padx=4)
            ctk.CTkButton(act, text="🗑 Delete", width=100, height=36,
                          fg_color=ERR, font=self.F_SMALL,
                          command=self._del_dept).pack(side="left", padx=4)

    def _refresh_departments(self):
        self._reload()
        for row in self._dept_tree.get_children(): self._dept_tree.delete(row)
        for name, d in self.data["departments"].items():
            cnt = sum(1 for e in self.data["employees"].values() if e.get("department") == name)
            self._dept_tree.insert("", "end", iid=name, values=(
                name, d.get("description",""), d.get("head_id","—"), cnt))

    def _dept_dialog(self, name: str = None):
        d = self.data["departments"].get(name, {}) if name else {}
        dlg = ctk.CTkToplevel(self)
        dlg.title("Edit Department" if name else "Add Department")
        dlg.geometry("460x320"); dlg.grab_set()
        nm_v = tk.StringVar(value=name or "")
        ds_v = tk.StringVar(value=d.get("description",""))
        hd_v = tk.StringVar(value=d.get("head_id","") or "")
        for label, var in [("Department Name *", nm_v), ("Description", ds_v), ("Head Employee ID (optional)", hd_v)]:
            ctk.CTkLabel(dlg, text=label, font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=22, pady=(10,1))
            ctk.CTkEntry(dlg, textvariable=var, height=34, font=self.F_BODY).pack(fill="x", padx=22)

        def _save():
            new_name = nm_v.get().strip()
            if not new_name: messagebox.showerror("Error","Name required."); return
            self._reload()
            if name and name != new_name and new_name in self.data["departments"]:
                messagebox.showerror("Error","Name already exists."); return
            dept = {"description": ds_v.get().strip(), "head_id": hd_v.get().strip() or None}
            if name and name != new_name:
                del self.data["departments"][name]
            self.data["departments"][new_name] = dept
            audit(self.data, self.user["username"], "Saved department", new_name)
            save_data(self.data); dlg.destroy(); self._refresh_departments()
            messagebox.showinfo("Saved", f"Department '{new_name}' saved.")

        ctk.CTkButton(dlg, text="💾 Save", fg_color=GOLD, text_color=BG,
                      hover_color=GOLD_L, height=38, command=_save).pack(pady=16, padx=22, fill="x")

    def _edit_dept(self):
        sel = self._dept_tree.selection()
        if not sel: messagebox.showwarning("No selection","Select a department."); return
        self._dept_dialog(sel[0])

    def _del_dept(self):
        sel = self._dept_tree.selection()
        if not sel: messagebox.showwarning("No selection","Select a department."); return
        name = sel[0]
        if not messagebox.askyesno("Confirm",f"Delete department '{name}'?"): return
        self._reload()
        del self.data["departments"][name]
        audit(self.data, self.user["username"], "Deleted department", name)
        save_data(self.data); self._refresh_departments()

    # ── PROMOTIONS ────────────────────────────────────────────────────────────
    def _build_tab_promotions(self):
        f = self._tab("Promotions")
        self._title(f, "Promotions")
        if self.lvl >= 2:
            card = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
            card.pack(fill="x", pady=(0,12))
            ctk.CTkLabel(card, text="Submit Request", font=self.F_HEAD, text_color=TX).pack(anchor="w", padx=18, pady=(14,6))
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=(0,14))
            self._p_eid = tk.StringVar()
            self._p_role = tk.StringVar()
            ctk.CTkLabel(row, text="Employee ID:", font=self.F_SMALL, text_color=TXM).pack(side="left")
            ctk.CTkEntry(row, textvariable=self._p_eid, width=180, height=34, font=self.F_BODY,
                         placeholder_text="ARCH-2026-0001").pack(side="left", padx=(6,14))
            ctk.CTkLabel(row, text="Requested Role:", font=self.F_SMALL, text_color=TXM).pack(side="left")
            ctk.CTkEntry(row, textvariable=self._p_role, width=180, height=34, font=self.F_BODY,
                         placeholder_text="e.g. Senior Engineer").pack(side="left", padx=6)
            ctk.CTkButton(row, text="Submit", width=90, height=34, fg_color=GOLD, text_color=BG,
                          hover_color=GOLD_L, command=self._sub_promo).pack(side="left", padx=8)

        cols = ("Employee ID","Name","Current Role","Requested Role","Date","Status")
        widths = {"Employee ID":120,"Name":150,"Current Role":130,"Requested Role":140,"Date":100,"Status":90}
        self._promo_tree = self._tree(f, cols, widths)
        self._promo_tree.bind("<<TreeviewSelect>>", lambda e: self._on_promo_sel())

        if self.lvl >= 3:
            act = ctk.CTkFrame(f, fg_color="transparent")
            act.pack(fill="x", pady=8)
            ctk.CTkButton(act, text="✅ Approve", fg_color=OK, hover_color="#2ea66b", width=120, height=36,
                          command=lambda: self._res_promo("approved")).pack(side="left", padx=4)
            ctk.CTkButton(act, text="❌ Deny", fg_color=ERR, hover_color="#c94040", width=120, height=36,
                          command=lambda: self._res_promo("denied")).pack(side="left", padx=4)

    def _refresh_promotions(self):
        self._reload()
        for row in self._promo_tree.get_children(): self._promo_tree.delete(row)
        for eid, e in self.data["employees"].items():
            for i, req in enumerate(e.get("promotion_requests", [])):
                iid = f"{eid}::{i}"
                self._promo_tree.insert("", "end", iid=iid, values=(
                    eid, e.get("full_name",""), req.get("current_role",""),
                    req.get("requested_role",""), req.get("date",""), req.get("status","").capitalize()))

    def _on_promo_sel(self):
        sel = self._promo_tree.selection()
        self.sel_promo = sel[0] if sel else None

    def _sub_promo(self):
        eid  = self._p_eid.get().strip()
        role = self._p_role.get().strip()
        self._reload()
        if eid not in self.data["employees"]:
            messagebox.showerror("Not Found", f"Employee '{eid}' not found."); return
        if not role:
            messagebox.showerror("Missing", "Requested role is required."); return
        e = self.data["employees"][eid]
        req = {"requested_role": role, "current_role": e.get("role",""), "status": "pending",
               "date": datetime.now().strftime("%Y-%m-%d"), "resolved_date": "", "resolved_by": ""}
        e.setdefault("promotion_requests", []).append(req)
        audit(self.data, self.user["username"], "Submitted promotion", eid, f"→ {role}")
        notify(self.data, "info", f"Promotion request: {e.get('full_name',eid)} → {role}")
        save_data(self.data); self._p_eid.set(""); self._p_role.set("")
        self._refresh_promotions(); messagebox.showinfo("Submitted", "Promotion request submitted.")

    def _res_promo(self, resolution: str):
        if not self.sel_promo: messagebox.showwarning("No selection","Select a request first."); return
        eid, idx_s = self.sel_promo.split("::")
        self._reload()
        req = self.data["employees"][eid]["promotion_requests"][int(idx_s)]
        if req["status"] != "pending": messagebox.showwarning("Already resolved","Request already resolved."); return
        req["status"] = resolution
        req["resolved_date"] = datetime.now().strftime("%Y-%m-%d")
        req["resolved_by"] = self.user["username"]
        if resolution == "approved":
            self.data["employees"][eid]["role"] = req["requested_role"]
        audit(self.data, self.user["username"], f"Promotion {resolution}", eid, req["requested_role"])
        save_data(self.data); self._refresh_promotions()
        messagebox.showinfo("Done", f"Promotion request {resolution}.")

    # ── LEAVE ─────────────────────────────────────────────────────────────────
    def _build_tab_leave(self):
        f = self._tab("Leave")
        self._title(f, "Leave Management")
        card = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
        card.pack(fill="x", pady=(0,12))
        ctk.CTkLabel(card, text="Submit Leave Request", font=self.F_HEAD, text_color=TX).pack(anchor="w", padx=18, pady=(14,6))
        sf = ctk.CTkFrame(card, fg_color="transparent")
        sf.pack(fill="x", padx=18, pady=(0,14))
        self._lv_eid   = tk.StringVar()
        self._lv_type  = tk.StringVar(value="annual")
        self._lv_start = tk.StringVar()
        self._lv_end   = tk.StringVar()
        row1 = ctk.CTkFrame(sf, fg_color="transparent"); row1.pack(fill="x", pady=3)
        if self.lvl >= 3:
            ctk.CTkLabel(row1, text="Employee ID:", font=self.F_SMALL, text_color=TXM, width=100).pack(side="left")
            ctk.CTkEntry(row1, textvariable=self._lv_eid, width=170, height=32,
                         placeholder_text="ARCH-2026-0001 or blank=self").pack(side="left", padx=(4,16))
        ctk.CTkLabel(row1, text="Type:", font=self.F_SMALL, text_color=TXM).pack(side="left")
        ctk.CTkOptionMenu(row1, variable=self._lv_type,
                          values=list(LT_LABELS.keys()), width=150,
                          font=self.F_SMALL).pack(side="left", padx=(4,0))
        row2 = ctk.CTkFrame(sf, fg_color="transparent"); row2.pack(fill="x", pady=3)
        for lbl, var, ph in [("Start:", self._lv_start, "YYYY-MM-DD"), ("End:", self._lv_end, "YYYY-MM-DD")]:
            ctk.CTkLabel(row2, text=lbl, font=self.F_SMALL, text_color=TXM, width=42).pack(side="left")
            ctk.CTkEntry(row2, textvariable=var, width=130, height=32, placeholder_text=ph,
                         font=self.F_MONO).pack(side="left", padx=(4,16))
        ctk.CTkButton(row2, text="Submit Request", fg_color=GOLD, text_color=BG,
                      hover_color=GOLD_L, height=32, command=self._sub_leave).pack(side="left")

        cols = ("Employee ID","Name","Type","From","To","Days","Status")
        widths = {"Employee ID":120,"Name":150,"Type":130,"From":100,"To":100,"Days":60,"Status":90}
        self._leave_tree = self._tree(f, cols, widths)
        self._leave_tree.bind("<<TreeviewSelect>>", lambda e: self._on_leave_sel())

        if self.lvl >= 3:
            act = ctk.CTkFrame(f, fg_color="transparent")
            act.pack(fill="x", pady=8)
            ctk.CTkButton(act, text="✅ Approve", fg_color=OK, hover_color="#2ea66b", width=120, height=36,
                          command=lambda: self._res_leave("approved")).pack(side="left", padx=4)
            ctk.CTkButton(act, text="❌ Deny", fg_color=ERR, hover_color="#c94040", width=120, height=36,
                          command=lambda: self._res_leave("denied")).pack(side="left", padx=4)

    def _refresh_leave(self):
        self._reload()
        for row in self._leave_tree.get_children(): self._leave_tree.delete(row)
        for i, req in enumerate(self.data.get("leave_requests", [])):
            if self.lvl < 3 and req.get("emp_id") != self.user.get("emp_id"): continue
            e = self.data["employees"].get(req.get("emp_id",""), {})
            start = req.get("start_date",""); end_ = req.get("end_date","")
            try: days = str((datetime.strptime(end_,"%Y-%m-%d") - datetime.strptime(start,"%Y-%m-%d")).days + 1)
            except Exception: days = "—"
            self._leave_tree.insert("", "end", iid=str(i), values=(
                req.get("emp_id",""), e.get("full_name",""),
                LT_LABELS.get(req.get("leave_type",""), req.get("leave_type","")),
                start, end_, days, req.get("status","").capitalize()))

    def _on_leave_sel(self):
        sel = self._leave_tree.selection()
        self.sel_leave = int(sel[0]) if sel else None

    def _sub_leave(self):
        eid   = self._lv_eid.get().strip() or self.user.get("emp_id","")
        ltype = self._lv_type.get()
        s     = self._lv_start.get().strip()
        e2    = self._lv_end.get().strip()
        if not s or not e2: messagebox.showerror("Error","Start and end dates required."); return
        if not eid: messagebox.showerror("Error","No employee ID found."); return
        self._reload()
        if eid not in self.data["employees"]: messagebox.showerror("Error",f"Employee '{eid}' not found."); return
        req = {"emp_id": eid, "leave_type": ltype, "start_date": s, "end_date": e2, "notes": "",
               "status": "pending", "submitted_by": self.user["username"],
               "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
        self.data.setdefault("leave_requests", []).append(req)
        audit(self.data, self.user["username"], "Leave submitted", eid, ltype)
        notify(self.data, "info", f"Leave request: {self.data['employees'][eid].get('full_name',eid)}")
        save_data(self.data)
        self._lv_eid.set(""); self._lv_start.set(""); self._lv_end.set("")
        self._refresh_leave(); messagebox.showinfo("Submitted","Leave request submitted.")

    def _res_leave(self, resolution: str):
        if self.sel_leave is None: messagebox.showwarning("No selection","Select a request first."); return
        self._reload()
        reqs = self.data.get("leave_requests",[])
        if self.sel_leave >= len(reqs): return
        req = reqs[self.sel_leave]
        if req["status"] != "pending": messagebox.showwarning("Already resolved","Already resolved."); return
        req["status"] = resolution
        req["resolved_by"] = self.user["username"]
        req["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        audit(self.data, self.user["username"], f"Leave {resolution}", req["emp_id"], req.get("leave_type",""))
        save_data(self.data); self.sel_leave = None
        self._refresh_leave(); messagebox.showinfo("Done", f"Leave {resolution}.")

    # ── PAYROLL ───────────────────────────────────────────────────────────────
    def _build_tab_payroll(self):
        f = self._tab("Payroll")
        self._title(f, "Payroll & Salary")
        tb = ctk.CTkFrame(f, fg_color="transparent"); tb.pack(fill="x", pady=(0,10))
        self._pr_search = tk.StringVar()
        self._pr_search.trace_add("write", lambda *_: self._refresh_payroll())
        ctk.CTkEntry(tb, textvariable=self._pr_search, width=280, height=36,
                     placeholder_text="🔍  Search…", font=self.F_BODY).pack(side="left")
        ctk.CTkButton(tb, text="📤 Export CSV", fg_color=GOLD_D, width=110, height=36,
                      command=self._export_pay_csv).pack(side="right", padx=3)
        ctk.CTkButton(tb, text="📤 Excel", fg_color=GOLD_D, width=100, height=36,
                      command=self._export_pay_xl).pack(side="right", padx=3)
        self._pr_stats_frame = ctk.CTkFrame(f, fg_color="transparent"); self._pr_stats_frame.pack(fill="x", pady=(0,10))
        cols = ("ID","Name","Department","Occupation","Salary","Currency","Type")
        widths = {"ID":130,"Name":160,"Department":130,"Occupation":140,"Salary":110,"Currency":70,"Type":110}
        self._pay_tree = self._tree(f, cols, widths)
        self._pay_tree.bind("<Double-1>", self._on_pay_dbl)
        act = ctk.CTkFrame(f, fg_color="transparent"); act.pack(fill="x", pady=8)
        ctk.CTkButton(act, text="✏️ Edit Salary", fg_color=INFO, width=120, height=36,
                      command=self._pay_dialog).pack(side="left")

    def _refresh_payroll(self):
        self._reload()
        q = self._pr_search.get().lower()
        rows = [(eid, e) for eid, e in self.data["employees"].items()
                if not q or any(q in str(v).lower() for v in [eid, e.get("full_name",""), e.get("department","")])]
        total = sum(float(e.get("salary","0") or 0) for _, e in rows)
        with_sal = sum(1 for _, e in rows if e.get("salary"))
        for w in self._pr_stats_frame.winfo_children(): w.destroy()
        self._stat_row(self._pr_stats_frame, [
            ("Total Employees", len(rows), INFO),
            ("With Salary Data", with_sal, OK),
            ("Total (Mixed Currencies)", f"{total:,.0f}", GOLD_D),
        ])
        for row in self._pay_tree.get_children(): self._pay_tree.delete(row)
        for eid, e in rows:
            self._pay_tree.insert("", "end", iid=eid, values=(
                eid, e.get("full_name",""), e.get("department",""), e.get("occupation",""),
                f"{float(e['salary']):,.0f}" if e.get("salary") else "—",
                e.get("salary_currency","—"),
                ET_LABELS.get(e.get("employment_type",""),e.get("employment_type",""))))

    def _on_pay_dbl(self, event):
        sel = self._pay_tree.selection()
        if sel: self._pay_dialog(sel[0])

    def _pay_dialog(self, eid: str = None):
        if not eid:
            sel = self._pay_tree.selection()
            if not sel: messagebox.showwarning("No selection","Select an employee."); return
            eid = sel[0]
        e = self.data["employees"].get(eid, {})
        dlg = ctk.CTkToplevel(self); dlg.title(f"Edit Salary — {eid}")
        dlg.geometry("360x220"); dlg.grab_set()
        sal_v = tk.StringVar(value=str(e.get("salary","") or ""))
        cur_v = tk.StringVar(value=e.get("salary_currency","USD"))
        ctk.CTkLabel(dlg, text="Salary Amount", font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=22, pady=(18,1))
        ctk.CTkEntry(dlg, textvariable=sal_v, height=36, font=self.F_MONO).pack(fill="x", padx=22)
        ctk.CTkLabel(dlg, text="Currency", font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=22, pady=(10,1))
        ctk.CTkOptionMenu(dlg, variable=cur_v, values=["USD","EUR","GBP","NGN","KES","ZAR","GHS"],
                          font=self.F_BODY).pack(fill="x", padx=22)
        def _save():
            self._reload()
            self.data["employees"][eid]["salary"] = sal_v.get().strip()
            self.data["employees"][eid]["salary_currency"] = cur_v.get()
            audit(self.data, self.user["username"], "Updated salary", eid)
            save_data(self.data); dlg.destroy(); self._refresh_payroll()
        ctk.CTkButton(dlg, text="💾 Save", fg_color=GOLD, text_color=BG,
                      hover_color=GOLD_L, height=38, command=_save).pack(pady=14, fill="x", padx=22)

    def _export_pay_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path: return
        emps = {k: v for k,v in self.data["employees"].items() if v.get("salary")}
        with open(path,"wb") as f: f.write(export_csv_bytes(emps))
        messagebox.showinfo("Exported", f"Saved → {path}")

    def _export_pay_xl(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not path: return
        emps = {k: v for k,v in self.data["employees"].items() if v.get("salary")}
        b = export_excel_bytes(emps)
        if not b: messagebox.showerror("Error","Install openpyxl first."); return
        with open(path,"wb") as f: f.write(b)
        messagebox.showinfo("Exported", f"Saved → {path}")

    # ── AUDIT ─────────────────────────────────────────────────────────────────
    def _build_tab_audit(self):
        f = self._tab("Audit Log")
        self._title(f, "Audit Log")
        tb = ctk.CTkFrame(f, fg_color="transparent"); tb.pack(fill="x", pady=(0,10))
        self._audit_search = tk.StringVar()
        self._audit_search.trace_add("write", lambda *_: self._refresh_audit())
        ctk.CTkEntry(tb, textvariable=self._audit_search, width=320, height=36,
                     placeholder_text="🔍  Search actions, users…", font=self.F_BODY).pack(side="left")
        cols = ("Timestamp","User","Action","Target","Detail")
        widths = {"Timestamp":150,"User":120,"Action":160,"Target":140,"Detail":260}
        self._audit_tree = self._tree(f, cols, widths)

    def _refresh_audit(self):
        self._reload()
        q = self._audit_search.get().lower()
        for row in self._audit_tree.get_children(): self._audit_tree.delete(row)
        for a in self.data.get("audit_log",[]):
            if q and not any(q in str(v).lower() for v in a.values()): continue
            self._audit_tree.insert("", "end", values=(
                a.get("ts",""), a.get("user",""), a.get("action",""),
                a.get("target",""), a.get("detail","")))

    # ── SYSTEM USERS ──────────────────────────────────────────────────────────
    def _build_tab_sysusers(self):
        f = self._tab("System Users")
        self._title(f, "System Users")
        tb = ctk.CTkFrame(f, fg_color="transparent"); tb.pack(fill="x", pady=(0,10))
        ctk.CTkButton(tb, text="+ Add System User", fg_color=GOLD, text_color=BG,
                      hover_color=GOLD_L, height=36, width=160, font=self.F_SMALL,
                      command=lambda: self._su_dialog()).pack(side="right")
        cols = ("Username","Full Name","Role","Employee ID","Created")
        widths = {"Username":130,"Full Name":170,"Role":100,"Employee ID":130,"Created":100}
        self._su_tree = self._tree(f, cols, widths)
        act = ctk.CTkFrame(f, fg_color="transparent"); act.pack(fill="x", pady=8)
        ctk.CTkButton(act, text="✏️ Edit Selected", fg_color=INFO, width=130, height=36,
                      command=self._edit_su).pack(side="left", padx=4)
        ctk.CTkButton(act, text="🗑 Delete", fg_color=ERR, width=100, height=36,
                      command=self._del_su).pack(side="left", padx=4)

    def _refresh_sysusers(self):
        self._reload()
        for row in self._su_tree.get_children(): self._su_tree.delete(row)
        for uname, d in self.data["system_users"].items():
            self._su_tree.insert("", "end", iid=uname, values=(
                uname, d.get("full_name",""), d.get("role",""),
                d.get("emp_id","—"), d.get("created","")))

    def _su_dialog(self, uname: str = None):
        d = self.data["system_users"].get(uname, {}) if uname else {}
        dlg = ctk.CTkToplevel(self); dlg.title("Edit System User" if uname else "Add System User")
        dlg.geometry("440x380"); dlg.grab_set()
        un_v  = tk.StringVar(value=uname or "")
        fn_v  = tk.StringVar(value=d.get("full_name",""))
        rl_v  = tk.StringVar(value=d.get("role","staff"))
        eid_v = tk.StringVar(value=d.get("emp_id","") or "")
        pw_v  = tk.StringVar()
        for label, var, opts in [
            ("Username *", un_v, None), ("Full Name", fn_v, None),
            ("Role", rl_v, ["staff","manager","hr","admin"]),
            ("Employee ID (optional)", eid_v, None),
            ("Password (blank = keep existing)", pw_v, None),
        ]:
            ctk.CTkLabel(dlg, text=label, font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=22, pady=(8,1))
            if opts:
                ctk.CTkOptionMenu(dlg, variable=var, values=opts, font=self.F_BODY).pack(fill="x", padx=22)
            else:
                ctk.CTkEntry(dlg, textvariable=var, height=32, font=self.F_BODY,
                             show="•" if label.startswith("Password") else None).pack(fill="x", padx=22)

        def _save():
            new_un = un_v.get().strip(); fn = fn_v.get().strip()
            role   = rl_v.get(); eid_ = eid_v.get().strip() or None
            pw = pw_v.get()
            if not new_un: messagebox.showerror("Error","Username required."); return
            self._reload()
            if not uname and new_un in self.data["system_users"]:
                messagebox.showerror("Error","Username already exists."); return
            if not uname and len(pw) < 6:
                messagebox.showerror("Error","Password must be at least 6 characters."); return
            entry = self.data["system_users"].get(uname or new_un, {
                "password_hash": hash_pw(pw), "photo": None,
                "created": datetime.now().strftime("%Y-%m-%d")})
            entry["full_name"] = fn; entry["role"] = role; entry["emp_id"] = eid_
            if pw and len(pw) >= 6: entry["password_hash"] = hash_pw(pw)
            if uname and uname != new_un:
                del self.data["system_users"][uname]
            self.data["system_users"][new_un] = entry
            audit(self.data, self.user["username"], "Saved system user", new_un)
            save_data(self.data); dlg.destroy(); self._refresh_sysusers()
            messagebox.showinfo("Saved","System user saved.")

        ctk.CTkButton(dlg, text="💾 Save", fg_color=GOLD, text_color=BG,
                      hover_color=GOLD_L, height=38, command=_save).pack(pady=12, fill="x", padx=22)

    def _edit_su(self):
        sel = self._su_tree.selection()
        if not sel: messagebox.showwarning("No selection","Select a user."); return
        self._su_dialog(sel[0])

    def _del_su(self):
        sel = self._su_tree.selection()
        if not sel: messagebox.showwarning("No selection","Select a user."); return
        uname = sel[0]
        if uname == self.user["username"]:
            messagebox.showerror("Error","Cannot delete yourself."); return
        if not messagebox.askyesno("Confirm",f"Delete system user '{uname}'?"): return
        self._reload()
        del self.data["system_users"][uname]
        audit(self.data, self.user["username"], "Deleted system user", uname)
        save_data(self.data); self._refresh_sysusers()

    # ── PROFILE ───────────────────────────────────────────────────────────────
    def _build_tab_profile(self):
        f = self._tab("Profile")
        self._title(f, "My Profile")
        card = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
        card.pack(fill="x", pady=(0,14))
        ctk.CTkLabel(card, text=self.user.get("full_name","—"),
                     font=ctk.CTkFont("Courier New", 20, "bold"), text_color=GOLD).pack(pady=(18,2))
        ctk.CTkLabel(card, text=ROLE_LABEL.get(self.user.get("role",""),"Staff"),
                     font=self.F_SMALL, text_color=TXM).pack()
        ctk.CTkLabel(card, text=f"Username: {self.user.get('username','')}   ·   Emp ID: {self.user.get('emp_id','Not linked')}",
                     font=self.F_MONO, text_color=TXM).pack(pady=(6,18))

        pw_card = ctk.CTkFrame(f, fg_color=CARD, corner_radius=10)
        pw_card.pack(fill="x")
        ctk.CTkLabel(pw_card, text="Change Password", font=self.F_HEAD, text_color=TX).pack(anchor="w", padx=18, pady=(14,8))
        self._pw_cur  = tk.StringVar()
        self._pw_new  = tk.StringVar()
        self._pw_conf = tk.StringVar()
        for label, var in [("Current Password","_pw_cur"),("New Password","_pw_new"),("Confirm New","_pw_conf")]:
            ctk.CTkLabel(pw_card, text=label, font=self.F_SMALL, text_color=TXM).pack(anchor="w", padx=18, pady=(4,1))
            ctk.CTkEntry(pw_card, textvariable=getattr(self, var), height=34, show="•",
                         font=self.F_BODY).pack(fill="x", padx=18, pady=(0,3))
        ctk.CTkButton(pw_card, text="Update Password", fg_color=GOLD, text_color=BG,
                      hover_color=GOLD_L, height=38, command=self._change_pw
                      ).pack(pady=16, fill="x", padx=18)

    def _change_pw(self):
        c = self._pw_cur.get(); n = self._pw_new.get(); cf = self._pw_conf.get()
        if not c or not n: messagebox.showerror("Error","Fill all fields."); return
        if n != cf: messagebox.showerror("Error","Passwords do not match."); return
        if len(n) < 6: messagebox.showerror("Error","Password too short (min 6)."); return
        self._reload()
        u = self.data["system_users"].get(self.user["username"], {})
        if not verify_pw(c, u.get("password_hash","")): messagebox.showerror("Error","Current password incorrect."); return
        u["password_hash"] = hash_pw(n)
        audit(self.data, self.user["username"], "Changed password", self.user["username"])
        save_data(self.data)
        self._pw_cur.set(""); self._pw_new.set(""); self._pw_conf.set("")
        messagebox.showinfo("Updated","Password updated successfully.")

    def _logout(self):
        if messagebox.askyesno("Sign Out","Sign out of ARCHER ENTERPRISE?"):
            self.destroy()


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    login = LoginWindow()
    login.mainloop()
    if login.logged_in_user:
        app = ArcherApp(login.logged_in_user)
        app.mainloop()
