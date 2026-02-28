# MOVING FORWARD WITH AI — app.py v3.0 (Elite Redesign)
# Architecture: Role pages + Comparison pages + Email capture + Tool reviews
# Deploy: GitHub → Render.com
# Redesign: Premium 2026 aesthetic — dark/light, refined typography, elite UX
# ============================================================================

import os, json, re, datetime
from data import TOOLS, COMPARISONS, BLOG_POSTS, LEAD_MAGNET, ROLES
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

def score_label(s):
    if s>=92: return 'Outstanding'
    if s>=88: return 'Excellent'
    if s>=80: return 'Very Good'
    if s>=75: return 'Good'
    return 'Decent'

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


# ═══════════════════════════════════════════════════════════════════════════════
# ELITE CSS — Premium 2026 Design System
# ═══════════════════════════════════════════════════════════════════════════════
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700;800;900&family=Geist+Mono:wght@300;400;500;600&display=swap');

/* ── Design Tokens ─────────────────────────────────────────────────────────── */
:root {
  /* Dark Mode (default) — deep navy/slate inspired by Linear */
  --bg:       #060810;
  --bg2:      #090c16;
  --bg3:      #0d1120;
  --bg4:      #111628;
  --surf:     #0f1422;
  --surf2:    #141930;
  --surf3:    #19203c;

  --ink:      #eef1fb;
  --ink2:     #bcc8e8;
  --ink3:     #7c8db5;
  --ink4:     #3e4d6e;
  --ink5:     #232d47;

  --cyan:     #4f9cf9;
  --cyan2:    #7ab8ff;
  --cyan-d:   rgba(79,156,249,.08);
  --cyan-g:   rgba(79,156,249,.16);
  --cyan-glow:rgba(79,156,249,.24);

  --amber:    #f0a429;
  --amber2:   #f7c05a;
  --amber-d:  rgba(240,164,41,.08);
  --amber-g:  rgba(240,164,41,.20);

  --green:    #22c55e;
  --green2:   #4ade80;
  --green-d:  rgba(34,197,94,.08);
  --green-g:  rgba(34,197,94,.18);

  --rose:     #f43f5e;
  --rose-d:   rgba(244,63,94,.08);
  --rose-g:   rgba(244,63,94,.18);

  --violet:   #8b5cf6;
  --violet-d: rgba(139,92,246,.08);

  --bdr:      rgba(79,156,249,.07);
  --bdr2:     rgba(79,156,249,.13);
  --bdr3:     rgba(79,156,249,.22);
  --div:      rgba(238,241,251,.04);
  --nav-bg:   rgba(6,8,16,.88);

  --r1: 5px; --r2: 10px; --r3: 16px; --r4: 22px; --rpill: 999px;

  --ease:   cubic-bezier(.16,1,.3,1);
  --spring: cubic-bezier(.34,1.56,.64,1);
  --slide:  cubic-bezier(.25,.46,.45,.94);

  --sh0: 0 1px 3px rgba(0,0,0,.4);
  --sh1: 0 2px 16px rgba(0,0,0,.6), 0 0 0 1px var(--bdr);
  --sh2: 0 8px 40px rgba(0,0,0,.7), 0 0 0 1px var(--bdr2);
  --sh3: 0 20px 80px rgba(0,0,0,.8), 0 0 0 1px var(--bdr2);
  --shc: 0 4px 20px rgba(79,156,249,.25), 0 0 0 1px rgba(79,156,249,.2);
  --sha: 0 4px 20px rgba(240,164,41,.22), 0 0 0 1px rgba(240,164,41,.15);
  --shg: 0 4px 20px rgba(34,197,94,.22), 0 0 0 1px rgba(34,197,94,.15);

  --font-display: 'Geist', system-ui, sans-serif;
  --font-body:    'Geist', system-ui, sans-serif;
  --font-mono:    'Geist Mono', 'Fira Code', monospace;
  --font-serif:   'Instrument Serif', Georgia, serif;
}

/* Light Mode */
html.light,
.light {
  --bg:       #fafbff;
  --bg2:      #f4f6fd;
  --bg3:      #edf0f9;
  --bg4:      #e5eaf6;
  --surf:     #ffffff;
  --surf2:    #f8f9fe;
  --surf3:    #f0f3fc;

  --ink:      #0d1117;
  --ink2:     #1e293b;
  --ink3:     #475569;
  --ink4:     #94a3b8;
  --ink5:     #cbd5e1;

  --cyan:     #2563eb;
  --cyan2:    #1d4ed8;
  --cyan-d:   rgba(37,99,235,.06);
  --cyan-g:   rgba(37,99,235,.12);
  --cyan-glow:rgba(37,99,235,.18);

  --amber:    #d97706;
  --amber2:   #b45309;
  --amber-d:  rgba(217,119,6,.06);
  --amber-g:  rgba(217,119,6,.14);

  --green:    #16a34a;
  --green2:   #15803d;
  --green-d:  rgba(22,163,74,.06);
  --green-g:  rgba(22,163,74,.14);

  --rose:     #e11d48;
  --rose-d:   rgba(225,29,72,.06);

  --bdr:      rgba(37,99,235,.08);
  --bdr2:     rgba(37,99,235,.14);
  --bdr3:     rgba(37,99,235,.24);
  --div:      rgba(13,17,23,.06);
  --nav-bg:   rgba(250,251,255,.92);

  --sh0: 0 1px 3px rgba(0,0,0,.05);
  --sh1: 0 2px 16px rgba(0,0,0,.06), 0 0 0 1px var(--bdr);
  --sh2: 0 8px 40px rgba(0,0,0,.09), 0 0 0 1px var(--bdr2);
  --sh3: 0 20px 80px rgba(0,0,0,.12), 0 0 0 1px var(--bdr2);
  --shc: 0 4px 20px rgba(37,99,235,.15), 0 0 0 1px rgba(37,99,235,.18);
  --sha: 0 4px 20px rgba(217,119,6,.15), 0 0 0 1px rgba(217,119,6,.14);
  --shg: 0 4px 20px rgba(22,163,74,.15), 0 0 0 1px rgba(22,163,74,.14);
}

/* ── Reset & Base ───────────────────────────────────────────────────────────── */
*, *::before, *::after { margin:0; padding:0; box-sizing:border-box }
html { scroll-behavior:smooth; -webkit-text-size-adjust:100% }
body {
  background:var(--bg);
  color:var(--ink);
  font-family:var(--font-body);
  font-size:15px;
  line-height:1.65;
  overflow-x:hidden;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
  transition:background .3s var(--slide), color .3s var(--slide);
}
a { text-decoration:none; color:inherit }
button { font-family:inherit; cursor:pointer; border:none; background:none }
img { display:block; max-width:100% }
svg { flex-shrink:0 }

/* ── Subtle Background Texture ─────────────────────────────────────────────── */
body::before {
  content:'';
  position:fixed;
  inset:0;
  pointer-events:none;
  z-index:0;
  background-image:
    radial-gradient(ellipse 80% 60% at 20% -10%, rgba(79,156,249,.06) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 120%, rgba(139,92,246,.04) 0%, transparent 60%);
}
.light body::before {
  background-image:
    radial-gradient(ellipse 80% 60% at 20% -10%, rgba(37,99,235,.04) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 120%, rgba(139,92,246,.025) 0%, transparent 60%);
}

/* Subtle grid pattern */
body::after {
  content:'';
  position:fixed;
  inset:0;
  pointer-events:none;
  z-index:0;
  background-image:
    linear-gradient(var(--div) 1px, transparent 1px),
    linear-gradient(90deg, var(--div) 1px, transparent 1px);
  background-size:64px 64px;
  mask-image:radial-gradient(ellipse at center, black 20%, transparent 75%);
}

/* ── Ticker Bar ─────────────────────────────────────────────────────────────── */
.ticker {
  position:relative;
  z-index:10;
  background:var(--surf);
  border-bottom:1px solid var(--bdr);
  padding:8px 0;
  overflow:hidden;
  white-space:nowrap;
}
.ticker-track {
  display:inline-flex;
  animation:ticker-move 55s linear infinite;
}
.ticker:hover .ticker-track { animation-play-state:paused }
.ticker-item {
  display:inline-flex;
  align-items:center;
  gap:0;
  font-family:var(--font-mono);
  font-size:.62rem;
  letter-spacing:.14em;
  text-transform:uppercase;
  color:var(--ink4);
  padding:0 18px;
}
.ticker-item.accent { color:var(--cyan); opacity:.9 }
.ticker-sep {
  color:var(--ink5);
  padding:0 4px;
  font-size:.5rem;
}
@keyframes ticker-move {
  from { transform:translateX(0) }
  to   { transform:translateX(-50%) }
}

/* ── Navigation ─────────────────────────────────────────────────────────────── */
.nav {
  position:sticky;
  top:0;
  z-index:200;
  background:var(--nav-bg);
  backdrop-filter:blur(24px) saturate(180%);
  -webkit-backdrop-filter:blur(24px) saturate(180%);
  border-bottom:1px solid var(--bdr);
  transition:box-shadow .3s, border-color .3s, background .3s;
}
.nav.scrolled {
  box-shadow:0 4px 32px rgba(0,0,0,.5);
  border-bottom-color:var(--bdr2);
}
.nav-in {
  max-width:1440px;
  margin:0 auto;
  padding:0 40px;
  display:flex;
  align-items:center;
  height:60px;
  gap:8px;
}
.nav-logo {
  font-family:var(--font-display);
  font-size:.92rem;
  font-weight:700;
  letter-spacing:-.03em;
  color:var(--ink);
  flex-shrink:0;
  margin-right:20px;
  display:flex;
  align-items:center;
  gap:7px;
  transition:opacity .2s;
}
.nav-logo:hover { opacity:.75 }
.logo-mark {
  display:flex;
  align-items:center;
  gap:5px;
}
.logo-icon {
  width:28px;
  height:28px;
  background:var(--cyan);
  border-radius:8px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:.7rem;
  color:#060810;
  font-weight:800;
  letter-spacing:-.04em;
  flex-shrink:0;
  transition:transform .2s var(--spring), box-shadow .2s;
  box-shadow:var(--shc);
}
.nav-logo:hover .logo-icon {
  transform:scale(1.08);
  box-shadow:0 4px 24px rgba(79,156,249,.4);
}
.logo-wordmark { color:var(--ink); font-weight:600 }
.logo-wordmark em { font-style:normal; color:var(--cyan) }

.nav-links {
  display:flex;
  align-items:center;
  gap:2px;
  flex:1;
}
.nav-links > a,
.nav-drop-btn {
  font-size:.84rem;
  font-weight:500;
  color:var(--ink3);
  padding:6px 12px;
  border-radius:var(--r2);
  transition:color .15s, background .15s;
  letter-spacing:-.01em;
  display:flex;
  align-items:center;
  gap:5px;
  white-space:nowrap;
}
.nav-links > a:hover,
.nav-drop-btn:hover { color:var(--ink); background:var(--cyan-d) }
.nav-links > a.active { color:var(--cyan) }

.nav-drop { position:relative }
.drop-chevron {
  width:12px; height:12px;
  stroke:currentColor; fill:none; stroke-width:2;
  transition:transform .2s var(--ease);
}
.nav-drop.open .drop-chevron { transform:rotate(180deg) }
.drop-menu {
  display:none;
  position:absolute;
  top:calc(100% + 10px);
  left:0;
  background:var(--surf2);
  border:1px solid var(--bdr2);
  border-radius:var(--r3);
  padding:6px;
  min-width:210px;
  box-shadow:var(--sh3);
  z-index:300;
}
.nav-drop.open .drop-menu {
  display:block;
  animation:dropIn .18s var(--ease);
}
@keyframes dropIn {
  from { opacity:0; transform:translateY(-8px) scale(.98) }
  to   { opacity:1; transform:translateY(0) scale(1) }
}
.drop-menu a {
  display:flex;
  align-items:center;
  gap:10px;
  padding:9px 12px;
  border-radius:var(--r2);
  font-size:.84rem;
  color:var(--ink3);
  transition:all .13s;
}
.drop-menu a:hover { background:var(--cyan-d); color:var(--ink) }
.drop-menu .dm-icon { font-size:1.05rem; flex-shrink:0 }

/* Search */
.nav-search { position:relative; display:flex; align-items:center }
.search-ico {
  position:absolute; left:11px;
  width:14px; height:14px;
  stroke:var(--ink4); fill:none; stroke-width:1.8;
  pointer-events:none; z-index:1;
}
.nav-search input {
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--rpill);
  padding:7px 14px 7px 34px;
  font-family:var(--font-mono);
  font-size:.75rem;
  color:var(--ink);
  width:180px;
  outline:none;
  transition:all .25s var(--ease);
  letter-spacing:.02em;
}
.nav-search input:focus {
  width:240px;
  border-color:var(--cyan);
  box-shadow:0 0 0 3px var(--cyan-d);
  background:var(--surf2);
}
.nav-search input::placeholder { color:var(--ink4) }

/* Theme toggle & icon buttons */
.nav-right { display:flex; align-items:center; gap:6px; flex-shrink:0 }
.nav-icon-btn {
  width:36px; height:36px;
  border-radius:var(--r2);
  border:1px solid var(--bdr);
  background:var(--surf);
  display:flex; align-items:center; justify-content:center;
  transition:all .18s;
  flex-shrink:0;
}
.nav-icon-btn:hover { background:var(--cyan-d); border-color:var(--bdr2) }
.nav-icon-btn svg { width:15px; height:15px; stroke:var(--ink3); fill:none; stroke-width:1.8 }

/* Hamburger */
#hbg {
  display:none;
  flex-direction:column;
  justify-content:center;
  align-items:center;
  gap:5px;
  width:36px; height:36px;
  border:1px solid var(--bdr);
  border-radius:var(--r2);
  background:var(--surf);
  flex-shrink:0;
}
#hbg span {
  display:block;
  width:16px; height:1.5px;
  background:var(--ink);
  border-radius:2px;
  transition:all .25s var(--ease);
  transform-origin:center;
}
#hbg.open span:nth-child(1) { transform:translateY(6.5px) rotate(45deg) }
#hbg.open span:nth-child(2) { opacity:0; transform:scaleX(0) }
#hbg.open span:nth-child(3) { transform:translateY(-6.5px) rotate(-45deg) }

/* Mobile Menu */
#mob {
  display:none;
  position:fixed;
  inset:0;
  background:var(--bg);
  z-index:190;
  overflow-y:auto;
  padding:72px 24px 48px;
  flex-direction:column;
  gap:0;
}
#mob.open {
  display:flex;
  animation:mobIn .28s var(--ease);
}
@keyframes mobIn {
  from { opacity:0; transform:translateY(-12px) }
  to   { opacity:1; transform:translateY(0) }
}
.mob-section { padding:24px 0; border-bottom:1px solid var(--div) }
.mob-section:first-child { padding-top:0 }
.mob-primary-links { display:flex; flex-direction:column; gap:4px }
.mob-link {
  font-family:var(--font-display);
  font-size:2rem;
  font-weight:700;
  color:var(--ink);
  padding:8px 0;
  display:block;
  letter-spacing:-.04em;
  transition:color .15s, padding-left .2s var(--ease);
}
.mob-link:hover { color:var(--cyan); padding-left:8px }
.mob-sublabel {
  font-family:var(--font-mono);
  font-size:.58rem;
  letter-spacing:.2em;
  text-transform:uppercase;
  color:var(--cyan);
  margin-bottom:14px;
  display:flex;
  align-items:center;
  gap:8px;
}
.mob-sublabel::after { content:''; flex:1; height:1px; background:var(--bdr2) }
.mob-pills { display:flex; flex-wrap:wrap; gap:7px }
.mob-pill {
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--rpill);
  padding:8px 16px;
  font-size:.84rem;
  color:var(--ink3);
  transition:all .18s;
  display:inline-flex;
  align-items:center;
  gap:6px;
}
.mob-pill:hover { background:var(--cyan-d); border-color:var(--bdr2); color:var(--ink) }

/* ── Layout ─────────────────────────────────────────────────────────────────── */
.page {
  max-width:1440px;
  margin:0 auto;
  padding:0 40px;
  position:relative;
  z-index:1;
}
.page-narrow {
  max-width:720px;
  margin:0 auto;
  padding:0 40px;
  position:relative;
  z-index:1;
}

/* ── Breadcrumbs ────────────────────────────────────────────────────────────── */
.breadcrumb {
  display:flex;
  align-items:center;
  gap:8px;
  font-family:var(--font-mono);
  font-size:.68rem;
  color:var(--ink4);
  padding:clamp(28px,4vw,48px) 0 0;
  flex-wrap:wrap;
  letter-spacing:.02em;
}
.breadcrumb a { color:var(--ink3); transition:color .15s }
.breadcrumb a:hover { color:var(--cyan) }
.breadcrumb .sep {
  width:14px; height:14px;
  stroke:var(--ink5); fill:none; stroke-width:1.5;
  flex-shrink:0;
}
.breadcrumb .current { color:var(--ink) }

/* ── Section Headers ────────────────────────────────────────────────────────── */
.sec { padding:clamp(64px,8vw,96px) 0 0 }
.sec-top {
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:20px;
  margin-bottom:32px;
}
.sec-eyebrow {
  font-family:var(--font-mono);
  font-size:.65rem;
  letter-spacing:.16em;
  text-transform:uppercase;
  color:var(--cyan);
  margin-bottom:10px;
  display:flex;
  align-items:center;
  gap:8px;
}
.sec-eyebrow::before { content:''; width:20px; height:1px; background:var(--cyan); flex-shrink:0 }
.sec-h2 {
  font-family:var(--font-display);
  font-size:clamp(1.8rem,3vw,2.7rem);
  font-weight:700;
  letter-spacing:-.04em;
  color:var(--ink);
  line-height:1.05;
}
.sec-h2 em { font-style:normal; color:var(--cyan) }
.sec-link {
  font-family:var(--font-mono);
  font-size:.7rem;
  color:var(--cyan);
  display:flex;
  align-items:center;
  gap:5px;
  letter-spacing:.04em;
  text-transform:uppercase;
  transition:gap .2s;
  white-space:nowrap;
  flex-shrink:0;
  padding-bottom:1px;
  border-bottom:1px solid var(--cyan-g);
}
.sec-link:hover { gap:9px; border-bottom-color:var(--cyan) }

/* ── Hero ───────────────────────────────────────────────────────────────────── */
.hero {
  padding:clamp(72px,10vw,128px) 0 clamp(56px,7vw,88px);
  display:grid;
  grid-template-columns:1fr 400px;
  gap:clamp(56px,8vw,100px);
  align-items:center;
  position:relative;
}
.hero-eyebrow {
  display:inline-flex;
  align-items:center;
  gap:9px;
  margin-bottom:24px;
  font-family:var(--font-mono);
  font-size:.65rem;
  font-weight:400;
  letter-spacing:.14em;
  text-transform:uppercase;
  color:var(--cyan);
}
.hero-eyebrow-dot {
  width:6px; height:6px;
  border-radius:50%;
  background:var(--cyan);
  animation:pulse 2.5s ease-in-out infinite;
}
@keyframes pulse {
  0%,100% { opacity:1; transform:scale(1) }
  50%      { opacity:.5; transform:scale(.8) }
}
.hero-h1 {
  font-family:var(--font-display);
  font-size:clamp(3rem,6.5vw,5.8rem);
  font-weight:800;
  line-height:.96;
  letter-spacing:-.05em;
  color:var(--ink);
  margin-bottom:24px;
}
.hero-h1 em { font-style:normal; color:var(--cyan) }
.hero-h1 .serif-accent {
  font-family:var(--font-serif);
  font-style:italic;
  font-weight:400;
  font-size:.92em;
  color:var(--ink2);
  display:block;
  margin-top:6px;
  letter-spacing:-.02em;
}
.hero-sub {
  font-size:1.02rem;
  line-height:1.8;
  color:var(--ink3);
  max-width:480px;
  margin-bottom:36px;
  font-weight:400;
}
.role-selector { margin-bottom:36px }
.role-label {
  font-family:var(--font-mono);
  font-size:.62rem;
  letter-spacing:.14em;
  text-transform:uppercase;
  color:var(--ink4);
  margin-bottom:12px;
}
.role-chips { display:flex; flex-wrap:wrap; gap:8px }
.role-chip {
  display:inline-flex;
  align-items:center;
  gap:7px;
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--rpill);
  padding:8px 16px;
  font-size:.85rem;
  font-weight:500;
  color:var(--ink3);
  transition:all .2s var(--ease);
}
.role-chip:hover {
  background:var(--cyan-d);
  border-color:var(--bdr2);
  color:var(--ink);
  transform:translateY(-2px);
  box-shadow:var(--sh0);
}
.chip-icon { font-size:.95rem }
.hero-ctas {
  display:flex;
  align-items:center;
  gap:12px;
  flex-wrap:wrap;
  margin-bottom:48px;
}
.stats-row {
  display:flex;
  gap:36px;
  padding-top:36px;
  border-top:1px solid var(--div);
  flex-wrap:wrap;
}
.stat-item {}
.stat-num {
  font-family:var(--font-display);
  font-size:2rem;
  font-weight:800;
  letter-spacing:-.05em;
  color:var(--ink);
  line-height:1;
}
.stat-num em { font-style:normal; color:var(--cyan) }
.stat-lbl {
  font-family:var(--font-mono);
  font-size:.6rem;
  color:var(--ink4);
  letter-spacing:.1em;
  text-transform:uppercase;
  margin-top:5px;
}

/* Hero Panel (leaderboard) */
.hero-panel {
  background:var(--surf);
  border:1px solid var(--bdr2);
  border-radius:var(--r4);
  overflow:hidden;
  box-shadow:var(--sh2);
  position:relative;
}
.hero-panel::before {
  content:'';
  position:absolute;
  top:0; left:0; right:0; height:2px;
  background:linear-gradient(90deg, var(--cyan), var(--violet), var(--cyan));
  background-size:200% 100%;
  animation:shimmer 3s ease-in-out infinite;
}
@keyframes shimmer {
  0%,100% { background-position:0% 50% }
  50%      { background-position:100% 50% }
}
.panel-hdr {
  padding:16px 20px;
  border-bottom:1px solid var(--div);
  display:flex;
  align-items:center;
  justify-content:space-between;
}
.panel-title {
  font-family:var(--font-mono);
  font-size:.64rem;
  color:var(--ink3);
  letter-spacing:.1em;
  text-transform:uppercase;
  display:flex;
  align-items:center;
  gap:7px;
}
.panel-title::before { content:''; width:14px; height:1px; background:var(--cyan) }
.panel-live {
  display:inline-flex;
  align-items:center;
  gap:5px;
  background:var(--green-d);
  border:1px solid var(--green-g);
  border-radius:var(--rpill);
  padding:3px 10px;
  font-family:var(--font-mono);
  font-size:.58rem;
  color:var(--green);
  letter-spacing:.08em;
  text-transform:uppercase;
}
.panel-live::before {
  content:'';
  width:5px; height:5px;
  border-radius:50%;
  background:var(--green);
  animation:blink 2s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1}50%{opacity:.25} }
.panel-list { padding:8px }
.ptool {
  display:flex;
  align-items:center;
  gap:14px;
  padding:10px 12px;
  border-radius:var(--r2);
  transition:background .15s;
  color:inherit;
}
.ptool:hover { background:var(--bg3) }
.ptool-rank {
  font-family:var(--font-mono);
  font-size:.62rem;
  color:var(--ink5);
  width:18px;
  text-align:center;
  flex-shrink:0;
  font-weight:500;
}
.ptool-info { flex:1; min-width:0 }
.ptool-name {
  font-family:var(--font-display);
  font-size:.9rem;
  font-weight:600;
  color:var(--ink2);
  letter-spacing:-.02em;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.ptool-cat {
  font-family:var(--font-mono);
  font-size:.58rem;
  color:var(--ink4);
  letter-spacing:.06em;
  text-transform:uppercase;
}
.ptool-score {
  font-family:var(--font-mono);
  font-size:.7rem;
  font-weight:600;
  padding:3px 10px;
  border-radius:var(--r1);
  flex-shrink:0;
}
.ps-hi { background:var(--green-d); border:1px solid var(--green-g); color:var(--green) }
.ps-md { background:var(--cyan-d); border:1px solid var(--cyan-g); color:var(--cyan) }
.panel-footer {
  margin:8px 8px 8px;
  background:var(--bg3);
  border:1px solid var(--bdr);
  border-radius:var(--r2);
  padding:12px;
  font-family:var(--font-mono);
  font-size:.68rem;
  color:var(--cyan);
  text-align:center;
  letter-spacing:.06em;
  text-transform:uppercase;
  transition:all .18s;
  display:block;
}
.panel-footer:hover { background:var(--cyan-d); border-color:var(--bdr2) }

/* ── Affiliate Strip ────────────────────────────────────────────────────────── */
.affil-strip {
  background:var(--surf);
  border-top:1px solid var(--bdr);
  border-bottom:1px solid var(--bdr);
}
.affil-in {
  max-width:1440px;
  margin:0 auto;
  padding:10px 40px;
  display:flex;
  align-items:center;
  gap:9px;
  font-family:var(--font-mono);
  font-size:.67rem;
  color:var(--ink4);
  letter-spacing:.02em;
}
.affil-icon { width:13px; height:13px; stroke:var(--cyan); fill:none; stroke-width:2 }
.affil-in strong { color:var(--ink3); font-weight:500 }
.affil-in a { color:var(--cyan); transition:opacity .15s }
.affil-in a:hover { opacity:.7 }

/* ── Buttons ────────────────────────────────────────────────────────────────── */
.btn-primary {
  display:inline-flex;
  align-items:center;
  gap:8px;
  background:var(--cyan);
  color:#060810;
  padding:13px 24px;
  border-radius:var(--rpill);
  font-family:var(--font-mono);
  font-size:.78rem;
  font-weight:600;
  letter-spacing:.04em;
  text-transform:uppercase;
  border:none;
  transition:all .2s var(--ease);
  box-shadow:var(--shc);
  white-space:nowrap;
}
.btn-primary:hover {
  background:var(--cyan2);
  transform:translateY(-2px);
  box-shadow:0 8px 32px rgba(79,156,249,.4);
}
.btn-primary svg { width:13px; height:13px; stroke:currentColor; fill:none; stroke-width:2.5 }

.btn-ghost {
  display:inline-flex;
  align-items:center;
  gap:8px;
  background:transparent;
  color:var(--ink2);
  padding:13px 22px;
  border-radius:var(--rpill);
  font-size:.9rem;
  font-weight:500;
  border:1px solid var(--bdr2);
  transition:all .18s;
  letter-spacing:-.01em;
  white-space:nowrap;
}
.btn-ghost:hover {
  background:var(--cyan-d);
  border-color:var(--bdr3);
  color:var(--cyan);
}

.btn-try {
  display:flex;
  align-items:center;
  justify-content:center;
  gap:8px;
  background:var(--cyan);
  color:#060810;
  padding:12px 18px;
  border-radius:var(--r2);
  font-family:var(--font-mono);
  font-size:.74rem;
  font-weight:600;
  letter-spacing:.04em;
  text-transform:uppercase;
  border:none;
  transition:all .18s;
  box-shadow:var(--shc);
}
.btn-try:hover {
  background:var(--cyan2);
  transform:translateY(-1px);
  box-shadow:0 8px 28px rgba(79,156,249,.35);
}
.btn-try svg { width:11px; height:11px; stroke:currentColor; fill:none; stroke-width:2.5 }

.btn-outline {
  display:block;
  text-align:center;
  padding:10px;
  border:1px solid var(--bdr);
  border-radius:var(--r2);
  font-family:var(--font-mono);
  font-size:.68rem;
  color:var(--ink4);
  letter-spacing:.04em;
  text-transform:uppercase;
  transition:all .18s;
}
.btn-outline:hover {
  color:var(--cyan);
  border-color:var(--bdr2);
  background:var(--cyan-d);
}

/* ── Tool Cards ─────────────────────────────────────────────────────────────── */
.tools-grid {
  display:grid;
  grid-template-columns:repeat(auto-fill, minmax(320px,1fr));
  gap:16px;
}
.tool-card {
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--r4);
  overflow:hidden;
  display:flex;
  flex-direction:column;
  position:relative;
  transition:transform .35s var(--spring), box-shadow .35s, border-color .25s;
  will-change:transform;
}
.tool-card:hover {
  transform:translateY(-5px);
  box-shadow:var(--sh2);
  border-color:var(--bdr2);
}
.tc-accent-bar {
  height:2px;
  background:linear-gradient(90deg, var(--cyan), transparent);
  opacity:0;
  transition:opacity .3s;
  flex-shrink:0;
}
.tool-card:hover .tc-accent-bar { opacity:1 }
.tc-body { padding:20px 20px 0; flex:1; display:flex; flex-direction:column }
.tc-meta {
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom:14px;
}
.tc-cat {
  font-family:var(--font-mono);
  font-size:.6rem;
  letter-spacing:.1em;
  text-transform:uppercase;
  color:var(--ink4);
  display:flex;
  align-items:center;
  gap:5px;
}
.tc-cat::before { content:'//'; opacity:.5 }
.tc-score {
  border-radius:var(--r1);
  padding:3px 10px;
  font-family:var(--font-mono);
  font-size:.67rem;
  font-weight:600;
}
.tc-name {
  font-family:var(--font-display);
  font-size:1.22rem;
  font-weight:700;
  letter-spacing:-.03em;
  color:var(--ink);
  display:block;
  margin-bottom:7px;
  transition:color .15s;
  line-height:1.2;
}
.tc-name:hover { color:var(--cyan) }
.tc-tagline {
  font-size:.86rem;
  line-height:1.65;
  color:var(--ink3);
  margin-bottom:14px;
  flex:1;
}
.tc-badges { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:16px }
.badge {
  display:inline-flex;
  align-items:center;
  gap:3px;
  border-radius:var(--rpill);
  padding:3px 10px;
  font-family:var(--font-mono);
  font-size:.59rem;
  letter-spacing:.06em;
  text-transform:uppercase;
  font-weight:500;
}
.b-free  { background:var(--green-d); border:1px solid var(--green-g); color:var(--green) }
.b-trial { background:var(--cyan-d);  border:1px solid var(--cyan-g);  color:var(--cyan) }
.b-paid  { background:var(--amber-d); border:1px solid var(--amber-g); color:var(--amber) }
.b-top   { background:var(--rose-d);  border:1px solid var(--rose-g);  color:var(--rose) }
.tc-divider { height:1px; background:var(--div); margin:0 -20px 16px }
.tc-footer { padding:0 20px 18px; margin-top:auto }
.tc-pricing {
  display:flex;
  align-items:baseline;
  gap:8px;
  margin-bottom:10px;
}
.tc-price {
  font-family:var(--font-display);
  font-size:1.1rem;
  font-weight:700;
  color:var(--ink);
  letter-spacing:-.03em;
}
.tc-model {
  font-family:var(--font-mono);
  font-size:.62rem;
  color:var(--ink4);
  letter-spacing:.04em;
  text-transform:uppercase;
}
.tc-rating {
  display:flex;
  align-items:center;
  gap:8px;
  margin-bottom:12px;
  font-family:var(--font-mono);
  font-size:.65rem;
  color:var(--ink4);
}
.tc-stars { color:var(--amber); font-size:.8rem; letter-spacing:-.04em }
.tc-btn-group { display:flex; flex-direction:column; gap:8px }

/* ── Role Cards ─────────────────────────────────────────────────────────────── */
.roles-grid {
  display:grid;
  grid-template-columns:repeat(auto-fill, minmax(240px,1fr));
  gap:14px;
}
.role-card {
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--r3);
  padding:24px;
  display:flex;
  flex-direction:column;
  gap:11px;
  transition:transform .3s var(--spring), box-shadow .3s, border-color .25s;
  position:relative;
  overflow:hidden;
}
.role-card:hover {
  transform:translateY(-4px);
  box-shadow:var(--sh2);
  border-color:var(--bdr2);
}
.rc-icon { font-size:2rem; line-height:1; display:block }
.rc-name {
  font-family:var(--font-display);
  font-size:1.05rem;
  font-weight:700;
  letter-spacing:-.03em;
  color:var(--ink);
}
.rc-desc {
  font-size:.85rem;
  color:var(--ink3);
  line-height:1.65;
  flex:1;
}
.rc-count {
  font-family:var(--font-mono);
  font-size:.62rem;
  color:var(--cyan);
  letter-spacing:.06em;
  text-transform:uppercase;
  display:flex;
  align-items:center;
  gap:5px;
}
.rc-count::before { content:'→' }
.rc-arrow {
  font-family:var(--font-mono);
  font-size:.68rem;
  color:var(--cyan);
  display:inline-flex;
  align-items:center;
  gap:5px;
  letter-spacing:.04em;
  transition:gap .2s;
  border-bottom:1px solid var(--cyan-g);
  padding-bottom:2px;
  width:fit-content;
}
.role-card:hover .rc-arrow { gap:9px; border-bottom-color:var(--cyan) }

/* ── Comparison Cards ───────────────────────────────────────────────────────── */
.comp-grid {
  display:grid;
  grid-template-columns:repeat(auto-fill, minmax(360px,1fr));
  gap:14px;
}
.comp-card {
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--r3);
  padding:24px;
  display:flex;
  flex-direction:column;
  gap:14px;
  transition:transform .3s var(--spring), box-shadow .3s, border-color .25s;
}
.comp-card:hover {
  transform:translateY(-3px);
  box-shadow:var(--sh2);
  border-color:var(--bdr2);
}
.comp-vs {
  display:flex;
  align-items:center;
  gap:12px;
  flex-wrap:wrap;
}
.comp-tool-name {
  font-family:var(--font-display);
  font-size:1.05rem;
  font-weight:700;
  color:var(--ink);
  letter-spacing:-.03em;
}
.comp-vs-tag {
  font-family:var(--font-mono);
  font-size:.58rem;
  color:var(--ink4);
  background:var(--bg3);
  border:1px solid var(--bdr);
  border-radius:var(--rpill);
  padding:3px 10px;
  letter-spacing:.1em;
  flex-shrink:0;
}
.comp-desc { font-size:.87rem; color:var(--ink3); line-height:1.7; flex:1 }
.comp-link {
  font-family:var(--font-mono);
  font-size:.68rem;
  color:var(--amber);
  display:inline-flex;
  align-items:center;
  gap:5px;
  letter-spacing:.04em;
  text-transform:uppercase;
  border-bottom:1px solid var(--amber-g);
  padding-bottom:2px;
  width:fit-content;
  transition:gap .2s, border-color .2s;
}
.comp-card:hover .comp-link { gap:9px; border-bottom-color:var(--amber) }

/* ── Blog Cards ─────────────────────────────────────────────────────────────── */
.blog-grid {
  display:grid;
  grid-template-columns:repeat(auto-fill, minmax(320px,1fr));
  gap:16px;
}
.blog-card {
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--r3);
  overflow:hidden;
  display:flex;
  flex-direction:column;
  color:inherit;
  transition:transform .3s var(--spring), box-shadow .3s, border-color .25s;
}
.blog-card:hover {
  transform:translateY(-4px);
  box-shadow:var(--sh2);
  border-color:var(--bdr2);
}
.blog-card-accent {
  height:2px;
  background:linear-gradient(90deg, var(--amber), transparent);
  opacity:0;
  transition:opacity .3s;
}
.blog-card:hover .blog-card-accent { opacity:1 }
.blog-card-body { padding:24px; flex:1; display:flex; flex-direction:column; gap:10px }
.blog-eyebrow {
  font-family:var(--font-mono);
  font-size:.62rem;
  color:var(--cyan);
  letter-spacing:.1em;
  text-transform:uppercase;
  display:flex;
  align-items:center;
  gap:6px;
}
.blog-eyebrow::before { content:'//'; opacity:.6 }
.blog-title {
  font-family:var(--font-display);
  font-size:1.1rem;
  font-weight:700;
  line-height:1.3;
  letter-spacing:-.03em;
  color:var(--ink);
  flex:1;
}
.blog-desc {
  font-size:.86rem;
  line-height:1.65;
  color:var(--ink3);
}
.blog-link {
  font-family:var(--font-mono);
  font-size:.66rem;
  color:var(--amber);
  display:inline-flex;
  align-items:center;
  gap:5px;
  transition:gap .2s;
  letter-spacing:.04em;
  text-transform:uppercase;
}
.blog-card:hover .blog-link { gap:9px }

/* ── Email Capture ──────────────────────────────────────────────────────────── */
.email-sec {
  position:relative;
  z-index:1;
  background:var(--surf);
  border-top:1px solid var(--bdr);
  border-bottom:1px solid var(--bdr);
  padding:clamp(64px,8vw,100px) 0;
  overflow:hidden;
}
.email-sec::before {
  content:'';
  position:absolute;
  top:0; left:0; right:0; bottom:0;
  background:radial-gradient(ellipse at 60% 50%, rgba(240,164,41,.04) 0%, transparent 65%);
  pointer-events:none;
}
.email-inner {
  max-width:1440px;
  margin:0 auto;
  padding:0 40px;
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:clamp(56px,8vw,100px);
  align-items:center;
  position:relative;
}
.email-eyebrow {
  font-family:var(--font-mono);
  font-size:.65rem;
  letter-spacing:.16em;
  text-transform:uppercase;
  color:var(--amber);
  margin-bottom:14px;
  display:flex;
  align-items:center;
  gap:8px;
}
.email-eyebrow::before { content:''; width:20px; height:1px; background:var(--amber) }
.email-h2 {
  font-family:var(--font-display);
  font-size:clamp(1.8rem,3vw,2.6rem);
  font-weight:700;
  letter-spacing:-.04em;
  color:var(--ink);
  margin-bottom:16px;
  line-height:1.1;
}
.email-h2 em { font-style:normal; color:var(--amber) }
.email-sub {
  font-size:.96rem;
  line-height:1.78;
  color:var(--ink3);
  margin-bottom:28px;
}
.email-form { display:flex; gap:8px; flex-wrap:wrap }
.email-input {
  flex:1;
  min-width:200px;
  background:var(--bg);
  border:1px solid var(--bdr2);
  border-radius:var(--r2);
  padding:13px 18px;
  color:var(--ink);
  font-family:var(--font-body);
  font-size:.9rem;
  outline:none;
  transition:border-color .2s, box-shadow .2s;
}
.email-input:focus {
  border-color:var(--amber);
  box-shadow:0 0 0 3px var(--amber-d);
}
.email-input::placeholder { color:var(--ink4) }
.btn-email {
  background:var(--amber);
  color:#060810;
  border:none;
  border-radius:var(--r2);
  padding:13px 24px;
  font-family:var(--font-mono);
  font-size:.78rem;
  font-weight:600;
  letter-spacing:.04em;
  text-transform:uppercase;
  transition:all .18s;
  box-shadow:var(--sha);
  white-space:nowrap;
}
.btn-email:hover {
  background:var(--amber2);
  transform:translateY(-1px);
  box-shadow:0 8px 28px rgba(240,164,41,.35);
}
.email-benefits { display:flex; flex-direction:column; gap:8px; margin-top:20px }
.email-benefit {
  display:flex;
  align-items:center;
  gap:9px;
  font-size:.86rem;
  color:var(--ink3);
}
.benefit-tick {
  width:16px; height:16px;
  background:var(--green-d);
  border:1px solid var(--green-g);
  border-radius:50%;
  display:flex;
  align-items:center;
  justify-content:center;
  flex-shrink:0;
  font-size:.6rem;
  color:var(--green);
  font-weight:700;
}
.email-notice {
  font-family:var(--font-mono);
  font-size:.6rem;
  color:var(--ink4);
  margin-top:14px;
  letter-spacing:.02em;
}
.email-visual {
  background:var(--surf2);
  border:1px solid var(--bdr2);
  border-radius:var(--r3);
  padding:30px;
  position:relative;
  overflow:hidden;
}
.email-visual::before {
  content:'';
  position:absolute;
  top:0; left:0; right:0; height:2px;
  background:linear-gradient(90deg, var(--amber), var(--cyan));
}
.ev-title {
  font-family:var(--font-display);
  font-size:1.1rem;
  font-weight:700;
  color:var(--ink);
  margin-bottom:5px;
  letter-spacing:-.03em;
}
.ev-subtitle {
  font-family:var(--font-mono);
  font-size:.64rem;
  color:var(--amber);
  letter-spacing:.1em;
  text-transform:uppercase;
  margin-bottom:20px;
}
.ev-items { display:flex; flex-direction:column; gap:12px }
.ev-item {
  display:flex;
  align-items:flex-start;
  gap:12px;
  font-size:.87rem;
  color:var(--ink3);
  line-height:1.6;
}
.ev-num {
  font-family:var(--font-mono);
  font-size:.62rem;
  font-weight:600;
  color:var(--amber);
  background:var(--amber-d);
  border:1px solid var(--amber-g);
  border-radius:var(--r1);
  padding:2px 8px;
  flex-shrink:0;
  margin-top:2px;
}

/* ── Role Detail Pages ──────────────────────────────────────────────────────── */
.rd-intro { padding:clamp(56px,7vw,88px) 0 0 }
.rd-icon { font-size:2.8rem; margin-bottom:16px; display:block }
.rd-h1 {
  font-family:var(--font-display);
  font-size:clamp(2.4rem,5vw,4.2rem);
  font-weight:800;
  letter-spacing:-.05em;
  color:var(--ink);
  margin-bottom:14px;
  line-height:1;
}
.rd-h1 em { font-style:normal; color:var(--cyan) }
.rd-sub {
  font-size:1.02rem;
  line-height:1.78;
  color:var(--ink3);
  max-width:560px;
  margin-bottom:32px;
}
.insight-box {
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--r3);
  padding:24px 26px;
  margin-bottom:20px;
}
.insight-box.pain {
  background:rgba(244,63,94,.03);
  border-color:rgba(244,63,94,.1);
}
.insight-box.solution {
  background:var(--cyan-d);
  border-color:var(--cyan-g);
}
.insight-label {
  font-family:var(--font-mono);
  font-size:.62rem;
  color:var(--ink4);
  letter-spacing:.14em;
  text-transform:uppercase;
  margin-bottom:14px;
}
.insight-box.pain .insight-label { color:var(--rose) }
.insight-box.solution .insight-label { color:var(--cyan) }
.pain-list { display:flex; flex-direction:column; gap:9px }
.pain-item {
  display:flex;
  align-items:flex-start;
  gap:10px;
  font-size:.89rem;
  color:var(--ink3);
  line-height:1.6;
}
.pain-x {
  color:var(--rose);
  flex-shrink:0;
  font-weight:700;
  font-size:.8rem;
  margin-top:3px;
}
.solution-text { font-size:.94rem; color:var(--ink2); line-height:1.78 }
.top-pick-bar {
  background:var(--surf);
  border:1px solid var(--bdr2);
  border-radius:var(--r3);
  padding:22px 24px;
  margin-bottom:18px;
  display:flex;
  align-items:center;
  gap:18px;
  flex-wrap:wrap;
}
.top-pick-badge {
  font-family:var(--font-mono);
  font-size:.62rem;
  background:var(--green-d);
  border:1px solid var(--green-g);
  color:var(--green);
  border-radius:var(--rpill);
  padding:4px 12px;
  letter-spacing:.08em;
  text-transform:uppercase;
  white-space:nowrap;
  flex-shrink:0;
}
.top-pick-info { flex:1; min-width:0 }
.top-pick-name {
  font-family:var(--font-display);
  font-size:1.2rem;
  font-weight:700;
  color:var(--ink);
  letter-spacing:-.03em;
}
.top-pick-tagline { font-size:.86rem; color:var(--ink3); margin-top:3px }
.top-pick-score {
  font-family:var(--font-display);
  font-size:2.2rem;
  font-weight:800;
  letter-spacing:-.06em;
  flex-shrink:0;
}

/* ── Tool Detail Page ───────────────────────────────────────────────────────── */
.td-wrapper { padding:clamp(48px,6vw,80px) 0 0 }
.td-header {
  background:var(--surf);
  border:1px solid var(--bdr2);
  border-radius:var(--r4);
  padding:36px;
  margin-bottom:24px;
  position:relative;
  overflow:hidden;
  box-shadow:var(--sh1);
}
.td-header::before {
  content:'';
  position:absolute;
  top:0; left:0; right:0; height:2px;
  background:linear-gradient(90deg, var(--cyan), var(--violet), var(--amber));
}
.td-header-grid {
  display:grid;
  grid-template-columns:1fr auto;
  gap:32px;
  align-items:start;
}
.td-eyebrow {
  font-family:var(--font-mono);
  font-size:.62rem;
  letter-spacing:.14em;
  text-transform:uppercase;
  color:var(--cyan);
  margin-bottom:10px;
  display:flex;
  align-items:center;
  gap:6px;
}
.td-eyebrow::before { content:'//'; opacity:.6 }
.td-h1 {
  font-family:var(--font-display);
  font-size:clamp(2.2rem,4.5vw,3.6rem);
  font-weight:800;
  letter-spacing:-.05em;
  color:var(--ink);
  line-height:1;
  margin-bottom:10px;
}
.td-tagline { font-size:1rem; color:var(--ink3); line-height:1.7; margin-bottom:20px }
.td-meta-row {
  display:flex;
  align-items:center;
  gap:14px;
  flex-wrap:wrap;
}
.td-stars { color:var(--amber); font-size:1rem; letter-spacing:-.04em }
.td-rating-txt {
  font-family:var(--font-mono);
  font-size:.78rem;
  color:var(--ink3);
}
.td-score-block { text-align:right; flex-shrink:0 }
.td-score-num {
  font-family:var(--font-display);
  font-size:3.8rem;
  font-weight:800;
  letter-spacing:-.06em;
  line-height:1;
}
.td-score-label {
  font-family:var(--font-mono);
  font-size:.64rem;
  letter-spacing:.08em;
  text-transform:uppercase;
  margin-top:3px;
}
.td-score-sub {
  font-family:var(--font-mono);
  font-size:.58rem;
  color:var(--ink4);
  letter-spacing:.08em;
  text-transform:uppercase;
  margin-top:2px;
}

/* Tool Detail Layout */
.td-layout {
  display:grid;
  grid-template-columns:1fr 280px;
  gap:20px;
  align-items:start;
}
.td-panel {
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--r3);
  padding:24px;
  margin-bottom:16px;
  box-shadow:var(--sh0);
}
.panel-label {
  font-family:var(--font-mono);
  font-size:.62rem;
  letter-spacing:.14em;
  text-transform:uppercase;
  color:var(--cyan);
  margin-bottom:16px;
  display:flex;
  align-items:center;
  gap:6px;
}
.panel-label::before { content:'//'; opacity:.5 }
.verdict-text { font-size:.96rem; line-height:1.85; color:var(--ink2) }
.pros-cons-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px }
.plist { list-style:none; display:flex; flex-direction:column; gap:9px }
.plist li {
  font-size:.87rem;
  line-height:1.6;
  color:var(--ink3);
  padding-left:20px;
  position:relative;
}
.plist.pros li::before {
  content:'✓';
  position:absolute; left:0;
  color:var(--green); font-weight:700;
}
.plist.cons li::before {
  content:'✗';
  position:absolute; left:0;
  color:var(--rose); font-weight:700;
}
.best-for-list { display:flex; flex-direction:column; gap:8px }
.best-for-item {
  display:flex;
  align-items:center;
  gap:9px;
  font-size:.88rem;
  color:var(--ink3);
}
.best-for-item::before {
  content:'→';
  color:var(--cyan);
  font-family:var(--font-mono);
  font-size:.7rem;
  flex-shrink:0;
}

/* Sidebar */
.td-sidebar {}
.price-box {
  background:var(--bg3);
  border:1px solid var(--bdr);
  border-radius:var(--r2);
  padding:20px;
  margin-bottom:14px;
}
.price-from {
  font-family:var(--font-mono);
  font-size:.6rem;
  color:var(--ink4);
  letter-spacing:.1em;
  text-transform:uppercase;
  margin-bottom:8px;
}
.price-value {
  font-family:var(--font-display);
  font-size:2rem;
  font-weight:800;
  color:var(--ink);
  letter-spacing:-.04em;
  line-height:1;
}
.price-period {
  font-family:var(--font-mono);
  font-size:.64rem;
  color:var(--ink4);
  letter-spacing:.06em;
  text-transform:uppercase;
  margin-top:5px;
}
.btn-td-cta {
  display:flex;
  align-items:center;
  justify-content:center;
  gap:10px;
  width:100%;
  background:var(--cyan);
  color:#060810;
  padding:16px 24px;
  border-radius:var(--r2);
  font-family:var(--font-mono);
  font-size:.8rem;
  font-weight:600;
  letter-spacing:.04em;
  text-transform:uppercase;
  border:none;
  transition:all .2s;
  box-shadow:var(--shc);
  margin-bottom:10px;
}
.btn-td-cta:hover {
  background:var(--cyan2);
  transform:translateY(-2px);
  box-shadow:0 10px 36px rgba(79,156,249,.4);
}
.btn-td-cta svg { width:13px; height:13px; stroke:currentColor; fill:none; stroke-width:2.5 }
.trust-items { display:flex; flex-direction:column; gap:8px; margin-top:14px }
.trust-item {
  display:flex;
  align-items:center;
  gap:8px;
  font-family:var(--font-mono);
  font-size:.64rem;
  color:var(--ink4);
}
.trust-item svg {
  width:13px; height:13px;
  stroke:var(--green); fill:none; stroke-width:2;
  flex-shrink:0;
}

/* ── Compare Detail ─────────────────────────────────────────────────────────── */
.comp-detail-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:24px }
.cd-card {
  background:var(--surf);
  border:1px solid var(--bdr2);
  border-radius:var(--r3);
  padding:26px;
  position:relative;
  overflow:hidden;
}
.cd-card.winner {
  border-color:var(--green-g);
  box-shadow:0 0 0 1px var(--green-g), var(--shg);
}
.cd-card.winner::before {
  content:'';
  position:absolute;
  top:0; left:0; right:0; height:2px;
  background:var(--green);
}
.cd-winner-tag {
  position:absolute;
  top:16px; right:16px;
  background:var(--green-d);
  border:1px solid var(--green-g);
  border-radius:var(--rpill);
  padding:3px 11px;
  font-family:var(--font-mono);
  font-size:.58rem;
  color:var(--green);
  letter-spacing:.08em;
  text-transform:uppercase;
}
.cd-name {
  font-family:var(--font-display);
  font-size:1.5rem;
  font-weight:800;
  color:var(--ink);
  letter-spacing:-.04em;
  margin-bottom:6px;
}
.cd-score {
  font-family:var(--font-display);
  font-size:2.6rem;
  font-weight:800;
  letter-spacing:-.06em;
  line-height:1;
  margin-bottom:8px;
}
.cd-tagline { font-size:.88rem; color:var(--ink3); line-height:1.65; margin-bottom:16px }
.comp-table {
  width:100%;
  border-collapse:collapse;
  margin-bottom:16px;
}
.comp-table td {
  padding:10px 0;
  border-bottom:1px solid var(--div);
  font-size:.87rem;
  color:var(--ink3);
  vertical-align:middle;
}
.comp-table td:first-child {
  color:var(--ink4);
  font-family:var(--font-mono);
  font-size:.68rem;
  letter-spacing:.04em;
  text-transform:uppercase;
  width:40%;
}
.comp-table tr:last-child td { border-bottom:none }
.tick { color:var(--green) }
.cross { color:var(--rose) }
.cd-verdict { font-size:.9rem; color:var(--ink3); line-height:1.72 }
.winner-block {
  background:var(--green-d);
  border:1px solid var(--green-g);
  border-radius:var(--r3);
  padding:20px 24px;
  margin-bottom:24px;
}
.winner-label {
  font-family:var(--font-mono);
  font-size:.64rem;
  color:var(--green);
  letter-spacing:.12em;
  text-transform:uppercase;
  margin-bottom:10px;
}
.winner-text { font-size:.92rem; color:var(--ink2); line-height:1.75 }

/* ── Prose / Blog ───────────────────────────────────────────────────────────── */
.prose {
  font-size:.97rem;
  line-height:1.9;
  color:var(--ink3);
}
.prose h2 {
  font-family:var(--font-display);
  font-size:1.75rem;
  font-weight:700;
  color:var(--ink);
  margin:56px 0 16px;
  letter-spacing:-.04em;
  padding-bottom:14px;
  border-bottom:1px solid var(--div);
  line-height:1.15;
}
.prose h3 {
  font-family:var(--font-display);
  font-size:1.25rem;
  font-weight:700;
  color:var(--ink);
  margin:36px 0 12px;
  letter-spacing:-.03em;
}
.prose p { margin-bottom:20px }
.prose a { color:var(--cyan); border-bottom:1px solid var(--cyan-g); transition:border-color .15s }
.prose a:hover { border-color:var(--cyan) }
.prose strong { color:var(--ink2); font-weight:600 }
.prose ul, .prose ol { margin:0 0 24px; padding:0; list-style:none }
.prose li { padding-left:22px; position:relative; margin-bottom:10px; line-height:1.75 }
.prose ul li::before {
  content:'▸';
  position:absolute; left:0; top:5px;
  font-size:.65rem; color:var(--cyan);
}
.prose ol { counter-reset:ol }
.prose ol li { counter-increment:ol }
.prose ol li::before {
  content:counter(ol, decimal-leading-zero);
  position:absolute; left:0; top:4px;
  font-family:var(--font-mono);
  font-size:.62rem;
  color:var(--cyan);
}
.prose blockquote {
  border-left:3px solid var(--cyan);
  padding:16px 24px;
  margin:28px 0;
  background:var(--cyan-d);
  border-radius:0 var(--r2) var(--r2) 0;
  font-style:italic;
  color:var(--ink2);
}

/* ── Legal Pages ────────────────────────────────────────────────────────────── */
.legal-wrap {
  max-width:740px;
  margin:56px auto 96px;
  padding:0 40px;
  position:relative;
  z-index:1;
}
.legal-wrap h1 {
  font-family:var(--font-display);
  font-size:2.4rem;
  font-weight:800;
  letter-spacing:-.05em;
  color:var(--ink);
  margin-bottom:28px;
}
.legal-wrap h2 {
  font-family:var(--font-display);
  font-size:1.5rem;
  font-weight:700;
  color:var(--ink);
  margin:40px 0 12px;
  letter-spacing:-.04em;
}
.legal-wrap p { font-size:.93rem; line-height:1.82; color:var(--ink3); margin-bottom:14px }
.legal-note {
  background:var(--surf);
  border:1px solid var(--bdr);
  border-radius:var(--r3);
  padding:22px 26px;
  margin-bottom:28px;
}

/* ── Pagination ─────────────────────────────────────────────────────────────── */
.pager {
  display:flex;
  justify-content:center;
  align-items:center;
  gap:10px;
  padding:56px 0;
}
.pager a {
  background:var(--surf);
  border:1px solid var(--bdr);
  color:var(--ink3);
  padding:10px 22px;
  border-radius:var(--rpill);
  font-family:var(--font-mono);
  font-size:.72rem;
  transition:all .18s;
  letter-spacing:.04em;
  text-transform:uppercase;
}
.pager a:hover {
  background:var(--cyan);
  color:#060810;
  border-color:var(--cyan);
  box-shadow:var(--shc);
  transform:translateY(-1px);
}

/* ── Search Overlay ─────────────────────────────────────────────────────────── */
#sov {
  display:none;
  position:fixed;
  inset:0;
  background:rgba(6,8,16,.92);
  backdrop-filter:blur(20px);
  z-index:500;
  padding:72px 20px;
  overflow-y:auto;
}
#sov.open { display:block; animation:fadeIn .18s ease }
@keyframes fadeIn { from{opacity:0}to{opacity:1} }
.sov-panel {
  max-width:960px;
  margin:0 auto;
  background:var(--surf);
  border:1px solid var(--bdr2);
  border-radius:var(--r4);
  padding:28px;
  box-shadow:var(--sh3);
  animation:panelIn .22s var(--ease);
}
@keyframes panelIn {
  from { opacity:0; transform:translateY(14px) scale(.99) }
  to   { opacity:1; transform:none }
}
.sov-hdr {
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom:6px;
}
.sov-title {
  font-family:var(--font-display);
  font-size:1.3rem;
  font-weight:700;
  color:var(--ink);
  letter-spacing:-.04em;
}
.sov-close {
  width:34px; height:34px;
  border-radius:var(--r2);
  border:1px solid var(--bdr);
  background:var(--surf2);
  display:flex; align-items:center; justify-content:center;
  font-size:1rem; color:var(--ink3);
  transition:all .18s;
}
.sov-close:hover { background:var(--rose-d); color:var(--rose) }
.sov-count {
  font-family:var(--font-mono);
  font-size:.68rem;
  color:var(--ink4);
  margin-bottom:20px;
  letter-spacing:.04em;
}
.sov-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(240px,1fr)); gap:12px }
.sov-empty {
  text-align:center;
  padding:52px;
  font-family:var(--font-mono);
  font-size:.74rem;
  color:var(--ink4);
  letter-spacing:.06em;
}

/* ── Cookie Bar ─────────────────────────────────────────────────────────────── */
#ckbar {
  display:none;
  position:fixed;
  bottom:20px;
  left:50%;
  transform:translateX(-50%);
  background:var(--surf2);
  border:1px solid var(--bdr2);
  border-radius:var(--r3);
  padding:16px 22px;
  box-shadow:var(--sh3);
  z-index:1000;
  max-width:560px;
  width:calc(100% - 32px);
  align-items:center;
  gap:16px;
  flex-wrap:wrap;
}
#ckbar.show { display:flex; animation:ckpop .28s var(--ease) }
@keyframes ckpop {
  from { opacity:0; transform:translateX(-50%) translateY(16px) }
  to   { opacity:1; transform:translateX(-50%) translateY(0) }
}
.ck-text {
  flex:1;
  min-width:180px;
  font-family:var(--font-mono);
  font-size:.68rem;
  color:var(--ink4);
  line-height:1.6;
}
.ck-text a { color:var(--cyan) }
.ck-btns { display:flex; gap:7px; flex-shrink:0 }
.ck-accept {
  background:var(--cyan);
  color:#060810;
  border:none;
  border-radius:var(--r1);
  padding:9px 18px;
  font-family:var(--font-mono);
  font-size:.72rem;
  font-weight:600;
  letter-spacing:.04em;
  transition:background .18s;
}
.ck-accept:hover { background:var(--cyan2) }
.ck-decline {
  background:transparent;
  color:var(--ink4);
  border:1px solid var(--bdr);
  border-radius:var(--r1);
  padding:9px 14px;
  font-family:var(--font-mono);
  font-size:.68rem;
  transition:all .18s;
}
.ck-decline:hover { border-color:var(--bdr2); color:var(--ink) }

/* ── Footer ─────────────────────────────────────────────────────────────────── */
.footer {
  background:var(--surf);
  border-top:1px solid var(--bdr);
  position:relative;
  z-index:1;
  margin-top:100px;
}
.footer::before {
  content:'';
  position:absolute;
  top:-1px; left:0; right:0; height:1px;
  background:linear-gradient(90deg, transparent, var(--cyan), var(--violet), var(--amber), transparent);
  opacity:.35;
}
.footer-in {
  max-width:1440px;
  margin:0 auto;
  padding:56px 40px 40px;
}
.footer-top {
  display:grid;
  grid-template-columns:2fr 1fr 1fr 1fr;
  gap:48px;
  margin-bottom:40px;
}
.f-brand {}
.f-logo {
  font-family:var(--font-display);
  font-size:1.05rem;
  font-weight:700;
  letter-spacing:-.03em;
  color:var(--ink);
  display:flex;
  align-items:center;
  gap:8px;
  margin-bottom:13px;
}
.f-logo-icon {
  width:26px; height:26px;
  background:var(--cyan);
  border-radius:7px;
  display:flex; align-items:center; justify-content:center;
  font-size:.65rem; color:#060810;
  font-weight:800; letter-spacing:-.04em;
  flex-shrink:0;
}
.f-desc {
  font-size:.86rem;
  line-height:1.78;
  color:var(--ink4);
  max-width:280px;
}
.f-affil {
  margin-top:18px;
  font-family:var(--font-mono);
  font-size:.6rem;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:var(--amber);
  display:flex;
  align-items:center;
  gap:7px;
}
.f-affil::before { content:''; width:14px; height:1px; background:var(--amber) }
.f-col-title {
  font-family:var(--font-mono);
  font-size:.6rem;
  letter-spacing:.18em;
  text-transform:uppercase;
  color:var(--ink4);
  margin-bottom:14px;
}
.f-col a {
  display:block;
  font-size:.86rem;
  color:var(--ink4);
  margin-bottom:9px;
  transition:color .15s, padding-left .2s var(--ease);
}
.f-col a:hover { color:var(--cyan); padding-left:4px }
.footer-divider { height:1px; background:var(--div); margin-bottom:22px }
.footer-bottom {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
  flex-wrap:wrap;
}
.f-copy {
  font-family:var(--font-mono);
  font-size:.64rem;
  color:var(--ink4);
  line-height:1.65;
}
.f-disclaimer {
  font-family:var(--font-mono);
  font-size:.6rem;
  color:var(--ink5);
  font-style:italic;
}

/* ── Reveal Animations ──────────────────────────────────────────────────────── */
/* Default: ALWAYS visible. JS adds .rv-ready to <body> before animating */
.rv {
  opacity:1;
  transform:none;
  transition:opacity .55s var(--ease), transform .55s var(--ease);
}
/* Only hide/animate when JS has confirmed IntersectionObserver support */
body.rv-ready .rv {
  opacity:0;
  transform:translateY(20px);
}
body.rv-ready .rv.visible {
  opacity:1;
  transform:translateY(0);
}
@media (prefers-reduced-motion: reduce) {
  body.rv-ready .rv,
  body.rv-ready .rv.visible { opacity:1; transform:none; transition:none }
}

/* ── Responsive ─────────────────────────────────────────────────────────────── */
@media (max-width:1200px) {
  .hero { grid-template-columns:1fr }
  .hero-panel { display:none }
  .td-layout { grid-template-columns:1fr }
  .footer-top { grid-template-columns:1fr 1fr; gap:32px }
  .comp-detail-grid { grid-template-columns:1fr }
  .email-inner { grid-template-columns:1fr }
  .email-visual { display:none }
  .pros-cons-grid { grid-template-columns:1fr }
}
@media (max-width:768px) {
  .nav-in { padding:0 20px; height:56px }
  .nav-links, .nav-search { display:none }
  #hbg { display:flex }
  .page, .page-narrow { padding:0 20px }
  .affil-in { padding:10px 20px }
  .email-inner { padding:0 20px }
  .footer-in { padding:40px 20px 32px }
  .footer-top { grid-template-columns:1fr; gap:24px }
  .footer-bottom { flex-direction:column; align-items:flex-start }
  .legal-wrap { padding:0 20px }
  .hero { grid-template-columns:1fr; padding:48px 0 28px }
  .stats-row { gap:24px }
  .td-header-grid { grid-template-columns:1fr }
  .td-score-block { display:none }
  .td-header { padding:24px }
}
@media (max-width:520px) {
  .hero-h1 { font-size:2.6rem }
  .roles-grid { grid-template-columns:1fr }
  .comp-grid { grid-template-columns:1fr }
  .tools-grid { grid-template-columns:1fr }
  .blog-grid { grid-template-columns:1fr }
}

/* ── Scrollbar ──────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width:4px }
::-webkit-scrollbar-track { background:transparent }
::-webkit-scrollbar-thumb { background:var(--bdr3); border-radius:2px }
::-webkit-scrollbar-thumb:hover { background:var(--cyan) }
::selection { background:var(--cyan-d); color:var(--cyan2) }

/* ── Focus Styles (Accessibility) ──────────────────────────────────────────── */
:focus-visible {
  outline:2px solid var(--cyan);
  outline-offset:2px;
  border-radius:var(--r1);
}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# BASE HTML TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════
BASE = """<!DOCTYPE html>
<html lang="en-GB" class="">
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
<meta name="theme-color" content="#060810">
{% if schema %}<script type="application/ld+json">{{ schema|safe }}</script>{% endif %}
{% if bcs %}<script type="application/ld+json">{{ bcs|safe }}</script>{% endif %}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- Theme: applied before paint to prevent flash -->
<script>
(function(){
  var saved=localStorage.getItem('mfwai-theme');
  var preferLight=window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches;
  var isLight=saved==='light'||(saved===null&&preferLight);
  if(isLight){
    document.documentElement.classList.add('light');
    document.body&&document.body.classList.add('light');
  }
})();
</script>

<style>{{ css|safe }}</style>
</head>
<body>

<!-- Ticker -->
<div class="ticker" aria-hidden="true" role="presentation">
  <div class="ticker-track">
    {% for _ in range(2) %}
    <span class="ticker-item">Independent AI Reviews</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item accent">UK-Focused · Updated Weekly</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item">No Paid Placements</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item">Honest Verdicts</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item accent">Moving Forward With AI</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item">Affiliate Commissions Fund This Site</span>
    <span class="ticker-sep">◆</span>
    {% endfor %}
  </div>
</div>

<!-- Navigation -->
<header class="nav" id="sitenav" role="banner">
  <div class="nav-in">
    <a href="/" class="nav-logo" aria-label="Moving Forward With AI — Home">
      <div class="logo-icon" aria-hidden="true">AI</div>
      <div class="logo-wordmark">Moving Forward <em>With AI</em></div>
    </a>

    <nav class="nav-links" aria-label="Primary navigation">
      <a href="/">Home</a>
      <a href="/tools">All Tools</a>
      <a href="/compare">Compare</a>
      <a href="/blog">Guides</a>
      <div class="nav-drop" role="navigation" aria-label="Role navigation">
        <button class="nav-drop-btn" type="button" aria-expanded="false" aria-haspopup="true">
          Who it's for
          <svg class="drop-chevron" viewBox="0 0 12 12" aria-hidden="true"><path d="M2 4l4 4 4-4"/></svg>
        </button>
        <div class="drop-menu" role="menu">
          {% for role in roles %}
          <a href="/for/{{ role.slug }}" role="menuitem">
            <span class="dm-icon" aria-hidden="true">{{ role.icon }}</span>{{ role.name }}
          </a>
          {% endfor %}
        </div>
      </div>
    </nav>

    <div class="nav-right">
      <div class="nav-search" role="search">
        <svg class="search-ico" viewBox="0 0 16 16" aria-hidden="true">
          <circle cx="6.5" cy="6.5" r="4.5"/>
          <path d="M10 10l3.5 3.5"/>
        </svg>
        <input type="search" id="search-input" placeholder="Search tools…" autocomplete="off"
          aria-label="Search AI tools" aria-controls="sov" aria-expanded="false">
      </div>

      <button class="nav-icon-btn" id="theme-btn" aria-label="Toggle light/dark theme" type="button">
        <svg id="ico-sun" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="4"/>
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
        </svg>
        <svg id="ico-moon" viewBox="0 0 24 24" style="display:none" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>

      <button id="hbg" aria-label="Open navigation menu" aria-expanded="false" type="button">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>

<!-- Mobile Menu -->
<div id="mob" role="dialog" aria-modal="true" aria-label="Navigation menu">
  <div class="mob-section">
    <nav class="mob-primary-links" aria-label="Mobile primary navigation">
      <a href="/" class="mob-link">Home</a>
      <a href="/tools" class="mob-link">All Tools</a>
      <a href="/compare" class="mob-link">Compare</a>
      <a href="/blog" class="mob-link">Guides</a>
    </nav>
  </div>
  <div class="mob-section">
    <div class="mob-sublabel">Who it's for</div>
    <div class="mob-pills">
      {% for role in roles %}
      <a href="/for/{{ role.slug }}" class="mob-pill">
        <span aria-hidden="true">{{ role.icon }}</span>{{ role.name }}
      </a>
      {% endfor %}
    </div>
  </div>
</div>

<!-- Page Content -->
<main id="main-content" tabindex="-1">
{{ content|safe }}
</main>

<!-- Footer -->
<footer class="footer" role="contentinfo">
  <div class="footer-in">
    <div class="footer-top">
      <div class="f-brand">
        <div class="f-logo">
          <div class="f-logo-icon" aria-hidden="true">AI</div>
          Moving Forward With AI
        </div>
        <p class="f-desc">Independent, honest reviews of AI tools for UK freelancers, marketers and builders. No paid placements. Ever.</p>
        <div class="f-affil">Affiliate commissions fund this site</div>
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
    <div class="footer-divider"></div>
    <div class="footer-bottom">
      <p class="f-copy">© 2026 Moving Forward With AI. All rights reserved. Prices verified at time of writing — always confirm on the tool's website.</p>
      <p class="f-disclaimer">// This site earns affiliate commissions. <a href="/affiliate-disclosure" style="color:var(--cyan)">Full disclosure →</a></p>
    </div>
  </div>
</footer>

<!-- Search Overlay -->
<div id="sov" role="dialog" aria-modal="true" aria-label="Search results">
  <div class="sov-panel">
    <div class="sov-hdr">
      <h2 class="sov-title">Search Tools</h2>
      <button class="sov-close" id="sov-close" aria-label="Close search">×</button>
    </div>
    <p class="sov-count" id="sov-count" aria-live="polite"></p>
    <div class="sov-grid" id="sov-results"></div>
  </div>
</div>

<!-- Cookie Consent -->
<div id="ckbar" role="dialog" aria-label="Cookie consent">
  <div class="ck-text">
    // We use essential cookies &amp; affiliate tracking.
    <a href="/privacy">Privacy policy →</a>
  </div>
  <div class="ck-btns">
    <button class="ck-accept" id="ck-ok" type="button">Accept all</button>
    <button class="ck-decline" id="ck-ess" type="button">Essential only</button>
  </div>
</div>

<script>
/* ─ Theme Toggle ─ */
(function(){
  var btn=document.getElementById('theme-btn');
  var sun=document.getElementById('ico-sun');
  var moon=document.getElementById('ico-moon');

  function applyTheme(isLight){
    /* Apply to both html and body so CSS vars cascade correctly */
    document.documentElement.classList.toggle('light',isLight);
    document.body.classList.toggle('light',isLight);
    if(sun)  sun.style.display =isLight?'none':'block';
    if(moon) moon.style.display=isLight?'block':'none';
  }

  /* Read current state from html element (set by inline script in <head>) */
  var current=document.documentElement.classList.contains('light');
  applyTheme(current);

  if(btn){
    btn.addEventListener('click',function(){
      current=!current;
      localStorage.setItem('mfwai-theme',current?'light':'dark');
      applyTheme(current);
    });
  }
})();

/* ─ Sticky nav shadow ─ */
window.addEventListener('scroll',function(){
  var nav=document.getElementById('sitenav');
  if(nav) nav.classList.toggle('scrolled',window.scrollY>24);
},{passive:true});

/* ─ Mobile hamburger menu ─ */
(function(){
  var btn=document.getElementById('hbg');
  var menu=document.getElementById('mob');
  if(!btn||!menu) return;

  function openMenu(){
    menu.classList.add('open');
    btn.classList.add('open');
    btn.setAttribute('aria-expanded','true');
    document.body.style.overflow='hidden';
  }
  function closeMenu(){
    menu.classList.remove('open');
    btn.classList.remove('open');
    btn.setAttribute('aria-expanded','false');
    document.body.style.overflow='';
  }

  btn.addEventListener('click',function(e){
    e.stopPropagation();
    if(menu.classList.contains('open')){closeMenu();}else{openMenu();}
  });

  /* Close when a nav link is tapped */
  menu.querySelectorAll('a').forEach(function(a){
    a.addEventListener('click',function(){closeMenu();});
  });

  /* Close on Escape */
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape') closeMenu();
  });
})();

/* ─ Desktop dropdown menus ─ */
(function(){
  var drops=document.querySelectorAll('.nav-drop');
  drops.forEach(function(d){
    var btn=d.querySelector('.nav-drop-btn');
    if(!btn) return;
    btn.addEventListener('click',function(e){
      e.stopPropagation();
      var isOpen=d.classList.contains('open');
      /* Close all */
      drops.forEach(function(x){
        x.classList.remove('open');
        var xb=x.querySelector('.nav-drop-btn');
        if(xb) xb.setAttribute('aria-expanded','false');
      });
      /* Open this one if it wasn't open */
      if(!isOpen){
        d.classList.add('open');
        btn.setAttribute('aria-expanded','true');
      }
    });
  });
  document.addEventListener('click',function(){
    drops.forEach(function(d){
      d.classList.remove('open');
      var b=d.querySelector('.nav-drop-btn');
      if(b) b.setAttribute('aria-expanded','false');
    });
  });
})();

/* ─ Scroll reveal ─ */
(function(){
  /* Only animate if IntersectionObserver is available */
  if(!('IntersectionObserver' in window)) return;

  /* Mark body so CSS can hide .rv elements */
  document.body.classList.add('rv-ready');

  var els=document.querySelectorAll('.rv');
  if(!els.length) return;

  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(entry.isIntersecting){
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  },{threshold:0.08, rootMargin:'0px 0px -30px 0px'});

  els.forEach(function(el,i){
    /* Stagger in groups of 4 */
    el.style.transitionDelay=(i%4*0.07)+'s';
    io.observe(el);
  });
})();

/* ─ Search overlay ─ */
var allTools=[];
(async function(){
  try{
    var r=await fetch('/api/tools');
    var d=await r.json();
    allTools=d.tools||[];
  }catch(e){}
})();

var sov=document.getElementById('sov');
var sovCount=document.getElementById('sov-count');
var sovRes=document.getElementById('sov-results');
var searchInput=document.getElementById('search-input');
var searchTimer;

function closeSov(){
  sov.classList.remove('open');
  document.body.style.overflow='';
  searchInput.setAttribute('aria-expanded','false');
}

function miniCard(t){
  var sc=t.score;
  var isShi=sc>=88;
  var bg=isShi?'var(--green-d)':'var(--cyan-d)';
  var bdr=isShi?'var(--green-g)':'var(--cyan-g)';
  var col=isShi?'var(--green)':'var(--cyan)';
  return '<div class="tool-card" style="cursor:pointer" onclick="location.href=\'/tool/'+t.slug+'\'">'
    +'<div class="tc-accent-bar"></div>'
    +'<div class="tc-body">'
    +'<div class="tc-meta">'
    +'<div class="tc-cat">'+t.category+'</div>'
    +'<div class="tc-score" style="background:'+bg+';border:1px solid '+bdr+';color:'+col+'">'+sc+'</div>'
    +'</div>'
    +'<a href="/tool/'+t.slug+'" class="tc-name">'+t.name+'</a>'
    +'<p class="tc-tagline">'+t.tagline+'</p>'
    +'</div>'
    +'<div class="tc-footer">'
    +'<div class="tc-pricing"><span class="tc-price">'+t.starting_price+'</span></div>'
    +'</div>'
    +'</div>';
}

searchInput.addEventListener('input',function(e){
  clearTimeout(searchTimer);
  var q=e.target.value.trim();
  if(q.length<2){
    if(sov.classList.contains('open'))closeSov();
    return;
  }
  searchTimer=setTimeout(function(){
    var ql=q.toLowerCase();
    var hits=allTools.filter(function(t){
      return (t.name||'').toLowerCase().includes(ql)
          ||(t.category||'').toLowerCase().includes(ql)
          ||(t.tagline||'').toLowerCase().includes(ql)
          ||(t.tags||[]).join(' ').toLowerCase().includes(ql);
    });
    sovCount.textContent='// '+hits.length+' result'+(hits.length!==1?'s':'')+' for "'+q+'"';
    sovRes.innerHTML=hits.length
      ?hits.map(miniCard).join('')
      :'<div class="sov-empty">// No tools found for "'+q+'"</div>';
    sov.classList.add('open');
    document.body.style.overflow='hidden';
    searchInput.setAttribute('aria-expanded','true');
  },160);
});

searchInput.addEventListener('keydown',function(e){
  if(e.key==='Escape'){closeSov();searchInput.value=''}
});
document.getElementById('sov-close').addEventListener('click',closeSov);
sov.addEventListener('click',function(e){if(e.target===sov)closeSov()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeSov()});

/* ─ Cookie banner ─ */
(function(){
  var KEY='mfwai_consent_v2';
  var bar=document.getElementById('ckbar');
  try{
    if(!localStorage.getItem(KEY)){
      setTimeout(function(){bar.classList.add('show')},1800);
    }
  }catch(e){bar.classList.add('show')}
  function dismiss(v){
    try{localStorage.setItem(KEY,v)}catch(e){}
    bar.classList.remove('show');
  }
  document.getElementById('ck-ok').addEventListener('click',function(){dismiss('all')});
  document.getElementById('ck-ess').addEventListener('click',function(){dismiss('ess')});
})();

/* ─ Email form ─ */
var ef=document.getElementById('email-form');
if(ef){
  ef.addEventListener('submit',function(e){
    e.preventDefault();
    var btn=ef.querySelector('button[type="submit"]');
    var em=ef.querySelector('input[type="email"]');
    if(!em||!em.value)return;
    btn.textContent='Sent ✓';
    btn.style.background='var(--green)';
    btn.disabled=true;
    em.disabled=true;
  });
}

/* ─ Skip to content ─ */
document.addEventListener('keydown',function(e){
  if(e.key==='Tab'&&!e.shiftKey){
    var skip=document.querySelector('.skip-link');
    if(skip)skip.focus();
  }
});
</script>

</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def render(title, desc, content, schema='', bcs=''):
    canon = SITE_URL + (request.path.rstrip('/') or '/')
    return render_template_string(BASE,
        title=title, desc=desc, content=content,
        css=CSS, roles=ROLES, slugify=slugify,
        canon=canon, schema=schema, bcs=bcs)


def breadcrumb_html(crumbs):
    """Crumbs: list of (label, url) pairs, last item has no link"""
    parts = []
    sep = '<svg class="sep" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    for i, (label, url) in enumerate(crumbs):
        if i < len(crumbs) - 1:
            parts.append(f'<a href="{url}">{label}</a>')
        else:
            parts.append(f'<span class="current" aria-current="page">{label}</span>')
    return f'<nav class="breadcrumb page" aria-label="Breadcrumb">{"".join(f"{p}{sep}" if i < len(crumbs)-1 else p for i,p in enumerate(parts))}</nav>'


def score_badge(score, size='normal'):
    bg = 'var(--green-d)' if score>=88 else 'var(--cyan-d)' if score>=78 else 'var(--amber-d)'
    bdr = 'var(--green-g)' if score>=88 else 'var(--cyan-g)' if score>=78 else 'var(--amber-g)'
    col = 'var(--green)' if score>=88 else 'var(--cyan)' if score>=78 else 'var(--amber)'
    font = '.72rem' if size == 'large' else '.67rem'
    pad = '4px 12px' if size == 'large' else '3px 10px'
    return f'<div class="tc-score" style="background:{bg};border:1px solid {bdr};color:{col};font-size:{font};padding:{pad}">{score}</div>'


def tool_card(t, delay=0):
    sc = t['score']
    sbg  = 'var(--green-d)' if sc>=88 else 'var(--cyan-d)'
    sbdr = 'var(--green-g)' if sc>=88 else 'var(--cyan-g)'
    scol = 'var(--green)' if sc>=88 else 'var(--cyan)'
    badges = []
    if t.get('free_tier'):  badges.append('<span class="badge b-free">Free tier</span>')
    if t.get('free_trial'): badges.append(f'<span class="badge b-trial">{t["trial_days"]}-day trial</span>')
    if not t.get('free_tier') and not t.get('free_trial'):
        badges.append('<span class="badge b-paid">Paid only</span>')
    if t.get('featured'): badges.append('<span class="badge b-top">Featured</span>')
    st = stars(t['rating'])
    return f"""<article class="tool-card rv" aria-label="{t['name']} — {t['category']} tool">
  <div class="tc-accent-bar" aria-hidden="true"></div>
  <div class="tc-body">
    <div class="tc-meta">
      <div class="tc-cat" aria-label="Category: {t['category']}">{t['category']}</div>
      <div class="tc-score" style="background:{sbg};border:1px solid {sbdr};color:{scol}"
           aria-label="MFWAI score: {sc} out of 100">{sc}</div>
    </div>
    <a href="/tool/{t['slug']}" class="tc-name">{t['name']}</a>
    <p class="tc-tagline">{t['tagline']}</p>
    <div class="tc-badges" aria-label="Pricing badges">{''.join(badges)}</div>
  </div>
  <div class="tc-divider" aria-hidden="true"></div>
  <div class="tc-footer">
    <div class="tc-pricing">
      <span class="tc-price">{t['starting_price']}</span>
      <span class="tc-model">{t['pricing_model']}</span>
    </div>
    <div class="tc-rating" aria-label="Rating: {t['rating']} out of 5 from {t['review_count']} reviews">
      <span class="tc-stars" aria-hidden="true">{st}</span>
      <span>{t['rating']}/5 · {t['review_count']} reviews</span>
    </div>
    <div class="tc-btn-group">
      <a href="{t['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener noreferrer"
         class="btn-try" aria-label="Try {t['name']} — affiliate link, opens in new tab">
        Try {t['name']}
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
      </a>
      <a href="/tool/{t['slug']}" class="btn-outline">Full review →</a>
    </div>
  </div>
</article>"""


def email_capture():
    lm = LEAD_MAGNET
    benefits = '\n'.join(
        f'<div class="email-benefit"><div class="benefit-tick" aria-hidden="true">✓</div>{item}</div>'
        for item in lm.get('items', []))
    ev_items = '\n'.join(
        f'<div class="ev-item"><span class="ev-num" aria-hidden="true">{str(i+1).zfill(2)}</span>{item}</div>'
        for i, item in enumerate(lm['items']))
    return f"""<section class="email-sec" aria-labelledby="email-heading">
  <div class="email-inner">
    <div>
      <div class="email-eyebrow">Free guide — no spam</div>
      <h2 class="email-h2" id="email-heading">{lm['title']}<br><em>{lm['subtitle']}</em></h2>
      <p class="email-sub">{lm['description']}</p>
      <form class="email-form" id="email-form" novalidate>
        <input class="email-input" type="email" placeholder="your@email.com"
          required aria-label="Your email address" autocomplete="email">
        <button type="submit" class="btn-email">{lm['cta']}</button>
      </form>
      <div class="email-benefits" aria-label="What you'll get">{benefits}</div>
      <p class="email-notice">// No spam. Unsubscribe any time. UK GDPR compliant.</p>
    </div>
    <div class="email-visual" aria-hidden="true">
      <div class="ev-title">{lm['title']}</div>
      <div class="ev-subtitle">{lm['subtitle']}</div>
      <div class="ev-items">{ev_items}</div>
    </div>
  </div>
</section>"""


def affil_strip():
    return """<div class="affil-strip" role="note" aria-label="Affiliate disclosure">
  <div class="affil-in">
    <svg class="affil-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 16v-4M12 8h.01"/>
    </svg>
    <strong>Affiliate disclosure:</strong> Moving Forward With AI earns a commission when you sign up through links — at no extra cost to you.
    <a href="/affiliate-disclosure">Learn more →</a>
  </div>
</div>"""


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def home():
    # Hero panel — top 4 tools
    panel_tools = sorted(TOOLS, key=lambda t: -t['score'])[:4]
    panel_items = ''
    for i, t in enumerate(panel_tools):
        sc = t['score']
        sc_cls = 'ps-hi' if sc >= 88 else 'ps-md'
        panel_items += f"""<a href="/tool/{t['slug']}" class="ptool">
          <span class="ptool-rank">{str(i+1).zfill(2)}</span>
          <div class="ptool-info">
            <div class="ptool-name">{t['name']}</div>
            <div class="ptool-cat">{t['category']}</div>
          </div>
          <div class="ptool-score {sc_cls}">{sc}</div>
        </a>"""

    role_chips = '\n'.join(
        f'<a href="/for/{r["slug"]}" class="role-chip"><span class="chip-icon" aria-hidden="true">{r["icon"]}</span>{r["name"]}</a>'
        for r in ROLES)

    hero = f"""<div class="page">
  <section class="hero" aria-labelledby="hero-heading">
    <div>
      <div class="hero-eyebrow">
        <div class="hero-eyebrow-dot" aria-hidden="true"></div>
        UK AI Tool Reviews · Independent · 2026
      </div>
      <h1 class="hero-h1" id="hero-heading">
        Cutting through<br>the <em>AI noise</em>
        <span class="serif-accent">Honest reviews. Real results.</span>
      </h1>
      <p class="hero-sub">We test, score, and rank AI tools so UK freelancers, marketers and business owners find what actually works — and skip what doesn't.</p>
      <div class="role-selector" aria-label="Browse by role">
        <div class="role-label" id="role-label">// I am a</div>
        <div class="role-chips" role="list" aria-labelledby="role-label">{role_chips}</div>
      </div>
      <div class="hero-ctas">
        <a href="/tools" class="btn-primary">Browse all tools →</a>
        <a href="/compare" class="btn-ghost">Compare tools</a>
      </div>
      <div class="stats-row" aria-label="Site statistics">
        <div class="stat-item">
          <div class="stat-num">{len(TOOLS)}<em>+</em></div>
          <div class="stat-lbl">tools reviewed</div>
        </div>
        <div class="stat-item">
          <div class="stat-num">{len(ROLES)}<em>+</em></div>
          <div class="stat-lbl">role guides</div>
        </div>
        <div class="stat-item">
          <div class="stat-num"><em>£0</em></div>
          <div class="stat-lbl">paid placements</div>
        </div>
        <div class="stat-item">
          <div class="stat-num">{len(COMPARISONS)}<em>+</em></div>
          <div class="stat-lbl">comparisons</div>
        </div>
      </div>
    </div>

    <aside class="hero-panel" aria-label="Top rated tools leaderboard">
      <div class="panel-hdr">
        <div class="panel-title">Top-rated tools</div>
        <div class="panel-live" aria-label="Updated recently">updated</div>
      </div>
      <div class="panel-list" role="list">{panel_items}</div>
      <a href="/tools" class="panel-footer">View all {len(TOOLS)} reviewed tools →</a>
    </aside>
  </section>
</div>"""

    # Roles section
    role_cards = '\n'.join(f"""<a href="/for/{r['slug']}" class="role-card rv" aria-label="{r['name']} — {len(r['tool_slugs'])} recommended tools">
      <span class="rc-icon" aria-hidden="true">{r['icon']}</span>
      <div class="rc-name">{r['name']}</div>
      <div class="rc-desc">{r['description']}</div>
      <div class="rc-count">{len(r['tool_slugs'])} recommended tools</div>
      <div class="rc-arrow">See the stack →</div>
    </a>""" for r in ROLES)

    roles_sec = f"""<div class="page">
  <section class="sec" aria-labelledby="roles-heading">
    <div class="sec-top">
      <div>
        <div class="sec-eyebrow">Built for your role</div>
        <h2 class="sec-h2" id="roles-heading">Find your <em>perfect stack</em></h2>
      </div>
      <a href="/tools" class="sec-link">All tools →</a>
    </div>
    <div class="roles-grid">{role_cards}</div>
  </section>
</div>"""

    # Featured tools
    featured = [t for t in TOOLS if t.get('featured')]
    cards_html = '\n'.join(tool_card(t) for t in featured)
    tools_sec = f"""<div class="page">
  <section class="sec" aria-labelledby="featured-heading">
    <div class="sec-top">
      <div>
        <div class="sec-eyebrow">Highest rated · Featured picks</div>
        <h2 class="sec-h2" id="featured-heading">Top <em>AI tools</em> right now</h2>
      </div>
      <a href="/tools" class="sec-link">All tools →</a>
    </div>
    <div class="tools-grid">{cards_html}</div>
  </section>
</div>"""

    # Comparisons
    comp_cards = '\n'.join(f"""<a href="/compare/{c['slug']}" class="comp-card rv">
      <div class="comp-vs">
        <span class="comp-tool-name">{get_tool(c['tool_a'])['name']}</span>
        <span class="comp-vs-tag">VS</span>
        <span class="comp-tool-name">{get_tool(c['tool_b'])['name']}</span>
      </div>
      <div class="comp-desc">{c['description']}</div>
      <div class="comp-link">Read comparison →</div>
    </a>""" for c in COMPARISONS)

    comp_sec = f"""<div class="page">
  <section class="sec" aria-labelledby="compare-heading">
    <div class="sec-top">
      <div>
        <div class="sec-eyebrow">Head to head · High intent</div>
        <h2 class="sec-h2" id="compare-heading"><em>Compare</em> tools side by side</h2>
      </div>
      <a href="/compare" class="sec-link">All comparisons →</a>
    </div>
    <div class="comp-grid">{comp_cards}</div>
  </section>
</div>"""

    # Blog
    posts = sorted([{**v, 'slug': k} for k, v in BLOG_POSTS.items()], key=lambda x: x['date'], reverse=True)
    blog_cards = '\n'.join(f"""<a href="/blog/{p['slug']}" class="blog-card rv">
      <div class="blog-card-accent"></div>
      <div class="blog-card-body">
        <div class="blog-eyebrow">{datetime.datetime.strptime(p['date'],'%Y-%m-%d').strftime('%d %b %Y')} · {p.get('category','Guide')}</div>
        <div class="blog-title">{p['title']}</div>
        <div class="blog-desc">{p.get('description','')}</div>
        <div class="blog-link">Read guide →</div>
      </div>
    </a>""" for p in posts[:3])

    blog_sec = f"""<div class="page">
  <section class="sec" aria-labelledby="guides-heading">
    <div class="sec-top">
      <div>
        <div class="sec-eyebrow">Guides · Analysis · How-tos</div>
        <h2 class="sec-h2" id="guides-heading">Latest <em>guides</em></h2>
      </div>
      <a href="/blog" class="sec-link">All guides →</a>
    </div>
    <div class="blog-grid">{blog_cards}</div>
  </section>
</div>"""

    content = (hero + affil_strip() + roles_sec + tools_sec + comp_sec
               + email_capture() + blog_sec + '<div style="height:56px"></div>')

    return render(
        title='Moving Forward With AI — Honest AI Tool Reviews for UK Freelancers & Builders',
        desc='Independent, honest reviews of AI tools for UK freelancers, marketers and builders. Role-based recommendations, head-to-head comparisons, no paid placements.',
        content=content)


@app.route('/tools')
def tools_all():
    page = int(request.args.get('page', 1))
    PER = 12
    paged = TOOLS[(page-1)*PER: page*PER]
    total_pages = (len(TOOLS)+PER-1)//PER
    cards = '\n'.join(tool_card(t) for t in paged)
    prev = f'<a href="/tools?page={page-1}" rel="prev">← Previous</a>' if page > 1 else ''
    nxt  = f'<a href="/tools?page={page+1}" rel="next">Next →</a>' if page < total_pages else ''
    pager = f'<div class="page"><div class="pager">{prev}{nxt}</div></div>' if prev or nxt else ''

    content = f"""
    {breadcrumb_html([('Home','/'),('All Tools','/tools')])}
    <div class="page" style="padding-top:32px;padding-bottom:24px">
      <div class="sec-eyebrow">All tools · {len(TOOLS)} reviewed</div>
      <h1 style="font-family:var(--font-display);font-size:clamp(2rem,4vw,3.2rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1;margin-top:8px">
        Every AI tool, <em style="color:var(--cyan);font-style:normal">honestly reviewed</em>
      </h1>
      <p style="font-size:.96rem;color:var(--ink3);margin-top:12px;max-width:500px;line-height:1.75">
        No sponsored rankings. No paid placements. Just thorough, independent reviews scored on merit.
      </p>
    </div>
    {affil_strip()}
    <div class="page" style="padding-top:40px"><div class="tools-grid">{cards}</div></div>
    {pager}"""
    return render(
        title='All AI Tools Reviewed — Moving Forward With AI',
        desc=f'Browse all {len(TOOLS)} AI tools reviewed on Moving Forward With AI. Honest scores, pricing, pros and cons for UK users.',
        content=content,
        bcs=bc_schema([('Home', '/'), ('All Tools', '/tools')]))


@app.route('/for/<slug>')
def role_page(slug):
    role = get_role(slug)
    if not role: abort(404)
    role_tools = [get_tool(s) for s in role['tool_slugs'] if get_tool(s)]
    top = get_tool(role['top_pick']) if role.get('top_pick') else None

    pain_items = '\n'.join(
        f'<div class="pain-item"><span class="pain-x" aria-hidden="true">✗</span>{p}</div>'
        for p in role.get('pain_points', []))

    top_pick_html = ''
    if top:
        sc = top['score']
        sc_col = score_color(sc)
        top_pick_html = f"""<div class="top-pick-bar rv">
          <div class="top-pick-badge">★ Top pick</div>
          <div class="top-pick-info">
            <div class="top-pick-name">{top['name']}</div>
            <div class="top-pick-tagline">{top['tagline']}</div>
          </div>
          <div class="top-pick-score" style="color:{sc_col}">{sc}</div>
          <a href="{top['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener noreferrer"
             class="btn-primary">Try it →</a>
        </div>"""

    cards = '\n'.join(tool_card(t) for t in role_tools)

    content = f"""
    {breadcrumb_html([('Home','/'),('Tools','/tools'),(role['name'],f'/for/{slug}')])}
    <div class="page">
      <section class="rd-intro" aria-labelledby="role-heading">
        <span class="rd-icon" aria-hidden="true">{role['icon']}</span>
        <h1 class="rd-h1" id="role-heading">
          {role['headline'].split(' for ')[0]} for<br><em>{role['name']}</em>
        </h1>
        <p class="rd-sub">{role['description']}</p>

        <div class="insight-box pain rv" role="note">
          <div class="insight-label">// Sound familiar?</div>
          <div class="pain-list">{pain_items}</div>
        </div>

        <div class="insight-box solution rv" role="note">
          <div class="insight-label">// How AI changes the game</div>
          <p class="solution-text">{role.get('how_ai_helps', '')}</p>
        </div>

        {top_pick_html}

        <div class="sec-eyebrow" style="margin:36px 0 20px">
          Recommended stack · {len(role_tools)} tools
        </div>
      </section>
      <div class="tools-grid">{cards}</div>
    </div>
    {email_capture()}"""

    return render(
        title=f'Best AI Tools for {role["name"]} 2026 — Moving Forward With AI',
        desc=f'{role["description"]} Honest reviews of the best AI tools for {role["name"].lower()} in 2026.',
        content=content,
        bcs=bc_schema([('Home','/'), ('Tools','/tools'), (role['name'], f'/for/{slug}')]))


@app.route('/tool/<slug>')
def tool_detail(slug):
    t = get_tool(slug)
    if not t: abort(404)
    sc = t['score']
    sc_col = score_color(sc)
    sc_lbl = score_label(sc)
    st = stars(t['rating'])
    badges = []
    if t.get('free_tier'):  badges.append('<span class="badge b-free">Free tier</span>')
    if t.get('free_trial'): badges.append(f'<span class="badge b-trial">{t["trial_days"]}-day trial</span>')

    pros_html = '\n'.join(f'<li>{p}</li>' for p in t['pros'])
    cons_html = '\n'.join(f'<li>{c}</li>' for c in t['cons'])
    best_html = '\n'.join(
        f'<div class="best-for-item">{b}</div>'
        for b in t['best_for'])

    related = [x for x in TOOLS if x['slug']!=slug and any(r in x.get('roles',[]) for r in t.get('roles',[]))][:3]
    if len(related) < 3:
        extra = [x for x in TOOLS if x['slug']!=slug and x not in related]
        related += extra[:3-len(related)]
    rel_cards = '\n'.join(tool_card(r) for r in related[:3])

    content = f"""
    {breadcrumb_html([('Home','/'),('Tools','/tools'),(t['category'],f'/category/{slugify(t["category"])}'),
                      (t['name'],f'/tool/{slug}')])}
    <div class="page">
      <div class="td-wrapper">
        <header class="td-header">
          <div class="td-header-grid">
            <div>
              <div class="td-eyebrow">{t['category'].upper()}</div>
              <h1 class="td-h1">{t['name']}</h1>
              <p class="td-tagline">{t['tagline']}</p>
              <div class="td-meta-row">
                <span class="td-stars" aria-label="Rating: {t['rating']} out of 5">{st}</span>
                <span class="td-rating-txt">{t['rating']}/5 · {t['review_count']} reviews</span>
                {''.join(badges)}
              </div>
            </div>
            <div class="td-score-block" aria-label="MFWAI score: {sc} out of 100">
              <div class="td-score-num" style="color:{sc_col}">{sc}</div>
              <div class="td-score-label" style="color:{sc_col}">{sc_lbl}</div>
              <div class="td-score-sub">MFWAI score / 100</div>
            </div>
          </div>
        </header>

        <div class="td-layout">
          <div>
            <div class="td-panel">
              <div class="panel-label">Our verdict</div>
              <p class="verdict-text">{t['verdict']}</p>
            </div>

            <div class="td-panel">
              <div class="pros-cons-grid">
                <div>
                  <div class="panel-label">Pros</div>
                  <ul class="plist pros" aria-label="Pros">{pros_html}</ul>
                </div>
                <div>
                  <div class="panel-label">Cons</div>
                  <ul class="plist cons" aria-label="Cons">{cons_html}</ul>
                </div>
              </div>
            </div>

            <div class="td-panel">
              <div class="panel-label">Best for</div>
              <div class="best-for-list">{best_html}</div>
            </div>
          </div>

          <aside class="td-sidebar" aria-label="Pricing and actions">
            <div class="td-panel">
              <div class="price-box">
                <div class="price-from">Starting from</div>
                <div class="price-value">{t['starting_price']}</div>
                <div class="price-period">{t['pricing_model']}</div>
              </div>

              <a href="{t['affiliate_url']}" target="_blank"
                 rel="nofollow sponsored noopener noreferrer"
                 class="btn-td-cta"
                 aria-label="Try {t['name']} — affiliate link, opens in new tab">
                Try {t['name']}
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                  <polyline points="15,3 21,3 21,9"/>
                  <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
              </a>

              <div class="trust-items" role="list">
                <div class="trust-item" role="listitem">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  Affiliate link — no extra cost to you
                </div>
                {'<div class="trust-item" role="listitem"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'+str(t["trial_days"])+"-day free trial available</div>" if t.get('free_trial') else ''}
                <div class="trust-item" role="listitem">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
                  Reviewed {t.get('date_added', '2026')}
                </div>
                <div class="trust-item" role="listitem">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                  Independent editorial
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>

    <div class="page">
      <section class="sec" aria-labelledby="related-heading">
        <div class="sec-top">
          <div>
            <div class="sec-eyebrow">You might also like</div>
            <h2 class="sec-h2" id="related-heading">Related <em>tools</em></h2>
          </div>
        </div>
        <div class="tools-grid">{rel_cards}</div>
      </section>
    </div>"""

    return render(
        title=f'{t["name"]} Review 2026 — Honest Score & Verdict | Moving Forward With AI',
        desc=f'{t["name"]}: {t["tagline"]}. MFWAI score: {sc}/100. From {t["starting_price"]}. Honest pros, cons and verdict for UK users.',
        content=content,
        schema=tool_schema(t),
        bcs=bc_schema([('Home', '/'), ('Tools', '/tools'), (t['name'], f'/tool/{slug}')]))


@app.route('/compare')
def compare_index():
    cards = '\n'.join(f"""<a href="/compare/{c['slug']}" class="comp-card rv">
      <div class="comp-vs">
        <span class="comp-tool-name">{get_tool(c['tool_a'])['name']}</span>
        <span class="comp-vs-tag">VS</span>
        <span class="comp-tool-name">{get_tool(c['tool_b'])['name']}</span>
      </div>
      <div class="comp-desc">{c['description']}</div>
      <div class="comp-link">Read full comparison →</div>
    </a>""" for c in COMPARISONS)

    content = f"""
    {breadcrumb_html([('Home','/'),('Compare','/compare')])}
    <div class="page" style="padding-top:32px;padding-bottom:28px">
      <div class="sec-eyebrow">Head-to-head · High intent</div>
      <h1 style="font-family:var(--font-display);font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1;margin-top:8px">
        Compare AI tools <em style="color:var(--cyan);font-style:normal">side by side</em>
      </h1>
      <p style="font-size:.96rem;color:var(--ink3);margin-top:12px;max-width:520px;line-height:1.75">
        When you're deciding between two tools, our head-to-head comparisons give you the honest verdict.
      </p>
    </div>
    <div class="page"><div class="comp-grid">{cards}</div></div>"""
    return render(
        'Compare AI Tools Side by Side — Moving Forward With AI',
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

    def cd_card(t, is_winner):
        sc = t['score']
        sc_col = score_color(sc)
        verdict = c['verdict_a'] if t['slug'] == c['tool_a'] else c['verdict_b']
        win_badge = '<div class="cd-winner-tag">&#10003; Winner</div>' if is_winner else ''
        card_class = 'cd-card winner' if is_winner else 'cd-card'

        # Build free tier cell
        free_tier_cell = '<span class="tick">&#10003;</span>' if t.get('free_tier') else '<span class="cross">&#10007;</span>'

        # Build free trial cell
        if t.get('free_trial'):
            trial_days = t.get('trial_days', '')
            free_trial_cell = '<span class="tick">&#10003; ' + str(trial_days) + 'd</span>'
        else:
            free_trial_cell = '<span class="cross">&#10007;</span>'

        rows = (
            '<tr><td>MFWAI Score</td>'
            '<td style="color:' + sc_col + ';font-family:var(--font-mono);font-weight:600">' + str(sc) + '/100</td></tr>'
            '<tr><td>Rating</td><td>' + str(t['rating']) + '/5</td></tr>'
            '<tr><td>Starting price</td><td>' + str(t['starting_price']) + '</td></tr>'
            '<tr><td>Free tier</td><td>' + free_tier_cell + '</td></tr>'
            '<tr><td>Free trial</td><td>' + free_trial_cell + '</td></tr>'
            '<tr><td>Pricing</td><td>' + str(t['pricing_model']) + '</td></tr>'
        )

        return (
            '<div class="' + card_class + '">'
            + win_badge
            + '<div class="cd-name">' + t['name'] + '</div>'
            + '<div class="cd-score" style="color:' + sc_col + '">' + str(sc) + '</div>'
            + '<p class="cd-tagline">' + t['tagline'] + '</p>'
            + '<table class="comp-table"><tbody>' + rows + '</tbody></table>'
            + '<p class="cd-verdict">' + verdict + '</p>'
            + '<a href="' + t['affiliate_url'] + '" target="_blank" rel="nofollow sponsored noopener noreferrer"'
            + ' class="btn-try" style="margin-top:16px;width:100%;justify-content:center">'
            + 'Try ' + t['name'] + ' &rarr;'
            + '</a>'
            + '</div>'
        )

    winner_block = ''
    if c.get('winner_reason'):
        winner_name = winner['name'] if winner else 'Our verdict'
        winner_block = f"""<div class="winner-block rv">
          <div class="winner-label">// Winner: {winner_name}</div>
          <p class="winner-text">{c['winner_reason']}</p>
        </div>"""

    content = f"""
    {breadcrumb_html([('Home','/'),('Compare','/compare'),(c['headline'],f'/compare/{slug}')])}
    <div class="page" style="padding-top:32px;padding-bottom:24px">
      <div class="sec-eyebrow">{datetime.datetime.strptime(c['date'],'%Y-%m-%d').strftime('%d %b %Y')} · Head to head</div>
      <h1 style="font-family:var(--font-display);font-size:clamp(2rem,4.5vw,3.4rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1;margin-top:8px;margin-bottom:10px">
        {c['headline']}
      </h1>
      <p style="font-size:.98rem;color:var(--ink3);max-width:560px;line-height:1.75">{c['description']}</p>
    </div>
    <div class="page">
      <div class="comp-detail-grid">
        {cd_card(ta, winner and winner['slug']==ta['slug'])}
        {cd_card(tb, winner and winner['slug']==tb['slug'])}
      </div>
      {winner_block}
    </div>
    {email_capture()}"""

    return render(
        title=f'{c["headline"]} 2026 — Which Is Better? | Moving Forward With AI',
        desc=c.get('meta_description', c['description']),
        content=content,
        bcs=bc_schema([('Home', '/'), ('Compare', '/compare'), (c['headline'], f'/compare/{slug}')]))


@app.route('/blog')
def blog():
    posts = sorted([{**v, 'slug': k} for k, v in BLOG_POSTS.items()], key=lambda x: x['date'], reverse=True)
    cards = '\n'.join(f"""<a href="/blog/{p['slug']}" class="blog-card rv">
      <div class="blog-card-accent"></div>
      <div class="blog-card-body">
        <div class="blog-eyebrow">{datetime.datetime.strptime(p['date'],'%Y-%m-%d').strftime('%d %b %Y')} · {p.get('category','Guide')}</div>
        <div class="blog-title">{p['title']}</div>
        <div class="blog-desc">{p.get('description','')}</div>
        <div class="blog-link">Read →</div>
      </div>
    </a>""" for p in posts)

    content = f"""
    {breadcrumb_html([('Home','/'),('Guides','/blog')])}
    <div class="page" style="padding-top:32px;padding-bottom:28px">
      <div class="sec-eyebrow">Guides · How-tos · Analysis</div>
      <h1 style="font-family:var(--font-display);font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1;margin-top:8px">
        AI tool <em style="color:var(--cyan);font-style:normal">guides</em>
      </h1>
    </div>
    <div class="page"><div class="blog-grid">{cards}</div></div>"""
    return render(
        'AI Tool Guides for UK Freelancers — Moving Forward With AI',
        'In-depth guides, comparisons and how-tos for AI tools. Honest, independent, updated regularly.',
        content)


@app.route('/blog/<slug>')
def blog_detail(slug):
    post = BLOG_POSTS.get(slug)
    if not post: abort(404)
    dt = datetime.datetime.strptime(post['date'], '%Y-%m-%d').strftime('%d %B %Y')
    related = [get_tool(s) for s in post.get('related_tools', []) if get_tool(s)]
    rel_cards = '\n'.join(tool_card(t) for t in related)

    role_cta = ''
    if post.get('related_role'):
        role = get_role(post['related_role'])
        if role:
            role_cta = f"""<div style="background:var(--cyan-d);border:1px solid var(--cyan-g);border-radius:var(--r3);padding:22px 24px;margin:40px 0">
              <div class="sec-eyebrow" style="margin-bottom:10px">Related guide</div>
              <div style="font-family:var(--font-display);font-size:1.1rem;font-weight:700;color:var(--ink);margin-bottom:8px">
                <span aria-hidden="true">{role['icon']}</span> {role['headline']}
              </div>
              <a href="/for/{role['slug']}" style="font-family:var(--font-mono);font-size:.7rem;color:var(--cyan);letter-spacing:.06em;text-transform:uppercase">
                See the full stack →
              </a>
            </div>"""

    content = f"""
    {breadcrumb_html([('Home','/'),('Guides','/blog'),(post['title'][:45]+'…',f'/blog/{slug}')])}
    <div class="page-narrow" style="padding-top:32px">
      <div class="sec-eyebrow" style="margin-bottom:18px">{dt} · {post.get('category','Guide')}</div>
      <h1 style="font-family:var(--font-display);font-size:clamp(2rem,4.5vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1.06;margin-bottom:16px">
        {post.get('heading', post['title'])}
      </h1>
      <p style="font-size:1.02rem;line-height:1.8;color:var(--ink3);margin-bottom:44px;padding-bottom:36px;border-bottom:1px solid var(--div)">
        {post.get('description','')}
      </p>
      <div class="prose">{post.get('content','')}</div>
      {role_cta}
    </div>
    {'<div class="page"><section class="sec" aria-labelledby="blog-tools-heading"><div class="sec-top"><div><div class="sec-eyebrow">Mentioned in this guide</div><h2 class="sec-h2" id="blog-tools-heading">Related <em>tools</em></h2></div></div><div class="tools-grid">'+rel_cards+'</div></section></div>' if rel_cards else ''}
    {email_capture()}"""
    return render(
        title=post['title'] + ' — Moving Forward With AI',
        desc=post.get('meta_description', post.get('description', '')),
        content=content,
        bcs=bc_schema([('Home', '/'), ('Guides', '/blog'), (post['title'], f'/blog/{slug}')]))


@app.route('/category/<cat_slug>')
def category(cat_slug):
    tools = [t for t in TOOLS if slugify(t['category']) == cat_slug]
    if not tools: abort(404)
    cat_name = tools[0]['category']
    cards = '\n'.join(tool_card(t) for t in tools)
    content = f"""
    {breadcrumb_html([('Home','/'),('Tools','/tools'),(cat_name,f'/category/{cat_slug}')])}
    <div class="page" style="padding-top:32px;padding-bottom:28px">
      <div class="sec-eyebrow">{cat_name} · {len(tools)} tools</div>
      <h1 style="font-family:var(--font-display);font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1;margin-top:8px">
        Best <em style="color:var(--cyan);font-style:normal">{cat_name}</em> tools
      </h1>
    </div>
    <div class="page"><div class="tools-grid">{cards}</div></div>"""
    return render(
        f'Best {cat_name} AI Tools 2026 | Moving Forward With AI',
        f'Honest reviews of the best {cat_name.lower()} AI tools for UK users in 2026.',
        content,
        bcs=bc_schema([('Home', '/'), ('Tools', '/tools'), (cat_name, f'/category/{cat_slug}')]))


@app.route('/affiliate-disclosure')
def affiliate_disclosure():
    content = """<div class="legal-wrap">
      <h1>Affiliate Disclosure</h1>
      <div class="legal-note">
        <p><strong>Last updated:</strong> February 2026</p>
        <p>Moving Forward With AI earns affiliate commissions from some tools reviewed on this site. When you click a link and sign up or purchase, we may receive a commission — at no extra cost to you.</p>
      </div>
      <h2>Our editorial independence</h2>
      <p>Our editorial process is entirely independent of commercial relationships. Tools are scored and ranked on merit alone. We do not accept payment for reviews, rankings, or placement.</p>
      <h2>How it works</h2>
      <p>When you click a "Try" button or affiliate link and subsequently purchase or subscribe, the tool's company pays us a referral commission. This has zero effect on our scores or editorial content.</p>
      <h2>Contact</h2>
      <p>Questions? <a href="mailto:hello@movingforwardwithai.com" style="color:var(--cyan)">hello@movingforwardwithai.com</a></p>
    </div>"""
    return render(
        'Affiliate Disclosure — Moving Forward With AI',
        'How Moving Forward With AI earns commissions while maintaining editorial independence.',
        content)


@app.route('/privacy')
def privacy():
    content = """<div class="legal-wrap">
      <h1>Privacy Policy</h1>
      <div class="legal-note">
        <p><strong>Last updated:</strong> February 2026</p>
        <p>Moving Forward With AI is committed to protecting your privacy in accordance with UK GDPR.</p>
      </div>
      <h2>Information we collect</h2>
      <p>We collect minimal data via cookies and analytics. We do not collect personal information directly unless you contact us or sign up for our email list.</p>
      <h2>Cookies</h2>
      <p>We use essential cookies for site functionality and analytics cookies (with your consent) to understand how visitors use the site. Affiliate links may use tracking cookies from third-party services.</p>
      <h2>Your rights (UK GDPR)</h2>
      <p>You have the right to access, correct, delete and port your data. To exercise these rights, contact <a href="mailto:hello@movingforwardwithai.com" style="color:var(--cyan)">hello@movingforwardwithai.com</a>.</p>
    </div>"""
    return render(
        'Privacy Policy — Moving Forward With AI',
        'Moving Forward With AI privacy policy — UK GDPR compliant.',
        content)


@app.route('/terms')
def terms():
    content = """<div class="legal-wrap">
      <h1>Terms of Service</h1>
      <div class="legal-note">
        <p>By using movingforwardwithai.com you accept these terms.</p>
      </div>
      <h2>About this site</h2>
      <p>Moving Forward With AI is an independent review and affiliate marketing website. We are not affiliated with, endorsed by, or officially connected to any tool we review.</p>
      <h2>Accuracy</h2>
      <p>Prices, features and availability are verified at time of writing. Always confirm current pricing on the tool's official website before purchasing. We cannot be held responsible for outdated information.</p>
      <h2>Affiliate links</h2>
      <p>This site contains affiliate links. See our <a href="/affiliate-disclosure" style="color:var(--cyan)">Affiliate Disclosure</a> for full details.</p>
    </div>"""
    return render(
        'Terms of Service — Moving Forward With AI',
        'Terms and conditions for using Moving Forward With AI.',
        content)


@app.route('/api/tools')
def api_tools():
    return jsonify({'tools': [{
        'slug': t['slug'], 'name': t['name'], 'category': t['category'],
        'tagline': t['tagline'], 'score': t['score'], 'rating': t['rating'],
        'starting_price': t['starting_price'], 'tags': t.get('tags', []),
        'featured': t.get('featured', False)} for t in TOOLS]})


@app.route('/robots.txt')
def robots():
    return Response(
        f'User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {SITE_URL}/sitemap.xml\n',
        mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    today = datetime.date.today().isoformat()
    urls = [
        (SITE_URL + '/',        today, '1.0', 'weekly'),
        (SITE_URL + '/tools',   today, '0.9', 'weekly'),
        (SITE_URL + '/compare', today, '0.9', 'weekly'),
        (SITE_URL + '/blog',    today, '0.8', 'weekly'),
    ]
    for t in TOOLS:
        urls.append((f'{SITE_URL}/tool/{t["slug"]}', t.get('date_added', today), '0.8', 'monthly'))
    for r in ROLES:
        urls.append((f'{SITE_URL}/for/{r["slug"]}', today, '0.8', 'weekly'))
    for c in COMPARISONS:
        urls.append((f'{SITE_URL}/compare/{c["slug"]}', c.get('date', today), '0.8', 'monthly'))
    for slug, post in BLOG_POSTS.items():
        urls.append((f'{SITE_URL}/blog/{slug}', post.get('date', today), '0.7', 'monthly'))
    cats = list({slugify(t['category']) for t in TOOLS})
    for cat in cats:
        urls.append((f'{SITE_URL}/category/{cat}', today, '0.6', 'monthly'))
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, lm, pri, cf in sorted(urls):
        xml += f'  <url><loc>{url}</loc><lastmod>{lm}</lastmod><changefreq>{cf}</changefreq><priority>{pri}</priority></url>\n'
    return Response(xml + '</urlset>', mimetype='application/xml')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
