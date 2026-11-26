"""HTML for the showcase site: CAD explorer first, then renderings, sheets, schedules and downloads."""

import json
from dataclasses import dataclass
from html import escape, unescape

from ..drawings.cad import ft_in
from ..drawings.sheets import SHEETS, Sheet
from ..model.parts import Mat
from ..report.content import CAPTIONS, CONCEPT
from ..spec import (CEILING_H, CHAIR_RAIL_TOP, FIXTURES, FURNITURE, HEAD_H, OPENINGS, PROJECT, ROOM_L, ROOM_W,
                    SILL_H, OpeningKind, Wall)
from .style import CSS

THREE = "https://cdn.jsdelivr.net/npm/three@0.160.0"
BVH = "https://cdn.jsdelivr.net/npm/three-mesh-bvh@0.7.6/build/index.module.js"
JSZIP = "https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"
FONTS = ("https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,500;1,6..96,500"
         "&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap")
RENDER_ORDER = ("hero", "bed", "door_wall", "canopy", "evening", "plan")


def _attr(text: str) -> str:
    """Report copy carries HTML entities; turn them into characters, then escape for an attribute."""
    return escape(unescape(text))


def _scale(sheet: Sheet) -> str:
    return sheet.ports[0].drawing.scale_label if sheet.ports else "as noted"


def head() -> str:
    importmap = ('{"imports": {"three": "%s/build/three.module.js", "three/addons/": "%s/examples/jsm/", '
                 '"three-mesh-bvh": "%s"}}') % (THREE, THREE, BVH)
    return (f'<title>{PROJECT}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            f'<meta name="description" content="Interactive CAD model, renderings and drawings of a neoclassical bedroom.">\n'
            f'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link rel="stylesheet" href="{FONTS}">\n<style>{CSS}</style>\n'
            f'<script type="importmap">{importmap}</script>\n')


def header() -> str:
    links = [("explore", "3D model"), ("renderings", "Renderings"), ("drawings", "Drawings"), ("specs", "Specifications"),
             ("downloads", "Downloads")]
    nav = "".join(f'<a href="#{k}">{v}</a>' for k, v in links)
    return (f'<header class="top"><div class="wrap"><a class="brand" href="#explore">{PROJECT}</a>'
            f'<nav aria-label="Sections">{nav}</nav></div></header>')


def intro() -> str:
    windows = [o for o in OPENINGS if o.kind is OpeningKind.WINDOW]
    facts = [("Room", f"{ft_in(ROOM_L)} x {ft_in(ROOM_W)}"), ("Ceiling", ft_in(CEILING_H)),
             ("Windows", f"{len(windows)} at {windows[0].width:.0f}\" x {windows[0].top - windows[0].bottom:.0f}\""),
             ("Drawing set", f"{len(SHEETS)} sheets, DXF")]
    dl = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in facts)
    return (f'<div class="intro wrap"><div><div class="eyebrow">Neoclassical bedroom &middot; interactive model</div>'
            f'<h1>{PROJECT}</h1><p class="lede">{CONCEPT} Orbit the room, walk through it, cut sections, measure '
            f'anything and click any object to read its finish and size.</p></div><dl class="facts">{dl}</dl></div>')


TOOLBAR = """
<div class="toolbar" role="toolbar" aria-label="Model tools">
  <div class="group" aria-label="Views">
    <button class="tb" data-view="iso" aria-pressed="true" title="3D overview (1)">3D</button>
    <button class="tb" data-view="top" aria-pressed="false" title="Floor plan view (2)">Plan</button>
    <button class="tb" data-view="north" aria-pressed="false" title="North wall elevation (3)">N</button>
    <button class="tb" data-view="south" aria-pressed="false" title="South wall elevation (4)">S</button>
    <button class="tb" data-view="east" aria-pressed="false" title="East wall elevation, door (5)">E</button>
    <button class="tb" data-view="west" aria-pressed="false" title="West wall elevation, bed (6)">W</button>
    <button class="tb" data-action="walk" aria-pressed="false" title="Walk through at eye height (G)">Walk</button>
  </div>
  <div class="group" aria-label="Display">
    <button class="tb" data-mode="realistic" aria-pressed="true">Realistic</button>
    <button class="tb" data-mode="shaded" aria-pressed="false">Shaded</button>
    <button class="tb" data-mode="clay" aria-pressed="false">Clay</button>
    <button class="tb" data-mode="wire" aria-pressed="false">Wireframe</button>
    <button class="tb" data-mode="xray" aria-pressed="false">X-ray</button>
  </div>
  <div class="group" aria-label="Tools">
    <button class="tb" data-tool="select" aria-pressed="true" title="Inspect objects">Select</button>
    <button class="tb" data-tool="measure" aria-pressed="false" title="Measure between two points (M)">Measure</button>
    <button class="tb" data-action="clear" title="Clear measurements">Clear</button>
    <button class="tb" data-action="section-panel" aria-pressed="false" title="Section cuts">Section</button>
  </div>
  <div class="group" aria-label="Scene">
    <button class="tb" data-action="night" aria-pressed="false" title="Evening lighting (N)">Evening</button>
    <button class="tb" data-action="labels" aria-pressed="false" title="Show tags and room dimensions (L)">Tags</button>
    <button class="tb" data-action="cutaway" aria-pressed="true" title="Cut away walls between you and the room">Cutaway</button>
  </div>
  <div class="group" aria-label="View">
    <button class="tb" data-action="fit" title="Zoom to fit (F)">Fit</button>
    <button class="tb" data-action="shot" title="Save this view as a PNG">Save view</button>
    <button class="tb" data-action="full" title="Full screen">Full screen</button>
    <button class="tb" data-action="panel-left" aria-pressed="true" title="Layers and objects">Layers</button>
    <button class="tb" data-action="panel-right" aria-pressed="true" title="Properties">Properties</button>
    <button class="tb" data-action="help" title="Controls">?</button>
  </div>
</div>"""

STAGE = """
<div class="stage">
  <div id="viewport"></div>
  <div id="pins"></div>
  <div id="tooltip" hidden></div>
  <div class="compass" id="compass" aria-label="Compass">
    <div class="ring">
      <button class="n" data-view="north" aria-pressed="false">N</button>
      <button class="e" data-view="east" aria-pressed="false">E</button>
      <button class="s" data-view="south" aria-pressed="false">S</button>
      <button class="w" data-view="west" aria-pressed="false">W</button>
    </div>
    <button class="top-btn" data-view="top" aria-pressed="false">TOP</button>
  </div>
  <div class="tours" id="tours" aria-label="Viewpoints"></div>
  <div class="floating section-panel" id="section" hidden>
    <label for="cut-height"><span><input type="checkbox" id="cut-height"> Plan cut height</span>
      <output id="cut-height-out"></output>
      <input type="range" id="cut-height-v" min="1" max="95" step="1" value="48"></label>
    <label for="cut-x"><span><input type="checkbox" id="cut-x"> Cut across (keep west)</span>
      <output id="cut-x-out"></output>
      <input type="range" id="cut-x-v" min="1" max="191" step="1" value="96"></label>
    <label for="cut-y"><span><input type="checkbox" id="cut-y"> Cut along (keep south)</span>
      <output id="cut-y-out"></output>
      <input type="range" id="cut-y-v" min="1" max="143" step="1" value="72"></label>
    <small>Distances are from the south-west corner and the finished floor.</small>
  </div>
  <div class="floating help" id="help" hidden>
    <h3>Controls</h3>
    <dl>
      <dt>Drag</dt><dd>Orbit around the room</dd>
      <dt>Right-drag / two fingers</dt><dd>Pan</dd>
      <dt>Scroll / pinch</dt><dd>Zoom toward the cursor</dd>
      <dt>Click</dt><dd>Select an object: finish, size, position</dd>
      <dt>1 to 6</dt><dd>3D, plan, north, south, east, west views</dd>
      <dt>G</dt><dd>Walk: drag to look, W A S D or arrows to move, Shift to hurry, Esc to stop</dd>
      <dt>M / F / L / N</dt><dd>Measure, fit, tags, evening light</dd>
      <dt>Esc</dt><dd>Clear the selection</dd>
    </dl>
  </div>
  <div class="walkpad" aria-label="Walk controls">
    <button id="pad-up" aria-label="Forward">&#9650;</button><button id="pad-left" aria-label="Left">&#9664;</button>
    <button id="pad-down" aria-label="Back">&#9660;</button><button id="pad-right" aria-label="Right">&#9654;</button>
  </div>
  <div class="loader" id="loader">
    <img src="img/renders/hero.jpg" alt="">
    <div class="box"><div class="eyebrow">Loading the model</div><div class="bar"><i id="loader-bar"></i></div>
      <p id="loader-msg">97 objects, 2 MB, built from the same file as the drawings.</p></div>
  </div>
</div>"""


def explorer() -> str:
    left = ('<aside class="panel" id="panel-left" aria-label="Layers and objects"><h4>Layers</h4><div id="layers"></div>'
            '<h4>Objects</h4><label class="iso" for="iso-only"><input type="checkbox" id="iso-only"> Show only the '
            'selected object</label><ul class="objects" id="objects"></ul></aside>')
    right = ('<aside class="panel right" id="panel-right" aria-label="Properties"><h4>Properties</h4>'
             '<p class="props-empty" id="props-empty">Click any object in the model to see its finish, size and '
             'position.</p><div class="props" id="props" hidden><span class="ptag" id="props-tag"></span>'
             '<h3 id="props-name"></h3><dl><dt>Type</dt><dd id="props-kind"></dd><dt>Size</dt><dd id="props-size"></dd>'
             '<dt>Corner</dt><dd id="props-pos"></dd><dt>About</dt><dd id="props-desc"></dd><dt>Finishes</dt>'
             '<dd><ul id="props-finishes"></ul></dd><dt>Model</dt><dd id="props-geo"></dd></dl></div></aside>')
    status = ('<div class="statusbar"><span id="stat-xyz">X --  Y --  Z --</span><span class="wide" id="stat-mode">'
              'Realistic</span><span class="wide" id="stat-light">Afternoon</span><span class="wide" id="stat-tris">'
              '</span><span class="wide">Units: ft-in</span><span id="status-msg">Loading</span></div>')
    return (f'<section id="explore">{intro()}<div class="app-wrap"><div class="app" id="explorer">{TOOLBAR}'
            f'<div class="workspace">{left}{STAGE}{right}</div>{status}</div></div></section>')


def renderings() -> str:
    figs = "".join(
        f'<a href="img/renders/{k}.jpg" data-title="{_attr(CAPTIONS[k][0])}" data-text="{_attr(CAPTIONS[k][1])}">'
        f'<figure style="margin:0"><img src="img/renders/thumbs/{k}.jpg" alt="{_attr(CAPTIONS[k][0])}" loading="lazy">'
        f'<figcaption><b>{CAPTIONS[k][0]}</b>{CAPTIONS[k][1]}</figcaption></figure></a>' for k in RENDER_ORDER)
    return (f'<section class="band" id="renderings"><div class="wrap"><div class="section-head"><div>'
            f'<div class="eyebrow">Cycles renderings</div><h2>Six views of the room</h2></div><p>Rendered from the '
            f'same model you can explore above: afternoon sun through the south windows, lamplight after dark, and the '
            f'ceiling lifted off for the plan view. Click any image to see it full size.</p></div>'
            f'<div class="renders" data-gallery="renders">{figs}</div></div></section>')


def _sheet_card(s: Sheet) -> str:
    title = s.title.title().replace("&", "&amp;")
    return (f'<a href="img/sheets/{s.number}.png" data-title="{s.number} {escape(s.title.title())}" '
            f'data-text="Scale {escape(_scale(s))}. Scroll or pinch to zoom.">'
            f'<img src="img/sheets/thumbs/{s.number}.png" alt="Sheet {s.number}" loading="lazy">'
            f'<span class="num">{s.number}</span><span class="title">{title}</span></a>')


def drawings() -> str:
    cards = "".join(_sheet_card(s) for s in SHEETS)
    return (f'<section class="band" id="drawings"><div class="wrap"><div class="section-head"><div>'
            f'<div class="eyebrow">AutoCAD drawing set</div><h2>Eight sheets, ready to plot</h2></div><p>Plan, '
            f'reflected ceiling with lighting and power, four interior elevations and full-size molding profiles. '
            f'Furniture outlines are traced from the 3D model with hidden lines removed, so the drawings and the model '
            f'always agree.</p></div><div class="sheets" data-gallery="sheets">{cards}</div></div></section>')


def specs() -> str:
    room = [("Clear interior", f"{ft_in(ROOM_L)} x {ft_in(ROOM_W)} ({ROOM_L * ROOM_W / 144:.0f} sq ft)"),
            ("Finished ceiling", ft_in(CEILING_H)), ("Window sill / head", f"{ft_in(SILL_H)} / {ft_in(HEAD_H)} AFF"),
            ("Chair rail", f"{ft_in(CHAIR_RAIL_TOP)} AFF, level with the stools"),
            ("Walls (assumed)", f"{ft_in(Wall.SOUTH.value.thickness)} exterior, {ft_in(Wall.EAST.value.thickness)} interior")]
    kv = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in room)
    openings = "".join(
        f"<tr><td class='t'>{o.tag}</td><td>{'6-over-6 double-hung' if o.kind is OpeningKind.WINDOW else 'Six-panel door'}"
        f"</td><td>{ft_in(o.width)} x {ft_in(o.top - o.bottom)}</td><td>{o.wall.value.label}</td></tr>" for o in OPENINGS)
    swatches = "".join(
        f'<div class="sw"><span class="chip" style="background:{m.value.hex_color}"></span><div><b>{m.value.code}</b>'
        f'<span>{escape(m.value.name)}</span></div></div>' for m in Mat if m is not Mat.WALL_SHELL)
    items = "".join(
        f"<tr><td class='t'>{i.tag}</td><td>{escape(i.name)}<small>{escape(i.description)}</small></td>"
        f"<td>{ft_in(i.size[0])} x {ft_in(i.size[1])} x {ft_in(i.size[2])}</td><td>{len(i.placements)}</td>"
        f"<td>{', '.join(i.finishes)}</td></tr>" for i in FURNITURE + FIXTURES)
    return (f'<section class="band" id="specs"><div class="wrap"><div class="section-head"><div>'
            f'<div class="eyebrow">Specifications</div><h2>Room, finishes and furniture</h2></div><p>Every figure here '
            f'comes from the design file that also drives the model and the drawings.</p></div>'
            f'<div class="specs"><div><h3>The room</h3><dl class="kv">{kv}</dl><h3>Windows and door</h3>'
            f'<div class="table-scroll"><table><tr><th>Tag</th><th>Type</th><th>Size</th><th>Wall</th></tr>{openings}'
            f'</table></div></div><div><h3>Finish schedule</h3><div class="swatches">{swatches}</div></div></div>'
            f'<h3 style="margin-top:40px">Furniture and lighting</h3><div class="table-scroll"><table><tr><th>Tag</th>'
            f'<th>Item</th><th>W x D x H</th><th>Qty</th><th>Finishes</th></tr>{items}</table></div></div></section>')


@dataclass(frozen=True)
class Download:
    """A file offered through the page's downloads capability; .zip files are assembled in the browser."""

    title: str
    text: str
    filename: str
    parts: tuple[tuple[str, str, str], ...]  # (published path, name inside the zip, "raw" | "base64")


DOWNLOADS = (
    Download("Design review book", "Renderings, concept, schedules and the full drawing set in one PDF.",
             "Pompeian_Bedroom_Design_Review.pdf", (("dl/Pompeian_Bedroom_Design_Review.pdf", "", "raw"),)),
    Download("Drawing set", "The eight sheets as a vector PDF, 17 x 11 in.",
             "Pompeian_Bedroom_Drawing_Set.pdf", (("dl/Pompeian_Bedroom_Drawing_Set.pdf", "", "raw"),)),
    Download("AutoCAD drawings", "DXF with eight layout tabs and AIA layers, plus the PDF set. Opens directly in "
             "AutoCAD; SAVEAS gives DWG.", "Pompeian_Bedroom_AutoCAD_DXF.zip",
             (("dl/Pompeian_Bedroom_Drawings.dxf.txt", "Pompeian_Bedroom_Drawings.dxf", "raw"),
              ("dl/Pompeian_Bedroom_Drawing_Set.pdf", "Pompeian_Bedroom_Drawing_Set.pdf", "raw"),
              ("dl/README.txt", "README.txt", "raw"))),
    Download("3D model", "FBX for 3ds Max, Maya and Autodesk Viewer, in real-world units.",
             "Pompeian_Bedroom_3D_FBX.zip", (("dl/Pompeian_Bedroom_3D.fbx.b64.txt", "Pompeian_Bedroom_3D.fbx", "base64"),
                                             ("dl/README.txt", "README.txt", "raw"))),
)


def downloads(sizes: dict[str, str]) -> str:
    buttons = "".join(
        f'<button class="dl" data-name="{d.filename}" data-parts="{escape(json.dumps(d.parts))}"><b>{d.title}</b>'
        f'<span>{d.text}</span><code>{d.filename.rsplit(".", 1)[1].upper()} &middot; {sizes[d.filename]}</code></button>'
        for d in DOWNLOADS)
    return (f'<section class="band" id="downloads"><div class="wrap"><div class="section-head"><div>'
            f'<div class="eyebrow">Files</div><h2>Take it into Autodesk</h2></div><p>The same files the drawings and '
            f'renderings were made from. The 3D view above can also be saved as an image with Save view.</p></div>'
            f'<div class="downloads">{buttons}</div><p id="dl-note"></p></div></section>')


LIGHTBOX = ('<div class="lightbox" id="lightbox" hidden role="dialog" aria-label="Image viewer"><div class="lb-bar">'
            '<button class="lb-prev">Previous</button><button class="lb-next">Next</button>'
            '<button class="lb-zoom">Zoom</button><button class="lb-close">Close</button></div>'
            '<div class="lb-stage"><img alt=""></div><div class="lb-caption"></div></div>')


def page(sizes: dict[str, str]) -> str:
    footer = ('<footer><div class="wrap"><span>Designed and drawn with Claude Code. One Python specification generates '
              'the 3D model, the renderings, the AutoCAD drawings and this page.</span><span>Textures and sky: '
              'Poly Haven (CC0)</span></div></footer>')
    return (head() + header() + f'<main>{explorer()}{renderings()}{drawings()}{specs()}{downloads(sizes)}</main>'
            + footer + LIGHTBOX + f'<script src="{JSZIP}"></script><script type="module" src="explorer/main.js"></script>'
            '<script type="module" src="site.js"></script>')
