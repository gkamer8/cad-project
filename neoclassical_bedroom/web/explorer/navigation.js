// Orbit / orthographic views, guided tours, walk mode and the compass.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { IN, ROOM, easeInOut } from './util.js';

const C = new THREE.Vector3(ROOM.L / 2, ROOM.H / 2, -ROOM.W / 2);
const EYE = 64 * IN;
const plane = (x, y, z, c) => new THREE.Plane(new THREE.Vector3(x, y, z), c);

// Standard CAD views. Elevations look at one wall from inside the room and keep a 3'-0" slice in front of it.
export const VIEWS = {
  iso: { label: '3D', ortho: false, eye: [C.x + 4.4, 5.2, C.z + 4.9], target: [C.x, 0.75, C.z] },
  top: { label: 'Plan', ortho: true, eye: [C.x, 14, C.z + 0.002], target: [C.x, 0, C.z], span: [ROOM.L, ROOM.W] },
  north: { label: 'N', ortho: true, eye: [C.x, C.y, 14], target: [C.x, C.y, C.z], span: [ROOM.L, ROOM.H],
           clip: plane(0, 0, -1, -(ROOM.W - 36 * IN)) },
  south: { label: 'S', ortho: true, eye: [C.x, C.y, -ROOM.W - 14], target: [C.x, C.y, C.z], span: [ROOM.L, ROOM.H],
           clip: plane(0, 0, 1, 36 * IN) },
  east: { label: 'E', ortho: true, eye: [-14, C.y, C.z], target: [C.x, C.y, C.z], span: [ROOM.W, ROOM.H],
          clip: plane(1, 0, 0, -(ROOM.L - 36 * IN)) },
  west: { label: 'W', ortho: true, eye: [ROOM.L + 14, C.y, C.z], target: [C.x, C.y, C.z], span: [ROOM.W, ROOM.H],
          clip: plane(-1, 0, 0, 92 * IN) },
};

export class Navigation {
  constructor(viewer, compass) {
    this.viewer = viewer;
    this.compass = compass;
    const controls = new OrbitControls(viewer.persp, viewer.renderer.domElement);
    Object.assign(controls, { enableDamping: true, dampingFactor: 0.09, screenSpacePanning: true, zoomToCursor: true,
                              minDistance: 0.25, maxDistance: 30, maxPolarAngle: Math.PI * 0.66 });
    controls.addEventListener('change', () => { viewer.dirty = true; });
    this.controls = controls;
    this.tween = null;
    this.walk = new Walk(this);
    this.view = 'iso';
  }

  _useCamera(ortho) {
    const v = this.viewer;
    v.camera = ortho ? v.ortho : v.persp;
    this.controls.object = v.camera;
    this.controls.maxPolarAngle = ortho ? Math.PI : Math.PI * 0.66;
  }

  setView(key) {
    this.walk.exit();
    const view = VIEWS[key];
    this.view = key;
    this.viewer.viewClip = view.clip || null;
    this._useCamera(view.ortho);
    if (view.ortho) {
      const { clientWidth: w, clientHeight: h } = this.viewer.container;
      const margin = 0.9;
      this.viewer.setOrthoHeight(Math.max(view.span[1] + margin, (view.span[0] + margin) / (w / Math.max(h, 1))));
      this.tween = null;
      this.viewer.camera.position.set(...view.eye);
      this.controls.target.set(...view.target);
      this.controls.update();
    } else {
      this.animateTo(new THREE.Vector3(...view.eye), new THREE.Vector3(...view.target), 55);
    }
    this.viewer.dirty = true;
  }

  /** Camera bookmarks matching the renderings (lens in mm on a 36 mm frame). */
  tour(view) {
    if (view.plan) return this.setView('top');
    this.walk.exit();
    this.view = view.key;
    this.viewer.viewClip = null;
    this._useCamera(false);
    const aspect = this.viewer.persp.aspect;
    const hfov = 2 * Math.atan(18 / view.fov_mm);
    const vfov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(hfov / 2) / aspect));
    this.animateTo(new THREE.Vector3(...view.eye), new THREE.Vector3(...view.target), Math.min(vfov, 80));
  }

  animateTo(eye, target, fov) {
    const cam = this.viewer.persp;
    this.tween = { t: 0, fromEye: cam.position.clone(), fromTarget: this.controls.target.clone(), fromFov: cam.fov,
                   eye, target, fov };
  }

  fit(box) {
    const v = this.viewer;
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    if (v.camera.isOrthographicCamera) {
      const dir = v.camera.position.clone().sub(this.controls.target);
      this.controls.target.copy(center);
      v.camera.position.copy(center).add(dir);
      v.setOrthoHeight(Math.max(size.x, size.y, size.z) * 1.25);
      this.controls.update();
      v.dirty = true;
      return;
    }
    const radius = size.length() / 2;
    const dist = radius / Math.sin(THREE.MathUtils.degToRad(v.persp.fov) / 2) * 0.9;
    const dir = v.camera.position.clone().sub(this.controls.target).normalize();
    this.animateTo(center.clone().addScaledVector(dir, Math.max(dist, 0.6)), center, v.persp.fov);
  }

  update(dt) {
    if (this.walk.active) return this.walk.update(dt);
    if (this.tween) {
      const tw = this.tween;
      tw.t = Math.min(1, tw.t + dt / 1.1);
      const k = easeInOut(tw.t);
      const cam = this.viewer.persp;
      cam.position.lerpVectors(tw.fromEye, tw.eye, k);
      this.controls.target.lerpVectors(tw.fromTarget, tw.target, k);
      cam.fov = tw.fromFov + (tw.fov - tw.fromFov) * k;
      cam.updateProjectionMatrix();
      if (tw.t >= 1) this.tween = null;
      this.viewer.dirty = true;
    }
    this.controls.update();
    const az = this.controls.getAzimuthalAngle();
    this.compass.style.setProperty('--az', `${THREE.MathUtils.radToDeg(az)}deg`);
  }
}

/** First-person walking at 5'-4" eye height: drag (or pointer lock) to look, WASD / arrows / pad to move. */
class Walk {
  constructor(nav) {
    this.nav = nav;
    this.active = false;
    this.keys = new Set();
    this.yaw = Math.PI / 2;
    this.pitch = 0;
    const dom = nav.viewer.renderer.domElement;
    const moveKeys = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']);
    addEventListener('keydown', (e) => {
      if (!this.active) return;
      this.keys.add(e.code);
      if (moveKeys.has(e.code)) e.preventDefault();
    });
    addEventListener('keyup', (e) => this.keys.delete(e.code));
    let drag = null;
    dom.addEventListener('pointerdown', (e) => {
      if (!this.active) return;
      if (e.pointerType === 'mouse' && dom.requestPointerLock && document.pointerLockElement !== dom) {
        const lock = dom.requestPointerLock();
        if (lock && lock.catch) lock.catch(() => {});
      }
      drag = { x: e.clientX, y: e.clientY };
    });
    addEventListener('pointerup', () => { drag = null; });
    addEventListener('pointermove', (e) => {
      if (!this.active) return;
      if (document.pointerLockElement === dom) return this.look(e.movementX, e.movementY);
      if (drag) {
        this.look(e.clientX - drag.x, e.clientY - drag.y);
        drag = { x: e.clientX, y: e.clientY };
      }
    });
  }

  look(dx, dy) {
    this.yaw -= dx * 0.0032;
    this.pitch = THREE.MathUtils.clamp(this.pitch - dy * 0.0032, -1.2, 1.2);
    this.nav.viewer.dirty = true;
  }

  enter() {
    const v = this.nav.viewer;
    this.nav._useCamera(false);
    v.viewClip = null;
    this.nav.tween = null;
    this.active = true;
    this.nav.controls.enabled = false;
    v.persp.position.set(ROOM.L - 0.6, EYE, -ROOM.W / 2);
    v.persp.fov = 68;
    v.persp.updateProjectionMatrix();
    this.yaw = Math.PI / 2;
    this.pitch = -0.05;
    v.dirty = true;
  }

  exit() {
    if (!this.active) return;
    this.active = false;
    this.keys.clear();
    if (document.pointerLockElement) document.exitPointerLock();
    const cam = this.nav.viewer.persp;
    const ahead = new THREE.Vector3(0, 0, -1).applyEuler(cam.rotation).multiplyScalar(1.2);
    this.nav.controls.target.copy(cam.position).add(ahead);
    this.nav.controls.enabled = true;
    this.nav.viewer.dirty = true;
  }

  press(code, down) {
    if (down) this.keys.add(code); else this.keys.delete(code);
  }

  update(dt) {
    const cam = this.nav.viewer.persp;
    const k = this.keys;
    const run = k.has('ShiftLeft') || k.has('ShiftRight') ? 2.2 : 1;
    const f = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    const s = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0);
    const step = 1.25 * run * dt;
    cam.position.x += (-Math.sin(this.yaw) * f + Math.cos(this.yaw) * s) * step;
    cam.position.z += (-Math.cos(this.yaw) * f - Math.sin(this.yaw) * s) * step;
    cam.position.x = THREE.MathUtils.clamp(cam.position.x, 0.3, ROOM.L - 0.3);
    cam.position.z = THREE.MathUtils.clamp(cam.position.z, -ROOM.W + 0.3, -0.3);
    cam.position.y = EYE;
    cam.rotation.set(this.pitch, this.yaw, 0, 'YXZ');
    if (f || s) this.nav.viewer.dirty = true;
    this.nav.compass.style.setProperty('--az', `${THREE.MathUtils.radToDeg(this.yaw)}deg`);
  }
}
