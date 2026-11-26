// Renderer, scene, lighting, model loading, display modes and clipping (cutaway + sections).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { computeBoundsTree, acceleratedRaycast } from 'three-mesh-bvh';
import { IN, ROOM } from './util.js';
import { MaterialLibrary } from './materials.js';

THREE.BufferGeometry.prototype.computeBoundsTree = computeBoundsTree;
THREE.Mesh.prototype.raycast = acceleratedRaycast;

const NO_SHADOW = new Set(['GZ-1', 'GZ-3', 'LT-2']);
const CENTER = new THREE.Vector3(ROOM.L / 2, ROOM.H / 2, -ROOM.W / 2);

// Dollhouse cutaway: when the camera is outside a wall, that wall (and what hugs it) is cut away.
const CUTAWAY = [
  { outside: (c) => c.z > 0.05, plane: new THREE.Plane(new THREE.Vector3(0, 0, -1), -7 * IN) },
  { outside: (c) => c.z < -ROOM.W - 0.05, plane: new THREE.Plane(new THREE.Vector3(0, 0, 1), ROOM.W - 7 * IN) },
  { outside: (c) => c.x < -0.05, plane: new THREE.Plane(new THREE.Vector3(1, 0, 0), -0.6 * IN) },
  { outside: (c) => c.x > ROOM.L + 0.05, plane: new THREE.Plane(new THREE.Vector3(-1, 0, 0), ROOM.L - 1.2 * IN) },
  { outside: (c) => c.y > ROOM.H + 0.05, plane: new THREE.Plane(new THREE.Vector3(0, -1, 0), 88.5 * IN) },
];

/** The GLB ships as base64 text, since artifact pages only serve web file types. */
function decodeBase64(text) {
  const bin = atob(text);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

function loadTexture(loader, url, srgb, repeat) {
  const t = loader.load(url);
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.wrapS = t.wrapT = repeat ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
  t.anisotropy = 8;
  return t;
}

/** Texture coordinates computed from world positions (the CAD model carries none). */
function setUV(mesh, fn) {
  const pos = mesh.geometry.attributes.position;
  const nrm = mesh.geometry.attributes.normal;
  const normalMatrix = new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);
  const uv = new Float32Array(pos.count * 2);
  const p = new THREE.Vector3();
  const n = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    p.fromBufferAttribute(pos, i).applyMatrix4(mesh.matrixWorld);
    n.fromBufferAttribute(nrm, i).applyMatrix3(normalMatrix);
    const [u, v] = fn(p, n);
    uv[2 * i] = u;
    uv[2 * i + 1] = v;
  }
  mesh.geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}

const boxProject = (scale) => (p, n) => {
  const a = [Math.abs(n.x), Math.abs(n.y), Math.abs(n.z)];
  if (a[0] >= a[1] && a[0] >= a[2]) return [p.z / scale, p.y / scale];
  if (a[1] >= a[2]) return [p.x / scale, p.z / scale];
  return [p.x / scale, p.y / scale];
};

export class Viewer {
  constructor(container) {
    this.container = container;
    const r = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    r.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    r.outputColorSpace = THREE.SRGBColorSpace;
    r.toneMapping = THREE.AgXToneMapping;
    r.toneMappingExposure = 1.05;
    r.shadowMap.enabled = true;
    r.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(r.domElement);
    this.renderer = r;
    this.scene = new THREE.Scene();
    this.persp = new THREE.PerspectiveCamera(55, 1, 0.03, 150);
    this.ortho = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.03, 150);
    this.orthoHeight = 4.5;
    this.camera = this.persp;
    this.meshes = [];
    this.assemblies = new Map();
    this.assemblyOfMesh = new Map();
    this.layerVisible = new Map();
    this.mode = 'realistic';
    this.night = false;
    this.cutawayOn = true;
    this.sections = { height: null, x: null, y: null };
    this.viewClip = null;
    this.edgesVisible = false;
    this.dirty = true;
    this.frameHooks = [];
    this.triangles = 0;
    this._lights();
    new ResizeObserver(() => this.resize()).observe(container);
    this.resize();
  }

  _lights() {
    this.hemi = new THREE.HemisphereLight(0xfff0dd, 0x3b2a24, 0.55);
    const sun = new THREE.DirectionalLight(0xffe0bb, 2.8);
    const az = THREE.MathUtils.degToRad(232), el = THREE.MathUtils.degToRad(24);
    const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
    sun.position.copy(CENTER).addScaledVector(dir, 8);
    sun.target.position.copy(CENTER);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -4.5, right: 4.5, top: 4.5, bottom: -4.5, near: 1, far: 18 });
    sun.shadow.bias = -0.0003;
    sun.shadow.normalBias = 0.025;
    this.sun = sun;
    this.scene.add(this.hemi, sun, sun.target);
    this.lamps = new THREE.Group();
    this.scene.add(this.lamps);
  }

  resize() {
    const w = this.container.clientWidth, h = Math.max(this.container.clientHeight, 1);
    this.renderer.setSize(w, h, false);
    this.persp.aspect = w / h;
    this.persp.updateProjectionMatrix();
    this._fitOrtho();
    this.dirty = true;
  }

  _fitOrtho() {
    const { clientWidth: w, clientHeight: h } = this.container;
    const half = this.orthoHeight / 2, aspect = w / Math.max(h, 1);
    Object.assign(this.ortho, { left: -half * aspect, right: half * aspect, top: half, bottom: -half });
    this.ortho.updateProjectionMatrix();
  }

  setOrthoHeight(metres) {
    this.orthoHeight = metres;
    this.ortho.zoom = 1;
    this._fitOrtho();
  }

  async load(onProgress) {
    const textureLoader = new THREE.TextureLoader();
    const textures = {
      parquet: loadTexture(textureLoader, 'tex/parquet.jpg', true, true),
      parquetNormal: loadTexture(textureLoader, 'tex/parquet_normal.jpg', false, true),
      rug: loadTexture(textureLoader, 'tex/rug.jpg', true, false),
      damask: loadTexture(textureLoader, 'tex/damask.jpg', true, true),
    };
    const [catalog, glb, sky] = await Promise.all([
      fetch('data/catalog.json').then((r) => r.json()),
      new THREE.FileLoader().loadAsync('model/bedroom.glb.b64.txt', (e) => onProgress(e.total ? e.loaded / e.total : 0)),
      textureLoader.loadAsync('tex/garden.jpg'),
    ]);
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(decodeBase64(glb), '');
    this.catalog = catalog;
    this.materials = new MaterialLibrary(catalog.finishes, textures);
    sky.mapping = THREE.EquirectangularReflectionMapping;
    sky.colorSpace = THREE.SRGBColorSpace;
    this.background = sky;
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromEquirectangular(sky).texture;
    pmrem.dispose();
    this._addModel(gltf.scene, catalog);
    this._addLamps(catalog.lamps);
    this.setNight(false);
  }

  _addModel(root, catalog) {
    root.updateMatrixWorld(true);
    const partToAssembly = new Map();
    for (const [key, a] of Object.entries(catalog.assemblies)) {
      this.assemblies.set(key, { key, ...a, meshes: [] });
      for (const name of a.parts) partToAssembly.set(name, key);
    }
    for (const layer of catalog.layers) this.layerVisible.set(layer.key, true);
    root.traverse((o) => {
      if (!o.isMesh) return;
      const info = catalog.parts[o.name];
      o.userData = { part: o.name, finish: info.finish, layer: info.layer, assembly: partToAssembly.get(o.name) };
      o.castShadow = !NO_SHADOW.has(info.finish);
      o.receiveShadow = true;
      o.geometry.computeBoundsTree();
      this.triangles += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3;
      this.meshes.push(o);
      this.assemblies.get(o.userData.assembly).meshes.push(o);
      this.assemblyOfMesh.set(o, o.userData.assembly);
    });
    const byName = (n) => this.meshes.find((m) => m.name === n);
    setUV(byName('floor_parquet'), (p) => [p.x / 3.4, -p.z / 3.4]);
    const rug = new THREE.Box3().setFromObject(byName('rug'));
    setUV(byName('rug'), (p) => [(p.x - rug.min.x) / (rug.max.x - rug.min.x), (rug.max.z - p.z) / (rug.max.z - rug.min.z)]);
    for (const name of ['damask_panel', 'bedding_damask']) setUV(byName(name), boxProject(0.55));
    for (const a of this.assemblies.values()) {
      a.box = new THREE.Box3();
      for (const m of a.meshes) a.box.union(new THREE.Box3().setFromObject(m));
    }
    this.scene.add(root);
    this.model = root;
    this.applyMode(this.mode);
  }

  _addLamps(lamps) {
    const clusters = [];
    for (const l of lamps) {
      const p = new THREE.Vector3(...l.position);
      const near = clusters.find((c) => c.pos.distanceTo(p) < 0.35);
      if (near) {
        near.pos.multiplyScalar(near.n).add(p).multiplyScalar(1 / (near.n + 1));
        near.n += 1;
        near.watts += l.watts;
      } else clusters.push({ pos: p, n: 1, watts: l.watts, color: new THREE.Color(...l.color) });
    }
    for (const c of clusters) {
      const light = new THREE.PointLight(c.color, 0, 0, 2);
      light.position.copy(c.pos);
      light.userData.watts = c.watts;
      this.lamps.add(light);
    }
  }

  setNight(night) {
    this.night = night;
    this.materials.setNight(night);
    this.sun.visible = !night;
    this.hemi.intensity = night ? 0.03 : 0.55;
    this.hemi.color.set(night ? 0x8090c0 : 0xfff0dd);
    for (const l of this.lamps.children) l.intensity = l.userData.watts * (night ? 0.06 : 0.02);
    this.renderer.toneMappingExposure = night ? 1.25 : 1.05;
    this._backgroundKey = null;
    this.dirty = true;
  }

  _background() {
    const c = this.camera.position;
    const inside = c.x > 0 && c.x < ROOM.L && c.z < 0 && c.z > -ROOM.W && c.y > 0 && c.y < ROOM.H;
    const sky = this.mode === 'realistic' && inside;
    const key = `${sky}:${this.night}`;
    if (key === this._backgroundKey) return;
    this._backgroundKey = key;
    this.scene.background = sky && !this.night ? this.background : new THREE.Color(sky ? '#0b0f1c' : '#191413');
    this.scene.backgroundIntensity = 0.9;
  }

  applyMode(mode) {
    this.mode = mode;
    for (const m of this.meshes) m.material = this.materials.get(mode, m.userData.finish);
    this.renderer.shadowMap.enabled = mode === 'realistic' || mode === 'clay';
    this.sun.castShadow = this.renderer.shadowMap.enabled;
    for (const m of this.materials.cache.values()) m.needsUpdate = true;
    this._backgroundKey = null;
    this.setEdges(mode === 'shaded' || mode === 'clay' || mode === 'xray');
    this.dirty = true;
  }

  setEdges(visible) {
    this.edgesVisible = visible;
    const color = this.mode === 'xray' ? 0xd9c7a8 : 0x2a201c;
    for (const m of this.meshes) {
      if (visible && !m.userData.edges) {
        const lines = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry, 32),
          new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.55 }));
        lines.raycast = () => {};
        m.add(lines);
        m.userData.edges = lines;
      }
      if (m.userData.edges) {
        m.userData.edges.visible = visible;
        m.userData.edges.material.color.set(color);
      }
    }
    this.dirty = true;
  }

  setLayer(layer, visible) {
    this.layerVisible.set(layer, visible);
    for (const m of this.meshes) if (m.userData.layer === layer) m.visible = visible;
    this.dirty = true;
  }

  isolate(assemblyKey) {
    for (const m of this.meshes) {
      m.visible = assemblyKey ? m.userData.assembly === assemblyKey : this.layerVisible.get(m.userData.layer);
    }
    this.dirty = true;
  }

  setSection(axis, value) {
    // value in inches, or null to remove. height: keep below; x: keep west of; y: keep south of.
    const planes = {
      height: (v) => new THREE.Plane(new THREE.Vector3(0, -1, 0), v * IN),
      x: (v) => new THREE.Plane(new THREE.Vector3(-1, 0, 0), v * IN),
      y: (v) => new THREE.Plane(new THREE.Vector3(0, 0, 1), v * IN),
    };
    this.sections[axis] = value === null ? null : planes[axis](value);
    this.dirty = true;
  }

  activePlanes() {
    const cam = this.camera.position;
    const planes = [];
    if (this.cutawayOn) for (const c of CUTAWAY) if (c.outside(cam)) planes.push(c.plane);
    for (const p of Object.values(this.sections)) if (p) planes.push(p);
    if (this.viewClip) planes.push(this.viewClip);
    return planes;
  }

  isClipped(point) {
    return this.renderer.clippingPlanes.some((p) => p.distanceToPoint(point) < 0);
  }

  pickables() {
    return this.meshes.filter((m) => m.visible);
  }

  render() {
    this.renderer.clippingPlanes = this.activePlanes();
    this._background();
    for (const hook of this.frameHooks) hook();
    this.renderer.render(this.scene, this.camera);
    this.dirty = false;
  }

  center() {
    return CENTER.clone();
  }
}
