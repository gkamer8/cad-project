"""HTML for the 17 x 11 in review document (printed by Chromium, CAD sheets appended after)."""

from pathlib import Path

from ..drawings.cad import ft_in
from ..model.ceiling import KEY_HOOK
from ..model.parts import Mat
from ..spec import (BASE_TOP, CEILING_H, CEILING_PANEL_INSET, CEILING_RING_R, CHAIR_RAIL_TOP, CORNICE_BOTTOM,
                    CROWN_BOTTOM, DADO_PANEL, FIXTURES, FURNITURE, HEAD_H, MEDALLION_R, OPENINGS, PROJECT,
                    ROOM_L, ROOM_W, SILL_H, UPPER_PANEL, OpeningKind, Wall)
from .content import ASSUMPTIONS, CAPTIONS, CONCEPT, DESIGN_MOVES, HOW_TO_OPEN, PLAN_IDEA, QUESTIONS

CSS = """
@page { size: 17in 11in; margin: 0; }
:root { --paper: #F7F1E6; --ink: #2A1F1B; --red: #8E2B22; --deep: #5A1613; --gold: #A9834A; --muted: #76665C; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--paper); color: var(--ink);
             font-family: 'Inter', sans-serif; font-weight: 300; -webkit-print-color-adjust: exact; }
.page { width: 17in; height: 11in; position: relative; overflow: hidden; break-after: page; background: var(--paper); }
.serif, h1, h2, h3 { font-family: 'Cormorant Garamond', serif; font-weight: 500; }
.label { font-size: 9pt; letter-spacing: .28em; text-transform: uppercase; color: var(--red); font-weight: 500; }
.frame { position: absolute; inset: .55in .75in .6in .75in; }
.top { display: flex; align-items: center; gap: .3in; }
.top .band { flex: 1; height: .2in; }
.foot { position: absolute; left: .75in; right: .75in; bottom: .3in; display: flex; justify-content: space-between;
        font-size: 8pt; letter-spacing: .2em; text-transform: uppercase; color: var(--muted); }
h2 { font-size: 40pt; margin: .18in 0 .12in; line-height: 1.02; color: var(--deep); }
h3 { font-size: 19pt; margin: 0 0 .06in; color: var(--deep); }
p { font-size: 11.5pt; line-height: 1.6; margin: 0 0 .12in; }
.lead { font-family: 'Cormorant Garamond', serif; font-size: 21pt; line-height: 1.35; font-weight: 400; }
.cover img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.cover .shade { position: absolute; inset: 0;
  background: linear-gradient(90deg, rgba(22,8,6,.86) 0%, rgba(22,8,6,.55) 34%, rgba(22,8,6,0) 58%); }
.cover .title { position: absolute; left: .9in; bottom: 1.0in; width: 6.8in; color: #F5E9D6; }
.cover .title .label { color: #D9B77A; }
.cover h1 { font-size: 78pt; font-weight: 400; font-style: italic; line-height: .95; margin: .2in 0 .25in; }
.cover .facts { font-size: 11pt; letter-spacing: .12em; line-height: 1.9; text-transform: uppercase; }
.cover .band { width: 5.2in; height: .22in; margin: .25in 0; }
.cols { display: grid; gap: .55in; }
.moves { display: grid; grid-template-columns: 1.25in 1fr; row-gap: .1in; column-gap: .2in; font-size: 11pt;
         line-height: 1.5; }
.moves b { font-family: 'Cormorant Garamond', serif; font-size: 15pt; font-weight: 600; color: var(--red); }
.swatches { display: grid; grid-template-columns: repeat(4, 1fr); gap: .16in .2in; }
.sw { display: flex; gap: .12in; align-items: center; }
.chip { width: .62in; height: .62in; border-radius: 50%; flex: none; box-shadow: inset 0 0 0 1px rgba(0,0,0,.12); }
.sw .t { font-size: 8.5pt; line-height: 1.35; }
.sw .t b { display: block; font-family: 'Cormorant Garamond', serif; font-size: 13pt; font-weight: 600; }
.shot { position: absolute; left: .75in; top: 1.05in; width: 15.5in; height: 8.9in; object-fit: cover; }
.cap { position: absolute; right: .75in; bottom: .55in; width: 5.2in; padding: .18in .25in; background: var(--paper); }
.cap h3 { font-size: 22pt; }
.cap p { font-size: 10pt; margin: 0; }
table { border-collapse: collapse; width: 100%; font-size: 9.5pt; }
th { text-align: left; font-weight: 500; font-size: 7.5pt; letter-spacing: .16em; text-transform: uppercase;
     color: var(--red); border-bottom: 1.4px solid var(--gold); padding: .05in .08in; }
td { padding: .055in .08in; border-bottom: .6px solid rgba(169,131,74,.45); vertical-align: top; line-height: 1.4; }
td.tag { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 12pt; color: var(--deep); }
.kv { display: grid; grid-template-columns: 2.3in 1fr; row-gap: .06in; font-size: 10.5pt; line-height: 1.45; }
.kv div:nth-child(odd) { color: var(--muted); }
ol, ul { margin: 0; padding-left: .22in; font-size: 10.5pt; line-height: 1.55; }
li { margin-bottom: .07in; }
.note { font-size: 9pt; color: var(--muted); line-height: 1.5; }
.two img { width: 100%; height: 5.1in; object-fit: cover; display: block; }
.figcap { font-size: 9.5pt; margin-top: .08in; line-height: 1.45; }
.figcap b { font-family: 'Cormorant Garamond', serif; font-size: 14pt; color: var(--deep); font-weight: 600; }
"""


def greek_key_svg(color: str, periods: int) -> str:
    hooks = " ".join("M" + " L".join(f"{4 * k + x},{y + 1}" for x, y in KEY_HOOK) for k in range(periods))
    rules = f"M-0.5,0 L{4 * periods - 0.5},0 M-0.5,6 L{4 * periods - 0.5},6"
    return (f'<svg class="band" viewBox="-0.8 -0.4 {4 * periods + 0.6} 6.8" preserveAspectRatio="xMinYMid slice">'
            f'<path d="{hooks} {rules}" fill="none" stroke="{color}" stroke-width="0.42" '
            f'stroke-linecap="square" stroke-linejoin="miter"/></svg>')


def _header(label: str) -> str:
    return f'<div class="top"><div class="label">{label}</div>{greek_key_svg("#A9834A", 60)}</div>'


def _footer(page: int) -> str:
    return f'<div class="foot"><span>{PROJECT}</span><span>Design review &middot; 26 November 2026</span><span>{page:02d}</span></div>'


def _page(body: str, page: int) -> str:
    return f'<section class="page">{body}{_footer(page)}</section>'


def cover(img: str) -> str:
    facts = (f"{ft_in(ROOM_L)} &times; {ft_in(ROOM_W)} &middot; {ft_in(CEILING_H)} ceiling<br>"
             f"Four {OPENINGS[0].width:.0f}&Prime; &times; {OPENINGS[0].top - OPENINGS[0].bottom:.0f}&Prime; windows "
             f"&middot; Pompeian red")
    return (f'<section class="page cover"><img src="{img}"><div class="shade"></div><div class="title">'
            f'<div class="label">Neoclassical bedroom &middot; Design review</div><h1>{PROJECT}</h1>'
            f'{greek_key_svg("#D9B77A", 26)}<div class="facts">{facts}<br>26 November 2026</div></div></section>')


def concept(img: str, page: int) -> str:
    moves = "".join(f"<b>{k}</b><div>{v}</div>" for k, v in DESIGN_MOVES)
    swatches = "".join(
        f'<div class="sw"><div class="chip" style="background:{m.value.hex_color}"></div>'
        f'<div class="t"><b>{m.value.name}</b>{m.value.code} &middot; {m.value.hex_color.upper()}</div></div>'
        for m in (Mat.WALL_RED, Mat.DAMASK, Mat.SILK_RED, Mat.VELVET, Mat.TRIM_IVORY, Mat.SILK_IVORY, Mat.GILT,
                  Mat.LACQUER))
    body = (f'<div class="frame">{_header("The concept")}'
            f'<div class="cols" style="grid-template-columns: 7.6in 1fr; margin-top:.25in">'
            f'<div><h2>Pompeian red,<br>Neoclassical order</h2><p class="lead">{CONCEPT}</p><p>{PLAN_IDEA}</p>'
            f'<div class="moves" style="margin-top:.22in">{moves}</div></div>'
            f'<div><img src="{img}" style="width:100%;height:4.6in;object-fit:cover;display:block">'
            f'<div class="label" style="margin:.28in 0 .16in">Principal palette</div>'
            f'<div class="swatches">{swatches}</div></div></div></div>')
    return _page(body, page)


def full_shot(name: str, img: str, page: int) -> str:
    title, text = CAPTIONS[name]
    body = (f'<div class="frame">{_header("Rendering")}</div><img class="shot" src="{img}">'
            f'<div class="cap"><h3>{title}</h3><p>{text}</p></div>')
    return _page(body, page)


def pair(left: tuple[str, str], right: tuple[str, str], page: int) -> str:
    figs = "".join(f'<div><img src="{img}"><div class="figcap"><b>{CAPTIONS[n][0]}</b><br>{CAPTIONS[n][1]}</div></div>'
                   for n, img in (left, right))
    body = (f'<div class="frame">{_header("Rendering")}<div class="cols two" '
            f'style="grid-template-columns:1fr 1fr;margin-top:.35in">{figs}</div></div>')
    return _page(body, page)


def plan_page(img: str, page: int) -> str:
    rows = "".join(f"<tr><td class='tag'>{i.tag}</td><td>{i.name}</td><td>{len(i.placements)}</td></tr>"
                   for i in FURNITURE + FIXTURES)
    title, text = CAPTIONS["plan"]
    body = (f'<div class="frame">{_header("Layout")}<div class="cols" style="grid-template-columns:10.6in 1fr;'
            f'margin-top:.3in"><img src="{img}" style="width:100%;height:7.95in;object-fit:contain;display:block">'
            f'<div><h2 style="font-size:34pt">{title}</h2><p>{text}</p>'
            f'<table><tr><th>Tag</th><th>Item</th><th>Qty</th></tr>{rows}</table>'
            f'<p class="note" style="margin-top:.15in">Tags match the CAD set (sheet A-101) and the schedules.</p>'
            f'</div></div></div>')
    return _page(body, page)


def _kv(pairs: list[tuple[str, str]]) -> str:
    return '<div class="kv">' + "".join(f"<div>{k}</div><div>{v}</div>" for k, v in pairs) + "</div>"


def specs_page(page: int) -> str:
    room = [("Clear interior", f"{ft_in(ROOM_L)} &times; {ft_in(ROOM_W)} ({ROOM_L * ROOM_W / 144:.0f} sq ft)"),
            ("Finished ceiling", ft_in(CEILING_H)),
            ("Walls (assumed)", f"Exterior {ft_in(Wall.SOUTH.value.thickness)}, interior {ft_in(Wall.EAST.value.thickness)}"),
            ("Floor", "White-oak herringbone parquet (WD-1)")]
    heights = [("Baseboard", ft_in(BASE_TOP)), ("Dado panels", f"{ft_in(DADO_PANEL[0])} to {ft_in(DADO_PANEL[1])}"),
               ("Chair rail (top)", f"{ft_in(CHAIR_RAIL_TOP)} &mdash; aligned with window stools"),
               ("Window sill", ft_in(SILL_H)), ("Window & door heads", ft_in(HEAD_H)),
               ("Upper wall panels", f"{ft_in(UPPER_PANEL[0])} to {ft_in(UPPER_PANEL[1])}"),
               ("Cornice", f"{ft_in(CORNICE_BOTTOM)} to ceiling: astragal, dentils, {ft_in(CEILING_H - CROWN_BOTTOM)} crown")]
    ceiling = [("Panel molding", f"Inset {ft_in(CEILING_PANEL_INSET)} from the walls"),
               ("Greek-key border", "Gilt relief on a 1.1\" grid between cornice and panel"),
               ("Ring & medallion", f"Ring &Oslash;{ft_in(2 * CEILING_RING_R)}, medallion &Oslash;{ft_in(2 * MEDALLION_R)}"),
               ("Corner fans", "Four reeded quarter-fans in the panel corners")]
    rows = "".join(
        f"<tr><td class='tag'>{o.tag}</td><td>{'6-over-6 double-hung' if o.kind is OpeningKind.WINDOW else 'Six-panel door'}"
        f"</td><td>{ft_in(o.width)} &times; {ft_in(o.top - o.bottom)}</td><td>{ft_in(o.bottom)}</td>"
        f"<td>{ft_in(o.top)}</td><td>{o.wall.value.label}</td></tr>" for o in OPENINGS)
    body = (f'<div class="frame">{_header("Specifications")}<h2>Room &amp; architecture</h2>'
            f'<div class="cols" style="grid-template-columns:1fr 1fr;gap:.7in">'
            f'<div><h3>Room</h3>{_kv(room)}<h3 style="margin-top:.25in">Vertical zoning (AFF)</h3>{_kv(heights)}</div>'
            f'<div><h3>Windows &amp; door</h3><table><tr><th>Tag</th><th>Type</th><th>Size</th><th>Sill</th>'
            f'<th>Head</th><th>Wall</th></tr>{rows}</table>'
            f'<p class="note" style="margin-top:.1in">Windows sit 4\'-8" from the corners, 6\'-8" on centre; the door '
            f'is centred on the east wall in a fluted-pilaster doorcase.</p>'
            f'<h3 style="margin-top:.22in">Ceiling</h3>{_kv(ceiling)}</div></div></div>')
    return _page(body, page)


def finishes_page(page: int) -> str:
    cells = "".join(
        f'<div class="sw"><div class="chip" style="background:{m.value.hex_color}"></div><div class="t">'
        f'<b>{m.value.code} &middot; {m.value.name}</b>{m.value.description}<br>'
        f'<span style="color:var(--muted)">{m.value.hex_color.upper()}</span></div></div>'
        for m in Mat if m is not Mat.WALL_SHELL)
    body = (f'<div class="frame">{_header("Specifications")}<h2>Finish schedule</h2>'
            f'<div class="swatches" style="margin-top:.3in;gap:.32in .3in">{cells}</div>'
            f'<p class="note" style="margin-top:.35in">Colours are sRGB approximations for review. Confirm with '
            f'physical paint draw-downs, fabric cuttings and a gilding sample board before ordering.</p></div>')
    return _page(body, page)


def ffe_page(page: int) -> str:
    rows = "".join(
        f"<tr><td class='tag'>{i.tag}</td><td><b style='font-weight:500'>{i.name}</b><br>{i.description}</td>"
        f"<td>{ft_in(i.size[0])} &times; {ft_in(i.size[1])} &times; {ft_in(i.size[2])}</td>"
        f"<td>{len(i.placements)}</td><td>{', '.join(i.finishes)}</td></tr>" for i in FURNITURE + FIXTURES)
    body = (f'<div class="frame">{_header("Specifications")}<h2>Furniture, lighting &amp; textiles</h2>'
            f'<table style="margin-top:.15in"><tr><th style="width:.6in">Tag</th><th>Item</th>'
            f'<th style="width:2.4in">W &times; D &times; H</th><th style="width:.5in">Qty</th>'
            f'<th style="width:1.7in">Finishes</th></tr>{rows}</table>'
            f'<p class="note" style="margin-top:.14in">Lighting control: chandelier on a 3-way dimmer (door and '
            f'bedside); sconces dimmed at the door; commode lamps on switched receptacles. Lamping 2700&thinsp;K, '
            f'2200&thinsp;K flame-tip for candle lights, CRI 90+.</p></div>')
    return _page(body, page)


def deliverables_page(sheets: list[tuple[str, str]], page: int) -> str:
    opens = "".join(f"<b>{k}</b><div>{v}</div>" for k, v in HOW_TO_OPEN)
    sheet_rows = "".join(f"<tr><td class='tag'>{n}</td><td>{t}</td></tr>" for n, t in sheets)
    body = (f'<div class="frame">{_header("Deliverables")}<h2>The CAD set &amp; open questions</h2>'
            f'<div class="cols" style="grid-template-columns:1.15fr 1fr;gap:.7in">'
            f'<div><h3>Opening the files in Autodesk</h3><div class="moves">{opens}</div>'
            f'<h3 style="margin-top:.25in">Drawing sheets (following pages)</h3>'
            f'<table><tr><th>Sheet</th><th>Title</th></tr>{sheet_rows}</table></div>'
            f'<div><h3>Assumptions</h3><ol>{"".join(f"<li>{a}</li>" for a in ASSUMPTIONS)}</ol>'
            f'<h3 style="margin-top:.22in">For your review</h3><ol>{"".join(f"<li>{q}</li>" for q in QUESTIONS)}</ol>'
            f'<p class="note" style="margin-top:.2in">Drawings, renderings and 3D files are generated from one '
            f'parametric source, so any change above updates every deliverable together.</p></div></div></div>')
    return _page(body, page)


def document(images: dict[str, Path], fonts_css: Path, sheets: list[tuple[str, str]]) -> str:
    img = {k: v.as_uri() for k, v in images.items()}
    pages = [
        cover(img["hero"]),
        concept(img["canopy"], 2),
        full_shot("hero", img["hero"], 3),
        pair(("bed", img["bed"]), ("canopy", img["canopy"]), 4),
        full_shot("door_wall", img["door_wall"], 5),
        full_shot("evening", img["evening"], 6),
        plan_page(img["plan"], 7),
        specs_page(8),
        finishes_page(9),
        ffe_page(10),
        deliverables_page(sheets, 11),
    ]
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{PROJECT}</title>'
            f'<link rel="stylesheet" href="{fonts_css.as_uri()}"><style>{CSS}</style></head>'
            f'<body>{"".join(pages)}</body></html>')
