// Picking, selection with bounding-box dimensions, tape measure and on-screen labels.
import * as THREE from 'three';
import { IN, ROOM, el, ftIn, metresToFtIn } from './util.js';

const GILT = 0xd2a54f;

/** An HTML label pinned to a 3D point (hidden when behind the camera or cut away). */
class Pin {
  constructor(layer, className, text) {
    this.node = el('div', className, text);
    this.point = new THREE.Vector3();
    layer.appendChild(this.node);
  }

  place(viewer, rect) {
    const p = this.point.clone().project(viewer.camera);
    const hidden = p.z > 1 || p.z < -1 || viewer.isClipped(this.point);
    this.node.hidden = hidden;
    if (!hidden) this.node.style.transform = `translate(${(p.x + 1) / 2 * rect.width}px, ${(1 - p.y) / 2 * rect.height}px)`;
  }

  remove() { this.node.remove(); }
}

export class Tools {
  constructor(viewer, overlay, ui) {
    this.viewer = viewer;
    this.overlay = overlay;
    this.ui = ui;
    this.raycaster = new THREE.Raycaster();
    this.raycaster.firstHitOnly = false;
    this.mode = 'select';
    this.selected = null;
    this.swapped = [];
    this.boxHelper = null;
    this.boxPins = [];
    this.measures = [];
    this.pending = null;
    this.tags = [];
    this.tagsOn = false;
    this.rubber = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
      new THREE.LineDashedMaterial({ color: GILT, dashSize: 0.05, gapSize: 0.03, depthTest: false }));
    this.rubber.renderOrder = 10;
    this.rubber.visible = false;
    this.rubberPin = new Pin(overlay, 'pin measure live', '');
    this.rubberPin.node.hidden = true;
    viewer.scene.add(this.rubber);
    viewer.frameHooks.push(() => this.placePins());
  }

  pick(clientX, clientY) {
    const rect = this.viewer.renderer.domElement.getBoundingClientRect();
    const ndc = new THREE.Vector2((clientX - rect.left) / rect.width * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
    this.raycaster.setFromCamera(ndc, this.viewer.camera);
    const hits = this.raycaster.intersectObjects(this.viewer.pickables(), false);
    return hits.find((h) => !this.viewer.isClipped(h.point) && h.object.isMesh) || null;
  }

  setMode(mode) {
    this.mode = mode;
    this.pending = null;
    this.rubber.visible = false;
    this.rubberPin.node.hidden = true;
    this.viewer.dirty = true;
  }

  hover(hit) {
    if (this.mode !== 'measure' || !this.pending) return;
    if (!hit) return;
    const pts = [this.pending, hit.point];
    this.rubber.geometry.setFromPoints(pts);
    this.rubber.computeLineDistances();
    this.rubber.visible = true;
    this.rubberPin.point.copy(this.pending).lerp(hit.point, 0.5);
    this.rubberPin.node.textContent = metresToFtIn(this.pending.distanceTo(hit.point));
    this.viewer.dirty = true;
  }

  click(hit) {
    if (this.mode === 'measure') return hit && this.measurePoint(hit.point.clone());
    this.select(hit ? hit.object.userData.assembly : null);
  }

  measurePoint(point) {
    if (!this.pending) {
      this.pending = point;
      return;
    }
    const a = this.pending, b = point;
    this.pending = null;
    this.rubber.visible = false;
    this.rubberPin.node.hidden = true;
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([a, b]),
      new THREE.LineBasicMaterial({ color: GILT, depthTest: false }));
    line.renderOrder = 10;
    const dots = [a, b].map((p) => {
      const dot = new THREE.Mesh(new THREE.SphereGeometry(0.018, 12, 8), new THREE.MeshBasicMaterial({ color: GILT, depthTest: false }));
      dot.position.copy(p);
      dot.renderOrder = 11;
      dot.raycast = () => {};
      return dot;
    });
    line.raycast = () => {};
    this.viewer.scene.add(line, ...dots);
    const d = b.clone().sub(a);
    const pin = new Pin(this.overlay, 'pin measure', metresToFtIn(d.length()));
    pin.node.title = `Along east ${ftIn(Math.abs(d.x) / IN)}, north ${ftIn(Math.abs(d.z) / IN)}, up ${ftIn(Math.abs(d.y) / IN)}`;
    pin.point.copy(a).lerp(b, 0.5);
    this.measures.push({ objects: [line, ...dots], pin });
    this.ui.measured(d);
    this.viewer.dirty = true;
  }

  clearMeasures() {
    for (const m of this.measures) {
      this.viewer.scene.remove(...m.objects);
      m.pin.remove();
    }
    this.measures = [];
    this.pending = null;
    this.rubber.visible = false;
    this.viewer.dirty = true;
  }

  select(key) {
    for (const [mesh, material] of this.swapped) mesh.material = material;
    this.swapped = [];
    if (this.boxHelper) this.viewer.scene.remove(this.boxHelper);
    this.boxPins.forEach((p) => p.remove());
    this.boxPins = [];
    this.selected = key;
    if (key) {
      const a = this.viewer.assemblies.get(key);
      for (const m of a.meshes) {
        this.swapped.push([m, m.material]);
        m.material = this.viewer.materials.highlight(m.material);
      }
      this.boxHelper = new THREE.Box3Helper(a.box, GILT);
      this.boxHelper.material.depthTest = false;
      this.boxHelper.renderOrder = 9;
      this.viewer.scene.add(this.boxHelper);
      const { min, max } = a.box;
      const dims = [
        [new THREE.Vector3((min.x + max.x) / 2, min.y, max.z), ftIn((max.x - min.x) / IN)],
        [new THREE.Vector3(max.x, min.y, (min.z + max.z) / 2), ftIn((max.z - min.z) / IN)],
        [new THREE.Vector3(max.x, (min.y + max.y) / 2, max.z), ftIn((max.y - min.y) / IN)],
      ];
      for (const [point, text] of dims) {
        const pin = new Pin(this.overlay, 'pin dim', text);
        pin.point.copy(point);
        this.boxPins.push(pin);
      }
    }
    this.ui.selected(key);
    this.viewer.dirty = true;
  }

  /** Re-apply the highlight after the display mode swaps materials. */
  refreshSelection() {
    const key = this.selected;
    this.swapped = [];
    this.select(key);
  }

  setTags(on) {
    this.tagsOn = on;
    if (!this.tags.length) {
      for (const a of this.viewer.assemblies.values()) {
        if (!a.tag) continue;
        const pin = new Pin(this.overlay, 'pin tag', a.tag);
        a.box.getCenter(pin.point);
        pin.point.y = Math.min(a.box.max.y + 0.08, ROOM.H - 0.05);
        this.tags.push(pin);
      }
      const room = [
        [new THREE.Vector3(ROOM.L / 2, 0.02, -0.25), `${ftIn(ROOM.L / IN)} E-W`],
        [new THREE.Vector3(0.25, 0.02, -ROOM.W / 2), `${ftIn(ROOM.W / IN)} N-S`],
        [new THREE.Vector3(ROOM.L - 0.2, ROOM.H / 2, -ROOM.W + 0.2), `${ftIn(ROOM.H / IN)} clg`],
      ];
      for (const [point, text] of room) {
        const pin = new Pin(this.overlay, 'pin room', text);
        pin.point.copy(point);
        this.tags.push(pin);
      }
    }
    this.viewer.dirty = true;
  }

  placePins() {
    const rect = this.viewer.renderer.domElement.getBoundingClientRect();
    const v = this.viewer;
    for (const p of this.tags) {
      if (this.tagsOn) p.place(v, rect); else p.node.hidden = true;
    }
    for (const p of this.boxPins) p.place(v, rect);
    for (const m of this.measures) m.pin.place(v, rect);
    if (this.rubber.visible) this.rubberPin.place(v, rect);
  }
}
