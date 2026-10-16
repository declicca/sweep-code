from core import *

PRICES = {"pro": {"m": 19, "y": 159}, "elite": {"m": 39, "y": 329}}
START = T("Start free","Commencer gratuitement","Empezar gratis")

def share_img(name, alt, w, h, sizes="(max-width: 860px) 64vw, 340px"):
    return (f'<img src="/img/{name}-540.webp" srcset="/img/{name}-540.webp 540w, /img/{name}-1080.webp 1080w" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{html.escape(alt)}" loading="lazy" decoding="async">')

def money(t, v):
    L = t(T("en","fr","es"))
    txt = f"{v:.2f}" if isinstance(v, float) and v != int(v) else f"{int(v)}"
    return f"${txt}" if L == "en" else txt.replace(".", ",") + " $"

