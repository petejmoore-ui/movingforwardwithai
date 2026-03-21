import os, json, re, datetime
from data import TOOLS, COMPARISONS, BLOG_POSTS, LEAD_MAGNET, ROLES
from flask import Flask, render_template_string, request, abort, Response, jsonify
from flask_caching import Cache
from dotenv import load_dotenv

load_dotenv()

app        = Flask(__name__)

# ── Flask-Caching Configuration ──────────────────────────────────────────────
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)



SITE_URL   = "https://www.movingforwardwithai.com"
SITE_NAME  = "Moving Forward With AI"
OG_IMAGE   = SITE_URL + "/static/og-default.png"


# ── helpers ──────────────────────────────────────────────────────────────────

def slugify(t):
    t = re.sub(r'&','-and-',str(t).lower())
    t = re.sub(r'[^a-z0-9\s-]','',t)
    return re.sub(r'[\s-]+',' ',t).strip().replace(' ','-')

def get_tool(slug):  return next((t for t in TOOLS if t['slug']==slug), None)
def get_role(slug):  return next((r for r in ROLES if r['slug']==slug), None)
def get_comp(slug):  return next((c for c in COMPARISONS if c['slug']==slug), None)

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
    sc = t['score']
    price_str = re.sub(r'[^0-9.]', '', t['starting_price'].split('/')[0]) or "0"
    review_count = t.get('review_count', '1').replace(',', '').replace('+', '') or "1"
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": t['name'],
        "description": t['tagline'],
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "offers": {
            "@type": "Offer",
            "priceCurrency": "USD",
            "price": price_str,
            "url": t['affiliate_url']
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": str(round(sc / 20, 1)),
            "bestRating": "5",
            "worstRating": "1",
            "ratingCount": review_count
        },
        "review": {
            "@type": "Review",
            "author": {
                "@type": "Organization",
                "name": SITE_NAME
            },
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": str(round(sc / 20, 1)),
                "bestRating": "5",
                "worstRating": "1"
            },
            "reviewBody": t['verdict']
        }
    })

def bc_schema(crumbs):
    return json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[{"@type":"ListItem","position":i+1,"name":n,
        "item":(SITE_URL+u if not u.startswith('http') else u)}
        for i,(n,u) in enumerate(crumbs)]})


def website_schema():
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": SITE_URL + "/",
        "description": "AI tool reviews with transparent scores for freelancers, marketers, and builders.",
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/"},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": SITE_URL + "/tools?q={search_term_string}"},
            "query-input": "required name=search_term_string"
        }
    })


def faq_schema(pairs):
    if not pairs:
        return ''
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in pairs
        ]
    })


def itemlist_schema(tools_list, list_name="AI Tools"):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": list_name,
        "numberOfItems": len(tools_list),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": t['name'],
             "url": SITE_URL + "/tool/" + t['slug']}
            for i, t in enumerate(tools_list[:50])
        ]
    })


def comparison_schema(ta, tb, c):
    def app_entry(t):
        return {
            "@type": "SoftwareApplication", "name": t['name'],
            "description": t['tagline'], "applicationCategory": "BusinessApplication",
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": str(round(t['score'] / 20, 1)),
                "bestRating": "5", "worstRating": "1",
                "ratingCount": t.get('review_count', '1').replace(',', '').replace('+', '') or "1"
            }
        }
    return json.dumps({
        "@context": "https://schema.org", "@type": "WebPage",
        "name": c['headline'], "description": c.get('meta_description', c['description']),
        "about": [app_entry(ta), app_entry(tb)]
    })


def extract_faq_from_blog(post):
    content = post.get('content', '')
    pairs = []
    pattern = r'<h[23][^>]*>(.*?\?.*?)</h[23]>\s*<p>(.*?)</p>'
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    for q, a in matches:
        clean_q = re.sub(r'<[^>]+>', '', q).strip()
        clean_a = re.sub(r'<[^>]+>', '', a).strip()
        if clean_q and clean_a and len(clean_a) > 30:
            pairs.append((clean_q, clean_a[:500]))
    title = post.get('heading', post.get('title', ''))
    desc = post.get('description', '')
    if desc and len(desc) > 40:
        if 'best' in title.lower():
            pairs.insert(0, (f"What are the {title.split('—')[0].strip().lower()}?", desc[:500]))
        elif 'how to' in title.lower():
            pairs.insert(0, (title.split('—')[0].strip() + '?', desc[:500]))
    return pairs[:5]


def tool_meta_title(t):
    name = t['name']
    cat = t['category']
    title = f"{name} Review 2026 — {cat} | MFWAI"
    if len(title) <= 60: return title
    title = f"{name} Review 2026 | Moving Forward With AI"
    if len(title) <= 60: return title
    return f"{name} Review 2026 | MFWAI"


def comp_meta_title(ta_name, tb_name):
    title = f"{ta_name} vs {tb_name} 2026 — Which Is Better? | MFWAI"
    if len(title) <= 60: return title
    title = f"{ta_name} vs {tb_name} 2026 | MFWAI"
    if len(title) <= 60: return title
    return f"{ta_name} vs {tb_name} | MFWAI"


def blog_meta_title(post):
    base = post['title']
    full = f"{base} | MFWAI"
    if len(full) <= 60: return full
    return base[:55] + chr(8230)


def generate_comparison_verdict(ta, tb):
    if not ta or not tb:
        return ''
    sa, sb = ta['score'], tb['score']
    diff = abs(sa - sb)
    na, nb = ta['name'], tb['name']
    pa, pb = ta['starting_price'], tb['starting_price']
    cat_a, cat_b = ta['category'], tb['category']
    free_a = ta.get('free_tier', False)
    free_b = tb.get('free_tier', False)

    def parse_price(p):
        try:
            return float(p.replace('$','').replace('/mo','').replace('/user','').split('/')[0])
        except (ValueError, AttributeError):
            return 0
    price_a = parse_price(pa)
    price_b = parse_price(pb)
    price_ratio = max(price_a, price_b) / max(min(price_a, price_b), 0.01)

    if cat_a != cat_b:
        return (
            f"{na} ({cat_a}) and {nb} ({cat_b}) serve different purposes — "
            f"this is less about which is better and more about which job you need done. "
            f"{na} scores {sa}/100 and starts at {pa}; {nb} scores {sb}/100 and starts at {pb}. "
            f"If your primary need falls into {cat_a.lower()}, go with {na}. "
            f"If you need {cat_b.lower()} capabilities, {nb} is your tool."
        )
    if diff >= 8:
        winner = na if sa > sb else nb
        loser = nb if sa > sb else na
        ws = max(sa, sb); ls = min(sa, sb)
        wp = pa if sa > sb else pb; lp = pb if sa > sb else pa
        return (
            f"{winner} is the stronger choice in this matchup, scoring {ws}/100 vs "
            f"{loser}'s {ls}/100. The {diff}-point gap reflects meaningful differences "
            f"in product quality, feature depth, and user satisfaction. "
            f"{winner} starts at {wp}; {loser} starts at {lp}."
        )
    if free_a and not free_b:
        return (
            f"With scores within {diff} points ({na}: {sa}/100, {nb}: {sb}/100), "
            f"{na} offers a free tier while {nb} does not (starting at {pb}). "
            f"Start with {na}'s free plan to evaluate the core experience."
        )
    if free_b and not free_a:
        return (
            f"With scores within {diff} points ({na}: {sa}/100, {nb}: {sb}/100), "
            f"{nb} offers a free tier while {na} does not (starting at {pa}). "
            f"Start with {nb}'s free plan to evaluate the core experience."
        )
    if free_a and free_b:
        return (
            f"This is a close matchup — {na} scores {sa}/100 and {nb} scores {sb}/100. "
            f"Both offer free tiers, so the best approach is to test each with your actual workflow. "
            f"{na} starts at {pa} on paid plans; {nb} starts at {pb}."
        )
    if price_ratio > 1.5 and price_a > 0 and price_b > 0:
        cheaper = na if price_a < price_b else nb
        pricier = nb if price_a < price_b else na
        cp = pa if price_a < price_b else pb
        pp = pb if price_a < price_b else pa
        cs = sa if price_a < price_b else sb
        ps = sb if price_a < price_b else sa
        return (
            f"Price is a significant factor here: {cheaper} starts at {cp} while "
            f"{pricier} starts at {pp}. {cheaper} scores {cs}/100; {pricier} scores {ps}/100."
        )
    return (
        f"{na} ({sa}/100) and {nb} ({sb}/100) are closely matched tools. "
        f"{na} starts at {pa}; {nb} starts at {pb}. "
        f"Review the pros and cons above and consider which tool's strengths align with your highest-priority use case."
    )


# ── Tool Finder Quiz: Matching Profiles ──────────────────────────────────────
TOOL_FINDER_PROFILES = {
    # ── AI Writing ─────────────────────────────────────────────────────────
    'jasper': {
        'roles':        ['marketer', 'content-creator', 'small-business-owner'],
        'goals':        ['create-content', 'grow-business'],
        'max_budget':   'mid',
        'skill_levels': ['basic', 'not-technical'],
    },
    'copy-ai': {
        'roles':        ['marketer', 'freelancer', 'freelance-writer', 'small-business-owner'],
        'goals':        ['create-content', 'grow-business'],
        'max_budget':   'mid',
        'skill_levels': ['basic', 'not-technical'],
    },
    'writesonic': {
        'roles':        ['content-creator', 'freelance-writer', 'marketer'],
        'goals':        ['create-content', 'improve-seo'],
        'max_budget':   'low',
        'skill_levels': ['basic', 'not-technical'],
    },
    # ── SEO Tools ──────────────────────────────────────────────────────────
    'surfer-seo': {
        'roles':        ['seo-professional', 'content-creator', 'marketer'],
        'goals':        ['improve-seo', 'create-content'],
        'max_budget':   'mid',
        'skill_levels': ['basic', 'fairly-technical'],
    },
    'semrush': {
        'roles':        ['seo-professional', 'marketer', 'small-business-owner'],
        'goals':        ['improve-seo', 'research-data', 'grow-business'],
        'max_budget':   'high',
        'skill_levels': ['basic', 'fairly-technical', 'developer'],
    },
    'ahrefs': {
        'roles':        ['seo-professional', 'marketer', 'content-creator'],
        'goals':        ['improve-seo', 'research-data'],
        'max_budget':   'high',
        'skill_levels': ['basic', 'fairly-technical', 'developer'],
    },
    # ── AI Assistants / General ────────────────────────────────────────────
    'chatgpt': {
        'roles':        ['marketer', 'content-creator', 'freelancer', 'freelance-writer',
                         'seo-professional', 'small-business-owner'],
        'goals':        ['create-content', 'research-data', 'automate-workflow', 'write-code'],
        'max_budget':   'low',
        'skill_levels': ['not-technical', 'basic', 'fairly-technical', 'developer'],
    },
    'claude': {
        'roles':        ['marketer', 'content-creator', 'freelancer', 'freelance-writer',
                         'seo-professional', 'small-business-owner'],
        'goals':        ['create-content', 'research-data', 'write-code', 'automate-workflow'],
        'max_budget':   'low',
        'skill_levels': ['not-technical', 'basic', 'fairly-technical', 'developer'],
    },
    'gemini': {
        'roles':        ['marketer', 'content-creator', 'freelancer', 'small-business-owner'],
        'goals':        ['create-content', 'research-data', 'automate-workflow'],
        'max_budget':   'free',
        'skill_levels': ['not-technical', 'basic', 'fairly-technical'],
    },
    # ── Code / Developer ───────────────────────────────────────────────────
    'github-copilot': {
        'roles':        ['freelancer'],
        'goals':        ['write-code', 'automate-workflow'],
        'max_budget':   'low',
        'skill_levels': ['fairly-technical', 'developer'],
    },
    'cursor': {
        'roles':        ['freelancer'],
        'goals':        ['write-code', 'automate-workflow'],
        'max_budget':   'low',
        'skill_levels': ['fairly-technical', 'developer'],
    },
    'windsurf': {
        'roles':        ['freelancer'],
        'goals':        ['write-code', 'automate-workflow'],
        'max_budget':   'low',
        'skill_levels': ['fairly-technical', 'developer'],
    },
    # ── Automation ─────────────────────────────────────────────────────────
    'zapier': {
        'roles':        ['marketer', 'small-business-owner', 'freelancer'],
        'goals':        ['automate-workflow', 'grow-business'],
        'max_budget':   'mid',
        'skill_levels': ['basic', 'not-technical', 'fairly-technical'],
    },
    'make': {
        'roles':        ['marketer', 'freelancer', 'small-business-owner'],
        'goals':        ['automate-workflow', 'grow-business'],
        'max_budget':   'low',
        'skill_levels': ['basic', 'fairly-technical'],
    },
    # ── Website & App Builders ─────────────────────────────────────────────
    'bolt-new': {
        'roles':        ['small-business-owner', 'freelancer', 'marketer'],
        'goals':        ['write-code', 'grow-business', 'automate-workflow'],
        'max_budget':   'low',
        'skill_levels': ['not-technical', 'basic', 'fairly-technical'],
    },
    # ── Video & Media ──────────────────────────────────────────────────────
    'runway': {
        'roles':        ['content-creator', 'marketer'],
        'goals':        ['create-content'],
        'max_budget':   'low',
        'skill_levels': ['not-technical', 'basic', 'fairly-technical'],
    },
    # ── Design / Image ─────────────────────────────────────────────────────
    'midjourney': {
        'roles':        ['content-creator', 'marketer', 'freelancer'],
        'goals':        ['create-content'],
        'max_budget':   'low',
        'skill_levels': ['not-technical', 'basic', 'fairly-technical'],
    },
    'canva': {
        'roles':        ['marketer', 'content-creator', 'small-business-owner', 'freelancer'],
        'goals':        ['create-content', 'grow-business'],
        'max_budget':   'low',
        'skill_levels': ['not-technical', 'basic'],
    },
    # ── Research / Data ────────────────────────────────────────────────────
    'perplexity': {
        'roles':        ['seo-professional', 'marketer', 'freelancer', 'content-creator',
                         'freelance-writer'],
        'goals':        ['research-data', 'create-content'],
        'max_budget':   'low',
        'skill_levels': ['not-technical', 'basic', 'fairly-technical', 'developer'],
    },
    'notion-ai': {
        'roles':        ['freelancer', 'small-business-owner', 'marketer', 'content-creator'],
        'goals':        ['automate-workflow', 'create-content', 'research-data'],
        'max_budget':   'low',
        'skill_levels': ['not-technical', 'basic', 'fairly-technical'],
    },
    'grammarly': {
        'roles':        ['freelance-writer', 'content-creator', 'marketer', 'freelancer'],
        'goals':        ['create-content'],
        'max_budget':   'low',
        'skill_levels': ['not-technical', 'basic'],
    },
}

BUDGET_ORDER = {'free': 0, 'low': 1, 'mid': 2, 'high': 3}


def match_tools_for_quiz(role, goal, budget, skill_level, tools_list):
    user_budget_tier = BUDGET_ORDER.get(budget, 1)
    scored = []

    for t in tools_list:
        slug = t['slug']
        profile = TOOL_FINDER_PROFILES.get(slug)
        if not profile:
            continue

        tool_budget_tier = BUDGET_ORDER.get(profile.get('max_budget', 'low'), 1)
        if user_budget_tier < tool_budget_tier and not t.get('free_tier'):
            continue

        points = 0.0

        if role in profile.get('roles', []):
            points += 3

        if goal in profile.get('goals', []):
            points += 3

        if skill_level in profile.get('skill_levels', []):
            points += 1

        points += t['score'] / 50.0

        if points > (t['score'] / 50.0):
            scored.append((points, t))

    scored.sort(key=lambda x: -x[0])
    return [t for _, t in scored[:4]]


TOOL_FINDER_TEMPLATE = """
{{ breadcrumb|safe }}

<div class="page">
  <div class="tf-wrap" id="tool-finder-app">

    <!-- Progress Bar -->
    <div class="tf-progress" role="progressbar" aria-valuenow="1" aria-valuemin="1" aria-valuemax="4" aria-label="Quiz progress">
      <div class="tf-progress-bar" id="tf-bar" style="width:25%"></div>
      <div class="tf-progress-steps">
        <span class="tf-step active" data-step="1">1</span>
        <span class="tf-step" data-step="2">2</span>
        <span class="tf-step" data-step="3">3</span>
        <span class="tf-step" data-step="4">4</span>
      </div>
    </div>

    <!-- Step 1: Role -->
    <div class="tf-screen active" id="tf-step-1" role="group" aria-labelledby="tf-q1">
      <div class="tf-question-wrap">
        <div class="tf-step-label">Step 1 of 4</div>
        <h2 class="tf-question" id="tf-q1">What best describes you?</h2>
        <p class="tf-hint">Pick the role closest to your day-to-day work.</p>
      </div>
      <div class="tf-options" role="radiogroup" aria-labelledby="tf-q1">
        <button class="tf-option" data-key="role" data-value="marketer" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F4E3;</span>
          <span class="tf-opt-text">Marketer</span>
        </button>
        <button class="tf-option" data-key="role" data-value="seo-professional" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F50D;</span>
          <span class="tf-opt-text">SEO Professional</span>
        </button>
        <button class="tf-option" data-key="role" data-value="content-creator" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x270D;&#xFE0F;</span>
          <span class="tf-opt-text">Content Creator</span>
        </button>
        <button class="tf-option" data-key="role" data-value="freelancer" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F4BC;</span>
          <span class="tf-opt-text">Freelancer</span>
        </button>
        <button class="tf-option" data-key="role" data-value="small-business-owner" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F3EA;</span>
          <span class="tf-opt-text">Small Business Owner</span>
        </button>
        <button class="tf-option" data-key="role" data-value="freelance-writer" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F4DD;</span>
          <span class="tf-opt-text">Freelance Writer</span>
        </button>
      </div>
    </div>

    <!-- Step 2: Goal -->
    <div class="tf-screen" id="tf-step-2" role="group" aria-labelledby="tf-q2">
      <div class="tf-question-wrap">
        <div class="tf-step-label">Step 2 of 4</div>
        <h2 class="tf-question" id="tf-q2">What's your main goal right now?</h2>
        <p class="tf-hint">We'll match tools to what you actually need to get done.</p>
      </div>
      <div class="tf-options" role="radiogroup" aria-labelledby="tf-q2">
        <button class="tf-option" data-key="goal" data-value="create-content" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x26A1;</span>
          <span class="tf-opt-text">Create content faster</span>
        </button>
        <button class="tf-option" data-key="goal" data-value="improve-seo" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F4C8;</span>
          <span class="tf-opt-text">Improve SEO rankings</span>
        </button>
        <button class="tf-option" data-key="goal" data-value="automate-workflow" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F504;</span>
          <span class="tf-opt-text">Automate my workflow</span>
        </button>
        <button class="tf-option" data-key="goal" data-value="write-code" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F4BB;</span>
          <span class="tf-opt-text">Write better code</span>
        </button>
        <button class="tf-option" data-key="goal" data-value="research-data" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F52C;</span>
          <span class="tf-opt-text">Research and analyse data</span>
        </button>
        <button class="tf-option" data-key="goal" data-value="grow-business" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F680;</span>
          <span class="tf-opt-text">Grow my business</span>
        </button>
      </div>
    </div>

    <!-- Step 3: Budget -->
    <div class="tf-screen" id="tf-step-3" role="group" aria-labelledby="tf-q3">
      <div class="tf-question-wrap">
        <div class="tf-step-label">Step 3 of 4</div>
        <h2 class="tf-question" id="tf-q3">What's your monthly budget for AI tools?</h2>
        <p class="tf-hint">We'll only recommend tools within your price range.</p>
      </div>
      <div class="tf-options tf-options-narrow" role="radiogroup" aria-labelledby="tf-q3">
        <button class="tf-option" data-key="budget" data-value="free" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F193;</span>
          <span class="tf-opt-text">Free only</span>
        </button>
        <button class="tf-option" data-key="budget" data-value="low" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F4B5;</span>
          <span class="tf-opt-text">Under $50/mo</span>
        </button>
        <button class="tf-option" data-key="budget" data-value="mid" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F4B0;</span>
          <span class="tf-opt-text">$50 &ndash; $150/mo</span>
        </button>
        <button class="tf-option" data-key="budget" data-value="high" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F48E;</span>
          <span class="tf-opt-text">$150+/mo</span>
        </button>
      </div>
    </div>

    <!-- Step 4: Skill Level -->
    <div class="tf-screen" id="tf-step-4" role="group" aria-labelledby="tf-q4">
      <div class="tf-question-wrap">
        <div class="tf-step-label">Step 4 of 4</div>
        <h2 class="tf-question" id="tf-q4">How technical are you?</h2>
        <p class="tf-hint">This helps us match tool complexity to your comfort level.</p>
      </div>
      <div class="tf-options tf-options-narrow" role="radiogroup" aria-labelledby="tf-q4">
        <button class="tf-option" data-key="skill" data-value="not-technical" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F331;</span>
          <span class="tf-opt-text">Not technical at all</span>
        </button>
        <button class="tf-option" data-key="skill" data-value="basic" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F527;</span>
          <span class="tf-opt-text">Comfortable with basic tools</span>
        </button>
        <button class="tf-option" data-key="skill" data-value="fairly-technical" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x2699;&#xFE0F;</span>
          <span class="tf-opt-text">Fairly technical</span>
        </button>
        <button class="tf-option" data-key="skill" data-value="developer" type="button" role="radio" aria-checked="false">
          <span class="tf-opt-icon" aria-hidden="true">&#x1F5A5;&#xFE0F;</span>
          <span class="tf-opt-text">Developer-level</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div class="tf-screen" id="tf-loading" style="text-align:center;padding:80px 0">
      <div class="tf-loader" aria-label="Finding your tools"></div>
      <p style="font-family:var(--font-mono);font-size:.76rem;color:var(--ink3);margin-top:20px;letter-spacing:.06em">
        Matching tools to your answers&hellip;
      </p>
    </div>

    <!-- Results -->
    <div class="tf-screen" id="tf-results">
      <div class="tf-question-wrap">
        <div class="tf-step-label">Your results</div>
        <h2 class="tf-question">Your recommended AI stack</h2>
        <p class="tf-hint">Based on your role, goals, budget, and skill level &mdash; here are the tools we'd pick for you.</p>
      </div>
      <div class="tf-results-grid" id="tf-results-grid"></div>
      <div class="tf-results-actions">
        <button class="btn-ghost" id="tf-retake" type="button" onclick="tfRetake()">
          &#8635; Retake quiz
        </button>
        <a href="/tools" class="btn-ghost">Browse all tools &rarr;</a>
      </div>
    </div>

    <!-- Back Button -->
    <div class="tf-nav" id="tf-nav">
      <button class="tf-back-btn" id="tf-back" type="button" style="display:none" aria-label="Go back to previous question">
        &larr; Back
      </button>
    </div>

  </div>
</div>

<script>
(function() {
  var currentStep = 1;
  var totalSteps  = 4;
  var answers     = {};
  var bar         = document.getElementById('tf-bar');
  var backBtn     = document.getElementById('tf-back');
  var steps       = document.querySelectorAll('.tf-step');
  var progressWrap= document.querySelector('.tf-progress');

  function showStep(n) {
    document.querySelectorAll('.tf-screen').forEach(function(s) {
      s.classList.remove('active');
    });
    var target = document.getElementById('tf-step-' + n);
    if (target) target.classList.add('active');
    bar.style.width = ((n / totalSteps) * 100) + '%';
    steps.forEach(function(s) {
      var sn = parseInt(s.getAttribute('data-step'));
      s.classList.toggle('active', sn <= n);
      s.classList.toggle('completed', sn < n);
    });
    backBtn.style.display = (n > 1) ? 'inline-flex' : 'none';
    progressWrap.setAttribute('aria-valuenow', n);
    currentStep = n;
    window.scrollTo({top: document.getElementById('tool-finder-app').offsetTop - 80, behavior: 'smooth'});
  }

  document.querySelectorAll('.tf-option').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var key   = this.getAttribute('data-key');
      var value = this.getAttribute('data-value');
      answers[key] = value;
      this.closest('.tf-options').querySelectorAll('.tf-option').forEach(function(b) {
        b.classList.remove('selected');
        b.setAttribute('aria-checked', 'false');
      });
      this.classList.add('selected');
      this.setAttribute('aria-checked', 'true');
      setTimeout(function() {
        if (currentStep < totalSteps) {
          showStep(currentStep + 1);
        } else {
          submitQuiz();
        }
      }, 280);
    });
  });

  backBtn.addEventListener('click', function() {
    if (currentStep > 1) showStep(currentStep - 1);
  });

  function submitQuiz() {
    document.querySelectorAll('.tf-screen').forEach(function(s) {
      s.classList.remove('active');
    });
    document.getElementById('tf-loading').classList.add('active');
    backBtn.style.display = 'none';
    progressWrap.style.display = 'none';
    var params = new URLSearchParams({
      role: answers.role || '', goal: answers.goal || '',
      budget: answers.budget || '', skill: answers.skill || ''
    });
    fetch('/api/tool-finder?' + params.toString())
      .then(function(r) { return r.json(); })
      .then(function(data) { renderResults(data.tools || []); })
      .catch(function() { renderResults([]); });
  }

  function renderResults(tools) {
    var grid = document.getElementById('tf-results-grid');
    if (tools.length === 0) {
      grid.innerHTML = '<div style="text-align:center;padding:40px;font-size:.9rem;color:var(--ink3)">' +
        'No exact matches found. Try broadening your budget or <a href="/tools" style="color:var(--cyan)">browse all tools</a>.</div>';
    } else {
      grid.innerHTML = tools.map(function(t, i) {
        var scCol = t.score >= 88 ? 'var(--green)' : (t.score >= 78 ? 'var(--cyan)' : 'var(--amber)');
        var scBg  = t.score >= 88 ? 'var(--green-d)' : (t.score >= 78 ? 'var(--cyan-d)' : 'var(--amber-d)');
        var scBdr = t.score >= 88 ? 'var(--green-g)' : (t.score >= 78 ? 'var(--cyan-g)' : 'var(--amber-g)');
        var rank  = i === 0 ? '<div class="tf-res-rank">Best match</div>' : '';
        return '<div class="tf-result-card' + (i === 0 ? ' tf-top-pick' : '') + '">' +
          rank +
          '<div class="tf-res-header">' +
            '<div class="tf-res-info">' +
              '<div class="tf-res-name">' + t.name + '</div>' +
              '<div class="tf-res-cat">' + t.category + '</div>' +
            '</div>' +
            '<div class="tf-res-score" style="color:' + scCol + ';background:' + scBg + ';border:1px solid ' + scBdr + '">' + t.score + '/100</div>' +
          '</div>' +
          '<p class="tf-res-verdict">' + t.verdict + '</p>' +
          '<div class="tf-res-footer">' +
            '<div class="tf-res-price">' +
              '<span class="tf-res-price-val">' + t.starting_price + '</span>' +
              '<span class="tf-res-price-model">' + t.pricing_model + '</span>' +
            '</div>' +
            '<div class="tf-res-btns">' +
              '<a href="/tool/' + t.slug + '" class="btn-outline" style="padding:8px 14px;font-size:.66rem">Full review</a>' +
              '<a href="' + t.affiliate_url + '" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-try" style="padding:10px 16px;font-size:.68rem">Try it &#8594;</a>' +
            '</div>' +
          '</div>' +
        '</div>';
      }).join('');
    }
    document.querySelectorAll('.tf-screen').forEach(function(s) { s.classList.remove('active'); });
    document.getElementById('tf-results').classList.add('active');
  }

  window.tfRetake = function() {
    answers = {};
    currentStep = 1;
    document.querySelectorAll('.tf-option').forEach(function(b) {
      b.classList.remove('selected');
      b.setAttribute('aria-checked', 'false');
    });
    progressWrap.style.display = '';
    showStep(1);
  };
})();
</script>
"""

TOOL_FINDER_CSS = """
/* ═══════════════════════════════════════════════════════════════
   TOOL FINDER QUIZ
   ═══════════════════════════════════════════════════════════════ */
.tf-wrap { max-width:680px; margin:0 auto; padding:clamp(48px,6vw,80px) 0 clamp(64px,8vw,96px) }
.tf-progress { position:relative; height:4px; background:var(--bg4); border-radius:var(--rpill); margin-bottom:48px; overflow:visible }
.tf-progress-bar { height:100%; background:linear-gradient(90deg, var(--cyan), var(--violet)); border-radius:var(--rpill); transition:width .4s var(--ease) }
.tf-progress-steps { position:absolute; top:-10px; left:0; right:0; display:flex; justify-content:space-between; pointer-events:none }
.tf-step { width:24px; height:24px; border-radius:50%; background:var(--bg4); border:2px solid var(--bdr2); display:flex; align-items:center; justify-content:center; font-family:var(--font-mono); font-size:.58rem; font-weight:600; color:var(--ink4); transition:all .3s var(--ease) }
.tf-step.active { background:var(--cyan); border-color:var(--cyan); color:#060810; box-shadow:0 0 0 4px var(--cyan-d) }
.tf-step.completed { background:var(--cyan); border-color:var(--cyan); color:#060810 }
.tf-screen { display:none; animation:tfFadeIn .35s var(--ease) }
.tf-screen.active { display:block }
@keyframes tfFadeIn { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
.tf-question-wrap { margin-bottom:32px }
.tf-step-label { font-family:var(--font-mono); font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; color:var(--cyan); margin-bottom:12px; display:flex; align-items:center; gap:8px }
.tf-step-label::before { content:''; width:16px; height:1px; background:var(--cyan) }
.tf-question { font-family:var(--font-display); font-size:clamp(1.6rem,3.5vw,2.4rem); font-weight:800; letter-spacing:-.05em; color:var(--ink); line-height:1.1; margin-bottom:10px }
.tf-hint { font-size:.9rem; color:var(--ink3); line-height:1.65 }
.tf-options { display:grid; grid-template-columns:1fr 1fr; gap:10px }
.tf-options-narrow { grid-template-columns:1fr 1fr }
.tf-option { display:flex; align-items:center; gap:14px; padding:18px 20px; background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); font-family:var(--font-body); font-size:.92rem; font-weight:500; color:var(--ink2); text-align:left; cursor:pointer; transition:all .2s var(--ease); position:relative; overflow:hidden }
.tf-option::before { content:''; position:absolute; inset:0; background:linear-gradient(135deg,var(--cyan-d),transparent); opacity:0; transition:opacity .2s }
.tf-option:hover { border-color:var(--bdr2); transform:translateY(-2px); box-shadow:var(--sh1) }
.tf-option:hover::before { opacity:1 }
.tf-option.selected { border-color:var(--cyan); background:var(--cyan-d); color:var(--ink); box-shadow:var(--shc) }
.tf-option.selected::after { content:'\\2713'; position:absolute; top:10px; right:12px; font-size:.72rem; color:var(--cyan); font-weight:700 }
.tf-opt-icon { font-size:1.4rem; flex-shrink:0; position:relative; z-index:1 }
.tf-opt-text { position:relative; z-index:1 }
.tf-loader { width:40px; height:40px; border:3px solid var(--bdr2); border-top-color:var(--cyan); border-radius:50%; margin:0 auto; animation:tfSpin .8s linear infinite }
@keyframes tfSpin { to{transform:rotate(360deg)} }
.tf-results-grid { display:flex; flex-direction:column; gap:14px; margin-bottom:32px }
.tf-result-card { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); padding:24px; position:relative; transition:transform .25s var(--spring),box-shadow .25s }
.tf-result-card:hover { transform:translateY(-3px); box-shadow:var(--sh2) }
.tf-result-card.tf-top-pick { border-color:var(--green-g); box-shadow:0 0 0 1px var(--green-g),var(--shg) }
.tf-result-card.tf-top-pick::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:var(--green); border-radius:var(--r3) var(--r3) 0 0 }
.tf-res-rank { position:absolute; top:14px; right:14px; background:var(--green-d); border:1px solid var(--green-g); color:var(--green); border-radius:var(--rpill); padding:3px 11px; font-family:var(--font-mono); font-size:.58rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase }
.tf-res-header { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:12px }
.tf-res-info { flex:1; min-width:0 }
.tf-res-name { font-family:var(--font-display); font-size:1.2rem; font-weight:700; color:var(--ink); letter-spacing:-.03em }
.tf-res-cat { font-family:var(--font-mono); font-size:.6rem; color:var(--ink4); letter-spacing:.08em; text-transform:uppercase; margin-top:2px }
.tf-res-score { font-family:var(--font-mono); font-size:.72rem; font-weight:600; padding:4px 12px; border-radius:var(--r1); flex-shrink:0 }
.tf-res-verdict { font-size:.88rem; line-height:1.7; color:var(--ink3); margin-bottom:16px }
.tf-res-footer { display:flex; align-items:center; justify-content:space-between; gap:16px; padding-top:14px; border-top:1px solid var(--div); flex-wrap:wrap }
.tf-res-price { display:flex; align-items:baseline; gap:8px }
.tf-res-price-val { font-family:var(--font-display); font-size:1.05rem; font-weight:700; color:var(--ink); letter-spacing:-.03em }
.tf-res-price-model { font-family:var(--font-mono); font-size:.6rem; color:var(--ink4); letter-spacing:.04em; text-transform:uppercase }
.tf-res-btns { display:flex; align-items:center; gap:8px }
.tf-results-actions { display:flex; align-items:center; justify-content:center; gap:12px; flex-wrap:wrap }
.tf-nav { margin-top:28px }
.tf-back-btn { display:inline-flex; align-items:center; gap:6px; font-family:var(--font-mono); font-size:.74rem; color:var(--ink3); letter-spacing:.04em; padding:8px 16px; border-radius:var(--rpill); border:1px solid var(--bdr); background:var(--surf); transition:all .18s; cursor:pointer }
.tf-back-btn:hover { color:var(--ink); border-color:var(--bdr2); background:var(--cyan-d) }
@media (max-width:520px) {
  .tf-options, .tf-options-narrow { grid-template-columns:1fr }
  .tf-res-footer { flex-direction:column; align-items:flex-start }
  .tf-res-btns { width:100% }
  .tf-res-btns a { flex:1; text-align:center; justify-content:center }
}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# CSS  (original CSS + Tool Finder CSS appended)
# ═══════════════════════════════════════════════════════════════════════════════
CSS = """
:root {
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

html.light {
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
*, *::before, *::after {
  transition-property: background-color, border-color, color;
  transition-duration: 0.25s;
  transition-timing-function: cubic-bezier(.25,.46,.45,.94);
}
.tool-card, .role-card, .comp-card, .blog-card {
  transition: transform .35s var(--spring), box-shadow .35s,
              border-color .25s, background-color .25s !important;
}
a { text-decoration:none; color:inherit }
button { font-family:inherit; cursor:pointer; border:none; background:none }
img { display:block; max-width:100%; height:auto }
svg { flex-shrink:0 }

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
html.light body::before {
  background-image:
    radial-gradient(ellipse 80% 60% at 20% -10%, rgba(37,99,235,.07) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 120%, rgba(139,92,246,.04) 0%, transparent 60%);
}
html.light #sitenav { border-bottom: 1px solid rgba(37,99,235,.18); }
html.light .tool-card, html.light .role-card,
html.light .comp-card, html.light .blog-card {
  box-shadow: 0 1px 12px rgba(37,99,235,.06), 0 0 0 1px rgba(37,99,235,.07);
}
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

/* Ticker */
.ticker {
  position:relative; z-index:10;
  background:var(--surf); border-bottom:1px solid var(--bdr);
  padding:8px 0; overflow:hidden; white-space:nowrap;
}
.ticker-track { display:inline-flex; animation:ticker-move 55s linear infinite; }
.ticker:hover .ticker-track { animation-play-state:paused }
.ticker-item {
  display:inline-flex; align-items:center; gap:0;
  font-family:var(--font-mono); font-size:.62rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--ink4); padding:0 18px;
}
.ticker-item.accent { color:var(--cyan); opacity:.9 }
.ticker-sep { color:var(--ink5); padding:0 4px; font-size:.5rem; }
@keyframes ticker-move { from{transform:translateX(0)} to{transform:translateX(-50%)} }

/* Nav */
.nav {
  position:sticky; top:0; z-index:200;
  background:var(--nav-bg);
  backdrop-filter:blur(24px) saturate(180%);
  -webkit-backdrop-filter:blur(24px) saturate(180%);
  border-bottom:1px solid var(--bdr);
  transition:box-shadow .3s, border-color .3s, background .3s;
}
.nav.scrolled { box-shadow:0 4px 32px rgba(0,0,0,.5); border-bottom-color:var(--bdr2); }
.nav-in {
  max-width:1440px; margin:0 auto; padding:0 40px;
  display:flex; align-items:center; height:60px; gap:8px;
}
.nav-logo {
  font-family:var(--font-display); font-size:.92rem; font-weight:700;
  letter-spacing:-.03em; color:var(--ink); flex-shrink:0; margin-right:20px;
  display:flex; align-items:center; gap:7px; transition:opacity .2s;
}
.nav-logo:hover { opacity:.75 }
.logo-icon {
  width:28px; height:28px; background:var(--cyan); border-radius:8px;
  display:flex; align-items:center; justify-content:center;
  font-size:.7rem; color:#060810; font-weight:800; letter-spacing:-.04em;
  flex-shrink:0; transition:transform .2s var(--spring), box-shadow .2s;
  box-shadow:var(--shc);
}
.nav-logo:hover .logo-icon { transform:scale(1.08); box-shadow:0 4px 24px rgba(79,156,249,.4); }
.logo-wordmark { color:var(--ink); font-weight:600 }
.logo-wordmark em { font-style:normal; color:var(--cyan) }

.nav-links { display:flex; align-items:center; gap:2px; flex:1; }
.nav-links > a, .nav-drop-btn {
  font-size:.84rem; font-weight:500; color:var(--ink3);
  padding:6px 12px; border-radius:var(--r2);
  transition:color .15s, background .15s;
  letter-spacing:-.01em; display:flex; align-items:center; gap:5px; white-space:nowrap;
}
.nav-links > a:hover, .nav-drop-btn:hover { color:var(--ink); background:var(--cyan-d) }
.nav-links > a.active { color:var(--cyan) }

.nav-drop { position:relative }
.drop-chevron {
  width:12px; height:12px; stroke:currentColor; fill:none; stroke-width:2;
  transition:transform .2s var(--ease);
}
.nav-drop.open .drop-chevron { transform:rotate(180deg) }
.drop-menu {
  display:none; position:absolute; top:calc(100% + 10px); left:0;
  background:var(--surf2); border:1px solid var(--bdr2);
  border-radius:var(--r3); padding:6px; min-width:210px;
  box-shadow:var(--sh3); z-index:300;
}
.nav-drop.open .drop-menu { display:block; animation:dropIn .18s var(--ease); }
@keyframes dropIn {
  from { opacity:0; transform:translateY(-8px) scale(.98) }
  to   { opacity:1; transform:translateY(0) scale(1) }
}
.drop-menu a {
  display:flex; align-items:center; gap:10px;
  padding:9px 12px; border-radius:var(--r2);
  font-size:.84rem; color:var(--ink3); transition:all .13s;
}
.drop-menu a:hover { background:var(--cyan-d); color:var(--ink) }
.drop-menu .dm-icon { font-size:1.05rem; flex-shrink:0 }

/* Search */
.nav-search { position:relative; display:flex; align-items:center }
.search-ico {
  position:absolute; left:11px; width:14px; height:14px;
  stroke:var(--ink4); fill:none; stroke-width:1.8;
  pointer-events:none; z-index:1;
}
.nav-search input {
  background:var(--surf); border:1px solid var(--bdr);
  border-radius:var(--rpill); padding:7px 14px 7px 34px;
  font-family:var(--font-mono); font-size:.75rem; color:var(--ink);
  width:180px; outline:none; transition:all .25s var(--ease); letter-spacing:.02em;
}
.nav-search input:focus {
  width:240px; border-color:var(--cyan);
  box-shadow:0 0 0 3px var(--cyan-d); background:var(--surf2);
}
.nav-search input::placeholder { color:var(--ink4) }

/* Nav right buttons */
.nav-right { display:flex; align-items:center; gap:6px; flex-shrink:0 }
.nav-icon-btn {
  width:36px; height:36px; border-radius:var(--r2);
  border:1px solid var(--bdr); background:var(--surf);
  display:flex; align-items:center; justify-content:center;
  transition:all .18s; flex-shrink:0;
}
.nav-icon-btn:hover { background:var(--cyan-d); border-color:var(--bdr2) }
.nav-icon-btn svg { width:15px; height:15px; stroke:var(--ink3); fill:none; stroke-width:1.8 }

/* Mobile theme toggle */
#mob-theme-btn {
  display:none;
  width:36px; height:36px; border-radius:var(--r2);
  border:1px solid var(--bdr); background:var(--surf);
  align-items:center; justify-content:center;
  transition:all .18s; flex-shrink:0;
}
#mob-theme-btn:hover { background:var(--cyan-d); border-color:var(--bdr2) }
#mob-theme-btn svg { width:15px; height:15px; stroke:var(--ink3); fill:none; stroke-width:1.8 }

/* Hamburger */
#hbg {
  display:none; flex-direction:column; justify-content:center;
  align-items:center; gap:5px; width:36px; height:36px;
  border:1px solid var(--bdr); border-radius:var(--r2);
  background:var(--surf); flex-shrink:0; cursor:pointer;
}
#hbg span {
  display:block; width:16px; height:1.5px;
  background:var(--ink); border-radius:2px;
  transition:all .25s var(--ease); transform-origin:center;
}
#hbg.open span:nth-child(1) { transform:translateY(6.5px) rotate(45deg) }
#hbg.open span:nth-child(2) { opacity:0; transform:scaleX(0) }
#hbg.open span:nth-child(3) { transform:translateY(-6.5px) rotate(-45deg) }

#mob {
  display:none; position:fixed; inset:0;
  background:var(--bg); z-index:210; overflow-y:auto;
  padding:72px 24px 48px;
  flex-direction:column; gap:0;
}
#mob.open { display:flex; animation:mobIn .28s var(--ease); }
@keyframes mobIn {
  from { opacity:0; transform:translateY(-12px) }
  to   { opacity:1; transform:translateY(0) }
}
.mob-section { padding:24px 0; border-bottom:1px solid var(--div) }
.mob-section:first-child { padding-top:0 }
.mob-primary-links { display:flex; flex-direction:column; gap:4px }
.mob-link {
  font-family:var(--font-display); font-size:2rem; font-weight:700;
  color:var(--ink); padding:8px 0; display:block; letter-spacing:-.04em;
  transition:color .15s, padding-left .2s var(--ease);
}
.mob-link:hover { color:var(--cyan); padding-left:8px }
.mob-sublabel {
  font-family:var(--font-mono); font-size:.58rem; letter-spacing:.2em;
  text-transform:uppercase; color:var(--cyan); margin-bottom:14px;
  display:flex; align-items:center; gap:8px;
}
.mob-sublabel::after { content:''; flex:1; height:1px; background:var(--bdr2) }
.mob-pills { display:flex; flex-wrap:wrap; gap:7px }
.mob-pill {
  background:var(--surf); border:1px solid var(--bdr);
  border-radius:var(--rpill); padding:8px 16px; font-size:.84rem;
  color:var(--ink3); transition:all .18s;
  display:inline-flex; align-items:center; gap:6px;
}
.mob-pill:hover { background:var(--cyan-d); border-color:var(--bdr2); color:var(--ink) }

/* Layout */
.page { max-width:1440px; margin:0 auto; padding:0 40px; position:relative; z-index:1; }
.page-narrow { max-width:720px; margin:0 auto; padding:0 40px; position:relative; z-index:1; }

/* Breadcrumbs */
.breadcrumb {
  display:flex; align-items:center; gap:8px;
  font-family:var(--font-mono); font-size:.68rem; color:var(--ink4);
  padding:clamp(28px,4vw,48px) 0 0; flex-wrap:wrap; letter-spacing:.02em;
}
.breadcrumb a { color:var(--ink3); transition:color .15s }
.breadcrumb a:hover { color:var(--cyan) }
.breadcrumb .sep { width:14px; height:14px; stroke:var(--ink5); fill:none; stroke-width:1.5; flex-shrink:0; }
.breadcrumb .current { color:var(--ink) }

/* Section headers */
.sec { padding:clamp(64px,8vw,96px) 0 0 }
.sec-top { display:flex; align-items:flex-end; justify-content:space-between; gap:20px; margin-bottom:32px; }
.sec-eyebrow {
  font-family:var(--font-mono); font-size:.65rem; letter-spacing:.16em;
  text-transform:uppercase; color:var(--cyan); margin-bottom:10px;
  display:flex; align-items:center; gap:8px;
}
.sec-eyebrow::before { content:''; width:20px; height:1px; background:var(--cyan); flex-shrink:0 }
.sec-h2 {
  font-family:var(--font-display); font-size:clamp(1.8rem,3vw,2.7rem);
  font-weight:700; letter-spacing:-.04em; color:var(--ink); line-height:1.05;
}
.sec-h2 em { font-style:normal; color:var(--cyan) }
.sec-link {
  font-family:var(--font-mono); font-size:.7rem; color:var(--cyan);
  display:flex; align-items:center; gap:5px; letter-spacing:.04em;
  text-transform:uppercase; transition:gap .2s; white-space:nowrap;
  flex-shrink:0; padding-bottom:1px; border-bottom:1px solid var(--cyan-g);
}
.sec-link:hover { gap:9px; border-bottom-color:var(--cyan) }

/* Hero */
.hero {
  padding:clamp(72px,10vw,128px) 0 clamp(56px,7vw,88px);
  display:grid; grid-template-columns:1fr 400px;
  gap:clamp(56px,8vw,100px); align-items:center; position:relative;
}
.hero-eyebrow {
  display:inline-flex; align-items:center; gap:9px; margin-bottom:24px;
  font-family:var(--font-mono); font-size:.65rem; font-weight:400;
  letter-spacing:.14em; text-transform:uppercase; color:var(--cyan);
}
.hero-eyebrow-dot {
  width:6px; height:6px; border-radius:50%; background:var(--cyan);
  animation:pulse 2.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }
.hero-h1 {
  font-family:var(--font-display); font-size:clamp(3rem,6.5vw,5.8rem);
  font-weight:800; line-height:.96; letter-spacing:-.05em; color:var(--ink); margin-bottom:24px;
}
.hero-h1 em { font-style:normal; color:var(--cyan) }
.hero-h1 .serif-accent {
  font-family:var(--font-serif); font-style:italic; font-weight:400;
  font-size:.92em; color:var(--ink2); display:block; margin-top:6px; letter-spacing:-.02em;
}
.hero-sub { font-size:1.02rem; line-height:1.8; color:var(--ink3); max-width:480px; margin-bottom:36px; font-weight:400; }
.role-selector { margin-bottom:36px }
.role-label { font-family:var(--font-mono); font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; color:var(--ink4); margin-bottom:12px; }
.role-chips { display:flex; flex-wrap:wrap; gap:8px }
.role-chip {
  display:inline-flex; align-items:center; gap:7px; background:var(--surf);
  border:1px solid var(--bdr); border-radius:var(--rpill); padding:8px 16px;
  font-size:.85rem; font-weight:500; color:var(--ink3); transition:all .2s var(--ease);
}
.role-chip:hover { background:var(--cyan-d); border-color:var(--bdr2); color:var(--ink); transform:translateY(-2px); box-shadow:var(--sh0); }
.chip-icon { font-size:.95rem }
.hero-ctas { display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:48px; }
.stats-row { display:flex; gap:36px; padding-top:36px; border-top:1px solid var(--div); flex-wrap:wrap; }
.stat-num { font-family:var(--font-display); font-size:2rem; font-weight:800; letter-spacing:-.05em; color:var(--ink); line-height:1; }
.stat-num em { font-style:normal; color:var(--cyan) }
.stat-lbl { font-family:var(--font-mono); font-size:.6rem; color:var(--ink4); letter-spacing:.1em; text-transform:uppercase; margin-top:5px; }

.hero-panel {
  background:var(--surf); border:1px solid var(--bdr2);
  border-radius:var(--r4); overflow:hidden; box-shadow:var(--sh2); position:relative;
}
.hero-panel::before {
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  background:linear-gradient(90deg, var(--cyan), var(--violet), var(--cyan));
  background-size:200% 100%; animation:shimmer 3s ease-in-out infinite;
}
@keyframes shimmer { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
.panel-hdr { padding:16px 20px; border-bottom:1px solid var(--div); display:flex; align-items:center; justify-content:space-between; }
.panel-title { font-family:var(--font-mono); font-size:.64rem; color:var(--ink3); letter-spacing:.1em; text-transform:uppercase; display:flex; align-items:center; gap:7px; }
.panel-title::before { content:''; width:14px; height:1px; background:var(--cyan) }
.panel-live {
  display:inline-flex; align-items:center; gap:5px; background:var(--green-d);
  border:1px solid var(--green-g); border-radius:var(--rpill); padding:3px 10px;
  font-family:var(--font-mono); font-size:.58rem; color:var(--green); letter-spacing:.08em; text-transform:uppercase;
}
.panel-live::before { content:''; width:5px; height:5px; border-radius:50%; background:var(--green); animation:blink 2s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1}50%{opacity:.25} }
.panel-list { padding:8px }
.ptool { display:flex; align-items:center; gap:14px; padding:10px 12px; border-radius:var(--r2); transition:background .15s; color:inherit; }
.ptool:hover { background:var(--bg3) }
.ptool-rank { font-family:var(--font-mono); font-size:.62rem; color:var(--ink5); width:18px; text-align:center; flex-shrink:0; font-weight:500; }
.ptool-info { flex:1; min-width:0 }
.ptool-name { font-family:var(--font-display); font-size:.9rem; font-weight:600; color:var(--ink2); letter-spacing:-.02em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.ptool-cat { font-family:var(--font-mono); font-size:.58rem; color:var(--ink4); letter-spacing:.06em; text-transform:uppercase; }
.ptool-score { font-family:var(--font-mono); font-size:.7rem; font-weight:600; padding:3px 10px; border-radius:var(--r1); flex-shrink:0; }
.ps-hi { background:var(--green-d); border:1px solid var(--green-g); color:var(--green) }
.ps-md { background:var(--cyan-d); border:1px solid var(--cyan-g); color:var(--cyan) }
.panel-footer {
  margin:8px; background:var(--bg3); border:1px solid var(--bdr);
  border-radius:var(--r2); padding:12px; font-family:var(--font-mono);
  font-size:.68rem; color:var(--cyan); text-align:center; letter-spacing:.06em;
  text-transform:uppercase; transition:all .18s; display:block;
}
.panel-footer:hover { background:var(--cyan-d); border-color:var(--bdr2) }

/* Affiliate strip */
.affil-strip { background:var(--surf); border-top:1px solid var(--bdr); border-bottom:1px solid var(--bdr); }
.affil-in {
  max-width:1440px; margin:0 auto; padding:10px 40px;
  display:flex; align-items:center; gap:9px;
  font-family:var(--font-mono); font-size:.67rem; color:var(--ink4); letter-spacing:.02em;
}
.affil-icon { width:13px; height:13px; stroke:var(--cyan); fill:none; stroke-width:2 }
.affil-in strong { color:var(--ink3); font-weight:500 }
.affil-in a { color:var(--cyan); transition:opacity .15s }
.affil-in a:hover { opacity:.7 }

/* Buttons */
.btn-primary {
  display:inline-flex; align-items:center; gap:8px;
  background:var(--cyan); color:#060810; padding:13px 24px;
  border-radius:var(--rpill); font-family:var(--font-mono); font-size:.78rem;
  font-weight:600; letter-spacing:.04em; text-transform:uppercase;
  border:none; transition:all .2s var(--ease); box-shadow:var(--shc); white-space:nowrap;
}
.btn-primary:hover { background:var(--cyan2); transform:translateY(-2px); box-shadow:0 8px 32px rgba(79,156,249,.4); }
.btn-primary svg { width:13px; height:13px; stroke:currentColor; fill:none; stroke-width:2.5 }
.btn-ghost {
  display:inline-flex; align-items:center; gap:8px;
  background:transparent; color:var(--ink2); padding:13px 22px;
  border-radius:var(--rpill); font-size:.9rem; font-weight:500;
  border:1px solid var(--bdr2); transition:all .18s; letter-spacing:-.01em; white-space:nowrap;
}
.btn-ghost:hover { background:var(--cyan-d); border-color:var(--bdr3); color:var(--cyan); }
.btn-try {
  display:flex; align-items:center; justify-content:center; gap:8px;
  background:var(--cyan); color:#060810; padding:12px 18px;
  border-radius:var(--r2); font-family:var(--font-mono); font-size:.74rem;
  font-weight:600; letter-spacing:.04em; text-transform:uppercase;
  border:none; transition:all .18s; box-shadow:var(--shc);
}
.btn-try:hover { background:var(--cyan2); transform:translateY(-1px); box-shadow:0 8px 28px rgba(79,156,249,.35); }
.btn-try svg { width:11px; height:11px; stroke:currentColor; fill:none; stroke-width:2.5 }
.btn-outline {
  display:block; text-align:center; padding:10px; border:1px solid var(--bdr);
  border-radius:var(--r2); font-family:var(--font-mono); font-size:.68rem;
  color:var(--ink4); letter-spacing:.04em; text-transform:uppercase; transition:all .18s;
}
.btn-outline:hover { color:var(--cyan); border-color:var(--bdr2); background:var(--cyan-d); }

/* Tool cards */
.tools-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(320px,1fr)); gap:16px; }
.tool-card {
  background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r4);
  overflow:hidden; display:flex; flex-direction:column; position:relative;
  transition:transform .35s var(--spring), box-shadow .35s, border-color .25s;
  will-change:transform;
}
.tool-card:hover { transform:translateY(-5px); box-shadow:var(--sh2); border-color:var(--bdr2); }
.tc-accent-bar { height:2px; background:linear-gradient(90deg, var(--cyan), transparent); opacity:0; transition:opacity .3s; flex-shrink:0; }
.tool-card:hover .tc-accent-bar { opacity:1 }
.tc-body { padding:20px 20px 0; flex:1; display:flex; flex-direction:column }
.tc-meta { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.tc-cat { font-family:var(--font-mono); font-size:.6rem; letter-spacing:.1em; text-transform:uppercase; color:var(--ink4); display:flex; align-items:center; gap:5px; }
.tc-cat::before { content:'//'; opacity:.5 }
.tc-score { border-radius:var(--r1); padding:3px 10px; font-family:var(--font-mono); font-size:.67rem; font-weight:600; }
.tc-name { font-family:var(--font-display); font-size:1.22rem; font-weight:700; letter-spacing:-.03em; color:var(--ink); display:block; margin-bottom:7px; transition:color .15s; line-height:1.2; }
.tc-name:hover { color:var(--cyan) }
.tc-tagline { font-size:.86rem; line-height:1.65; color:var(--ink3); margin-bottom:14px; flex:1; }
.tc-badges { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:16px }
.badge { display:inline-flex; align-items:center; gap:3px; border-radius:var(--rpill); padding:3px 10px; font-family:var(--font-mono); font-size:.59rem; letter-spacing:.06em; text-transform:uppercase; font-weight:500; }
.b-free  { background:var(--green-d); border:1px solid var(--green-g); color:var(--green) }
.b-trial { background:var(--cyan-d);  border:1px solid var(--cyan-g);  color:var(--cyan) }
.b-paid  { background:var(--amber-d); border:1px solid var(--amber-g); color:var(--amber) }
.b-top   { background:var(--rose-d);  border:1px solid var(--rose-g);  color:var(--rose) }
.tc-divider { height:1px; background:var(--div); margin:0 -20px 16px }
.tc-footer { padding:0 20px 18px; margin-top:auto }
.tc-pricing { display:flex; align-items:baseline; gap:8px; margin-bottom:12px; }
.tc-price { font-family:var(--font-display); font-size:1.1rem; font-weight:700; color:var(--ink); letter-spacing:-.03em; }
.tc-model { font-family:var(--font-mono); font-size:.62rem; color:var(--ink4); letter-spacing:.04em; text-transform:uppercase; }
.tc-btn-group { display:flex; flex-direction:column; gap:8px }

/* Role cards */
.roles-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(240px,1fr)); gap:14px; }
.role-card {
  background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3);
  padding:24px; display:flex; flex-direction:column; gap:11px;
  transition:transform .3s var(--spring), box-shadow .3s, border-color .25s;
  position:relative; overflow:hidden;
}
.role-card:hover { transform:translateY(-4px); box-shadow:var(--sh2); border-color:var(--bdr2); }
.rc-icon { font-size:2rem; line-height:1; display:block }
.rc-name { font-family:var(--font-display); font-size:1.05rem; font-weight:700; letter-spacing:-.03em; color:var(--ink); }
.rc-desc { font-size:.85rem; color:var(--ink3); line-height:1.65; flex:1; }
.rc-count { font-family:var(--font-mono); font-size:.62rem; color:var(--cyan); letter-spacing:.06em; text-transform:uppercase; display:flex; align-items:center; gap:5px; }
.rc-count::before { content:'→' }
.rc-arrow { font-family:var(--font-mono); font-size:.68rem; color:var(--cyan); display:inline-flex; align-items:center; gap:5px; letter-spacing:.04em; transition:gap .2s; border-bottom:1px solid var(--cyan-g); padding-bottom:2px; width:fit-content; }
.role-card:hover .rc-arrow { gap:9px; border-bottom-color:var(--cyan) }

/* Comparison cards */
.comp-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(360px,1fr)); gap:14px; }
.comp-card { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); padding:24px; display:flex; flex-direction:column; gap:14px; transition:transform .3s var(--spring), box-shadow .3s, border-color .25s; }
.comp-card:hover { transform:translateY(-3px); box-shadow:var(--sh2); border-color:var(--bdr2); }
.comp-vs { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.comp-tool-name { font-family:var(--font-display); font-size:1.05rem; font-weight:700; color:var(--ink); letter-spacing:-.03em; }
.comp-vs-tag { font-family:var(--font-mono); font-size:.58rem; color:var(--ink4); background:var(--bg3); border:1px solid var(--bdr); border-radius:var(--rpill); padding:3px 10px; letter-spacing:.1em; flex-shrink:0; }
.comp-desc { font-size:.87rem; color:var(--ink3); line-height:1.7; flex:1 }
.comp-link { font-family:var(--font-mono); font-size:.68rem; color:var(--amber); display:inline-flex; align-items:center; gap:5px; letter-spacing:.04em; text-transform:uppercase; border-bottom:1px solid var(--amber-g); padding-bottom:2px; width:fit-content; transition:gap .2s, border-color .2s; }
.comp-card:hover .comp-link { gap:9px; border-bottom-color:var(--amber) }

/* Blog cards */
.blog-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(320px,1fr)); gap:16px; }
.blog-card { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); overflow:hidden; display:flex; flex-direction:column; color:inherit; transition:transform .3s var(--spring), box-shadow .3s, border-color .25s; }
.blog-card:hover { transform:translateY(-4px); box-shadow:var(--sh2); border-color:var(--bdr2); }
.blog-card-accent { height:2px; background:linear-gradient(90deg, var(--amber), transparent); opacity:0; transition:opacity .3s; }
.blog-card:hover .blog-card-accent { opacity:1 }
.blog-card-body { padding:24px; flex:1; display:flex; flex-direction:column; gap:10px }
.blog-eyebrow { font-family:var(--font-mono); font-size:.62rem; color:var(--cyan); letter-spacing:.1em; text-transform:uppercase; display:flex; align-items:center; gap:6px; }
.blog-eyebrow::before { content:'//'; opacity:.6 }
.blog-title { font-family:var(--font-display); font-size:1.1rem; font-weight:700; line-height:1.3; letter-spacing:-.03em; color:var(--ink); flex:1; }
.blog-desc { font-size:.86rem; line-height:1.65; color:var(--ink3); }
.blog-link { font-family:var(--font-mono); font-size:.66rem; color:var(--amber); display:inline-flex; align-items:center; gap:5px; transition:gap .2s; letter-spacing:.04em; text-transform:uppercase; }
.blog-card:hover .blog-link { gap:9px }

/* Newsletter / Email Section */
.email-sec {
  position:relative; z-index:1;
  background:var(--surf);
  border-top:1px solid var(--bdr); border-bottom:1px solid var(--bdr);
  padding:clamp(36px,5vw,56px) 0;
  overflow:hidden;
}
.email-inner {
  max-width:1440px; margin:0 auto; padding:0 40px;
  display:flex; align-items:center; gap:clamp(24px,5vw,64px);
  flex-wrap:wrap; justify-content:space-between;
}
.email-left { flex:1; min-width:260px; max-width:520px; }
.email-eyebrow {
  font-family:var(--font-mono); font-size:.62rem; letter-spacing:.16em;
  text-transform:uppercase; color:var(--amber); margin-bottom:10px;
  display:flex; align-items:center; gap:8px;
}
.email-eyebrow::before { content:''; width:16px; height:1px; background:var(--amber) }
.email-h2 {
  font-family:var(--font-display); font-size:clamp(1.4rem,2.5vw,1.9rem);
  font-weight:700; letter-spacing:-.04em; color:var(--ink); margin-bottom:8px; line-height:1.1;
}
.email-h2 em { font-style:normal; color:var(--amber) }
.email-sub { font-size:.88rem; line-height:1.65; color:var(--ink3); margin-bottom:0; }
.email-right { display:flex; align-items:center; gap:8px; flex-wrap:wrap; flex-shrink:0; }
.email-input {
  background:var(--bg); border:1px solid var(--bdr2); border-radius:var(--r2);
  padding:12px 16px; color:var(--ink); font-family:var(--font-body); font-size:.88rem;
  outline:none; transition:border-color .2s, box-shadow .2s; width:220px;
}
.email-input:focus { border-color:var(--amber); box-shadow:0 0 0 3px var(--amber-d); }
.email-input::placeholder { color:var(--ink4) }
.btn-email {
  background:var(--amber); color:#060810; border:none; border-radius:var(--r2);
  padding:12px 20px; font-family:var(--font-mono); font-size:.76rem; font-weight:600;
  letter-spacing:.04em; text-transform:uppercase; transition:all .18s;
  box-shadow:var(--sha); white-space:nowrap;
}
.btn-email:hover { background:var(--amber2); transform:translateY(-1px); box-shadow:0 8px 28px rgba(240,164,41,.35); }
.email-notice {
  font-family:var(--font-mono); font-size:.58rem; color:var(--ink5);
  margin-top:8px; letter-spacing:.02em; width:100%;
}

/* Role detail */
.rd-intro { padding:clamp(56px,7vw,88px) 0 0 }
.rd-icon { font-size:2.8rem; margin-bottom:16px; display:block }
.rd-h1 { font-family:var(--font-display); font-size:clamp(2.4rem,5vw,4.2rem); font-weight:800; letter-spacing:-.05em; color:var(--ink); margin-bottom:14px; line-height:1; }
.rd-h1 em { font-style:normal; color:var(--cyan) }
.rd-sub { font-size:1.02rem; line-height:1.78; color:var(--ink3); max-width:560px; margin-bottom:32px; }
.insight-box { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); padding:24px 26px; margin-bottom:20px; }
.insight-box.pain { background:rgba(244,63,94,.03); border-color:rgba(244,63,94,.1); }
.insight-box.solution { background:var(--cyan-d); border-color:var(--cyan-g); }
.insight-label { font-family:var(--font-mono); font-size:.62rem; color:var(--ink4); letter-spacing:.14em; text-transform:uppercase; margin-bottom:14px; }
.insight-box.pain .insight-label { color:var(--rose) }
.insight-box.solution .insight-label { color:var(--cyan) }
.pain-list { display:flex; flex-direction:column; gap:9px }
.pain-item { display:flex; align-items:flex-start; gap:10px; font-size:.89rem; color:var(--ink3); line-height:1.6; }
.pain-x { color:var(--rose); flex-shrink:0; font-weight:700; font-size:.8rem; margin-top:3px; }
.solution-text { font-size:.94rem; color:var(--ink2); line-height:1.78 }
.top-pick-bar { background:var(--surf); border:1px solid var(--bdr2); border-radius:var(--r3); padding:22px 24px; margin-bottom:18px; display:flex; align-items:center; gap:18px; flex-wrap:wrap; }
.top-pick-badge { font-family:var(--font-mono); font-size:.62rem; background:var(--green-d); border:1px solid var(--green-g); color:var(--green); border-radius:var(--rpill); padding:4px 12px; letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; flex-shrink:0; }
.top-pick-info { flex:1; min-width:0 }
.top-pick-name { font-family:var(--font-display); font-size:1.2rem; font-weight:700; color:var(--ink); letter-spacing:-.03em; }
.top-pick-tagline { font-size:.86rem; color:var(--ink3); margin-top:3px }
.top-pick-score { font-family:var(--font-display); font-size:2.2rem; font-weight:800; letter-spacing:-.06em; flex-shrink:0; }

/* Tool detail */
.td-wrapper { padding:clamp(48px,6vw,80px) 0 0 }
.td-header { background:var(--surf); border:1px solid var(--bdr2); border-radius:var(--r4); padding:36px; margin-bottom:24px; position:relative; overflow:hidden; box-shadow:var(--sh1); }
.td-header::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg, var(--cyan), var(--violet), var(--amber)); }
.td-header-grid { display:grid; grid-template-columns:1fr auto; gap:32px; align-items:start; }
.td-eyebrow { font-family:var(--font-mono); font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; color:var(--cyan); margin-bottom:10px; display:flex; align-items:center; gap:6px; }
.td-eyebrow::before { content:'//'; opacity:.6 }
.td-h1 { font-family:var(--font-display); font-size:clamp(2.2rem,4.5vw,3.6rem); font-weight:800; letter-spacing:-.05em; color:var(--ink); line-height:1; margin-bottom:10px; }
.td-tagline { font-size:1rem; color:var(--ink3); line-height:1.7; margin-bottom:20px }
.td-meta-row { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
.td-score-block { text-align:right; flex-shrink:0 }
.td-score-num { font-family:var(--font-display); font-size:3.8rem; font-weight:800; letter-spacing:-.06em; line-height:1; }
.td-score-label { font-family:var(--font-mono); font-size:.64rem; letter-spacing:.08em; text-transform:uppercase; margin-top:3px; }
.td-score-sub { font-family:var(--font-mono); font-size:.58rem; color:var(--ink4); letter-spacing:.08em; text-transform:uppercase; margin-top:2px; }
.td-layout { display:grid; grid-template-columns:1fr 280px; gap:20px; align-items:start; }
.td-panel { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); padding:24px; margin-bottom:16px; box-shadow:var(--sh0); }
.panel-label { font-family:var(--font-mono); font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; color:var(--cyan); margin-bottom:16px; display:flex; align-items:center; gap:6px; }
.panel-label::before { content:'//'; opacity:.5 }
.verdict-text { font-size:.96rem; line-height:1.85; color:var(--ink2) }
.pros-cons-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px }
.plist { list-style:none; display:flex; flex-direction:column; gap:9px }
.plist li { font-size:.87rem; line-height:1.6; color:var(--ink3); padding-left:20px; position:relative; }
.plist.pros li::before { content:'✓'; position:absolute; left:0; color:var(--green); font-weight:700; }
.plist.cons li::before { content:'✗'; position:absolute; left:0; color:var(--rose); font-weight:700; }
.best-for-list { display:flex; flex-direction:column; gap:8px }
.best-for-item { display:flex; align-items:center; gap:9px; font-size:.88rem; color:var(--ink3); }
.best-for-item::before { content:'→'; color:var(--cyan); font-family:var(--font-mono); font-size:.7rem; flex-shrink:0; }
.price-box { background:var(--bg3); border:1px solid var(--bdr); border-radius:var(--r2); padding:20px; margin-bottom:14px; }
.price-from { font-family:var(--font-mono); font-size:.6rem; color:var(--ink4); letter-spacing:.1em; text-transform:uppercase; margin-bottom:8px; }
.price-value { font-family:var(--font-display); font-size:2rem; font-weight:800; color:var(--ink); letter-spacing:-.04em; line-height:1; }
.price-period { font-family:var(--font-mono); font-size:.64rem; color:var(--ink4); letter-spacing:.06em; text-transform:uppercase; margin-top:5px; }
.btn-td-cta { display:flex; align-items:center; justify-content:center; gap:10px; width:100%; background:var(--cyan); color:#060810; padding:16px 24px; border-radius:var(--r2); font-family:var(--font-mono); font-size:.8rem; font-weight:600; letter-spacing:.04em; text-transform:uppercase; border:none; transition:all .2s; box-shadow:var(--shc); margin-bottom:10px; }
.btn-td-cta:hover { background:var(--cyan2); transform:translateY(-2px); box-shadow:0 10px 36px rgba(79,156,249,.4); }
.btn-td-cta svg { width:13px; height:13px; stroke:currentColor; fill:none; stroke-width:2.5 }
.trust-items { display:flex; flex-direction:column; gap:8px; margin-top:14px }
.trust-item { display:flex; align-items:center; gap:8px; font-family:var(--font-mono); font-size:.64rem; color:var(--ink4); }
.trust-item svg { width:13px; height:13px; stroke:var(--green); fill:none; stroke-width:2; flex-shrink:0; }

/* Compare detail */
.comp-detail-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:24px }
.cd-card { background:var(--surf); border:1px solid var(--bdr2); border-radius:var(--r3); padding:26px; position:relative; overflow:hidden; }
.cd-card.winner { border-color:var(--green-g); box-shadow:0 0 0 1px var(--green-g), var(--shg); }
.cd-card.winner::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:var(--green); }
.cd-winner-tag { position:absolute; top:16px; right:16px; background:var(--green-d); border:1px solid var(--green-g); border-radius:var(--rpill); padding:3px 11px; font-family:var(--font-mono); font-size:.58rem; color:var(--green); letter-spacing:.08em; text-transform:uppercase; }
.cd-name { font-family:var(--font-display); font-size:1.5rem; font-weight:800; color:var(--ink); letter-spacing:-.04em; margin-bottom:6px; }
.cd-score { font-family:var(--font-display); font-size:2.6rem; font-weight:800; letter-spacing:-.06em; line-height:1; margin-bottom:8px; }
.cd-tagline { font-size:.88rem; color:var(--ink3); line-height:1.65; margin-bottom:16px; }
.comp-table { width:100%; border-collapse:collapse; margin-bottom:16px; }
.comp-table td { padding:10px 0; border-bottom:1px solid var(--div); font-size:.87rem; color:var(--ink3); vertical-align:middle; }
.comp-table td:first-child { color:var(--ink4); font-family:var(--font-mono); font-size:.68rem; letter-spacing:.04em; text-transform:uppercase; width:40%; }
.comp-table tr:last-child td { border-bottom:none }
.tick { color:var(--green) }
.cross { color:var(--rose) }
.cd-verdict { font-size:.9rem; color:var(--ink3); line-height:1.72 }
.winner-block { background:var(--green-d); border:1px solid var(--green-g); border-radius:var(--r3); padding:20px 24px; margin-bottom:24px; }
.winner-label { font-family:var(--font-mono); font-size:.64rem; color:var(--green); letter-spacing:.12em; text-transform:uppercase; margin-bottom:10px; }
.winner-text { font-size:.92rem; color:var(--ink2); line-height:1.75 }

/* Prose */
.prose { font-size:.97rem; line-height:1.9; color:var(--ink3); }
.prose h2 { font-family:var(--font-display); font-size:1.75rem; font-weight:700; color:var(--ink); margin:56px 0 16px; letter-spacing:-.04em; padding-bottom:14px; border-bottom:1px solid var(--div); line-height:1.15; }
.prose h3 { font-family:var(--font-display); font-size:1.25rem; font-weight:700; color:var(--ink); margin:36px 0 12px; letter-spacing:-.03em; }
.prose p { margin-bottom:20px }
.prose a { color:var(--cyan); border-bottom:1px solid var(--cyan-g); transition:border-color .15s }
.prose a:hover { border-color:var(--cyan) }
.prose strong { color:var(--ink2); font-weight:600 }
.prose ul, .prose ol { margin:0 0 24px; padding:0; list-style:none }
.prose li { padding-left:22px; position:relative; margin-bottom:10px; line-height:1.75 }
.prose ul li::before { content:'▸'; position:absolute; left:0; top:5px; font-size:.65rem; color:var(--cyan); }
.prose ol { counter-reset:ol }
.prose ol li { counter-increment:ol }
.prose ol li::before { content:counter(ol, decimal-leading-zero); position:absolute; left:0; top:4px; font-family:var(--font-mono); font-size:.62rem; color:var(--cyan); }
.prose blockquote { border-left:3px solid var(--cyan); padding:16px 24px; margin:28px 0; background:var(--cyan-d); border-radius:0 var(--r2) var(--r2) 0; font-style:italic; color:var(--ink2); }

/* Legal */
.legal-wrap { max-width:740px; margin:56px auto 96px; padding:0 40px; position:relative; z-index:1; }
.legal-wrap h1 { font-family:var(--font-display); font-size:2.4rem; font-weight:800; letter-spacing:-.05em; color:var(--ink); margin-bottom:28px; }
.legal-wrap h2 { font-family:var(--font-display); font-size:1.5rem; font-weight:700; color:var(--ink); margin:40px 0 12px; letter-spacing:-.04em; }
.legal-wrap p { font-size:.93rem; line-height:1.82; color:var(--ink3); margin-bottom:14px }
.legal-note { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); padding:22px 26px; margin-bottom:28px; }

/* Pagination */
.pager { display:flex; justify-content:center; align-items:center; gap:10px; padding:56px 0; }
.pager a { background:var(--surf); border:1px solid var(--bdr); color:var(--ink3); padding:10px 22px; border-radius:var(--rpill); font-family:var(--font-mono); font-size:.72rem; transition:all .18s; letter-spacing:.04em; text-transform:uppercase; }
.pager a:hover { background:var(--cyan); color:#060810; border-color:var(--cyan); box-shadow:var(--shc); transform:translateY(-1px); }

/* Search overlay */
#sov { display:none; position:fixed; inset:0; background:rgba(6,8,16,.92); backdrop-filter:blur(20px); z-index:500; padding:72px 20px; overflow-y:auto; }
#sov.open { display:block; animation:fadeIn .18s ease }
@keyframes fadeIn { from{opacity:0}to{opacity:1} }
.sov-panel { max-width:960px; margin:0 auto; background:var(--surf); border:1px solid var(--bdr2); border-radius:var(--r4); padding:28px; box-shadow:var(--sh3); animation:panelIn .22s var(--ease); }
@keyframes panelIn { from{opacity:0;transform:translateY(14px) scale(.99)} to{opacity:1;transform:none} }
.sov-hdr { display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
.sov-title { font-family:var(--font-display); font-size:1.3rem; font-weight:700; color:var(--ink); letter-spacing:-.04em; }
.sov-close { width:34px; height:34px; border-radius:var(--r2); border:1px solid var(--bdr); background:var(--surf2); display:flex; align-items:center; justify-content:center; font-size:1rem; color:var(--ink3); transition:all .18s; }
.sov-close:hover { background:var(--rose-d); color:var(--rose) }
.sov-count { font-family:var(--font-mono); font-size:.68rem; color:var(--ink4); margin-bottom:20px; letter-spacing:.04em; }
.sov-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(240px,1fr)); gap:12px }
.sov-empty { text-align:center; padding:52px; font-family:var(--font-mono); font-size:.74rem; color:var(--ink4); letter-spacing:.06em; }

/* Cookie bar */
#ckbar { display:none; position:fixed; bottom:20px; left:50%; transform:translateX(-50%); background:var(--surf2); border:1px solid var(--bdr2); border-radius:var(--r3); padding:16px 22px; box-shadow:var(--sh3); z-index:1000; max-width:560px; width:calc(100% - 32px); align-items:center; gap:16px; flex-wrap:wrap; }
#ckbar.show { display:flex; animation:ckpop .28s var(--ease) }
@keyframes ckpop { from{opacity:0;transform:translateX(-50%) translateY(16px)} to{opacity:1;transform:translateX(-50%) translateY(0)} }
.ck-text { flex:1; min-width:180px; font-family:var(--font-mono); font-size:.68rem; color:var(--ink4); line-height:1.6; }
.ck-text a { color:var(--cyan) }
.ck-btns { display:flex; gap:7px; flex-shrink:0 }
.ck-accept { background:var(--cyan); color:#060810; border:none; border-radius:var(--r1); padding:9px 18px; font-family:var(--font-mono); font-size:.72rem; font-weight:600; letter-spacing:.04em; transition:background .18s; }
.ck-accept:hover { background:var(--cyan2) }
.ck-decline { background:transparent; color:var(--ink4); border:1px solid var(--bdr); border-radius:var(--r1); padding:9px 14px; font-family:var(--font-mono); font-size:.68rem; transition:all .18s; }
.ck-decline:hover { border-color:var(--bdr2); color:var(--ink) }

/* Footer */
.footer { background:var(--surf); border-top:1px solid var(--bdr); position:relative; z-index:1; margin-top:100px; }
.footer::before { content:''; position:absolute; top:-1px; left:0; right:0; height:1px; background:linear-gradient(90deg, transparent, var(--cyan), var(--violet), var(--amber), transparent); opacity:.35; }
.footer-in { max-width:1440px; margin:0 auto; padding:56px 40px 40px; }
.footer-top { display:grid; grid-template-columns:2fr 1fr 1fr 1fr; gap:48px; margin-bottom:40px; }
.f-logo { font-family:var(--font-display); font-size:1.05rem; font-weight:700; letter-spacing:-.03em; color:var(--ink); display:flex; align-items:center; gap:8px; margin-bottom:13px; }
.f-logo-icon { width:26px; height:26px; background:var(--cyan); border-radius:7px; display:flex; align-items:center; justify-content:center; font-size:.65rem; color:#060810; font-weight:800; letter-spacing:-.04em; flex-shrink:0; }
.f-desc { font-size:.86rem; line-height:1.78; color:var(--ink4); max-width:280px; }
.f-affil { margin-top:18px; font-family:var(--font-mono); font-size:.6rem; letter-spacing:.12em; text-transform:uppercase; color:var(--amber); display:flex; align-items:center; gap:7px; }
.f-affil::before { content:''; width:14px; height:1px; background:var(--amber) }
.f-col-title { font-family:var(--font-mono); font-size:.6rem; letter-spacing:.18em; text-transform:uppercase; color:var(--ink4); margin-bottom:14px; }
.f-col a { display:block; font-size:.86rem; color:var(--ink4); margin-bottom:9px; transition:color .15s, padding-left .2s var(--ease); }
.f-col a:hover { color:var(--cyan); padding-left:4px }
.footer-divider { height:1px; background:var(--div); margin-bottom:22px }
.footer-bottom { display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; }
.f-copy { font-family:var(--font-mono); font-size:.64rem; color:var(--ink4); line-height:1.65; }
.f-disclaimer { font-family:var(--font-mono); font-size:.6rem; color:var(--ink5); font-style:italic; }

/* Reveal animations */
.rv { opacity:1; transform:none; transition:opacity .55s var(--ease), transform .55s var(--ease); }
body.rv-ready .rv { opacity:0; transform:translateY(20px); }
body.rv-ready .rv.visible { opacity:1; transform:translateY(0); }
@media (prefers-reduced-motion: reduce) {
  body.rv-ready .rv, body.rv-ready .rv.visible { opacity:1; transform:none; transition:none }
}

/* Responsive */
@media (max-width:1200px) {
  .hero { grid-template-columns:1fr }
  .hero-panel { display:none }
  .td-layout { grid-template-columns:1fr }
  .footer-top { grid-template-columns:1fr 1fr; gap:32px }
  .comp-detail-grid { grid-template-columns:1fr }
  .email-inner { flex-direction:column; align-items:flex-start; }
  .email-right { width:100% }
  .pros-cons-grid { grid-template-columns:1fr }
}
@media (max-width:768px) {
  .nav-in { padding:0 20px; height:56px }
  .nav-links, .nav-search { display:none }
  #theme-btn { display:none; }
  #mob-theme-btn { display:flex; }
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
  .email-right { flex-direction:column; width:100% }
  .email-input { width:100% }
  .btn-email { width:100%; text-align:center; justify-content:center; }
}

/* Scrollbar */
::-webkit-scrollbar { width:4px }
::-webkit-scrollbar-track { background:transparent }
::-webkit-scrollbar-thumb { background:var(--bdr3); border-radius:2px }
::-webkit-scrollbar-thumb:hover { background:var(--cyan) }
::selection { background:var(--cyan-d); color:var(--cyan2) }
:focus-visible { outline:2px solid var(--cyan); outline-offset:2px; border-radius:var(--r1); }

/* ═══════════════════════════════════════════════════════════════
   TOOL REVIEW PAGE v2 — Quick Verdict, Pricing, FAQ, Alternatives
   ═══════════════════════════════════════════════════════════════ */

.verdict-box {
  background:var(--surf); border:1px solid var(--bdr2); border-radius:var(--r4);
  padding:32px 36px; margin-bottom:24px; position:relative; overflow:hidden; box-shadow:var(--sh1);
}
.verdict-box::before {
  content:''; position:absolute; top:0; left:0; right:0; height:3px;
  background:linear-gradient(90deg, var(--green), var(--cyan), var(--violet));
}
.verdict-box-grid { display:grid; grid-template-columns:auto 1fr auto; gap:28px; align-items:center; }
.vb-score-ring {
  width:100px; height:100px; border-radius:50%;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  flex-shrink:0; position:relative;
}
.vb-score-ring::before { content:''; position:absolute; inset:0; border-radius:50%; border:3px solid var(--bdr); }
.vb-score-ring::after {
  content:''; position:absolute; inset:0; border-radius:50%;
  border:3px solid transparent; border-top-color:currentColor; border-right-color:currentColor;
  transform:rotate(-45deg);
}
.vb-score-num { font-family:var(--font-display); font-size:2.4rem; font-weight:800; letter-spacing:-.06em; line-height:1; }
.vb-score-max { font-family:var(--font-mono); font-size:.58rem; color:var(--ink4); letter-spacing:.06em; margin-top:2px; }
.vb-content { min-width:0 }
.vb-label { font-family:var(--font-mono); font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; color:var(--cyan); margin-bottom:8px; display:flex; align-items:center; gap:6px; }
.vb-label::before { content:'//'; opacity:.5 }
.vb-verdict { font-family:var(--font-display); font-size:1.15rem; font-weight:600; color:var(--ink); line-height:1.5; margin-bottom:14px; letter-spacing:-.02em; }
.vb-meta-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px 20px; }
.vb-meta-item { display:flex; align-items:center; gap:8px; font-size:.84rem; color:var(--ink3); line-height:1.5; }
.vb-meta-label { font-family:var(--font-mono); font-size:.62rem; color:var(--ink4); letter-spacing:.06em; text-transform:uppercase; flex-shrink:0; min-width:72px; }
.vb-meta-value { color:var(--ink2); font-weight:500 }
.vb-cta-col { display:flex; flex-direction:column; align-items:stretch; gap:10px; flex-shrink:0; min-width:180px; }

.pc-grid {
  display:grid; grid-template-columns:1fr 1fr; gap:0;
  background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3);
  overflow:hidden; margin-bottom:24px; box-shadow:var(--sh0);
}
.pc-col { padding:24px 28px }
.pc-col + .pc-col { border-left:1px solid var(--div) }
.pc-col-title { font-family:var(--font-mono); font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; margin-bottom:16px; display:flex; align-items:center; gap:8px; }
.pc-col-title.pro-title { color:var(--green) }
.pc-col-title.con-title { color:var(--rose) }
.pc-col-title::before { content:''; width:14px; height:1px; background:currentColor }

.pricing-section { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); overflow:hidden; margin-bottom:24px; box-shadow:var(--sh0); }
.pricing-section-hdr { padding:20px 28px; border-bottom:1px solid var(--div); display:flex; align-items:center; justify-content:space-between; }
.pricing-table { width:100%; border-collapse:collapse; }
.pricing-table th { text-align:left; padding:12px 20px; font-family:var(--font-mono); font-size:.62rem; letter-spacing:.1em; text-transform:uppercase; color:var(--ink4); background:var(--bg3); border-bottom:1px solid var(--div); font-weight:500; }
.pricing-table td { padding:14px 20px; font-size:.88rem; color:var(--ink3); border-bottom:1px solid var(--div); vertical-align:top; }
.pricing-table tr:last-child td { border-bottom:none }
.pricing-table td:first-child { font-weight:600; color:var(--ink); white-space:nowrap; }
.pricing-verified { font-family:var(--font-mono); font-size:.58rem; color:var(--ink5); letter-spacing:.04em; display:flex; align-items:center; gap:6px; }
.pricing-verified::before { content:''; width:5px; height:5px; border-radius:50%; background:var(--green); flex-shrink:0; }

.who-section { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); padding:28px; margin-bottom:24px; box-shadow:var(--sh0); }
.who-grid { display:grid; grid-template-columns:1fr 1fr; gap:24px; }
.who-list { list-style:none; display:flex; flex-direction:column; gap:10px }
.who-list li { font-size:.88rem; line-height:1.65; color:var(--ink3); padding-left:22px; position:relative; }
.who-list.who-yes li::before { content:'✓'; position:absolute; left:0; color:var(--green); font-weight:700; }
.who-list.who-no li::before { content:'→'; position:absolute; left:0; color:var(--amber); font-family:var(--font-mono); font-size:.72rem; }

.faq-section { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); overflow:hidden; margin-bottom:24px; box-shadow:var(--sh0); }
.faq-section-hdr { padding:20px 28px; border-bottom:1px solid var(--div); }
.faq-item { border-bottom:1px solid var(--div); }
.faq-item:last-child { border-bottom:none }
.faq-q { width:100%; text-align:left; padding:18px 28px; font-family:var(--font-display); font-size:1rem; font-weight:600; color:var(--ink); letter-spacing:-.02em; display:flex; align-items:center; justify-content:space-between; gap:16px; cursor:pointer; background:none; border:none; transition:background .15s, color .15s; }
.faq-q:hover { background:var(--cyan-d) }
.faq-chevron { width:18px; height:18px; stroke:var(--ink4); fill:none; stroke-width:2; flex-shrink:0; transition:transform .25s var(--ease); }
.faq-item.open .faq-chevron { transform:rotate(180deg) }
.faq-a { display:none; padding:0 28px 20px; font-size:.9rem; line-height:1.78; color:var(--ink3); }
.faq-item.open .faq-a { display:block }

.alts-section { background:var(--surf); border:1px solid var(--bdr); border-radius:var(--r3); padding:28px; margin-bottom:24px; box-shadow:var(--sh0); }
.alt-card { display:flex; align-items:center; gap:16px; padding:16px 0; border-bottom:1px solid var(--div); }
.alt-card:last-child { border-bottom:none }
.alt-card:first-child { padding-top:0 }
.alt-info { flex:1; min-width:0 }
.alt-name { font-family:var(--font-display); font-size:1rem; font-weight:700; color:var(--ink); letter-spacing:-.02em; }
.alt-desc { font-size:.84rem; color:var(--ink3); margin-top:3px; line-height:1.6; }
.alt-links { display:flex; align-items:center; gap:10px; flex-shrink:0; }
.alt-link { font-family:var(--font-mono); font-size:.66rem; letter-spacing:.04em; text-transform:uppercase; padding:6px 12px; border-radius:var(--r1); border:1px solid var(--bdr); color:var(--ink3); transition:all .18s; white-space:nowrap; }
.alt-link:hover { background:var(--cyan-d); border-color:var(--bdr2); color:var(--cyan); }
.alt-score { font-family:var(--font-mono); font-size:.72rem; font-weight:600; padding:4px 10px; border-radius:var(--r1); flex-shrink:0; }

.bottom-cta { background:var(--surf); border:1px solid var(--bdr2); border-radius:var(--r3); padding:28px 32px; margin-bottom:24px; display:flex; align-items:center; justify-content:space-between; gap:20px; flex-wrap:wrap; box-shadow:var(--sh1); }
.bottom-cta-text { flex:1; min-width:200px; }
.bottom-cta-name { font-family:var(--font-display); font-size:1.2rem; font-weight:700; color:var(--ink); letter-spacing:-.03em; }
.bottom-cta-sub { font-size:.86rem; color:var(--ink3); margin-top:4px; }

.review-section-hdr { font-family:var(--font-mono); font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; color:var(--cyan); margin-bottom:16px; display:flex; align-items:center; gap:6px; }
.review-section-hdr::before { content:'//'; opacity:.5 }

@media (max-width:768px) {
  .verdict-box { padding:24px 20px }
  .verdict-box-grid { grid-template-columns:1fr; gap:20px; text-align:center; }
  .vb-score-ring { margin:0 auto }
  .vb-meta-grid { grid-template-columns:1fr; text-align:left }
  .vb-cta-col { min-width:100% }
  .pc-grid { grid-template-columns:1fr }
  .pc-col + .pc-col { border-left:none; border-top:1px solid var(--div) }
  .who-grid { grid-template-columns:1fr }
  .alt-card { flex-direction:column; align-items:flex-start }
  .alt-links { width:100% }
  .bottom-cta { flex-direction:column; text-align:center }
}
@media (max-width:520px) {
  .vb-meta-grid { grid-template-columns:1fr }
}
""" + TOOL_FINDER_CSS



# ═══════════════════════════════════════════════════════════════════════════════
# BASE HTML TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════
BASE = """<!DOCTYPE html>
<html lang="en" class="">
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
<meta property="og:type" content="{{ og_type }}">
<meta property="og:url" content="{{ canon }}">
<meta property="og:site_name" content="Moving Forward With AI">
<meta property="og:locale" content="en_GB">
<meta property="og:image" content="{{ og_image }}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ title }}">
<meta name="twitter:description" content="{{ desc[:200] }}">
<meta name="twitter:image" content="{{ og_image }}">
<meta name="theme-color" content="#060810">
<script type="application/ld+json">{{ ws_schema|safe }}</script>
{% if bcs %}<script type="application/ld+json">{{ bcs|safe }}</script>{% endif %}
{% if schema %}<script type="application/ld+json">{{ schema|safe }}</script>{% endif %}
{% if schema2 %}<script type="application/ld+json">{{ schema2|safe }}</script>{% endif %}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700;800;900&family=Geist+Mono:wght@300;400;500;600&display=swap">
<script>
(function(){
  try {
    var saved = localStorage.getItem('mfwai-theme');
    var preferLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    var isLight = saved === 'light' || (saved === null && preferLight);
    if (isLight) { document.documentElement.classList.add('light'); }
  } catch(e) {}
})();
</script>
<style>{{ css|safe }}</style>
<meta name="google-site-verification" content="U4OV71VLG-_zLDoFNbwH9ghMzxs-fQEPOkrKresvHOU" />
<script async src="https://www.googletagmanager.com/gtag/js?id=G-TBH27VXH8M"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-TBH27VXH8M');
</script>
</head>
<body>

<div class="ticker" aria-hidden="true" role="presentation">
  <div class="ticker-track">
    {% for _ in range(2) %}
    <span class="ticker-item">Independent AI Reviews</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item accent">Freelancers</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item">Marketers</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item accent">SEO Professionals</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item">Content Creators</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item accent">Small Business Owners</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item">Freelance Writers</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item accent">Compare AI Tools</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item">AI Tool Guides</span>
    <span class="ticker-sep">◆</span>
    <span class="ticker-item accent">Moving Forward With AI</span>
    <span class="ticker-sep">◆</span>
    {% endfor %}
  </div>
</div>

<header class="nav" id="sitenav" role="banner">
  <div class="nav-in">
    <a href="/" class="nav-logo" aria-label="Moving Forward With AI — Home">
      <div class="logo-icon" aria-hidden="true">AI</div>
      <div class="logo-wordmark">Moving Forward <em>With AI</em></div>
    </a>

    <nav class="nav-links" aria-label="Primary navigation">
      <a href="/">Home</a>
      <a href="/tool-finder">Tool Finder</a>
      <a href="/tools">All Tools</a>
      <div class="nav-drop" id="drop-compare">
        <button class="nav-drop-btn" type="button" aria-expanded="false" aria-haspopup="true" id="btn-drop-compare">
          Compare
          <svg class="drop-chevron" viewBox="0 0 12 12" aria-hidden="true"><path d="M2 4l4 4 4-4"/></svg>
        </button>
        <div class="drop-menu" id="menu-drop-compare" role="menu">
          <a href="/compare" role="menuitem">
            <span class="dm-icon" aria-hidden="true">⚔️</span>All Comparisons
          </a>
          <a href="/compare/custom" role="menuitem">
            <span class="dm-icon" aria-hidden="true">🔀</span>Custom Compare →
          </a>
        </div>
      </div>
      <a href="/blog">Guides</a>
      <div class="nav-drop" id="drop-roles">
        <button class="nav-drop-btn" type="button" aria-expanded="false" aria-haspopup="true" id="btn-drop-roles">
          Who it's for
          <svg class="drop-chevron" viewBox="0 0 12 12" aria-hidden="true"><path d="M2 4l4 4 4-4"/></svg>
        </button>
        <div class="drop-menu" id="menu-drop-roles" role="menu">
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
        <svg id="ico-moon" viewBox="0 0 24 24" aria-hidden="true" style="display:none">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>
      <button id="mob-theme-btn" aria-label="Toggle light/dark theme" type="button">
        <svg id="mob-ico-sun" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="4"/>
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
        </svg>
        <svg id="mob-ico-moon" viewBox="0 0 24 24" aria-hidden="true" style="display:none">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>
      <button id="hbg" aria-label="Open navigation menu" aria-expanded="false" type="button">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>

<div id="mob" role="dialog" aria-modal="true" aria-label="Navigation menu">
  <div class="mob-section">
    <nav class="mob-primary-links" aria-label="Mobile primary navigation">
      <a href="/" class="mob-link">Home</a>
      <a href="/tool-finder" class="mob-link">Tool Finder</a>
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
  <div class="mob-section">
    <div class="mob-sublabel">Compare tools</div>
    <div class="mob-pills">
      <a href="/compare" class="mob-pill">
        <span aria-hidden="true">⚔️</span>All Comparisons
      </a>
      <a href="/compare/custom" class="mob-pill">
        <span aria-hidden="true">🔀</span>Custom Compare
      </a>
    </div>
  </div>
</div>

<main id="main-content" tabindex="-1">
{{ content|safe }}
</main>

<footer class="footer" role="contentinfo">
  <div class="footer-in">
    <div class="footer-top">
      <div class="f-brand">
        <div class="f-logo">
          <div class="f-logo-icon" aria-hidden="true">AI</div>
          Moving Forward With AI
        </div>
        <p class="f-desc">Independent, transparent reviews of AI tools for freelancers, marketers, and builders. No paid placements. Clear verdicts. Updated weekly.</p>
        <div class="f-affil">Affiliate commissions fund this site</div>
      </div>
      <div class="f-col">
        <div class="f-col-title">Explore</div>
        <a href="/">Home</a>
        <a href="/tool-finder">Tool Finder</a>
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
      <p class="f-copy">© 2026 Moving Forward With AI. All rights reserved. Prices verified at time of writing — always confirm on the tool's website before purchasing.</p>
      <p class="f-disclaimer">// This site earns affiliate commissions. <a href="/affiliate-disclosure" style="color:var(--cyan)">Full disclosure →</a></p>
    </div>
  </div>
</footer>

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
(function () {
  var html = document.documentElement;
  function syncAllIcons(isLight) {
    var pairs = [['ico-sun','ico-moon'],['mob-ico-sun','mob-ico-moon']];
    pairs.forEach(function(p) {
      var sun  = document.getElementById(p[0]);
      var moon = document.getElementById(p[1]);
      if (sun)  sun.style.display  = isLight ? 'none'  : 'block';
      if (moon) moon.style.display = isLight ? 'block' : 'none';
    });
    var label = isLight ? 'Switch to dark mode' : 'Switch to light mode';
    ['theme-btn','mob-theme-btn'].forEach(function(id){
      var b = document.getElementById(id);
      if (b) b.setAttribute('aria-label', label);
    });
  }
  function applyTheme(isLight) {
    if (isLight) { html.classList.add('light'); } else { html.classList.remove('light'); }
    try { localStorage.setItem('mfwai-theme', isLight ? 'light' : 'dark'); } catch(e) {}
    syncAllIcons(isLight);
    html.style.display = 'none'; void html.offsetHeight; html.style.display = '';
  }
  syncAllIcons(html.classList.contains('light'));
  ['theme-btn', 'mob-theme-btn'].forEach(function(id) {
    var btn = document.getElementById(id);
    if (btn) { btn.addEventListener('click', function() { applyTheme(!html.classList.contains('light')); }); }
  });
})();

window.addEventListener('scroll', function () {
  var nav = document.getElementById('sitenav');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 24);
}, { passive: true });

(function () {
  var btn  = document.getElementById('hbg');
  var menu = document.getElementById('mob');
  if (!btn || !menu) return;
  function openMenu() {
    menu.classList.add('open'); btn.classList.add('open');
    btn.setAttribute('aria-expanded', 'true'); btn.setAttribute('aria-label', 'Close navigation menu');
    document.body.style.overflow = 'hidden';
  }
  function closeMenu() {
    menu.classList.remove('open'); btn.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-label', 'Open navigation menu');
    document.body.style.overflow = '';
  }
  btn.addEventListener('click', function (e) { e.stopPropagation(); if (menu.classList.contains('open')) { closeMenu(); } else { openMenu(); } });
  menu.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { closeMenu(); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && menu.classList.contains('open')) { closeMenu(); btn.focus(); } });
  document.addEventListener('click', function (e) {
    if (menu.classList.contains('open') && !menu.contains(e.target) && e.target !== btn && !btn.contains(e.target)) { closeMenu(); }
  });
})();

(function () {
  var dropIds = ['drop-compare', 'drop-roles'];
  function closeAll() {
    dropIds.forEach(function(id) {
      var drop = document.getElementById(id); if (!drop) return;
      drop.classList.remove('open');
      var btn = drop.querySelector('.nav-drop-btn'); if (btn) btn.setAttribute('aria-expanded', 'false');
    });
  }
  dropIds.forEach(function(id) {
    var drop = document.getElementById(id); if (!drop) return;
    var btn = drop.querySelector('.nav-drop-btn'); if (!btn) return;
    btn.addEventListener('click', function(e) {
      e.stopPropagation(); var isOpen = drop.classList.contains('open'); closeAll();
      if (!isOpen) { drop.classList.add('open'); btn.setAttribute('aria-expanded', 'true'); }
    });
  });
  document.addEventListener('click', function(e) {
    var insideDrop = dropIds.some(function(id) { var drop = document.getElementById(id); return drop && drop.contains(e.target); });
    if (!insideDrop) closeAll();
  });
  document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeAll(); });
})();

(function () {
  if (!('IntersectionObserver' in window)) return;
  document.body.classList.add('rv-ready');
  var els = document.querySelectorAll('.rv');
  if (!els.length) return;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) { if (entry.isIntersecting) { entry.target.classList.add('visible'); io.unobserve(entry.target); } });
  }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
  els.forEach(function (el, i) { el.style.transitionDelay = (i % 4 * 0.07) + 's'; io.observe(el); });
})();

(function() {
  var allTools = null, loading = false;
  var sov = document.getElementById('sov'), sovCount = document.getElementById('sov-count');
  var sovRes = document.getElementById('sov-results'), searchInput = document.getElementById('search-input');
  var searchTimer;
  if (!sov || !searchInput) return;
  function loadTools(cb) {
    if (allTools !== null) { cb(); return; }
    if (loading) return; loading = true;
    fetch('/api/tools').then(function(r){ return r.json(); }).then(function(d){ allTools = d.tools || []; loading = false; cb(); }).catch(function(){ allTools = []; loading = false; cb(); });
  }
  function closeSov() { sov.classList.remove('open'); document.body.style.overflow = ''; if (searchInput) searchInput.setAttribute('aria-expanded', 'false'); }
    function miniCard(t) {
  var sc = t.score, isHi = sc >= 88;
  var bg  = isHi ? 'var(--green-d)' : 'var(--cyan-d)',
      bdr = isHi ? 'var(--green-g)' : 'var(--cyan-g)',
      col  = isHi ? 'var(--green)' : 'var(--cyan)';

  return '<div class="tool-card" style="cursor:pointer" data-slug="'+t.slug+'">'+
           '<div class="tc-accent-bar"></div>'+
           '<div class="tc-body">'+
             '<div class="tc-meta">'+
               '<div class="tc-cat">'+(t.category||'')+'</div>'+
               '<div class="tc-score" style="background:'+bg+';border:1px solid '+bdr+';color:'+col+'">'+sc+'</div>'+
             '</div>'+
             '<a href="/tool/'+t.slug+'" class="tc-name">'+t.name+'</a>'+
             '<p class="tc-tagline">'+(t.tagline||'')+'</p>'+
           '</div>'+
           '<div class="tc-footer">'+
             '<div class="tc-pricing">'+
               '<span class="tc-price">'+(t.starting_price||'')+'</span>'+
             '</div>'+
           '</div>'+
         '</div>';
}

// Attach click handler safely via JS
document.addEventListener('click', function(e){
  const card = e.target.closest('.tool-card');
  if(card) location.href = '/tool/' + encodeURIComponent(card.dataset.slug);
});
  function runSearch(q) {
    if (!q || q.length < 2) { closeSov(); return; }
    loadTools(function() {
      var ql = q.toLowerCase();
      var hits = allTools.filter(function(t) { return (t.name||'').toLowerCase().includes(ql)||(t.category||'').toLowerCase().includes(ql)||(t.tagline||'').toLowerCase().includes(ql)||(t.tags||[]).join(' ').toLowerCase().includes(ql); });
      sovCount.textContent = '// '+hits.length+' result'+(hits.length!==1?'s':'')+' for "'+q+'"';
      sovRes.innerHTML = hits.length ? hits.map(miniCard).join('') : '<div class="sov-empty">// No tools found for "'+q+'"</div>';
      sov.classList.add('open'); document.body.style.overflow = 'hidden'; searchInput.setAttribute('aria-expanded', 'true');
    });
  }
  searchInput.addEventListener('input', function(e) { clearTimeout(searchTimer); var q = e.target.value.trim(); searchTimer = setTimeout(function() { runSearch(q); }, 160); });
  searchInput.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closeSov(); searchInput.value = ''; } });
  document.getElementById('sov-close').addEventListener('click', closeSov);
  sov.addEventListener('click', function(e) { if (e.target === sov) closeSov(); });
  document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeSov(); });
})();

(function () {
  var KEY = 'mfwai_consent_v2', bar = document.getElementById('ckbar');
  try { if (!localStorage.getItem(KEY)) { setTimeout(function () { bar.classList.add('show'); }, 1800); } } catch (e) { bar.classList.add('show'); }
  function dismiss(v) { try { localStorage.setItem(KEY, v); } catch (e) {} bar.classList.remove('show'); }
  document.getElementById('ck-ok').addEventListener('click',  function () { dismiss('all'); });
  document.getElementById('ck-ess').addEventListener('click', function () { dismiss('ess'); });
})();

var ef = document.getElementById('email-form');
if (ef) {
  ef.addEventListener('submit', function (e) {
    e.preventDefault();
    var btn = ef.querySelector('button[type="submit"]'), em = ef.querySelector('input[type="email"]');
    if (!em || !em.value) return;
    btn.textContent = 'Subscribed!'; btn.style.background = 'var(--green)'; btn.disabled = true; em.disabled = true;
  });
}
</script>

</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def render(title, desc, content, schema='', bcs='', schema2='', og_type='website', og_image=''):
    canon = SITE_URL + (request.path.rstrip('/') or '/')
    return render_template_string(BASE,
        title=title, desc=desc, content=content,
        css=CSS, roles=ROLES, slugify=slugify,
        canon=canon, schema=schema, bcs=bcs, schema2=schema2,
        og_type=og_type, og_image=og_image or OG_IMAGE,
        ws_schema=website_schema())


def breadcrumb_html(crumbs):
    parts = []
    sep = '<svg class="sep" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    for i, (label, url) in enumerate(crumbs):
        if i < len(crumbs) - 1:
            parts.append(f'<a href="{url}">{label}</a>')
        else:
            parts.append(f'<span class="current" aria-current="page">{label}</span>')
    return f'<nav class="breadcrumb page" aria-label="Breadcrumb">{"".join(f"{p}{sep}" if i < len(crumbs)-1 else p for i,p in enumerate(parts))}</nav>'


def score_badge(score):
    bg  = 'var(--green-d)' if score>=88 else 'var(--cyan-d)' if score>=78 else 'var(--amber-d)'
    bdr = 'var(--green-g)' if score>=88 else 'var(--cyan-g)' if score>=78 else 'var(--amber-g)'
    col = 'var(--green)'   if score>=88 else 'var(--cyan)'   if score>=78 else 'var(--amber)'
    return f'<div class="tc-score" style="background:{bg};border:1px solid {bdr};color:{col}">{score}</div>'


def tool_card(t, delay=0):
    sc   = t['score']
    sbg  = 'var(--green-d)' if sc>=88 else 'var(--cyan-d)'
    sbdr = 'var(--green-g)' if sc>=88 else 'var(--cyan-g)'
    scol = 'var(--green)'   if sc>=88 else 'var(--cyan)'
    badges = []
    if t.get('free_tier'):  badges.append('<span class="badge b-free">Free tier</span>')
    if t.get('free_trial'): badges.append(f'<span class="badge b-trial">{t["trial_days"]}-day trial</span>')
    if not t.get('free_tier') and not t.get('free_trial'):
        badges.append('<span class="badge b-paid">Paid only</span>')
    if t.get('featured'): badges.append('<span class="badge b-top">Featured</span>')
    return f"""<article class="tool-card rv" aria-label="{t['name']} — {t['category']} tool">
  <div class="tc-accent-bar" aria-hidden="true"></div>
  <div class="tc-body">
    <div class="tc-meta">
      <div class="tc-cat" aria-label="Category: {t['category']}">{t['category']}</div>
      <div class="tc-score" style="background:{sbg};border:1px solid {sbdr};color:{scol}"
           aria-label="MFWAI score: {sc} out of 100">{sc}/100</div>
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
    return """<section class="email-sec" aria-labelledby="newsletter-heading">
  <div class="email-inner">
    <div class="email-left">
      <div class="email-eyebrow">Weekly newsletter</div>
      <h2 class="email-h2" id="newsletter-heading">
        Stay ahead of <em>AI tool</em> changes
      </h2>
      <p class="email-sub">New reviews, pricing updates, and tool recommendations — delivered weekly. No spam.</p>
    </div>
    <div class="email-right">
      <form id="email-form" novalidate style="display:contents">
        <input class="email-input" type="email" placeholder="your@email.com" required
          aria-label="Your email address" autocomplete="email">
        <button type="submit" class="btn-email">Subscribe</button>
      </form>
      <p class="email-notice">// No spam. Unsubscribe any time.</p>
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
    <strong>Affiliate disclosure:</strong>
    Moving Forward With AI earns a commission when you sign up through links —
    at no extra cost to you.
    <a href="/affiliate-disclosure">Learn more →</a>
  </div>
</div>"""


def build_custom_compare_page(sorted_tools, ta, tb, verdict, slug_a, slug_b):
    opts_a = "\n".join(
        f'<option value="{t["slug"]}" {"selected" if t["slug"] == slug_a else ""}>{t["name"]}</option>'
        for t in sorted_tools
    )
    opts_b = "\n".join(
        f'<option value="{t["slug"]}" {"selected" if t["slug"] == slug_b else ""}>{t["name"]}</option>'
        for t in sorted_tools
    )

    selector_html = f"""
<div class="page" style="padding-top:32px;padding-bottom:28px">
  <div class="sec-eyebrow">Custom comparison · Any two tools</div>
  <h1 style="font-family:var(--font-display);font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1;margin-top:8px;margin-bottom:8px">
    Compare any two <em style="color:var(--cyan);font-style:normal">AI tools</em>
  </h1>
  <p style="font-size:.96rem;color:var(--ink3);margin-top:12px;max-width:520px;line-height:1.75;margin-bottom:28px">
    Select any two tools from our reviewed collection and get an instant side-by-side comparison.
  </p>
  <div style="background:var(--surf);border:1px solid var(--bdr2);border-radius:var(--r3);padding:24px;display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap;box-shadow:var(--sh1)">
    <div style="flex:1;min-width:180px">
      <label for="sel-a" style="font-family:var(--font-mono);font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;color:var(--ink4);display:block;margin-bottom:8px">Tool A</label>
      <select id="sel-a" name="a" style="width:100%;background:var(--bg3);border:1px solid var(--bdr2);border-radius:var(--r2);padding:11px 14px;color:var(--ink);font-family:var(--font-body);font-size:.88rem;outline:none;appearance:none;cursor:pointer;transition:border-color .2s;-webkit-appearance:none" onfocus="this.style.borderColor='var(--cyan)'" onblur="this.style.borderColor='var(--bdr2)'">
        <option value="">Select a tool…</option>
        {opts_a}
      </select>
    </div>
    <div style="font-family:var(--font-mono);font-size:.68rem;color:var(--ink4);padding:11px 0;letter-spacing:.08em;flex-shrink:0">VS</div>
    <div style="flex:1;min-width:180px">
      <label for="sel-b" style="font-family:var(--font-mono);font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;color:var(--ink4);display:block;margin-bottom:8px">Tool B</label>
      <select id="sel-b" name="b" style="width:100%;background:var(--bg3);border:1px solid var(--bdr2);border-radius:var(--r2);padding:11px 14px;color:var(--ink);font-family:var(--font-body);font-size:.88rem;outline:none;appearance:none;cursor:pointer;transition:border-color .2s;-webkit-appearance:none" onfocus="this.style.borderColor='var(--cyan)'" onblur="this.style.borderColor='var(--bdr2)'">
        <option value="">Select a tool…</option>
        {opts_b}
      </select>
    </div>
    <button id="compare-btn" type="button" class="btn-primary" style="flex-shrink:0"
            onclick="var a=document.getElementById('sel-a').value,b=document.getElementById('sel-b').value;if(a&&b&&a!==b)window.location.href='/compare/custom?a='+a+'&b='+b;else if(a===b)alert('Please select two different tools.');">
      Compare now →
    </button>
  </div>
</div>"""

    if not ta or not tb:
        return f"""
{breadcrumb_html([('Home','/'),('Compare','/compare'),('Custom Compare','/compare/custom')])}
{selector_html}
<div class="page" style="padding:64px 0;text-align:center">
  <p style="font-family:var(--font-mono);font-size:.78rem;color:var(--ink4);letter-spacing:.04em">// Select two tools above to see a side-by-side comparison</p>
</div>"""

    def build_cd_card(t):
        sc = t["score"]
        sc_col = score_color(sc)
        free_tier_cell = '<span class="tick">✓</span>' if t.get("free_tier") else '<span class="cross">✗</span>'
        if t.get("free_trial"):
            trial_cell = f'<span class="tick">✓ {t.get("trial_days", "")}d</span>'
        else:
            trial_cell = '<span class="cross">✗</span>'
        pros_html = "".join(f"<li>{p}</li>" for p in t["pros"][:3])
        cons_html = "".join(f"<li>{c}</li>" for c in t["cons"][:2])
        return f"""<div class="cd-card">
  <div class="cd-name">{t['name']}</div>
  <div class="cd-score" style="color:{sc_col}">{sc}/100</div>
  <div style="font-family:var(--font-mono);font-size:.64rem;color:{sc_col};letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px">{score_label(sc)} · MFWAI Score</div>
  <table class="comp-table"><tbody>
    <tr><td>Starting price</td><td style="font-weight:600;color:var(--ink)">{t['starting_price']}</td></tr>
    <tr><td>Pricing model</td><td>{t['pricing_model']}</td></tr>
    <tr><td>Free tier</td><td>{free_tier_cell}</td></tr>
    <tr><td>Free trial</td><td>{trial_cell}</td></tr>
    <tr><td>Category</td><td>{t['category']}</td></tr>
  </tbody></table>
  <div style="margin-top:16px"><div class="panel-label">Top pros</div><ul class="plist pros">{pros_html}</ul></div>
  <div style="margin-top:16px"><div class="panel-label">Key cons</div><ul class="plist cons">{cons_html}</ul></div>
  <a href="{t['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener noreferrer"
     class="btn-try" style="margin-top:20px;width:100%;justify-content:center">Try {t['name']} →</a>
</div>"""

    verdict_html = ""
    if verdict:
        verdict_html = f"""<div class="winner-block rv" style="background:var(--cyan-d);border-color:var(--cyan-g)">
  <div class="winner-label" style="color:var(--cyan)">// Quick verdict</div>
  <p class="winner-text">{verdict}</p>
</div>"""

    return f"""
{breadcrumb_html([('Home','/'),('Compare','/compare'),(f'{ta["name"]} vs {tb["name"]}',f'/compare/custom?a={slug_a}&b={slug_b}')])}
{selector_html}
<div class="page" style="padding-top:28px">
  <div class="comp-detail-grid">
    {build_cd_card(ta)}
    {build_cd_card(tb)}
  </div>
  {verdict_html}
</div>"""


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
@cache.cached(timeout=600, query_string=True)
def home():
    panel_tools = sorted(TOOLS, key=lambda t: -t['score'])[:4]
    panel_items = ''
    for i, t in enumerate(panel_tools):
        sc     = t['score']
        sc_cls = 'ps-hi' if sc >= 88 else 'ps-md'
        panel_items += f"""<a href="/tool/{t['slug']}" class="ptool">
          <span class="ptool-rank">{str(i+1).zfill(2)}</span>
          <div class="ptool-info">
            <div class="ptool-name">{t['name']}</div>
            <div class="ptool-cat">{t['category']}</div>
          </div>
          <div class="ptool-score {sc_cls}">{sc}</div>
        </a>"""

    hero = f"""<div class="page">
  <section class="hero" aria-labelledby="hero-heading">
    <div>
      <div class="hero-eyebrow">
        <div class="hero-eyebrow-dot" aria-hidden="true"></div>
        AI Tool Reviews · Updated 2026
      </div>
      <h1 class="hero-h1" id="hero-heading"><em>AI tool reviews</em>
        <span class="serif-accent">Cut through the noise. Find what works.</span>
      </h1>
      <p class="hero-sub">
        Hundreds of AI tools, impossible to evaluate them all — we do it for you.
        Transparent scores, honest verdicts, zero paid placements. Built for
        freelancers, marketers, and business owners who need answers, not hype.
      </p>
      <div class="hero-ctas">
        <a href="/tool-finder" class="btn-primary">
          Find my tool stack
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </a>
        <a href="/tools" class="btn-ghost">Browse all {len(TOOLS)} tools</a>
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

    trust_bar = f"""<div class="page" style="padding-top:0;padding-bottom:0" role="note" aria-label="Site statistics">
  <div style="display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:0;padding:18px 0 24px;border-bottom:1px solid var(--div);">
    <div style="display:flex;align-items:center;gap:10px;padding:8px 28px;border-right:1px solid var(--div)">
      <span style="font-family:var(--font-display);font-size:1.6rem;font-weight:800;letter-spacing:-.05em;color:var(--cyan)">{len(TOOLS)}+</span>
      <span style="font-family:var(--font-mono);font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink4)">tools<br>reviewed</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;padding:8px 28px;border-right:1px solid var(--div)">
      <span style="font-family:var(--font-display);font-size:1.6rem;font-weight:800;letter-spacing:-.05em;color:var(--cyan)">{len(COMPARISONS)}+</span>
      <span style="font-family:var(--font-mono);font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink4)">head-to-head<br>comparisons</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;padding:8px 28px;border-right:1px solid var(--div)">
      <span style="font-family:var(--font-display);font-size:1.6rem;font-weight:800;letter-spacing:-.05em;color:var(--green)">$0</span>
      <span style="font-family:var(--font-mono);font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink4)">paid<br>placements</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;padding:8px 28px">
      <span style="font-family:var(--font-display);font-size:1.6rem;font-weight:800;letter-spacing:-.05em;color:var(--amber)">Weekly</span>
      <span style="font-family:var(--font-mono);font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink4)">updates &amp;<br>new reviews</span>
    </div>
  </div>
</div>"""

    role_options = '\n'.join(
        f'<option value="/for/{r["slug"]}">{r["icon"]} {r["name"]}</option>'
        for r in ROLES
    )

    tool_finder = f"""<div class="page" id="tool-finder">
  <section style="background:var(--surf);border:1px solid var(--bdr2);border-radius:var(--r4);padding:36px 40px;display:grid;grid-template-columns:1fr auto;gap:32px;align-items:center;box-shadow:var(--sh1);position:relative;overflow:hidden;margin-top:clamp(40px,5vw,64px);" aria-labelledby="finder-heading">
    <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--amber),var(--cyan),var(--violet))"></div>
    <div>
      <div style="font-family:var(--font-mono);font-size:.62rem;letter-spacing:.16em;text-transform:uppercase;color:var(--amber);margin-bottom:10px;display:flex;align-items:center;gap:8px">
        <span style="display:inline-block;width:16px;height:1px;background:var(--amber)"></span>
        Not sure where to start?
      </div>
      <h2 id="finder-heading" style="font-family:var(--font-display);font-size:clamp(1.4rem,2.5vw,2rem);font-weight:800;letter-spacing:-.04em;color:var(--ink);margin-bottom:8px;line-height:1.1">
        Find your <em style="font-style:normal;color:var(--cyan)">recommended stack</em>
      </h2>
      <p style="font-size:.9rem;color:var(--ink3);line-height:1.7;max-width:420px">
        Tell us your role and we&#39;ll show you the exact tools our reviewers recommend &mdash; scored and ranked.
        Or <a href="/tool-finder" style="color:var(--cyan)">take the full quiz →</a>
      </p>
    </div>
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end">
      <div style="display:flex;flex-direction:column;gap:6px">
        <label for="role-finder-select" style="font-family:var(--font-mono);font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink4)">I am a&hellip;</label>
        <select id="role-finder-select"
          style="background:var(--bg3);border:1px solid var(--bdr2);border-radius:var(--r2);padding:12px 44px 12px 16px;color:var(--ink);font-family:var(--font-body);font-size:.92rem;font-weight:500;outline:none;cursor:pointer;appearance:none;-webkit-appearance:none;min-width:240px;background-image:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' stroke='%237c8db5' fill='none' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E\");background-repeat:no-repeat;background-position:right 14px center;transition:border-color .2s,box-shadow .2s;"
          onfocus="this.style.borderColor='var(--cyan)';this.style.boxShadow='0 0 0 3px var(--cyan-d)'"
          onblur="this.style.borderColor='var(--bdr2)';this.style.boxShadow='none'"
          aria-label="Select your role">
          <option value="" disabled selected>Select your role…</option>
          {role_options}
        </select>
      </div>
      <div style="padding-top:22px">
        <button type="button" class="btn-primary"
          onclick="var v=document.getElementById('role-finder-select').value;if(v)window.location.href=v;"
          aria-label="Go to my recommended tool stack">
          Show my stack
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </section>
</div>"""

    role_cards = '\n'.join(f"""<a href="/for/{r['slug']}" class="role-card rv" aria-label="{r['name']}: {len(r['tool_slugs'])} recommended tools">
      <span class="rc-icon" aria-hidden="true">{r['icon']}</span>
      <div class="rc-name">{r['name']}</div>
      <div class="rc-desc">{r['description']}</div>
      <div class="rc-count">{len(r['tool_slugs'])} recommended tools</div>
      <div class="rc-arrow">See the stack →</div>
    </a>""" for r in ROLES)

    roles_sec = f"""<div class="page">
  <section class="sec" aria-labelledby="roles-heading">
    <div class="sec-top">
      <div><div class="sec-eyebrow">Built for your role</div>
      <h2 class="sec-h2" id="roles-heading">Find your <em>perfect stack</em></h2></div>
      <a href="/tools" class="sec-link">All tools →</a>
    </div>
    <div class="roles-grid">{role_cards}</div>
  </section>
</div>"""

    featured  = [t for t in TOOLS if t.get('featured')]
    cards_html = '\n'.join(tool_card(t) for t in featured)
    tools_sec = f"""<div class="page">
  <section class="sec" aria-labelledby="featured-heading">
    <div class="sec-top">
      <div><div class="sec-eyebrow">Highest rated · Featured picks</div>
      <h2 class="sec-h2" id="featured-heading">Top <em>AI tools</em> right now</h2></div>
      <a href="/tools" class="sec-link">All {len(TOOLS)} tools →</a>
    </div>
    <div class="tools-grid">{cards_html}</div>
  </section>
</div>"""

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
      <div><div class="sec-eyebrow">Head to head · High intent</div>
      <h2 class="sec-h2" id="compare-heading"><em>Compare</em> tools side by side</h2></div>
      <a href="/compare" class="sec-link">All {len(COMPARISONS)} comparisons →</a>
    </div>
    <div class="comp-grid">{comp_cards}</div>
  </section>
</div>"""

    posts = sorted([{**v, 'slug': k} for k, v in BLOG_POSTS.items()], key=lambda x: x['date'], reverse=True)
    blog_cards = '\n'.join(f"""<a href="/blog/{p['slug']}" class="blog-card rv" aria-label="Guide: {p['title']}">
      <div class="blog-card-accent"></div>
      <div class="blog-card-body">
        <div class="blog-eyebrow">{datetime.datetime.strptime(p['date'],'%Y-%m-%d').strftime('%d %b %Y')} &nbsp;·&nbsp;{p.get('category','Guide')}</div>
        <div class="blog-title">{p['title']}</div>
        <div class="blog-desc">{p.get('description','')}</div>
        <div class="blog-link" aria-hidden="true">Read guide →</div>
      </div>
    </a>""" for p in posts[:3])

    blog_sec = f"""<div class="page">
  <section class="sec" aria-labelledby="guides-heading">
    <div class="sec-top">
      <div><div class="sec-eyebrow">Guides · Analysis · How-tos</div>
      <h2 class="sec-h2" id="guides-heading">Latest <em>guides</em></h2></div>
      <a href="/blog" class="sec-link">All guides →</a>
    </div>
    <div class="blog-grid">{blog_cards}</div>
  </section>
</div>"""

    content = (
        hero + trust_bar + affil_strip() + tool_finder + roles_sec
        + tools_sec + comp_sec + blog_sec + email_capture()
        + '<div style="height:56px"></div>'
    )

    return render(
        title='Independent AI Tool Reviews 2026 — Moving Forward With AI',
        desc=f'Independent reviews of {len(TOOLS)}+ AI tools with transparent scores. No paid placements. Built for freelancers, marketers, and business owners.',
        content=content,
        bcs=bc_schema([('Home', '/')]))


@app.route('/tool-finder')
@cache.cached(timeout=600)
def tool_finder_page():
    bc_html = breadcrumb_html([('Home', '/'), ('Tool Finder', '/tool-finder')])
    content = render_template_string(
        TOOL_FINDER_TEMPLATE,
        breadcrumb=bc_html
    )
    return render(
        title='AI Tool Finder Quiz 2026 — Find Your Perfect Stack | MFWAI',
        desc='Answer 4 quick questions and get personalised AI tool recommendations based on your role, goals, budget, and skill level.',
        content=content,
        bcs=bc_schema([('Home', '/'), ('Tool Finder', '/tool-finder')])
    )


@app.route('/api/tool-finder')
def api_tool_finder():
    role   = request.args.get('role', '')
    goal   = request.args.get('goal', '')
    budget = request.args.get('budget', '')
    skill  = request.args.get('skill', '')

    matched = match_tools_for_quiz(role, goal, budget, skill, TOOLS)

    return jsonify({'tools': [{
        'slug':           t['slug'],
        'name':           t['name'],
        'category':       t['category'],
        'score':          t['score'],
        'verdict':        t['verdict'][:160],
        'starting_price': t['starting_price'],
        'pricing_model':  t['pricing_model'],
        'affiliate_url':  t['affiliate_url'],
    } for t in matched]})


@app.route('/tools')
@cache.cached(timeout=600, query_string=True)
def tools_all():
    page  = int(request.args.get('page', 1))
    PER   = 12
    paged = TOOLS[(page-1)*PER: page*PER]
    total_pages = (len(TOOLS)+PER-1)//PER
    cards = '\n'.join(tool_card(t) for t in paged)
    prev  = f'<a href="/tools?page={page-1}" rel="prev">← Previous</a>' if page > 1 else ''
    nxt   = f'<a href="/tools?page={page+1}" rel="next">Next →</a>'    if page < total_pages else ''
    pager = f'<div class="page"><div class="pager">{prev}{nxt}</div></div>' if prev or nxt else ''
    content = f"""
    {breadcrumb_html([('Home','/'),('All Tools','/tools')])}
    <div class="page" style="padding-top:32px;padding-bottom:24px">
      <div class="sec-eyebrow">All tools · {len(TOOLS)} reviewed</div>
      <h1 style="font-family:var(--font-display);font-size:clamp(2rem,4vw,3.2rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1;margin-top:8px">
        Best AI tools, <em style="color:var(--cyan);font-style:normal">independently reviewed</em>
      </h1>
      <p style="font-size:.96rem;color:var(--ink3);margin-top:12px;max-width:500px;line-height:1.75">
        No sponsored rankings. No paid placements. Just thorough, independent reviews scored on merit.
      </p>
    </div>
    {affil_strip()}
    <div class="page" style="padding-top:40px"><div class="tools-grid">{cards}</div></div>
    {pager}"""
    return render(
        title=f'Best AI Tools 2026 — {len(TOOLS)} Independently Reviewed | MFWAI',
        desc=f'Browse all {len(TOOLS)} AI tools reviewed independently. Transparent scores, honest verdicts, zero paid placements.',
        content=content,
        schema=itemlist_schema(TOOLS, "AI Tools Directory"),
        bcs=bc_schema([('Home', '/'), ('All Tools', '/tools')]))


@app.route('/for/<slug>')
@cache.cached(timeout=900)
def role_page(slug):
    role       = get_role(slug)
    if not role: abort(404)
    role_tools = [get_tool(s) for s in role['tool_slugs'] if get_tool(s)]
    top        = get_tool(role['top_pick']) if role.get('top_pick') else None

    pain_items = '\n'.join(
        f'<div class="pain-item"><span class="pain-x" aria-hidden="true">✗</span>{p}</div>'
        for p in role.get('pain_points', []))

    top_pick_html = ''
    if top:
        sc_col  = score_color(top['score'])
        top_pick_html = f"""<div class="top-pick-bar rv">
          <div class="top-pick-badge">★ Top pick</div>
          <div class="top-pick-info">
            <div class="top-pick-name">{top['name']}</div>
            <div class="top-pick-tagline">{top['tagline']}</div>
          </div>
          <div class="top-pick-score" style="color:{sc_col}">{top['score']}</div>
          <a href="{top['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener noreferrer"
             class="btn-primary">Try it →</a>
        </div>"""

    cards   = '\n'.join(tool_card(t) for t in role_tools)
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
        <div class="sec-eyebrow" style="margin:36px 0 20px">Recommended stack · {len(role_tools)} tools</div>
      </section>
      <div class="tools-grid">{cards}</div>
    </div>
    {email_capture()}"""

    return render(
        title=f'Best AI Tools for {role["name"]} 2026 — Moving Forward With AI',
        desc=f'{role["description"]} Independent reviews of the best AI tools for {role["name"].lower()} in 2026.',
        content=content,
        bcs=bc_schema([('Home','/'), ('Tools','/tools'), (role['name'], f'/for/{slug}')]))


@app.route('/tool/<slug>')
@cache.cached(timeout=1800)
def tool_detail(slug):
    t = get_tool(slug)
    if not t: abort(404)
    sc     = t['score']
    sc_col = score_color(sc)
    sc_lbl = score_label(sc)
    name   = t['name']

    badges = []
    if t.get('free_tier'):  badges.append('<span class="badge b-free">Free tier</span>')
    if t.get('free_trial'): badges.append(f'<span class="badge b-trial">{t["trial_days"]}-day trial</span>')

    header = f"""
    <header class="td-header">
      <div class="td-header-grid">
        <div>
          <div class="td-eyebrow">{t['category'].upper()} REVIEW</div>
          <h1 class="td-h1">{name}</h1>
          <p class="td-tagline">{t['tagline']}</p>
          <div class="td-meta-row">{''.join(badges)}</div>
        </div>
        <div class="td-score-block" aria-label="MFWAI score: {sc} out of 100">
          <div class="td-score-num" style="color:{sc_col}">{sc}</div>
          <div class="td-score-label" style="color:{sc_col}">{sc_lbl}</div>
          <div class="td-score-sub">MFWAI score / 100</div>
        </div>
      </div>
    </header>"""

    free_tier_text = 'Yes' if t.get('free_tier') else 'No'
    best_for_line  = t['best_for'][0] if t['best_for'] else ''
    not_ideal_items = t.get('not_ideal_for', [])
    not_ideal_line  = not_ideal_items[0] if not_ideal_items else (t['cons'][0] if t['cons'] else '')

    verdict_box = f"""
    <section class="verdict-box rv" aria-labelledby="quick-verdict-heading">
      <div class="verdict-box-grid">
        <div class="vb-score-ring" style="color:{sc_col}" aria-label="Score: {sc} out of 100">
          <div class="vb-score-num" style="color:{sc_col}">{sc}</div>
          <div class="vb-score-max">/ 100</div>
        </div>
        <div class="vb-content">
          <div class="vb-label" id="quick-verdict-heading">Quick verdict</div>
          <p class="vb-verdict">{t['verdict']}</p>
          <div class="vb-meta-grid">
            <div class="vb-meta-item">
              <span class="vb-meta-label">Best for</span>
              <span class="vb-meta-value">{best_for_line}</span>
            </div>
            <div class="vb-meta-item">
              <span class="vb-meta-label">Not ideal for</span>
              <span class="vb-meta-value">{not_ideal_line}</span>
            </div>
            <div class="vb-meta-item">
              <span class="vb-meta-label">Starting at</span>
              <span class="vb-meta-value">{t['starting_price']}</span>
            </div>
            <div class="vb-meta-item">
              <span class="vb-meta-label">Free tier</span>
              <span class="vb-meta-value">{free_tier_text}</span>
            </div>
          </div>
        </div>
        <div class="vb-cta-col">
          <a href="{t['affiliate_url']}" target="_blank"
             rel="nofollow sponsored noopener noreferrer"
             class="btn-td-cta" aria-label="Try {name} — opens in new tab">
            Try {name}
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15,3 21,3 21,9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
          </a>
          <div class="trust-items" role="list" style="margin-top:4px">
            <div class="trust-item" role="listitem">
              <svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              No extra cost to you
            </div>
          </div>
        </div>
      </div>
    </section>"""

    pros_html = '\n'.join(f'<li>{p}</li>' for p in t['pros'])
    cons_html = '\n'.join(f'<li>{c}</li>' for c in t['cons'])

    pros_cons = f"""
    <section class="pc-grid rv" aria-labelledby="pros-heading cons-heading">
      <div class="pc-col">
        <h2 class="pc-col-title pro-title" id="pros-heading">What we like</h2>
        <ul class="plist pros" aria-label="Pros">{pros_html}</ul>
      </div>
      <div class="pc-col">
        <h2 class="pc-col-title con-title" id="cons-heading">Where it falls short</h2>
        <ul class="plist cons" aria-label="Cons">{cons_html}</ul>
      </div>
    </section>"""

    pricing_tiers = t.get('pricing_tiers', [])
    if pricing_tiers:
        rows = ''
        for tier in pricing_tiers:
            monthly  = tier.get('monthly', '\u2014')
            annual   = tier.get('annual', '\u2014')
            features = tier.get('features', '\u2014')
            rows += f'<tr><td>{tier["name"]}</td><td>{monthly}</td><td>{annual}</td><td>{features}</td></tr>'
        pricing_table = f"""
        <table class="pricing-table">
          <thead><tr><th>Plan</th><th>Monthly</th><th>Annual</th><th>What\u2019s included</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>"""
    else:
        free_row = ''
        if t.get('free_tier'):
            free_row = '<tr><td>Free</td><td>$0</td><td>$0</td><td>Limited features \u2014 free forever</td></tr>'
        pricing_table = f"""
        <table class="pricing-table">
          <thead><tr><th>Plan</th><th>Monthly</th><th>Annual</th><th>What\u2019s included</th></tr></thead>
          <tbody>
            {free_row}
            <tr><td>Paid</td><td>{t['starting_price']}</td><td>\u2014</td><td>{t['pricing_model']}</td></tr>
          </tbody>
        </table>"""

    date_verified = t.get('date_added', '2026')
    pricing_section = f"""
    <section class="pricing-section rv" aria-labelledby="pricing-heading">
      <div class="pricing-section-hdr">
        <h2 class="review-section-hdr" id="pricing-heading">{name} pricing</h2>
        <div class="pricing-verified">Prices verified {date_verified}</div>
      </div>
      {pricing_table}
    </section>"""

    yes_items = '\n'.join(f'<li>{b}</li>' for b in t['best_for'])
    not_ideal_list = t.get('not_ideal_for', t['cons'][:3])
    no_items = '\n'.join(f'<li>{n}</li>' for n in not_ideal_list)

    who_section = f"""
    <section class="who-section rv" aria-labelledby="who-heading">
      <h2 class="review-section-hdr" id="who-heading">Who should use {name}?</h2>
      <div class="who-grid">
        <div>
          <div class="panel-label" style="color:var(--green)">\u2714 This tool is right for you if\u2026</div>
          <ul class="who-list who-yes">{yes_items}</ul>
        </div>
        <div>
          <div class="panel-label" style="color:var(--amber)">\u2192 Consider an alternative if\u2026</div>
          <ul class="who-list who-no">{no_items}</ul>
        </div>
      </div>
    </section>"""

    faqs = t.get('faqs', [])
    if not faqs:
        faqs = [
            (f'Is {name} worth it in 2026?', f'{name} scores {sc}/100 in our independent review. {t["verdict"]}'),
            (f'What is {name} best for?', 'Claude Pro output indicates, ' + '; '.join(t['best_for'][:3]) + '.'),
            (f'How much does {name} cost?', f'{name} starts at {t["starting_price"]} ({t["pricing_model"]}). ' + ('A free tier is available.' if t.get('free_tier') else 'No free tier is available.')),
            (f'Does {name} offer a free trial?', (f'Yes \u2014 {name} offers a {t.get("trial_days","")}-day free trial.' if t.get('free_trial') else f'Currently, {name} does not offer a free trial.' + (' However, it does have a free tier.' if t.get('free_tier') else ''))),
            (f'What are the main downsides of {name}?', 'The key limitations are: ' + '; '.join(t['cons'][:3]) + '.'),
        ]
    else:
        faqs = [(f['q'], f['a']) for f in faqs]

    faq_items = ''
    for i, (q, a) in enumerate(faqs):
        faq_items += f"""<div class="faq-item" id="faq-{i}">
          <button class="faq-q" type="button" aria-expanded="false" aria-controls="faq-a-{i}"
                  onclick="this.parentElement.classList.toggle('open');this.setAttribute('aria-expanded',this.parentElement.classList.contains('open'))">
            {q}
            <svg class="faq-chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg>
          </button>
          <div class="faq-a" id="faq-a-{i}" role="region">{a}</div>
        </div>"""

    faq_html = f"""
    <section class="faq-section rv" aria-labelledby="faq-heading">
      <div class="faq-section-hdr">
        <h2 class="review-section-hdr" id="faq-heading">Frequently asked questions</h2>
      </div>
      {faq_items}
    </section>"""

    faq_sd = faq_schema(faqs)

    alt_slugs = t.get('alternatives', [])
    if alt_slugs:
        alt_tools = [get_tool(s) for s in alt_slugs if get_tool(s)]
    else:
        alt_tools = [x for x in TOOLS if x['slug'] != slug and x['category'] == t['category']]
        if len(alt_tools) < 2:
            alt_tools += [x for x in TOOLS if x['slug'] != slug and x not in alt_tools
                          and any(r in x.get('roles', []) for r in t.get('roles', []))]
        alt_tools = sorted(alt_tools, key=lambda x: -x['score'])[:3]

    alt_cards = ''
    for alt in alt_tools:
        asc  = alt['score']
        abg  = 'var(--green-d)' if asc >= 88 else 'var(--cyan-d)'
        abdr = 'var(--green-g)' if asc >= 88 else 'var(--cyan-g)'
        acol = 'var(--green)'   if asc >= 88 else 'var(--cyan)'
        comp_link = ''
        for comp in COMPARISONS:
            if (comp['tool_a'] == slug and comp['tool_b'] == alt['slug']) or \
               (comp['tool_b'] == slug and comp['tool_a'] == alt['slug']):
                comp_link = f'<a href="/compare/{comp["slug"]}" class="alt-link">Compare \u2192</a>'
                break
        alt_cards += f"""<div class="alt-card">
          <div class="alt-score" style="background:{abg};border:1px solid {abdr};color:{acol}">{asc}/100</div>
          <div class="alt-info">
            <div class="alt-name">{alt['name']}</div>
            <div class="alt-desc">{alt['tagline']}</div>
          </div>
          <div class="alt-links">
            <a href="/tool/{alt['slug']}" class="alt-link">Full review \u2192</a>
            {comp_link}
          </div>
        </div>"""

    alts_html = f"""
    <section class="alts-section rv" aria-labelledby="alts-heading">
      <h2 class="review-section-hdr" id="alts-heading">Alternatives to {name}</h2>
      {alt_cards}
    </section>"""

    bottom_cta = f"""
    <section class="bottom-cta rv">
      <div class="bottom-cta-text">
        <div class="bottom-cta-name">Ready to try {name}?</div>
        <div class="bottom-cta-sub">
          {sc}/100 MFWAI score \u00b7 Starts at {t['starting_price']}
          {' \u00b7 Free tier available' if t.get('free_tier') else ''}
          {' \u00b7 ' + str(t.get('trial_days','')) + '-day free trial' if t.get('free_trial') else ''}
        </div>
      </div>
      <a href="{t['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener noreferrer"
         class="btn-td-cta" style="width:auto;flex-shrink:0" aria-label="Try {name} \u2014 opens in new tab">
        Try {name}
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
          <polyline points="15,3 21,3 21,9"/>
          <line x1="10" y1="14" x2="21" y2="3"/>
        </svg>
      </a>
    </section>"""

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
        {header}
        {verdict_box}
        {pros_cons}
        {pricing_section}
        {who_section}
        {faq_html}
        {alts_html}
        {bottom_cta}
      </div>
    </div>
    <div class="page">
      <section class="sec" aria-labelledby="related-heading">
        <div class="sec-top">
          <div><div class="sec-eyebrow">You might also like</div>
          <h2 class="sec-h2" id="related-heading">Related <em>tools</em></h2></div>
        </div>
        <div class="tools-grid">{rel_cards}</div>
      </section>
    </div>"""

    return render(
        title=tool_meta_title(t),
        desc=f'{t["name"]}: {t["tagline"][:100]}. Score: {sc}/100. From {t["starting_price"]}. Read the full review.',
        content=content,
        schema=tool_schema(t),
        schema2=faq_sd,
        bcs=bc_schema([('Home', '/'), ('Tools', '/tools'), (t['name'], f'/tool/{slug}')]),
        og_type='article')


@app.route('/compare')
@cache.cached(timeout=600)
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
    </div>
    <div class="page">
      <div style="background:var(--cyan-d);border:1px solid var(--cyan-g);border-radius:var(--r3);padding:18px 22px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap">
        <div>
          <div style="font-family:var(--font-display);font-size:1rem;font-weight:700;color:var(--ink);letter-spacing:-.02em">Can't find your matchup?</div>
          <div style="font-size:.86rem;color:var(--ink3);margin-top:3px">Compare any two tools from our full collection.</div>
        </div>
        <a href="/compare/custom" class="btn-primary" style="flex-shrink:0">Custom Compare →</a>
      </div>
      <div class="comp-grid">{cards}</div>
    </div>"""
    return render(
        'Compare AI Tools Side by Side 2026 | MFWAI',
        f'Head-to-head AI tool comparisons with clear verdicts. {len(COMPARISONS)} matchups reviewed independently.',
        content,
        bcs=bc_schema([('Home', '/'), ('Compare', '/compare')]))


@app.route('/compare/<slug>')
@cache.cached(timeout=1800)
def compare_detail(slug):
    if slug == 'custom':
        return compare_custom()
    c = get_comp(slug)
    if not c: abort(404)
    ta = get_tool(c['tool_a'])
    tb = get_tool(c['tool_b'])
    if not ta or not tb: abort(404)
    winner = get_tool(c['winner_slug']) if c.get('winner_slug') else None

    def cd_card(t, is_winner):
        sc     = t['score']
        sc_col = score_color(sc)
        verdict = c['verdict_a'] if t['slug'] == c['tool_a'] else c['verdict_b']
        win_badge  = '<div class="cd-winner-tag">&#10003; Winner</div>' if is_winner else ''
        card_class = 'cd-card winner' if is_winner else 'cd-card'
        free_tier_cell  = '<span class="tick">&#10003;</span>' if t.get('free_tier') else '<span class="cross">&#10007;</span>'
        if t.get('free_trial'):
            free_trial_cell = '<span class="tick">&#10003; ' + str(t.get('trial_days','')) + 'd</span>'
        else:
            free_trial_cell = '<span class="cross">&#10007;</span>'
        rows = (
            '<tr><td>MFWAI Score</td><td style="color:' + sc_col + ';font-family:var(--font-mono);font-weight:600">' + str(sc) + '/100</td></tr>'
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
        winner_name  = winner['name'] if winner else 'Our verdict'
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
        title=comp_meta_title(ta['name'], tb['name']),
        desc=c.get('meta_description', c['description'])[:155],
        content=content,
        schema=comparison_schema(ta, tb, c),
        bcs=bc_schema([('Home', '/'), ('Compare', '/compare'), (c['headline'], f'/compare/{slug}')]),
        og_type='article')


@app.route('/compare/custom')
def compare_custom():
    slug_a = request.args.get('a', '')
    slug_b = request.args.get('b', '')
    ta = get_tool(slug_a) if slug_a else None
    tb = get_tool(slug_b) if slug_b else None
    if not ta or not tb:
        ta, tb = TOOLS[0], TOOLS[1]
        slug_a, slug_b = ta['slug'], tb['slug']
    verdict = generate_comparison_verdict(ta, tb)
    sorted_tools = sorted(TOOLS, key=lambda t: t['name'])
    content = build_custom_compare_page(sorted_tools, ta, tb, verdict, slug_a, slug_b)
    ttl = f'{ta["name"]} vs {tb["name"]} — Compare AI Tools | Moving Forward With AI'
    dsc = f'Side-by-side comparison of {ta["name"]} and {tb["name"]}. Scores, pricing, pros, cons and a clear verdict.'
    return render(title=ttl, desc=dsc, content=content)


@app.route('/blog')
@cache.cached(timeout=600)
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
        'AI Tool Guides for Freelancers & Marketers 2026 | MFWAI',
        'In-depth guides, comparisons and how-tos for AI tools. Updated weekly.',
        content,
        bcs=bc_schema([('Home', '/'), ('Guides', '/blog')]))


@app.route('/blog/<slug>')
@cache.cached(timeout=3600)
def blog_detail(slug):
    post = BLOG_POSTS.get(slug)
    if not post: abort(404)
    dt      = datetime.datetime.strptime(post['date'], '%Y-%m-%d').strftime('%d %B %Y')
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

    faq_pairs = extract_faq_from_blog(post)
    faq_sd = faq_schema(faq_pairs) if faq_pairs else ''

    return render(
        title=blog_meta_title(post),
        desc=post.get('meta_description', post.get('description', ''))[:155],
        content=content,
        schema=faq_sd,
        bcs=bc_schema([('Home', '/'), ('Guides', '/blog'), (post['title'], f'/blog/{slug}')]),
        og_type='article')


@app.route('/category/<cat_slug>')
@cache.cached(timeout=900)
def category(cat_slug):
    tools = [t for t in TOOLS if slugify(t['category']) == cat_slug]
    if not tools: abort(404)
    cat_name = tools[0]['category']
    cards    = '\n'.join(tool_card(t) for t in tools)
    content  = f"""
    {breadcrumb_html([('Home','/'),('Tools','/tools'),(cat_name,f'/category/{cat_slug}')])}
    <div class="page" style="padding-top:32px;padding-bottom:28px">
      <div class="sec-eyebrow">{cat_name} · {len(tools)} tools</div>
      <h1 style="font-family:var(--font-display);font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.05em;color:var(--ink);line-height:1;margin-top:8px">
        Best <em style="color:var(--cyan);font-style:normal">{cat_name}</em> tools
      </h1>
    </div>
    <div class="page"><div class="tools-grid">{cards}</div></div>"""
    return render(
        f'Best {cat_name} AI Tools 2026 | MFWAI',
        f'Independent reviews of the best {cat_name.lower()} AI tools in 2026. Transparent scores and honest verdicts.',
        content,
        schema=itemlist_schema(tools, f"{cat_name} AI Tools"),
        bcs=bc_schema([('Home', '/'), ('Tools', '/tools'), (cat_name, f'/category/{cat_slug}')]))


@app.route('/affiliate-disclosure')
@cache.cached(timeout=3600)
def affiliate_disclosure():
    content = """<div class="legal-wrap">
      <h1>Affiliate Disclosure</h1>
      <div class="legal-note"><p><strong>Last updated:</strong> February 2026</p>
        <p>Moving Forward With AI earns affiliate commissions from some tools reviewed on this site.</p></div>
      <h2>Our editorial independence</h2>
      <p>Tools are scored and ranked on merit alone. We do not accept payment for reviews, rankings, or placement.</p>
      <h2>Contact</h2>
      <p>Questions? <a href="mailto:hello@movingforwardwithai.com" style="color:var(--cyan)">hello@movingforwardwithai.com</a></p>
    </div>"""
    return render('Affiliate Disclosure — Moving Forward With AI', 'How MFWAI earns commissions while maintaining editorial independence.', content,
                  bcs=bc_schema([('Home', '/'), ('Affiliate Disclosure', '/affiliate-disclosure')]))


@app.route('/privacy')
@cache.cached(timeout=3600)
def privacy():
    content = """<div class="legal-wrap">
      <h1>Privacy Policy</h1>
      <div class="legal-note"><p><strong>Last updated:</strong> February 2026</p></div>
      <h2>Information we collect</h2>
      <p>We collect minimal data via cookies and analytics. We do not collect personal information unless you contact us or subscribe to our newsletter.</p>
      <h2>Cookies</h2>
      <p>Essential cookies for functionality and analytics cookies (with consent). Affiliate links use tracking cookies from third-party services.</p>
      <h2>Your rights</h2>
      <p>Contact <a href="mailto:hello@movingforwardwithai.com" style="color:var(--cyan)">hello@movingforwardwithai.com</a> to exercise data rights.</p>
    </div>"""
    return render('Privacy Policy — Moving Forward With AI', 'Privacy policy for Moving Forward With AI.', content,
                  bcs=bc_schema([('Home', '/'), ('Privacy Policy', '/privacy')]))


@app.route('/terms')
@cache.cached(timeout=3600)
def terms():
    content = """<div class="legal-wrap">
      <h1>Terms of Service</h1>
      <div class="legal-note"><p>By using movingforwardwithai.com you accept these terms.</p></div>
      <h2>Accuracy</h2>
      <p>Prices verified at time of writing. Always confirm on the tool's official website before purchasing.</p>
      <h2>Affiliate links</h2>
      <p>See our <a href="/affiliate-disclosure" style="color:var(--cyan)">Affiliate Disclosure</a>.</p>
    </div>"""
    return render('Terms of Service — Moving Forward With AI', 'Terms for Moving Forward With AI.', content,
                  bcs=bc_schema([('Home', '/'), ('Terms', '/terms')]))


@app.route('/api/tools')
def api_tools():
    return jsonify({'tools': [{
        'slug': t['slug'], 'name': t['name'], 'category': t['category'],
        'tagline': t['tagline'], 'score': t['score'],
        'starting_price': t['starting_price'], 'tags': t.get('tags', []),
        'featured': t.get('featured', False)} for t in TOOLS]})


@app.route('/api/cache-clear')
def cache_clear():
    cache.clear()
    return jsonify({'status': 'ok', 'message': 'Cache cleared successfully'})


@app.route('/robots.txt')
@cache.cached(timeout=3600)
def robots():
    return Response(
        f'User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {SITE_URL}/sitemap.xml\n',
        mimetype='text/plain')


@app.route('/sitemap.xml')
@cache.cached(timeout=3600)
def sitemap():
    today = datetime.date.today().isoformat()
    urls  = [
        (SITE_URL + '/',               today, '1.0', 'weekly'),
        (SITE_URL + '/tools',          today, '0.9', 'weekly'),
        (SITE_URL + '/tool-finder',    today, '0.8', 'weekly'),
        (SITE_URL + '/compare',        today, '0.9', 'weekly'),
        (SITE_URL + '/blog',           today, '0.8', 'weekly'),
    ]
    for t in TOOLS:
        urls.append((f'{SITE_URL}/tool/{t["slug"]}',    t.get('date_added', today), '0.8', 'monthly'))
    for r in ROLES:
        urls.append((f'{SITE_URL}/for/{r["slug"]}',     today, '0.8', 'weekly'))
    for c in COMPARISONS:
        urls.append((f'{SITE_URL}/compare/{c["slug"]}', c.get('date', today), '0.8', 'monthly'))
    for slug, post in BLOG_POSTS.items():
        urls.append((f'{SITE_URL}/blog/{slug}',         post.get('date', today), '0.7', 'monthly'))
    cats = list({slugify(t['category']) for t in TOOLS})
    for cat in cats:
        urls.append((f'{SITE_URL}/category/{cat}',      today, '0.6', 'monthly'))
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, lm, pri, cf in sorted(urls):
        xml += f'  <url><loc>{url}</loc><lastmod>{lm}</lastmod><changefreq>{cf}</changefreq><priority>{pri}</priority></url>\n'
    return Response(xml + '</urlset>', mimetype='application/xml')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
