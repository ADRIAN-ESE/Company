"""
ARCHER ENTERPRISE — Web Edition v2.0
Flask single-file application

pip install flask openpyxl
python archer_web.py  →  http://localhost:5000

Default credentials:
  admin / admin123  |  hr_manager / hr123  |  manager1 / mgr123  |  staff1 / staff123
"""
import csv
import io, json, secrets
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, render_template_string, request, send_file, session

from archer_shared import (load_data, save_data, gen_emp_id, audit, notify,
                            hash_pw, verify_pw, export_csv_bytes, export_excel_bytes,
                            ROLE_LEVEL, ROLE_LABEL, EMP_FIELDS)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ─── guards ───────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def d(*a, **kw):
        if "username" not in session:
            return jsonify({"error": "Not authenticated"}), 401
        return f(*a, **kw)
    return d

def role_required(min_role):
    def dec(f):
        @wraps(f)
        def d(*a, **kw):
            if "username" not in session:
                return jsonify({"error": "Not authenticated"}), 401
            if ROLE_LEVEL.get(session.get("role","staff"),0) < ROLE_LEVEL.get(min_role,0):
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*a, **kw)
        return d
    return dec

# ─── HTML ─────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ARCHER ENTERPRISE</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:#07091a;--sur:#0c0f22;--card:#111428;--card2:#161a30;--bdr:#1e2240;--gold:#c9a84c;--gl:#e8c56a;--gd:#9a7a30;--gg:rgba(201,168,76,.14);--ok:#3dba7a;--warn:#e09a30;--err:#e05252;--info:#4f8ef7;--tx:#d4d8f0;--txm:#5a6080;--txd:#2a3050;--bb:'Bebas Neue',sans-serif;--dm:'DM Sans',sans-serif;--mo:'DM Mono',monospace;--r:10px;--sw:238px;--hh:60px}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--tx);font-family:var(--dm);font-size:14px}
::-webkit-scrollbar{width:5px;height:5px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px}

/* ── LOGIN ── */
#ls{position:fixed;inset:0;z-index:1000;background:var(--bg);display:flex;align-items:center;justify-content:center;overflow:hidden}
#ls.gone{display:none!important}
.lgrid{position:absolute;inset:0;background-image:linear-gradient(rgba(201,168,76,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(201,168,76,.035) 1px,transparent 1px);background-size:55px 55px;animation:gs 25s linear infinite}
@keyframes gs{100%{background-position:55px 55px}}
.lvig{position:absolute;inset:0;background:radial-gradient(ellipse at center,transparent 25%,var(--bg) 78%)}
#spl{position:absolute;display:flex;flex-direction:column;align-items:center;z-index:2;transition:opacity .7s,transform .7s;gap:0}
#spl.hidden{opacity:0;transform:translateY(-28px);pointer-events:none}
.sa{font-family:var(--bb);font-size:clamp(72px,12vw,160px);letter-spacing:.14em;color:var(--gold);text-shadow:0 0 50px rgba(201,168,76,.45),0 0 100px rgba(201,168,76,.18);line-height:1;opacity:0;animation:ain 1.1s ease .2s forwards}
@keyframes ain{from{opacity:0;letter-spacing:.42em}to{opacity:1;letter-spacing:.14em}}
.se{font-family:var(--bb);font-size:clamp(15px,2.2vw,30px);letter-spacing:.52em;color:var(--txm);margin-top:-4px;opacity:0;animation:fup .8s ease 1.1s forwards}
.sdiv{width:110px;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:12px auto;opacity:0;animation:fup .8s ease 1.4s forwards}
.stag{font-size:clamp(8px,1vw,11px);letter-spacing:.18em;color:var(--gd);text-transform:uppercase;opacity:0;animation:fup .8s ease 1.7s forwards}
@keyframes fup{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
#lfw{position:absolute;z-index:3;width:100%;display:flex;justify-content:center;opacity:0;transform:translateY(70px);transition:opacity .7s,transform .7s;pointer-events:none}
#lfw.vis{opacity:1;transform:translateY(0);pointer-events:all}
.lcard{background:rgba(13,15,34,.94);border:1px solid var(--bdr);border-top:2px solid var(--gold);border-radius:16px;padding:40px 46px;width:390px;backdrop-filter:blur(18px);box-shadow:0 40px 80px rgba(0,0,0,.65),0 0 35px rgba(201,168,76,.07)}
.lclg{font-family:var(--bb);font-size:28px;letter-spacing:.14em;color:var(--gold);text-align:center;margin-bottom:3px}
.lcs{font-size:11px;letter-spacing:.13em;color:var(--txm);text-transform:uppercase;text-align:center;margin-bottom:22px}
.ldiv{width:52px;height:2px;background:var(--gold);margin:0 auto 20px}
.ll{font-size:10px;font-weight:700;letter-spacing:.11em;text-transform:uppercase;color:var(--txm);margin-bottom:5px;display:block}
.li{width:100%;background:rgba(7,9,26,.85);border:1px solid var(--bdr);color:var(--tx);padding:11px 14px;border-radius:8px;font-family:var(--dm);font-size:14px;outline:none;margin-bottom:14px;transition:border-color .18s}
.li:focus{border-color:var(--gold)}
.lbtn{width:100%;background:var(--gold);color:var(--bg);border:none;padding:13px;border-radius:8px;font-family:var(--bb);font-size:17px;letter-spacing:.14em;cursor:pointer;transition:all .2s;margin-top:4px}
.lbtn:hover{background:var(--gl);box-shadow:0 0 18px rgba(201,168,76,.28)}
.lerr{color:var(--err);font-size:12px;text-align:center;margin-top:8px;min-height:16px}

/* ── APP LAYOUT ── */
#app{display:none;height:100vh;flex-direction:column;overflow:hidden}
#app.vis{display:flex}
#hdr{height:var(--hh);background:var(--sur);border-bottom:1px solid var(--bdr);display:flex;align-items:center;padding:0 24px;flex-shrink:0;gap:14px;z-index:50}
.hlog{font-family:var(--bb);font-size:19px;letter-spacing:.1em;color:var(--gold);flex-shrink:0}
.hbc{font-size:12px;color:var(--txm);flex:1}.hbc span{color:var(--tx);font-weight:500}
.hr2{display:flex;align-items:center;gap:10px}
.nbtn{position:relative;background:transparent;border:1px solid var(--bdr);color:var(--txm);width:34px;height:34px;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:14px;transition:all .18s}
.nbtn:hover{border-color:var(--gold);color:var(--gold)}
.nbdg{position:absolute;top:-5px;right:-5px;background:var(--err);color:#fff;font-size:9px;font-weight:700;width:16px;height:16px;border-radius:50%;display:none;align-items:center;justify-content:center}
.nbdg.v{display:flex}
.upill{display:flex;align-items:center;gap:7px;background:var(--card);border:1px solid var(--bdr);border-radius:8px;padding:4px 12px;cursor:pointer;transition:border-color .18s}
.upill:hover{border-color:var(--gold)}
.uname{font-size:13px;font-weight:500}
.urole{font-size:10px;font-weight:700;letter-spacing:.07em;color:var(--gold);background:var(--gg);padding:1px 8px;border-radius:20px;text-transform:uppercase}
.lout{background:transparent;border:1px solid var(--bdr);color:var(--txm);padding:5px 12px;border-radius:8px;font-family:var(--dm);font-size:12px;cursor:pointer;transition:all .18s}
.lout:hover{border-color:var(--err);color:var(--err)}
#body{display:flex;flex:1;overflow:hidden}

/* ── SIDEBAR ── */
#sb{width:var(--sw);flex-shrink:0;background:var(--sur);border-right:1px solid var(--bdr);display:flex;flex-direction:column;overflow-y:auto}
.ssl{font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--txd);padding:16px 20px 5px}
.nb{display:flex;align-items:center;gap:9px;padding:9px 20px;background:transparent;border:none;color:var(--txm);font-family:var(--dm);font-size:13px;width:100%;text-align:left;cursor:pointer;transition:all .14s;border-left:3px solid transparent}
.nb:hover{background:rgba(201,168,76,.04);color:var(--tx)}
.nb.act{background:rgba(201,168,76,.08);color:var(--gold);border-left-color:var(--gold)}
.ni{font-size:14px;width:18px;text-align:center;flex-shrink:0}
.nbdge{margin-left:auto;background:var(--err);color:#fff;font-size:9px;font-weight:700;padding:1px 6px;border-radius:10px;display:none}
.nbdge.v{display:inline}

/* role-based show/hide */
.ao,.ho,.mo{display:none!important}
body.ra .ao,body.ra .ho,body.ra .mo{display:flex!important}
body.rh .ho,body.rh .mo{display:flex!important}
body.rm .mo{display:flex!important}
nav .ao,nav .ho,nav .mo{display:none!important}
body.ra nav .ao,body.ra nav .ho,body.ra nav .mo{display:flex!important}
body.rh nav .ho,body.rh nav .mo{display:flex!important}
body.rm nav .mo{display:flex!important}

/* ── MAIN ── */
#main{flex:1;overflow-y:auto;padding:26px 30px}
.pg{display:none}.pg.act{display:block}
.pghdr{margin-bottom:20px}
.pgt{font-family:var(--bb);font-size:34px;letter-spacing:.04em;color:#fff;line-height:1}
.pgs{font-size:12px;color:var(--txm);margin-top:3px}

/* ── CARDS ── */
.card{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:20px;margin-bottom:16px}
.ct{font-family:var(--bb);font-size:16px;letter-spacing:.04em;color:#fff;margin-bottom:12px}

/* ── STATS ── */
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:11px;margin-bottom:20px}
.sc{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:16px;position:relative;overflow:hidden}
.sc::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--gold)}
.sc.bl::before{background:var(--info)}.sc.gn::before{background:var(--ok)}.sc.rd::before{background:var(--err)}.sc.wn::before{background:var(--warn)}
.si{font-size:18px;margin-bottom:6px}
.sv{font-family:var(--bb);font-size:38px;color:#fff;line-height:1}
.slb{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--txm);margin-top:3px}

/* ── CHARTS ── */
.cr{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.cc{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:16px}
.cc canvas{max-height:190px}

/* ── TOOLBAR ── */
.tb{display:flex;align-items:center;gap:7px;margin-bottom:10px;flex-wrap:wrap}
.si2{flex:1;min-width:170px;max-width:340px;background:var(--card);border:1px solid var(--bdr);color:var(--tx);padding:7px 11px;border-radius:7px;font-family:var(--dm);font-size:13px;outline:none;transition:border-color .15s}
.si2:focus{border-color:var(--gold)}.si2::placeholder{color:var(--txd)}
.flt{background:var(--card);border:1px solid var(--bdr);color:var(--tx);padding:7px 10px;border-radius:7px;font-family:var(--dm);font-size:13px;outline:none;cursor:pointer}
.flt option{background:var(--card)}
.sp{flex:1}

/* ── BUTTONS ── */
.btn{display:inline-flex;align-items:center;gap:5px;padding:7px 14px;border-radius:7px;border:none;font-family:var(--dm);font-size:13px;font-weight:600;cursor:pointer;transition:all .14s;white-space:nowrap}
.bg{background:var(--gold);color:var(--bg)}.bg:hover{background:var(--gl);box-shadow:0 0 12px rgba(201,168,76,.28)}
.bk{background:var(--ok);color:#fff}.bk:hover{background:#2ea66b}
.br{background:var(--err);color:#fff}.br:hover{background:#c94040}
.bh{background:transparent;border:1px solid var(--bdr);color:var(--txm)}.bh:hover{border-color:var(--gold);color:var(--gold)}
.sm{padding:5px 10px;font-size:12px}

/* ── TABLE ── */
.tw{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);overflow:auto}
table{width:100%;border-collapse:collapse}
thead th{background:var(--sur);color:var(--txm);font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;padding:10px 12px;text-align:left;white-space:nowrap;border-bottom:1px solid var(--bdr);position:sticky;top:0;z-index:1}
tbody tr{border-bottom:1px solid rgba(30,34,64,.45);transition:background .1s;cursor:pointer}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:rgba(201,168,76,.04)}
tbody tr.sel{background:rgba(201,168,76,.1)!important}
td{padding:10px 12px;font-size:13px;white-space:nowrap}
.er td{text-align:center;padding:36px;color:var(--txm);font-size:12px}

/* ── BADGES ── */
.bdg{display:inline-block;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;letter-spacing:.03em;text-transform:uppercase}
.bgold{background:var(--gg);color:var(--gold);border:1px solid rgba(201,168,76,.2)}
.bgreen{background:rgba(61,186,122,.12);color:var(--ok)}
.bred{background:rgba(224,82,82,.12);color:var(--err)}
.bwarn{background:rgba(224,154,48,.12);color:var(--warn)}
.bblue{background:rgba(79,142,247,.12);color:var(--info)}
.bgray{background:rgba(90,96,128,.1);color:var(--txm)}

/* ── FORM ── */
.fg{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.fgr{display:flex;flex-direction:column;gap:4px}
.fgr.full{grid-column:1/-1}
.flb{font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--txm)}
.fi,.fsel,.fta{background:var(--bg);border:1px solid var(--bdr);color:var(--tx);padding:8px 11px;border-radius:7px;font-family:var(--dm);font-size:13px;outline:none;transition:border-color .15s;width:100%}
.fi:focus,.fsel:focus,.fta:focus{border-color:var(--gold)}
.fi::placeholder{color:var(--txd)}
.fta{resize:vertical;min-height:64px}
.fsel option{background:var(--card)}

/* ── MODALS ── */
.mo2{position:fixed;inset:0;background:rgba(0,0,0,.78);display:flex;align-items:center;justify-content:center;z-index:200;backdrop-filter:blur(6px);opacity:0;pointer-events:none;transition:opacity .2s}
.mo2.open{opacity:1;pointer-events:all}
.mdl{background:var(--card);border:1px solid var(--bdr);border-top:2px solid var(--gold);border-radius:14px;padding:28px;width:620px;max-width:96vw;max-height:90vh;overflow-y:auto;transform:translateY(16px);transition:transform .2s}
.mo2.open .mdl{transform:translateY(0)}
.mdlt{font-family:var(--bb);font-size:21px;letter-spacing:.04em;color:#fff;margin-bottom:20px}
.mact{display:flex;gap:9px;justify-content:flex-end;margin-top:18px}

/* ── NOTIF PANEL ── */
#np{position:fixed;top:var(--hh);right:0;width:330px;height:calc(100vh - var(--hh));background:var(--sur);border-left:1px solid var(--bdr);z-index:100;transform:translateX(100%);transition:transform .28s;display:flex;flex-direction:column}
#np.open{transform:translateX(0)}
.nph{padding:16px 20px;border-bottom:1px solid var(--bdr);display:flex;align-items:center;justify-content:space-between}
.npht{font-family:var(--bb);font-size:17px;letter-spacing:.04em;color:#fff}
.npb{flex:1;overflow-y:auto}
.nit{padding:12px 20px;border-bottom:1px solid rgba(30,34,64,.4);cursor:pointer;transition:background .1s;border-left:3px solid transparent}
.nit.unr{border-left-color:var(--gold)}
.nit:hover{background:rgba(201,168,76,.04)}
.nim{font-size:13px;color:var(--tx);line-height:1.4}
.nts{font-size:11px;color:var(--txm);margin-top:3px;font-family:var(--mo)}
.nem{text-align:center;padding:36px;color:var(--txm);font-size:13px}

/* ── DEPT GRID ── */
.dg{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}
.dc{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:16px;transition:all .18s;position:relative;overflow:hidden}
.dc:hover{border-color:var(--gold);background:var(--card2)}
.dcn{font-family:var(--bb);font-size:18px;letter-spacing:.04em;color:#fff;margin-bottom:4px}
.dcd{font-size:12px;color:var(--txm);line-height:1.4}
.dcc{position:absolute;top:12px;right:14px;font-family:var(--bb);font-size:24px;color:var(--gold);opacity:.7}
.dch{font-size:11px;color:var(--gd);margin-top:7px}
.dca{display:flex;gap:7px;margin-top:10px}

/* ── AUDIT ── */
.ae{display:flex;gap:12px;padding:9px 0;border-bottom:1px solid rgba(30,34,64,.35)}
.adot{width:7px;height:7px;border-radius:50%;background:var(--gold);flex-shrink:0;margin-top:5px}
.ats{font-family:var(--mo);font-size:10px;color:var(--txm);margin-top:2px}

/* ── PHOTO ── */
.ep{width:36px;height:36px;border-radius:50%;object-fit:cover;border:2px solid var(--bdr)}
.epp{width:36px;height:36px;border-radius:50%;background:var(--card2);border:2px solid var(--bdr);display:flex;align-items:center;justify-content:center;font-size:14px}
.pavw{position:relative;display:inline-block;cursor:pointer}
.pav2{width:84px;height:84px;border-radius:50%;object-fit:cover;border:3px solid var(--gold)}
.pavb{position:absolute;bottom:0;right:0;background:var(--gold);color:var(--bg);width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px}

/* ── TOAST ── */
#toast{position:fixed;bottom:24px;right:24px;z-index:500;background:var(--card);border:1px solid var(--bdr);border-left:4px solid var(--gold);padding:12px 16px;border-radius:8px;font-size:13px;transform:translateY(80px);opacity:0;transition:all .28s;max-width:290px;pointer-events:none}
#toast.show{transform:translateY(0);opacity:1}
#toast.success{border-left-color:var(--ok)}
#toast.error{border-left-color:var(--err)}
#toast.warn{border-left-color:var(--warn)}

.irow{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid rgba(30,34,64,.5)}
.irow:last-child{border-bottom:none}.ik{font-size:11px;color:var(--txm)}.iv{font-size:13px}
.saldsp{font-family:var(--mo);font-size:20px;color:var(--gold)}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="ls">
  <canvas id="lc"></canvas>
  <div class="lgrid"></div><div class="lvig"></div>
  <div id="spl">
    <div class="sa">ARCHER</div>
    <div class="se">ENTERPRISE</div>
    <div class="sdiv"></div>
    <div class="stag">Your Corporate Management &amp; Service Agency</div>
  </div>
  <div id="lfw">
    <div class="lcard">
      <div class="lclg">ARCHER</div>
      <div class="lcs">Enterprise Portal</div>
      <div class="ldiv"></div>
      <label class="ll">Username</label>
      <input id="lu" class="li" type="text" placeholder="Enter username" autocomplete="username">
      <label class="ll">Password</label>
      <input id="lp" class="li" type="password" placeholder="••••••••" autocomplete="current-password">
      <button class="lbtn" onclick="doLogin()">SIGN IN</button>
      <div class="lerr" id="lerr"></div>
    </div>
  </div>
</div>

<!-- APP -->
<div id="app">
  <header id="hdr">
    <div class="hlog">ARCHER</div>
    <div class="hbc">ENTERPRISE &nbsp;›&nbsp; <span id="bcp">Dashboard</span></div>
    <div class="hr2">
      <button class="nbtn" onclick="toggleNP()" title="Notifications">🔔<span class="nbdg" id="nbdg">0</span></button>
      <div class="upill" onclick="nav('profile')">
        <div id="hav" style="font-size:18px">👤</div>
        <div class="uname" id="hname">—</div>
        <span class="urole" id="hrole">—</span>
      </div>
      <button class="lout" onclick="doLogout()">Sign Out</button>
    </div>
  </header>
  <div id="body">
    <nav id="sb">
      <div class="ssl">Main</div>
      <button class="nb" data-p="dashboard"><span class="ni">📊</span>Dashboard</button>
      <button class="nb" data-p="employees"><span class="ni">👥</span>Employees<span class="nbdge" id="bdg-e"></span></button>
      <button class="nb" data-p="departments"><span class="ni">🏢</span>Departments</button>
      <div class="ssl">HR Operations</div>
      <button class="nb" data-p="promotions"><span class="ni">🏆</span>Promotions<span class="nbdge" id="bdg-p"></span></button>
      <button class="nb" data-p="leave"><span class="ni">📅</span>Leave Mgmt<span class="nbdge" id="bdg-l"></span></button>
      <button class="nb" data-p="payroll" style="display:none" id="sb-payroll"><span class="ni">💰</span>Payroll</button>
      <button class="nb" data-p="audit" style="display:none" id="sb-audit"><span class="ni">📋</span>Audit Log</button>
      <div class="ssl">System</div>
      <button class="nb" data-p="sysusers" style="display:none" id="sb-su"><span class="ni">🔐</span>System Users</button>
      <button class="nb" data-p="reports" style="display:none" id="sb-reports"><span class="ni">📈</span>Reports</button>
      <button class="nb" data-p="feedback" style="display:none" id="sb-feedback"><span class="ni">💬</span>Feedback<span class="nbdge" id="bdg-fb"></span></button>
      <button class="nb" data-p="profile"><span class="ni">⚙️</span>My Profile</button>
    </nav>
    <main id="main">

      <!-- DASHBOARD -->
      <section class="pg" id="pg-dashboard">
        <div class="pghdr"><div class="pgt">Dashboard</div><div class="pgs">ARCHER ENTERPRISE — Corporate Overview</div></div>
        <div class="sg" id="dstats"></div>
        <div class="cr">
          <div class="cc"><div class="ct">By Department</div><canvas id="ch-dept"></canvas></div>
          <div class="cc"><div class="ct">Employment Types</div><canvas id="ch-type"></canvas></div>
        </div>
        <div class="card"><div class="ct">Recent Audit Activity</div><div id="daud" style="padding:4px 0"></div></div>
      </section>

      <!-- EMPLOYEES -->
      <section class="pg" id="pg-employees">
        <div class="pghdr"><div class="pgt">Employees</div><div class="pgs">Workforce management</div></div>
        <div class="tb">
          <input class="si2" id="esrch" type="text" placeholder="🔍  Name, ID, department…" oninput="rEmp()">
          <select class="flt" id="efd" onchange="rEmp()"><option value="">All Departments</option></select>
          <select class="flt" id="efs" onchange="rEmp()"><option value="">All Status</option><option value="active">Active</option><option value="inactive">Inactive</option><option value="on_leave">On Leave</option></select>
          <div class="sp"></div>
          <button class="btn bh sm" onclick="openModal('m-imp')">📥 Import</button>
          <button class="btn bh sm" onclick="expMenu()">📤 Export ▾</button>
          <button class="btn bg" id="add-emp-btn" onclick="oAddEmp()" style="display:none">+ Add Employee</button>
        </div>
        <div class="tw"><table><thead><tr><th>Photo</th><th>ID</th><th>Name</th><th>Department</th><th>Occupation</th><th>Type</th><th>Status</th><th>Added</th><th></th></tr></thead><tbody id="etb"></tbody></table></div>
      </section>

      <!-- DEPARTMENTS -->
      <section class="pg" id="pg-departments">
        <div class="pghdr"><div class="pgt">Departments</div><div class="pgs">Organisational structure</div></div>
        <div class="tb"><div class="sp"></div><button class="btn bg" id="add-dept-btn" onclick="oAddDept()" style="display:none">+ Add Department</button></div>
        <div class="dg" id="deptg"></div>
      </section>

      <!-- PROMOTIONS -->
      <section class="pg" id="pg-promotions">
        <div class="pghdr"><div class="pgt">Promotions</div><div class="pgs">Career advancement workflow</div></div>
        <div class="card" id="prq-card" style="display:none">
          <div class="ct">Submit New Request</div>
          <div class="fg">
            <div class="fgr"><label class="flb">Employee ID</label><input class="fi" id="p-eid" placeholder="ARCH-2026-0001"></div>
            <div class="fgr"><label class="flb">Requested Role / Level</label><input class="fi" id="p-role" placeholder="e.g. Senior Engineer"></div>
          </div>
          <div style="margin-top:12px"><button class="btn bg" onclick="subPromo()">Submit Request</button></div>
        </div>
        <div class="tb">
          <select class="flt" id="pfl" onchange="rPromo()"><option value="">All Statuses</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="denied">Denied</option></select>
          <div class="sp"></div>
          <button class="btn bk sm" id="promo-apr" onclick="resPromo('approved')" style="display:none">✅ Approve</button>
          <button class="btn br sm" id="promo-dny" onclick="resPromo('denied')" style="display:none">❌ Deny</button>
        </div>
        <div class="tw"><table><thead><tr><th>Employee</th><th>Name</th><th>Current Role</th><th>Requested Role</th><th>Date</th><th>Status</th></tr></thead><tbody id="ptb"></tbody></table></div>
      </section>

      <!-- LEAVE -->
      <section class="pg" id="pg-leave">
        <div class="pghdr"><div class="pgt">Leave Management</div><div class="pgs">Absence tracking and approval</div></div>
        <div class="card">
          <div class="ct">Submit Leave Request</div>
          <div class="fg">
            <div class="fgr" id="lv-eid-row" style="display:none"><label class="flb">Employee ID (blank = self)</label><input class="fi" id="lv-eid" placeholder="ARCH-2026-0001"></div>
            <div class="fgr"><label class="flb">Leave Type</label>
              <select class="fsel" id="lv-type"><option value="annual">Annual Leave</option><option value="sick">Sick Leave</option><option value="maternity">Maternity / Paternity</option><option value="unpaid">Unpaid Leave</option><option value="other">Other</option></select></div>
            <div class="fgr"><label class="flb">Start Date</label><input class="fi" id="lv-s" type="date"></div>
            <div class="fgr"><label class="flb">End Date</label><input class="fi" id="lv-e" type="date"></div>
            <div class="fgr full"><label class="flb">Notes</label><textarea class="fta" id="lv-r" placeholder="Optional…" style="min-height:52px"></textarea></div>
          </div>
          <div style="margin-top:12px"><button class="btn bg" onclick="subLeave()">Submit Request</button></div>
        </div>
        <div class="tb">
          <select class="flt" id="lfl" onchange="rLeave()"><option value="">All</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="denied">Denied</option></select>
          <div class="sp"></div>
          <button class="btn bk sm" id="lv-apr" onclick="resLeave('approved')" style="display:none">✅ Approve</button>
          <button class="btn br sm" id="lv-dny" onclick="resLeave('denied')" style="display:none">❌ Deny</button>
        </div>
        <div class="tw"><table><thead><tr><th>Employee</th><th>Name</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Status</th></tr></thead><tbody id="ltb"></tbody></table></div>
      </section>

      <!-- PAYROLL -->
      <section class="pg" id="pg-payroll">
        <div class="pghdr"><div class="pgt">Payroll &amp; Salary</div><div class="pgs">Compensation — HR &amp; Admin only</div></div>
        <div class="sg" id="prstats"></div>
        <div class="tb">
          <input class="si2" id="prsrch" type="text" placeholder="🔍  Search…" oninput="rPay()">
          <div class="sp"></div>
          <button class="btn bh sm" onclick="window.location.href='/api/export/payroll-csv'">📤 CSV</button>
          <button class="btn bh sm" onclick="window.location.href='/api/export/payroll-excel'">📤 Excel</button>
        </div>
        <div class="tw"><table><thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Occupation</th><th>Salary</th><th>Currency</th><th>Type</th><th></th></tr></thead><tbody id="prtb"></tbody></table></div>
      </section>

      <!-- AUDIT -->
      <section class="pg" id="pg-audit">
        <div class="pghdr"><div class="pgt">Audit Log</div><div class="pgs">Full activity trail</div></div>
        <div class="tb"><input class="si2" id="asrch" type="text" placeholder="🔍  Search…" oninput="rAudit()"><div class="sp"></div></div>
        <div class="card" style="padding:0 20px;max-height:600px;overflow-y:auto"><div id="audl"></div></div>
      </section>

      <!-- SYSTEM USERS -->
      <section class="pg" id="pg-sysusers">
        <div class="pghdr"><div class="pgt">System Users</div><div class="pgs">Portal access — Admin only</div></div>
        <div class="tb"><div class="sp"></div><button class="btn bg" onclick="oAddSU()">+ Add System User</button></div>
        <div class="tw"><table><thead><tr><th>Username</th><th>Full Name</th><th>Role</th><th>Employee ID</th><th>Created</th><th></th></tr></thead><tbody id="sutb"></tbody></table></div>
      </section>


      <!-- REPORTS -->
      <section class="pg" id="pg-reports">
        <div class="pghdr"><div class="pgt">Reports</div><div class="pgs">Analytics &amp; workforce insights</div></div>
        <div class="tb">
          <div class="ssl" style="padding:0;font-size:11px;color:var(--txm)">Report Type</div>
          <select class="flt" id="rpt-type" onchange="rReport()" style="min-width:220px">
            <option value="headcount">&#128101; Headcount &amp; Department Summary</option>
            <option value="leave">&#128197; Leave &amp; Absence Report</option>
            <option value="payroll">&#128176; Payroll &amp; Salary Report</option>
            <option value="promotions">&#127942; Promotion History</option>
            <option value="behavior">&#9878;&#65039; Behaviour &amp; Work Ethics</option>
          </select>
          <div class="sp"></div>
          <button class="btn bh sm" onclick="exportRptCSV()">Export CSV</button>
          <button class="btn bh sm" onclick="window.print()">Print / PDF</button>
        </div>
        <div id="rpt-body"></div>
      </section>

      <!-- FEEDBACK -->
      <section class="pg" id="pg-feedback">
        <div class="pghdr"><div class="pgt">Feedback</div><div class="pgs">Two-way communication channel</div></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px">
          <div class="card">
            <div class="ct">Submit Feedback</div>
            <div style="display:flex;flex-direction:column;gap:10px">
              <div class="fgr" id="fb-emp-row"><label class="flb">About Employee (ID)</label><input class="fi" id="fb-eid" placeholder="ARCH-2026-0001 or leave blank"></div>
              <div class="fgr"><label class="flb">Category</label>
                <select class="fsel" id="fb-cat">
                  <option value="performance">Performance</option><option value="behavior">Behaviour</option>
                  <option value="work_ethics">Work Ethics</option><option value="attendance">Attendance</option>
                  <option value="teamwork">Teamwork</option><option value="complaint">Complaint</option><option value="general">General</option>
                </select>
              </div>
              <div class="fgr"><label class="flb">Subject</label><input class="fi" id="fb-sub" placeholder="Brief summary..."></div>
              <div class="fgr"><label class="flb">Details</label><textarea class="fta" id="fb-body" placeholder="Describe in detail..." style="min-height:88px"></textarea></div>
              <div class="fgr"><label class="flb">Rating (optional)</label>
                <select class="fsel" id="fb-rate"><option value="">No rating</option><option value="5">5 - Excellent</option><option value="4">4 - Good</option><option value="3">3 - Average</option><option value="2">2 - Below Average</option><option value="1">1 - Poor</option></select>
              </div>
              <div style="display:flex;align-items:center;gap:8px">
                <input type="checkbox" id="fb-anon" style="accent-color:var(--gold);width:15px;height:15px">
                <label for="fb-anon" style="font-size:12px;color:var(--txm);cursor:pointer">Submit anonymously</label>
              </div>
              <button class="btn bg" onclick="subFeedback()">Submit Feedback</button>
            </div>
          </div>
          <div class="card"><div class="ct">Overview</div><div id="fb-stats" style="display:flex;flex-direction:column;gap:8px"></div></div>
        </div>
        <div class="tb">
          <select class="flt" id="fb-fcat" onchange="rFeedback()"><option value="">All Categories</option><option value="performance">Performance</option><option value="behavior">Behaviour</option><option value="work_ethics">Work Ethics</option><option value="attendance">Attendance</option><option value="teamwork">Teamwork</option><option value="complaint">Complaint</option><option value="general">General</option></select>
          <select class="flt" id="fb-fst" onchange="rFeedback()"><option value="">All Status</option><option value="open">Open</option><option value="reviewed">Reviewed</option><option value="resolved">Resolved</option></select>
          <div class="sp"></div>
        </div>
        <div id="fb-list"></div>
      </section>

      <div class="mo2" id="m-fb"><div class="mdl" style="width:640px">
        <div class="mdlt" id="m-fb-t">Feedback Detail</div>
        <div id="m-fb-body"></div>
        <div id="fb-reply-row" style="margin-top:14px;display:none">
          <div class="fgr"><label class="flb">Add Response</label><textarea class="fta" id="fb-reply" placeholder="Your response..." style="min-height:72px"></textarea></div>
          <div style="display:flex;gap:8px;margin-top:8px">
            <select class="fsel" id="fb-res-st" style="width:160px"><option value="reviewed">Mark Reviewed</option><option value="resolved">Mark Resolved</option><option value="open">Keep Open</option></select>
            <button class="btn bg" onclick="sendFbReply()">Send Response</button>
          </div>
        </div>
        <div class="mact"><button class="btn bh" onclick="cm('m-fb')">Close</button></div>
      </div></div>

      <style>
      .rpt-card{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:18px;margin-bottom:12px}
      .rpt-title{font-family:var(--bb);font-size:18px;letter-spacing:.04em;color:var(--gold);margin-bottom:12px}
      .rpt-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:14px}
      .rpt-stat{background:var(--card2);border:1px solid var(--bdr);border-radius:8px;padding:12px;text-align:center}
      .rpt-sv{font-family:var(--bb);font-size:32px;color:#fff}
      .rpt-sl{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--txm);margin-top:2px}
      .fb-card{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:14px;margin-bottom:10px;cursor:pointer;transition:all .15s;border-left:3px solid transparent}
      .fb-card:hover{border-color:var(--gold)}
      .fb-card.unread{border-left:3px solid var(--gold)}
      .fb-sub{font-size:14px;font-weight:600;color:#fff}
      .fb-meta{font-size:11px;color:var(--txm)}
      .fb-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:5px}
      .reply-bub{background:var(--card2);border-radius:8px;padding:10px 14px;margin-top:8px}
      .reply-who{font-size:11px;font-weight:700;color:var(--gold);margin-bottom:3px}
      @media print{#sb,#hdr,#np,.tb,button,.nbtn,.lout{display:none!important}#main{padding:0!important}body{background:#fff;color:#000}}
      </style>

      <!-- PROFILE -->
      <section class="pg" id="pg-profile">
        <div class="pghdr"><div class="pgt">My Profile</div><div class="pgs">Account settings</div></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          <div class="card">
            <div class="ct">Profile</div>
            <div style="text-align:center;margin-bottom:16px">
              <div class="pavw" onclick="document.getElementById('pfi').click()">
                <img id="pav" src="" style="display:none;width:84px;height:84px;border-radius:50%;object-fit:cover;border:3px solid var(--gold)">
                <div id="pavp" style="width:84px;height:84px;border-radius:50%;background:var(--card2);border:3px solid var(--gold);display:flex;align-items:center;justify-content:center;font-size:32px;margin:0 auto">👤</div>
                <div class="pavb">✏️</div>
              </div>
              <input type="file" id="pfi" accept="image/*" style="display:none" onchange="upPhoto(this)">
              <div style="font-family:var(--bb);font-size:19px;color:#fff;margin-top:9px" id="pfn">—</div>
              <div class="bdg bgold" style="margin-top:5px" id="pfrb">—</div>
            </div>
            <div class="irow"><span class="ik">Username</span><span class="iv" style="font-family:var(--mo);font-size:12px" id="pfu">—</span></div>
            <div class="irow"><span class="ik">Employee ID</span><span class="iv" style="font-family:var(--mo);font-size:12px" id="pfeid">—</span></div>
          </div>
          <div class="card">
            <div class="ct">Change Password</div>
            <div style="display:flex;flex-direction:column;gap:10px">
              <div class="fgr"><label class="flb">Current Password</label><input class="fi" id="pwc" type="password" placeholder="••••••••"></div>
              <div class="fgr"><label class="flb">New Password</label><input class="fi" id="pwn" type="password" placeholder="Min 6 characters"></div>
              <div class="fgr"><label class="flb">Confirm New</label><input class="fi" id="pwcf" type="password" placeholder="Repeat new password"></div>
              <button class="btn bg" onclick="chgPw()">Update Password</button>
            </div>
          </div>
        </div>
      </section>

    </main>
  </div>
</div>

<!-- NOTIFICATIONS PANEL -->
<div id="np">
  <div class="nph"><div class="npht">🔔 Notifications</div><button class="btn bh sm" onclick="markAllRead()">Mark All Read</button></div>
  <div class="npb" id="npl"></div>
</div>

<!-- EMPLOYEE MODAL -->
<div class="mo2" id="m-emp"><div class="mdl" style="width:680px">
  <div class="mdlt" id="m-emp-t">Add Employee</div>
  <input type="hidden" id="me-id">
  <div class="fg">
    <div class="fgr"><label class="flb">Full Name *</label><input class="fi" id="me-fn" placeholder="First Last"></div>
    <div class="fgr"><label class="flb">Email</label><input class="fi" id="me-em" type="email" placeholder="email@co.com"></div>
    <div class="fgr"><label class="flb">Department</label><select class="fsel" id="me-dept"></select></div>
    <div class="fgr"><label class="flb">Occupation / Title</label><input class="fi" id="me-occ" placeholder="e.g. Software Engineer"></div>
    <div class="fgr"><label class="flb">Role / Level</label><input class="fi" id="me-rl" placeholder="e.g. Senior, Manager"></div>
    <div class="fgr"><label class="flb">Age</label><input class="fi" id="me-age" type="number" placeholder="28"></div>
    <div class="fgr"><label class="flb">Location</label><input class="fi" id="me-loc" placeholder="City, Country"></div>
    <div class="fgr"><label class="flb">Employment Type</label>
      <select class="fsel" id="me-et"><option value="permanent">Permanent</option><option value="contract">Contract</option><option value="probation">Probation</option><option value="intern">Intern</option><option value="part_time">Part Time</option></select></div>
    <div class="fgr"><label class="flb">Status</label>
      <select class="fsel" id="me-st"><option value="active">Active</option><option value="inactive">Inactive</option><option value="on_leave">On Leave</option></select></div>
    <div class="fgr full"><label class="flb">Purpose / Job Description</label><textarea class="fta" id="me-pur" placeholder="Describe this employee's role and responsibilities within their department…" style="min-height:80px"></textarea></div>
    <div class="fgr"><label class="flb">Contract End Date</label><input class="fi" id="me-ce" type="date"></div>
    <div class="fgr"><label class="flb">Salary</label><input class="fi" id="me-sal" type="number" placeholder="50000"></div>
    <div class="fgr"><label class="flb">Currency</label>
      <select class="fsel" id="me-cur"><option value="USD">USD</option><option value="EUR">EUR</option><option value="GBP">GBP</option><option value="NGN">NGN</option><option value="KES">KES</option><option value="ZAR">ZAR</option><option value="GHS">GHS</option></select></div>
  </div>
  <div class="mact"><button class="btn bh" onclick="cm('m-emp')">Cancel</button><button class="btn bg" onclick="saveEmp()">Save Employee</button></div>
</div></div>

<!-- VIEW EMP MODAL -->
<div class="mo2" id="m-vew"><div class="mdl" style="width:660px">
  <div class="mdlt">Employee Details</div>
  <div id="vew-cnt"></div>
  <div class="mact">
    <button class="btn bh" onclick="cm('m-vew')">Close</button>
    <button class="btn br sm" id="vew-del" onclick="delEmpFromView()" style="display:none">🗑 Delete</button>
    <button class="btn bg" id="vew-edt" onclick="editFromView()" style="display:none">✏️ Edit</button>
  </div>
</div></div>

<!-- DEPT MODAL -->
<div class="mo2" id="m-dept"><div class="mdl">
  <div class="mdlt" id="m-dept-t">Add Department</div>
  <input type="hidden" id="md-on">
  <div class="fg">
    <div class="fgr full"><label class="flb">Department Name *</label><input class="fi" id="md-nm" placeholder="e.g. Engineering"></div>
    <div class="fgr full"><label class="flb">Description</label><textarea class="fta" id="md-ds" placeholder="Brief description…"></textarea></div>
    <div class="fgr full"><label class="flb">Head Employee ID (optional)</label><input class="fi" id="md-hd" placeholder="ARCH-2026-0001"></div>
  </div>
  <div class="mact"><button class="btn bh" onclick="cm('m-dept')">Cancel</button><button class="btn bg" onclick="saveDept()">Save</button></div>
</div></div>

<!-- PAYROLL MODAL -->
<div class="mo2" id="m-pay"><div class="mdl">
  <div class="mdlt">Edit Salary</div>
  <input type="hidden" id="mp-id">
  <div class="fg">
    <div class="fgr"><label class="flb">Salary Amount</label><input class="fi" id="mp-sal" type="number" placeholder="50000"></div>
    <div class="fgr"><label class="flb">Currency</label>
      <select class="fsel" id="mp-cur"><option value="USD">USD</option><option value="EUR">EUR</option><option value="GBP">GBP</option><option value="NGN">NGN</option><option value="KES">KES</option><option value="ZAR">ZAR</option><option value="GHS">GHS</option></select></div>
  </div>
  <div class="mact"><button class="btn bh" onclick="cm('m-pay')">Cancel</button><button class="btn bg" onclick="savePay()">Save</button></div>
</div></div>

<!-- SYS USER MODAL -->
<div class="mo2" id="m-su"><div class="mdl">
  <div class="mdlt" id="m-su-t">Add System User</div>
  <input type="hidden" id="su-ou">
  <div class="fg">
    <div class="fgr"><label class="flb">Username *</label><input class="fi" id="su-un" placeholder="unique_username"></div>
    <div class="fgr"><label class="flb">Full Name</label><input class="fi" id="su-fn" placeholder="First Last"></div>
    <div class="fgr"><label class="flb">Role</label>
      <select class="fsel" id="su-rl"><option value="staff">Staff</option><option value="manager">Manager</option><option value="hr">HR Manager</option><option value="admin">Admin</option></select></div>
    <div class="fgr"><label class="flb">Employee ID (optional)</label><input class="fi" id="su-eid" placeholder="ARCH-2026-0001"></div>
    <div class="fgr full"><label class="flb">Password (blank = keep existing)</label><input class="fi" id="su-pw" type="password" placeholder="Min 6 characters"></div>
  </div>
  <div class="mact"><button class="btn bh" onclick="cm('m-su')">Cancel</button><button class="btn bg" onclick="saveSU()">Save</button></div>
</div></div>

<!-- IMPORT MODAL -->
<div class="mo2" id="m-imp"><div class="mdl">
  <div class="mdlt">Import Employees</div>
  <p style="font-size:13px;color:var(--txm);margin-bottom:14px">Upload JSON or CSV. Existing IDs are overwritten.</p>
  <input type="file" id="impf" accept=".json,.csv" class="fi">
  <div class="mact"><button class="btn bh" onclick="cm('m-imp')">Cancel</button><button class="btn bg" onclick="doImport()">Import</button></div>
</div></div>

<div id="toast"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
const S = {user:null,employees:{},departments:{},sysUsers:{},auditLog:[],notifications:[],leaveReqs:[],selEmp:null,selPromo:null,selLeave:null,charts:{},npOpen:false};
const RL={admin:4,hr:3,manager:2,staff:1};
const RLAB={admin:'Admin',hr:'HR Manager',manager:'Manager',staff:'Staff'};
const ET={permanent:'Permanent',contract:'Contract',probation:'Probation',intern:'Intern',part_time:'Part Time'};
const LT={annual:'Annual',sick:'Sick',maternity:'Maternity/Paternity',unpaid:'Unpaid',other:'Other'};

// ── BOOT
window.addEventListener('load',async()=>{
  initParticles();
  try{const r=await fetch('/api/me');if(r.ok){S.user=await r.json();await loadAll();showApp();document.getElementById('ls').classList.add('gone');return;}}catch(e){}
  setTimeout(()=>document.getElementById('lfw').classList.add('vis'),2700);
});

function initParticles(){
  const cv=document.getElementById('lc'),cx=cv.getContext('2d');
  const pts=[];
  function rsz(){cv.width=innerWidth;cv.height=innerHeight;}rsz();window.addEventListener('resize',rsz);
  for(let i=0;i<65;i++)pts.push({x:Math.random()*innerWidth,y:Math.random()*innerHeight,vx:(Math.random()-.5)*.35,vy:(Math.random()-.5)*.35,r:Math.random()*1.5+.4,a:Math.random()*.3+.08});
  function draw(){
    cx.clearRect(0,0,cv.width,cv.height);
    for(let i=0;i<pts.length;i++){
      for(let j=i+1;j<pts.length;j++){const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y,d=Math.sqrt(dx*dx+dy*dy);if(d<130){cx.strokeStyle=`rgba(201,168,76,${.055*(1-d/130)})`;cx.lineWidth=.4;cx.beginPath();cx.moveTo(pts[i].x,pts[i].y);cx.lineTo(pts[j].x,pts[j].y);cx.stroke();}}
      pts[i].x+=pts[i].vx;pts[i].y+=pts[i].vy;
      if(pts[i].x<0||pts[i].x>cv.width)pts[i].vx*=-1;if(pts[i].y<0||pts[i].y>cv.height)pts[i].vy*=-1;
      cx.fillStyle=`rgba(201,168,76,${pts[i].a})`;cx.beginPath();cx.arc(pts[i].x,pts[i].y,pts[i].r,0,Math.PI*2);cx.fill();
    }
    requestAnimationFrame(draw);
  }draw();
}

// ── AUTH
async function doLogin(){
  const u=v('lu'),p=v('lp'),el=document.getElementById('lerr');
  if(!u||!p){el.textContent='Please enter credentials.';return;}
  const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
  if(!r.ok){el.textContent=(await r.json()).error||'Login failed.';return;}
  S.user=await r.json();
  document.getElementById('spl').classList.add('hidden');
  await loadAll();
  document.getElementById('ls').classList.add('gone');
  showApp();
}
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&!document.getElementById('ls').classList.contains('gone'))doLogin();});
async function doLogout(){await fetch('/api/logout',{method:'POST'});location.reload();}

// ── SHOW APP
function showApp(){
  const a=document.getElementById('app');a.style.display='flex';a.classList.add('vis');
  const lvl=RL[S.user.role]||1;
  document.body.className='r'+S.user.role.charAt(0);
  document.getElementById('hname').textContent=S.user.full_name;
  document.getElementById('hrole').textContent=(RLAB[S.user.role]||S.user.role).toUpperCase();
  if(S.user.photo)document.getElementById('hav').innerHTML=`<img src="${S.user.photo}" style="width:30px;height:30px;border-radius:50%;object-fit:cover;border:2px solid var(--gd)">`;
  if(lvl>=2){['sb-reports','sb-feedback'].forEach(id=>{const el=document.getElementById(id);if(el)el.style.display='';});}  if(lvl>=3){['sb-payroll','sb-audit','add-emp-btn','add-dept-btn','promo-apr','promo-dny','lv-apr','lv-dny'].forEach(id=>{const el=document.getElementById(id);if(el)el.style.display='';});}
  if(lvl===4)document.getElementById('sb-su').style.display='';
  if(lvl>=3){['prq-card','lv-eid-row'].forEach(id=>{const el=document.getElementById(id);if(el)el.style.display='';});}
  document.querySelectorAll('.nb[data-p]').forEach(b=>b.addEventListener('click',()=>nav(b.dataset.p)));
  nav('dashboard');
}

// ── NAV
function nav(p){
  const lvl=RL[S.user.role]||1;
  if((p==='payroll'||p==='audit')&&lvl<3){toast('HR or Admin access required.','error');return;}
  if(p==='sysusers'&&lvl<4){toast('Admin access required.','error');return;}
  document.querySelectorAll('.pg').forEach(x=>x.classList.remove('act'));
  document.querySelectorAll('.nb').forEach(x=>x.classList.remove('act'));
  const pg=document.getElementById('pg-'+p);if(!pg)return;pg.classList.add('act');
  document.querySelectorAll(`.nb[data-p="${p}"]`).forEach(b=>b.classList.add('act'));
  document.getElementById('bcp').textContent={dashboard:'Dashboard',employees:'Employees',departments:'Departments',promotions:'Promotions',leave:'Leave Management',payroll:'Payroll & Salary',audit:'Audit Log',sysusers:'System Users',profile:'My Profile'}[p]||p;
  if(p==='dashboard')renderDash();
  if(p==='employees')rEmp();
  if(p==='departments')rDepts();
  if(p==='promotions')rPromo();
  if(p==='leave')rLeave();
  if(p==='payroll')rPay();
  if(p==='audit')rAudit();
  if(p==='sysusers')rSU();
  if(p==='profile')rProfile();
  if(p==='reports')rReport();
  if(p==='feedback'){S.feedback=S.feedback||[];rFeedback();}
}

// ── DATA LOAD
async function loadAll(){
  const r=await fetch('/api/data');const d=await r.json();
  S.employees=d.employees||{};S.departments=d.departments||{};S.feedback=d.feedback||[];
  S.sysUsers=d.system_users||{};S.auditLog=d.audit_log||[];
  S.notifications=d.notifications||[];S.leaveReqs=d.leave_requests||[];
  refreshBadges();refreshNotifPanel();
}

function refreshBadges(){
  const pe=S.leaveReqs.filter(r=>r.status==='pending').length;
  const pfb=(S.feedback||[]).filter(f=>f.status==='open'&&!(f.read_by||[]).includes(S.user.username)).length;
  setBdg('bdg-fb',pfb);
  const pp=Object.values(S.employees).reduce((n,e)=>(e.promotion_requests||[]).filter(r=>r.status==='pending').length+n,0);
  const unr=S.notifications.filter(n=>!n.read_by?.includes(S.user.username)).length;
  setBdg('bdg-l',pe);setBdg('bdg-p',pp);
  const nbdg=document.getElementById('nbdg');
  if(unr>0){nbdg.textContent=unr>9?'9+':unr;nbdg.classList.add('v');}else{nbdg.classList.remove('v');}
}
function setBdg(id,n){const el=document.getElementById(id);if(!el)return;if(n>0){el.textContent=n;el.classList.add('v');}else el.classList.remove('v');}

// ── DASHBOARD
const GCOLS=['#c9a84c','#4f8ef7','#3dba7a','#e09a30','#e05252','#7c5df9','#2dd4bf','#f472b6'];
function renderDash(){
  const emps=Object.values(S.employees);
  const active=emps.filter(e=>e.status==='active').length;
  const pend=emps.reduce((n,e)=>(e.promotion_requests||[]).filter(r=>r.status==='pending').length+n,0);
  const onLeave=emps.filter(e=>e.status==='on_leave').length;
  const depts=Object.keys(S.departments).length;
  const stats=[
    {label:'Total Employees',val:emps.length,cls:''},
    {label:'Active',val:active,cls:'gn'},
    {label:'On Leave',val:onLeave,cls:'wn'},
    {label:'Pending Promotions',val:pend,cls:'rd'},
    {label:'Departments',val:depts,cls:'bl'},
    {label:'Leave Requests',val:S.leaveReqs.filter(r=>r.status==='pending').length,cls:'wn'},
  ];
  document.getElementById('dstats').innerHTML=stats.map(s=>`<div class="sc ${s.cls}"><div class="sv">${s.val}</div><div class="slb">${s.label}</div></div>`).join('');

  // dept chart
  const dmap={};
  emps.forEach(e=>{if(e.department)dmap[e.department]=(dmap[e.department]||0)+1;});
  const dlabs=Object.keys(dmap),dvals=Object.values(dmap);
  mkChart('ch-dept','doughnut',dlabs,dvals);

  // type chart
  const tmap={};
  emps.forEach(e=>{const t=ET[e.employment_type]||e.employment_type||'Unknown';tmap[t]=(tmap[t]||0)+1;});
  mkChart('ch-type','bar',Object.keys(tmap),Object.values(tmap));

  // recent audit
  const el=document.getElementById('daud');
  const recent=S.auditLog.slice(0,8);
  el.innerHTML=recent.length?recent.map(a=>`<div class="ae"><div class="adot"></div><div><div style="font-size:12px">${esc(a.user)} <span style="color:var(--txm)">${esc(a.action)}</span> <strong>${esc(a.target)}</strong>${a.detail?' — '+esc(a.detail):''}</div><div class="ats">${esc(a.ts)}</div></div></div>`).join(''):'<div style="color:var(--txm);font-size:12px;padding:8px 0">No activity yet.</div>';
}

function mkChart(id,type,labels,data){
  if(S.charts[id])S.charts[id].destroy();
  const ctx=document.getElementById(id);if(!ctx)return;
  S.charts[id]=new Chart(ctx,{type,data:{labels,datasets:[{data,backgroundColor:GCOLS,borderColor:GCOLS,borderWidth:type==='bar'?0:2,borderRadius:type==='bar'?5:0}]},options:{responsive:true,plugins:{legend:{display:type==='doughnut',labels:{color:'#d4d8f0',font:{size:11}}}},scales:type==='bar'?{x:{ticks:{color:'#5a6080'},grid:{color:'rgba(30,34,64,.5)'}},y:{ticks:{color:'#5a6080'},grid:{color:'rgba(30,34,64,.5)'}}}:{}}});
}

// ── EMPLOYEES
function rEmp(){
  const q=(document.getElementById('esrch')?.value||'').toLowerCase();
  const fd=document.getElementById('efd')?.value||'';
  const fs=document.getElementById('efs')?.value||'';
  // refresh dept filter
  const dsel=document.getElementById('efd');
  const curD=dsel.value;
  dsel.innerHTML='<option value="">All Departments</option>'+Object.keys(S.departments).map(d=>`<option value="${esc(d)}" ${d===curD?'selected':''}>${esc(d)}</option>`).join('');

  const rows=Object.entries(S.employees).filter(([id,e])=>{
    if(fd&&e.department!==fd)return false;
    if(fs&&e.status!==fs)return false;
    if(q&&![id,e.full_name,e.email,e.department,e.occupation,e.role].some(x=>(x||'').toLowerCase().includes(q)))return false;
    // staff can only see own record
    if(S.user.role==='staff'&&id!==S.user.emp_id)return false;
    return true;
  });
  const tb=document.getElementById('etb');
  if(!rows.length){tb.innerHTML='<tr class="er"><td colspan="9">No employees found.</td></tr>';return;}
  tb.innerHTML=rows.map(([id,e])=>{
    const photo=e.photo?`<img class="ep" src="${e.photo}">`:`<div class="epp">👤</div>`;
    const sbc={active:'bgreen',inactive:'bgray',on_leave:'bwarn'}[e.status]||'bgray';
    const tbc={permanent:'bgold',contract:'bblue',probation:'bwarn',intern:'bgray',part_time:'bgray'}[e.employment_type]||'bgray';
    return `<tr onclick="viewEmp('${esc(id)}')">
      <td>${photo}</td>
      <td style="font-family:var(--mo);font-size:11px">${esc(id)}</td>
      <td><strong>${esc(e.full_name||'')}</strong></td>
      <td>${esc(e.department||'')}</td>
      <td>${esc(e.occupation||'')}</td>
      <td><span class="bdg ${tbc}">${esc(ET[e.employment_type]||e.employment_type||'—')}</span></td>
      <td><span class="bdg ${sbc}">${esc(e.status||'—')}</span></td>
      <td style="font-size:11px;color:var(--txm)">${esc(e.date_added||'')}</td>
      <td><button class="btn bh sm" onclick="event.stopPropagation();viewEmp('${esc(id)}')">View</button></td>
    </tr>`;
  }).join('');
}

function viewEmp(id){
  S.selEmp=id;const e=S.employees[id];if(!e)return;
  const lvl=RL[S.user.role]||1;
  const salary=lvl>=3?`<div class="irow"><span class="ik">Salary</span><span class="iv" style="font-family:var(--mo);color:var(--gold)">${e.salary?e.salary_currency+' '+Number(e.salary).toLocaleString():'—'}</span></div>`:''
  document.getElementById('vew-cnt').innerHTML=`
    <div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:16px">
      ${e.photo?`<img src="${e.photo}" style="width:72px;height:72px;border-radius:50%;object-fit:cover;border:3px solid var(--gold);flex-shrink:0">`:`<div style="width:72px;height:72px;border-radius:50%;background:var(--card2);border:3px solid var(--gold);display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0">👤</div>`}
      <div><div style="font-family:var(--bb);font-size:22px;color:#fff">${esc(e.full_name||'')}</div>
      <div style="color:var(--txm);font-size:12px">${esc(e.occupation||'—')}</div>
      <div class="bdg bgold" style="margin-top:6px">${esc(id)}</div></div>
    </div>
    <div class="irow"><span class="ik">Email</span><span class="iv">${esc(e.email||'—')}</span></div>
    <div class="irow"><span class="ik">Department</span><span class="iv">${esc(e.department||'—')}</span></div>
    <div class="irow"><span class="ik">Role / Level</span><span class="iv">${esc(e.role||'—')}</span></div>
    <div class="irow"><span class="ik">Employment Type</span><span class="iv">${esc(ET[e.employment_type]||e.employment_type||'—')}</span></div>
    <div class="irow"><span class="ik">Status</span><span class="iv">${esc(e.status||'—')}</span></div>
    <div class="irow"><span class="ik">Location</span><span class="iv">${esc(e.location||'—')}</span></div>
    <div class="irow"><span class="ik">Age</span><span class="iv">${esc(e.age||'—')}</span></div>
    <div class="irow"><span class="ik">Contract End</span><span class="iv">${esc(e.contract_end||'—')}</span></div>
    ${e.purpose?`<div style="margin-top:10px;padding:10px 0;border-top:1px solid var(--bdr)"><div style="font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--txm);margin-bottom:6px">Purpose / Job Description</div><div style="font-size:13px;line-height:1.6;color:var(--tx)">${esc(e.purpose)}</div></div>`:''}
    ${salary}
    <div class="irow"><span class="ik">Date Added</span><span class="iv">${esc(e.date_added||'—')}</span></div>`;
  const lvl2=RL[S.user.role]||1;
  const edtBtn=document.getElementById('vew-edt');const delBtn=document.getElementById('vew-del');
  if(edtBtn)edtBtn.style.display=lvl2>=3?'':'none';
  if(delBtn)delBtn.style.display=lvl2>=3?'':'none';
  openModal('m-vew');
}
function editFromView(){cm('m-vew');if(S.selEmp)oEditEmp(S.selEmp);}
async function delEmpFromView(){
  if(!S.selEmp||!confirm(`Delete employee ${S.selEmp}? This cannot be undone.`))return;
  const r=await api('DELETE',`/api/employees/${encodeURIComponent(S.selEmp)}`);
  if(r.ok){delete S.employees[S.selEmp];S.selEmp=null;cm('m-vew');rEmp();renderDash();toast('Employee deleted.','success');}
  else toast((await r.json()).error,'error');
}

function oAddEmp(){
  S.selEmp=null;document.getElementById('m-emp-t').textContent='Add Employee';
  const dsel=document.getElementById('me-dept');
  dsel.innerHTML=Object.keys(S.departments).map(d=>`<option value="${esc(d)}">${esc(d)}</option>`).join('');
  ['me-id','me-fn','me-em','me-occ','me-rl','me-age','me-loc','me-ce','me-sal','me-pur'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('me-et').value='permanent';
  document.getElementById('me-st').value='active';
  document.getElementById('me-cur').value='USD';
  openModal('m-emp');
}
function oEditEmp(id){
  S.selEmp=id;const e=S.employees[id];if(!e)return;
  document.getElementById('m-emp-t').textContent='Edit Employee';
  document.getElementById('me-id').value=id;
  const dsel=document.getElementById('me-dept');
  dsel.innerHTML=Object.keys(S.departments).map(d=>`<option value="${esc(d)}" ${d===e.department?'selected':''}>${esc(d)}</option>`).join('');
  set('me-fn',e.full_name);set('me-em',e.email);set('me-occ',e.occupation);
  set('me-rl',e.role);set('me-age',e.age);set('me-loc',e.location);
  set('me-ce',e.contract_end);set('me-sal',e.salary);set('me-pur',e.purpose);
  document.getElementById('me-et').value=e.employment_type||'permanent';
  document.getElementById('me-st').value=e.status||'active';
  document.getElementById('me-cur').value=e.salary_currency||'USD';
  openModal('m-emp');
}
async function saveEmp(){
  const id=document.getElementById('me-id').value;
  const body={full_name:v('me-fn'),email:v('me-em'),department:document.getElementById('me-dept').value,occupation:v('me-occ'),role:v('me-rl'),purpose:v('me-pur'),age:v('me-age'),location:v('me-loc'),employment_type:document.getElementById('me-et').value,status:document.getElementById('me-st').value,contract_end:v('me-ce'),salary:v('me-sal'),salary_currency:document.getElementById('me-cur').value};
  if(!body.full_name){toast('Full name is required.','error');return;}
  const r=await api(id?'PUT':'POST',id?`/api/employees/${encodeURIComponent(id)}`:'/api/employees',body);
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees[d.id]=d.employee;cm('m-emp');rEmp();renderDash();
  toast(id?'Employee updated.':'Employee added.','success');
}
function expMenu(){window.location.href='/api/export/employees-csv';}

// ── DEPARTMENTS
function rDepts(){
  const lvl=RL[S.user.role]||1;
  document.getElementById('deptg').innerHTML=Object.entries(S.departments).map(([n,d])=>{
    const cnt=Object.values(S.employees).filter(e=>e.department===n).length;
    const head=d.head_id?S.employees[d.head_id]?.full_name||d.head_id:'No head assigned';
    const editBtn=lvl>=3?`<button class="btn bh sm" onclick="oEditDept('${esc(n)}')">Edit</button>`:''
    const delBtn=lvl>=4?`<button class="btn br sm" onclick="delDept('${esc(n)}')">Delete</button>`:''
    return `<div class="dc"><div class="dcc">${cnt}</div>
      <div class="dcn">${esc(n)}</div>
      <div class="dcd">${esc(d.description||'')}</div>
      <div class="dch">👤 ${esc(head)}</div>
      <div class="dca">${editBtn}${delBtn}</div></div>`;
  }).join('')||'<div style="color:var(--txm);font-size:13px">No departments found.</div>';
}
function oAddDept(){document.getElementById('m-dept-t').textContent='Add Department';['md-on','md-nm','md-ds','md-hd'].forEach(id=>document.getElementById(id).value='');openModal('m-dept');}
function oEditDept(n){
  document.getElementById('m-dept-t').textContent='Edit Department';
  const d=S.departments[n]||{};
  set('md-on',n);set('md-nm',n);set('md-ds',d.description);set('md-hd',d.head_id);
  openModal('m-dept');
}
async function saveDept(){
  const orig=v('md-on'),name=v('md-nm'),desc=v('md-ds'),head=v('md-hd');
  if(!name){toast('Department name required.','error');return;}
  const r=await api(orig?'PUT':'POST',orig?`/api/departments/${encodeURIComponent(orig)}`:'/api/departments',{name,description:desc,head_id:head||null});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  if(orig&&orig!==name)delete S.departments[orig];
  S.departments[name]=d.department;cm('m-dept');rDepts();toast('Department saved.','success');
}
async function delDept(n){
  if(!confirm(`Delete department "${n}"?`))return;
  const r=await api('DELETE',`/api/departments/${encodeURIComponent(n)}`);
  if(r.ok){delete S.departments[n];rDepts();toast('Department deleted.','success');}
  else toast((await r.json()).error,'error');
}

// ── PROMOTIONS
function rPromo(){
  const fl=document.getElementById('pfl')?.value||'';
  const rows=[];
  Object.entries(S.employees).forEach(([id,e])=>{
    (e.promotion_requests||[]).forEach((req,i)=>{
      if(fl&&req.status!==fl)return;
      rows.push({id,e,req,i});
    });
  });
  const tb=document.getElementById('ptb');
  if(!rows.length){tb.innerHTML='<tr class="er"><td colspan="6">No promotion requests.</td></tr>';return;}
  tb.innerHTML=rows.map(({id,e,req,i})=>{
    const sc={pending:'bwarn',approved:'bgreen',denied:'bred'}[req.status]||'bgray';
    return `<tr class="${S.selPromo===id+'::'+i?'sel':''}" onclick="selPromo2('${esc(id)}','${i}',this)"><td style="font-family:var(--mo);font-size:11px">${esc(id)}</td><td>${esc(e.full_name||'')}</td><td>${esc(req.current_role||'')}</td><td><strong>${esc(req.requested_role||'')}</strong></td><td style="font-size:11px;color:var(--txm)">${esc(req.date||'')}</td><td><span class="bdg ${sc}">${esc(req.status)}</span></td></tr>`;
  }).join('');
}
function selPromo2(id,i,row){S.selPromo=id+'::'+i;document.querySelectorAll('#ptb tr').forEach(r=>r.classList.remove('sel'));row.classList.add('sel');}
async function subPromo(){
  const eid=v('p-eid'),role=v('p-role');
  if(!eid||!role){toast('Employee ID and role required.','error');return;}
  const r=await api('POST','/api/promotions',{emp_id:eid,requested_role:role});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees[eid]=d.employee;set('p-eid','');set('p-role','');rPromo();refreshBadges();toast('Promotion request submitted.','success');
}
async function resPromo(res){
  if(!S.selPromo){toast('Select a request first.','error');return;}
  const [id,idx]=S.selPromo.split('::');
  const r=await api('PUT',`/api/promotions/${encodeURIComponent(id)}/${idx}`,{resolution:res});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees[id]=d.employee;S.selPromo=null;rPromo();refreshBadges();
  toast(`Request ${res==='approved'?'approved ✅':'denied ❌'}`,res==='approved'?'success':'error');
}

// ── LEAVE
function rLeave(){
  const fl=document.getElementById('lfl')?.value||'';
  const lvl=RL[S.user.role]||1;
  const rows=S.leaveReqs.filter(r=>{
    if(fl&&r.status!==fl)return false;
    if(lvl<3&&r.emp_id!==S.user.emp_id)return false;
    return true;
  });
  const tb=document.getElementById('ltb');
  if(!rows.length){tb.innerHTML='<tr class="er"><td colspan="7">No leave requests.</td></tr>';return;}
  tb.innerHTML=rows.map((r,idx)=>{
    const e=S.employees[r.emp_id]||{};
    const sc={pending:'bwarn',approved:'bgreen',denied:'bred'}[r.status]||'bgray';
    const days=r.start_date&&r.end_date?Math.ceil((new Date(r.end_date)-new Date(r.start_date))/(86400000))+1:'—';
    return `<tr class="${S.selLeave===idx?'sel':''}" onclick="selLeave2(${idx},this)"><td style="font-family:var(--mo);font-size:11px">${esc(r.emp_id||'')}</td><td>${esc(e.full_name||r.emp_id||'—')}</td><td>${esc(LT[r.leave_type]||r.leave_type||'—')}</td><td>${esc(r.start_date||'')}</td><td>${esc(r.end_date||'')}</td><td>${days}</td><td><span class="bdg ${sc}">${esc(r.status)}</span></td></tr>`;
  }).join('');
}
function selLeave2(idx,row){S.selLeave=idx;document.querySelectorAll('#ltb tr').forEach(r=>r.classList.remove('sel'));row.classList.add('sel');}
async function subLeave(){
  const eid=v('lv-eid')||S.user.emp_id;
  const ltype=document.getElementById('lv-type').value;
  const s=v('lv-s'),e2=v('lv-e');
  if(!s||!e2){toast('Start and end dates required.','error');return;}
  if(!eid){toast('Employee ID not found. Please link your account to an employee.','error');return;}
  const r=await api('POST','/api/leave',{emp_id:eid,leave_type:ltype,start_date:s,end_date:e2,notes:v('lv-r')});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.leaveReqs=d.leave_requests;set('lv-eid','');set('lv-s','');set('lv-e','');set('lv-r','');
  rLeave();refreshBadges();toast('Leave request submitted.','success');
}
async function resLeave(res){
  if(S.selLeave===null){toast('Select a request first.','error');return;}
  const r=await api('PUT',`/api/leave/${S.selLeave}`,{resolution:res});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.leaveReqs=d.leave_requests;S.selLeave=null;rLeave();refreshBadges();
  toast(`Leave ${res==='approved'?'approved ✅':'denied ❌'}`,res==='approved'?'success':'error');
}

// ── PAYROLL
function rPay(){
  const q=(document.getElementById('prsrch')?.value||'').toLowerCase();
  const rows=Object.entries(S.employees).filter(([id,e])=>!q||[id,e.full_name,e.department].some(x=>(x||'').toLowerCase().includes(q)));
  const total=rows.reduce((s,[,e])=>s+(parseFloat(e.salary)||0),0);
  const withSal=rows.filter(([,e])=>e.salary&&e.salary>0).length;
  document.getElementById('prstats').innerHTML=`
    <div class="sc"><div class="sv">${rows.length}</div><div class="slb">Total Employees</div></div>
    <div class="sc gn"><div class="sv">${withSal}</div><div class="slb">With Salary Data</div></div>
    <div class="sc bl"><div class="sv" style="font-size:18px">${total.toLocaleString()}</div><div class="slb">Total Salary (Mixed Currencies)</div></div>`;
  const tb=document.getElementById('prtb');
  if(!rows.length){tb.innerHTML='<tr class="er"><td colspan="8">No employees.</td></tr>';return;}
  tb.innerHTML=rows.map(([id,e])=>{
    const tbc={permanent:'bgold',contract:'bblue',probation:'bwarn',intern:'bgray',part_time:'bgray'}[e.employment_type]||'bgray';
    return `<tr><td style="font-family:var(--mo);font-size:11px">${esc(id)}</td><td><strong>${esc(e.full_name||'')}</strong></td><td>${esc(e.department||'')}</td><td>${esc(e.occupation||'')}</td><td style="font-family:var(--mo);color:var(--gold)">${e.salary?Number(e.salary).toLocaleString():'—'}</td><td>${esc(e.salary_currency||'—')}</td><td><span class="bdg ${tbc}">${esc(ET[e.employment_type]||e.employment_type||'—')}</span></td><td><button class="btn bh sm" onclick="editPay('${esc(id)}')">Edit</button></td></tr>`;
  }).join('');
}
function editPay(id){
  const e=S.employees[id]||{};
  document.getElementById('mp-id').value=id;
  set('mp-sal',e.salary);document.getElementById('mp-cur').value=e.salary_currency||'USD';
  openModal('m-pay');
}
async function savePay(){
  const id=v('mp-id'),sal=v('mp-sal'),cur=document.getElementById('mp-cur').value;
  const r=await api('PUT',`/api/employees/${encodeURIComponent(id)}`,{salary:sal,salary_currency:cur});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees[id]=d.employee;cm('m-pay');rPay();toast('Salary updated.','success');
}

// ── AUDIT
function rAudit(){
  const q=(document.getElementById('asrch')?.value||'').toLowerCase();
  const rows=S.auditLog.filter(a=>!q||[a.user,a.action,a.target,a.detail].some(x=>(x||'').toLowerCase().includes(q)));
  document.getElementById('audl').innerHTML=rows.length
    ?rows.map(a=>`<div class="ae"><div class="adot"></div><div><div style="font-size:12px;padding-top:1px">${esc(a.user)} <span style="color:var(--txm)">${esc(a.action)}</span> <strong>${esc(a.target)}</strong>${a.detail?' — <span style="color:var(--txm)">'+esc(a.detail)+'</span>':''}</div><div class="ats">${esc(a.ts)}</div></div></div>`).join('')
    :'<div style="color:var(--txm);font-size:13px;padding:20px 0">No audit entries found.</div>';
}

// ── SYSTEM USERS
function rSU(){
  const tb=document.getElementById('sutb');
  const rows=Object.entries(S.sysUsers);
  if(!rows.length){tb.innerHTML='<tr class="er"><td colspan="6">No system users.</td></tr>';return;}
  tb.innerHTML=rows.map(([u,d])=>{
    const rl={admin:'bred',hr:'bblue',manager:'bgreen',staff:'bgray'}[d.role]||'bgray';
    return `<tr><td style="font-family:var(--mo);font-size:12px">${esc(u)}</td><td>${esc(d.full_name||'')}</td><td><span class="bdg ${rl}">${esc(d.role)}</span></td><td style="font-family:var(--mo);font-size:11px">${esc(d.emp_id||'—')}</td><td style="font-size:11px;color:var(--txm)">${esc(d.created||'')}</td><td style="display:flex;gap:6px;padding:6px 12px"><button class="btn bh sm" onclick="oEditSU('${esc(u)}')">Edit</button>${u!==S.user.username?`<button class="btn br sm" onclick="delSU('${esc(u)}')">Del</button>`:''}</td></tr>`;
  }).join('');
}
function oAddSU(){document.getElementById('m-su-t').textContent='Add System User';['su-ou','su-un','su-fn','su-pw','su-eid'].forEach(id=>document.getElementById(id).value='');document.getElementById('su-rl').value='staff';openModal('m-su');}
function oEditSU(u){
  const d=S.sysUsers[u]||{};
  document.getElementById('m-su-t').textContent='Edit System User';
  set('su-ou',u);set('su-un',u);set('su-fn',d.full_name);set('su-eid',d.emp_id);
  document.getElementById('su-rl').value=d.role||'staff';
  document.getElementById('su-pw').value='';
  openModal('m-su');
}
async function saveSU(){
  const orig=v('su-ou'),un=v('su-un'),fn=v('su-fn'),role=document.getElementById('su-rl').value,pw=v('su-pw'),eid=v('su-eid');
  if(!un){toast('Username required.','error');return;}
  const r=await api(orig?'PUT':'POST',orig?`/api/sysusers/${encodeURIComponent(orig)}`:'/api/sysusers',{username:un,full_name:fn,role,password:pw||null,emp_id:eid||null});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.sysUsers=d.system_users;cm('m-su');rSU();toast('System user saved.','success');
}
async function delSU(u){
  if(!confirm(`Delete system user "${u}"?`))return;
  const r=await api('DELETE',`/api/sysusers/${encodeURIComponent(u)}`);
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.sysUsers=d.system_users;rSU();toast('User deleted.','success');
}

// ── PROFILE
function rProfile(){
  const u=S.user;
  document.getElementById('pfn').textContent=u.full_name||'—';
  document.getElementById('pfrb').textContent=(RLAB[u.role]||u.role||'—').toUpperCase();
  document.getElementById('pfu').textContent=u.username||'—';
  document.getElementById('pfeid').textContent=u.emp_id||'Not linked';
  if(u.photo){document.getElementById('pav').src=u.photo;document.getElementById('pav').style.display='';document.getElementById('pavp').style.display='none';}
  else{document.getElementById('pav').style.display='none';document.getElementById('pavp').style.display='flex';}
}
async function upPhoto(inp){
  const file=inp.files[0];if(!file)return;
  const reader=new FileReader();
  reader.onload=async(e)=>{
    const r=await api('PUT','/api/profile',{photo:e.target.result});
    const d=await r.json();
    if(!r.ok){toast(d.error,'error');return;}
    S.user.photo=e.target.result;rProfile();
    document.getElementById('hav').innerHTML=`<img src="${e.target.result}" style="width:30px;height:30px;border-radius:50%;object-fit:cover;border:2px solid var(--gd)">`;
    toast('Photo updated.','success');
  };
  reader.readAsDataURL(file);
}
async function chgPw(){
  const c=v('pwc'),n=v('pwn'),cf=v('pwcf');
  if(!c||!n){toast('Fill all fields.','error');return;}
  if(n!==cf){toast('Passwords do not match.','error');return;}
  if(n.length<6){toast('Password too short (min 6).','error');return;}
  const r=await api('POST','/api/change-password',{current:c,new:n});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  ['pwc','pwn','pwcf'].forEach(id=>set(id,''));toast('Password updated.','success');
}

// ── NOTIFICATIONS
function toggleNP(){S.npOpen=!S.npOpen;document.getElementById('np').classList.toggle('open',S.npOpen);}
function refreshNotifPanel(){
  const el=document.getElementById('npl');
  const relevant=S.notifications.filter(n=>n.roles.includes(S.user.role));
  if(!relevant.length){el.innerHTML='<div class="nem">No notifications.</div>';return;}
  el.innerHTML=relevant.map(n=>{
    const unr=!n.read_by?.includes(S.user.username);
    const dot={info:'#4f8ef7',success:'#3dba7a',warning:'#e09a30',error:'#e05252'}[n.type]||'#c9a84c';
    return `<div class="nit ${unr?'unr':''}" onclick="markRead('${n.id}',this)"><div class="nim"><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:${dot};margin-right:6px;vertical-align:middle"></span>${esc(n.message)}</div><div class="nts">${esc(n.ts)}</div></div>`;
  }).join('');
}
async function markRead(id,row){
  await api('POST','/api/notifications/read',{id});
  row.classList.remove('unr');
  const n=S.notifications.find(x=>x.id===id);
  if(n&&!n.read_by)n.read_by=[];
  if(n&&!n.read_by.includes(S.user.username))n.read_by.push(S.user.username);
  refreshBadges();
}
async function markAllRead(){
  await api('POST','/api/notifications/read-all');
  S.notifications.forEach(n=>{if(!n.read_by)n.read_by=[];if(!n.read_by.includes(S.user.username))n.read_by.push(S.user.username);});
  refreshNotifPanel();refreshBadges();
}

// ── IMPORT
async function doImport(){
  const f=document.getElementById('impf').files[0];if(!f){toast('Select a file.','error');return;}
  const fd=new FormData();fd.append('file',f);
  const r=await fetch('/api/import',{method:'POST',body:fd});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees=d.employees;cm('m-imp');rEmp();renderDash();toast(`Imported ${d.count} employees.`,'success');
}


// ── REPORTS
let _rptData=[];
function rReport(){
  const type=document.getElementById('rpt-type')?.value||'headcount';
  const body=document.getElementById('rpt-body');if(!body)return;
  const emps=Object.entries(S.employees);
  const leaves=S.leaveReqs||[];const fb=S.feedback||[];
  if(type==='headcount'){
    const depts={};
    emps.forEach(([id,e])=>{const d=e.department||'Unassigned';if(!depts[d])depts[d]={count:0,active:0,contract:0,probation:0};depts[d].count++;if(e.status==='active')depts[d].active++;if(e.employment_type==='contract')depts[d].contract++;if(e.employment_type==='probation')depts[d].probation++;});
    const total=emps.length,active=emps.filter(([,e])=>e.status==='active').length,onLeave=emps.filter(([,e])=>e.status==='on_leave').length;
    _rptData=Object.entries(depts).map(([d,v])=>({Department:d,Total:v.count,Active:v.active,Contract:v.contract,Probation:v.probation}));
    body.innerHTML=`<div class="rpt-card"><div class="rpt-title">Headcount & Department Summary</div>
      <div class="rpt-grid"><div class="rpt-stat"><div class="rpt-sv">${total}</div><div class="rpt-sl">Total</div></div><div class="rpt-stat"><div class="rpt-sv">${active}</div><div class="rpt-sl">Active</div></div><div class="rpt-stat"><div class="rpt-sv">${onLeave}</div><div class="rpt-sl">On Leave</div></div><div class="rpt-stat"><div class="rpt-sv">${Object.keys(depts).length}</div><div class="rpt-sl">Departments</div></div></div>
      <div class="tw"><table><thead><tr><th>Department</th><th>Total</th><th>Active</th><th>Contract</th><th>Probation</th></tr></thead><tbody>${Object.entries(depts).map(([d,v])=>`<tr><td><strong>${esc(d)}</strong></td><td>${v.count}</td><td>${v.active}</td><td>${v.contract}</td><td>${v.probation}</td></tr>`).join('')}</tbody></table></div></div>`;
  }else if(type==='leave'){
    const byType={};const byStatus={pending:0,approved:0,denied:0};
    leaves.forEach(r=>{const lt=r.leave_type||'other';byType[lt]=(byType[lt]||0)+1;byStatus[r.status]=(byStatus[r.status]||0)+1;});
    _rptData=leaves.map(r=>({ID:r.emp_id,Name:S.employees[r.emp_id]?.full_name||'',Type:r.leave_type,From:r.start_date,To:r.end_date,Status:r.status}));
    body.innerHTML=`<div class="rpt-card"><div class="rpt-title">Leave & Absence Report</div>
      <div class="rpt-grid"><div class="rpt-stat"><div class="rpt-sv">${leaves.length}</div><div class="rpt-sl">Total</div></div><div class="rpt-stat"><div class="rpt-sv">${byStatus.approved}</div><div class="rpt-sl">Approved</div></div><div class="rpt-stat"><div class="rpt-sv">${byStatus.pending}</div><div class="rpt-sl">Pending</div></div><div class="rpt-stat"><div class="rpt-sv">${byStatus.denied}</div><div class="rpt-sl">Denied</div></div>${Object.entries(byType).map(([t,n])=>`<div class="rpt-stat"><div class="rpt-sv">${n}</div><div class="rpt-sl">${esc(t)}</div></div>`).join('')}</div>
      <div class="tw"><table><thead><tr><th>Emp ID</th><th>Name</th><th>Department</th><th>Type</th><th>From</th><th>To</th><th>Status</th></tr></thead><tbody>${leaves.map(r=>{const e=S.employees[r.emp_id]||{};const sc={pending:'bwarn',approved:'bgreen',denied:'bred'}[r.status]||'bgray';return`<tr><td style="font-family:var(--mo);font-size:11px">${esc(r.emp_id||'')}</td><td>${esc(e.full_name||'')}</td><td>${esc(e.department||'')}</td><td>${esc(r.leave_type||'')}</td><td>${esc(r.start_date||'')}</td><td>${esc(r.end_date||'')}</td><td><span class="bdg ${sc}">${esc(r.status)}</span></td></tr>`}).join('')}</tbody></table></div></div>`;
  }else if(type==='payroll'){
    const lvl2=ROLE_LEVEL[S.user.role]||1;
    if(lvl2<3){body.innerHTML='<div class="card" style="color:var(--err)">HR or Admin access required.</div>';return;}
    const byCur={};let withSal=0;
    emps.forEach(([,e])=>{if(e.salary){withSal++;const c=e.salary_currency||'USD';byCur[c]=(byCur[c]||0)+parseFloat(e.salary||0);}});
    _rptData=emps.map(([id,e])=>({ID:id,Name:e.full_name,Department:e.department,Occupation:e.occupation,Role:e.role,Salary:e.salary,Currency:e.salary_currency,Type:e.employment_type}));
    body.innerHTML=`<div class="rpt-card"><div class="rpt-title">Payroll & Salary Report</div>
      <div class="rpt-grid"><div class="rpt-stat"><div class="rpt-sv">${emps.length}</div><div class="rpt-sl">Employees</div></div><div class="rpt-stat"><div class="rpt-sv">${withSal}</div><div class="rpt-sl">With Salary</div></div>${Object.entries(byCur).map(([c,t])=>`<div class="rpt-stat"><div class="rpt-sv" style="font-size:18px">${c} ${t.toLocaleString()}</div><div class="rpt-sl">Total ${c}</div></div>`).join('')}</div>
      <div class="tw"><table><thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Occupation</th><th>Role</th><th>Salary</th><th>CCY</th><th>Type</th></tr></thead><tbody>${emps.map(([id,e])=>`<tr><td style="font-family:var(--mo);font-size:11px">${esc(id)}</td><td>${esc(e.full_name||'')}</td><td>${esc(e.department||'')}</td><td>${esc(e.occupation||'')}</td><td>${esc(e.role||'')}</td><td style="font-family:var(--mo);color:var(--gold)">${e.salary?Number(e.salary).toLocaleString():'—'}</td><td>${esc(e.salary_currency||'—')}</td><td>${esc(e.employment_type||'')}</td></tr>`).join('')}</tbody></table></div></div>`;
  }else if(type==='promotions'){
    const rows=[];emps.forEach(([id,e])=>{(e.promotion_requests||[]).forEach(r=>rows.push({id,name:e.full_name||'',dept:e.department||'',req:r}));});
    const approved=rows.filter(r=>r.req.status==='approved').length,pending=rows.filter(r=>r.req.status==='pending').length;
    _rptData=rows.map(({id,name,dept,req})=>({ID:id,Name:name,Department:dept,'Current Role':req.current_role,'Requested Role':req.requested_role,Date:req.date,Status:req.status,'Resolved By':req.resolved_by||''}));
    body.innerHTML=`<div class="rpt-card"><div class="rpt-title">Promotion History Report</div>
      <div class="rpt-grid"><div class="rpt-stat"><div class="rpt-sv">${rows.length}</div><div class="rpt-sl">Total</div></div><div class="rpt-stat"><div class="rpt-sv">${approved}</div><div class="rpt-sl">Approved</div></div><div class="rpt-stat"><div class="rpt-sv">${pending}</div><div class="rpt-sl">Pending</div></div></div>
      <div class="tw"><table><thead><tr><th>Emp ID</th><th>Name</th><th>Department</th><th>Current Role</th><th>Requested Role</th><th>Date</th><th>Status</th><th>Resolved By</th></tr></thead><tbody>${rows.map(({id,name,dept,req})=>{const sc={pending:'bwarn',approved:'bgreen',denied:'bred'}[req.status]||'bgray';return`<tr><td style="font-family:var(--mo);font-size:11px">${esc(id)}</td><td>${esc(name)}</td><td>${esc(dept)}</td><td>${esc(req.current_role||'')}</td><td><strong>${esc(req.requested_role||'')}</strong></td><td style="font-size:11px;color:var(--txm)">${esc(req.date||'')}</td><td><span class="bdg ${sc}">${esc(req.status)}</span></td><td style="font-size:11px;color:var(--txm)">${esc(req.resolved_by||'—')}</td></tr>`}).join('')}</tbody></table></div></div>`;
  }else if(type==='behavior'){
    const bFb=fb.filter(f=>['behavior','work_ethics','attendance','complaint'].includes(f.category));
    const byEmpB={};bFb.forEach(f=>{if(f.emp_id){if(!byEmpB[f.emp_id])byEmpB[f.emp_id]={name:S.employees[f.emp_id]?.full_name||f.emp_id,dept:S.employees[f.emp_id]?.department||'—',count:0,cats:[]};byEmpB[f.emp_id].count++;byEmpB[f.emp_id].cats.push(f.category);}});
    _rptData=bFb.map(f=>({ID:f.id,Employee:f.emp_id||'General',Category:f.category,Subject:f.subject,From:f.is_anonymous?'Anonymous':f.from_user,Date:f.ts,Status:f.status}));
    body.innerHTML=`<div class="rpt-card"><div class="rpt-title">Behaviour & Work Ethics Report</div>
      <div class="rpt-grid"><div class="rpt-stat"><div class="rpt-sv">${bFb.length}</div><div class="rpt-sl">Total Reports</div></div><div class="rpt-stat"><div class="rpt-sv">${bFb.filter(f=>f.status==='open').length}</div><div class="rpt-sl">Open</div></div><div class="rpt-stat"><div class="rpt-sv">${bFb.filter(f=>f.status==='resolved').length}</div><div class="rpt-sl">Resolved</div></div><div class="rpt-stat"><div class="rpt-sv">${Object.keys(byEmpB).length}</div><div class="rpt-sl">Employees Flagged</div></div></div>
      ${Object.keys(byEmpB).length?`<div style="margin-bottom:10px"><div class="tw"><table><thead><tr><th>Emp ID</th><th>Name</th><th>Department</th><th>Reports</th><th>Categories</th></tr></thead><tbody>${Object.entries(byEmpB).map(([id,v])=>`<tr><td style="font-family:var(--mo);font-size:11px">${esc(id)}</td><td><strong>${esc(v.name)}</strong></td><td>${esc(v.dept)}</td><td>${v.count}</td><td style="font-size:11px;color:var(--txm)">${[...new Set(v.cats)].join(', ')}</td></tr>`).join('')}</tbody></table></div></div>`:''}
      <div class="tw"><table><thead><tr><th>Employee</th><th>Category</th><th>Subject</th><th>Submitted By</th><th>Date</th><th>Status</th></tr></thead><tbody>${bFb.length?bFb.map(f=>{const sc={open:'bwarn',reviewed:'bblue',resolved:'bgreen'}[f.status]||'bgray';return`<tr onclick="openFbDetail('${f.id}')" style="cursor:pointer"><td style="font-family:var(--mo);font-size:11px">${esc(f.emp_id||'—')}</td><td><span class="bdg bwarn">${esc(f.category)}</span></td><td>${esc(f.subject||'')}</td><td>${f.is_anonymous?'<span style="color:var(--txm);font-size:11px">Anonymous</span>':esc(f.from_user||'')}</td><td style="font-size:11px;color:var(--txm)">${esc((f.ts||'').slice(0,10))}</td><td><span class="bdg ${sc}">${esc(f.status)}</span></td></tr>`}).join(''):'<tr class="er"><td colspan="6">No behaviour reports found.</td></tr>'}</tbody></table></div></div>`;
  }
}
function exportRptCSV(){
  if(!_rptData.length){toast('Run a report first.','warn');return;}
  const keys=Object.keys(_rptData[0]);
  const rows=[keys.join(','),..._rptData.map(r=>keys.map(k=>`"${String(r[k]||'').replace(/"/g,'""')}"`).join(','))].join('\n');
  const a=document.createElement('a');a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(rows);a.download='archer_report.csv';a.click();
}

// ── FEEDBACK
async function subFeedback(){
  const eid=v('fb-eid'),cat=document.getElementById('fb-cat').value,sub=v('fb-sub'),content=v('fb-body');
  const anon=document.getElementById('fb-anon').checked,rating=document.getElementById('fb-rate').value;
  if(!sub||!content){toast('Subject and details required.','error');return;}
  const r=await api('POST','/api/feedback',{emp_id:eid||null,category:cat,subject:sub,content,rating:rating||null,is_anonymous:anon});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.feedback=d.feedback;
  set('fb-eid','');set('fb-sub','');set('fb-body','');
  document.getElementById('fb-rate').value='';document.getElementById('fb-anon').checked=false;
  rFeedback();refreshBadges();toast('Feedback submitted.','success');
}
function rFeedback(){
  const fcat=document.getElementById('fb-fcat')?.value||'';
  const fst=document.getElementById('fb-fst')?.value||'';
  const lvl=ROLE_LEVEL[S.user.role]||1;
  const fb=S.feedback||[];
  const open=fb.filter(f=>f.status==='open').length;
  const mine=fb.filter(f=>f.from_user===S.user.username).length;
  const anon=fb.filter(f=>f.is_anonymous).length;
  document.getElementById('fb-stats').innerHTML=`
    <div class="irow"><span class="ik">Total Feedback</span><span class="iv" style="font-family:var(--bb);font-size:22px;color:#fff">${fb.length}</span></div>
    <div class="irow"><span class="ik">Open / Unresolved</span><span class="iv"><span class="bdg bwarn">${open}</span></span></div>
    <div class="irow"><span class="ik">Submitted by Me</span><span class="iv">${mine}</span></div>
    <div class="irow"><span class="ik">Anonymous</span><span class="iv">${anon}</span></div>`;
  const empRow=document.getElementById('fb-emp-row');
  if(empRow)empRow.style.display=lvl>=2?'':'none';
  let rows=fb.filter(f=>{
    if(fcat&&f.category!==fcat)return false;
    if(fst&&f.status!==fst)return false;
    if(lvl<2&&f.from_user!==S.user.username)return false;
    return true;
  });
  const catcols={performance:'bblue',behavior:'bred',work_ethics:'bred',attendance:'bwarn',teamwork:'bgreen',complaint:'bred',general:'bgray'};
  const stcols={open:'bwarn',reviewed:'bblue',resolved:'bgreen'};
  const el=document.getElementById('fb-list');
  if(!rows.length){el.innerHTML='<div class="card" style="color:var(--txm);font-size:13px">No feedback found.</div>';return;}
  el.innerHTML=rows.map(f=>{
    const e=f.emp_id?S.employees[f.emp_id]:null;
    const stars=f.rating?'* '.repeat(parseInt(f.rating)).trim():'';
    const repCount=(f.responses||[]).length;
    const unread=!(f.read_by||[]).includes(S.user.username);
    return `<div class="fb-card ${unread?'unread':''}" onclick="openFbDetail('${f.id}')">
      <div class="fb-head">
        <span class="bdg ${catcols[f.category]||'bgray'}">${esc(f.category)}</span>
        <span class="bdg ${stcols[f.status]||'bgray'}">${esc(f.status)}</span>
        ${f.rating?`<span style="color:var(--gold);font-size:12px">${stars} (${f.rating}/5)</span>`:''}
        <span style="flex:1"></span>
        <span style="font-size:10px;color:var(--txm);font-family:var(--mo)">${esc((f.ts||'').slice(0,10))}</span>
      </div>
      <div class="fb-sub">${esc(f.subject||'')}</div>
      <div class="fb-meta" style="margin-top:3px">${e?`About: <strong>${esc(e.full_name||f.emp_id)}</strong> &middot; `:''}From: ${f.is_anonymous?'<span style="color:var(--txm)">Anonymous</span>':esc(f.from_user||'')}${repCount?` &middot; <span style="color:var(--gold)">${repCount} response${repCount>1?'s':''}</span>`:''}</div>
      <div style="font-size:12px;color:var(--txm);margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(f.content||'')}</div>
    </div>`;
  }).join('');
}
function openFbDetail(id){
  const f=S.feedback.find(x=>x.id===id);if(!f)return;
  const lvl=ROLE_LEVEL[S.user.role]||1;
  const e=f.emp_id?S.employees[f.emp_id]:null;
  const catcols={performance:'bblue',behavior:'bred',work_ethics:'bred',attendance:'bwarn',teamwork:'bgreen',complaint:'bred',general:'bgray'};
  const stcols={open:'bwarn',reviewed:'bblue',resolved:'bgreen'};
  document.getElementById('m-fb-t').textContent=f.subject||'Feedback Detail';
  document.getElementById('m-fb-body').innerHTML=`
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
      <span class="bdg ${catcols[f.category]||'bgray'}">${esc(f.category)}</span>
      <span class="bdg ${stcols[f.status]||'bgray'}">${esc(f.status)}</span>
      ${f.rating?`<span style="color:var(--gold);font-size:13px">Rating: ${f.rating}/5</span>`:''}
    </div>
    ${e?`<div class="irow"><span class="ik">About</span><span class="iv"><strong>${esc(e.full_name||'')}</strong> &middot; <span style="font-family:var(--mo);font-size:11px">${esc(f.emp_id)}</span></span></div>`:''}
    <div class="irow"><span class="ik">Submitted By</span><span class="iv">${f.is_anonymous?'<span style="color:var(--txm)">Anonymous</span>':esc(f.from_user||'—')}</span></div>
    <div class="irow"><span class="ik">Date</span><span class="iv" style="font-family:var(--mo);font-size:12px">${esc(f.ts||'')}</span></div>
    <div style="margin-top:10px;padding:12px;background:var(--bg);border-radius:7px;font-size:13px;line-height:1.6">${esc(f.content||'')}</div>
    ${(f.responses||[]).length?`<div style="margin-top:12px"><div style="font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--txm);margin-bottom:8px">Responses</div>${(f.responses||[]).map(r=>`<div class="reply-bub"><div class="reply-who">${esc(r.user)} <span style="font-weight:400;color:var(--txm)">${esc(r.ts)}</span></div><div style="font-size:13px">${esc(r.content)}</div></div>`).join('')}</div>`:''}`;
  api('POST','/api/feedback/read',{id});
  if(!f.read_by)f.read_by=[];if(!f.read_by.includes(S.user.username))f.read_by.push(S.user.username);
  refreshBadges();rFeedback();
  document.getElementById('fb-reply-row').style.display=lvl>=2?'':'none';
  document.getElementById('m-fb-body').dataset.fbid=id;
  openModal('m-fb');
}
async function sendFbReply(){
  const id=document.getElementById('m-fb-body').dataset.fbid;
  const content=v('fb-reply');const status=document.getElementById('fb-res-st').value;
  if(!content){toast('Write a response first.','error');return;}
  const r=await api('PUT',`/api/feedback/${id}`,{response:content,status});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.feedback=d.feedback;set('fb-reply','');cm('m-fb');rFeedback();toast('Response sent.','success');
}

// ── UTILS
const api=(method,url,body)=>fetch(url,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});
function openModal(id){document.getElementById(id).classList.add('open');}
function cm(id){document.getElementById(id).classList.remove('open');}
function v(id){const el=document.getElementById(id);return el?el.value.trim():'';}
function set(id,val){const el=document.getElementById(id);if(el)el.value=val||'';}
function esc(s){return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
let _toast;
function toast(msg,type='success'){
  const el=document.getElementById('toast');
  el.textContent=msg;el.className='show '+(type==='success'?'success':type==='error'?'error':type==='warn'?'warn':'');
  clearTimeout(_toast);_toast=setTimeout(()=>el.className='',3400);
}
document.querySelectorAll('.mo2').forEach(m=>m.addEventListener('click',function(e){if(e.target===this)this.classList.remove('open');}));
</script>
</body></html>"""

# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/me")
@login_required
def me():
    data = load_data()
    u = data["system_users"].get(session["username"], {})
    return jsonify({"username": session["username"], "full_name": u.get("full_name",""),
                    "role": session["role"], "emp_id": u.get("emp_id"),
                    "photo": u.get("photo")})

@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json() or {}
    uname = body.get("username","").strip()
    pw    = body.get("password","")
    data  = load_data()
    u = data["system_users"].get(uname)
    if not u or not verify_pw(pw, u.get("password_hash","")):
        return jsonify({"error": "Invalid credentials."}), 401
    session["username"] = uname
    session["role"]     = u.get("role","staff")
    audit(data, uname, "Login", uname)
    save_data(data)
    return jsonify({"username": uname, "full_name": u.get("full_name",""),
                    "role": u.get("role","staff"), "emp_id": u.get("emp_id"),
                    "photo": u.get("photo")})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/data")
@login_required
def get_data():
    data = load_data()
    lvl  = ROLE_LEVEL.get(session["role"],1)
    emps = data["employees"]
    if lvl < 3:  # staff/manager: strip salary
        emps = {k: {f: v for f,v in e.items() if f not in ("salary","salary_currency")} for k,e in emps.items()}
    if lvl < 2:  # staff: own record only
        emp_id = data["system_users"].get(session["username"],{}).get("emp_id")
        emps = {k: v for k,v in emps.items() if k == emp_id}
    result = {"employees": emps, "departments": data["departments"], "feedback": data.get("feedback",[]),
              "audit_log": data.get("audit_log",[])[:100] if lvl>=3 else [],
              "notifications": data.get("notifications",[]),
              "leave_requests": data.get("leave_requests",[]),
              "meta": data.get("meta",{})}
    if lvl >= 4:
        result["system_users"] = {u: {k: v for k,v in d.items() if k!="password_hash"}
                                   for u,d in data["system_users"].items()}
    return jsonify(result)

# ─── EMPLOYEES
@app.route("/api/employees", methods=["POST"])
@role_required("hr")
def add_employee():
    data = load_data()
    body = request.get_json() or {}
    if not body.get("full_name","").strip():
        return jsonify({"error": "Full name is required."}), 400
    eid = gen_emp_id(data)
    emp = {
        "full_name":       body.get("full_name","").strip(),
        "email":           body.get("email","").strip(),
        "department":      body.get("department",""),
        "occupation":      body.get("occupation","").strip(),
        "role":            body.get("role","").strip(),
        "purpose":         body.get("purpose","").strip(),
        "age":             body.get("age",""),
        "location":        body.get("location","").strip(),
        "employment_type": body.get("employment_type","permanent"),
        "status":          body.get("status","active"),
        "contract_end":    body.get("contract_end",""),
        "salary":          body.get("salary",""),
        "salary_currency": body.get("salary_currency","USD"),
        "photo":           None,
        "promotion_requests": [],
        "date_added":      datetime.now().strftime("%Y-%m-%d"),
    }
    data["employees"][eid] = emp
    audit(data, session["username"], "Added employee", eid, emp["full_name"])
    notify(data, "success", f"New employee added: {emp['full_name']} ({eid})")
    save_data(data)
    return jsonify({"id": eid, "employee": emp}), 201

@app.route("/api/employees/<eid>", methods=["PUT"])
@role_required("hr")
def update_employee(eid):
    data = load_data()
    if eid not in data["employees"]:
        return jsonify({"error": "Employee not found."}), 404
    body = request.get_json() or {}
    fields = ["full_name","email","department","occupation","role","purpose","age","location",
              "employment_type","status","contract_end","salary","salary_currency"]
    for f in fields:
        if f in body:
            data["employees"][eid][f] = body[f]
    audit(data, session["username"], "Updated employee", eid)
    save_data(data)
    return jsonify({"id": eid, "employee": data["employees"][eid]})

@app.route("/api/employees/<eid>", methods=["DELETE"])
@role_required("hr")
def delete_employee(eid):
    data = load_data()
    if eid not in data["employees"]:
        return jsonify({"error": "Employee not found."}), 404
    name = data["employees"][eid].get("full_name","")
    del data["employees"][eid]
    audit(data, session["username"], "Deleted employee", eid, name)
    save_data(data)
    return jsonify({"ok": True})

# ─── DEPARTMENTS
@app.route("/api/departments", methods=["POST"])
@role_required("hr")
def add_department():
    data = load_data()
    body = request.get_json() or {}
    name = body.get("name","").strip()
    if not name: return jsonify({"error": "Name required."}), 400
    if name in data["departments"]: return jsonify({"error": "Department exists."}), 409
    dept = {"description": body.get("description",""), "head_id": body.get("head_id")}
    data["departments"][name] = dept
    audit(data, session["username"], "Added department", name)
    save_data(data)
    return jsonify({"name": name, "department": dept}), 201

@app.route("/api/departments/<name>", methods=["PUT"])
@role_required("hr")
def update_department(name):
    data = load_data()
    if name not in data["departments"]: return jsonify({"error": "Not found."}), 404
    body = request.get_json() or {}
    new_name = body.get("name", name).strip()
    dept = {"description": body.get("description",""), "head_id": body.get("head_id")}
    if new_name != name:
        del data["departments"][name]
    data["departments"][new_name] = dept
    audit(data, session["username"], "Updated department", new_name)
    save_data(data)
    return jsonify({"name": new_name, "department": dept})

@app.route("/api/departments/<name>", methods=["DELETE"])
@role_required("admin")
def delete_department(name):
    data = load_data()
    if name not in data["departments"]: return jsonify({"error": "Not found."}), 404
    del data["departments"][name]
    audit(data, session["username"], "Deleted department", name)
    save_data(data)
    return jsonify({"ok": True})

# ─── PROMOTIONS
@app.route("/api/promotions", methods=["POST"])
@login_required
def submit_promo():
    data = load_data()
    body = request.get_json() or {}
    eid  = body.get("emp_id","").strip()
    role = body.get("requested_role","").strip()
    if eid not in data["employees"]: return jsonify({"error": "Employee not found."}), 404
    if not role: return jsonify({"error": "Requested role required."}), 400
    req = {"requested_role": role, "current_role": data["employees"][eid].get("role",""),
           "status": "pending", "date": datetime.now().strftime("%Y-%m-%d"),
           "resolved_date": "", "resolved_by": ""}
    data["employees"][eid].setdefault("promotion_requests",[]).append(req)
    audit(data, session["username"], "Submitted promotion request", eid, f"→ {role}")
    notify(data, "info", f"Promotion request: {data['employees'][eid].get('full_name',eid)} → {role}")
    save_data(data)
    return jsonify({"employee": data["employees"][eid]}), 201

@app.route("/api/promotions/<eid>/<int:idx>", methods=["PUT"])
@role_required("hr")
def resolve_promo(eid, idx):
    data = load_data()
    if eid not in data["employees"]: return jsonify({"error": "Employee not found."}), 404
    reqs = data["employees"][eid].get("promotion_requests",[])
    if idx >= len(reqs): return jsonify({"error": "Request not found."}), 404
    req = reqs[idx]
    if req["status"] != "pending": return jsonify({"error": "Already resolved."}), 409
    res = (request.get_json() or {}).get("resolution","")
    if res not in ("approved","denied"): return jsonify({"error": "Invalid resolution."}), 400
    req["status"]       = res
    req["resolved_date"]= datetime.now().strftime("%Y-%m-%d")
    req["resolved_by"]  = session["username"]
    if res == "approved":
        data["employees"][eid]["role"] = req["requested_role"]
    audit(data, session["username"], f"Promotion {res}", eid, req["requested_role"])
    save_data(data)
    return jsonify({"employee": data["employees"][eid]})

# ─── LEAVE
@app.route("/api/leave", methods=["POST"])
@login_required
def submit_leave():
    data = load_data()
    body = request.get_json() or {}
    eid  = body.get("emp_id","").strip()
    lvl  = ROLE_LEVEL.get(session["role"],1)
    if lvl < 3:
        my_eid = data["system_users"].get(session["username"],{}).get("emp_id")
        if eid != my_eid: return jsonify({"error": "Can only submit for yourself."}), 403
    if eid not in data["employees"]: return jsonify({"error": "Employee not found."}), 404
    req = {"emp_id": eid, "leave_type": body.get("leave_type","annual"),
           "start_date": body.get("start_date",""), "end_date": body.get("end_date",""),
           "notes": body.get("notes",""), "status": "pending",
           "submitted_by": session["username"],
           "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    data.setdefault("leave_requests",[]).append(req)
    audit(data, session["username"], "Leave request submitted", eid, req["leave_type"])
    notify(data, "info", f"Leave request: {data['employees'][eid].get('full_name',eid)} — {req['leave_type']}")
    save_data(data)
    return jsonify({"leave_requests": data["leave_requests"]})

@app.route("/api/leave/<int:idx>", methods=["PUT"])
@role_required("hr")
def resolve_leave(idx):
    data = load_data()
    reqs = data.get("leave_requests",[])
    if idx >= len(reqs): return jsonify({"error": "Not found."}), 404
    req = reqs[idx]
    if req["status"] != "pending": return jsonify({"error": "Already resolved."}), 409
    res = (request.get_json() or {}).get("resolution","")
    if res not in ("approved","denied"): return jsonify({"error": "Invalid."}), 400
    req["status"] = res
    req["resolved_by"] = session["username"]
    req["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    if res == "approved" and req["emp_id"] in data["employees"]:
        data["employees"][req["emp_id"]]["status"] = "on_leave"
    audit(data, session["username"], f"Leave {res}", req["emp_id"], req["leave_type"])
    save_data(data)
    return jsonify({"leave_requests": data["leave_requests"]})

# ─── PROFILE / PASSWORD
@app.route("/api/profile", methods=["PUT"])
@login_required
def update_profile():
    data = load_data()
    body = request.get_json() or {}
    if "photo" in body:
        data["system_users"][session["username"]]["photo"] = body["photo"]
    audit(data, session["username"], "Updated profile", session["username"])
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/change-password", methods=["POST"])
@login_required
def change_password():
    data = load_data()
    body = request.get_json() or {}
    u = data["system_users"].get(session["username"])
    if not verify_pw(body.get("current",""), u.get("password_hash","")):
        return jsonify({"error": "Current password incorrect."}), 400
    new_pw = body.get("new","")
    if len(new_pw) < 6: return jsonify({"error": "Password too short (min 6)."}), 400
    u["password_hash"] = hash_pw(new_pw)
    audit(data, session["username"], "Changed password", session["username"])
    save_data(data)
    return jsonify({"ok": True})

# ─── SYSTEM USERS
@app.route("/api/sysusers", methods=["POST"])
@role_required("admin")
def add_sysuser():
    data = load_data()
    body = request.get_json() or {}
    uname = body.get("username","").strip()
    if not uname: return jsonify({"error": "Username required."}), 400
    if uname in data["system_users"]: return jsonify({"error": "Username taken."}), 409
    pw = body.get("password","")
    if len(pw) < 6: return jsonify({"error": "Password too short."}), 400
    data["system_users"][uname] = {
        "password_hash": hash_pw(pw), "role": body.get("role","staff"),
        "full_name": body.get("full_name","").strip(),
        "emp_id": body.get("emp_id") or None,
        "photo": None, "created": datetime.now().strftime("%Y-%m-%d")
    }
    audit(data, session["username"], "Added system user", uname)
    save_data(data)
    su_clean = {u: {k:v for k,v in d.items() if k!="password_hash"} for u,d in data["system_users"].items()}
    return jsonify({"system_users": su_clean}), 201

@app.route("/api/sysusers/<uname>", methods=["PUT"])
@role_required("admin")
def update_sysuser(uname):
    data = load_data()
    if uname not in data["system_users"]: return jsonify({"error": "Not found."}), 404
    body = request.get_json() or {}
    u = data["system_users"][uname]
    new_un = body.get("username", uname).strip()
    u["full_name"] = body.get("full_name", u.get("full_name",""))
    u["role"]      = body.get("role", u.get("role","staff"))
    u["emp_id"]    = body.get("emp_id") or u.get("emp_id")
    if body.get("password"):
        if len(body["password"]) < 6: return jsonify({"error": "Password too short."}), 400
        u["password_hash"] = hash_pw(body["password"])
    if new_un != uname:
        data["system_users"][new_un] = u
        del data["system_users"][uname]
    else:
        data["system_users"][uname] = u
    audit(data, session["username"], "Updated system user", new_un)
    save_data(data)
    su_clean = {u2: {k:v for k,v in d.items() if k!="password_hash"} for u2,d in data["system_users"].items()}
    return jsonify({"system_users": su_clean})

@app.route("/api/sysusers/<uname>", methods=["DELETE"])
@role_required("admin")
def delete_sysuser(uname):
    data = load_data()
    if uname not in data["system_users"]: return jsonify({"error": "Not found."}), 404
    if uname == session["username"]: return jsonify({"error": "Cannot delete yourself."}), 400
    del data["system_users"][uname]
    audit(data, session["username"], "Deleted system user", uname)
    save_data(data)
    su_clean = {u: {k:v for k,v in d.items() if k!="password_hash"} for u,d in data["system_users"].items()}
    return jsonify({"system_users": su_clean})

# ─── NOTIFICATIONS
@app.route("/api/notifications/read", methods=["POST"])
@login_required
def mark_notif_read():
    data = load_data()
    nid = (request.get_json() or {}).get("id")
    for n in data.get("notifications",[]):
        if n.get("id") == nid:
            n.setdefault("read_by",[])
            if session["username"] not in n["read_by"]:
                n["read_by"].append(session["username"])
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    data = load_data()
    for n in data.get("notifications",[]):
        n.setdefault("read_by",[])
        if session["username"] not in n["read_by"]:
            n["read_by"].append(session["username"])
    save_data(data)
    return jsonify({"ok": True})

# ─── EXPORT
@app.route("/api/export/employees-csv")
@login_required
def export_emp_csv():
    data = load_data()
    return send_file(io.BytesIO(export_csv_bytes(data["employees"])),
                     mimetype="text/csv", as_attachment=True, download_name="archer_employees.csv")

@app.route("/api/export/employees-excel")
@login_required
def export_emp_excel():
    data  = load_data()
    b     = export_excel_bytes(data["employees"])
    if not b: return jsonify({"error": "openpyxl not installed."}), 500
    return send_file(io.BytesIO(b),
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name="archer_employees.xlsx")

@app.route("/api/export/payroll-csv")
@role_required("hr")
def export_pay_csv():
    data  = load_data()
    emps  = {k: v for k,v in data["employees"].items() if v.get("salary")}
    return send_file(io.BytesIO(export_csv_bytes(emps)),
                     mimetype="text/csv", as_attachment=True, download_name="archer_payroll.csv")

@app.route("/api/export/payroll-excel")
@role_required("hr")
def export_pay_excel():
    data  = load_data()
    emps  = {k: v for k,v in data["employees"].items() if v.get("salary")}
    b     = export_excel_bytes(emps)
    if not b: return jsonify({"error": "openpyxl not installed."}), 500
    return send_file(io.BytesIO(b),
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name="archer_payroll.xlsx")

# ─── IMPORT
@app.route("/api/import", methods=["POST"])
@role_required("hr")
def import_emps():
    if "file" not in request.files: return jsonify({"error": "No file uploaded."}), 400
    f    = request.files["file"]
    name = f.filename.lower()
    data = load_data()
    count = 0
    try:
        if name.endswith(".json"):
            raw = json.load(f)
            if isinstance(raw, dict) and "employees" in raw:
                emp_data = raw["employees"]
                if isinstance(emp_data, list):
                    for emp in emp_data:
                        emp = dict(emp)
                        eid = emp.pop("id", None) or gen_emp_id(data)
                        emp.setdefault("promotion_requests", [])
                        data["employees"][eid] = emp; count += 1
                else:
                    for eid, emp in emp_data.items():
                        data["employees"][eid] = emp; count += 1
            elif isinstance(raw, dict):
                for eid, emp in raw.items():
                    data["employees"][eid] = emp; count += 1
            elif isinstance(raw, list):
                for emp in raw:
                    eid = emp.pop("id", None) or gen_emp_id(data)
                    emp.setdefault("promotion_requests", [])
                    data["employees"][eid] = emp; count += 1
        elif name.endswith(".csv"):
            text   = f.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                eid = row.pop("id", None) or gen_emp_id(data)
                row.setdefault("promotion_requests", [])
                data["employees"][eid] = dict(row); count += 1
        else:
            return jsonify({"error": "Only .json and .csv supported."}), 400
        audit(data, session["username"], "Imported employees", f"count={count}")
        save_data(data)
        return jsonify({"count": count, "employees": data["employees"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── FEEDBACK
import secrets as _sec
@app.route("/api/feedback", methods=["POST"])
@login_required
def add_feedback():
    data  = load_data()
    body  = request.get_json() or {}
    sub   = body.get("subject","").strip()
    cont  = body.get("content","").strip()
    if not sub or not cont:
        return jsonify({"error": "Subject and content required."}), 400
    lvl   = ROLE_LEVEL.get(session["role"],1)
    emp_id = body.get("emp_id") or None
    if lvl < 2 and emp_id:
        my_eid = data["system_users"].get(session["username"],{}).get("emp_id")
        if emp_id != my_eid:
            return jsonify({"error": "Staff can only submit general feedback."}), 403
    fb = {
        "id":           _sec.token_hex(8),
        "ts":           datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "emp_id":       emp_id,
        "category":     body.get("category","general"),
        "subject":      sub,
        "content":      cont,
        "rating":       body.get("rating") or None,
        "is_anonymous": bool(body.get("is_anonymous")),
        "from_user":    None if body.get("is_anonymous") else session["username"],
        "status":       "open",
        "responses":    [],
        "read_by":      [session["username"]],
    }
    data.setdefault("feedback",[]).insert(0, fb)
    audit(data, session["username"], "Submitted feedback", fb["id"], sub)
    if lvl < 2:
        notify(data, "info", f"New feedback: {sub}", roles=["admin","hr","manager"])
    save_data(data)
    return jsonify({"feedback": data["feedback"]}), 201

@app.route("/api/feedback/<fid>", methods=["PUT"])
@login_required
def update_feedback(fid):
    data = load_data()
    if ROLE_LEVEL.get(session["role"],1) < 2:
        return jsonify({"error": "Manager or HR access required."}), 403
    fb = next((f for f in data.get("feedback",[]) if f.get("id")==fid), None)
    if not fb: return jsonify({"error": "Not found."}), 404
    body = request.get_json() or {}
    if body.get("response"):
        fb.setdefault("responses",[]).append({
            "user":    session["username"],
            "content": body["response"],
            "ts":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    if body.get("status") in ("open","reviewed","resolved"):
        fb["status"] = body["status"]
    audit(data, session["username"], "Responded to feedback", fid)
    save_data(data)
    return jsonify({"feedback": data["feedback"]})

@app.route("/api/feedback/read", methods=["POST"])
@login_required
def mark_fb_read():
    data = load_data()
    fid  = (request.get_json() or {}).get("id")
    for f in data.get("feedback",[]):
        if f.get("id") == fid:
            f.setdefault("read_by",[])
            if session["username"] not in f["read_by"]:
                f["read_by"].append(session["username"])
    save_data(data)
    return jsonify({"ok": True})

# ─── RUN
if __name__ == "__main__":
    print("\n  ╔═══════════════════════════════════════════════╗")
    print("  ║     ARCHER ENTERPRISE  —  Web Edition v2.0   ║")
    print("  ║     Your Corporate Management & Service Agency║")
    print("  ╠═══════════════════════════════════════════════╣")
    print("  ║   http://localhost:5000                       ║")
    print("  ║   admin / admin123  |  hr_manager / hr123     ║")
    print("  ╚═══════════════════════════════════════════════╝\n")
    app.run(debug=True, port=5000)
