// Explorer entry point: wires the toolbar, panels, keyboard and status bar to the viewer.
import * as THREE from 'three';
import { Viewer } from './viewer.js';
import { Navigation, VIEWS } from './navigation.js';
import { Tools } from './tools.js';
import { IN, el, ftIn, roomCoords } from './util.js';

const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const app = $('#explorer');

function webglAvailable() {
  const c = document.createElement('canvas');
  return Boolean(c.getContext('webgl2') || c.getContext('webgl'));
}

const ui = {
  selected(key) {
    const panel = $('#props');
    const empty = $('#props-empty');
    const assembly = key ? viewer.assemblies.get(key) : null;
    panel.hidden = !assembly;
    empty.hidden = Boolean(assembly);
    $$('#objects button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.key === key)));
    if (!assembly) return;
    $('#props-tag').textContent = assembly.tag || '';
    $('#props-tag').hidden = !assembly.tag;
    $('#props-name').textContent = assembly.label;
    $('#props-kind').textContent = assembly.kind;
    $('#props-desc').textContent = assembly.description;
    const size = assembly.box.getSize(new THREE.Vector3());
    $('#props-size').textContent = assembly.size || `${ftIn(size.x / IN)} x ${ftIn(size.z / IN)} x ${ftIn(size.y / IN)}`;
    const min = roomCoords(new THREE.Vector3(assembly.box.min.x, assembly.box.min.y, assembly.box.max.z));
    $('#props-pos').textContent = `${ftIn(min.x)} E, ${ftIn(min.y)} N, ${ftIn(min.z)} up`;
    const finishes = [...new Set(assembly.meshes.map((m) => m.userData.finish))];
    const list = $('#props-finishes');
    list.replaceChildren(...finishes.map((code) => {
      const f = viewer.catalog.finishes[code];
      const row = el('li');
      const chip = el('span', 'chip');
      chip.style.background = f.hex;
      row.append(chip, el('b', '', code), el('span', '', ` ${f.name}`));
      row.title = f.description;
      return row;
    }));
    const tris = assembly.meshes.reduce((n, m) => n + (m.geometry.index ? m.geometry.index.count : 0) / 3, 0);
    $('#props-geo').textContent = `${assembly.meshes.length} mesh${assembly.meshes.length > 1 ? 'es' : ''}, ${Math.round(tris).toLocaleString()} triangles`;
    if (matchMedia('(max-width: 860px)').matches) togglePanel('right', true);
  },
  measured(d) {
    status(`Measured ${ftIn(d.length() / IN)}  (east ${ftIn(Math.abs(d.x) / IN)}, north ${ftIn(Math.abs(d.z) / IN)}, up ${ftIn(Math.abs(d.y) / IN)})`);
  },
};

function status(text) { $('#status-msg').textContent = text; }

function togglePanel(side, force) {
  const panel = $(`#panel-${side}`);
  const open = force ?? panel.hidden;
  panel.hidden = !open;
  $(`[data-action="panel-${side}"]`).setAttribute('aria-pressed', String(open));
}

function setPressed(selector, match) {
  $$(selector).forEach((b) => b.setAttribute('aria-pressed', String(match(b))));
}

let viewer, nav, tools;

async function start() {
  if (!webglAvailable()) {
    $('#loader-msg').textContent = 'This browser cannot show 3D graphics. The renderings and drawings below still work.';
    return;
  }
  viewer = new Viewer($('#viewport'));
  nav = new Navigation(viewer, $('#compass'));
  tools = new Tools(viewer, $('#pins'), ui);
  await viewer.load((f) => { $('#loader-bar').style.width = `${Math.round(f * 100)}%`; });
  buildPanels();
  if (matchMedia('(max-width: 860px)').matches) {
    togglePanel('left', false);
    togglePanel('right', false);
  }
  bindToolbar();
  bindPointer();
  bindKeys();
  nav.setView('iso');
  status('Drag to orbit, right-drag or two fingers to pan, scroll or pinch to zoom. Click anything to inspect it.');
  $('#stat-tris').textContent = `${Math.round(viewer.triangles).toLocaleString()} triangles`;
  $('#loader').hidden = true;
  let last = performance.now();
  const loop = (now) => {
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;
    nav.update(dt);
    if (viewer.dirty || nav.walk.active || tools.measures.length || tools.tagsOn) viewer.render();
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
}

function buildPanels() {
  const layers = $('#layers');
  for (const layer of viewer.catalog.layers) {
    const id = `layer-${layer.key}`;
    const row = el('label', 'layer');
    const box = el('input');
    Object.assign(box, { type: 'checkbox', checked: true, id });
    box.addEventListener('change', () => viewer.setLayer(layer.key, box.checked));
    const count = viewer.meshes.filter((m) => m.userData.layer === layer.key).length;
    row.append(box, el('span', 'layer-name', layer.label), el('code', '', layer.key), el('span', 'count', String(count)));
    layers.append(row);
  }
  const objects = $('#objects');
  const KINDS = ['Furniture & fixtures', 'Openings', 'Architecture'];
  const sorted = [...viewer.assemblies.values()].sort((a, b) =>
    KINDS.indexOf(a.kind) - KINDS.indexOf(b.kind) || a.label.localeCompare(b.label));
  let kind = '';
  for (const a of sorted) {
    if (a.kind !== kind) {
      kind = a.kind;
      objects.append(el('li', 'group', kind));
    }
    const btn = el('button', '', a.label);
    btn.dataset.key = a.key;
    if (a.tag) btn.prepend(el('span', 'tag', a.tag));
    btn.addEventListener('click', () => { tools.select(a.key); nav.fit(a.box.clone().expandByScalar(0.15)); });
    const li = el('li');
    li.append(btn);
    objects.append(li);
  }
  const tours = $('#tours');
  const names = { hero: 'From the door', bed: 'Bed wall', door_wall: 'Door wall', evening: 'Evening', canopy: 'Canopy', plan: 'Overhead' };
  for (const v of viewer.catalog.views) {
    const btn = el('button', '', names[v.key]);
    btn.dataset.tour = v.key;
    btn.addEventListener('click', () => {
      nav.tour(v);
      if (v.key === 'evening' !== viewer.night) toggleNight();
      setPressed('[data-view]', () => false);
    });
    tours.append(btn);
  }
}

function toggleNight() {
  viewer.setNight(!viewer.night);
  $('[data-action="night"]').setAttribute('aria-pressed', String(viewer.night));
  $('#stat-light').textContent = viewer.night ? 'Evening' : 'Afternoon';
}

async function screenshot() {
  viewer.render();
  const blob = await new Promise((resolve) => viewer.renderer.domElement.toBlob(resolve, 'image/png'));
  const downloads = window.claude ? await window.claude.use('downloads') : null;
  if (!downloads) return status('Saving images is not available in this view.');
  downloads.save({ filename: 'Pompeian_Bedroom_view.png', data: blob })
    .then(() => status('Saved Pompeian_Bedroom_view.png'))
    .catch((e) => status(e.code === 'declined' ? 'Save cancelled.' : 'The image could not be saved here.'));
}

function bindToolbar() {
  $$('[data-view]').forEach((b) => b.addEventListener('click', () => {
    nav.setView(b.dataset.view);
    setPressed('[data-view]', (x) => x === b);
    setPressed('[data-action="walk"]', () => false);
  }));
  $$('[data-mode]').forEach((b) => b.addEventListener('click', () => {
    viewer.applyMode(b.dataset.mode);
    tools.refreshSelection();
    setPressed('[data-mode]', (x) => x === b);
    $('#stat-mode').textContent = b.textContent.trim();
  }));
  $$('[data-tool]').forEach((b) => b.addEventListener('click', () => {
    tools.setMode(b.dataset.tool);
    setPressed('[data-tool]', (x) => x === b);
    viewer.renderer.domElement.style.cursor = b.dataset.tool === 'measure' ? 'crosshair' : '';
    status(b.dataset.tool === 'measure' ? 'Click two points to measure between them.' : 'Click anything to inspect it.');
  }));
  const actions = {
    walk: () => {
      if (nav.walk.active) { nav.walk.exit(); app.classList.remove('walking'); return; }
      nav.walk.enter();
      app.classList.add('walking');
      setPressed('[data-view]', () => false);
      status('Walking: drag to look around, W A S D or the arrow pad to move, Esc to stop.');
    },
    night: toggleNight,
    labels: () => {
      tools.setTags(!tools.tagsOn);
      $('[data-action="labels"]').setAttribute('aria-pressed', String(tools.tagsOn));
    },
    cutaway: () => {
      viewer.cutawayOn = !viewer.cutawayOn;
      viewer.dirty = true;
      $('[data-action="cutaway"]').setAttribute('aria-pressed', String(viewer.cutawayOn));
    },
    fit: () => {
      const box = new THREE.Box3();
      for (const m of viewer.pickables()) box.union(new THREE.Box3().setFromObject(m));
      nav.fit(box);
    },
    clear: () => tools.clearMeasures(),
    shot: screenshot,
    full: () => {
      const req = document.fullscreenElement ? document.exitFullscreen() : app.requestFullscreen?.();
      if (req && req.catch) req.catch(() => status('Full screen is not available here.'));
    },
    help: () => { $('#help').hidden = !$('#help').hidden; },
    'panel-left': () => togglePanel('left'),
    'panel-right': () => togglePanel('right'),
    'section-panel': () => {
      const p = $('#section');
      p.hidden = !p.hidden;
      $('[data-action="section-panel"]').setAttribute('aria-pressed', String(!p.hidden));
    },
  };
  $$('[data-action]').forEach((b) => b.addEventListener('click', () => actions[b.dataset.action]()));
  for (const axis of ['height', 'x', 'y']) {
    const on = $(`#cut-${axis}`), range = $(`#cut-${axis}-v`), out = $(`#cut-${axis}-out`);
    const apply = () => {
      out.textContent = ftIn(Number(range.value));
      viewer.setSection(axis, on.checked ? Number(range.value) : null);
    };
    on.addEventListener('change', apply);
    range.addEventListener('input', () => { on.checked = true; apply(); });
    apply();
  }
  $('#iso-only').addEventListener('change', (e) => viewer.isolate(e.target.checked ? tools.selected : null));
  for (const [id, code] of [['pad-up', 'KeyW'], ['pad-down', 'KeyS'], ['pad-left', 'KeyA'], ['pad-right', 'KeyD']]) {
    const b = $(`#${id}`);
    b.addEventListener('pointerdown', (e) => { e.preventDefault(); nav.walk.press(code, true); });
    for (const ev of ['pointerup', 'pointerleave', 'pointercancel']) b.addEventListener(ev, () => nav.walk.press(code, false));
  }
  $$('#compass [data-view]').forEach((b) => b.setAttribute('title', `${VIEWS[b.dataset.view].label} view`));
}

function bindPointer() {
  const dom = viewer.renderer.domElement;
  let down = null, frame = 0, lastMove = null;
  dom.addEventListener('pointerdown', (e) => { down = { x: e.clientX, y: e.clientY }; });
  dom.addEventListener('pointerup', (e) => {
    if (!down || nav.walk.active) return;
    const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y);
    down = null;
    if (moved < 6) tools.click(tools.pick(e.clientX, e.clientY));
  });
  dom.addEventListener('pointermove', (e) => {
    lastMove = e;
    if (frame || nav.walk.active || e.pointerType === 'touch') return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      const hit = tools.pick(lastMove.clientX, lastMove.clientY);
      const tip = $('#tooltip');
      tip.hidden = !hit;
      if (hit) {
        const r = roomCoords(hit.point);
        $('#stat-xyz').textContent = `X ${ftIn(r.x)}  Y ${ftIn(r.y)}  Z ${ftIn(r.z)}`;
        tip.textContent = viewer.assemblies.get(hit.object.userData.assembly).label;
        const rect = dom.getBoundingClientRect();
        tip.style.transform = `translate(${lastMove.clientX - rect.left + 14}px, ${lastMove.clientY - rect.top + 16}px)`;
      }
      tools.hover(hit);
    });
  });
  dom.addEventListener('pointerleave', () => { $('#tooltip').hidden = true; });
}

function bindKeys() {
  const views = { Digit1: 'iso', Digit2: 'top', Digit3: 'north', Digit4: 'south', Digit5: 'east', Digit6: 'west' };
  addEventListener('keydown', (e) => {
    if (e.target.closest('input, textarea') || !app.matches(':hover, :focus-within')) return;
    if (nav.walk.active) {
      if (e.code === 'Escape') { nav.walk.exit(); app.classList.remove('walking'); }
      return;
    }
    if (views[e.code]) $(`[data-view="${views[e.code]}"]`).click();
    if (e.code === 'KeyM') $('[data-tool="measure"]').click();
    if (e.code === 'KeyF') $('[data-action="fit"]').click();
    if (e.code === 'KeyL') $('[data-action="labels"]').click();
    if (e.code === 'KeyN') $('[data-action="night"]').click();
    if (e.code === 'KeyG') $('[data-action="walk"]').click();
    if (e.code === 'Escape') { tools.select(null); $('[data-tool="select"]').click(); $('#help').hidden = true; }
  });
}

start().catch((err) => {
  $('#loader-msg').textContent = `The 3D model could not load (${err.message}). The renderings and drawings below still work.`;
  console.error(err);
});
