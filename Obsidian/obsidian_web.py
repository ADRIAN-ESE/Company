"""
OBSIDIAN CORPORATION — Web Edition v3.0
Flask single-file application

pip install flask openpyxl
python obsidian_web.py  →  http://localhost:5000

Default credentials:
  admin / admin123  |  hr_manager / hr123  |  manager1 / mgr123  |  staff1 / staff123
"""
import csv, io, json, secrets
from datetime import datetime, date
from functools import wraps
from flask import Flask, jsonify, render_template_string, request, send_file, session

from obsidian_shared import (load_data, save_data, gen_emp_id, audit, notify,
                            hash_pw, verify_pw, export_csv_bytes, export_excel_bytes,
                            export_audit_csv_bytes,
                            ROLE_LEVEL, ROLE_LABEL, ROLE_DEFINITIONS, DEPT_DEFINITIONS,
                            get_dept_definition, EMP_FIELDS)

app = Flask(__name__)
# Fixed secret key — sessions survive server restarts.
# Change this to a long random string in production.
app.secret_key = "obsidian-corp-v3-s3cr3t-k3y-change-in-production-2026"
# Unique cookie name prevents any collision with old archer_web.py sessions in the browser
app.config["SESSION_COOKIE_NAME"] = "obsidian_session"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

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
<title>OBSIDIAN CORPORATION</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#07091a;--sur:#0c0f22;--card:#111428;--card2:#161a30;--bdr:#1e2240;
  --gold:#c9a84c;--gl:#e8c56a;--gd:#9a7a30;--gg:rgba(201,168,76,.14);
  --ok:#3dba7a;--warn:#e09a30;--err:#e05252;--info:#4f8ef7;--purple:#7c5df9;
  --tx:#d4d8f0;--txm:#5a6080;--txd:#2a3050;
  --bb:'Bebas Neue',sans-serif;--dm:'DM Sans',sans-serif;--mo:'DM Mono',monospace;
  --r:10px;--sw:244px;--hh:60px
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--tx);font-family:var(--dm);font-size:14px}
::-webkit-scrollbar{width:5px;height:5px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px}

/* LOGIN */
#ls{position:fixed;inset:0;z-index:1000;background:var(--bg);display:flex;align-items:center;justify-content:center;overflow:hidden}
#ls.gone{display:none!important}
.lgrid{position:absolute;inset:0;background-image:linear-gradient(rgba(201,168,76,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(201,168,76,.03) 1px,transparent 1px);background-size:55px 55px;animation:gs 25s linear infinite}
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

/* APP LAYOUT */
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

/* SIDEBAR */
#sb{width:var(--sw);flex-shrink:0;background:var(--sur);border-right:1px solid var(--bdr);display:flex;flex-direction:column;overflow-y:auto}
.ssl{font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--txd);padding:16px 20px 5px}
.nb{display:flex;align-items:center;gap:9px;padding:9px 20px;background:transparent;border:none;color:var(--txm);font-family:var(--dm);font-size:13px;width:100%;text-align:left;cursor:pointer;transition:all .14s;border-left:3px solid transparent}
.nb:hover{background:rgba(201,168,76,.04);color:var(--tx)}
.nb.act{background:rgba(201,168,76,.08);color:var(--gold);border-left-color:var(--gold)}
.ni{font-size:14px;width:18px;text-align:center;flex-shrink:0}
.nbdge{margin-left:auto;background:var(--err);color:#fff;font-size:9px;font-weight:700;padding:1px 6px;border-radius:10px;display:none}
.nbdge.v{display:inline}

/* MAIN */
#main{flex:1;overflow-y:auto;padding:26px 30px}
.pg{display:none}.pg.act{display:block}
.pghdr{margin-bottom:20px;display:flex;align-items:flex-end;gap:14px}
.pght{flex:1}
.pgt{font-family:var(--bb);font-size:34px;letter-spacing:.04em;color:#fff;line-height:1}
.pgs{font-size:12px;color:var(--txm);margin-top:3px}

/* CARDS */
.card{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:20px;margin-bottom:16px}
.ct{font-family:var(--bb);font-size:16px;letter-spacing:.04em;color:#fff;margin-bottom:12px}

/* STATS */
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:11px;margin-bottom:20px}
.sc{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:16px;position:relative;overflow:hidden}
.sc::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--gold)}
.sc.bl::before{background:var(--info)}.sc.gn::before{background:var(--ok)}.sc.rd::before{background:var(--err)}.sc.wn::before{background:var(--warn)}.sc.pu::before{background:var(--purple)}
.sv{font-family:var(--bb);font-size:38px;color:#fff;line-height:1}
.slb{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--txm);margin-top:3px}

/* ALERT STRIP */
.alert-strip{border-radius:8px;padding:10px 14px;font-size:12px;margin-bottom:10px;display:flex;align-items:center;gap:8px}
.alert-strip.warn{background:rgba(224,154,48,.1);border:1px solid rgba(224,154,48,.3);color:var(--warn)}
.alert-strip.err{background:rgba(224,82,82,.1);border:1px solid rgba(224,82,82,.3);color:var(--err)}
.alert-strip.info{background:rgba(79,142,247,.1);border:1px solid rgba(79,142,247,.3);color:var(--info)}

/* CHARTS */
.cr{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.cc{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:16px}
.cc canvas{max-height:190px}

/* TOOLBAR */
.tb{display:flex;align-items:center;gap:7px;margin-bottom:10px;flex-wrap:wrap}
.si2{flex:1;min-width:170px;max-width:340px;background:var(--card);border:1px solid var(--bdr);color:var(--tx);padding:7px 11px;border-radius:7px;font-family:var(--dm);font-size:13px;outline:none;transition:border-color .15s}
.si2:focus{border-color:var(--gold)}.si2::placeholder{color:var(--txd)}
.flt{background:var(--card);border:1px solid var(--bdr);color:var(--tx);padding:7px 10px;border-radius:7px;font-family:var(--dm);font-size:13px;outline:none;cursor:pointer}
.flt option{background:var(--card)}
.sp{flex:1}

/* BUTTONS */
.btn{display:inline-flex;align-items:center;gap:5px;padding:7px 14px;border-radius:7px;border:none;font-family:var(--dm);font-size:13px;font-weight:600;cursor:pointer;transition:all .14s;white-space:nowrap}
.bg{background:var(--gold);color:var(--bg)}.bg:hover{background:var(--gl);box-shadow:0 0 12px rgba(201,168,76,.28)}
.bk{background:var(--ok);color:#fff}.bk:hover{background:#2ea66b}
.br{background:var(--err);color:#fff}.br:hover{background:#c94040}
.bh{background:transparent;border:1px solid var(--bdr);color:var(--txm)}.bh:hover{border-color:var(--gold);color:var(--gold)}
.binfo{background:transparent;border:1px solid var(--info);color:var(--info)}.binfo:hover{background:rgba(79,142,247,.12)}
.sm{padding:5px 10px;font-size:12px}

/* TABLE */
.tw{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);overflow:auto}
table{width:100%;border-collapse:collapse}
thead th{background:var(--sur);color:var(--txm);font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;padding:10px 12px;text-align:left;white-space:nowrap;border-bottom:1px solid var(--bdr);position:sticky;top:0;z-index:1}
tbody tr{border-bottom:1px solid rgba(30,34,64,.45);transition:background .1s;cursor:pointer}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:rgba(201,168,76,.04)}
tbody tr.sel{background:rgba(201,168,76,.1)!important}
td{padding:10px 12px;font-size:13px;white-space:nowrap}
.er td{text-align:center;padding:36px;color:var(--txm);font-size:12px}

/* BADGES */
.bdg{display:inline-block;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;letter-spacing:.03em;text-transform:uppercase}
.bgold{background:var(--gg);color:var(--gold);border:1px solid rgba(201,168,76,.2)}
.bgreen{background:rgba(61,186,122,.12);color:var(--ok)}
.bred{background:rgba(224,82,82,.12);color:var(--err)}
.bwarn{background:rgba(224,154,48,.12);color:var(--warn)}
.bblue{background:rgba(79,142,247,.12);color:var(--info)}
.bgray{background:rgba(90,96,128,.1);color:var(--txm)}
.bpurple{background:rgba(124,93,249,.12);color:var(--purple)}

/* FORM */
.fg{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.fgr{display:flex;flex-direction:column;gap:4px}
.fgr.full{grid-column:1/-1}
.flb{font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--txm)}
.fi,.fsel,.fta{background:var(--bg);border:1px solid var(--bdr);color:var(--tx);padding:8px 11px;border-radius:7px;font-family:var(--dm);font-size:13px;outline:none;transition:border-color .15s;width:100%}
.fi:focus,.fsel:focus,.fta:focus{border-color:var(--gold)}
.fi::placeholder{color:var(--txd)}
.fta{resize:vertical;min-height:64px}
.fsel option{background:var(--card)}
.fhint{font-size:10px;color:var(--txm);margin-top:2px}

/* SKILLS TAGS */
.tags-wrap{display:flex;flex-wrap:wrap;gap:5px;padding:6px 8px;background:var(--bg);border:1px solid var(--bdr);border-radius:7px;min-height:38px;cursor:text;transition:border-color .15s}
.tags-wrap:focus-within{border-color:var(--gold)}
.tag-item{display:inline-flex;align-items:center;gap:4px;background:var(--gg);color:var(--gold);border:1px solid rgba(201,168,76,.25);border-radius:20px;padding:2px 8px;font-size:11px;font-weight:600}
.tag-rm{background:none;border:none;color:var(--gd);cursor:pointer;font-size:11px;padding:0;line-height:1}
.tag-rm:hover{color:var(--err)}
.tag-input{border:none;background:transparent;color:var(--tx);font-family:var(--dm);font-size:13px;outline:none;min-width:80px;flex:1}

/* MODALS */
.mo2{position:fixed;inset:0;background:rgba(0,0,0,.78);display:flex;align-items:center;justify-content:center;z-index:200;backdrop-filter:blur(6px);opacity:0;pointer-events:none;transition:opacity .2s}
.mo2.open{opacity:1;pointer-events:all}
.mdl{background:var(--card);border:1px solid var(--bdr);border-top:2px solid var(--gold);border-radius:14px;padding:28px;width:660px;max-width:96vw;max-height:90vh;overflow-y:auto;transform:translateY(16px);transition:transform .2s}
.mo2.open .mdl{transform:translateY(0)}
.mdlt{font-family:var(--bb);font-size:21px;letter-spacing:.04em;color:#fff;margin-bottom:20px}
.mact{display:flex;gap:9px;justify-content:flex-end;margin-top:18px}
.mdl-wide{width:760px}

/* NOTIF PANEL */
#np{position:fixed;top:var(--hh);right:0;width:340px;height:calc(100vh - var(--hh));background:var(--sur);border-left:1px solid var(--bdr);z-index:100;transform:translateX(100%);transition:transform .28s;display:flex;flex-direction:column}
#np.open{transform:translateX(0)}
.nph{padding:16px 20px;border-bottom:1px solid var(--bdr);display:flex;align-items:center;justify-content:space-between}
.npht{font-family:var(--bb);font-size:17px;letter-spacing:.04em;color:#fff}
.npb{flex:1;overflow-y:auto}
.nit{padding:12px 20px;border-bottom:1px solid rgba(30,34,64,.4);cursor:pointer;transition:background .1s;border-left:3px solid transparent;display:flex;gap:10px;align-items:flex-start}
.nit.unr{border-left-color:var(--gold)}
.nit:hover{background:rgba(201,168,76,.04)}
.nico{font-size:16px;flex-shrink:0;margin-top:1px}
.nim{font-size:13px;color:var(--tx);line-height:1.4}
.nts{font-size:11px;color:var(--txm);margin-top:3px;font-family:var(--mo)}
.nem{text-align:center;padding:36px;color:var(--txm);font-size:13px}

/* DEPT GRID */
.dg{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.dc{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:18px;transition:all .18s;position:relative;overflow:hidden;cursor:pointer}
.dc:hover{border-color:var(--gold);background:var(--card2);transform:translateY(-1px);box-shadow:0 8px 24px rgba(0,0,0,.3)}
.dc-accent{position:absolute;top:0;left:0;right:0;height:3px}
.dcn{font-family:var(--bb);font-size:20px;letter-spacing:.04em;color:#fff;margin-bottom:4px;display:flex;align-items:center;gap:8px}
.dci{font-size:20px}
.dcd{font-size:12px;color:var(--txm);line-height:1.5;margin-bottom:10px}
.dcc{position:absolute;top:14px;right:16px;font-family:var(--bb);font-size:28px;color:var(--gold);opacity:.5}
.dch{font-size:11px;color:var(--gd);margin-bottom:8px}
.dc-kpis{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.dc-kpi{font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:rgba(201,168,76,.08);color:var(--gd);border:1px solid rgba(201,168,76,.15);padding:2px 7px;border-radius:20px}
.dca{display:flex;gap:7px;margin-top:12px;padding-top:10px;border-top:1px solid var(--bdr)}

/* DEPT DETAIL MODAL */
.resp-list{list-style:none;padding:0}
.resp-list li{padding:5px 0;border-bottom:1px solid rgba(30,34,64,.4);font-size:13px;color:var(--tx);display:flex;gap:8px}
.resp-list li::before{content:'→';color:var(--gold);font-family:var(--mo);flex-shrink:0}
.resp-list li:last-child{border-bottom:none}

/* ROLE CARDS */
.role-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-bottom:16px}
.role-card{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:16px;position:relative;overflow:hidden}
.role-card-accent{position:absolute;top:0;left:0;right:0;height:3px}
.rc-head{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.rc-icon{font-size:22px}
.rc-label{font-family:var(--bb);font-size:16px;letter-spacing:.04em;color:#fff}
.rc-level{font-size:9px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--txm);background:var(--card2);padding:2px 8px;border-radius:20px;margin-top:1px}
.rc-purpose{font-size:12px;color:var(--txm);line-height:1.5;margin-bottom:8px;font-style:italic}
.rc-resps{list-style:none;padding:0}
.rc-resps li{font-size:11px;color:var(--tx);padding:3px 0;display:flex;gap:6px;align-items:flex-start}
.rc-resps li::before{content:'•';color:var(--gold);flex-shrink:0}

/* AUDIT */
.ae{display:flex;gap:12px;padding:9px 0;border-bottom:1px solid rgba(30,34,64,.35)}
.adot{width:7px;height:7px;border-radius:50%;background:var(--gold);flex-shrink:0;margin-top:5px}
.ats{font-family:var(--mo);font-size:10px;color:var(--txm);margin-top:2px}
.aat{font-size:11px;background:rgba(201,168,76,.08);color:var(--gd);border:1px solid rgba(201,168,76,.15);padding:1px 6px;border-radius:4px;margin-left:4px;font-family:var(--mo)}

/* PHOTO */
.ep{width:36px;height:36px;border-radius:50%;object-fit:cover;border:2px solid var(--bdr)}
.epp{width:36px;height:36px;border-radius:50%;background:var(--card2);border:2px solid var(--bdr);display:flex;align-items:center;justify-content:center;font-size:14px}
.pavw{position:relative;display:inline-block;cursor:pointer}
.pav2{width:84px;height:84px;border-radius:50%;object-fit:cover;border:3px solid var(--gold)}
.pavb{position:absolute;bottom:0;right:0;background:var(--gold);color:var(--bg);width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px}

/* TOAST */
#toast{position:fixed;bottom:24px;right:24px;z-index:500;background:var(--card);border:1px solid var(--bdr);border-left:4px solid var(--gold);padding:12px 16px;border-radius:8px;font-size:13px;transform:translateY(80px);opacity:0;transition:all .28s;max-width:290px;pointer-events:none}
#toast.show{transform:translateY(0);opacity:1}
#toast.success{border-left-color:var(--ok)}
#toast.error{border-left-color:var(--err)}
#toast.warn{border-left-color:var(--warn)}

.irow{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid rgba(30,34,64,.5)}
.irow:last-child{border-bottom:none}.ik{font-size:11px;color:var(--txm)}.iv{font-size:13px}
.saldsp{font-family:var(--mo);font-size:20px;color:var(--gold)}

/* CONTRACT EXPIRY */
.exp-warn{background:rgba(224,154,48,.08);border:1px solid rgba(224,154,48,.2);border-radius:8px;padding:12px 14px;margin-bottom:12px}
.exp-item{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(30,34,64,.3);font-size:12px}
.exp-item:last-child{border-bottom:none}
.exp-days{font-family:var(--mo);font-size:11px;color:var(--warn);font-weight:600}

/* EMPLOYEE MINI LIST */
.emp-mini{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid rgba(30,34,64,.3)}
.emp-mini:last-child{border-bottom:none}
.emp-mini-name{font-size:13px;font-weight:500}
.emp-mini-role{font-size:11px;color:var(--txm)}

/* PROFILE ROLE CARD */
.prc{background:var(--card2);border:1px solid var(--bdr);border-radius:var(--r);padding:16px;margin-bottom:14px}

/* KEYBOARD HINT */
.kbhint{font-size:10px;color:var(--txd);font-family:var(--mo)}
kbd{background:var(--card2);border:1px solid var(--bdr);border-radius:4px;padding:1px 5px;font-size:10px;font-family:var(--mo)}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="ls">
  <canvas id="lc"></canvas>
  <div class="lgrid"></div><div class="lvig"></div>
  <div id="spl">
    <div class="sa">OBSIDIAN</div>
    <div class="se">CORPORATION</div>
    <div class="sdiv"></div>
    <div class="stag">The Corporate Management Platform</div>
  </div>
  <div id="lfw">
    <div class="lcard">
      <div class="lclg">OBSIDIAN</div>
      <div class="lcs">Corporate Portal</div>
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
    <div class="hlog">OBSIDIAN</div>
    <div class="hbc">CORPORATION &nbsp;›&nbsp; <span id="bcp">Dashboard</span></div>
    <div class="hr2">
      <button class="nbtn" onclick="toggleNP()" title="Notifications (N)">🔔<span class="nbdg" id="nbdg">0</span></button>
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
      <button class="nb" data-p="roles"><span class="ni">🔑</span>Role Guide</button>
      <button class="nb" data-p="sysusers" style="display:none" id="sb-su"><span class="ni">🔐</span>System Users</button>
      <button class="nb" data-p="profile"><span class="ni">⚙️</span>My Profile</button>
    </nav>
    <main id="main">

      <!-- DASHBOARD -->
      <section class="pg" id="pg-dashboard">
        <div class="pghdr"><div class="pght"><div class="pgt">Dashboard</div><div class="pgs">Corporate Overview — OBSIDIAN CORPORATION</div></div></div>
        <div id="dash-alerts"></div>
        <div class="sg" id="dstats"></div>
        <div class="cr">
          <div class="cc"><div class="ct">By Department</div><canvas id="ch-dept"></canvas></div>
          <div class="cc"><div class="ct">Employment Types</div><canvas id="ch-type"></canvas></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
          <div class="card" style="margin:0">
            <div class="ct">⚠️ Contract Expirations (90 days)</div>
            <div id="exp-list"><div style="color:var(--txm);font-size:12px">Loading…</div></div>
          </div>
          <div class="card" style="margin:0">
            <div class="ct">📋 Recent Activity</div>
            <div id="daud" style="padding:4px 0"></div>
          </div>
        </div>
      </section>

      <!-- EMPLOYEES -->
      <section class="pg" id="pg-employees">
        <div class="pghdr">
          <div class="pght"><div class="pgt">Employees</div><div class="pgs">Workforce management and records</div></div>
        </div>
        <div class="tb">
          <input class="si2" id="esrch" type="text" placeholder="🔍  Name, ID, email, department…" oninput="rEmp()">
          <select class="flt" id="efd" onchange="rEmp()"><option value="">All Departments</option></select>
          <select class="flt" id="efs" onchange="rEmp()"><option value="">All Status</option><option value="active">Active</option><option value="inactive">Inactive</option><option value="on_leave">On Leave</option></select>
          <select class="flt" id="eft" onchange="rEmp()"><option value="">All Types</option><option value="permanent">Permanent</option><option value="contract">Contract</option><option value="probation">Probation</option><option value="intern">Intern</option><option value="part_time">Part Time</option></select>
          <div class="sp"></div>
          <button class="btn bh sm" onclick="openModal('m-imp')">📥 Import</button>
          <div style="position:relative;display:inline-block">
            <button class="btn bh sm" onclick="toggleExpMenu()">📤 Export ▾</button>
            <div id="exp-menu" style="display:none;position:absolute;top:calc(100% + 4px);right:0;background:var(--card);border:1px solid var(--bdr);border-radius:8px;z-index:50;min-width:140px;overflow:hidden">
              <button class="btn bh sm" style="width:100%;border-radius:0;border:none;justify-content:flex-start" onclick="expCSV()">CSV</button>
              <button class="btn bh sm" style="width:100%;border-radius:0;border:none;justify-content:flex-start" onclick="expXLSX()">Excel (.xlsx)</button>
            </div>
          </div>
          <button class="btn bg" id="add-emp-btn" onclick="oAddEmp()" style="display:none">+ Add Employee</button>
        </div>
        <div id="emp-count" style="font-size:11px;color:var(--txm);margin-bottom:8px"></div>
        <div class="tw"><table><thead><tr><th>Photo</th><th>ID</th><th>Name</th><th>Department</th><th>Occupation</th><th>Type</th><th>Status</th><th>Start Date</th><th></th></tr></thead><tbody id="etb"></tbody></table></div>
      </section>

      <!-- DEPARTMENTS -->
      <section class="pg" id="pg-departments">
        <div class="pghdr">
          <div class="pght"><div class="pgt">Departments</div><div class="pgs">Organisational structure and purpose</div></div>
          <div><button class="btn bg" id="add-dept-btn" onclick="oAddDept()" style="display:none">+ Add Department</button></div>
        </div>
        <div class="dg" id="deptg"></div>
      </section>

      <!-- PROMOTIONS -->
      <section class="pg" id="pg-promotions">
        <div class="pghdr"><div class="pght"><div class="pgt">Promotions</div><div class="pgs">Career advancement workflow</div></div></div>
        <div class="card" id="prq-card" style="display:none">
          <div class="ct">Submit New Request</div>
          <div class="fg">
            <div class="fgr"><label class="flb">Employee ID</label><input class="fi" id="p-eid" placeholder="OBSD-2026-0001"></div>
            <div class="fgr"><label class="flb">Requested Role / Level</label><input class="fi" id="p-role" placeholder="e.g. Senior Engineer"></div>
            <div class="fgr full"><label class="flb">Justification / Notes</label><textarea class="fta" id="p-notes" placeholder="Brief reason for this promotion request…" style="min-height:52px"></textarea></div>
          </div>
          <div style="margin-top:12px"><button class="btn bg" onclick="subPromo()">Submit Request</button></div>
        </div>
        <div class="tb">
          <select class="flt" id="pfl" onchange="rPromo()"><option value="">All Statuses</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="denied">Denied</option></select>
          <div class="sp"></div>
          <button class="btn bk sm" id="promo-apr" onclick="resPromo('approved')" style="display:none">✅ Approve</button>
          <button class="btn br sm" id="promo-dny" onclick="resPromo('denied')" style="display:none">❌ Deny</button>
        </div>
        <div class="tw"><table><thead><tr><th>Employee</th><th>Name</th><th>Current Role</th><th>Requested Role</th><th>Notes</th><th>Date</th><th>Status</th><th>Resolved By</th></tr></thead><tbody id="ptb"></tbody></table></div>
      </section>

      <!-- LEAVE -->
      <section class="pg" id="pg-leave">
        <div class="pghdr"><div class="pght"><div class="pgt">Leave Management</div><div class="pgs">Absence tracking and approval</div></div></div>
        <div class="card">
          <div class="ct">Submit Leave Request</div>
          <div class="fg">
            <div class="fgr" id="lv-eid-row" style="display:none"><label class="flb">Employee ID (blank = self)</label><input class="fi" id="lv-eid" placeholder="OBSD-2026-0001"></div>
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
        <div class="tw"><table><thead><tr><th>Employee</th><th>Name</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Notes</th><th>Status</th><th>Resolved By</th></tr></thead><tbody id="ltb"></tbody></table></div>
      </section>

      <!-- PAYROLL -->
      <section class="pg" id="pg-payroll">
        <div class="pghdr"><div class="pght"><div class="pgt">Payroll &amp; Salary</div><div class="pgs">Compensation — HR &amp; Admin only</div></div></div>
        <div class="sg" id="prstats"></div>
        <div id="dept-pay-breakdown" style="margin-bottom:16px"></div>
        <div class="tb">
          <input class="si2" id="psrch" type="text" placeholder="🔍  Search by name or ID…" oninput="rPay()">
          <div class="sp"></div>
          <button class="btn bh sm" onclick="expPayCSV()">📤 CSV</button>
          <button class="btn bh sm" onclick="expPayXLSX()">📤 Excel</button>
          <button class="btn bg sm" onclick="oEditPayModal(S.selPay)" id="edit-pay-btn" style="display:none">✏️ Edit Salary</button>
        </div>
        <div class="tw"><table><thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Occupation</th><th>Role</th><th>Salary</th><th>Type</th></tr></thead><tbody id="prtb"></tbody></table></div>
      </section>

      <!-- AUDIT LOG -->
      <section class="pg" id="pg-audit">
        <div class="pghdr"><div class="pght"><div class="pgt">Audit Log</div><div class="pgs">System activity trail — HR &amp; Admin only</div></div></div>
        <div class="tb">
          <input class="si2" id="asrch" type="text" placeholder="🔍  Search user, action, target…" oninput="rAudit()">
          <select class="flt" id="afl" onchange="rAudit()">
            <option value="">All Actions</option>
            <option value="Login">Login</option>
            <option value="Added employee">Added Employee</option>
            <option value="Updated employee">Updated Employee</option>
            <option value="Deleted employee">Deleted Employee</option>
            <option value="Promotion">Promotion</option>
            <option value="Leave">Leave</option>
            <option value="Imported">Import</option>
          </select>
          <div class="sp"></div>
          <button class="btn bh sm" onclick="expAuditCSV()">📤 Export CSV</button>
        </div>
        <div class="tw"><table><thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Target</th><th>Detail</th></tr></thead><tbody id="atb"></tbody></table></div>
      </section>

      <!-- ROLE GUIDE -->
      <section class="pg" id="pg-roles">
        <div class="pghdr"><div class="pght"><div class="pgt">Role Guide</div><div class="pgs">System access levels and responsibilities</div></div></div>
        <div id="role-cards-container"></div>
      </section>

      <!-- SYSTEM USERS -->
      <section class="pg" id="pg-sysusers">
        <div class="pghdr"><div class="pght"><div class="pgt">System Users</div><div class="pgs">Portal access and authentication — Admin only</div></div></div>
        <div class="tb"><div class="sp"></div><button class="btn bg" onclick="oAddSU()">+ New User</button></div>
        <div class="tw"><table><thead><tr><th>Username</th><th>Full Name</th><th>Role</th><th>Employee ID</th><th>Created</th><th></th></tr></thead><tbody id="sutb"></tbody></table></div>
      </section>

      <!-- PROFILE -->
      <section class="pg" id="pg-profile">
        <div class="pghdr"><div class="pght"><div class="pgt">My Profile</div><div class="pgs">Account settings and personal details</div></div></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
          <div>
            <div class="card">
              <div class="ct">Account Details</div>
              <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px">
                <div class="pavw" onclick="document.getElementById('pf-photo-in').click()">
                  <div id="pf-av" style="font-size:40px;width:84px;height:84px;border-radius:50%;background:var(--card2);border:3px solid var(--gold);display:flex;align-items:center;justify-content:center">👤</div>
                  <div class="pavb">✏️</div>
                </div>
                <div>
                  <div style="font-family:var(--bb);font-size:22px;color:#fff" id="pf-name">—</div>
                  <div style="font-size:12px;color:var(--txm)" id="pf-uname">—</div>
                  <div class="bdg bgold" style="margin-top:6px" id="pf-role-badge">—</div>
                </div>
              </div>
              <input type="file" id="pf-photo-in" accept="image/*" style="display:none" onchange="uploadPhoto(this)">
              <div id="pf-emp-link"></div>
            </div>
            <div class="card prc" id="pf-role-card"></div>
          </div>
          <div>
            <div class="card">
              <div class="ct">Change Password</div>
              <div class="fgr" style="margin-bottom:10px"><label class="flb">Current Password</label><input class="fi" id="pw-cur" type="password"></div>
              <div class="fgr" style="margin-bottom:10px"><label class="flb">New Password</label><input class="fi" id="pw-new" type="password"></div>
              <div class="fgr" style="margin-bottom:14px"><label class="flb">Confirm New Password</label><input class="fi" id="pw-cnf" type="password"></div>
              <button class="btn bg" onclick="changePassword()">Update Password</button>
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
<div class="mo2" id="m-emp"><div class="mdl mdl-wide">
  <div class="mdlt" id="m-emp-t">Add Employee</div>
  <input type="hidden" id="me-id">
  <div class="fg">
    <div class="fgr"><label class="flb">Full Name *</label><input class="fi" id="me-fn" placeholder="First Last"></div>
    <div class="fgr"><label class="flb">Email</label><input class="fi" id="me-em" type="email" placeholder="email@co.com"></div>
    <div class="fgr"><label class="flb">Phone</label><input class="fi" id="me-ph" placeholder="+234 800 000 0000"></div>
    <div class="fgr"><label class="flb">Department</label><select class="fsel" id="me-dept"></select></div>
    <div class="fgr"><label class="flb">Occupation / Title</label><input class="fi" id="me-occ" placeholder="e.g. Software Engineer"></div>
    <div class="fgr"><label class="flb">Role / Level</label><input class="fi" id="me-rl" placeholder="e.g. Senior, Manager"></div>
    <div class="fgr"><label class="flb">Age</label><input class="fi" id="me-age" type="number" placeholder="28"></div>
    <div class="fgr"><label class="flb">Location</label><input class="fi" id="me-loc" placeholder="City, Country"></div>
    <div class="fgr"><label class="flb">Employment Type</label>
      <select class="fsel" id="me-et"><option value="permanent">Permanent</option><option value="contract">Contract</option><option value="probation">Probation</option><option value="intern">Intern</option><option value="part_time">Part Time</option></select></div>
    <div class="fgr"><label class="flb">Status</label>
      <select class="fsel" id="me-st"><option value="active">Active</option><option value="inactive">Inactive</option><option value="on_leave">On Leave</option></select></div>
    <div class="fgr"><label class="flb">Start Date</label><input class="fi" id="me-sd" type="date"></div>
    <div class="fgr"><label class="flb">Contract End Date</label><input class="fi" id="me-ce" type="date"></div>
    <div class="fgr"><label class="flb">Salary</label><input class="fi" id="me-sal" type="number" placeholder="50000"></div>
    <div class="fgr"><label class="flb">Currency</label>
      <select class="fsel" id="me-cur"><option value="USD">USD</option><option value="EUR">EUR</option><option value="GBP">GBP</option><option value="NGN">NGN</option><option value="KES">KES</option><option value="ZAR">ZAR</option><option value="GHS">GHS</option></select></div>
    <div class="fgr"><label class="flb">Direct Manager (Employee ID)</label><input class="fi" id="me-mgr" placeholder="OBSD-2026-0001 (optional)"></div>
    <div class="fgr"><label class="flb">Emergency Contact</label><input class="fi" id="me-ec" placeholder="Name — Phone"></div>
    <div class="fgr full"><label class="flb">Skills <span style="font-weight:400;text-transform:none;letter-spacing:0;color:var(--txd)">(type &amp; press Enter or comma)</span></label>
      <div class="tags-wrap" id="skills-wrap" onclick="document.getElementById('skills-input').focus()">
        <input class="tag-input" id="skills-input" placeholder="Add skill…" onkeydown="skillKey(event)" oninput="skillInput(event)">
      </div>
    </div>
  </div>
  <div class="mact"><button class="btn bh" onclick="cm('m-emp')">Cancel</button><button class="btn bg" onclick="saveEmp()">Save Employee</button></div>
</div></div>

<!-- VIEW EMP MODAL -->
<div class="mo2" id="m-vew"><div class="mdl mdl-wide">
  <div class="mdlt">Employee Profile</div>
  <div id="vew-cnt"></div>
  <div class="mact">
    <button class="btn bh" onclick="cm('m-vew')">Close</button>
    <button class="btn br sm" id="vew-del" onclick="delEmpFromView()" style="display:none">🗑 Delete</button>
    <button class="btn bg" id="vew-edt" onclick="editFromView()" style="display:none">✏️ Edit</button>
  </div>
</div></div>

<!-- DEPT MODAL (add/edit) -->
<div class="mo2" id="m-dept"><div class="mdl">
  <div class="mdlt" id="m-dept-t">Add Department</div>
  <input type="hidden" id="md-on">
  <div class="fg">
    <div class="fgr full"><label class="flb">Department Name *</label><input class="fi" id="md-nm" placeholder="e.g. Engineering"></div>
    <div class="fgr full"><label class="flb">Description</label><textarea class="fta" id="md-ds" placeholder="Brief description of what this department does…"></textarea></div>
    <div class="fgr full"><label class="flb">Head Employee ID (optional)</label><input class="fi" id="md-hd" placeholder="OBSD-2026-0001"></div>
  </div>
  <div class="mact"><button class="btn bh" onclick="cm('m-dept')">Cancel</button><button class="btn bg" onclick="saveDept()">Save</button></div>
</div></div>

<!-- DEPT DETAIL MODAL -->
<div class="mo2" id="m-dept-detail"><div class="mdl mdl-wide">
  <div class="mdlt" id="dd-title">Department Details</div>
  <div id="dd-content"></div>
  <div class="mact">
    <button class="btn bh" onclick="cm('m-dept-detail')">Close</button>
    <button class="btn bh sm" id="dd-edit-btn" onclick="editDeptFromDetail()" style="display:none">✏️ Edit</button>
    <button class="btn br sm" id="dd-del-btn" onclick="delDeptFromDetail()" style="display:none">🗑 Delete</button>
  </div>
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
      <select class="fsel" id="su-rl" onchange="updateRolePreview()">
        <option value="staff">Staff</option><option value="manager">Manager</option><option value="hr">HR Manager</option><option value="admin">Admin</option>
      </select></div>
    <div class="fgr"><label class="flb">Employee ID (optional)</label><input class="fi" id="su-eid" placeholder="OBSD-2026-0001"></div>
    <div class="fgr full"><label class="flb">Password (blank = keep existing)</label><input class="fi" id="su-pw" type="password" placeholder="Min 6 characters"></div>
    <div class="fgr full" id="su-role-preview" style="background:var(--card2);border:1px solid var(--bdr);border-radius:8px;padding:12px;font-size:12px;color:var(--txm)"></div>
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
const S = {
  user:null,employees:{},departments:{},sysUsers:{},auditLog:[],
  notifications:[],leaveReqs:[],selEmp:null,selPromo:null,selLeave:null,
  selPay:null,charts:{},npOpen:false,deptDefs:{},roleDefs:{},
  currentDeptDetail:null,skills:[]
};
const RL={admin:4,hr:3,manager:2,staff:1};
const RLAB={admin:'Admin',hr:'HR Manager',manager:'Manager',staff:'Staff'};
const RICO={admin:'🛡️',hr:'👔',manager:'📋',staff:'🧑‍💼'};
const RCOL={admin:'#e05252',hr:'#4f8ef7',manager:'#e09a30',staff:'#3dba7a'};
const ET={permanent:'Permanent',contract:'Contract',probation:'Probation',intern:'Intern',part_time:'Part Time'};
const LT={annual:'Annual',sick:'Sick',maternity:'Maternity/Paternity',unpaid:'Unpaid',other:'Other'};
const NOTIF_ICO={success:'✅',error:'❌',warning:'⚠️',info:'ℹ️'};

// ── BOOT
window.addEventListener('load',async()=>{
  initParticles();
  try{const r=await fetch('/api/me');if(r.ok){S.user=await r.json();await loadAll();showApp();document.getElementById('ls').classList.add('gone');return;}}catch(e){}
  setTimeout(()=>document.getElementById('lfw').classList.add('vis'),2700);
});

// ── PARTICLES
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
document.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&!document.getElementById('ls').classList.contains('gone'))doLogin();
  if(e.key==='Escape'){document.querySelectorAll('.mo2.open').forEach(m=>m.classList.remove('open'));if(S.npOpen)toggleNP();}
  if(e.key==='n'&&!e.target.matches('input,textarea,select')&&document.getElementById('app').classList.contains('vis'))toggleNP();
});
async function doLogout(){await fetch('/api/logout',{method:'POST'});location.reload();}

// ── SHOW APP
function showApp(){
  const a=document.getElementById('app');a.style.display='flex';a.classList.add('vis');
  const lvl=RL[S.user.role]||1;
  document.body.className='r'+S.user.role.charAt(0);
  document.getElementById('hname').textContent=S.user.full_name;
  document.getElementById('hrole').textContent=(RLAB[S.user.role]||S.user.role).toUpperCase();
  if(S.user.photo)document.getElementById('hav').innerHTML=`<img src="${S.user.photo}" style="width:30px;height:30px;border-radius:50%;object-fit:cover;border:2px solid var(--gd)">`;
  if(lvl>=3){['sb-payroll','sb-audit','add-emp-btn','add-dept-btn','promo-apr','promo-dny','lv-apr','lv-dny'].forEach(id=>{const el=document.getElementById(id);if(el)el.style.display='';});}
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
  document.getElementById('bcp').textContent={
    dashboard:'Dashboard',employees:'Employees',departments:'Departments',
    promotions:'Promotions',leave:'Leave Management',payroll:'Payroll & Salary',
    audit:'Audit Log',roles:'Role Guide',sysusers:'System Users',profile:'My Profile'
  }[p]||p;
  if(p==='dashboard')renderDash();
  if(p==='employees')rEmp();
  if(p==='departments')rDepts();
  if(p==='promotions')rPromo();
  if(p==='leave')rLeave();
  if(p==='payroll')rPay();
  if(p==='audit')rAudit();
  if(p==='roles')rRoles();
  if(p==='sysusers')rSU();
  if(p==='profile')rProfile();
}

// ── DATA LOAD
async function loadAll(){
  const r=await fetch('/api/data');const d=await r.json();
  S.employees=d.employees||{};S.departments=d.departments||{};
  S.sysUsers=d.system_users||{};S.auditLog=d.audit_log||[];
  S.notifications=d.notifications||[];S.leaveReqs=d.leave_requests||[];
  S.deptDefs=d.dept_definitions||{};S.roleDefs=d.role_definitions||{};
  refreshBadges();refreshNotifPanel();
}

function refreshBadges(){
  const pe=S.leaveReqs.filter(r=>r.status==='pending').length;
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
  const inactive=emps.filter(e=>e.status==='inactive').length;
  const depts=Object.keys(S.departments).length;
  const stats=[
    {label:'Total Employees',val:emps.length,cls:''},
    {label:'Active',val:active,cls:'gn'},
    {label:'On Leave',val:onLeave,cls:'wn'},
    {label:'Inactive',val:inactive,cls:'rd'},
    {label:'Pending Promotions',val:pend,cls:'rd'},
    {label:'Departments',val:depts,cls:'bl'},
    {label:'Leave Requests',val:S.leaveReqs.filter(r=>r.status==='pending').length,cls:'wn'},
  ];
  document.getElementById('dstats').innerHTML=stats.map(s=>`<div class="sc ${s.cls}"><div class="sv">${s.val}</div><div class="slb">${s.label}</div></div>`).join('');

  // contract expiry alerts
  const today=new Date();const d90=new Date();d90.setDate(d90.getDate()+90);
  const expiring=Object.entries(S.employees).filter(([,e])=>{
    if(!e.contract_end)return false;
    const ce=new Date(e.contract_end);return ce>=today&&ce<=d90;
  }).sort(([,a],[,b])=>new Date(a.contract_end)-new Date(b.contract_end));
  const expEl=document.getElementById('exp-list');
  if(expiring.length===0){expEl.innerHTML='<div style="color:var(--txm);font-size:12px;padding:4px 0">No contracts expiring in the next 90 days.</div>';}
  else{expEl.innerHTML=expiring.map(([id,e])=>{
    const days=Math.ceil((new Date(e.contract_end)-today)/(1000*60*60*24));
    const cls=days<=30?'bred':days<=60?'bwarn':'bgray';
    return `<div class="exp-item"><span><strong>${esc(e.full_name)}</strong><span style="font-size:11px;color:var(--txm);margin-left:6px">${esc(e.occupation||'')}</span></span><span class="bdg ${cls} exp-days">${days}d — ${esc(e.contract_end)}</span></div>`;
  }).join('');}

  // alerts
  const alerts=document.getElementById('dash-alerts');
  const warns=[];
  if(expiring.filter(([,e])=>Math.ceil((new Date(e.contract_end)-today)/(1000*60*60*24))<=30).length>0)warns.push(`⚠️  ${expiring.filter(([,e])=>Math.ceil((new Date(e.contract_end)-today)/(1000*60*60*24))<=30).length} contract(s) expiring within 30 days.`);
  if(pend>0)warns.push(`🏆  ${pend} pending promotion request${pend>1?'s':''}.`);
  alerts.innerHTML=warns.map(w=>`<div class="alert-strip warn">${w}</div>`).join('');

  // dept chart
  const dmap={};
  emps.forEach(e=>{if(e.department)dmap[e.department]=(dmap[e.department]||0)+1;});
  mkChart('ch-dept','doughnut',Object.keys(dmap),Object.values(dmap));

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
  const ft=document.getElementById('eft')?.value||'';
  const dsel=document.getElementById('efd');
  const curD=dsel.value;
  dsel.innerHTML='<option value="">All Departments</option>'+Object.keys(S.departments).map(d=>`<option value="${esc(d)}" ${d===curD?'selected':''}>${esc(d)}</option>`).join('');
  const rows=Object.entries(S.employees).filter(([id,e])=>{
    if(fd&&e.department!==fd)return false;
    if(fs&&e.status!==fs)return false;
    if(ft&&e.employment_type!==ft)return false;
    if(q&&![id,e.full_name,e.email,e.department,e.occupation,e.role,e.phone].some(x=>(x||'').toLowerCase().includes(q)))return false;
    if(S.user.role==='staff'&&id!==S.user.emp_id)return false;
    return true;
  });
  document.getElementById('emp-count').textContent=`Showing ${rows.length} of ${Object.keys(S.employees).length} employees`;
  const tb=document.getElementById('etb');
  if(!rows.length){tb.innerHTML='<tr class="er"><td colspan="9">No employees found.</td></tr>';return;}
  tb.innerHTML=rows.map(([id,e])=>{
    const photo=e.photo?`<img class="ep" src="${e.photo}">`:`<div class="epp">👤</div>`;
    const sbc=stCls(e.status);
    const tbc={permanent:'bgold',contract:'bblue',probation:'bwarn',intern:'bgray',part_time:'bgray'}[e.employment_type]||'bgray';
    const startDate=e.start_date||e.date_added||'—';
    return `<tr onclick="viewEmp('${esc(id)}')">
      <td>${photo}</td>
      <td style="font-family:var(--mo);font-size:11px">${esc(id)}</td>
      <td><strong>${esc(e.full_name||'')}</strong>${e.phone?`<div style="font-size:10px;color:var(--txm)">${esc(e.phone)}</div>`:''}</td>
      <td>${esc(e.department||'')}</td>
      <td>${esc(e.occupation||'')}${e.role?`<div style="font-size:10px;color:var(--txm)">${esc(e.role)}</div>`:''}</td>
      <td><span class="bdg ${tbc}">${esc(ET[e.employment_type]||e.employment_type||'—')}</span></td>
      <td><span class="bdg ${sbc}">${esc(e.status||'—')}</span></td>
      <td style="font-size:11px;color:var(--txm);font-family:var(--mo)">${esc(startDate)}</td>
      <td><button class="btn bh sm" onclick="event.stopPropagation();viewEmp('${esc(id)}')">View</button></td>
    </tr>`;
  }).join('');
}

function viewEmp(id){
  S.selEmp=id;const e=S.employees[id];if(!e)return;
  const lvl=RL[S.user.role]||1;
  const salary=lvl>=3?`<div class="irow"><span class="ik">Salary</span><span class="iv saldsp">${e.salary?e.salary_currency+' '+Number(e.salary).toLocaleString():'—'}</span></div>`:''
  const skills=(e.skills&&e.skills.length)?`<div class="irow"><span class="ik">Skills</span><span class="iv" style="display:flex;flex-wrap:wrap;gap:4px">${e.skills.map(s=>`<span class="bdg bgold">${esc(s)}</span>`).join('')}</span></div>`:'';
  const manager=e.manager_id&&S.employees[e.manager_id]?`<div class="irow"><span class="ik">Manager</span><span class="iv">${esc(S.employees[e.manager_id].full_name)} <span style="font-family:var(--mo);font-size:11px;color:var(--txm)">(${esc(e.manager_id)})</span></span></div>`:'';
  const ddef=S.deptDefs[e.department]||{};
  document.getElementById('vew-cnt').innerHTML=`
    <div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:16px">
      ${e.photo?`<img src="${e.photo}" style="width:72px;height:72px;border-radius:50%;object-fit:cover;border:3px solid var(--gold);flex-shrink:0">`:`<div style="width:72px;height:72px;border-radius:50%;background:var(--card2);border:3px solid var(--gold);display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0">👤</div>`}
      <div>
        <div style="font-family:var(--bb);font-size:22px;color:#fff">${esc(e.full_name||'')}</div>
        <div style="color:var(--txm);font-size:12px">${esc(e.occupation||'—')}${e.role?` · ${esc(e.role)}`:''}</div>
        <div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:5px">
          <div class="bdg bgold">${esc(id)}</div>
          ${ddef.icon?`<div class="bdg" style="background:rgba(201,168,76,.08);color:var(--txm)">${esc(ddef.icon)} ${esc(e.department||'')}</div>`:''}
        </div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0">
      <div>
        <div class="irow"><span class="ik">Email</span><span class="iv">${esc(e.email||'—')}</span></div>
        <div class="irow"><span class="ik">Phone</span><span class="iv">${esc(e.phone||'—')}</span></div>
        <div class="irow"><span class="ik">Department</span><span class="iv">${esc(e.department||'—')}</span></div>
        <div class="irow"><span class="ik">Employment Type</span><span class="iv">${esc(ET[e.employment_type]||e.employment_type||'—')}</span></div>
        <div class="irow"><span class="ik">Status</span><span class="iv"><span class="bdg ${stCls(e.status)}">${esc(e.status||'—')}</span></span></div>
        ${salary}
      </div>
      <div>
        <div class="irow"><span class="ik">Location</span><span class="iv">${esc(e.location||'—')}</span></div>
        <div class="irow"><span class="ik">Age</span><span class="iv">${esc(e.age||'—')}</span></div>
        <div class="irow"><span class="ik">Start Date</span><span class="iv">${esc(e.start_date||'—')}</span></div>
        <div class="irow"><span class="ik">Contract End</span><span class="iv">${esc(e.contract_end||'—')}</span></div>
        <div class="irow"><span class="ik">Date Added</span><span class="iv">${esc(e.date_added||'—')}</span></div>
        <div class="irow"><span class="ik">Emergency Contact</span><span class="iv">${esc(e.emergency_contact||'—')}</span></div>
      </div>
    </div>
    ${manager}${skills}
    ${(e.promotion_requests||[]).length?`<div style="margin-top:12px"><div class="ct" style="font-size:13px;margin-bottom:6px">Promotion History</div>${(e.promotion_requests||[]).slice(0,3).map(r=>`<div class="irow"><span class="ik">${esc(r.date||'')}</span><span class="iv">${esc(r.current_role||'?')} → <strong>${esc(r.requested_role||'')}</strong> <span class="bdg ${prCls(r.status)}">${esc(r.status)}</span></span></div>`).join('')}</div>`:''}`;
  const edtBtn=document.getElementById('vew-edt');const delBtn=document.getElementById('vew-del');
  if(edtBtn)edtBtn.style.display=lvl>=3?'':'none';
  if(delBtn)delBtn.style.display=lvl>=3?'':'none';
  openModal('m-vew');
}
function editFromView(){cm('m-vew');if(S.selEmp)oEditEmp(S.selEmp);}
async function delEmpFromView(){
  if(!S.selEmp||!confirm(`Delete employee ${S.selEmp}? This cannot be undone.`))return;
  const r=await api('DELETE',`/api/employees/${encodeURIComponent(S.selEmp)}`);
  if(r.ok){delete S.employees[S.selEmp];S.selEmp=null;cm('m-vew');rEmp();renderDash();toast('Employee deleted.','success');}
  else toast((await r.json()).error,'error');
}

// ── SKILLS TAG INPUT
function skillKey(e){
  if(e.key==='Enter'||e.key===','||e.key===';'){e.preventDefault();addSkillTag(e.target.value);}
  if(e.key==='Backspace'&&!e.target.value&&S.skills.length){removeSkill(S.skills.length-1);}
}
function skillInput(e){if(e.target.value.includes(',')){const parts=e.target.value.split(',');parts.slice(0,-1).forEach(p=>addSkillTag(p));e.target.value=parts[parts.length-1];}}
function addSkillTag(val){val=val.trim();if(!val||S.skills.includes(val))return;S.skills.push(val);renderSkillTags();document.getElementById('skills-input').value='';}
function removeSkill(i){S.skills.splice(i,1);renderSkillTags();}
function renderSkillTags(){
  const wrap=document.getElementById('skills-wrap');
  const input=document.getElementById('skills-input');
  wrap.querySelectorAll('.tag-item').forEach(t=>t.remove());
  S.skills.forEach((s,i)=>{
    const t=document.createElement('span');t.className='tag-item';
    t.innerHTML=`${esc(s)}<button class="tag-rm" onclick="removeSkill(${i})">×</button>`;
    wrap.insertBefore(t,input);
  });
}

function oAddEmp(){
  S.selEmp=null;S.skills=[];
  document.getElementById('m-emp-t').textContent='Add Employee';
  const dsel=document.getElementById('me-dept');
  dsel.innerHTML=Object.keys(S.departments).map(d=>`<option value="${esc(d)}">${esc(d)}</option>`).join('');
  ['me-id','me-fn','me-em','me-ph','me-occ','me-rl','me-age','me-loc','me-ce','me-sal','me-mgr','me-ec','me-sd'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('me-et').value='permanent';
  document.getElementById('me-st').value='active';
  document.getElementById('me-cur').value='USD';
  renderSkillTags();
  openModal('m-emp');
}
function oEditEmp(id){
  S.selEmp=id;const e=S.employees[id];if(!e)return;
  S.skills=Array.isArray(e.skills)?[...e.skills]:[];
  document.getElementById('m-emp-t').textContent='Edit Employee';
  document.getElementById('me-id').value=id;
  const dsel=document.getElementById('me-dept');
  dsel.innerHTML=Object.keys(S.departments).map(d=>`<option value="${esc(d)}" ${d===e.department?'selected':''}>${esc(d)}</option>`).join('');
  set('me-fn',e.full_name);set('me-em',e.email);set('me-ph',e.phone);
  set('me-occ',e.occupation);set('me-rl',e.role);set('me-age',e.age);
  set('me-loc',e.location);set('me-ce',e.contract_end);set('me-sal',e.salary);
  set('me-mgr',e.manager_id);set('me-ec',e.emergency_contact);set('me-sd',e.start_date);
  document.getElementById('me-et').value=e.employment_type||'permanent';
  document.getElementById('me-st').value=e.status||'active';
  document.getElementById('me-cur').value=e.salary_currency||'USD';
  renderSkillTags();
  openModal('m-emp');
}
async function saveEmp(){
  const id=document.getElementById('me-id').value;
  const remaining=document.getElementById('skills-input').value.trim();
  if(remaining)addSkillTag(remaining);
  const body={
    full_name:v('me-fn'),email:v('me-em'),phone:v('me-ph'),
    department:document.getElementById('me-dept').value,
    occupation:v('me-occ'),role:v('me-rl'),age:v('me-age'),location:v('me-loc'),
    employment_type:document.getElementById('me-et').value,
    status:document.getElementById('me-st').value,
    contract_end:v('me-ce'),start_date:v('me-sd'),
    salary:v('me-sal'),salary_currency:document.getElementById('me-cur').value,
    manager_id:v('me-mgr'),emergency_contact:v('me-ec'),
    skills:S.skills,
  };
  if(!body.full_name){toast('Full name is required.','error');return;}
  const r=await api(id?'PUT':'POST',id?`/api/employees/${encodeURIComponent(id)}`:'/api/employees',body);
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees[d.id]=d.employee;cm('m-emp');rEmp();renderDash();
  toast(id?'Employee updated.':'Employee added.','success');
}

function toggleExpMenu(){
  const m=document.getElementById('exp-menu');m.style.display=m.style.display==='none'?'block':'none';
}
document.addEventListener('click',e=>{if(!e.target.closest('#exp-menu')&&!e.target.textContent.includes('Export'))document.getElementById('exp-menu').style.display='none';});
function expCSV(){window.location.href='/api/export/employees-csv';document.getElementById('exp-menu').style.display='none';}
function expXLSX(){window.location.href='/api/export/employees-excel';document.getElementById('exp-menu').style.display='none';}
function expPayCSV(){window.location.href='/api/export/payroll-csv';}
function expPayXLSX(){window.location.href='/api/export/payroll-excel';}
function expAuditCSV(){window.location.href='/api/export/audit-csv';}

// ── DEPARTMENTS
function rDepts(){
  const lvl=RL[S.user.role]||1;
  document.getElementById('deptg').innerHTML=Object.entries(S.departments).map(([n,d])=>{
    const cnt=Object.values(S.employees).filter(e=>e.department===n).length;
    const head=d.head_id?S.employees[d.head_id]?.full_name||d.head_id:'No head assigned';
    const def=S.deptDefs[n]||{icon:'🏢',color:'#5a6080',kpis:[]};
    const kpis=(def.kpis||[]).map(k=>`<span class="dc-kpi">${esc(k)}</span>`).join('');
    return `<div class="dc" onclick="viewDept('${esc(n)}')">
      <div class="dc-accent" style="background:${esc(def.color||'#c9a84c')}"></div>
      <div class="dcc">${cnt}</div>
      <div class="dcn"><span class="dci">${esc(def.icon||'🏢')}</span>${esc(n)}</div>
      <div class="dcd">${esc(d.description||def.purpose||'')}</div>
      <div class="dch">👤 ${esc(head)}</div>
      <div class="dc-kpis">${kpis}</div>
      <div class="dca" onclick="event.stopPropagation()">
        ${lvl>=3?`<button class="btn bh sm" onclick="oEditDept('${esc(n)}')">Edit</button>`:''}
        ${lvl>=4?`<button class="btn br sm" onclick="delDept('${esc(n)}')">Delete</button>`:''}
        <button class="btn binfo sm" onclick="viewDept('${esc(n)}')">Details</button>
      </div>
    </div>`;
  }).join('')||'<div style="color:var(--txm);font-size:13px">No departments found.</div>';
}

function viewDept(name){
  S.currentDeptDetail=name;
  const d=S.departments[name]||{};
  const def=S.deptDefs[name]||{icon:'🏢',color:'#5a6080',purpose:'',responsibilities:[],kpis:[]};
  const lvl=RL[S.user.role]||1;
  const emps=Object.entries(S.employees).filter(([,e])=>e.department===name);
  const head=d.head_id?S.employees[d.head_id]:null;

  document.getElementById('dd-title').innerHTML=`<span style="margin-right:8px">${esc(def.icon)}</span>${esc(name)}`;
  document.getElementById('dd-content').innerHTML=`
    <div style="border-left:3px solid ${esc(def.color)};padding-left:14px;margin-bottom:16px">
      <div style="font-size:13px;color:var(--txm);line-height:1.6;font-style:italic">${esc(def.purpose||d.description||'')}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
      <div>
        <div class="ct" style="font-size:13px">Key Responsibilities</div>
        <ul class="resp-list">${(def.responsibilities||[]).map(r=>`<li>${esc(r)}</li>`).join('')||'<li>No responsibilities defined.</li>'}</ul>
      </div>
      <div>
        <div class="ct" style="font-size:13px">Performance Indicators</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px">${(def.kpis||[]).map(k=>`<span class="bdg bgold" style="font-size:11px">${esc(k)}</span>`).join('')||'<span style="font-size:12px;color:var(--txm)">Not defined.</span>'}</div>
        <div style="margin-top:16px">
          <div class="ct" style="font-size:13px">Department Head</div>
          ${head?`<div class="emp-mini"><div class="epp" style="width:30px;height:30px;font-size:12px">👤</div><div><div class="emp-mini-name">${esc(head.full_name)}</div><div class="emp-mini-role">${esc(head.occupation||'—')}</div></div></div>`:`<div style="font-size:12px;color:var(--txm)">No head assigned.</div>`}
        </div>
      </div>
    </div>
    <div>
      <div class="ct" style="font-size:13px">Team Members (${emps.length})</div>
      ${emps.slice(0,6).map(([id,e])=>`<div class="emp-mini"><div class="epp" style="width:28px;height:28px;font-size:11px">👤</div><div><div class="emp-mini-name">${esc(e.full_name)}</div><div class="emp-mini-role">${esc(e.occupation||'—')} · <span class="bdg ${stCls(e.status)}" style="font-size:9px">${esc(e.status)}</span></div></div></div>`).join('')}
      ${emps.length>6?`<div style="font-size:11px;color:var(--txm);padding:4px 0">+${emps.length-6} more</div>`:''}
    </div>`;
  document.getElementById('dd-edit-btn').style.display=lvl>=3?'':'none';
  document.getElementById('dd-del-btn').style.display=lvl>=4?'':'none';
  openModal('m-dept-detail');
}
function editDeptFromDetail(){cm('m-dept-detail');oEditDept(S.currentDeptDetail);}
async function delDeptFromDetail(){
  if(!S.currentDeptDetail||!confirm(`Delete department "${S.currentDeptDetail}"?`))return;
  const r=await api('DELETE',`/api/departments/${encodeURIComponent(S.currentDeptDetail)}`);
  if(r.ok){delete S.departments[S.currentDeptDetail];cm('m-dept-detail');rDepts();toast('Department deleted.','success');}
  else toast((await r.json()).error,'error');
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
  if(!rows.length){tb.innerHTML='<tr class="er"><td colspan="8">No promotion requests.</td></tr>';return;}
  tb.innerHTML=rows.map(({id,e,req,i})=>{
    const sc={pending:'bwarn',approved:'bgreen',denied:'bred'}[req.status]||'bgray';
    const notes=req.notes?`<span title="${esc(req.notes)}" style="cursor:help">💬</span>`:'';
    const resolver=req.resolved_by?`<span style="font-size:11px;color:var(--txm)">${esc(req.resolved_by)}</span>`:'—';
    return `<tr class="${S.selPromo===id+'::'+i?'sel':''}" onclick="selPromo2('${esc(id)}','${i}',this)">
      <td style="font-family:var(--mo);font-size:11px">${esc(id)}</td>
      <td>${esc(e.full_name||'')}</td>
      <td>${esc(req.current_role||'')}</td>
      <td><strong>${esc(req.requested_role||'')}</strong></td>
      <td>${notes}${req.notes?`<span style="font-size:11px;color:var(--txm);max-width:120px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(req.notes)}</span>`:''}</td>
      <td style="font-size:11px;color:var(--txm);font-family:var(--mo)">${esc(req.date||'')}</td>
      <td><span class="bdg ${sc}">${esc(req.status)}</span></td>
      <td>${resolver}</td>
    </tr>`;
  }).join('');
}
function selPromo2(id,i,row){
  document.querySelectorAll('#ptb tr').forEach(r=>r.classList.remove('sel'));
  row.classList.add('sel');
  S.selPromo=id+'::'+i;
}
async function subPromo(){
  const eid=v('p-eid'),rr=v('p-role'),notes=v('p-notes');
  if(!eid||!rr){toast('Employee ID and role required.','error');return;}
  const r=await api('POST','/api/promotions',{emp_id:eid,requested_role:rr,notes});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees=d.employees;rPromo();renderDash();
  set('p-eid','');set('p-role','');set('p-notes','');
  toast('Promotion request submitted.','success');
}
async function resPromo(resolution){
  if(!S.selPromo){toast('Select a request first.','error');return;}
  const[id,i]=S.selPromo.split('::');
  const r=await api('PUT',`/api/promotions/${encodeURIComponent(id)}/${i}`,{resolution});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees=d.employees;S.selPromo=null;rPromo();renderDash();
  toast(`Promotion ${resolution}.`,'success');
}

// ── LEAVE
function rLeave(){
  const fl=document.getElementById('lfl')?.value||'';
  const rows=S.leaveReqs.filter(r=>!fl||r.status===fl);
  const tb=document.getElementById('ltb');
  if(!rows.length){tb.innerHTML='<tr class="er"><td colspan="9">No leave requests.</td></tr>';return;}
  tb.innerHTML=rows.map((req,i)=>{
    const e=S.employees[req.emp_id]||{};
    const sc={pending:'bwarn',approved:'bgreen',denied:'bred'}[req.status]||'bgray';
    const days=req.start_date&&req.end_date?Math.ceil((new Date(req.end_date)-new Date(req.start_date))/(1000*60*60*24))+1:'—';
    const resolver=req.resolved_by?`<span style="font-size:11px;color:var(--txm)">${esc(req.resolved_by)}</span>`:'—';
    return `<tr class="${S.selLeave===i?'sel':''}" onclick="selLeave2(${i},this)">
      <td style="font-family:var(--mo);font-size:11px">${esc(req.emp_id||'')}</td>
      <td>${esc(e.full_name||req.emp_id||'—')}</td>
      <td><span class="bdg bblue">${esc(LT[req.leave_type]||req.leave_type||'—')}</span></td>
      <td style="font-family:var(--mo);font-size:11px">${esc(req.start_date||'')}</td>
      <td style="font-family:var(--mo);font-size:11px">${esc(req.end_date||'')}</td>
      <td style="font-family:var(--bb);font-size:16px">${days}</td>
      <td style="max-width:120px;overflow:hidden;text-overflow:ellipsis;font-size:11px;color:var(--txm)">${esc(req.notes||'—')}</td>
      <td><span class="bdg ${sc}">${esc(req.status||'—')}</span></td>
      <td>${resolver}</td>
    </tr>`;
  }).join('');
}
function selLeave2(i,row){document.querySelectorAll('#ltb tr').forEach(r=>r.classList.remove('sel'));row.classList.add('sel');S.selLeave=i;}
async function subLeave(){
  const lvl=RL[S.user.role]||1;
  const eid_input=v('lv-eid');
  let eid=eid_input||S.user.emp_id;
  if(!eid&&lvl<3){toast('No employee ID linked to your account. Ask HR.','error');return;}
  const body={emp_id:eid,leave_type:document.getElementById('lv-type').value,start_date:v('lv-s'),end_date:v('lv-e'),notes:v('lv-r')};
  if(!body.start_date||!body.end_date){toast('Start and end dates required.','error');return;}
  const r=await api('POST','/api/leave',body);
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.leaveReqs=d.leave_requests;rLeave();refreshBadges();
  set('lv-eid','');set('lv-s','');set('lv-e','');set('lv-r','');
  toast('Leave request submitted.','success');
}
async function resLeave(resolution){
  if(S.selLeave===null||S.selLeave===undefined){toast('Select a request first.','error');return;}
  const r=await api('PUT',`/api/leave/${S.selLeave}`,{resolution});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.leaveReqs=d.leave_requests;S.employees=d.employees||S.employees;
  S.selLeave=null;rLeave();refreshBadges();renderDash();
  toast(`Leave ${resolution}.`,'success');
}

// ── PAYROLL
function rPay(){
  const q=(document.getElementById('psrch')?.value||'').toLowerCase();
  const lvl=RL[S.user.role]||1;
  if(lvl<3){document.getElementById('prtb').innerHTML='<tr class="er"><td colspan="7">Access restricted to HR and Admin.</td></tr>';return;}
  const emps=Object.entries(S.employees).filter(([id,e])=>{
    if(!q)return true;
    return [id,e.full_name,e.department,e.occupation].some(x=>(x||'').toLowerCase().includes(q));
  });

  // dept breakdown
  const deptPay={};
  Object.values(S.employees).forEach(e=>{
    if(!e.salary||e.salary_currency!=='USD')return;
    const d=e.department||'Unknown';
    deptPay[d]=(deptPay[d]||0)+Number(e.salary);
  });
  const totalUSD=Object.values(deptPay).reduce((a,b)=>a+b,0);
  const deptBreakEl=document.getElementById('dept-pay-breakdown');
  if(Object.keys(deptPay).length){
    deptBreakEl.innerHTML=`<div class="card" style="margin-bottom:0"><div class="ct">USD Payroll by Department</div><div style="display:flex;gap:14px;flex-wrap:wrap">${
      Object.entries(deptPay).sort(([,a],[,b])=>b-a).map(([d,v])=>{
        const def=S.deptDefs[d]||{};
        const pct=totalUSD?Math.round(v/totalUSD*100):0;
        return `<div style="flex:1;min-width:140px"><div style="font-size:11px;color:var(--txm);margin-bottom:3px">${esc(def.icon||'')}&nbsp;${esc(d)}</div><div style="font-family:var(--bb);font-size:18px;color:var(--gold)">$${v.toLocaleString()}</div><div style="height:4px;background:var(--bdr);border-radius:2px;margin-top:3px"><div style="height:4px;background:${esc(def.color||'#c9a84c')};border-radius:2px;width:${pct}%"></div></div><div style="font-size:10px;color:var(--txm);margin-top:2px">${pct}% of USD total</div></div>`;
      }).join('')
    }</div></div>`;
  }else{deptBreakEl.innerHTML='';}

  // stats
  let tot=0,with_sal=0;
  Object.values(S.employees).forEach(e=>{if(e.salary&&e.salary_currency==='USD'){tot+=Number(e.salary);with_sal++;}});
  const avg=with_sal?Math.round(tot/with_sal):0;
  document.getElementById('prstats').innerHTML=[
    {label:'Total Employees',val:Object.keys(S.employees).length,cls:''},
    {label:'With Salary Set',val:with_sal,cls:'gn'},
    {label:'Total USD Payroll',val:'$'+tot.toLocaleString(),cls:'bl'},
    {label:'Avg USD Salary',val:'$'+avg.toLocaleString(),cls:''},
  ].map(s=>`<div class="sc ${s.cls}"><div class="sv" style="font-size:${typeof s.val==='string'&&s.val.length>8?'24px':'38px'}">${s.val}</div><div class="slb">${s.label}</div></div>`).join('');

  const tb=document.getElementById('prtb');
  if(!emps.length){tb.innerHTML='<tr class="er"><td colspan="7">No employees found.</td></tr>';return;}
  tb.innerHTML=emps.map(([id,e])=>{
    const sc=stCls(e.status);
    return `<tr class="${S.selPay===id?'sel':''}" onclick="selPayRow('${esc(id)}',this)">
      <td style="font-family:var(--mo);font-size:11px">${esc(id)}</td>
      <td><strong>${esc(e.full_name||'')}</strong></td>
      <td>${esc(e.department||'')}</td>
      <td>${esc(e.occupation||'')}</td>
      <td><span class="bdg bgray">${esc(e.role||'—')}</span></td>
      <td class="saldsp" style="font-size:14px">${e.salary?esc(e.salary_currency)+' '+Number(e.salary).toLocaleString():'<span style="color:var(--txm)">—</span>'}</td>
      <td><span class="bdg ${sc}">${esc(e.status||'—')}</span></td>
    </tr>`;
  }).join('');
}
function selPayRow(id,row){
  document.querySelectorAll('#prtb tr').forEach(r=>r.classList.remove('sel'));
  row.classList.add('sel');S.selPay=id;
  document.getElementById('edit-pay-btn').style.display='';
}
function oEditPayModal(id){
  if(!id)return;const e=S.employees[id];if(!e)return;
  document.getElementById('mp-id').value=id;
  set('mp-sal',e.salary);
  document.getElementById('mp-cur').value=e.salary_currency||'USD';
  openModal('m-pay');
}
async function savePay(){
  const id=document.getElementById('mp-id').value;
  const r=await api('PUT',`/api/employees/${encodeURIComponent(id)}`,{salary:v('mp-sal'),salary_currency:document.getElementById('mp-cur').value});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees[id]=d.employee;cm('m-pay');rPay();toast('Salary updated.','success');
}

// ── AUDIT LOG
function rAudit(){
  const q=(document.getElementById('asrch')?.value||'').toLowerCase();
  const af=document.getElementById('afl')?.value||'';
  const rows=S.auditLog.filter(a=>{
    if(af&&!a.action.toLowerCase().includes(af.toLowerCase()))return false;
    if(q&&![a.user,a.action,a.target,a.detail].some(x=>(x||'').toLowerCase().includes(q)))return false;
    return true;
  });
  const tb=document.getElementById('atb');
  if(!rows.length){tb.innerHTML='<tr class="er"><td colspan="5">No log entries found.</td></tr>';return;}
  tb.innerHTML=rows.map(a=>{
    const action_cls={'Login':'bblue','Added employee':'bgreen','Deleted employee':'bred','Updated employee':'bwarn','Imported employees':'bpurple'}[a.action]||'bgray';
    return `<tr>
      <td style="font-family:var(--mo);font-size:11px;color:var(--txm)">${esc(a.ts)}</td>
      <td><span class="bdg bgold">${esc(a.user)}</span></td>
      <td><span class="bdg ${action_cls}" style="font-size:10px">${esc(a.action)}</span></td>
      <td style="font-family:var(--mo);font-size:11px">${esc(a.target)}</td>
      <td style="font-size:12px;color:var(--txm)">${esc(a.detail)}</td>
    </tr>`;
  }).join('');
}

// ── ROLE GUIDE
function rRoles(){
  const defs=S.roleDefs;
  if(!defs||!Object.keys(defs).length){
    document.getElementById('role-cards-container').innerHTML='<div style="color:var(--txm)">Role definitions not loaded.</div>';return;
  }
  document.getElementById('role-cards-container').innerHTML=`
    <div class="role-grid">
      ${['admin','hr','manager','staff'].map(k=>{
        const def=defs[k]||{};
        const resps=(def.responsibilities||[]).map(r=>`<li>${esc(r)}</li>`).join('');
        return `<div class="role-card">
          <div class="role-card-accent" style="background:${esc(def.color||'#c9a84c')}"></div>
          <div class="rc-head">
            <div class="rc-icon">${esc(def.icon||'👤')}</div>
            <div>
              <div class="rc-label">${esc(def.label||RLAB[k]||k)}</div>
              <div class="rc-level">Level ${esc(String(def.level||'?'))} Access</div>
            </div>
          </div>
          <div class="rc-purpose">${esc(def.purpose||'')}</div>
          <ul class="rc-resps">${resps}</ul>
        </div>`;
      }).join('')}
    </div>
    <div class="card">
      <div class="ct">Permission Matrix</div>
      <div class="tw" style="border:none;border-radius:0">
      <table>
        <thead><tr><th>Feature</th><th>Staff</th><th>Manager</th><th>HR</th><th>Admin</th></tr></thead>
        <tbody>
          ${[
            ['View own record','✅','✅','✅','✅'],
            ['View all employees','','✅','✅','✅'],
            ['Add / Edit employees','','','✅','✅'],
            ['Delete employees','','','✅','✅'],
            ['View departments','✅','✅','✅','✅'],
            ['Add / Edit departments','','','✅','✅'],
            ['Delete departments','','','','✅'],
            ['Submit promotion request','✅','✅','✅','✅'],
            ['Approve / Deny promotions','','','✅','✅'],
            ['Submit own leave','✅','✅','✅','✅'],
            ['Submit leave for any employee','','','✅','✅'],
            ['Approve / Deny leave','','','✅','✅'],
            ['View payroll / salary','','','✅','✅'],
            ['Edit salary','','','✅','✅'],
            ['View audit log','','','✅','✅'],
            ['Manage system users','','','','✅'],
            ['Change own password','✅','✅','✅','✅'],
          ].map(([feat,...perms])=>`<tr><td>${feat}</td>${perms.map(p=>`<td style="text-align:center">${p}</td>`).join('')}</tr>`).join('')}
        </tbody>
      </table>
      </div>
    </div>`;
}

// ── SYSTEM USERS
function rSU(){
  const tb=document.getElementById('sutb');
  tb.innerHTML=Object.entries(S.sysUsers).map(([u,d])=>{
    const def=S.roleDefs[d.role]||{};
    const roleBadge=`<span class="bdg" style="background:${esc(def.color||'#c9a84c')}22;color:${esc(def.color||'#c9a84c')};border:1px solid ${esc(def.color||'#c9a84c')}44">${esc(def.icon||'')} ${esc(RLAB[d.role]||d.role)}</span>`;
    return `<tr>
      <td style="font-family:var(--mo);font-size:12px">${esc(u)}</td>
      <td>${esc(d.full_name||'')}</td>
      <td>${roleBadge}</td>
      <td style="font-family:var(--mo);font-size:11px;color:var(--txm)">${esc(d.emp_id||'—')}</td>
      <td style="font-size:11px;color:var(--txm);font-family:var(--mo)">${esc(d.created||'')}</td>
      <td style="display:flex;gap:6px">
        <button class="btn bh sm" onclick="oEditSU('${esc(u)}')">✏️</button>
        <button class="btn br sm" onclick="deleteSU('${esc(u)}')">🗑</button>
      </td>
    </tr>`;
  }).join('');
}
function oAddSU(){
  document.getElementById('m-su-t').textContent='Add System User';
  document.getElementById('su-ou').value='';
  ['su-un','su-fn','su-eid','su-pw'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('su-rl').value='staff';
  updateRolePreview();
  openModal('m-su');
}
function oEditSU(u){
  document.getElementById('m-su-t').textContent='Edit System User';
  const d=S.sysUsers[u]||{};
  set('su-ou',u);set('su-un',u);set('su-fn',d.full_name);
  set('su-eid',d.emp_id);document.getElementById('su-pw').value='';
  document.getElementById('su-rl').value=d.role||'staff';
  updateRolePreview();
  openModal('m-su');
}
function updateRolePreview(){
  const role=document.getElementById('su-rl').value;
  const def=S.roleDefs[role]||{};
  document.getElementById('su-role-preview').innerHTML=`<strong style="color:${esc(def.color||'#c9a84c')}">${esc(def.icon||'')} ${esc(def.label||role)}</strong> — ${esc(def.purpose||'')}`;
}
async function saveSU(){
  const orig=v('su-ou'),uname=v('su-un'),fn=v('su-fn'),role=document.getElementById('su-rl').value,eid=v('su-eid'),pw=v('su-pw');
  if(!uname){toast('Username required.','error');return;}
  const body={username:uname,full_name:fn,role,emp_id:eid||null};
  if(pw)body.password=pw;
  const r=await api(orig?'PUT':'POST',orig?`/api/sysusers/${encodeURIComponent(orig)}`:'/api/sysusers',body);
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.sysUsers=d.system_users;cm('m-su');rSU();toast(orig?'User updated.':'User created.','success');
}
async function deleteSU(u){
  if(!confirm(`Delete system user "${u}"?`))return;
  const r=await api('DELETE',`/api/sysusers/${encodeURIComponent(u)}`);
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.sysUsers=d.system_users;rSU();toast('User deleted.','success');
}

// ── PROFILE
function rProfile(){
  document.getElementById('pf-name').textContent=S.user.full_name||'—';
  document.getElementById('pf-uname').textContent='@'+S.user.username;
  document.getElementById('pf-role-badge').textContent=(RLAB[S.user.role]||S.user.role).toUpperCase();
  if(S.user.photo)document.getElementById('pf-av').innerHTML=`<img src="${S.user.photo}" class="pav2">`;

  // linked employee
  const empEl=document.getElementById('pf-emp-link');
  if(S.user.emp_id&&S.employees[S.user.emp_id]){
    const e=S.employees[S.user.emp_id];
    empEl.innerHTML=`<div class="irow"><span class="ik">Employee ID</span><span class="iv" style="font-family:var(--mo);font-size:12px;cursor:pointer;color:var(--gold)" onclick="nav('employees');viewEmp('${esc(S.user.emp_id)}')">${esc(S.user.emp_id)} ↗</span></div><div class="irow"><span class="ik">Department</span><span class="iv">${esc(e.department||'—')}</span></div><div class="irow"><span class="ik">Occupation</span><span class="iv">${esc(e.occupation||'—')}</span></div>`;
  }else{empEl.innerHTML='<div style="font-size:12px;color:var(--txm);margin-top:4px">No employee record linked.</div>';}

  // role card
  const def=S.roleDefs[S.user.role]||{};
  document.getElementById('pf-role-card').innerHTML=`
    <div style="border-left:3px solid ${esc(def.color||'var(--gold)')};padding-left:12px;margin-bottom:10px">
      <div style="font-family:var(--bb);font-size:15px;letter-spacing:.04em;color:#fff">${esc(def.icon||'')} ${esc(def.label||S.user.role)}</div>
      <div style="font-size:11px;color:var(--txm);margin-top:2px;font-style:italic">${esc(def.purpose||'')}</div>
    </div>
    <ul class="rc-resps">${(def.responsibilities||[]).map(r=>`<li>${esc(r)}</li>`).join('')}</ul>`;
}

async function uploadPhoto(input){
  if(!input.files[0])return;
  const fr=new FileReader();
  fr.onload=async()=>{
    const r=await api('PUT','/api/profile',{photo:fr.result});
    const d=await r.json();
    if(!r.ok){toast(d.error,'error');return;}
    S.user.photo=fr.result;
    document.getElementById('pf-av').innerHTML=`<img src="${S.user.photo}" class="pav2">`;
    document.getElementById('hav').innerHTML=`<img src="${S.user.photo}" style="width:30px;height:30px;border-radius:50%;object-fit:cover;border:2px solid var(--gd)">`;
    toast('Photo updated.','success');
  };
  fr.readAsDataURL(input.files[0]);
}
async function changePassword(){
  const cur=v('pw-cur'),nw=v('pw-new'),cnf=v('pw-cnf');
  if(!cur||!nw||!cnf){toast('All fields required.','error');return;}
  if(nw!==cnf){toast('New passwords do not match.','error');return;}
  if(nw.length<6){toast('Password must be at least 6 characters.','error');return;}
  const r=await api('POST','/api/change-password',{current_password:cur,new_password:nw});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  ['pw-cur','pw-new','pw-cnf'].forEach(id=>set(id,''));
  toast('Password updated.','success');
}

// ── NOTIFICATIONS
function toggleNP(){S.npOpen=!S.npOpen;document.getElementById('np').classList.toggle('open',S.npOpen);}
function refreshNotifPanel(){
  const el=document.getElementById('npl');
  const visible=S.notifications.filter(n=>(n.roles||[]).includes(S.user.role));
  if(!visible.length){el.innerHTML='<div class="nem">No notifications.</div>';return;}
  el.innerHTML=visible.map(n=>{
    const unr=!(n.read_by||[]).includes(S.user.username);
    const ico=NOTIF_ICO[n.type]||'🔔';
    return `<div class="nit ${unr?'unr':''}" onclick="markRead('${esc(n.id)}',this)">
      <div class="nico">${ico}</div>
      <div><div class="nim">${esc(n.message)}</div><div class="nts">${esc(n.ts)}</div></div>
    </div>`;
  }).join('');
}
async function markRead(id,el){
  el.classList.remove('unr');
  await fetch('/api/notifications/read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  const n=S.notifications.find(n=>n.id===id);
  if(n){n.read_by=n.read_by||[];if(!n.read_by.includes(S.user.username))n.read_by.push(S.user.username);}
  refreshBadges();
}
async function markAllRead(){
  await fetch('/api/notifications/read-all',{method:'POST'});
  S.notifications.forEach(n=>{n.read_by=n.read_by||[];if(!n.read_by.includes(S.user.username))n.read_by.push(S.user.username);});
  refreshNotifPanel();refreshBadges();
  toast('All notifications marked read.','success');
}

// ── IMPORT
async function doImport(){
  const f=document.getElementById('impf').files[0];if(!f){toast('Select a file.','error');return;}
  const fd=new FormData();fd.append('file',f);
  const r=await fetch('/api/import',{method:'POST',body:fd});
  const d=await r.json();
  if(!r.ok){toast(d.error,'error');return;}
  S.employees=d.employees;cm('m-imp');rEmp();renderDash();
  toast(`Imported ${d.count} employees.`,'success');
}

// ── HELPERS
const api=(method,url,body)=>fetch(url,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});
function openModal(id){document.getElementById(id).classList.add('open');}
function cm(id){document.getElementById(id).classList.remove('open');}
function v(id){const el=document.getElementById(id);return el?el.value.trim():'';}
function set(id,val){const el=document.getElementById(id);if(el)el.value=val||'';}
function esc(s){return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function stCls(s){return s==='active'?'bgreen':s==='on_leave'?'bwarn':'bgray';}
function prCls(s){return s==='approved'?'bgreen':s==='denied'?'bred':'bwarn';}
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
    if lvl < 3:
        emps = {k: {f: v for f,v in e.items() if f not in ("salary","salary_currency")} for k,e in emps.items()}
    if lvl < 2:
        emp_id = data["system_users"].get(session["username"],{}).get("emp_id")
        emps = {k: v for k,v in emps.items() if k == emp_id}
    # Serialize role_definitions for JS consumption
    role_defs_clean = {}
    for k, v in ROLE_DEFINITIONS.items():
        role_defs_clean[k] = {
            "label": v["label"], "icon": v["icon"], "color": v["color"],
            "purpose": v["purpose"], "responsibilities": v["responsibilities"],
            "level": v["level"],
        }
    # Serialize dept_definitions
    dept_defs_clean = {}
    for name in data["departments"]:
        d = get_dept_definition(name)
        dept_defs_clean[name] = {
            "icon": d["icon"], "color": d["color"], "purpose": d["purpose"],
            "responsibilities": d["responsibilities"], "kpis": d["kpis"],
        }
    result = {
        "employees": emps,
        "departments": data["departments"],
        "audit_log": data.get("audit_log",[])[:100] if lvl>=3 else [],
        "notifications": data.get("notifications",[]),
        "leave_requests": data.get("leave_requests",[]),
        "meta": data.get("meta",{}),
        "role_definitions": role_defs_clean,
        "dept_definitions": dept_defs_clean,
    }
    if lvl >= 4:
        result["system_users"] = {u: {k: v2 for k,v2 in d.items() if k!="password_hash"}
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
        "full_name":        body.get("full_name","").strip(),
        "email":            body.get("email","").strip(),
        "phone":            body.get("phone","").strip(),
        "department":       body.get("department",""),
        "occupation":       body.get("occupation","").strip(),
        "role":             body.get("role","").strip(),
        "age":              body.get("age",""),
        "location":         body.get("location","").strip(),
        "employment_type":  body.get("employment_type","permanent"),
        "status":           body.get("status","active"),
        "contract_end":     body.get("contract_end",""),
        "start_date":       body.get("start_date",""),
        "salary":           body.get("salary",""),
        "salary_currency":  body.get("salary_currency","USD"),
        "manager_id":       body.get("manager_id","") or None,
        "emergency_contact":body.get("emergency_contact","").strip(),
        "skills":           body.get("skills",[]),
        "photo":            None,
        "promotion_requests": [],
        "date_added":       datetime.now().strftime("%Y-%m-%d"),
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
    fields = ["full_name","email","phone","department","occupation","role","age","location",
              "employment_type","status","contract_end","start_date","salary","salary_currency",
              "manager_id","emergency_contact","skills"]
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
    if name not in data["departments"]:
        return jsonify({"error": "Not found."}), 404
    body = request.get_json() or {}
    new_name = body.get("name", name).strip()
    dept = {"description": body.get("description", data["departments"][name].get("description","")),
            "head_id": body.get("head_id") or data["departments"][name].get("head_id")}
    if new_name != name:
        del data["departments"][name]
        for eid, emp in data["employees"].items():
            if emp.get("department") == name:
                emp["department"] = new_name
    data["departments"][new_name] = dept
    audit(data, session["username"], "Updated department", new_name)
    save_data(data)
    return jsonify({"name": new_name, "department": dept})

@app.route("/api/departments/<name>", methods=["DELETE"])
@role_required("admin")
def delete_department(name):
    data = load_data()
    if name not in data["departments"]:
        return jsonify({"error": "Not found."}), 404
    del data["departments"][name]
    audit(data, session["username"], "Deleted department", name)
    save_data(data)
    return jsonify({"ok": True})

# ─── PROMOTIONS
@app.route("/api/promotions", methods=["POST"])
@login_required
def add_promotion():
    data = load_data()
    body = request.get_json() or {}
    eid  = body.get("emp_id","").strip()
    rr   = body.get("requested_role","").strip()
    notes= body.get("notes","").strip()
    if not eid or not rr:
        return jsonify({"error": "emp_id and requested_role required."}), 400
    if eid not in data["employees"]:
        return jsonify({"error": "Employee not found."}), 404
    req = {
        "current_role":   data["employees"][eid].get("role",""),
        "requested_role": rr,
        "notes":          notes,
        "date":           datetime.now().strftime("%Y-%m-%d"),
        "status":         "pending",
        "submitted_by":   session["username"],
        "resolved_by":    None,
    }
    data["employees"][eid].setdefault("promotion_requests",[]).append(req)
    audit(data, session["username"], "Promotion request", eid, rr)
    notify(data, "warning", f"Promotion request for {data['employees'][eid].get('full_name',eid)}: {req['current_role']} → {rr}")
    save_data(data)
    return jsonify({"employees": data["employees"]})

@app.route("/api/promotions/<eid>/<int:idx>", methods=["PUT"])
@role_required("hr")
def resolve_promotion(eid, idx):
    data = load_data()
    if eid not in data["employees"]:
        return jsonify({"error": "Employee not found."}), 404
    reqs = data["employees"][eid].get("promotion_requests",[])
    if idx >= len(reqs):
        return jsonify({"error": "Request not found."}), 404
    resolution = (request.get_json() or {}).get("resolution","")
    if resolution not in ("approved","denied"):
        return jsonify({"error": "Invalid resolution."}), 400
    reqs[idx]["status"] = resolution
    reqs[idx]["resolved_by"] = session["username"]
    reqs[idx]["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    if resolution == "approved":
        data["employees"][eid]["role"] = reqs[idx]["requested_role"]
    audit(data, session["username"], f"Promotion {resolution}", eid, reqs[idx]["requested_role"])
    save_data(data)
    return jsonify({"employees": data["employees"]})

# ─── LEAVE
@app.route("/api/leave", methods=["POST"])
@login_required
def add_leave():
    data = load_data()
    body = request.get_json() or {}
    lvl  = ROLE_LEVEL.get(session["role"],1)
    emp_id = body.get("emp_id","").strip()
    if not emp_id:
        emp_id = data["system_users"].get(session["username"],{}).get("emp_id","")
    if not emp_id:
        return jsonify({"error": "No employee ID provided or linked."}), 400
    if lvl < 3 and emp_id != data["system_users"].get(session["username"],{}).get("emp_id",""):
        return jsonify({"error": "You can only submit leave for yourself."}), 403
    req = {
        "emp_id":       emp_id,
        "leave_type":   body.get("leave_type","annual"),
        "start_date":   body.get("start_date",""),
        "end_date":     body.get("end_date",""),
        "notes":        body.get("notes",""),
        "status":       "pending",
        "submitted_by": session["username"],
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "resolved_by":  None,
    }
    if not req["start_date"] or not req["end_date"]:
        return jsonify({"error": "Start and end dates required."}), 400
    data.setdefault("leave_requests",[]).append(req)
    name = data["employees"].get(emp_id,{}).get("full_name", emp_id)
    audit(data, session["username"], "Leave request", emp_id, req["leave_type"])
    notify(data, "info", f"Leave request: {name} — {req['leave_type']} ({req['start_date']} to {req['end_date']})")
    save_data(data)
    return jsonify({"leave_requests": data["leave_requests"]})

@app.route("/api/leave/<int:idx>", methods=["PUT"])
@role_required("hr")
def resolve_leave(idx):
    data = load_data()
    reqs = data.get("leave_requests",[])
    if idx >= len(reqs):
        return jsonify({"error": "Not found."}), 404
    resolution = (request.get_json() or {}).get("resolution","")
    if resolution not in ("approved","denied"):
        return jsonify({"error": "Invalid resolution."}), 400
    reqs[idx]["status"] = resolution
    reqs[idx]["resolved_by"] = session["username"]
    reqs[idx]["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    if resolution == "approved":
        eid = reqs[idx].get("emp_id","")
        if eid in data["employees"]:
            data["employees"][eid]["status"] = "on_leave"
    audit(data, session["username"], f"Leave {resolution}", reqs[idx].get("emp_id",""))
    save_data(data)
    return jsonify({"leave_requests": data["leave_requests"], "employees": data["employees"]})

# ─── PROFILE
@app.route("/api/profile", methods=["PUT"])
@login_required
def update_profile():
    data = load_data()
    body = request.get_json() or {}
    u = data["system_users"].get(session["username"])
    if not u: return jsonify({"error": "User not found."}), 404
    if "photo" in body:
        u["photo"] = body["photo"]
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/change-password", methods=["POST"])
@login_required
def change_password():
    data = load_data()
    body = request.get_json() or {}
    u = data["system_users"].get(session["username"])
    if not u: return jsonify({"error": "User not found."}), 404
    if not verify_pw(body.get("current_password",""), u.get("password_hash","")):
        return jsonify({"error": "Current password incorrect."}), 400
    new_pw = body.get("new_password","")
    if len(new_pw) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
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
    if len(pw) < 6: return jsonify({"error": "Password must be at least 6 characters."}), 400
    data["system_users"][uname] = {
        "password_hash": hash_pw(pw),
        "role": body.get("role","staff"),
        "full_name": body.get("full_name",""),
        "emp_id": body.get("emp_id") or None,
        "photo": None,
        "created": datetime.now().strftime("%Y-%m-%d"),
    }
    audit(data, session["username"], "Created system user", uname)
    save_data(data)
    su_clean = {u: {k: v for k,v in d.items() if k!="password_hash"} for u,d in data["system_users"].items()}
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
                     mimetype="text/csv", as_attachment=True, download_name="obsidian_employees.csv")

@app.route("/api/export/employees-excel")
@login_required
def export_emp_excel():
    data = load_data()
    b = export_excel_bytes(data["employees"])
    if not b: return jsonify({"error": "openpyxl not installed."}), 500
    return send_file(io.BytesIO(b),
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name="obsidian_employees.xlsx")

@app.route("/api/export/payroll-csv")
@role_required("hr")
def export_pay_csv():
    data = load_data()
    emps = {k: v for k,v in data["employees"].items() if v.get("salary")}
    return send_file(io.BytesIO(export_csv_bytes(emps)),
                     mimetype="text/csv", as_attachment=True, download_name="obsidian_payroll.csv")

@app.route("/api/export/payroll-excel")
@role_required("hr")
def export_pay_excel():
    data = load_data()
    emps = {k: v for k,v in data["employees"].items() if v.get("salary")}
    b = export_excel_bytes(emps)
    if not b: return jsonify({"error": "openpyxl not installed."}), 500
    return send_file(io.BytesIO(b),
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name="obsidian_payroll.xlsx")

@app.route("/api/export/audit-csv")
@role_required("hr")
def export_audit_csv():
    data = load_data()
    return send_file(io.BytesIO(export_audit_csv_bytes(data.get("audit_log",[]))),
                     mimetype="text/csv", as_attachment=True, download_name="obsidian_audit.csv")

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
            if isinstance(raw, dict):
                for eid, emp in raw.items():
                    emp.setdefault("promotion_requests",[])
                    data["employees"][eid] = emp; count += 1
            elif isinstance(raw, list):
                for emp in raw:
                    eid = emp.pop("id", None) or gen_emp_id(data)
                    emp.setdefault("promotion_requests",[])
                    data["employees"][eid] = emp; count += 1
        elif name.endswith(".csv"):
            text   = f.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                eid = row.pop("id", None) or gen_emp_id(data)
                row.setdefault("promotion_requests",[])
                if "skills" in row and isinstance(row["skills"], str):
                    row["skills"] = [s.strip() for s in row["skills"].split(",") if s.strip()]
                data["employees"][eid] = dict(row); count += 1
        else:
            return jsonify({"error": "Only .json and .csv supported."}), 400
        audit(data, session["username"], "Imported employees", f"count={count}")
        save_data(data)
        return jsonify({"count": count, "employees": data["employees"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── RUN
if __name__ == "__main__":
    print("\n  ╔═══════════════════════════════════════════════════╗")
    print("  ║     OBSIDIAN CORPORATION  —  Web Edition v3.0       ║")
    print("  ║     The Corporate Management Platform   ║")
    print("  ╠═══════════════════════════════════════════════════╣")
    print("  ║   http://localhost:5001                           ║")
    print("  ║   admin / admin123  |  hr_manager / hr123        ║")
    print("  ╚═══════════════════════════════════════════════════╝\n")
    app.run(debug=True, port=5001)
