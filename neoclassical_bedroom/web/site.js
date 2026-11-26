// Renderings and drawing-sheet viewer (zoom + pan), and downloads through the page's downloads capability.
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];

class Lightbox {
  constructor(root) {
    this.root = root;
    this.stage = $('.lb-stage', root);
    this.img = $('img', root);
    this.caption = $('.lb-caption', root);
    this.items = [];
    this.index = 0;
    this.pointers = new Map();
    this.reset();
    $('.lb-close', root).addEventListener('click', () => this.close());
    $('.lb-prev', root).addEventListener('click', () => this.show(this.index - 1));
    $('.lb-next', root).addEventListener('click', () => this.show(this.index + 1));
    $('.lb-zoom', root).addEventListener('click', () => this.zoomBy(this.scale > 1.01 ? 1 / this.scale : 2.5, null));
    addEventListener('keydown', (e) => {
      if (this.root.hidden) return;
      if (e.key === 'Escape') this.close();
      if (e.key === 'ArrowLeft') this.show(this.index - 1);
      if (e.key === 'ArrowRight') this.show(this.index + 1);
    });
    this.stage.addEventListener('wheel', (e) => { e.preventDefault(); this.zoomBy(Math.exp(-e.deltaY * 0.0015), e); }, { passive: false });
    this.stage.addEventListener('dblclick', (e) => this.zoomBy(this.scale > 1.01 ? 1 / this.scale : 2.5, e));
    this.stage.addEventListener('pointerdown', (e) => {
      this.stage.setPointerCapture(e.pointerId);
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    });
    this.stage.addEventListener('pointermove', (e) => this.move(e));
    for (const ev of ['pointerup', 'pointercancel']) this.stage.addEventListener(ev, (e) => this.pointers.delete(e.pointerId));
  }

  reset() {
    this.scale = 1;
    this.tx = 0;
    this.ty = 0;
    this.apply();
  }

  apply() {
    this.img.style.transform = `translate(${this.tx}px, ${this.ty}px) scale(${this.scale})`;
    this.root.classList.toggle('zoomed', this.scale > 1.01);
  }

  zoomBy(factor, e) {
    const next = Math.min(8, Math.max(1, this.scale * factor));
    const rect = this.stage.getBoundingClientRect();
    const cx = e ? e.clientX - rect.left - rect.width / 2 : 0;
    const cy = e ? e.clientY - rect.top - rect.height / 2 : 0;
    const k = next / this.scale;
    this.tx = cx - (cx - this.tx) * k;
    this.ty = cy - (cy - this.ty) * k;
    this.scale = next;
    if (next === 1) { this.tx = 0; this.ty = 0; }
    this.apply();
  }

  move(e) {
    const prev = this.pointers.get(e.pointerId);
    if (!prev) return;
    if (this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      const before = Math.hypot(a.x - b.x, a.y - b.y);
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      const [c, d] = [...this.pointers.values()];
      const after = Math.hypot(c.x - d.x, c.y - d.y);
      if (before > 0) this.zoomBy(after / before, { clientX: (c.x + d.x) / 2, clientY: (c.y + d.y) / 2 });
      return;
    }
    this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (this.scale > 1) {
      this.tx += e.clientX - prev.x;
      this.ty += e.clientY - prev.y;
      this.apply();
    }
  }

  open(items, index) {
    this.items = items;
    this.root.hidden = false;
    document.documentElement.classList.add('lb-open');
    this.show(index);
    $('.lb-close', this.root).focus();
  }

  show(i) {
    this.index = (i + this.items.length) % this.items.length;
    const item = this.items[this.index];
    this.img.src = item.src;
    this.img.alt = item.title;
    this.caption.replaceChildren();
    const title = document.createElement('b');
    title.textContent = item.title;
    this.caption.append(title, document.createTextNode(item.text ? `  ${item.text}` : ''));
    this.reset();
  }

  close() {
    this.root.hidden = true;
    this.img.removeAttribute('src');
    document.documentElement.classList.remove('lb-open');
  }
}

const lightbox = new Lightbox($('#lightbox'));
for (const gallery of $$('[data-gallery]')) {
  const links = $$('a', gallery);
  const items = links.map((a) => ({ src: a.getAttribute('href'), title: a.dataset.title, text: a.dataset.text }));
  links.forEach((a, i) => a.addEventListener('click', (e) => { e.preventDefault(); lightbox.open(items, i); }));
}

async function payload(name, parts) {
  if (!name.endsWith('.zip')) return fetch(parts[0][0]).then((r) => r.blob());
  const zip = new window.JSZip();
  for (const [url, inner, encoding] of parts) {
    const res = await fetch(url);
    if (encoding === 'base64') zip.file(inner, await res.text(), { base64: true });
    else zip.file(inner, await res.blob());
  }
  return zip.generateAsync({ type: 'blob', compression: 'DEFLATE' });
}

async function setupDownloads() {
  const note = $('#dl-note');
  const downloads = window.claude ? await window.claude.use('downloads') : null;
  const buttons = $$('[data-parts]');
  if (!downloads) {
    buttons.forEach((b) => { b.disabled = true; });
    note.textContent = 'Downloads are not available in this view. Open the page on claude.ai to save the files.';
    return;
  }
  for (const b of buttons) {
    b.addEventListener('click', async () => {
      b.disabled = true;
      note.textContent = `Preparing ${b.dataset.name}…`;
      const data = await payload(b.dataset.name, JSON.parse(b.dataset.parts));
      downloads.save({ filename: b.dataset.name, data })
        .then(() => { note.textContent = `Saved ${b.dataset.name}.`; })
        .catch((e) => {
          note.textContent = e.code === 'declined' ? 'Download cancelled.' : `${b.dataset.name} could not be saved here.`;
        })
        .finally(() => { b.disabled = false; });
    });
  }
}

setupDownloads();
