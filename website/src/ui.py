"""The design system's building blocks (styles in system.css). A page built with them is listed in
core.SYSTEM_PAGES and loads system.css; the others keep styles.css until they are migrated.
Grid rules are checked here, at build time: a row of cards never mixes cards with and without a visual,
and never ends on an orphan row."""
import os, html as _html
from core import *

CAP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "img", "captures", "en")
RHYTHM = {"t": "s-t", "n": "s", "a": "s-a"}

def sec(inner, rhythm="n", id_="", cls="", width="", flush=False):
    """A section: rhythm t(ight) / n(ormal) / a(mple), container standard / wide / read."""
    if width == "read": inner, width = f'<div class="read">{inner}</div>', ""   # long text: narrow, on the same left edge as the rest
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

def _img_d(name, alt, sizes, eager=False):
    base = name[:-5]
    ss = f' srcset="/img/captures/{base}-1200.webp 1200w, /img/captures/{name} 2400w" sizes="{sizes}"' if _has(base + "-1200.webp") else ""
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return f'<img src="/img/captures/{name}"{ss} width="2880" height="1800" alt="{_html.escape(alt)}" {load} decoding="async">'

def frame_d(name, alt, m=None, sizes="(max-width: 1067px) 92vw, 700px", cap=True, t=None, cls="reveal"):
    """A computer capture. On phones it becomes the phone capture `m`: a desktop screen shrunk to 300 px can't be read."""
    img = _img_d(name, alt, sizes)
    if m:
        img = f'<picture><source media="(max-width: 743px)" srcset="/img/captures/{m}">{img}</picture>'
    c = f'<figcaption class="cap">{t(SAMPLE)}</figcaption>' if cap and t else ""
    return f'<figure class="fr fr-d{" has-m" if m else ""} {cls}"><div class="scr">{img}</div>{c}</figure>'

def frame_p(name, alt, t=None, video=None, cap=True, width=None, cls="reveal"):
    """A phone. With `video`, the capture `name` is its first frame and the video fades in once it plays."""
    st = f' style="--pw:{width}px"' if width else ""
    if video:
        media = (f'<img class="vfb" src="/img/captures/{name}" width="900" height="1948" alt="" aria-hidden="true" loading="lazy" decoding="async">'
                 f'<video muted loop playsinline preload="none" data-auto aria-label="{_html.escape(alt)}"><source src="/img/captures/{video}" type="video/mp4"></video>')
    else:
        media = f'<img src="/img/captures/{name}" width="900" height="1948" alt="{_html.escape(alt)}" loading="lazy" decoding="async">'
    c = f'<figcaption class="cap">{t(SAMPLE)}</figcaption>' if cap and t else ""
    return f'<figure class="fr fr-p {cls}"{st}><div class="scr">{media}</div>{c}</figure>'

def phone_img(src, alt, pos="50% 0%"):
    """A phone capture cropped for a card (the top of the screen unless `pos` says otherwise)."""
    return f'<img src="{src}" width="900" height="1948" alt="{_html.escape(alt)}" loading="lazy" decoding="async" style="object-position:{pos}">'

# ---------------------------------------------------------------- cards
class Card:
    def __init__(self, kind, markup): self.kind, self.markup = kind, markup

def card(t, title, text, icon=None, more=""):
    i = f'<span class="ico" aria-hidden="true">{ico(I[icon])}</span>' if icon else ""
    return Card("text", f'<article class="card">{i}<h3>{t(title)}</h3><p>{t(text)}</p>{f"<div class=more>{more}</div>" if more else ""}</article>')

def card_media(t, title, text, media, crop=False, more=""):
    """A card with a visual on top; every card of the row shares the visual's ratio."""
    return Card("media" + ("-crop" if crop else ""), f'<article class="card media{" phone-crop" if crop else ""}"><div class="cm">{media}</div>'
                f'<div class="ct"><h3>{t(title)}</h3><p>{t(text)}</p>{f"<div class=more>{more}</div>" if more else ""}</div></article>')

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

def stats(items, caption="", note=""):
    """Key numbers: (label, value, small note)."""
    dl = "".join(f'<div class="stat"><dt>{a}</dt><dd>{b}{f"<small>{c}</small>" if c else ""}</dd></div>' for a, b, c in items)
    cap = f'<div class="stats-cap"><b>{caption}</b><span>{note}</span></div>' if caption else ""
    return f'{cap}<dl class="stats reveal" style="--n:{len(items)}">{dl}</dl>'

def qa(t, items, more=""):
    return '<div class="qa">' + "".join(faq_item(t, q, a) for q, a in items) + (f'<p class="more-q">{more}</p>' if more else "") + "</div>"

def state(text):
    return f'<div class="state reveal"><span class="dot" aria-hidden="true"></span><p>{text}</p></div>'

def final(lang, t):
    """The site's closing block: one promise, one action."""
    return (f'<section class="final s-a"><div class="c c-wide"><div class="stage reveal">'
            f'<span class="mark" aria-hidden="true">{ANIM_MARK}</span>'
            f'<h2>{t(T("Your edge, finally in one place.","Ton edge, enfin au même endroit.","Tu edge, por fin en un solo lugar."))}</h2>'
            f'<div class="cta-row">{btn(t(CREATE_FREE), SIGNUP, lg=True)}</div>'
            f'<p class="reassure">{t(T("Free forever · 60 days of Pro · No card","Gratuit pour toujours · 60 jours de Pro · Sans carte","Gratis para siempre · 60 días de Pro · Sin tarjeta"))}</p>'
            f'</div></div></section>')

def read_next(lang, t, items):
    """« Read next »: three cards, from core.related."""
    return related(lang, t, items).replace('<section class="rule related"><div class="wrap">', '<section class="s-t related"><div class="c">', 1)
