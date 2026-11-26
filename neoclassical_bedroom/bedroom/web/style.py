"""Stylesheet for the showcase site (single deliberate dark theme: a drafting room at night)."""

CSS = """
/* Layout: a dark drafting-room shell. The 3D explorer runs full width like a CAD workspace;
   renderings, sheets and schedules follow on a 1240px column. */
:root {
  --ink: #15100f;
  --well: #1e1816;
  --well-2: #261e1b;
  --rule: #3c2f2a;
  --ivory: #efe6d6;
  --dust: #a99b8c;
  --gilt: #cfa555;
  --pompeian: #9b2c22;
  --display: 'Bodoni Moda', 'Bodoni 72', Didot, 'Times New Roman', serif;
  --text: 'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  --gutter-l: max(16px, env(safe-area-inset-left, 0px));
  --gutter-r: max(16px, env(safe-area-inset-right, 0px));
  color-scheme: dark;
}
html { scroll-behavior: smooth; }
html.lb-open { overflow: hidden; }
body { background: var(--ink); color: var(--ivory); font-family: var(--text); font-size: 15px; line-height: 1.55; }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10;
               background: var(--ink); }
a { color: var(--gilt); }
button { font: inherit; color: inherit; }
:focus-visible { outline: 2px solid var(--gilt); outline-offset: 2px; }
.wrap { max-width: 1240px; margin: 0 auto; padding-left: var(--gutter-l); padding-right: var(--gutter-r); }
.eyebrow { font: 500 11px/1 var(--mono); letter-spacing: .22em; text-transform: uppercase; color: var(--gilt); }
h1, h2, h3 { font-family: var(--display); font-weight: 500; text-wrap: balance; margin: 0; }
h2 { font-size: clamp(30px, 4vw, 46px); line-height: 1.05; font-style: italic; }
h3 { font-size: 22px; }
p { max-width: 65ch; }

/* header */
.top { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 20; background: rgba(21, 16, 15, .92);
       backdrop-filter: blur(8px); border-bottom: 1px solid var(--rule); }
.top .wrap { display: flex; align-items: center; gap: 24px; padding-block: 12px; }
.brand { font: italic 500 21px/1 var(--display); color: var(--ivory); text-decoration: none; white-space: nowrap; }
.top nav { display: flex; gap: 20px; overflow-x: auto; scrollbar-width: none; margin-left: auto; }
.top nav a { color: var(--dust); text-decoration: none; font-size: 13px; letter-spacing: .04em; white-space: nowrap; }
.top nav a:hover { color: var(--ivory); }

/* intro */
.intro { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr); gap: 28px 48px; align-items: end;
         padding-block: 40px 26px; }
.intro h1 { font-size: clamp(44px, 7vw, 88px); line-height: .95; font-style: italic; margin-top: 12px; }
.intro .lede { color: var(--dust); margin: 16px 0 0; font-size: 16px; }
.facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; background: var(--rule);
         border: 1px solid var(--rule); }
.facts div { background: var(--ink); padding: 12px 14px; }
.facts dt { font: 500 10px/1.2 var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--dust); }
.facts dd { margin: 6px 0 0; font: 500 18px/1.2 var(--mono); font-variant-numeric: tabular-nums; }

/* explorer */
.app-wrap { padding-left: var(--gutter-l); padding-right: var(--gutter-r); }
.app { display: grid; grid-template-rows: auto minmax(0, 1fr) auto; height: clamp(540px, 82vh, 880px);
       border: 1px solid var(--rule); background: var(--well); position: relative; }
.app:fullscreen { height: 100%; border: 0; }
.toolbar { display: flex; flex-wrap: wrap; gap: 6px 14px; padding: 8px 10px; border-bottom: 1px solid var(--rule);
           background: var(--well-2); align-items: center; }
.group { display: flex; gap: 2px; align-items: center; }
.group + .group { padding-left: 14px; border-left: 1px solid var(--rule); }
.tb { background: transparent; border: 1px solid transparent; border-radius: 4px; padding: 5px 9px; cursor: pointer;
      font-size: 12.5px; color: var(--dust); white-space: nowrap; line-height: 1.2; }
.tb:hover { color: var(--ivory); background: rgba(239, 230, 214, .06); }
.tb[aria-pressed="true"] { color: var(--ink); background: var(--gilt); }
.tb kbd { font: 10px var(--mono); opacity: .6; margin-left: 4px; }
.workspace { display: flex; min-height: 0; position: relative; }
.panel { width: 270px; flex: none; overflow-y: auto; background: var(--well); padding: 14px 14px 18px;
         border-right: 1px solid var(--rule); }
.panel.right { border-right: 0; border-left: 1px solid var(--rule); width: 300px; }
.panel h4 { font: 500 10.5px/1 var(--mono); letter-spacing: .18em; text-transform: uppercase; color: var(--dust);
            margin: 4px 0 10px; }
.panel h4 + * { margin-bottom: 18px; }
.layer { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 2px 8px; align-items: center;
         padding: 5px 0; font-size: 13px; cursor: pointer; }
.layer code { grid-column: 2; font: 10.5px var(--mono); color: var(--dust); }
.layer .count { grid-row: 1; grid-column: 3; font: 11px var(--mono); color: var(--dust); }
.layer input { accent-color: var(--gilt); grid-row: span 2; }
.objects { list-style: none; margin: 0; padding: 0; }
.objects .group { font: 500 10px/1 var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--gilt);
                  padding: 12px 0 6px; border: 0; }
.objects button { display: flex; gap: 8px; align-items: baseline; width: 100%; text-align: left; background: none;
                  border: 0; padding: 5px 6px; border-radius: 3px; cursor: pointer; font-size: 13px; color: var(--ivory); }
.objects button:hover { background: rgba(239, 230, 214, .06); }
.objects button[aria-pressed="true"] { background: rgba(207, 165, 85, .16); }
.tag { font: 500 10.5px var(--mono); color: var(--gilt); min-width: 26px; }
.iso { display: flex; gap: 8px; align-items: center; font-size: 12.5px; color: var(--dust); }
.iso input { accent-color: var(--gilt); }
.stage { position: relative; flex: 1; min-width: 0; overflow: hidden; background: #191413; touch-action: none; }
#viewport, #viewport canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
#pins { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.pin { position: absolute; left: 0; top: 0; white-space: nowrap; font: 500 11px/1 var(--mono); padding: 4px 6px;
       border-radius: 3px; margin: -10px 0 0 -14px; font-variant-numeric: tabular-nums; }
.pin.tag { background: var(--ink); color: var(--gilt); border: 1px solid var(--gilt); }
.pin.room { background: rgba(21, 16, 15, .8); color: var(--ivory); }
.pin.dim { background: var(--gilt); color: var(--ink); }
.pin.measure { background: var(--ivory); color: var(--ink); }
.pin.measure.live { background: var(--gilt); }
#tooltip { position: absolute; left: 0; top: 0; pointer-events: none; background: rgba(21, 16, 15, .9); color: var(--ivory);
           font-size: 12px; padding: 4px 8px; border-radius: 3px; border: 1px solid var(--rule); white-space: nowrap; }
.compass { position: absolute; top: 12px; right: calc(12px + env(safe-area-inset-right, 0px)); width: 92px; height: 92px; }
.compass .ring { position: absolute; inset: 0; border: 1px solid var(--rule); border-radius: 50%;
                 background: rgba(21, 16, 15, .72); transform: rotate(var(--az, 0deg)); }
.compass .ring button { position: absolute; width: 26px; height: 26px; margin: -13px; border: 0; border-radius: 50%;
                        background: none; color: var(--dust); font: 600 12px/26px var(--mono); cursor: pointer;
                        transform: rotate(calc(-1 * var(--az, 0deg))); padding: 0; }
.compass .ring button:hover { color: var(--gilt); }
.compass .n { left: 50%; top: 12px; color: var(--gilt) !important; }
.compass .s { left: 50%; top: calc(100% - 12px); }
.compass .e { left: calc(100% - 12px); top: 50%; }
.compass .w { left: 12px; top: 50%; }
.compass .top-btn { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); background: var(--well-2);
                    border: 1px solid var(--rule); color: var(--ivory); border-radius: 4px; font: 500 10px var(--mono);
                    letter-spacing: .1em; padding: 4px 6px; cursor: pointer; }
.tours { position: absolute; left: calc(12px + env(safe-area-inset-left, 0px)); right: 120px; bottom: 12px; display: flex;
         gap: 6px; flex-wrap: wrap; }
.tours::before { content: 'Viewpoints'; font: 500 10px/26px var(--mono); letter-spacing: .16em; text-transform: uppercase;
                 color: var(--dust); margin-right: 4px; }
.tours button { background: rgba(21, 16, 15, .78); border: 1px solid var(--rule); color: var(--ivory); border-radius: 13px;
                padding: 4px 11px; font-size: 12px; cursor: pointer; flex: none; white-space: nowrap; }
.tours button:hover { border-color: var(--gilt); }
.floating { position: absolute; background: rgba(30, 24, 22, .96); border: 1px solid var(--rule); border-radius: 6px;
            padding: 14px 16px; box-shadow: 0 12px 40px rgba(0, 0, 0, .45); }
.section-panel { top: 12px; left: calc(12px + env(safe-area-inset-left, 0px)); width: min(320px, calc(100% - 140px)); }
.section-panel label { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 2px 8px; align-items: center;
                       font-size: 12.5px; margin-bottom: 12px; }
.section-panel input[type=range] { grid-column: 1 / -1; width: 100%; accent-color: var(--gilt); }
.section-panel output { font: 12px var(--mono); color: var(--gilt); justify-self: end; grid-row: 1; grid-column: 2; }
.section-panel small { display: block; color: var(--dust); font-size: 11.5px; }
.help { inset: 50% auto auto 50%; transform: translate(-50%, -50%); width: min(560px, calc(100% - 32px));
        max-height: calc(100% - 32px); overflow-y: auto; }
.help dl { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr); gap: 6px 16px; font-size: 13px; margin: 12px 0 0; }
.help dt { font: 12px var(--mono); color: var(--gilt); }
.help dd { margin: 0; color: var(--ivory); }
.loader { position: absolute; inset: 0; display: grid; place-items: center; text-align: center; z-index: 5; }
.loader img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; filter: brightness(.42) saturate(.9); }
.loader .box { position: relative; width: min(360px, 80%); }
.loader .bar { height: 2px; background: var(--rule); margin: 14px 0 10px; }
.loader .bar i { display: block; height: 100%; width: 0; background: var(--gilt); transition: width .2s; }
.loader p { margin: 0 auto; font-size: 13px; color: var(--ivory); }
.walkpad { position: absolute; right: calc(16px + env(safe-area-inset-right, 0px)); bottom: 16px; display: none;
           grid-template-columns: repeat(3, 48px); grid-template-rows: repeat(2, 48px); gap: 6px; }
.walking .walkpad { display: grid; }
.walking .tours { display: none; }
.walkpad button { background: rgba(21, 16, 15, .8); border: 1px solid var(--rule); border-radius: 6px; color: var(--ivory);
                  font-size: 18px; touch-action: none; user-select: none; }
.walkpad #pad-up { grid-column: 2; }
.walkpad #pad-left { grid-row: 2; grid-column: 1; }
.walkpad #pad-down { grid-row: 2; grid-column: 2; }
.walkpad #pad-right { grid-row: 2; grid-column: 3; }
.statusbar { display: flex; gap: 18px; align-items: center; padding: 6px 12px; border-top: 1px solid var(--rule);
             font: 11.5px var(--mono); color: var(--dust); background: var(--well-2); overflow: hidden; white-space: nowrap; }
.statusbar #status-msg { margin-left: auto; overflow: hidden; text-overflow: ellipsis; color: var(--ivory); }
#stat-xyz { color: var(--gilt); min-width: 230px; font-variant-numeric: tabular-nums; }
.props dl { display: grid; grid-template-columns: 74px minmax(0, 1fr); gap: 8px 10px; margin: 14px 0 0; font-size: 13px; }
.props dt { font: 500 10px/1.6 var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--dust); }
.props dd { margin: 0; font-variant-numeric: tabular-nums; }
.props h3 { font-size: 24px; margin-top: 6px; }
.props .ptag { font: 500 12px var(--mono); color: var(--ink); background: var(--gilt); padding: 2px 6px; border-radius: 3px; }
.props ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 6px; }
.props li { display: flex; gap: 8px; align-items: center; font-size: 12.5px; }
.props li b { font: 500 11.5px var(--mono); }
.chip { width: 16px; height: 16px; border-radius: 50%; flex: none; border: 1px solid rgba(239, 230, 214, .25); }
.props-empty { color: var(--dust); font-size: 13px; }

/* sections */
section.band { padding-block: 72px 24px; }
.section-head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px; align-items: end;
                margin-bottom: 28px; }
.section-head p { color: var(--dust); margin: 0; }
.renders { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 12px; }
.renders a { position: relative; display: block; overflow: hidden; border-radius: 2px; grid-column: span 3; }
.renders a:nth-child(1), .renders a:nth-child(2) { grid-column: span 6; }
.renders img { display: block; width: 100%; aspect-ratio: 3 / 2; object-fit: cover; transition: transform .6s; }
.renders a:hover img { transform: scale(1.03); }
.renders figcaption { position: absolute; inset: auto 0 0 0; padding: 26px 14px 12px; font-size: 13px; color: var(--ivory);
                      background: linear-gradient(transparent, rgba(12, 8, 7, .85)); }
.renders figcaption b { display: block; font: italic 500 18px/1.2 var(--display); }
.sheets { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; }
.sheets a { display: block; color: var(--ivory); text-decoration: none; }
.sheets img { display: block; width: 100%; aspect-ratio: 17 / 11; object-fit: cover; background: #fff; border-radius: 2px;
              box-shadow: 0 10px 30px rgba(0, 0, 0, .35); }
.sheets .num { font: 500 12px var(--mono); color: var(--gilt); margin-top: 10px; display: block; }
.sheets .title { font-size: 13px; color: var(--ivory); }
.specs { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 40px; }
.kv { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.3fr); gap: 8px 16px; margin: 14px 0 28px;
      font-size: 14px; }
.kv dt { color: var(--dust); }
.kv dd { margin: 0; font-variant-numeric: tabular-nums; }
.swatches { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 18px; margin-top: 14px; }
.sw { display: flex; gap: 12px; align-items: center; min-width: 0; }
.sw .chip { width: 38px; height: 38px; }
.sw b { display: block; font: 500 12px var(--mono); color: var(--gilt); }
.sw span { font-size: 13px; }
.table-scroll { overflow-x: auto; margin-top: 14px; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; min-width: 620px; }
th { text-align: left; font: 500 10.5px/1.2 var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--dust);
     border-bottom: 1px solid var(--gilt); padding: 8px 10px 8px 0; }
td { border-bottom: 1px solid var(--rule); padding: 10px 10px 10px 0; vertical-align: top; }
td.t { font: 500 12.5px var(--mono); color: var(--gilt); white-space: nowrap; }
td small { display: block; color: var(--dust); font-size: 12.5px; margin-top: 2px; }
.downloads { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
.dl { display: flex; flex-direction: column; gap: 6px; text-align: left; background: var(--well); border: 1px solid var(--rule);
      border-radius: 4px; padding: 16px; cursor: pointer; }
.dl:hover:not(:disabled) { border-color: var(--gilt); }
.dl:disabled { opacity: .55; cursor: default; }
.dl b { font: italic 500 19px/1.2 var(--display); }
.dl span { font-size: 12.5px; color: var(--dust); }
.dl code { font: 500 11px var(--mono); color: var(--gilt); }
#dl-note { color: var(--dust); font-size: 13px; min-height: 1.5em; }
footer { border-top: 1px solid var(--rule); margin-top: 72px; }
footer .wrap { padding-block: 28px 40px; color: var(--dust); font-size: 13px; display: flex; flex-wrap: wrap;
               gap: 8px 24px; justify-content: space-between; }

/* lightbox */
.lightbox { position: fixed; inset: 0; z-index: 50; background: rgba(10, 7, 6, .96); display: grid;
            grid-template-rows: auto minmax(0, 1fr) auto; padding: env(safe-area-inset-top, 0px)
            env(safe-area-inset-right, 0px) env(safe-area-inset-bottom, 0px) env(safe-area-inset-left, 0px); }
.lb-bar { display: flex; gap: 8px; justify-content: flex-end; padding: 10px var(--gutter-r) 10px var(--gutter-l); }
.lb-bar button { background: var(--well); border: 1px solid var(--rule); color: var(--ivory); border-radius: 4px;
                 padding: 6px 12px; cursor: pointer; font-size: 13px; }
.lb-stage { position: relative; overflow: hidden; touch-action: none; display: grid; place-items: center; cursor: zoom-in; }
.lightbox.zoomed .lb-stage { cursor: grab; }
.lb-stage img { max-width: 100%; max-height: 100%; transform-origin: center; user-select: none; -webkit-user-drag: none; }
.lb-caption { padding: 12px var(--gutter-r) 18px var(--gutter-l); color: var(--dust); font-size: 13.5px; text-align: center; }
.lb-caption b { color: var(--ivory); font: italic 500 18px var(--display); margin-right: 8px; }

@media (max-width: 1100px) {
  .downloads { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sheets { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 860px) {
  .intro, .section-head, .specs { grid-template-columns: minmax(0, 1fr); }
  .app { height: clamp(520px, 78vh, 760px); }
  .toolbar { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: thin; }
  .panel { position: absolute; z-index: 6; top: 0; bottom: 0; left: 0; width: min(300px, 86%);
           box-shadow: 12px 0 40px rgba(0, 0, 0, .5); }
  .panel.right { left: auto; right: 0; width: min(320px, 90%); }
  .renders { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .renders a { grid-column: span 1; }
  .renders a:nth-child(1), .renders a:nth-child(2) { grid-column: 1 / -1; }
  .sheets { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tours { right: 12px; bottom: 10px; flex-wrap: nowrap; overflow-x: auto; }
  .tours::before { display: none; }
  .statusbar .wide { display: none; }
  #stat-xyz { min-width: 0; }
}
@media (max-width: 520px) {
  .downloads, .swatches { grid-template-columns: minmax(0, 1fr); }
  .compass { width: 76px; height: 76px; }
  .facts dd { font-size: 15px; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .renders img, .loader .bar i { transition: none; }
}
"""
