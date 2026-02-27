# ============================================================================
# MOVING FORWARD WITH AI — app.py v2.1
# Architecture: Role pages + Comparison pages + Email capture + Tool reviews
# Deploy: GitHub → Render.com
# Fixed: domain updated to .com, mobile reveal animation fixed
# ============================================================================

import os, json, re, datetime
from data import TOOLS,
from flask import Flask, render_template_string, request, abort, Response, jsonify
from dotenv import load_dotenv

load_dotenv()

app        = Flask(__name__)
SITE_URL   = "https://www.movingforwardwithai.com"
SITE_NAME  = "Moving Forward With AI"

# ── helpers ──────────────────────────────────────────────────────────────────

def slugify(t):
    t = re.sub(r'&','-and-',str(t).lower())
    t = re.sub(r'[^a-z0-9\s-]','',t)
    return re.sub(r'[\s-]+',' ',t).strip().replace(' ','-')

def get_tool(slug):  return next((t for t in TOOLS if t['slug']==slug), None)
def get_role(slug):  return next((r for r in ROLES if r['slug']==slug), None)
def get_comp(slug):  return next((c for c in COMPARISONS if c['slug']==slug), None)
def stars(r):        return '★'*int(r)+('½' if r-int(r)>=.5 else '')+'☆'*(5-int(r)-(1 if r-int(r)>=.5 else 0))

def score_color(s):
    if s>=88: return 'var(--green)'
    if s>=78: return 'var(--cyan)'
    return 'var(--amber)'

def tool_schema(t):
    return json.dumps({"@context":"https://schema.org","@type":"SoftwareApplication",
        "name":t['name'],"description":t['tagline'],
        "applicationCategory":"BusinessApplication",
        "offers":{"@type":"Offer","priceCurrency":"GBP"},
        "aggregateRating":{"@type":"AggregateRating","ratingValue":str(t['rating']),
            "reviewCount":t['review_count'].replace('+','').replace(',',''),
            "bestRating":"5","worstRating":"1"}})

def bc_schema(crumbs):
    return json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[{"@type":"ListItem","position":i+1,"name":n,
        "item":(SITE_URL+u if not u.startswith('http') else u)}
        for i,(n,u) in enumerate(crumbs)]})


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,800&family=JetBrains+Mono:wght@300;400;500;700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

:root{
  --bg:#070b14; --bg2:#0b1120; --bg3:#101828; --bg4:#141e2e;
  --surf:#131c2e; --surf2:#1a2540; --surf3:#1f2d4a;
  --ink:#e2eaf8; --ink2:#b0bdd8; --ink3:#6b7a9a; --ink4:#3d4d6a;
  --cyan:#22d3ee; --cyan2:#67e8f9; --cyan-d:rgba(34,211,238,.10); --cyan-g:rgba(34,211,238,.18);
  --amber:#f59e0b; --amber2:#fbbf24; --amber-d:rgba(245,158,11,.10); --amber-g:rgba(245,158,11,.22);
  --green:#10b981; --green2:#34d399; --green-d:rgba(16,185,129,.10); --green-g:rgba(16,185,129,.20);
  --rose:#f43f5e; --rose-d:rgba(244,63,94,.10);
  --bdr:rgba(34,211,238,.07); --bdr2:rgba(34,211,238,.14); --bdr3:rgba(34,211,238,.28);
  --div:rgba(226,234,248,.05);
  --nav:rgba(7,11,20,.93);
  --r1:4px; --r2:8px; --r3:14px; --r4:20px; --rpill:99px;
  --ease:cubic-bezier(.16,1,.3,1); --spring:cubic-bezier(.34,1.56,.64,1);
  --sh1:0 2px 12px rgba(0,0,0,.7),0 0 0 1px var(--bdr);
  --sh2:0 4px 28px rgba(0,0,0,.8),0 0 0 1px var(--bdr2);
  --sh3:0 12px 56px rgba(0,0,0,.85),0 0 0 1px var(--bdr2);
  --shc:0 4px 24px rgba(34,211,238,.22),0 0 0 1px rgba(34,211,238,.18);
  --sha:0 4px 24px rgba(245,158,11,.28),0 0 0 1px rgba(245,158,11,.16);
}
.light{
  --bg:#f0f4fc; --bg2:#e8edf8; --bg3:#dfe5f4; --bg4:#d6ddef;
  --surf:#fff; --surf2:#f5f7fd; --surf3:#edf0fa;
  --ink:#080d1e; --ink2:#1e2b50; --ink3:#4a5880; --ink4:#8898bc;
  --cyan:#0891b2; --cyan2:#0e7490;
  --cyan-d:rgba(8,145,178,.07); --cyan-g:rgba(8,145,178,.14);
  --bdr:rgba(8,145,178,.09); --bdr2:rgba(8,145,178,.18); --bdr3:rgba(8,145,178,.32);
  --div:rgba(8,13,30,.06); --nav:rgba(240,244,252,.94);
  --sh1:0 2px 12px rgba(0,0,0,.06),0 0 0 1px var(--bdr);
  --sh2:0 4px 28px rgba(0,0,0,.08),0 0 0 1px var(--bdr2);
  --sh3:0 12px 56px rgba(0,0,0,.10),0 0 0 1px var(--bdr2);
}

*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif;
  font-size:15px;line-height:1.65;overflow-x:hidden;
  -webkit-font-smoothing:antialiased;transition:background .35s,color .35s}
a{text-decoration:none;color:inherit}
button{font-family:inherit;cursor:pointer}

body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:linear-gradient(rgba(34,211,238,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(34,211,238,.025) 1px,transparent 1px);
  background-size:52px 52px}

body::after{content:'';position:fixed;top:-200px;right:-200px;
  width:600px;height:600px;pointer-events:none;z-index:0;border-radius:50%;
  background:radial-gradient(circle,rgba(34,211,238,.04) 0%,transparent 65%)}

.ticker{position:relative;z-index:10;background:var(--surf);
  border-bottom:1px solid var(--bdr);padding:7px 0;overflow:hidden;white-space:nowrap}
.ticker-inner{display:inline-flex;animation:tick 60s linear infinite}
.ticker-inner span{font-family:'JetBrains Mono',monospace;font-size:.58rem;
  letter-spacing:.18em;text-transform:uppercase;color:var(--ink4);padding:0 20px}
.ticker-inner .hi{color:var(--cyan);opacity:.85}
.ticker-inner .dot{color:var(--cyan);opacity:.35;padding:0 4px}
@keyframes tick{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.ticker:hover .ticker-inner{animation-play-state:paused}

.nav{position:sticky;top:0;z-index:200;background:var(--nav);
  backdrop-filter:blur(28px) saturate(160%);
  border-bottom:1px solid var(--bdr);transition:box-shadow .3s,border-color .3s}
.nav.scrolled{box-shadow:0 4px 40px rgba(0,0,0,.65);border-bottom-color:var(--bdr2)}
.nav-in{max-width:1440px;margin:0 auto;padding:0 40px;
  display:flex;align-items:center;height:58px;gap:6px}
.nav-logo{font-family:'Bricolage Grotesque',sans-serif;font-size:.95rem;
  font-weight:800;letter-spacing:-.02em;color:var(--ink);flex-shrink:0;
  margin-right:18px;display:flex;align-items:center;gap:6px;
  transition:opacity .2s;white-space:nowrap}
.nav-logo:hover{opacity:.8}
.logo-mark{display:flex;align-items:center;gap:3px}
.logo-arrow{color:var(--cyan);font-size:1.1rem;animation:nudge 3s ease-in-out infinite}
@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(3px)}}
.logo-text{color:var(--ink)}
.logo-ai{color:var(--cyan)}
.nav-links{display:flex;align-items:center;gap:1px;flex:1}
.nav-links>a,.nav-drop-btn{
  font-size:.81rem;font-weight:500;color:var(--ink3);
  padding:5px 10px;border-radius:var(--r1);
  transition:color .15s,background .15s;letter-spacing:-.01em;
  background:none;border:none;display:flex;align-items:center;gap:4px}
.nav-links>a:hover,.nav-drop-btn:hover{color:var(--ink);background:var(--cyan-d)}
.nav-drop{position:relative}
.drop-chevron{width:10px;height:10px;stroke:currentColor;fill:none;stroke-width:2;
  transition:transform .2s}
.nav-drop.open .drop-chevron{transform:rotate(180deg)}
.drop-menu{display:none;position:absolute;top:calc(100% + 8px);left:0;
  background:var(--surf2);border:1px solid var(--bdr2);border-radius:var(--r3);
  padding:6px;min-width:200px;box-shadow:var(--sh3);z-index:300}
.nav-drop.open .drop-menu{display:block;animation:dropIn .15s var(--ease)}
@keyframes dropIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
.drop-menu a{display:flex;align-items:center;gap:9px;padding:8px 12px;
  border-radius:var(--r1);font-size:.81rem;color:var(--ink3);transition:all .13s}
.drop-menu a:hover{background:var(--cyan-d);color:var(--cyan2);padding-left:16px}
.drop-menu .dm-icon{font-size:1rem;flex-shrink:0}
.nav-search{position:relative;display:flex;align-items:center}
.nav-search-ico{position:absolute;left:10px;width:13px;height:13px;
  stroke:var(--ink4);fill:none;stroke-width:1.8;pointer-events:none}
.nav-search input{background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--rpill);padding:6px 14px 6px 30px;
  font-family:'JetBrains Mono',monospace;font-size:.74rem;color:var(--ink);
  width:175px;outline:none;transition:all .25s var(--ease)}
.nav-search input:focus{width:230px;border-color:var(--cyan);
  box-shadow:0 0 0 3px var(--cyan-d);background:var(--surf2)}
.nav-search input::placeholder{color:var(--ink4)}
.nav-right{display:flex;align-items:center;gap:5px;flex-shrink:0}
.nav-icon{width:33px;height:33px;border-radius:var(--r1);border:1px solid var(--bdr);
  background:var(--surf);display:flex;align-items:center;justify-content:center;
  transition:all .18s;flex-shrink:0}
.nav-icon:hover{background:var(--cyan-d);border-color:rgba(34,211,238,.25)}
.nav-icon svg{width:14px;height:14px;stroke:var(--ink3);fill:none;stroke-width:1.8}
#hbg{display:none;flex-direction:column;justify-content:center;align-items:center;
  gap:5px;width:33px;height:33px;border:1px solid var(--bdr);
  border-radius:var(--r1);background:var(--surf)}
#hbg span{display:block;width:15px;height:1.5px;background:var(--ink);
  border-radius:2px;transition:all .24s var(--ease);transform-origin:center}
#hbg.open span:nth-child(1){transform:translateY(6.5px) rotate(45deg)}
#hbg.open span:nth-child(2){opacity:0;transform:scaleX(0)}
#hbg.open span:nth-child(3){transform:translateY(-6.5px) rotate(-45deg)}

#mob{display:none;position:fixed;inset:0;background:var(--bg);
  z-index:190;overflow-y:auto;padding:74px 20px 44px;flex-direction:column}
#mob.open{display:flex;animation:mobIn .26s var(--ease)}
@keyframes mobIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
.mob-links{display:flex;flex-direction:column;gap:0;margin-bottom:24px}
.mob-link{font-family:'Bricolage Grotesque',sans-serif;font-size:2.2rem;font-weight:800;
  color:var(--ink);padding:9px 0;border-bottom:1px solid var(--div);
  transition:color .18s,padding-left .18s;display:block;letter-spacing:-.03em}
.mob-link:hover{color:var(--cyan);padding-left:6px}
.mob-sec{margin-bottom:20px}
.mob-label{font-family:'JetBrains Mono',monospace;font-size:.56rem;
  letter-spacing:.2em;text-transform:uppercase;color:var(--cyan);
  margin-bottom:10px;display:flex;align-items:center;gap:9px}
.mob-label::before{content:'→'}
.mob-label::after{content:'';flex:1;height:1px;background:var(--cyan-g)}
.mob-pills{display:flex;flex-wrap:wrap;gap:6px}
.mob-pill{background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--rpill);padding:7px 15px;font-size:.79rem;
  color:var(--ink3);transition:all .18s}
.mob-pill:hover{background:var(--cyan-d);border-color:rgba(34,211,238,.25);color:var(--cyan2)}

.page{max-width:1440px;margin:0 auto;padding:0 40px;position:relative;z-index:1}

.hero{padding:clamp(60px,9vw,120px) 0 clamp(48px,6vw,80px);
  display:grid;grid-template-columns:1fr 420px;gap:clamp(48px,7vw,96px);
  align-items:center;position:relative}
.hero::before{content:'';position:absolute;top:0;left:-40px;right:-40px;
  height:100%;background:radial-gradient(ellipse at 20% 50%,rgba(34,211,238,.04) 0%,transparent 55%);
  pointer-events:none}
.hero-kicker{display:inline-flex;align-items:center;gap:8px;margin-bottom:20px;
  font-family:'JetBrains Mono',monospace;font-size:.6rem;font-weight:400;
  letter-spacing:.18em;text-transform:uppercase;color:var(--cyan)}
.hero-kicker::before{content:'→';font-size:.7rem}
.hero-h1{font-family:'Bricolage Grotesque',sans-serif;
  font-size:clamp(2.8rem,6vw,5.4rem);font-weight:800;
  line-height:.95;letter-spacing:-.04em;color:var(--ink);margin-bottom:20px;
  animation:rise .8s var(--ease) both}
.hero-h1 em{font-style:normal;color:var(--cyan)}
.hero-h1 .sub{display:block;font-size:.5em;font-weight:500;
  color:var(--ink3);margin-top:10px;letter-spacing:-.01em;line-height:1.3}
@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
.hero-sub{font-size:.97rem;line-height:1.78;color:var(--ink3);max-width:460px;
  margin-bottom:28px;font-weight:300;animation:rise .8s .08s var(--ease) both}

.role-selector{margin-bottom:32px;animation:rise .8s .14s var(--ease) both}
.role-label{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ink4);margin-bottom:10px}
.role-chips{display:flex;flex-wrap:wrap;gap:7px}
.role-chip{display:inline-flex;align-items:center;gap:7px;
  background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--rpill);padding:8px 16px;
  font-size:.83rem;font-weight:500;color:var(--ink3);
  transition:all .2s var(--ease);letter-spacing:-.01em}
.role-chip:hover{background:var(--cyan-d);border-color:rgba(34,211,238,.25);
  color:var(--cyan2);transform:translateY(-1px)}
.role-chip .chip-icon{font-size:1rem}

.hero-acts{display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  animation:rise .8s .2s var(--ease) both}

.hero-panel{background:var(--surf);border:1px solid var(--bdr2);
  border-radius:var(--r4);overflow:hidden;box-shadow:var(--sh2);
  position:relative;animation:rise .8s .18s var(--ease) both}
.hero-panel::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--cyan),var(--amber))}
.panel-head{padding:16px 18px 12px;border-bottom:1px solid var(--div);
  display:flex;align-items:center;justify-content:space-between}
.panel-title{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--cyan);letter-spacing:.14em;text-transform:uppercase}
.panel-live{display:inline-flex;align-items:center;gap:5px;
  background:var(--green-d);border:1px solid var(--green-g);
  border-radius:var(--rpill);padding:2px 9px;
  font-family:'JetBrains Mono',monospace;font-size:.54rem;
  color:var(--green);letter-spacing:.08em;text-transform:uppercase}
.panel-live::before{content:'';width:5px;height:5px;border-radius:50%;
  background:var(--green);animation:blink 1.8s ease-in-out infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}
.panel-tools{padding:10px}
.ptool{display:flex;align-items:center;gap:12px;padding:10px 10px;
  border-radius:var(--r2);transition:background .16s;cursor:pointer;
  text-decoration:none;color:inherit}
.ptool:hover{background:var(--bg2)}
.ptool-rank{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--ink4);width:16px;text-align:center;flex-shrink:0}
.ptool-name{font-family:'Bricolage Grotesque',sans-serif;font-size:.9rem;
  font-weight:600;color:var(--ink2);letter-spacing:-.02em;flex:1}
.ptool-cat{font-family:'JetBrains Mono',monospace;font-size:.56rem;
  color:var(--ink4);letter-spacing:.06em;text-transform:uppercase}
.ptool-score{font-family:'JetBrains Mono',monospace;font-size:.68rem;
  font-weight:700;padding:2px 8px;border-radius:var(--r1);flex-shrink:0}
.ps-hi{background:var(--green-d);border:1px solid var(--green-g);color:var(--green)}
.ps-md{background:var(--cyan-d);border:1px solid rgba(34,211,238,.18);color:var(--cyan)}
.panel-cta{display:block;margin:6px 10px 10px;padding:11px;
  background:linear-gradient(135deg,rgba(34,211,238,.08),rgba(245,158,11,.06));
  border:1px solid var(--bdr2);border-radius:var(--r2);
  font-family:'JetBrains Mono',monospace;font-size:.68rem;
  color:var(--cyan);text-align:center;letter-spacing:.08em;text-transform:uppercase;
  transition:all .2s}
.panel-cta:hover{background:var(--cyan-d);border-color:rgba(34,211,238,.3)}

.stats-bar{border-top:1px solid var(--div);margin-top:clamp(32px,4vw,52px);
  padding-top:clamp(24px,3vw,36px);display:flex;gap:36px;
  animation:rise .8s .28s var(--ease) both}
.stat-num{font-family:'Bricolage Grotesque',sans-serif;
  font-size:2.2rem;font-weight:800;letter-spacing:-.05em;
  color:var(--ink);line-height:1}
.stat-num em{font-style:normal;color:var(--cyan)}
.stat-lbl{font-family:'JetBrains Mono',monospace;font-size:.56rem;
  color:var(--ink4);letter-spacing:.1em;text-transform:uppercase;margin-top:5px}

.affil{background:var(--surf);border-top:1px solid var(--bdr);
  border-bottom:1px solid var(--bdr)}
.affil-in{max-width:1440px;margin:0 auto;padding:10px 40px;
  display:flex;align-items:center;gap:10px;
  font-family:'JetBrains Mono',monospace;font-size:.66rem;color:var(--ink4)}
.affil-in strong{color:var(--ink3);font-weight:500}
.affil-in a{color:var(--cyan)}
.affil-ico{width:13px;height:13px;stroke:var(--cyan);fill:none;stroke-width:2;flex-shrink:0}

.sec{padding:clamp(56px,7vw,88px) 0 0}
.sec-top{display:flex;align-items:flex-end;justify-content:space-between;
  gap:16px;margin-bottom:28px}
.sec-kicker{font-family:'JetBrains Mono',monospace;font-size:.58rem;
  letter-spacing:.18em;text-transform:uppercase;color:var(--cyan);
  margin-bottom:9px;display:flex;align-items:center;gap:7px}
.sec-kicker::before{content:'→'}
.sec-h2{font-family:'Bricolage Grotesque',sans-serif;
  font-size:clamp(1.7rem,3.2vw,2.6rem);font-weight:800;
  letter-spacing:-.04em;color:var(--ink);line-height:1}
.sec-h2 em{font-style:normal;color:var(--cyan)}
.sec-more{font-family:'JetBrains Mono',monospace;font-size:.66rem;color:var(--cyan);
  display:flex;align-items:center;gap:6px;letter-spacing:.06em;text-transform:uppercase;
  border-bottom:1px solid var(--cyan-g);padding-bottom:2px;
  transition:gap .2s,border-color .2s;white-space:nowrap;flex-shrink:0}
.sec-more:hover{border-color:var(--cyan);gap:10px}

.roles-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.role-card{background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--r3);padding:22px;
  display:flex;flex-direction:column;gap:10px;
  transition:transform .35s var(--spring),box-shadow .35s,border-color .25s;
  position:relative;overflow:hidden}
.role-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--cyan),transparent);
  opacity:0;transition:opacity .3s}
.role-card:hover{transform:translateY(-5px);box-shadow:var(--sh2);border-color:var(--bdr2)}
.role-card:hover::after{opacity:1}
.rc-icon{font-size:1.8rem;line-height:1}
.rc-name{font-family:'Bricolage Grotesque',sans-serif;font-size:1.05rem;
  font-weight:700;letter-spacing:-.03em;color:var(--ink)}
.rc-desc{font-size:.84rem;color:var(--ink3);line-height:1.6;font-weight:300;flex:1}
.rc-count{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--cyan);letter-spacing:.08em;text-transform:uppercase;
  display:flex;align-items:center;gap:5px}
.rc-count::before{content:'→'}
.rc-arrow{margin-top:4px;font-family:'JetBrains Mono',monospace;font-size:.66rem;
  color:var(--cyan);display:flex;align-items:center;gap:5px;
  letter-spacing:.06em;text-transform:uppercase;
  border-bottom:1px solid var(--cyan-g);padding-bottom:2px;
  transition:gap .2s;width:fit-content}
.role-card:hover .rc-arrow{gap:9px}

.tools-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:14px}
.tool-card{background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--r4);overflow:hidden;display:flex;flex-direction:column;
  position:relative;transition:transform .4s var(--spring),box-shadow .4s,border-color .28s;
  will-change:transform}
.tool-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--cyan),transparent);
  opacity:0;transition:opacity .3s;z-index:2}
.tool-card:hover{transform:translateY(-6px);
  box-shadow:0 16px 60px rgba(0,0,0,.8),0 0 0 1px var(--bdr3);
  border-color:var(--bdr3)}
.tool-card:hover::before{opacity:1}
.tc-top{padding:20px 20px 0}
.tc-meta{display:flex;align-items:center;justify-content:space-between;margin-bottom:13px}
.tc-cat{font-family:'JetBrains Mono',monospace;font-size:.56rem;
  letter-spacing:.1em;text-transform:uppercase;color:var(--cyan);
  display:flex;align-items:center;gap:5px}
.tc-cat::before{content:'//'}
.tc-score{border-radius:var(--r1);padding:3px 9px;
  font-family:'JetBrains Mono',monospace;font-size:.64rem;font-weight:700}
.tc-name{font-family:'Bricolage Grotesque',sans-serif;font-size:1.28rem;
  font-weight:700;letter-spacing:-.03em;color:var(--ink);
  display:block;margin-bottom:6px;transition:color .16s}
.tc-name:hover{color:var(--cyan)}
.tc-tagline{font-size:.83rem;line-height:1.6;color:var(--ink3);
  font-weight:300;margin-bottom:14px}
.tc-badges{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:16px}
.badge{display:inline-flex;align-items:center;gap:3px;
  border-radius:var(--rpill);padding:3px 9px;
  font-family:'JetBrains Mono',monospace;font-size:.56rem;
  letter-spacing:.06em;text-transform:uppercase}
.b-free{background:var(--green-d);border:1px solid var(--green-g);color:var(--green)}
.b-trial{background:var(--cyan-d);border:1px solid rgba(34,211,238,.18);color:var(--cyan)}
.b-paid{background:var(--amber-d);border:1px solid var(--amber-g);color:var(--amber)}
.b-top{background:var(--rose-d);border:1px solid rgba(244,63,94,.2);color:var(--rose)}
.tc-div{height:1px;background:var(--div);margin:0 20px 14px}
.tc-bot{padding:0 20px 18px;display:flex;flex-direction:column;gap:8px;flex:1;justify-content:flex-end}
.tc-price-row{display:flex;align-items:baseline;gap:7px;margin-bottom:3px}
.tc-price{font-family:'Bricolage Grotesque',sans-serif;font-size:1.05rem;
  font-weight:700;color:var(--ink);letter-spacing:-.02em}
.tc-model{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--ink4);letter-spacing:.04em;text-transform:uppercase}
.tc-rating{display:flex;align-items:center;gap:7px;margin-bottom:8px;
  font-family:'JetBrains Mono',monospace;font-size:.63rem;color:var(--ink4)}
.tc-stars{color:var(--amber);font-size:.78rem;letter-spacing:-.04em}
.btn-try{display:flex;align-items:center;justify-content:center;gap:7px;
  background:var(--cyan);color:#070b14;padding:11px 16px;
  border-radius:var(--r2);font-family:'JetBrains Mono',monospace;
  font-size:.74rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  border:none;transition:background .18s,transform .18s,box-shadow .18s;
  box-shadow:var(--shc)}
.btn-try:hover{background:var(--cyan2);transform:translateY(-1px);
  box-shadow:0 8px 28px rgba(34,211,238,.32)}
.btn-try svg{width:11px;height:11px;stroke:currentColor;fill:none;stroke-width:2.5;flex-shrink:0}
.btn-review{display:block;text-align:center;
  font-family:'JetBrains Mono',monospace;font-size:.64rem;color:var(--ink4);
  padding:7px;border:1px solid var(--bdr);border-radius:var(--r1);
  transition:all .18s;letter-spacing:.06em;text-transform:uppercase}
.btn-review:hover{color:var(--cyan);border-color:rgba(34,211,238,.25);background:var(--cyan-d)}

.comp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:14px}
.comp-card{background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--r3);padding:22px;
  display:flex;flex-direction:column;gap:14px;
  transition:transform .35s var(--spring),box-shadow .35s,border-color .25s}
.comp-card:hover{transform:translateY(-4px);box-shadow:var(--sh2);border-color:var(--bdr2)}
.comp-vs{display:flex;align-items:center;gap:10px}
.comp-tool-name{font-family:'Bricolage Grotesque',sans-serif;font-size:1rem;
  font-weight:700;color:var(--ink);letter-spacing:-.03em}
.comp-vs-sep{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--ink4);letter-spacing:.1em;background:var(--bg2);
  border:1px solid var(--bdr);border-radius:var(--rpill);padding:2px 8px;flex-shrink:0}
.comp-desc{font-size:.85rem;color:var(--ink3);line-height:1.65;font-weight:300;flex:1}
.comp-cta{font-family:'JetBrains Mono',monospace;font-size:.66rem;
  color:var(--amber);display:inline-flex;align-items:center;gap:5px;
  letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid var(--amber-g);
  padding-bottom:2px;transition:gap .2s;width:fit-content}
.comp-card:hover .comp-cta{gap:9px}

.email-sec{position:relative;z-index:1;
  background:linear-gradient(135deg,var(--surf) 0%,var(--bg2) 100%);
  border-top:1px solid var(--bdr);border-bottom:1px solid var(--bdr);
  padding:clamp(52px,7vw,88px) 0}
.email-inner{max-width:1440px;margin:0 auto;padding:0 40px;
  display:grid;grid-template-columns:1fr 1fr;gap:clamp(48px,7vw,96px);
  align-items:center}
.email-kicker{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  letter-spacing:.18em;text-transform:uppercase;color:var(--amber);
  margin-bottom:12px;display:flex;align-items:center;gap:7px}
.email-kicker::before{content:'→'}
.email-h2{font-family:'Bricolage Grotesque',sans-serif;
  font-size:clamp(1.7rem,3vw,2.6rem);font-weight:800;
  letter-spacing:-.04em;color:var(--ink);margin-bottom:14px;line-height:1.05}
.email-h2 em{font-style:normal;color:var(--amber)}
.email-sub{font-size:.93rem;line-height:1.75;color:var(--ink3);
  font-weight:300;margin-bottom:24px}
.email-form{display:flex;gap:8px;flex-wrap:wrap}
.email-input{flex:1;min-width:200px;background:var(--bg);
  border:1px solid var(--bdr2);border-radius:var(--r2);
  padding:12px 18px;color:var(--ink);
  font-family:'DM Sans',sans-serif;font-size:.88rem;outline:none;
  transition:border-color .2s,box-shadow .2s}
.email-input:focus{border-color:var(--amber);box-shadow:0 0 0 3px var(--amber-d)}
.email-input::placeholder{color:var(--ink4)}
.btn-email{background:var(--amber);color:#070b14;border:none;
  border-radius:var(--r2);padding:12px 22px;
  font-family:'JetBrains Mono',monospace;font-size:.78rem;font-weight:700;
  letter-spacing:.06em;text-transform:uppercase;
  transition:background .18s,transform .18s,box-shadow .18s;
  box-shadow:var(--sha);white-space:nowrap}
.btn-email:hover{background:var(--amber2);transform:translateY(-1px);
  box-shadow:0 8px 28px rgba(245,158,11,.35)}
.email-items{display:flex;flex-direction:column;gap:8px;margin-top:16px}
.email-item{display:flex;align-items:center;gap:9px;
  font-size:.84rem;color:var(--ink3);font-weight:300}
.email-item::before{content:'✓';color:var(--green);font-size:.8rem;
  font-weight:700;flex-shrink:0}
.email-notice{font-family:'JetBrains Mono',monospace;font-size:.58rem;
  color:var(--ink4);margin-top:12px;letter-spacing:.02em}
.email-card{background:var(--surf2);border:1px solid var(--bdr2);
  border-radius:var(--r3);padding:28px;position:relative;overflow:hidden}
.email-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--amber),var(--cyan))}
.email-card-title{font-family:'Bricolage Grotesque',sans-serif;font-size:1.1rem;
  font-weight:700;color:var(--ink);margin-bottom:4px;letter-spacing:-.03em}
.email-card-sub{font-family:'JetBrains Mono',monospace;font-size:.62rem;
  color:var(--amber);letter-spacing:.08em;text-transform:uppercase;margin-bottom:16px}
.email-card-items{display:flex;flex-direction:column;gap:10px}
.eci{display:flex;align-items:flex-start;gap:10px;
  font-size:.85rem;color:var(--ink3);line-height:1.55;font-weight:300}
.eci-num{font-family:'JetBrains Mono',monospace;font-size:.6rem;font-weight:700;
  color:var(--amber);background:var(--amber-d);border:1px solid var(--amber-g);
  border-radius:var(--r1);padding:2px 7px;flex-shrink:0;margin-top:2px}

.rd-header{padding:clamp(52px,7vw,88px) 0 0}
.rd-breadcrumb{display:flex;align-items:center;gap:7px;
  font-family:'JetBrains Mono',monospace;font-size:.63rem;color:var(--ink4);
  margin-bottom:20px;flex-wrap:wrap;letter-spacing:.04em}
.rd-breadcrumb a{color:var(--cyan);transition:opacity .18s}
.rd-breadcrumb a:hover{opacity:.7}
.rd-breadcrumb span{opacity:.3}
.rd-icon{font-size:2.6rem;margin-bottom:14px;display:block}
.rd-h1{font-family:'Bricolage Grotesque',sans-serif;
  font-size:clamp(2.2rem,5vw,4rem);font-weight:800;
  letter-spacing:-.05em;color:var(--ink);margin-bottom:12px;line-height:1}
.rd-h1 em{font-style:normal;color:var(--cyan)}
.rd-sub{font-size:1rem;line-height:1.75;color:var(--ink3);
  max-width:560px;font-weight:300;margin-bottom:28px}
.rd-pain{background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--r3);padding:22px 24px;margin-bottom:32px}
.rd-pain-title{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--ink4);letter-spacing:.14em;text-transform:uppercase;margin-bottom:12px}
.rd-pain-list{display:flex;flex-direction:column;gap:8px}
.rd-pain-item{display:flex;align-items:flex-start;gap:10px;
  font-size:.87rem;color:var(--ink3);line-height:1.55;font-weight:300}
.rd-pain-item::before{content:'✗';color:var(--rose);flex-shrink:0;
  font-weight:700;font-size:.8rem;margin-top:2px}
.rd-how{background:linear-gradient(135deg,var(--cyan-d),rgba(34,211,238,.04));
  border:1px solid rgba(34,211,238,.16);border-radius:var(--r3);
  padding:22px 24px;margin-bottom:32px}
.rd-how-title{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--cyan);letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px}
.rd-how-text{font-size:.92rem;color:var(--ink2);line-height:1.75;font-weight:300}
.rd-top-pick{background:var(--surf);border:1px solid var(--bdr2);
  border-radius:var(--r3);padding:22px;margin-bottom:16px;
  display:flex;align-items:center;gap:16px}
.rd-top-badge{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  background:var(--green-d);border:1px solid var(--green-g);color:var(--green);
  border-radius:var(--rpill);padding:3px 10px;letter-spacing:.08em;
  text-transform:uppercase;white-space:nowrap;flex-shrink:0}

.cd-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:28px}
.cd-tool{background:var(--surf);border:1px solid var(--bdr2);
  border-radius:var(--r3);padding:24px;position:relative;overflow:hidden}
.cd-tool.winner{border-color:var(--green-g);
  box-shadow:0 0 0 1px var(--green-g),0 4px 24px rgba(16,185,129,.08)}
.cd-tool.winner::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:var(--green)}
.cd-winner-badge{position:absolute;top:14px;right:14px;
  background:var(--green-d);border:1px solid var(--green-g);
  border-radius:var(--rpill);padding:3px 10px;
  font-family:'JetBrains Mono',monospace;font-size:.56rem;
  color:var(--green);letter-spacing:.08em;text-transform:uppercase}
.cd-tool-name{font-family:'Bricolage Grotesque',sans-serif;font-size:1.4rem;
  font-weight:800;color:var(--ink);letter-spacing:-.04em;margin-bottom:6px}
.cd-tool-score{font-family:'Bricolage Grotesque',sans-serif;font-size:2.4rem;
  font-weight:800;letter-spacing:-.06em;line-height:1;margin-bottom:6px}
.cd-tool-tagline{font-size:.86rem;color:var(--ink3);line-height:1.6;
  font-weight:300;margin-bottom:14px}
.cd-verdict{font-size:.88rem;color:var(--ink3);line-height:1.7;font-weight:300}
.cd-winner-reason{background:var(--green-d);border:1px solid var(--green-g);
  border-radius:var(--r2);padding:16px 18px;margin-bottom:28px}
.cd-wr-title{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--green);letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px}
.cd-wr-text{font-size:.88rem;color:var(--ink2);line-height:1.7;font-weight:300}
.compare-table{width:100%;border-collapse:collapse;
  background:var(--surf);border-radius:var(--r3);overflow:hidden;
  border:1px solid var(--bdr2);margin-bottom:28px}
.compare-table th{background:var(--surf2);padding:12px 18px;text-align:left;
  font-family:'JetBrains Mono',monospace;font-size:.6rem;font-weight:500;
  color:var(--cyan);border-bottom:1px solid var(--bdr2);
  letter-spacing:.1em;text-transform:uppercase}
.compare-table td{padding:12px 18px;border-bottom:1px solid var(--div);
  color:var(--ink3);font-size:.86rem;vertical-align:middle}
.compare-table tr:last-child td{border-bottom:none}
.compare-table tr:hover td{background:var(--bg2)}
.tick{color:var(--green)} .cross{color:var(--rose)}

.blog-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.blog-card{background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--r3);overflow:hidden;display:flex;flex-direction:column;
  transition:transform .3s var(--spring),box-shadow .3s,border-color .25s;
  position:relative;color:inherit}
.blog-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--amber),transparent);
  opacity:0;transition:opacity .28s;z-index:2}
.blog-card:hover{transform:translateY(-4px);box-shadow:var(--sh2);border-color:var(--bdr2)}
.blog-card:hover::before{opacity:1}
.blog-card-body{padding:22px;display:flex;flex-direction:column;gap:8px;flex:1}
.blog-date{font-family:'JetBrains Mono',monospace;font-size:.58rem;
  color:var(--cyan);letter-spacing:.12em;text-transform:uppercase;
  display:flex;align-items:center;gap:6px}
.blog-date::before{content:'//'}
.blog-title{font-family:'Bricolage Grotesque',sans-serif;font-size:1.12rem;
  font-weight:700;line-height:1.25;letter-spacing:-.03em;color:var(--ink)}
.blog-desc{font-size:.84rem;line-height:1.65;color:var(--ink3);flex:1;font-weight:300}
.blog-more{font-family:'JetBrains Mono',monospace;font-size:.64rem;
  color:var(--amber);display:inline-flex;align-items:center;gap:5px;
  margin-top:2px;transition:gap .2s;letter-spacing:.06em;text-transform:uppercase}
.blog-card:hover .blog-more{gap:9px}

.td-hero{padding:clamp(48px,6vw,80px) 0 0}
.td-bc{display:flex;align-items:center;gap:7px;
  font-family:'JetBrains Mono',monospace;font-size:.63rem;color:var(--ink4);
  margin-bottom:18px;flex-wrap:wrap;letter-spacing:.04em}
.td-bc a{color:var(--cyan);transition:opacity .18s}
.td-bc a:hover{opacity:.7}
.td-bc span{opacity:.3}
.td-header{background:var(--surf);border:1px solid var(--bdr2);
  border-radius:var(--r4);padding:32px;margin-bottom:28px;
  position:relative;overflow:hidden;box-shadow:var(--sh1)}
.td-header::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--cyan),var(--amber))}
.td-header-in{display:grid;grid-template-columns:1fr auto;gap:28px;align-items:start}
.td-cat{font-family:'JetBrains Mono',monospace;font-size:.58rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--cyan);
  margin-bottom:9px;display:flex;align-items:center;gap:6px}
.td-cat::before{content:'//'}
.td-h1{font-family:'Bricolage Grotesque',sans-serif;
  font-size:clamp(2rem,4.5vw,3.4rem);font-weight:800;
  letter-spacing:-.05em;color:var(--ink);line-height:1;margin-bottom:9px}
.td-tagline{font-size:.97rem;color:var(--ink3);line-height:1.7;
  font-weight:300;margin-bottom:18px}
.td-rating-row{display:flex;align-items:center;gap:11px;flex-wrap:wrap;margin-bottom:18px}
.td-stars{color:var(--amber);font-size:1rem;letter-spacing:-.04em}
.td-rating-txt{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--ink3)}
.td-score-block{text-align:right;flex-shrink:0}
.td-score-num{font-family:'Bricolage Grotesque',sans-serif;
  font-size:3.6rem;font-weight:800;letter-spacing:-.06em;line-height:1}
.td-score-lbl{font-family:'JetBrains Mono',monospace;font-size:.58rem;
  color:var(--ink4);letter-spacing:.1em;text-transform:uppercase;margin-top:4px}
.td-body{display:grid;grid-template-columns:1fr 280px;gap:20px;align-items:start}
.td-sec{background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--r3);padding:22px;margin-bottom:14px;box-shadow:var(--sh1)}
.td-sec-title{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--cyan);
  margin-bottom:14px;display:flex;align-items:center;gap:6px}
.td-sec-title::before{content:'//'}
.verdict-text{font-size:.94rem;line-height:1.8;color:var(--ink2);font-weight:300}
.pros-list,.cons-list{list-style:none;display:flex;flex-direction:column;gap:8px}
.pros-list li,.cons-list li{font-size:.86rem;line-height:1.6;color:var(--ink3);
  padding-left:20px;position:relative;font-weight:300}
.pros-list li::before{content:'✓';position:absolute;left:0;color:var(--green);font-weight:700}
.cons-list li::before{content:'✗';position:absolute;left:0;color:var(--rose);font-weight:700}
.td-price-box{background:var(--bg2);border:1px solid var(--bdr);
  border-radius:var(--r2);padding:18px;margin-bottom:12px}
.td-price{font-family:'Bricolage Grotesque',sans-serif;font-size:2rem;
  font-weight:800;color:var(--ink);letter-spacing:-.04em;line-height:1}
.td-price-note{font-family:'JetBrains Mono',monospace;font-size:.62rem;
  color:var(--ink4);letter-spacing:.06em;text-transform:uppercase;margin-top:5px}
.btn-td-try{display:flex;align-items:center;justify-content:center;gap:9px;
  background:var(--cyan);color:#070b14;padding:15px 24px;
  border-radius:var(--rpill);font-family:'JetBrains Mono',monospace;
  font-size:.8rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  transition:background .18s,transform .18s,box-shadow .18s;
  box-shadow:var(--shc);margin-bottom:10px;width:100%}
.btn-td-try:hover{background:var(--cyan2);transform:translateY(-2px);
  box-shadow:0 10px 36px rgba(34,211,238,.38)}
.td-trust{display:flex;flex-direction:column;gap:7px}
.td-trust-item{display:flex;align-items:center;gap:7px;
  font-family:'JetBrains Mono',monospace;font-size:.62rem;color:var(--ink4)}
.td-trust-item svg{width:12px;height:12px;stroke:var(--green);fill:none;stroke-width:2;flex-shrink:0}

.prose{font-size:.95rem;line-height:1.88;color:var(--ink3);font-weight:300}
.prose h2{font-family:'Bricolage Grotesque',sans-serif;font-size:1.7rem;
  font-weight:800;color:var(--ink);margin:48px 0 14px;letter-spacing:-.04em;
  padding-bottom:12px;border-bottom:1px solid var(--div);line-height:1.1}
.prose h3{font-family:'Bricolage Grotesque',sans-serif;font-size:1.25rem;
  font-weight:700;color:var(--ink);margin:32px 0 10px;letter-spacing:-.03em}
.prose p{margin-bottom:18px}
.prose a{color:var(--cyan);border-bottom:1px solid var(--cyan-g);transition:border-color .18s}
.prose a:hover{border-color:var(--cyan)}
.prose strong{color:var(--ink2);font-weight:600}
.prose ul,.prose ol{margin:0 0 22px;padding:0;list-style:none}
.prose li{padding-left:20px;position:relative;margin-bottom:8px;line-height:1.72}
.prose ul li::before{content:'▸';position:absolute;left:0;top:4px;
  font-size:.65rem;color:var(--cyan)}
.prose ol{counter-reset:ol}
.prose ol li{counter-increment:ol}
.prose ol li::before{content:counter(ol,decimal-leading-zero);position:absolute;
  left:0;top:3px;font-family:'JetBrains Mono',monospace;font-size:.6rem;color:var(--cyan)}

.breadcrumb{display:flex;align-items:center;gap:7px;
  font-family:'JetBrains Mono',monospace;font-size:.63rem;color:var(--ink4);
  margin-bottom:18px;flex-wrap:wrap;letter-spacing:.04em;
  padding:clamp(24px,3vw,40px) 0 0}
.breadcrumb a{color:var(--cyan);transition:opacity .18s}
.breadcrumb a:hover{opacity:.7}
.breadcrumb .sep{opacity:.3}

.pager{display:flex;justify-content:center;align-items:center;gap:9px;
  padding:48px 0;position:relative;z-index:1}
.pager a{background:var(--surf);border:1px solid var(--bdr);color:var(--ink3);
  padding:9px 20px;border-radius:var(--rpill);
  font-family:'JetBrains Mono',monospace;font-size:.7rem;
  transition:all .18s;letter-spacing:.06em;text-transform:uppercase}
.pager a:hover{background:var(--cyan);color:#070b14;
  border-color:var(--cyan);box-shadow:var(--shc);transform:translateY(-1px)}

.legal-wrap{max-width:740px;margin:52px auto 80px;padding:0 40px;
  position:relative;z-index:1}
.legal-wrap h2{font-family:'Bricolage Grotesque',sans-serif;font-size:1.55rem;
  font-weight:700;color:var(--ink);margin:40px 0 12px;letter-spacing:-.04em}
.legal-wrap h3{font-family:'Bricolage Grotesque',sans-serif;font-size:1.1rem;
  font-weight:700;color:var(--ink2);margin:24px 0 8px}
.legal-wrap p{font-size:.91rem;line-height:1.82;color:var(--ink3);
  margin-bottom:14px;font-weight:300}
.legal-card{background:var(--surf);border:1px solid var(--bdr);
  border-radius:var(--r3);padding:22px 26px;margin-bottom:24px}

.footer{background:var(--surf);border-top:1px solid var(--bdr);
  position:relative;z-index:1;margin-top:88px}
.footer::before{content:'';position:absolute;top:-1px;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--cyan),var(--amber),transparent);opacity:.3}
.footer-in{max-width:1440px;margin:0 auto;padding:52px 40px 36px}
.footer-top{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:44px;margin-bottom:36px}
.f-logo{font-family:'Bricolage Grotesque',sans-serif;font-size:1.1rem;
  font-weight:800;letter-spacing:-.03em;color:var(--ink);
  display:flex;align-items:center;gap:6px;margin-bottom:11px}
.f-logo-arrow{color:var(--cyan);animation:nudge 3s ease-in-out infinite}
.f-logo-ai{color:var(--cyan)}
.f-desc{font-size:.84rem;line-height:1.78;color:var(--ink4);max-width:260px;font-weight:300}
.f-tag{margin-top:16px;font-family:'JetBrains Mono',monospace;font-size:.56rem;
  letter-spacing:.16em;text-transform:uppercase;color:var(--amber);
  display:flex;align-items:center;gap:7px}
.f-tag::before{content:'→'}
.f-col-title{font-family:'JetBrains Mono',monospace;font-size:.56rem;
  font-weight:400;letter-spacing:.18em;text-transform:uppercase;
  color:var(--ink4);margin-bottom:13px}
.f-col a{display:block;font-size:.83rem;color:var(--ink4);
  margin-bottom:8px;transition:color .18s,padding-left .18s}
.f-col a:hover{color:var(--cyan);padding-left:4px}
.f-div{height:1px;background:var(--div);margin-bottom:20px}
.f-bottom{display:flex;align-items:center;justify-content:space-between;
  gap:14px;flex-wrap:wrap}
.f-legal{font-family:'JetBrains Mono',monospace;font-size:.6rem;
  color:var(--ink4);line-height:1.65}
.f-note{font-family:'JetBrains Mono',monospace;font-size:.56rem;
  color:var(--ink4);opacity:.45;font-style:italic}

#sov{display:none;position:fixed;inset:0;background:rgba(7,11,20,.92);
  backdrop-filter:blur(18px);z-index:500;padding:64px 18px;overflow-y:auto}
#sov.open{display:block;animation:fadeIn .18s ease}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.sov-panel{max-width:960px;margin:0 auto;background:var(--surf);
  border:1px solid var(--bdr2);border-radius:var(--r4);padding:26px;
  box-shadow:var(--sh3);animation:panelIn .22s var(--ease)}
@keyframes panelIn{from{opacity:0;transform:translateY(12px) scale(.99)}to{opacity:1;transform:none}}
.sov-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:5px}
.sov-title{font-family:'Bricolage Grotesque',sans-serif;font-size:1.35rem;
  font-weight:700;color:var(--ink);letter-spacing:-.04em}
.sov-close{width:32px;height:32px;border-radius:var(--r1);
  border:1px solid var(--bdr);background:var(--surf2);
  display:flex;align-items:center;justify-content:center;
  font-size:.9rem;color:var(--ink3);transition:all .18s}
.sov-close:hover{background:var(--rose-d);color:var(--rose)}
.sov-count{font-family:'JetBrains Mono',monospace;font-size:.66rem;
  color:var(--ink4);margin-bottom:18px;letter-spacing:.06em}
.sov-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}

#ckbar{display:none;position:fixed;bottom:16px;left:50%;transform:translateX(-50%);
  background:var(--surf2);border:1px solid var(--bdr2);border-radius:var(--r4);
  padding:14px 20px;box-shadow:var(--sh3);z-index:1000;
  max-width:540px;width:calc(100% - 28px);
  align-items:center;gap:14px;flex-wrap:wrap}
#ckbar.show{display:flex;animation:ckpop .28s var(--ease)}
@keyframes ckpop{from{opacity:0;transform:translateX(-50%) translateY(14px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
.ck-txt{flex:1;min-width:170px;font-family:'JetBrains Mono',monospace;
  font-size:.66rem;color:var(--ink4);line-height:1.55}
.ck-txt a{color:var(--cyan)}
.ck-btns{display:flex;gap:6px;flex-shrink:0}
.ck-ok{background:var(--cyan);color:#070b14;border:none;border-radius:var(--r1);
  padding:8px 16px;font-family:'JetBrains Mono',monospace;font-size:.7rem;
  font-weight:700;transition:background .18s}
.ck-ok:hover{background:var(--cyan2)}
.ck-ess{background:transparent;color:var(--ink4);border:1px solid var(--bdr);
  border-radius:var(--r1);padding:8px 13px;
  font-family:'JetBrains Mono',monospace;font-size:.66rem;transition:all .18s}
.ck-ess:hover{border-color:rgba(34,211,238,.25);color:var(--cyan)}

/* ── FIXED: rv starts visible, no hidden flash on mobile ── */
.rv{opacity:1;transform:none;
  transition:opacity .55s var(--ease),transform .55s var(--ease)}
.rv.in{opacity:1;transform:none}

.btn-primary{display:inline-flex;align-items:center;gap:8px;
  background:var(--cyan);color:#070b14;padding:13px 24px;
  border-radius:var(--rpill);font-family:'JetBrains Mono',monospace;
  font-size:.79rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
  border:none;transition:all .18s;box-shadow:var(--shc)}
.btn-primary:hover{background:var(--cyan2);transform:translateY(-2px);
  box-shadow:0 8px 32px rgba(34,211,238,.38)}
.btn-ghost{display:inline-flex;align-items:center;gap:8px;
  background:transparent;color:var(--ink2);padding:13px 22px;
  border-radius:var(--rpill);font-size:.875rem;font-weight:500;
  border:1px solid var(--bdr2);transition:all .18s;letter-spacing:-.01em}
.btn-ghost:hover{background:var(--cyan-d);border-color:rgba(34,211,238,.25);color:var(--cyan2)}

@media(max-width:1100px){
  .hero{grid-template-columns:1fr}
  .hero-panel{display:none}
  .td-body{grid-template-columns:1fr}
  .footer-top{grid-template-columns:1fr 1fr;gap:28px}
  .cd-grid{grid-template-columns:1fr}
  .email-inner{grid-template-columns:1fr}
  .email-card{display:none}
}
@media(max-width:768px){
  .nav-in{padding:0 16px;height:54px}
  .nav-links,.nav-search{display:none}
  #hbg{display:flex}
  .page{padding:0 16px}
  .affil-in{padding:10px 16px}
  .email-inner{padding:0 16px}
  .footer-in{padding:36px 16px 26px}
  .footer-top{grid-template-columns:1fr;gap:20px}
  .f-bottom{flex-direction:column;align-items:flex-start}
  .legal-wrap{padding:0 16px}
  .hero{grid-template-columns:1fr;padding:36px 0 20px}
  .stats-bar{gap:22px}
  .td-header-in{grid-template-columns:1fr}
  .td-score-block{display:none}
}
@media(max-width:480px){
  .hero-h1{font-size:2.2rem}
  .comp-grid,.roles-grid{grid-template-columns:1fr}
  .tools-grid{grid-template-columns:1fr}
}

::-webkit-scrollbar{width:3px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--bdr3);border-radius:2px}
::-webkit-scrollbar-thumb:hover{background:var(--cyan)}
::selection{background:var(--cyan-d);color:var(--cyan2)}
"""


BASE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="author" content="Moving Forward With AI">
<title>{{ title }}</title>
<meta name="description" content="{{ desc[:155] }}">
<link rel="canonical" href="{{ canon }}">
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ desc[:200] }}">
<meta property="og:type" content="website">
<meta property="og:url" content="{{ canon }}">
<meta property="og:site_name" content="Moving Forward With AI">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
{% if schema %}<script type="application/ld+json">{{ schema|safe }}</script>{% endif %}
{% if bcs %}<script type="application/ld+json">{{ bcs|safe }}</script>{% endif %}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<style>{{ css|safe }}</style>
</head>
<body>

<div class="ticker" aria-hidden="true">
  <div class="ticker-inner">
    {% for _ in range(2) %}
    <span>Independent AI Tool Reviews</span><span class="dot">◆</span>
    <span class="hi">UK-Focused · Updated Weekly</span><span class="dot">◆</span>
    <span>No Paid Placements</span><span class="dot">◆</span>
    <span>Honest Verdicts</span><span class="dot">◆</span>
    <span class="hi">Moving Forward With AI</span><span class="dot">◆</span>
    <span>Affiliate Commissions Fund This Site</span><span class="dot">◆</span>
    {% endfor %}
  </div>
</div>

<header class="nav" id="sitenav">
  <div class="nav-in">
    <a href="/" class="nav-logo">
      <div class="logo-mark">
        <span class="logo-arrow">→</span>
        <span class="logo-text">Moving Forward </span><span class="logo-ai">With AI</span>
      </div>
    </a>
    <nav class="nav-links" aria-label="Primary">
      <a href="/">Home</a>
      <a href="/tools">All Tools</a>
      <a href="/compare">Compare</a>
      <a href="/blog">Guides</a>
      <div class="nav-drop">
        <button class="nav-drop-btn" type="button" aria-expanded="false">
          Who it's for
          <svg class="drop-chevron" viewBox="0 0 12 12"><path d="M2 4l4 4 4-4"/></svg>
        </button>
        <div class="drop-menu" role="menu">
          {% for role in roles %}
          <a href="/for/{{ role.slug }}" role="menuitem">
            <span class="dm-icon">{{ role.icon }}</span>{{ role.name }}
          </a>
          {% endfor %}
        </div>
      </div>
    </nav>
    <div class="nav-right">
      <div class="nav-search">
        <svg class="nav-search-ico" viewBox="0 0 16 16"><circle cx="6.5" cy="6.5" r="4.5"/><path d="M10 10l3.5 3.5"/></svg>
        <input type="search" id="search-input" placeholder="search tools…" autocomplete="off">
      </div>
      <button class="nav-icon" id="theme-btn" aria-label="Toggle theme">
        <svg id="ico-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>
        <svg id="ico-moon" viewBox="0 0 24 24" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
      <button id="hbg" aria-label="Open menu" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>

<div id="mob" role="dialog" aria-modal="true">
  <div class="mob-links">
    <a href="/" class="mob-link">Home</a>
    <a href="/tools" class="mob-link">All Tools</a>
    <a href="/compare" class="mob-link">Compare</a>
    <a href="/blog" class="mob-link">Guides</a>
  </div>
  <div class="mob-sec">
    <div class="mob-label">Who it's for</div>
    <div class="mob-pills">
      {% for role in roles %}
      <a href="/for/{{ role.slug }}" class="mob-pill">{{ role.icon }} {{ role.name }}</a>
      {% endfor %}
    </div>
  </div>
</div>

{{ content|safe }}

<footer class="footer">
  <div class="footer-in">
    <div class="footer-top">
      <div>
        <div class="f-logo">
          <span class="f-logo-arrow">→</span>
          Moving Forward <span class="f-logo-ai">With AI</span>
        </div>
        <p class="f-desc">Independent, honest reviews of AI tools for UK freelancers, marketers and builders. No paid placements. Ever.</p>
        <div class="f-tag">Affiliate commissions fund this site</div>
      </div>
      <div class="f-col">
        <div class="f-col-title">Explore</div>
        <a href="/">Home</a>
        <a href="/tools">All Tools</a>
        <a href="/compare">Compare</a>
        <a href="/blog">Guides</a>
      </div>
      <div class="f-col">
        <div class="f-col-title">Who it's for</div>
        {% for role in roles %}
        <a href="/for/{{ role.slug }}">{{ role.name }}</a>
        {% endfor %}
      </div>
      <div class="f-col">
        <div class="f-col-title">Legal</div>
        <a href="/privacy">Privacy Policy</a>
        <a href="/terms">Terms</a>
        <a href="/affiliate-disclosure">Affiliate Disclosure</a>
        <a href="mailto:hello@movingforwardwithai.com">Contact</a>
      </div>
    </div>
    <div class="f-div"></div>
    <div class="f-bottom">
      <p class="f-legal">© 2026 Moving Forward With AI. All rights reserved. Prices verified at time of writing — always confirm on the tool's website.</p>
      <p class="f-note">// This site earns affiliate commissions. <a href="/affiliate-disclosure" style="color:var(--cyan)">Full disclosure →</a></p>
    </div>
  </div>
</footer>

<div id="sov" role="dialog" aria-modal="true">
  <div class="sov-panel">
    <div class="sov-hdr">
      <h2 class="sov-title">Search Tools</h2>
      <button class="sov-close" id="sov-close">×</button>
    </div>
    <p class="sov-count" id="sov-count"></p>
    <div class="sov-grid" id="sov-results"></div>
  </div>
</div>

<div id="ckbar" role="dialog">
  <div class="ck-txt">// Essential cookies + affiliate tracking. <a href="/privacy">Privacy policy →</a></div>
  <div class="ck-btns">
    <button class="ck-ok" id="ck-ok">Accept</button>
    <button class="ck-ess" id="ck-ess">Essential only</button>
  </div>
</div>

<script>
(function(){
  var l=localStorage.getItem('mfwai-light')==='1';
  function a(v){document.documentElement.classList.toggle('light',v);
    document.getElementById('ico-sun').style.display=v?'none':'block';
    document.getElementById('ico-moon').style.display=v?'block':'none'}
  a(l);
  document.getElementById('theme-btn').onclick=function(){l=!l;localStorage.setItem('mfwai-light',l?'1':'0');a(l)}
})();

window.addEventListener('scroll',function(){
  document.getElementById('sitenav').classList.toggle('scrolled',scrollY>16)
},{passive:true});

(function(){
  var b=document.getElementById('hbg'),m=document.getElementById('mob');
  b.onclick=function(){var o=m.classList.toggle('open');b.classList.toggle('open',o);
    b.setAttribute('aria-expanded',String(o));document.body.style.overflow=o?'hidden':''};
  m.querySelectorAll('a').forEach(function(a){a.onclick=function(){
    m.classList.remove('open');b.classList.remove('open');
    b.setAttribute('aria-expanded','false');document.body.style.overflow=''}});
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'&&m.classList.contains('open')){
      m.classList.remove('open');b.classList.remove('open');
      b.setAttribute('aria-expanded','false');document.body.style.overflow=''}});
})();

(function(){
  var ds=document.querySelectorAll('.nav-drop');
  ds.forEach(function(d){
    d.querySelector('.nav-drop-btn').addEventListener('click',function(e){
      e.stopPropagation();var o=d.classList.contains('open');
      ds.forEach(function(x){x.classList.remove('open');x.querySelector('.nav-drop-btn').setAttribute('aria-expanded','false')});
      if(!o){d.classList.add('open');d.querySelector('.nav-drop-btn').setAttribute('aria-expanded','true')}
    })
  });
  document.addEventListener('click',function(){ds.forEach(function(d){d.classList.remove('open')})});
})();

/* FIXED REVEAL — always visible, enhanced with scroll animation where supported */
(function(){
  var els=document.querySelectorAll('.rv');
  els.forEach(function(e){e.classList.add('in')});
})();

var allTools=[];
(async function(){try{var r=await fetch('/api/tools');var d=await r.json();allTools=d.tools||[]}catch(e){}})();
var sov=document.getElementById('sov'),cnt=document.getElementById('sov-count'),res=document.getElementById('sov-results'),inp=document.getElementById('search-input'),stmr;
function closeSov(){sov.classList.remove('open');document.body.style.overflow=''}
function miniCard(t){
  return '<div class="tool-card" style="cursor:pointer" onclick="location.href=\'/tool/'+t.slug+'\'">'+
    '<div class="tc-top"><div class="tc-meta"><div class="tc-cat">'+t.category+'</div>'+
    '<div class="tc-score" style="background:var(--'+(t.score>=88?'green':'cyan')+'-d);border:1px solid var(--'+(t.score>=88?'green':'cyan')+'-g);color:var(--'+(t.score>=88?'green':'cyan')+')">'+t.score+'</div></div>'+
    '<a href="/tool/'+t.slug+'" class="tc-name">'+t.name+'</a>'+
    '<p class="tc-tagline">'+t.tagline+'</p></div>'+
    '<div class="tc-bot"><div class="tc-price-row"><span class="tc-price">'+t.starting_price+'</span></div></div></div>'}
inp.addEventListener('input',function(e){
  clearTimeout(stmr);var q=e.target.value.trim();
  if(q.length<2){if(sov.classList.contains('open'))closeSov();return}
  stmr=setTimeout(function(){
    var ql=q.toLowerCase();
    var hits=allTools.filter(function(t){
      return (t.name||'').toLowerCase().includes(ql)||
             (t.category||'').toLowerCase().includes(ql)||
             (t.tagline||'').toLowerCase().includes(ql)||
             (t.tags||[]).join(' ').toLowerCase().includes(ql)});
    cnt.textContent='// '+hits.length+' result'+(hits.length!==1?'s':'')+' for "'+q+'"';
    res.innerHTML=hits.length?hits.map(miniCard).join(''):'<p style="text-align:center;padding:44px;font-family:JetBrains Mono,monospace;font-size:.72rem;color:var(--ink4)">// no results found</p>';
    sov.classList.add('open');document.body.style.overflow='hidden'},160)});
inp.addEventListener('keydown',function(e){if(e.key==='Escape'){closeSov();inp.value=''}});
document.getElementById('sov-close').onclick=closeSov;
sov.addEventListener('click',function(e){if(e.target===sov)closeSov()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeSov()});

(function(){
  var KEY='mfwai_consent_v1',bar=document.getElementById('ckbar');
  try{if(!localStorage.getItem(KEY))setTimeout(function(){bar.classList.add('show')},1600)}catch(e){bar.classList.add('show')}
  function dismiss(v){try{localStorage.setItem(KEY,v)}catch(e){}bar.classList.remove('show')}
  document.getElementById('ck-ok').onclick=function(){dismiss('all')};
  document.getElementById('ck-ess').onclick=function(){dismiss('ess')};
})();

var ef=document.getElementById('email-form');
if(ef){ef.addEventListener('submit',function(e){e.preventDefault();
  var btn=ef.querySelector('button'),em=ef.querySelector('input').value;
  if(!em){return}
  btn.textContent='Sent ✓';btn.style.background='var(--green)';
  btn.disabled=true;
})}
</script>
</body>
</html>"""


def render(title, desc, content, schema='', bcs=''):
    canon = SITE_URL + (request.path.rstrip('/') or '/')
    return render_template_string(BASE,
        title=title, desc=desc, content=content,
        css=CSS, roles=ROLES, slugify=slugify,
        canon=canon, schema=schema, bcs=bcs)


def tool_card(t, delay=0):
    sc = t['score']
    s_bg  = 'var(--green-d)' if sc>=88 else 'var(--cyan-d)'
    s_bdr = 'var(--green-g)' if sc>=88 else 'rgba(34,211,238,.18)'
    s_col = 'var(--green)' if sc>=88 else 'var(--cyan)'
    badges = []
    if t.get('free_tier'):   badges.append('<span class="badge b-free">Free tier</span>')
    if t.get('free_trial'):  badges.append(f'<span class="badge b-trial">{t["trial_days"]}d trial</span>')
    if not t.get('free_tier') and not t.get('free_trial'):
        badges.append('<span class="badge b-paid">Paid only</span>')
    if t.get('featured'):    badges.append('<span class="badge b-top">Featured</span>')
    st = stars(t['rating'])
    return f"""<div class="tool-card rv">
  <div class="tc-top">
    <div class="tc-meta">
      <div class="tc-cat">{t['category']}</div>
      <div class="tc-score" style="background:{s_bg};border:1px solid {s_bdr};color:{s_col}">{sc}</div>
    </div>
    <a href="/tool/{t['slug']}" class="tc-name">{t['name']}</a>
    <p class="tc-tagline">{t['tagline']}</p>
    <div class="tc-badges">{''.join(badges)}</div>
  </div>
  <div class="tc-div"></div>
  <div class="tc-bot">
    <div class="tc-price-row">
      <span class="tc-price">{t['starting_price']}</span>
      <span class="tc-model">{t['pricing_model']}</span>
    </div>
    <div class="tc-rating">
      <span class="tc-stars">{st}</span>
      <span>{t['rating']}/5 · {t['review_count']} reviews</span>
    </div>
    <a href="{t['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener" class="btn-try">
      Try {t['name']}
      <svg viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
    </a>
    <a href="/tool/{t['slug']}" class="btn-review">Full review →</a>
  </div>
</div>"""


def email_capture():
    lm = LEAD_MAGNET
    items_html = '\n'.join(f'<div class="email-item">{i}</div>' for i in lm['items'])
    card_items = '\n'.join(f'<div class="eci"><span class="eci-num">{str(i+1).zfill(2)}</span>{item}</div>'
                           for i,item in enumerate(lm['items']))
    return f"""<section class="email-sec">
  <div class="email-inner">
    <div>
      <div class="email-kicker">Free guide — no spam</div>
      <h2 class="email-h2">{lm['title']}<br><em>{lm['subtitle']}</em></h2>
      <p class="email-sub">{lm['description']}</p>
      <form class="email-form" id="email-form">
        <input class="email-input" type="email" placeholder="your@email.com" required>
        <button type="submit" class="btn-email">{lm['cta']}</button>
      </form>
      <div class="email-items">{items_html}</div>
      <p class="email-notice">// No spam. Unsubscribe any time. UK GDPR compliant.</p>
    </div>
    <div class="email-card">
      <div class="email-card-title">{lm['title']}</div>
      <div class="email-card-sub">{lm['subtitle']}</div>
      <div class="email-card-items">{card_items}</div>
    </div>
  </div>
</section>"""


def affil_strip():
    return """<div class="affil"><div class="affil-in">
      <svg class="affil-ico" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
      // <strong>Affiliate disclosure:</strong> Moving Forward With AI earns a commission when you sign up through links — at no extra cost to you.
      <a href="/affiliate-disclosure">Learn more →</a>
    </div></div>"""


@app.route('/')
def home():
    panel_tools = sorted(TOOLS, key=lambda t: -t['score'])[:4]
    panel_html = ''
    for i,t in enumerate(panel_tools):
        s_bg = 'var(--green-d)' if t['score']>=88 else 'var(--cyan-d)'
        s_bdr = 'var(--green-g)' if t['score']>=88 else 'rgba(34,211,238,.18)'
        s_col = 'var(--green)' if t['score']>=88 else 'var(--cyan)'
        panel_html += f"""<a href="/tool/{t['slug']}" class="ptool">
          <span class="ptool-rank">{str(i+1).zfill(2)}</span>
          <div><div class="ptool-name">{t['name']}</div>
          <div class="ptool-cat">{t['category']}</div></div>
          <div class="ptool-score" style="background:{s_bg};border:1px solid {s_bdr};color:{s_col}">{t['score']}</div>
        </a>"""

    role_chips = '\n'.join(
        f'<a href="/for/{r["slug"]}" class="role-chip"><span class="chip-icon">{r["icon"]}</span>{r["name"]}</a>'
        for r in ROLES)

    hero = f"""<div class="page">
  <div class="hero">
    <div>
      <div class="hero-kicker">UK AI Tool Reviews · Honest · Independent · 2026</div>
      <h1 class="hero-h1">Moving forward<br><em>with AI</em>
        <span class="sub">Honest reviews. No sponsored rankings. Real results.</span>
      </h1>
      <p class="hero-sub">We review, score, and rank AI tools so UK freelancers, marketers and business owners can find what actually works — and skip what doesn't.</p>
      <div class="role-selector">
        <div class="role-label">// I am a</div>
        <div class="role-chips">{role_chips}</div>
      </div>
      <div class="hero-acts">
        <a href="/tools" class="btn-primary">Browse all tools →</a>
        <a href="/compare" class="btn-ghost">Compare tools</a>
      </div>
      <div class="stats-bar">
        <div><div class="stat-num">{len(TOOLS)}<em>+</em></div><div class="stat-lbl">tools reviewed</div></div>
        <div><div class="stat-num">{len(ROLES)}<em>+</em></div><div class="stat-lbl">role guides</div></div>
        <div><div class="stat-num"><em>£0</em></div><div class="stat-lbl">paid placements</div></div>
        <div><div class="stat-num">{len(COMPARISONS)}<em>+</em></div><div class="stat-lbl">comparisons</div></div>
      </div>
    </div>
    <div class="hero-panel">
      <div class="panel-head">
        <span class="panel-title">Top-rated tools</span>
        <span class="panel-live">updated</span>
      </div>
      <div class="panel-tools">{panel_html}</div>
      <a href="/tools" class="panel-cta">View all {len(TOOLS)} reviewed tools →</a>
    </div>
  </div>
</div>"""

    role_cards = '\n'.join(f"""<a href="/for/{r['slug']}" class="role-card rv">
      <div class="rc-icon">{r['icon']}</div>
      <div class="rc-name">{r['name']}</div>
      <div class="rc-desc">{r['description']}</div>
      <div class="rc-count">{len(r['tool_slugs'])} recommended tools</div>
      <div class="rc-arrow">See the stack →</div>
    </a>""" for r in ROLES)

    roles_sec = f"""<div class="page">
  <div class="sec">
    <div class="sec-top">
      <div>
        <div class="sec-kicker">Built for your situation</div>
        <h2 class="sec-h2">Who are you <em>moving forward?</em></h2>
      </div>
      <a href="/tools" class="sec-more">All tools →</a>
    </div>
    <div class="roles-grid">{role_cards}</div>
  </div>
</div>"""

    featured = [t for t in TOOLS if t.get('featured')]
    tool_cards_html = '\n'.join(tool_card(t) for t in featured)
    tools_sec = f"""<div class="page">
  <div class="sec">
    <div class="sec-top">
      <div>
        <div class="sec-kicker">Highest rated · Featured picks</div>
        <h2 class="sec-h2">Top <em>AI tools</em> right now</h2>
      </div>
      <a href="/tools" class="sec-more">All tools →</a>
    </div>
    <div class="tools-grid">{tool_cards_html}</div>
  </div>
</div>"""

    comp_cards = '\n'.join(f"""<a href="/compare/{c['slug']}" class="comp-card rv">
      <div class="comp-vs">
        <span class="comp-tool-name">{get_tool(c['tool_a'])['name']}</span>
        <span class="comp-vs-sep">VS</span>
        <span class="comp-tool-name">{get_tool(c['tool_b'])['name']}</span>
      </div>
      <div class="comp-desc">{c['description']}</div>
      <div class="comp-cta">Read comparison →</div>
    </a>""" for c in COMPARISONS)

    comp_sec = f"""<div class="page">
  <div class="sec">
    <div class="sec-top">
      <div>
        <div class="sec-kicker">Head to head · High intent</div>
        <h2 class="sec-h2"><em>Compare</em> tools side by side</h2>
      </div>
      <a href="/compare" class="sec-more">All comparisons →</a>
    </div>
    <div class="comp-grid">{comp_cards}</div>
  </div>
</div>"""

    posts = sorted([{**v,'slug':k} for k,v in BLOG_POSTS.items()], key=lambda x:x['date'], reverse=True)
    blog_cards = '\n'.join(f"""<a href="/blog/{p['slug']}" class="blog-card rv">
      <div class="blog-card-body">
        <div class="blog-date">{datetime.datetime.strptime(p['date'],'%Y-%m-%d').strftime('%d %b %Y')} · {p.get('category','Guide')}</div>
        <div class="blog-title">{p['title']}</div>
        <div class="blog-desc">{p.get('description','')}</div>
        <div class="blog-more">Read guide →</div>
      </div>
    </a>""" for p in posts[:3])

    blog_sec = f"""<div class="page">
  <div class="sec">
    <div class="sec-top">
      <div>
        <div class="sec-kicker">Guides · Analysis · How-tos</div>
        <h2 class="sec-h2">Latest <em>guides</em></h2>
      </div>
      <a href="/blog" class="sec-more">All guides →</a>
    </div>
    <div class="blog-grid">{blog_cards}</div>
  </div>
</div>"""

    content = hero + affil_strip() + roles_sec + tools_sec + comp_sec + email_capture() + blog_sec + '<div style="height:48px"></div>'
    return render(
        title='Moving Forward With AI — Honest AI Tool Reviews for UK Freelancers & Builders',
        desc='Independent, honest reviews of AI tools for UK freelancers, marketers and builders. Role-based recommendations, head-to-head comparisons, no paid placements.',
        content=content)


@app.route('/tools')
def tools_all():
    page = int(request.args.get('page',1))
    PER  = 12
    paged = TOOLS[(page-1)*PER : page*PER]
    total_pages = (len(TOOLS)+PER-1)//PER
    cards = '\n'.join(tool_card(t) for t in paged)
    prev = f'<a href="/tools?page={page-1}" rel="prev">← prev</a>' if page>1 else ''
    nxt  = f'<a href="/tools?page={page+1}" rel="next">next →</a>' if page<total_pages else ''
    pager = f'<div class="page"><div class="pager">{prev}{nxt}</div></div>' if prev or nxt else ''
    content = f"""
    <div class="page">
      <div class="breadcrumb"><a href="/">Home</a><span>/</span><span>All Tools</span></div>
      <div style="margin-bottom:28px">
        <div class="sec-kicker">All tools · {len(TOOLS)} reviewed</div>
        <h1 style="font-family:Bricolage Grotesque,sans-serif;font-size:clamp(2rem,4vw,3.2rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1">
          Every AI tool, <em style="color:var(--cyan);font-style:normal">honestly reviewed</em>
        </h1>
      </div>
    </div>
    {affil_strip()}
    <div class="page"><div class="tools-grid">{cards}</div></div>
    {pager}"""
    return render(
        title=f'All AI Tools Reviewed — Moving Forward With AI',
        desc=f'Browse all {len(TOOLS)} AI tools reviewed on Moving Forward With AI. Honest scores, pricing, pros and cons for UK users.',
        content=content,
        bcs=bc_schema([('Home','/'),('All Tools','/tools')]))


@app.route('/for/<slug>')
def role_page(slug):
    role = get_role(slug)
    if not role: abort(404)
    role_tools = [get_tool(s) for s in role['tool_slugs'] if get_tool(s)]
    top = get_tool(role['top_pick'])
    pain_items = '\n'.join(f'<div class="rd-pain-item">{p}</div>' for p in role.get('pain_points',[]))
    cards = '\n'.join(tool_card(t) for t in role_tools)
    top_pick_html = ''
    if top:
        sc = top['score']
        sc_col = 'var(--green)' if sc>=88 else 'var(--cyan)'
        top_pick_html = f"""<div class="rd-top-pick rv">
          <div>
            <div class="sec-kicker" style="margin-bottom:6px">Top pick for {role['name']}</div>
            <div style="font-family:Bricolage Grotesque,sans-serif;font-size:1.2rem;font-weight:800;color:var(--ink);letter-spacing:-.04em">{top['name']}</div>
            <div style="font-size:.84rem;color:var(--ink3);font-weight:300;margin-top:4px">{top['tagline']}</div>
          </div>
          <div class="rd-top-badge"># Top pick</div>
          <div style="font-family:Bricolage Grotesque,sans-serif;font-size:2rem;font-weight:800;color:{sc_col};letter-spacing:-.06em;flex-shrink:0">{sc}</div>
          <a href="{top['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener" class="btn-primary" style="flex-shrink:0">Try it →</a>
        </div>"""

    content = f"""
    <div class="page">
      <div class="rd-header">
        <div class="rd-breadcrumb">
          <a href="/">Home</a><span>/</span>
          <a href="/tools">Tools</a><span>/</span>
          <span>{role['name']}</span>
        </div>
        <div class="rd-icon">{role['icon']}</div>
        <h1 class="rd-h1">{role['headline'].split(' for ')[0]} for<br><em>{role['name']}</em></h1>
        <p class="rd-sub">{role['description']}</p>
        <div class="rd-pain rv">
          <div class="rd-pain-title">// Sound familiar?</div>
          <div class="rd-pain-list">{pain_items}</div>
        </div>
        <div class="rd-how rv">
          <div class="rd-how-title">// How AI helps</div>
          <div class="rd-how-text">{role.get('how_ai_helps','')}</div>
        </div>
        {top_pick_html}
        <div class="sec-kicker" style="margin:32px 0 18px">The recommended stack · {len(role_tools)} tools</div>
      </div>
      <div class="tools-grid">{cards}</div>
    </div>
    {email_capture()}"""

    return render(
        title=f'Best AI Tools for {role["name"]} 2026 — Moving Forward With AI',
        desc=f'{role["description"]} Honest reviews of the best AI tools for {role["name"].lower()} in 2026.',
        content=content,
        bcs=bc_schema([('Home','/'),('Tools','/tools'),(role['name'],f'/for/{slug}')]))


@app.route('/tool/<slug>')
def tool_detail(slug):
    t = get_tool(slug)
    if not t: abort(404)
    sc = t['score']
    sc_col = score_color(sc)
    sl = 'Excellent' if sc>=88 else ('Good' if sc>=78 else 'Decent')
    st = stars(t['rating'])
    badges = []
    if t.get('free_tier'):  badges.append('<span class="badge b-free">Free tier</span>')
    if t.get('free_trial'): badges.append(f'<span class="badge b-trial">{t["trial_days"]}-day trial</span>')
    pros_html = '\n'.join(f'<li>{p}</li>' for p in t['pros'])
    cons_html = '\n'.join(f'<li>{c}</li>' for c in t['cons'])
    best_html = '\n'.join(f'<div style="display:flex;align-items:center;gap:8px;font-size:.86rem;color:var(--ink3);margin-bottom:6px;font-weight:300"><span style="color:var(--cyan);font-family:JetBrains Mono,monospace;font-size:.7rem">→</span>{b}</div>' for b in t['best_for'])
    related = [x for x in TOOLS if x['slug']!=slug and any(r in x.get('roles',[]) for r in t.get('roles',[]))][:3]
    if len(related)<3:
        extra = [x for x in TOOLS if x['slug']!=slug and x not in related]
        related += extra[:3-len(related)]
    rel_cards = '\n'.join(tool_card(r) for r in related[:3])
    content = f"""
    <div class="page">
      <div class="td-hero">
        <div class="td-bc">
          <a href="/">Home</a><span>/</span>
          <a href="/tools">Tools</a><span>/</span>
          <a href="/category/{slugify(t['category'])}">{t['category']}</a><span>/</span>
          <span>{t['name']}</span>
        </div>
        <div class="td-header">
          <div class="td-header-in">
            <div>
              <div class="td-cat">{t['category'].upper()}</div>
              <h1 class="td-h1">{t['name']}</h1>
              <p class="td-tagline">{t['tagline']}</p>
              <div class="td-rating-row">
                <span class="td-stars">{st}</span>
                <span class="td-rating-txt">{t['rating']}/5 · {t['review_count']} reviews</span>
                {''.join(badges)}
              </div>
            </div>
            <div class="td-score-block">
              <div class="td-score-num" style="color:{sc_col}">{sc}</div>
              <div style="font-family:JetBrains Mono,monospace;font-size:.62rem;color:{sc_col};letter-spacing:.08em;margin-top:2px">{sl}</div>
              <div class="td-score-lbl">MFWAI score</div>
            </div>
          </div>
        </div>
        <div class="td-body">
          <div>
            <div class="td-sec">
              <div class="td-sec-title">Verdict</div>
              <p class="verdict-text">{t['verdict']}</p>
            </div>
            <div class="td-sec" style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
              <div><div class="td-sec-title">Pros</div><ul class="pros-list">{pros_html}</ul></div>
              <div><div class="td-sec-title">Cons</div><ul class="cons-list">{cons_html}</ul></div>
            </div>
            <div class="td-sec">
              <div class="td-sec-title">Best for</div>
              {best_html}
            </div>
          </div>
          <div>
            <div class="td-price-box">
              <div style="font-family:JetBrains Mono,monospace;font-size:.58rem;color:var(--ink4);letter-spacing:.1em;text-transform:uppercase;margin-bottom:7px">Starting from</div>
              <div class="td-price">{t['starting_price']}</div>
              <div class="td-price-note">{t['pricing_model']}</div>
            </div>
            <a href="{t['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener" class="btn-td-try">
              Try {t['name']}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </a>
            <div class="td-trust">
              <div class="td-trust-item"><svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Affiliate link — no extra cost</div>
              {'<div class="td-trust-item"><svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Free trial available</div>' if t.get('free_trial') else ''}
              <div class="td-trust-item"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>Reviewed {t.get('date_added','2026')}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="page">
      <div class="sec">
        <div class="sec-top">
          <div><div class="sec-kicker">You might also consider</div>
          <h2 class="sec-h2">Related <em>tools</em></h2></div>
        </div>
        <div class="tools-grid">{rel_cards}</div>
      </div>
    </div>"""
    return render(
        title=f'{t["name"]} Review 2026 — Honest Score & Verdict | Moving Forward With AI',
        desc=f'{t["name"]}: {t["tagline"]}. MFWAI score: {sc}/100. From {t["starting_price"]}. Honest pros, cons and verdict for UK users.',
        content=content,
        schema=tool_schema(t),
        bcs=bc_schema([('Home','/'),('Tools','/tools'),(t['name'],f'/tool/{slug}')]))


@app.route('/compare')
def compare_index():
    cards = '\n'.join(f"""<a href="/compare/{c['slug']}" class="comp-card rv">
      <div class="comp-vs">
        <span class="comp-tool-name">{get_tool(c['tool_a'])['name']}</span>
        <span class="comp-vs-sep">VS</span>
        <span class="comp-tool-name">{get_tool(c['tool_b'])['name']}</span>
      </div>
      <div class="comp-desc">{c['description']}</div>
      <div class="comp-cta">Read full comparison →</div>
    </a>""" for c in COMPARISONS)
    content = f"""
    <div class="page">
      <div class="breadcrumb"><a href="/">Home</a><span>/</span><span>Compare</span></div>
      <div style="margin-bottom:28px">
        <div class="sec-kicker">Head-to-head · High intent</div>
        <h1 style="font-family:Bricolage Grotesque,sans-serif;font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1">
          Compare AI tools <em style="color:var(--cyan);font-style:normal">side by side</em>
        </h1>
        <p style="font-size:.93rem;color:var(--ink3);font-weight:300;margin-top:10px;max-width:500px">
          When you're deciding between two tools, our head-to-head comparisons give you the honest verdict.
        </p>
      </div>
      <div class="comp-grid">{cards}</div>
    </div>"""
    return render('Compare AI Tools Side by Side — Moving Forward With AI',
        'Head-to-head AI tool comparisons for UK users. Honest verdicts on which tool wins and why.',
        content)


@app.route('/compare/<slug>')
def compare_detail(slug):
    c = get_comp(slug)
    if not c: abort(404)
    ta = get_tool(c['tool_a'])
    tb = get_tool(c['tool_b'])
    if not ta or not tb: abort(404)
    winner = get_tool(c['winner_slug']) if c.get('winner_slug') else None

    def cd_tool_html(t, is_winner):
        sc = t['score']
        sc_col = score_color(sc)
        w = 'winner' if is_winner else ''
        wb = '<div class="cd-winner-badge">✓ Winner</div>' if is_winner else ''
        rows = f"""<tr><td>Rating</td><td>{t['rating']}/5</td></tr>
          <tr><td>Starting price</td><td>{t['starting_price']}</td></tr>
          <tr><td>Free tier</td><td>{'<span class="tick">✓</span>' if t.get('free_tier') else '<span class="cross">✗</span>'}</td></tr>
          <tr><td>Free trial</td><td>{'<span class="tick">✓ '+str(t['trial_days'])+'d</span>' if t.get('free_trial') else '<span class="cross">✗</span>'}</td></tr>
          <tr><td>Pricing model</td><td>{t['pricing_model']}</td></tr>"""
        return f"""<div class="cd-tool {w}">
          {wb}
          <div class="cd-tool-name">{t['name']}</div>
          <div class="cd-tool-score" style="color:{sc_col}">{sc}</div>
          <p class="cd-tool-tagline">{t['tagline']}</p>
          <table class="compare-table" style="margin-bottom:14px"><tbody>{rows}</tbody></table>
          <p class="cd-verdict">{c['verdict_a'] if t['slug']==c['tool_a'] else c['verdict_b']}</p>
          <a href="{t['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener"
            class="btn-try" style="margin-top:14px;width:100%;justify-content:center">
            Try {t['name']} →</a>
        </div>"""

    winner_html = ''
    if c.get('winner_reason'):
        winner_name = winner['name'] if winner else 'It depends'
        winner_html = f"""<div class="cd-winner-reason rv">
          <div class="cd-wr-title">// Our verdict: {winner_name}</div>
          <div class="cd-wr-text">{c['winner_reason']}</div>
        </div>"""

    content = f"""
    <div class="page">
      <div class="breadcrumb"><a href="/">Home</a><span>/</span><a href="/compare">Compare</a><span>/</span><span>{c['headline']}</span></div>
      <div style="margin-bottom:28px">
        <div class="sec-kicker">{datetime.datetime.strptime(c['date'],'%Y-%m-%d').strftime('%d %b %Y')} · Head to head</div>
        <h1 style="font-family:Bricolage Grotesque,sans-serif;font-size:clamp(2rem,4.5vw,3.4rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1;margin-bottom:10px">
          {c['headline']}
        </h1>
        <p style="font-size:.97rem;color:var(--ink3);font-weight:300;max-width:540px">{c['description']}</p>
      </div>
      <div class="cd-grid">
        {cd_tool_html(ta, winner and winner['slug']==ta['slug'])}
        {cd_tool_html(tb, winner and winner['slug']==tb['slug'])}
      </div>
      {winner_html}
    </div>
    {email_capture()}"""

    return render(
        title=f'{c["headline"]} 2026 — Which Is Better? | Moving Forward With AI',
        desc=c.get('meta_description', c['description']),
        content=content,
        bcs=bc_schema([('Home','/'),('Compare','/compare'),(c['headline'],f'/compare/{slug}')]))


@app.route('/blog')
def blog():
    posts = sorted([{**v,'slug':k} for k,v in BLOG_POSTS.items()], key=lambda x:x['date'], reverse=True)
    cards = '\n'.join(f"""<a href="/blog/{p['slug']}" class="blog-card rv">
      <div class="blog-card-body">
        <div class="blog-date">{datetime.datetime.strptime(p['date'],'%Y-%m-%d').strftime('%d %b %Y')} · {p.get('category','Guide')}</div>
        <div class="blog-title">{p['title']}</div>
        <div class="blog-desc">{p.get('description','')}</div>
        <div class="blog-more">Read →</div>
      </div>
    </a>""" for p in posts)
    content = f"""
    <div class="page">
      <div class="breadcrumb"><a href="/">Home</a><span>/</span><span>Guides</span></div>
      <div style="margin-bottom:28px">
        <div class="sec-kicker">Guides · How-tos · Analysis</div>
        <h1 style="font-family:Bricolage Grotesque,sans-serif;font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1">
          AI tool <em style="color:var(--cyan);font-style:normal">guides</em>
        </h1>
      </div>
      <div class="blog-grid">{cards}</div>
    </div>"""
    return render('AI Tool Guides for UK Freelancers — Moving Forward With AI',
        'In-depth guides, comparisons and how-tos for AI tools. Honest, independent, updated regularly.',
        content)


@app.route('/blog/<slug>')
def blog_detail(slug):
    post = BLOG_POSTS.get(slug)
    if not post: abort(404)
    dt = datetime.datetime.strptime(post['date'],'%Y-%m-%d').strftime('%d %B %Y')
    related = [get_tool(s) for s in post.get('related_tools',[]) if get_tool(s)]
    rel_cards = '\n'.join(tool_card(t) for t in related)
    role_cta = ''
    if post.get('related_role'):
        role = get_role(post['related_role'])
        if role:
            role_cta = f"""<div style="background:var(--cyan-d);border:1px solid rgba(34,211,238,.18);border-radius:var(--r3);padding:20px 22px;margin:36px 0">
              <div style="font-family:JetBrains Mono,monospace;font-size:.58rem;color:var(--cyan);letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px">→ Related guide</div>
              <div style="font-family:Bricolage Grotesque,sans-serif;font-size:1.05rem;font-weight:700;color:var(--ink);margin-bottom:6px">{role['icon']} {role['headline']}</div>
              <a href="/for/{role['slug']}" style="font-family:JetBrains Mono,monospace;font-size:.68rem;color:var(--cyan);letter-spacing:.06em;text-transform:uppercase">See the full stack →</a>
            </div>"""
    content = f"""
    <div class="page">
      <div class="breadcrumb"><a href="/">Home</a><span>/</span><a href="/blog">Guides</a><span>/</span><span>{post['title'][:40]}…</span></div>
      <div style="max-width:680px;margin:0 auto">
        <div style="font-family:JetBrains Mono,monospace;font-size:.58rem;letter-spacing:.18em;text-transform:uppercase;color:var(--cyan);margin-bottom:16px;display:flex;align-items:center;gap:7px"><span>→</span>{dt} · {post.get('category','Guide')}</div>
        <h1 style="font-family:Bricolage Grotesque,sans-serif;font-size:clamp(1.9rem,4.5vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1.06;margin-bottom:14px">{post.get('heading',post['title'])}</h1>
        <p style="font-size:1rem;line-height:1.78;color:var(--ink3);margin-bottom:40px;padding-bottom:32px;border-bottom:1px solid var(--div);font-weight:300">{post.get('description','')}</p>
        <div class="prose">{post.get('content','')}</div>
        {role_cta}
      </div>
    </div>
    {'<div class="page"><div class="sec"><div class="sec-top"><div><div class="sec-kicker">Mentioned in this guide</div><h2 class="sec-h2">Related <em>tools</em></h2></div></div><div class="tools-grid">'+rel_cards+"</div></div></div>" if rel_cards else ""}
    {email_capture()}"""
    return render(
        title=post['title']+' — Moving Forward With AI',
        desc=post.get('meta_description', post.get('description','')),
        content=content,
        bcs=bc_schema([('Home','/'),('Guides','/blog'),(post['title'],f'/blog/{slug}')]))


@app.route('/category/<cat_slug>')
def category(cat_slug):
    tools = [t for t in TOOLS if slugify(t['category'])==cat_slug]
    if not tools: abort(404)
    cat_name = tools[0]['category']
    cards = '\n'.join(tool_card(t) for t in tools)
    content = f"""
    <div class="page">
      <div class="breadcrumb"><a href="/">Home</a><span>/</span><a href="/tools">Tools</a><span>/</span><span>{cat_name}</span></div>
      <div style="margin-bottom:28px">
        <div class="sec-kicker">{cat_name} · {len(tools)} tools</div>
        <h1 style="font-family:Bricolage Grotesque,sans-serif;font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1">
          Best <em style="color:var(--cyan);font-style:normal">{cat_name}</em> tools
        </h1>
      </div>
      <div class="tools-grid">{cards}</div>
    </div>"""
    return render(f'Best {cat_name} AI Tools 2026 | Moving Forward With AI',
        f'Honest reviews of the best {cat_name.lower()} AI tools for UK users in 2026.',
        content,
        bcs=bc_schema([('Home','/'),('Tools','/tools'),(cat_name,f'/category/{cat_slug}')]))


@app.route('/affiliate-disclosure')
def affiliate_disclosure():
    content = """<div class="legal-wrap">
      <h1 style="font-family:Bricolage Grotesque,sans-serif;font-size:2.4rem;font-weight:800;letter-spacing:-.05em;color:var(--ink);margin-bottom:24px">Affiliate Disclosure</h1>
      <div class="legal-card"><p><strong>Last updated:</strong> February 2026</p>
        <p>Moving Forward With AI earns affiliate commissions from some tools reviewed on this site. When you click a link and sign up or purchase, we may receive a commission — at no extra cost to you.</p></div>
      <p>Our editorial process is entirely independent of commercial relationships. Tools are scored and ranked on merit. We do not accept payment for reviews, rankings, or placement.</p>
      <p>For questions: <a href="mailto:hello@movingforwardwithai.com" style="color:var(--cyan)">hello@movingforwardwithai.com</a></p>
    </div>"""
    return render('Affiliate Disclosure — Moving Forward With AI',
        'How Moving Forward With AI earns commissions while maintaining editorial independence.', content)


@app.route('/privacy')
def privacy():
    content = """<div class="legal-wrap">
      <h1 style="font-family:Bricolage Grotesque,sans-serif;font-size:2.4rem;font-weight:800;letter-spacing:-.05em;color:var(--ink);margin-bottom:24px">Privacy Policy</h1>
      <div class="legal-card"><p><strong>Last updated:</strong> February 2026</p>
        <p>Moving Forward With AI is committed to protecting your privacy in accordance with UK GDPR.</p></div>
      <h2>Information we collect</h2>
      <p>We collect minimal data via cookies and analytics. We do not collect personal information directly unless you contact us or sign up for our email list.</p>
      <h2>Your rights (UK GDPR)</h2>
      <p>You have the right to access, correct, delete and port your data. Contact <a href="mailto:hello@movingforwardwithai.com" style="color:var(--cyan)">hello@movingforwardwithai.com</a>.</p>
    </div>"""
    return render('Privacy Policy — Moving Forward With AI',
        'Moving Forward With AI privacy policy — UK GDPR compliant.', content)


@app.route('/terms')
def terms():
    content = """<div class="legal-wrap">
      <h1 style="font-family:Bricolage Grotesque,sans-serif;font-size:2.4rem;font-weight:800;letter-spacing:-.05em;color:var(--ink);margin-bottom:24px">Terms of Service</h1>
      <div class="legal-card"><p>By using movingforwardwithai.com you accept these terms.</p></div>
      <h2>About this site</h2>
      <p>Moving Forward With AI is an independent review and affiliate marketing website. We are not affiliated with or endorsed by any tool we review.</p>
      <h2>Accuracy</h2>
      <p>Prices and features are verified at time of writing. Always confirm current pricing on the tool's official website before purchasing.</p>
    </div>"""
    return render('Terms of Service — Moving Forward With AI',
        'Terms and conditions for using Moving Forward With AI.', content)


@app.route('/api/tools')
def api_tools():
    return jsonify({'tools':[{
        'slug':t['slug'],'name':t['name'],'category':t['category'],
        'tagline':t['tagline'],'score':t['score'],'rating':t['rating'],
        'starting_price':t['starting_price'],'tags':t.get('tags',[]),
        'featured':t.get('featured',False)} for t in TOOLS]})


@app.route('/robots.txt')
def robots():
    return Response(f'User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n', mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    today = datetime.date.today().isoformat()
    urls = [
        (SITE_URL+'/', today, '1.0', 'weekly'),
        (SITE_URL+'/tools', today, '0.9', 'weekly'),
        (SITE_URL+'/compare', today, '0.9', 'weekly'),
        (SITE_URL+'/blog', today, '0.8', 'weekly'),
    ]
    for t in TOOLS:
        urls.append((f'{SITE_URL}/tool/{t["slug"]}', t.get('date_added',today), '0.8', 'monthly'))
    for r in ROLES:
        urls.append((f'{SITE_URL}/for/{r["slug"]}', today, '0.8', 'weekly'))
    for c in COMPARISONS:
        urls.append((f'{SITE_URL}/compare/{c["slug"]}', c.get('date',today), '0.8', 'monthly'))
    for slug,post in BLOG_POSTS.items():
        urls.append((f'{SITE_URL}/blog/{slug}', post.get('date',today), '0.7', 'monthly'))
    cats = list({slugify(t['category']) for t in TOOLS})
    for cat in cats:
        urls.append((f'{SITE_URL}/category/{cat}', today, '0.6', 'monthly'))
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url,lm,pri,cf in sorted(urls):
        xml += f'  <url><loc>{url}</loc><lastmod>{lm}</lastmod><changefreq>{cf}</changefreq><priority>{pri}</priority></url>\n'
    return Response(xml+'</urlset>', mimetype='application/xml')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',8080)))
