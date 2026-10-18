"""The design system's building blocks (styles in system.css). Every page is built with them and listed in
core.SYSTEM_PAGES.
Grid rules are checked here, at build time: a row of cards never mixes cards with and without a visual,
and never ends on an orphan row."""
import os, re, unicodedata, html as _html
import core
from core import *

CAP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "img", "captures", "en")
RHYTHM = {"t": "s-t", "n": "s", "a": "s-a"}

def sec(inner, rhythm="n", id_="", cls="", width="", flush=False):
    """A section: rhythm t(ight) / n(ormal) / a(mple), container standard / wide / read."""
    if width == "read": inner, width = f'<div class="read">{inner}</div>', ""   # long text: narrow, on the same left edge as the rest
    if width == "read-center": width = "read"   # a centred page (/100): the reading column is centred too
    c = "c" + (f" c-{width}" if width else "")
    k = " ".join(x for x in (RHYTHM[rhythm], "s-flush-top" if flush else "", cls) if x)
    return f'<section class="{k}"{f" id=\"{id_}\"" if id_ else ""}><div class="{c}">{inner}</div></section>'

def head(t, kick=None, title=None, lead=None, links="", center=False, level=2, cls=""):
    k = f'<span class="eyebrow">{t(kick)}</span>' if kick else ""
    h = f'<h{level}>{t(title)}</h{level}>' if title else ""
    p = f'<p class="lead">{t(lead)}</p>' if lead else ""
    l = f'<div class="links">{links}</div>' if links else ""
    return f'<div class="head{" center" if center else ""}{" " + cls if cls else ""}">{k}{h}{p}{l}</div>'

def btn(label, url, kind="primary", lg=False, attrs=""):
    return f'<a class="btn btn-{kind}{" btn-lg" if lg else ""}" href="{url}"{" " + attrs if attrs else ""}>{label}</a>'

def go(lang, t, page, label, anchor=""):
    return f'<a class="go" href="{href(lang, page)}{anchor}">{t(label)} <span aria-hidden="true">→</span></a>'

def bullets(t, items):
    return '<ul class="list">' + "".join(f"<li>{t(x)}</li>" for x in items) + "</ul>"

# ---------------------------------------------------------------- captures
def _has(name): return os.path.exists(os.path.join(CAP_DIR, name))

def ss600(src, size="300px"):
    """srcset for a phone capture shown at most ~320 px wide: its 600-px copy is enough (2x screens), the 900-px original for 3x."""
    if not src.startswith("/img/captures/"): return ""
    n = src[len("/img/captures/"):]
    if not _has(n[:-5] + "-600.webp"): return ""
    return f' srcset="/img/captures/{n[:-5]}-600.webp 600w, {src} 900w" sizes="{size}"'

def _img_d(name, alt, sizes, eager=False):
    base = name[:-5]
    ss = f' srcset="/img/captures/{base}-1200.webp 1200w, /img/captures/{name} 2400w" sizes="{sizes}"' if _has(base + "-1200.webp") else ""
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return f'<img src="/img/captures/{name}"{ss} width="2880" height="1800" alt="{_html.escape(alt)}" {load} decoding="async">'

def frame_d(name, alt, m=None, sizes="(max-width: 1067px) 92vw, 700px", cap=True, t=None, cls="reveal"):
    """A computer capture. On phones it becomes the phone capture `m`: a desktop screen shrunk to 300 px can't be read."""
    img = _img_d(name, alt, sizes)
    if m:
        mss = ss600(f"/img/captures/{m}") or f' srcset="/img/captures/{m}"'
        img = f'<picture><source media="(max-width: 743px)"{mss}>{img}</picture>'
    c = f'<figcaption class="cap">{t(SAMPLE)}</figcaption>' if cap and t else ""
    return f'<figure class="fr fr-d{" has-m" if m else ""} {cls}"><div class="scr">{img}</div>{c}</figure>'

def frame_p(name, alt, t=None, video=None, cap=True, width=None, cls="reveal", eager=False, sizes="320px"):
    """A phone. With `video`, the capture `name` is its first frame and the video fades in once it plays."""
    st = f' style="--pw:{width}px"' if width else ""
    src = name if name.startswith("/") else f"/img/captures/{name}"   # a path in /img works too (older phone captures)
    if video:
        media = (f'<img class="vfb" src="{src}"{ss600(src, "320px")} width="900" height="1948" alt="" aria-hidden="true" loading="lazy" decoding="async">'
                 f'<video muted loop playsinline preload="none" data-auto aria-label="{_html.escape(alt)}"><source src="/img/captures/{video}" type="video/mp4"></video>')
    else:
        load = 'fetchpriority="high"' if eager else 'loading="lazy"'
        media = f'<img src="{src}"{ss600(src, sizes)} width="900" height="1948" alt="{_html.escape(alt)}" {load} decoding="async">'
    c = f'<figcaption class="cap">{t(SAMPLE)}</figcaption>' if cap and t else ""
    return f'<figure class="fr fr-p {cls}"{st}><div class="scr">{media}</div>{c}</figure>'

def phone_img(src, alt, pos="50% 0%"):
    """A phone capture cropped for a card (the top of the screen unless `pos` says otherwise)."""
    return f'<img src="{src}"{ss600(src)} width="900" height="1948" alt="{_html.escape(alt)}" loading="lazy" decoding="async" style="object-position:{pos}">'

# ---------------------------------------------------------------- cards
class Card:
    def __init__(self, kind, markup): self.kind, self.markup = kind, markup

def card(t, title, text, icon=None, more="", kick=None, id_="", items=None, cls="", url=None):
    """A text card; with `url`, the whole card is the link (`more` is then a label, never a link)."""
    i = f'<span class="ico" aria-hidden="true">{ico(I[icon])}</span>' if icon else ""
    k = f'<span class="eyebrow">{t(kick)}</span>' if kick else ""
    d = f' id="{id_}"' if id_ else ""
    p = f"<p>{t(text)}</p>" if text else ""
    tag, h = ("a", f' href="{url}"') if url else ("article", "")
    c = " ".join(x for x in ("card", "lift" if url else "", cls) if x)
    m = (f'<div class="more"><span class="go">{t(more)} <span aria-hidden="true">→</span></span></div>' if url else f'<div class="more">{more}</div>') if more else ""
    return Card("text", f'<{tag} class="{c}"{d}{h}>{i}{k}<h3>{t(title)}</h3>{p}{bullets(t, items) if items else ""}{m}</{tag}>')

def card_media(t, title, text, media, crop=False, more="", kick=None, items=None, id_=""):
    """A card with a visual on top; every card of the row shares the visual's ratio."""
    k = f'<span class="eyebrow">{t(kick)}</span>' if kick else ""
    l = bullets(t, items) if items else ""
    i = f' id="{id_}"' if id_ else ""
    return Card("media" + ("-crop" if crop else ""), f'<article class="card media{" phone-crop" if crop else ""}"{i}><div class="cm">{media}</div>'
                f'<div class="ct">{k}<h3>{t(title)}</h3><p>{t(text)}</p>{l}{f"<div class=more>{more}</div>" if more else ""}</div></article>')

def card_side(t, title, text, media):
    return Card("side", f'<article class="card side"><div class="ct"><h3>{t(title)}</h3><p>{t(text)}</p></div><div class="cm">{media}</div></article>')

def cards(items, cols=3, cls="stagger"):
    """A row of cards. Build-time checks: one structure per row, no orphan row."""
    kinds = {c.kind for c in items}
    if len(kinds) != 1: raise ValueError(f"grid rule: a row mixes cards {sorted(kinds)}")
    if len(items) % cols: raise ValueError(f"grid rule: {len(items)} cards in {cols} columns leave an orphan row")
    return f'<div class="cards c{cols} {cls}">' + "".join(c.markup for c in items) + "</div>"

def tiles(t, items, cls="trust stagger"):
    return f'<div class="{cls}">' + "".join(f'<div class="tile"><span class="ico" aria-hidden="true">{ico(I[k])}</span><div><b>{t(a)}</b>{f"<span>{t(b)}</span>" if b else ""}</div></div>' for k, a, b in items) + "</div>"

# ---------------------------------------------------------------- sections
def split(t, kick, title, lead, items, media, flip=False, id_="", more="", phone=False, rhythm="n"):
    copy = (f'<div class="copy">{head(t, kick, title, lead)}' + (bullets(t, items) if items else "") + more + "</div>")
    return sec(f'<div class="split{" flip" if flip else ""}{" phone-media" if phone else ""}">{copy}<div>{media}</div></div>', rhythm, id_)

def rings(t):
    """The day's three rings (Plan, Execution, Review): site.js closes them one by one as the block scrolls through
    the screen, then shows « Day swept ». Without the script, or with reduced motion, they are already closed."""
    names = [T("Plan","Plan","Plan"), T("Execution","Exécution","Ejecución"), T("Review","Revue","Revisión")]
    ring = lambda n: (f'<div class="ring"><svg viewBox="0 0 64 64" aria-hidden="true"><circle class="tr" cx="32" cy="32" r="27"/>'
                      f'<circle class="fg" cx="32" cy="32" r="27" pathLength="100"/><path class="ck" d="M22 33l7 7 13-15" pathLength="1"/></svg><span>{t(n)}</span></div>')
    return (f'<div class="rings" data-rings>{"".join(ring(n) for n in names)}'
            f'<span class="swept">{t(T("Day swept","Journée balayée","Día barrido"))}</span></div>')

def stats(items, caption="", note=""):
    """Key numbers: (label, value, small note)."""
    dl = "".join(f'<div class="stat"><dt>{a}</dt><dd>{b}{f"<small>{c}</small>" if c else ""}</dd></div>' for a, b, c in items)
    cap = f'<div class="stats-cap"><b>{caption}</b><span>{note}</span></div>' if caption else ""
    return f'{cap}<dl class="stats reveal" style="--n:{len(items)}">{dl}</dl>'

def qa(t, items, more=""):
    """Questions: two columns on large screens (the first half, then the second: the order stays the same on phones)."""
    h = (len(items) + 1) // 2
    cols = "".join('<div class="qa-col">' + "".join(faq_item(t, q, a) for q, a in part) + "</div>" for part in (items[:h], items[h:]) if part)
    return f'<div class="qa{" qa2" if len(items) > 1 else ""}">' + cols + (f'<p class="more-q">{more}</p>' if more else "") + "</div>"

def band(title, text, cta):
    """A call to action after a table: one line, one button."""
    return f'<div class="band reveal" style="margin-top:40px"><div><h2>{title}</h2><p data-nolinks>{text}</p></div><div class="cta-row">{cta}</div></div>'

def state(text):
    return f'<div class="state reveal"><span class="dot" aria-hidden="true"></span><p>{text}</p></div>'

def final(lang, t, title=None, note=None, label=None):
    """The site's closing block: one promise, one action. Only /100 keeps its own words (title, note, button)."""
    return (f'<section class="final s-a"><div class="c c-wide"><div class="stage reveal">'
            f'<span class="mark" aria-hidden="true">{ANIM_MARK}</span>'
            f'<h2>{words(t(title or T("Your edge, finally in one place.","Ton edge, enfin au même endroit.","Tu edge, por fin en un solo lugar.")))}</h2>'
            f'<div class="cta-row">{btn(label or t(CREATE_FREE), SIGNUP, lg=True)}</div>'
            f'<p class="reassure">{t(note or T("Free forever · 60 days of Pro · No card","Gratuit pour toujours · 60 jours de Pro · Sans carte","Gratis para siempre · 60 días de Pro · Sin tarjeta"))}</p>'
            f'</div></div></section>')

def read_next(lang, t, items):
    """« Read next »: three cards, from core.related."""
    return related(lang, t, items).replace('<section class="rule related"><div class="wrap">', '<section class="s-t related"><div class="c">', 1)

# ---------------------------------------------------------------- page heads, chapters, older captures
def hero(t, kick, h1, lead, cta="", note=None, visual="", center=False, extra="", kick_in_h1=False):
    """A page's first screen: eyebrow, title, lead, actions, then an optional visual. Keeps the .page-hero hook (phone dock).
    kick_in_h1: the eyebrow is part of the title (it carries the page's keyword), read as « eyebrow: title »."""
    k = f'<span class="eyebrow rise">{t(kick)}</span>' if kick else ""
    c = f'<div class="cta-row rise d4">{cta}</div>' if cta else ""
    n = f'<p class="reassure rise d4">{t(note)}</p>' if note else ""
    v = f'<div class="c c-wide hero-visual">{hero_shot(visual)}</div>' if visual else ""
    p = f'<p class="lead rise d3">{t(lead)}</p>' if lead else ""
    h = f'<h1 class="wu">{words(t(h1))}</h1>'
    if kick_in_h1 and k: k, h = "", f'<h1 class="wu">{k}<span class="sr">{t(T(": ",". ",". "))}</span>{words(t(h1))}</h1>'
    return f'<div class="page-hero{" center" if center else ""}"><div class="c">{k}{h}{p}{c}{n}{extra}</div>{v}</div>'

def hero_shot(visual):
    """The visual of a first screen: loaded at once and first, never hidden while it loads (it is the largest paint)."""
    v = visual.replace('loading="lazy"', 'loading="eager" fetchpriority="high"', 1)
    return v.replace(" reveal zoom\"", " hero-shot\"", 1).replace(" reveal\"", " hero-shot\"", 1)

def _anchor(text, used):
    a = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()).strip("-")[:48].strip("-") or "s"
    k, n = a, 2
    while k in used: k, n = f"{a}-{n}", n + 1
    used.add(k); return k

def doc(t, html):
    """A long text with its chapters: a sticky column beside the text on computers, the capsule under the menu on phones
    (site.js highlights the chapter being read, as for .subnav). Each <h2> gets an id."""
    used, toc = set(), []
    def h2(m):
        label = _html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        k = _anchor(label, used); toc.append((k, label)); return f'<h2{m.group(1)} id="{k}">{m.group(2)}</h2>'
    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", h2, html, flags=re.S)
    nav = (f'<nav class="subnav toc" aria-label="{t(T("On this page","Sur cette page","En esta página"))}"><div class="sn">'
           + "".join(f'<a href="#{k}">{_html.escape(l, quote=False)}</a>' for k, l in toc) + "</div></nav>")
    return f'<div class="doc">{nav}<article class="article">{body}</article></div>'

def subnav(t, label, items):
    """Chapters of a long page, in a capsule that stays under the menu (site.js highlights the current one)."""
    return f'<nav class="subnav" aria-label="{t(label)}"><div class="c"><div class="sn">' + "".join(f'<a href="#{a}">{t(n)}</a>' for a, n in items) + "</div></div></nav>"

def frame_pic(screen, lang, alt, mobile=None, t=None, cap=True, cls="reveal", sizes="(max-width: 1067px) 92vw, 700px"):
    """A computer capture from /img (older screens, by language), with its phone capture on phones."""
    L = core._pick("desktop", lang, screen); d = f"desktop-{L}-dark-{screen}"
    img = (f'<img src="/img/{d}-1200.webp" srcset="/img/{d}-1200.webp 1200w, /img/{d}-2400.webp 2400w" sizes="{sizes}" width="2880" height="1800" '
           f'alt="{_html.escape(alt)}" loading="lazy" decoding="async">')
    m = mobile or (screen if has_mobile(screen) else None)
    if m:
        Lm = core._pick("mobile", lang, m)
        img = f'<picture><source media="(max-width: 743px)" srcset="/img/mobile-{Lm}-dark-{m}-786.webp">{img}</picture>'
    c = f'<figcaption class="cap">{t(SAMPLE)}</figcaption>' if cap and t else ""
    return f'<figure class="fr fr-d{" has-m" if m else ""} {cls}"><div class="scr">{img}</div>{c}</figure>'

def phone_src(screen, lang):
    """The path of an older phone capture in /img, in the page's language when it exists."""
    return f"/img/mobile-{core._pick('mobile', lang, screen)}-dark-{screen}-786.webp"

def phones(t, items, cls="phones-row stagger"):
    """A row of phones (a swipe rail on phones): (capture, alt)."""
    return f'<div class="{cls}">' + "".join(frame_p(n, t(a), cap=False, cls="") for n, a in items) + "</div>"

def points(t, items):
    return '<ul class="points stagger">' + "".join(f"<li>{t(x)}</li>" for x in items) + "</ul>"
