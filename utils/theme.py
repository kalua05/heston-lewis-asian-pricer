"""Design system for the SM Energy Pricer.

One file owns everything visual: design tokens, the global stylesheet, small HTML
components (page header, KPI tiles, panels, badges, empty states) and the Plotly
template.  Pages stay declarative and the whole app keeps a single palette.

Colours are published as CSS custom properties so the stylesheet and the Plotly
template cannot drift apart.
"""
from __future__ import annotations

import html as _html

import plotly.graph_objects as go
import plotly.io as pio

# --------------------------------------------------------------------------- tokens
TOKENS = {
    "bg": "#080C14",
    "surface": "#0F1626",
    "surface_2": "#151E30",
    "surface_3": "#1B2639",
    "border": "rgba(148,163,184,.16)",
    "border_strong": "rgba(148,163,184,.30)",
    "text": "#E8EEF9",
    "text_dim": "#B6C4D8",
    "muted": "#8194AC",
    "accent": "#2DD4BF",
    "accent_dim": "rgba(45,212,191,.14)",
    "info": "#60A5FA",
    "info_dim": "rgba(96,165,250,.14)",
    "warn": "#FBBF24",
    "warn_dim": "rgba(251,191,36,.14)",
    "danger": "#F87171",
    "danger_dim": "rgba(248,113,113,.14)",
    "purple": "#A78BFA",
    "radius": "14px",
    "radius_sm": "10px",
    "shadow": "0 8px 24px rgba(0,0,0,.28)",
    "font": "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    "mono": "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace",
}

ACCENT = TOKENS["accent"]
COLORWAY = [TOKENS["accent"], TOKENS["info"], TOKENS["warn"], TOKENS["purple"], "#4ADE80", TOKENS["danger"]]

_VARS = "\n".join(f"  --{k.replace('_', '-')}: {v};" for k, v in TOKENS.items())

_STYLE = r"""
* { box-sizing: border-box; }
html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family: var(--font); }
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(900px 480px at 88% -8%, rgba(96,165,250,.10), transparent 62%),
    radial-gradient(760px 420px at -6% 0%, rgba(45,212,191,.08), transparent 58%),
    var(--bg);
  color: var(--text);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: .6rem; }
.block-container { padding: 1.6rem 2rem 4rem; max-width: 1260px; }
h1, h2, h3, h4 { color: var(--text); letter-spacing: -.015em; }
h1 { font-weight: 750 !important; font-size: 1.9rem !important; }
h2 { font-weight: 700 !important; font-size: 1.25rem !important; margin-top: 1.4rem !important; }
h3 { font-weight: 650 !important; font-size: 1.02rem !important; }
p, li, label, span { color: var(--text-dim); }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code, kbd, .gsq-mono { font-family: var(--mono); font-size: .86em; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 6px; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0C1322 0%, #080C14 100%);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebarNav"] { padding-top: .2rem; }
[data-testid="stSidebarNav"] ul { gap: .1rem; }
[data-testid="stSidebarNav"] a { border-radius: var(--radius-sm); padding: .28rem .5rem; }
[data-testid="stSidebarNav"] a:hover { background: rgba(148,163,184,.10); }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: var(--accent-dim); }
[data-testid="stSidebarNav"] a[aria-current="page"] span { color: var(--text) !important; font-weight: 600; }
[data-testid="stSidebarNav"] + div hr { margin: .6rem 0; }

.gsq-brand { display: flex; align-items: center; gap: .65rem; padding: .2rem 0 .9rem; }
.gsq-brand__mark {
  width: 34px; height: 34px; border-radius: 9px; flex: 0 0 auto;
  display: grid; place-items: center; font-weight: 800; font-size: .82rem; letter-spacing: -.02em;
  color: #04211C; background: linear-gradient(135deg, var(--accent), #5EEAD4);
  box-shadow: 0 4px 14px rgba(45,212,191,.28);
}
.gsq-brand__name { font-size: .92rem; font-weight: 700; color: var(--text); line-height: 1.15; }
.gsq-brand__sub { font-size: .68rem; color: var(--muted); letter-spacing: .08em; text-transform: uppercase; }
.gsq-sidefoot { font-size: .68rem; line-height: 1.5; color: var(--muted); border-top: 1px solid var(--border); padding-top: .7rem; margin-top: .4rem; }
.gsq-sidefoot b { color: var(--text-dim); font-weight: 600; }

/* ---------- page header ---------- */
.gsq-head {
  display: flex; flex-wrap: wrap; gap: 1rem 1.4rem; align-items: flex-end; justify-content: space-between;
  padding: 0 0 1rem; margin-bottom: 1.1rem; border-bottom: 1px solid var(--border);
}
.gsq-head__main { min-width: min(100%, 30rem); }
.gsq-kicker { font-size: .68rem; letter-spacing: .13em; text-transform: uppercase; color: var(--accent); font-weight: 700; margin-bottom: .35rem; }
.gsq-head h1 { margin: 0 0 .3rem; }
.gsq-sub { margin: 0; font-size: .9rem; line-height: 1.5; color: var(--muted); max-width: 52rem; }
.gsq-head__meta { display: flex; flex-wrap: wrap; gap: .4rem; align-items: center; justify-content: flex-end; }

/* ---------- badges ---------- */
.gsq-badge {
  display: inline-flex; align-items: center; gap: .3rem; padding: .18rem .55rem; border-radius: 999px;
  font-size: .68rem; font-weight: 650; letter-spacing: .02em; white-space: nowrap;
  border: 1px solid var(--border); background: rgba(148,163,184,.10); color: var(--text-dim);
}
.gsq-badge--accent { background: var(--accent-dim); color: var(--accent); border-color: rgba(45,212,191,.28); }
.gsq-badge--info { background: var(--info-dim); color: var(--info); border-color: rgba(96,165,250,.28); }
.gsq-badge--warn { background: var(--warn-dim); color: var(--warn); border-color: rgba(251,191,36,.28); }
.gsq-badge--danger { background: var(--danger-dim); color: var(--danger); border-color: rgba(248,113,113,.28); }
.gsq-badge--ok { background: rgba(74,222,128,.13); color: #4ADE80; border-color: rgba(74,222,128,.28); }

/* ---------- KPI tiles ---------- */
.gsq-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(11.5rem, 1fr)); gap: .75rem; margin: .2rem 0 1rem; }
.gsq-kpi {
  background: linear-gradient(180deg, var(--surface-2), var(--surface)); border: 1px solid var(--border);
  border-radius: var(--radius); padding: .85rem 1rem; box-shadow: var(--shadow); transition: border-color .15s ease, transform .15s ease;
}
.gsq-kpi:hover { border-color: var(--border-strong); transform: translateY(-1px); }
.gsq-kpi__l { font-size: .68rem; font-weight: 650; letter-spacing: .09em; text-transform: uppercase; color: var(--muted); }
.gsq-kpi__v { font-size: 1.55rem; font-weight: 720; color: var(--text); margin: .25rem 0 .1rem; font-variant-numeric: tabular-nums; line-height: 1.15; }
.gsq-kpi__s { font-size: .74rem; color: var(--muted); line-height: 1.4; }
.gsq-kpi__s .up { color: #4ADE80; font-weight: 600; }
.gsq-kpi__s .down { color: var(--danger); font-weight: 600; }
.gsq-t-accent { color: var(--accent) !important; }
.gsq-t-warn { color: var(--warn) !important; }
.gsq-t-danger { color: var(--danger) !important; }
.gsq-t-info { color: var(--info) !important; }

/* ---------- panels ---------- */
.gsq-panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.15rem; height: 100%; }
.gsq-panel__head { display: flex; align-items: center; justify-content: space-between; gap: .6rem; margin-bottom: .5rem; }
.gsq-panel__t { font-size: .95rem; font-weight: 650; color: var(--text); margin: 0; }
.gsq-panel p, .gsq-panel li { font-size: .86rem; line-height: 1.55; }

/* ---------- callouts / states ---------- */
.gsq-callout {
  border-left: 3px solid var(--info); background: var(--info-dim); border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: .7rem .9rem; font-size: .85rem; line-height: 1.55; color: var(--text-dim); margin: .8rem 0;
}
.gsq-callout--warn { border-color: var(--warn); background: var(--warn-dim); }
.gsq-callout--danger { border-color: var(--danger); background: var(--danger-dim); }
.gsq-callout--ok { border-color: #4ADE80; background: rgba(74,222,128,.10); }
.gsq-callout b { color: var(--text); }
.gsq-empty {
  border: 1px dashed var(--border-strong); border-radius: var(--radius); padding: 1.6rem 1.2rem; text-align: center; background: rgba(148,163,184,.04);
}
.gsq-empty__t { font-weight: 650; color: var(--text); margin-bottom: .25rem; }
.gsq-empty__x { font-size: .84rem; color: var(--muted); line-height: 1.5; }

/* ---------- misc stock widgets ---------- */
div[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: .7rem .9rem; }
div[data-testid="stMetricLabel"] p { font-size: .72rem !important; letter-spacing: .06em; text-transform: uppercase; color: var(--muted) !important; }
div[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; font-size: 1.4rem !important; }
.stTabs [data-baseweb="tab-list"] { gap: .2rem; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { border-radius: var(--radius-sm) var(--radius-sm) 0 0; padding: .45rem .9rem; font-size: .85rem; }
.stTabs [aria-selected="true"] { background: rgba(148,163,184,.08); }
.stButton > button, .stDownloadButton > button { border-radius: var(--radius-sm); font-weight: 600; border: 1px solid var(--border-strong); }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--accent); color: var(--accent); }
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: var(--radius-sm); background: rgba(148,163,184,.03); }
[data-testid="stDataFrame"], [data-testid="stTable"] { border-radius: var(--radius-sm); overflow: hidden; border: 1px solid var(--border); }
[data-testid="stFileUploaderDropzone"] { border-radius: var(--radius-sm); border-color: var(--border-strong); }
hr { border-color: var(--border) !important; margin: 1.6rem 0 !important; }
.gsq-cap { font-size: .72rem; color: var(--muted); line-height: 1.5; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }

@media (max-width: 900px) {
  .block-container { padding: 1.1rem 1rem 3rem; }
  .gsq-head { align-items: flex-start; }
  .gsq-head__meta { justify-content: flex-start; }
  .gsq-kpi__v { font-size: 1.35rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; animation: none !important; }
}
@media print {
  [data-testid="stSidebar"], [data-testid="stHeader"], .gsq-head__meta { display: none !important; }
  .block-container { max-width: 100%; padding: 0; }
}
"""

CSS = f"<style>:root{{\n{_VARS}\n}}{_STYLE}</style>"


# --------------------------------------------------------------------------- helpers
def esc(value) -> str:
    """Escape any value for safe insertion into HTML."""
    return _html.escape(str(value), quote=True)


def badge(text, tone: str = "neutral", icon: str = "") -> str:
    tone = tone if tone in {"accent", "info", "warn", "danger", "ok"} else "neutral"
    return f"<span class='gsq-badge gsq-badge--{tone}'>{esc(icon)}{esc(text)}</span>"


def page_header(title, subtitle: str = "", kicker: str = "", meta=()) -> str:
    """Standard page header: kicker, h1, subtitle and a row of status badges."""
    m = "".join(meta)
    kick = f"<div class='gsq-kicker'>{esc(kicker)}</div>" if kicker else ""
    sub = f"<p class='gsq-sub'>{esc(subtitle)}</p>" if subtitle else ""
    return (
        "<header class='gsq-head' role='banner'>"
        f"<div class='gsq-head__main'>{kick}<h1>{esc(title)}</h1>{sub}</div>"
        f"<div class='gsq-head__meta'>{m}</div></header>"
    )


def kpi(label, value, sub: str = "", tone: str = "") -> str:
    """Single KPI tile. ``sub`` may contain inline HTML (controlled by the page)."""
    cls = f" gsq-t-{tone}" if tone else ""
    return (
        f"<div class='gsq-kpi' role='group' aria-label='{esc(label)}'>"
        f"<div class='gsq-kpi__l'>{esc(label)}</div>"
        f"<div class='gsq-kpi__v{cls}'>{esc(value)}</div>"
        f"<div class='gsq-kpi__s'>{sub}</div></div>"
    )


def kpi_row(items) -> str:
    """``items`` = iterable of (label, value, sub) or (label, value, sub, tone)."""
    tiles = []
    for item in items:
        label, value, sub = item[0], item[1], (item[2] if len(item) > 2 else "")
        tone = item[3] if len(item) > 3 else ""
        tiles.append(kpi(label, value, sub, tone))
    return "<div class='gsq-grid'>" + "".join(tiles) + "</div>"


def panel(title, body_html: str, right: str = "") -> str:
    r = f"<div>{right}</div>" if right else ""
    return (
        f"<section class='gsq-panel'><div class='gsq-panel__head'>"
        f"<h3 class='gsq-panel__t'>{esc(title)}</h3>{r}</div><div>{body_html}</div></section>"
    )


def callout(text_html: str, tone: str = "info", title: str = "") -> str:
    cls = {"warn": " gsq-callout--warn", "danger": " gsq-callout--danger", "ok": " gsq-callout--ok"}.get(tone, "")
    head = f"<b>{esc(title)}</b> " if title else ""
    return f"<div class='gsq-callout{cls}' role='note'>{head}{text_html}</div>"


def empty_state(title, text, hint: str = "") -> str:
    hint_html = f"<div class='gsq-cap' style='margin-top:.5rem'>{esc(hint)}</div>" if hint else ""
    return (
        "<div class='gsq-empty' role='status'>"
        f"<div class='gsq-empty__t'>{esc(title)}</div>"
        f"<div class='gsq-empty__x'>{esc(text)}</div>{hint_html}</div>"
    )


def caption(text) -> str:
    return f"<div class='gsq-cap'>{esc(text)}</div>"


# --------------------------------------------------------------------------- plotly
def _template() -> go.layout.Template:
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family="Inter, ui-sans-serif, system-ui, sans-serif", color=TOKENS["text"], size=12),
        colorway=COLORWAY,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(21,30,48,.55)",
        xaxis=dict(gridcolor="rgba(148,163,184,.10)", zerolinecolor="rgba(148,163,184,.22)", linecolor="rgba(148,163,184,.22)"),
        yaxis=dict(gridcolor="rgba(148,163,184,.10)", zerolinecolor="rgba(148,163,184,.22)", linecolor="rgba(148,163,184,.22)"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=52, r=18, t=54, b=44),
        title=dict(font=dict(size=14), x=0, xanchor="left"),
        hoverlabel=dict(bgcolor=TOKENS["surface_3"], bordercolor=TOKENS["border_strong"], font=dict(color=TOKENS["text"])),
        coloraxis=dict(colorbar=dict(outlinewidth=0, tickfont=dict(size=10))),
    )
    return t


pio.templates["gsq"] = _template()
pio.templates.default = "gsq"
