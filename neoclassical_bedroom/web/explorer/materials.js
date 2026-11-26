// Materials per finish code (P-1, GL-1 ...) for each display mode.
import * as THREE from 'three';

// Physically based settings for the "Realistic" mode, keyed on the finish schedule codes.
const PBR = {
  'P-1': { rough: 0.7, env: 0.42 },
  'P-2': { rough: 0.42, env: 0.5 },
  'P-3': { rough: 0.9, env: 0.4 },
  'P-4': { rough: 0.95, env: 0.3 },
  'GL-1': { color: '#d6aa58', metal: 1, rough: 0.3, env: 1.2 },
  'WD-1': { rough: 0.48, env: 0.5, map: 'parquet', normal: 'parquetNormal' },
  'WD-2': { color: '#120d0b', rough: 0.3, env: 0.9, clearcoat: 1, clearcoatRough: 0.06 },
  'ST-1': { color: '#f1eee9', rough: 0.12, env: 0.85 },
  'FB-1': { rough: 0.62, env: 0.45, map: 'damask', sheen: 0.6, sheenColor: '#ff9e8f' },
  'FB-2': { rough: 0.5, env: 0.45, sheen: 1, sheenColor: '#ff8d80', sheenRough: 0.35, double: true },
  'FB-3': { rough: 0.88, env: 0.4, sheen: 1, sheenColor: '#ff7070', sheenRough: 0.3 },
  'FB-4': { rough: 0.5, env: 0.45, sheen: 0.9, sheenColor: '#fff2dc', sheenRough: 0.35, double: true },
  'FB-5': { rough: 0.78, env: 0.45, sheen: 0.4, sheenColor: '#ffffff' },
  'RG-1': { rough: 0.95, env: 0.35, map: 'rug', sheen: 0.5, sheenColor: '#ffc9b8' },
  'MT-1': { color: '#e2b764', metal: 1, rough: 0.24, env: 1.15 },
  'CR-1': { color: '#f6f3ee', rough: 0.15, env: 0.8, clearcoat: 1, clearcoatRough: 0.03 },
  'LS-1': { rough: 0.85, env: 0.4, double: true, glow: '#ffcf8f' },
  'LS-2': { rough: 0.35, env: 0.7, clearcoat: 0.6, double: true },
  'GZ-1': { glass: true },
  'GZ-2': { color: '#e3e7ea', metal: 1, rough: 0.03, env: 1.3 },
  'GZ-3': { crystal: true },
  'LT-1': { rough: 0.5, env: 0.4 },
  'LT-2': { bulb: true },
};

const SEE_THROUGH = new Set(['GZ-1', 'GZ-3']);
const ENV_GAIN = 1.7; // the sky ships as an 8-bit JPEG, so reflections need a lift
const GILT = new THREE.Color('#c99a3a');

function realistic(code, hex, tex) {
  const s = PBR[code];
  if (s.glass) {
    return new THREE.MeshPhysicalMaterial({ color: 0xe4f2f4, roughness: 0.02, transparent: true, opacity: 0.12,
      envMapIntensity: 1.1, depthWrite: false, side: THREE.DoubleSide });
  }
  if (s.crystal) {
    return new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.02, transparent: true, opacity: 0.6,
      envMapIntensity: 2.6, iridescence: 0.5, iridescenceIOR: 1.5, depthWrite: false });
  }
  if (s.bulb) {
    const m = new THREE.MeshStandardMaterial({ color: 0xfff1d8, emissive: new THREE.Color(hex), emissiveIntensity: 1.2 });
    m.userData.bulb = true;
    return m;
  }
  const physical = Boolean(s.sheen || s.clearcoat);
  const Material = physical ? THREE.MeshPhysicalMaterial : THREE.MeshStandardMaterial;
  const m = new Material({
    color: new THREE.Color(s.map ? '#ffffff' : (s.color || hex)), roughness: s.rough, metalness: s.metal || 0,
    envMapIntensity: s.env * ENV_GAIN, side: s.double ? THREE.DoubleSide : THREE.FrontSide,
  });
  if (s.map) m.map = tex[s.map];
  if (s.normal) { m.normalMap = tex[s.normal]; m.normalScale.set(0.55, 0.55); }
  if (s.sheen) { m.sheen = s.sheen; m.sheenColor = new THREE.Color(s.sheenColor); m.sheenRoughness = s.sheenRough || 0.5; }
  if (s.clearcoat) { m.clearcoat = s.clearcoat; m.clearcoatRoughness = s.clearcoatRough || 0.1; }
  if (s.glow) { m.emissive = new THREE.Color(s.glow); m.emissiveIntensity = 0; m.userData.glow = true; }
  m.userData.baseEnv = s.env * ENV_GAIN;
  return m;
}

const BUILDERS = {
  realistic,
  shaded: (code, hex) => new THREE.MeshLambertMaterial({ color: hex, side: THREE.DoubleSide,
    transparent: SEE_THROUGH.has(code), opacity: SEE_THROUGH.has(code) ? 0.25 : 1 }),
  clay: (code) => new THREE.MeshStandardMaterial({ color: 0xf2eee7, roughness: 0.92, envMapIntensity: 0.55,
    side: THREE.DoubleSide, transparent: SEE_THROUGH.has(code), opacity: SEE_THROUGH.has(code) ? 0.3 : 1 }),
  wire: (code, hex) => new THREE.MeshBasicMaterial({ color: new THREE.Color(hex).lerp(new THREE.Color('#ffffff'), 0.35),
    wireframe: true }),
  xray: (code, hex) => new THREE.MeshBasicMaterial({ color: hex, transparent: true, opacity: 0.08, depthWrite: false,
    side: THREE.DoubleSide }),
};

export const MODES = Object.keys(BUILDERS);

export class MaterialLibrary {
  constructor(finishes, textures) {
    this.finishes = finishes;
    this.textures = textures;
    this.cache = new Map();
    this.highlights = new WeakMap();
  }

  get(mode, code) {
    const key = `${mode}:${code}`;
    if (!this.cache.has(key)) this.cache.set(key, BUILDERS[mode](code, this.finishes[code].hex, this.textures));
    return this.cache.get(key);
  }

  /** Gilt-tinted twin of a material, used to show the current selection. */
  highlight(material) {
    if (!this.highlights.has(material)) {
      const twin = material.clone();
      if (twin.emissive) {
        twin.emissive = GILT.clone();
        twin.emissiveIntensity = 0.32;
      } else {
        twin.color = GILT.clone();
        twin.opacity = Math.max(twin.opacity, 0.35);
      }
      this.highlights.set(material, twin);
    }
    return this.highlights.get(material);
  }

  /** Day or night: environment strength, bulbs and lamp-shade glow. */
  setNight(night) {
    for (const [key, m] of this.cache) {
      if (!key.startsWith('realistic:')) continue;
      if (m.userData.baseEnv !== undefined) m.envMapIntensity = m.userData.baseEnv * (night ? 0.12 : 1);
      if (m.userData.bulb) m.emissiveIntensity = night ? 9 : 1.2;
      if (m.userData.glow) m.emissiveIntensity = night ? 0.9 : 0;
    }
  }
}
