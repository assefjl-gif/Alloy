/**
 * Controlador imperativo da cena 3D (Etapa 3). Isolado do React: recebe estado pronto
 * e desenha. Princípios:
 *  - renderização SOB DEMANDA (sem loop contínuo); pausa com a aba oculta (3.2);
 *  - InstancedMesh por classe de esfera; geometria de esfera compartilhada (3.3);
 *  - atualizações incrementais: exibição muda escala/visibilidade, overlays fazem diff por id;
 *  - tudo é liberado (dispose) ao desmontar.
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import type { StructureResult, Vec3 } from '../../services/api/contracts.ts';
import type { AtomRef, OverlayItem } from '../../stores/overlays.ts';
import type { CameraState, DisplaySettings } from '../../stores/viewer.ts';
import { bounds, buildAtoms, buildEdges, contactBonds, isLatticePoint, stackingLayers, type DisplayAtom } from './geometry.ts';

export interface ThemeTokens {
  edge: string;
  labelStroke: string;
  selection: string;
  site: Record<string, string>;
  axis: { x: string; y: string; z: string; a3: string };
  replicaOpacity: number;
  ink: string;
}

export function readTokens(): ThemeTokens {
  const cs = getComputedStyle(document.documentElement);
  const v = (name: string, fallback: string) => cs.getPropertyValue(name).trim() || fallback;
  return {
    edge: v('--viewer-edge', '#29313f'),
    labelStroke: v('--viewer-label-stroke', 'rgba(255,255,255,.92)'),
    selection: v('--viewer-selection', '#10131a'),
    site: { vertice: v('--site-vertice', '#1aa7d9'), centro: v('--site-centro', '#d79319'), face: v('--site-face', '#19a56b'), basal: v('--site-basal', '#19a56b'), interior: v('--site-interior', '#7256d9') },
    axis: { x: v('--axis-x', '#ce3f4f'), y: v('--axis-y', '#19a56b'), z: v('--axis-z', '#1aa7d9'), a3: v('--axis-a3', '#d79319') },
    replicaOpacity: Number(v('--viewer-replica-opacity', '0.55')) || 0.55,
    ink: v('--color-ink', '#10131a'),
  };
}

export interface ElementColoring {
  /** elemento atribuído a cada átomo exibido (mesma ordem de `atoms`) */
  elements: string[];
  colors: Record<string, string>;
  shapes: Record<string, ShapeName>;
}

export type ShapeName = 'sphere' | 'cube' | 'octahedron' | 'tetrahedron' | 'icosahedron' | 'dodecahedron' | 'cylinder';
export const SHAPE_ORDER: ShapeName[] = ['sphere', 'cube', 'octahedron', 'tetrahedron', 'icosahedron', 'dodecahedron', 'cylinder'];

export interface AnimationFrame {
  kind: 'stacking' | 'alpha-gamma' | 'thermal';
  sequence?: string[];
  visibleLayers?: number;
  /** 0..1 entre o estado inicial e o final */
  mix?: number;
  from?: StructureResult | null;
  to?: StructureResult | null;
  scale?: number;
  layerColors?: Record<string, string>;
}

interface Batch {
  mesh: THREE.InstancedMesh;
  /** cor base do lote (o material fica branco e a cor vai por instância, para permitir destaque) */
  color: THREE.Color;
  atoms: DisplayAtom[];
  /** índice de cada átomo do lote em `this.atoms` */
  globalIndex: number[];
}

interface OverlayEntry {
  group: THREE.Group;
  signature: string;
}

export interface ControllerCallbacks {
  onCamera?: (cam: CameraState) => void;
  onPick?: (ref: AtomRef | null) => void;
}

const MODE_SCALE: Record<DisplaySettings['atoms'], number> = { reduced: 0.32, rigid: 1, ballstick: 0.22, points: 0.09 };

function disposeObject(obj: THREE.Object3D, shared: Set<THREE.BufferGeometry>): void {
  obj.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (mesh.geometry && !shared.has(mesh.geometry)) mesh.geometry.dispose();
    const mat = (mesh as unknown as { material?: THREE.Material | THREE.Material[] }).material;
    if (mat) {
      for (const m of Array.isArray(mat) ? mat : [mat]) {
        const map = (m as THREE.SpriteMaterial).map;
        if (map) map.dispose();
        m.dispose();
      }
    }
  });
}

function clearGroup(group: THREE.Group, shared: Set<THREE.BufferGeometry>): void {
  while (group.children.length) {
    const child = group.children[0] as THREE.Object3D;
    group.remove(child);
    disposeObject(child, shared);
  }
}

export class SceneController {
  readonly renderer: THREE.WebGLRenderer;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(36, 1, 0.01, 200);
  private readonly controls: OrbitControls;
  private readonly crystal = new THREE.Group();
  private readonly frame = new THREE.Group();
  private readonly atomsGroup = new THREE.Group();
  private readonly edgesGroup = new THREE.Group();
  private readonly bondsGroup = new THREE.Group();
  private readonly latticeGroup = new THREE.Group();
  private readonly overlaysGroup = new THREE.Group();
  private readonly axesGroup = new THREE.Group();
  private readonly markersGroup = new THREE.Group();
  private readonly animGroup = new THREE.Group();
  private readonly raycaster = new THREE.Raycaster();
  private readonly shared = new Set<THREE.BufferGeometry>();
  private readonly geometries: Record<ShapeName, THREE.BufferGeometry>;
  /** esfera de menor resolução para cenas grandes (nível de detalhe por quantidade de instâncias) */
  private readonly sphereLow = new THREE.SphereGeometry(1, 16, 12);
  private tokens: ThemeTokens;
  private structure: StructureResult | null = null;
  private supercell: [number, number, number] = [1, 1, 1];
  private display: DisplaySettings | null = null;
  private atoms: DisplayAtom[] = [];
  private batches: Batch[] = [];
  private overlays = new Map<string, OverlayEntry>();
  private overlayItems: OverlayItem[] = [];
  private selectedOverlay: string | null = null;
  private selection: AtomRef | null = null;
  private picks: AtomRef[] = [];
  private coloring: ElementColoring | null = null;
  private clipPlanes: THREE.Plane[] = [];
  private edgeMaterial: THREE.LineBasicMaterial | null = null;
  private rafId = 0;
  private continuous = 0;
  private disposed = false;
  private resizeObserver: ResizeObserver | null = null;
  private cameraTimer = 0;
  private boundRadius = 1;
  private autoRotate = false;
  private animating = false;
  private touchLocked = false;
  private readonly callbacks: ControllerCallbacks;
  /** Telemetria para testes/medição (3.18). */
  /**
   * Métricas de desempenho (Etapa 8): lastPickMs = raycast + atualização do estado (síncrono);
   * lastSelectWorkMs = lastPickMs + tempo do quadro que desenha o destaque (trabalho da CPU, sem a espera do vsync);
   * lastSelectToFrameMs = do clique ao fim desse quadro (inclui a espera pelo próximo quadro).
   */
  readonly stats = { renders: 0, lastPickMs: 0, lastRenderMs: 0, instances: 0, lastSelectWorkMs: 0, lastSelectToFrameMs: 0 };
  private pendingPick: { t0: number; work: number } | null = null;

  constructor(private readonly container: HTMLElement, callbacks: ControllerCallbacks = {}) {
    this.callbacks = callbacks;
    this.tokens = readTokens();
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.localClippingEnabled = true;
    this.renderer.domElement.className = 'viewer-canvas';
    this.renderer.domElement.setAttribute('aria-hidden', 'true');
    container.appendChild(this.renderer.domElement);

    this.scene.add(new THREE.AmbientLight(0xffffff, 1.35));
    const key = new THREE.DirectionalLight(0xffffff, 2.1);
    key.position.set(4, 6, 5);
    const fill = new THREE.DirectionalLight(0xffffff, 0.75);
    fill.position.set(-5, -2, -4);
    this.scene.add(key, fill);

    this.crystal.rotation.x = -Math.PI / 2; // eixo c/z do motor para cima (como no legado)
    this.frame.add(this.edgesGroup, this.bondsGroup, this.latticeGroup, this.atomsGroup, this.overlaysGroup, this.axesGroup, this.markersGroup);
    this.crystal.add(this.frame, this.animGroup);
    this.scene.add(this.crystal);

    this.geometries = {
      sphere: new THREE.SphereGeometry(1, 32, 20),
      cube: new THREE.BoxGeometry(1.5, 1.5, 1.5),
      octahedron: new THREE.OctahedronGeometry(1.25),
      tetrahedron: new THREE.TetrahedronGeometry(1.35),
      icosahedron: new THREE.IcosahedronGeometry(1.1),
      dodecahedron: new THREE.DodecahedronGeometry(1.15),
      cylinder: new THREE.CylinderGeometry(0.95, 0.95, 1.6, 20),
    };
    Object.values(this.geometries).forEach((g) => this.shared.add(g));
    this.shared.add(this.sphereLow);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.enablePan = false;
    this.controls.autoRotateSpeed = 1.6;
    this.controls.addEventListener('change', this.onControlsChange);
    this.setTouchLocked(false);

    this.renderer.domElement.addEventListener('pointerdown', this.onPointerDown);
    this.renderer.domElement.addEventListener('pointerup', this.onPointerUp);
    document.addEventListener('visibilitychange', this.onVisibility);
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.resize();
  }

  // ------------------------------------------------------------------ render
  requestRender(): void {
    if (this.disposed || this.rafId || document.hidden) return;
    this.rafId = requestAnimationFrame(this.tick);
  }

  private readonly tick = (): void => {
    this.rafId = 0;
    if (this.disposed) return;
    const t0 = performance.now();
    const moving = this.controls.update();
    this.renderer.render(this.scene, this.camera);
    this.stats.renders += 1;
    this.stats.lastRenderMs = performance.now() - t0;
    if (this.pendingPick) {
      this.stats.lastSelectWorkMs = this.pendingPick.work + this.stats.lastRenderMs;
      this.stats.lastSelectToFrameMs = performance.now() - this.pendingPick.t0;
      this.pendingPick = null;
    }
    if (moving || this.autoRotate || this.continuous > 0 || this.animating) this.requestRender();
  };

  private readonly onVisibility = (): void => {
    if (document.hidden) {
      if (this.rafId) cancelAnimationFrame(this.rafId);
      this.rafId = 0;
    } else this.requestRender();
  };

  private readonly onControlsChange = (): void => {
    this.requestRender();
    window.clearTimeout(this.cameraTimer);
    this.cameraTimer = window.setTimeout(() => this.callbacks.onCamera?.(this.getCamera()), 250);
  };

  resize(): void {
    const w = this.container.clientWidth || 600;
    const h = this.container.clientHeight || 420;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.requestRender();
  }

  // ------------------------------------------------------------------ estrutura
  setStructure(result: StructureResult, supercell: [number, number, number], display: DisplaySettings, keepCamera: boolean): void {
    const changed = result !== this.structure || supercell.join() !== this.supercell.join();
    this.structure = result;
    this.supercell = supercell;
    this.display = display;
    if (!changed) return;
    this.atoms = buildAtoms(result, supercell);
    this.coloring = null;
    this.rebuildAtoms();
    this.rebuildEdges();
    this.rebuildBonds();
    this.rebuildLattice();
    this.rebuildAxes();
    const b = bounds(this.atoms.map((a) => a.pos));
    this.frame.position.set(-b.center[0], -b.center[1], -b.center[2]);
    this.boundRadius = b.radius;
    this.frame.updateMatrixWorld(true);
    this.rebuildOverlays(true);
    this.updateMarkers();
    if (!keepCamera) this.resetView();
    this.requestRender();
  }

  getAtoms(): DisplayAtom[] {
    return this.atoms;
  }

  private atomColor(a: DisplayAtom, i: number): string {
    if (this.coloring) return this.coloring.colors[this.coloring.elements[i] ?? ''] ?? this.tokens.ink;
    return this.tokens.site[a.tipo] ?? '#1aa7d9';
  }

  private rebuildAtoms(): void {
    clearGroup(this.atomsGroup, this.shared);
    this.batches = [];
    const groups = new Map<string, { atoms: DisplayAtom[]; idx: number[]; shape: ShapeName; color: string; replica: boolean }>();
    this.atoms.forEach((a, i) => {
      const cls = this.coloring ? `el:${this.coloring.elements[i]}` : `site:${a.tipo}`;
      const key = `${cls}|${a.replica ? 'r' : 'o'}`;
      let g = groups.get(key);
      if (!g) {
        const shape: ShapeName = this.coloring ? (this.coloring.shapes[this.coloring.elements[i] ?? ''] ?? 'sphere') : 'sphere';
        g = { atoms: [], idx: [], shape, color: this.atomColor(a, i), replica: a.replica };
        groups.set(key, g);
      }
      g.atoms.push(a);
      g.idx.push(i);
    });
    for (const g of groups.values()) {
      const material = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.34,
        metalness: 0.18,
        transparent: g.replica,
        opacity: g.replica ? this.tokens.replicaOpacity : 1,
        clippingPlanes: this.clipPlanes,
      });
      const geometry = g.shape === 'sphere' && this.atoms.length > 60 ? this.sphereLow : this.geometries[g.shape];
      const mesh = new THREE.InstancedMesh(geometry, material, g.atoms.length);
      mesh.userData.batch = this.batches.length;
      this.atomsGroup.add(mesh);
      this.batches.push({ mesh, color: new THREE.Color(g.color), atoms: g.atoms, globalIndex: g.idx });
    }
    this.stats.instances = this.atoms.length;
    this.updateAtomScale();
    this.updateHighlights();
  }

  private updateAtomScale(): void {
    if (!this.structure || !this.display) return;
    const radius = this.structure.raio_relativo * MODE_SCALE[this.display.atoms];
    const m = new THREE.Matrix4();
    const s = new THREE.Vector3(radius, radius, radius);
    const q = new THREE.Quaternion();
    for (const b of this.batches) {
      b.atoms.forEach((a, i) => {
        m.compose(new THREE.Vector3(...a.pos), q, s);
        b.mesh.setMatrixAt(i, m);
      });
      b.mesh.instanceMatrix.needsUpdate = true;
      b.mesh.computeBoundingSphere();
    }
    this.bondsGroup.visible = this.display.atoms === 'ballstick';
    this.updateMarkers();
  }

  private rebuildEdges(): void {
    clearGroup(this.edgesGroup, this.shared);
    if (!this.structure) return;
    const segs = buildEdges(this.structure, this.supercell);
    const positions = new Float32Array(segs.length * 6);
    segs.forEach(([p, q], i) => positions.set([...p, ...q], i * 6));
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this.edgeMaterial = new THREE.LineBasicMaterial({ color: new THREE.Color(this.tokens.edge), clippingPlanes: this.clipPlanes });
    this.edgesGroup.add(new THREE.LineSegments(geom, this.edgeMaterial));
    this.edgesGroup.visible = this.display?.edges ?? true;
  }

  private rebuildBonds(): void {
    clearGroup(this.bondsGroup, this.shared);
    if (!this.structure) return;
    const pairs = this.atoms.length <= 900 ? contactBonds(this.atoms, this.structure.raio_relativo) : [];
    if (!pairs.length) return;
    const geom = new THREE.CylinderGeometry(1, 1, 1, 10);
    const material = new THREE.MeshStandardMaterial({ color: new THREE.Color(this.tokens.edge), roughness: 0.6, clippingPlanes: this.clipPlanes });
    const mesh = new THREE.InstancedMesh(geom, material, pairs.length);
    const up = new THREE.Vector3(0, 1, 0);
    const m = new THREE.Matrix4();
    const radius = this.structure.raio_relativo * 0.07;
    pairs.forEach(([i, j], k) => {
      const a = new THREE.Vector3(...(this.atoms[i] as DisplayAtom).pos);
      const b = new THREE.Vector3(...(this.atoms[j] as DisplayAtom).pos);
      const dir = b.clone().sub(a);
      const len = dir.length();
      const q = new THREE.Quaternion().setFromUnitVectors(up, dir.normalize());
      m.compose(a.clone().add(b).multiplyScalar(0.5), q, new THREE.Vector3(radius, len, radius));
      mesh.setMatrixAt(k, m);
    });
    mesh.instanceMatrix.needsUpdate = true;
    this.bondsGroup.add(mesh);
    this.bondsGroup.visible = this.display?.atoms === 'ballstick';
  }

  private rebuildLattice(): void {
    clearGroup(this.latticeGroup, this.shared);
    if (!this.structure) return;
    const pts = this.atoms.filter((a) => isLatticePoint(this.structure!.estrutura, a.tipo));
    const material = new THREE.MeshBasicMaterial({ color: new THREE.Color(this.tokens.ink) });
    const mesh = new THREE.InstancedMesh(this.geometries.octahedron, material, pts.length);
    const m = new THREE.Matrix4();
    const s = 0.035;
    pts.forEach((a, i) => { m.compose(new THREE.Vector3(...a.pos), new THREE.Quaternion(), new THREE.Vector3(s, s, s)); mesh.setMatrixAt(i, m); });
    mesh.instanceMatrix.needsUpdate = true;
    this.latticeGroup.add(mesh);
    this.latticeGroup.visible = this.display?.latticePoints ?? false;
  }

  private rebuildAxes(): void {
    clearGroup(this.axesGroup, this.shared);
    if (!this.structure) return;
    const t = this.tokens.axis;
    const hc = this.structure.estrutura === 'HC';
    const vectors: Array<[Vec3, string, string]> = hc
      ? [[[1.3, 0, 0], 'a₁', t.x], [[-0.65, 1.126, 0], 'a₂', t.y], [[-0.65, -1.126, 0], 'a₃', t.a3], [[0, 0, (this.structure.c_a ?? 1.633) * 1.28], 'c', t.z]]
      : [[[1.32, 0, 0], 'x', t.x], [[0, 1.32, 0], 'y', t.y], [[0, 0, 1.32], 'z', t.z]];
    for (const [tip, label, color] of vectors) {
      this.axesGroup.add(this.arrow([0, 0, 0], tip, color, 0.007));
      const sprite = this.label(label, color, 0.11);
      sprite.position.set(tip[0] * 1.08, tip[1] * 1.08, tip[2] * 1.06);
      this.axesGroup.add(sprite);
    }
    const origin = this.label('O', this.tokens.ink, 0.09);
    origin.position.set(-0.07, -0.07, -0.07);
    this.axesGroup.add(origin);
    this.axesGroup.visible = this.display?.axes ?? true;
  }

  // ------------------------------------------------------------------ exibição
  setDisplay(display: DisplaySettings): void {
    const prev = this.display;
    this.display = display;
    if (!prev || prev.atoms !== display.atoms) this.updateAtomScale();
    this.edgesGroup.visible = display.edges;
    this.axesGroup.visible = display.axes;
    this.latticeGroup.visible = display.latticePoints;
    this.setAutoRotate(display.autoRotate);
    if (prev && prev.labels !== display.labels) this.rebuildOverlays(true);
    this.requestRender();
  }

  setAutoRotate(on: boolean): void {
    this.autoRotate = on;
    this.controls.autoRotate = on;
    if (on) this.requestRender();
  }

  setElementColoring(coloring: ElementColoring | null): void {
    this.coloring = coloring;
    this.rebuildAtoms();
    this.requestRender();
  }

  setTheme(): void {
    this.tokens = readTokens();
    if (this.edgeMaterial) this.edgeMaterial.color.set(this.tokens.edge);
    this.rebuildAtoms();
    this.rebuildLattice();
    this.rebuildAxes();
    this.rebuildOverlays(true);
    this.updateMarkers();
    this.requestRender();
  }

  // ------------------------------------------------------------------ overlays
  setOverlays(items: OverlayItem[], selectedId: string | null): void {
    this.overlayItems = items;
    this.selectedOverlay = selectedId;
    this.rebuildOverlays(false);
  }

  private signature(it: OverlayItem): string {
    const extra = it.kind === 'plane' ? it.clip : it.kind === 'measurement' ? it.data.points.flat().join(',') : '';
    return `${it.visible}|${it.color}|${it.label}|${extra}|${it.id === this.selectedOverlay}|${this.display?.labels}`;
  }

  private rebuildOverlays(force: boolean): void {
    const ids = new Set(this.overlayItems.map((i) => i.id));
    for (const [id, entry] of this.overlays) {
      if (!ids.has(id) || force) {
        this.overlaysGroup.remove(entry.group);
        disposeObject(entry.group, this.shared);
        this.overlays.delete(id);
      }
    }
    for (const it of this.overlayItems) {
      const sig = this.signature(it);
      const existing = this.overlays.get(it.id);
      if (existing && existing.signature === sig) continue;
      if (existing) { this.overlaysGroup.remove(existing.group); disposeObject(existing.group, this.shared); }
      const group = this.buildOverlay(it);
      group.visible = it.visible;
      this.overlaysGroup.add(group);
      this.overlays.set(it.id, { group, signature: sig });
    }
    this.updateClipping();
    this.updateHighlights();
    this.requestRender();
  }

  private buildOverlay(it: OverlayItem): THREE.Group {
    const group = new THREE.Group();
    const selected = it.id === this.selectedOverlay;
    const showLabel = this.display?.labels ?? true;
    if (it.kind === 'plane') {
      const pts = it.data.poligono;
      const c = it.data.centro;
      const tri: number[] = [];
      for (let i = 0; i < pts.length; i += 1) tri.push(...c, ...(pts[i] as Vec3), ...(pts[(i + 1) % pts.length] as Vec3));
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(tri, 3));
      const fill = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: new THREE.Color(it.color), transparent: true, opacity: selected ? 0.5 : 0.3, side: THREE.DoubleSide, depthWrite: false }));
      fill.renderOrder = 2;
      const og = new THREE.BufferGeometry();
      og.setAttribute('position', new THREE.Float32BufferAttribute(pts.flat(), 3));
      // Plano: contorno TRACEJADO (direção usa seta cheia) — diferença não depende só de cor (3.12/7.4).
      const outline = new THREE.LineLoop(og, new THREE.LineDashedMaterial({ color: new THREE.Color(it.color), dashSize: 0.06, gapSize: 0.035 }));
      outline.computeLineDistances();
      group.add(fill, outline);
      if (showLabel) {
        const label = this.label(it.data.notacao, it.color, 0.12);
        const n = it.data.normal;
        label.position.set(c[0] + n[0] * 0.06, c[1] + n[1] * 0.06, c[2] + n[2] * 0.06);
        group.add(label);
      }
    } else if (it.kind === 'direction') {
      group.add(this.arrow(it.data.inicio, it.data.fim, it.color, selected ? 0.022 : 0.016));
      if (showLabel) {
        const label = this.label(it.data.notacao, it.color, 0.12);
        const s = it.data.inicio;
        const e = it.data.fim;
        label.position.set(s[0] + (e[0] - s[0]) * 0.6, s[1] + (e[1] - s[1]) * 0.6, s[2] + (e[2] - s[2]) * 0.6 + 0.08);
        group.add(label);
      }
    } else if (it.kind === 'measurement') {
      const pts = it.data.points;
      const g = new THREE.BufferGeometry().setFromPoints(pts.map((p) => new THREE.Vector3(...p)));
      const line = new THREE.Line(g, new THREE.LineDashedMaterial({ color: new THREE.Color(it.color), dashSize: 0.03, gapSize: 0.02, depthTest: false }));
      line.computeLineDistances();
      line.renderOrder = 5;
      group.add(line);
      const anchor = it.data.type === 'angle' ? (pts[1] as Vec3) : ([(pts[0]![0] + pts[1]![0]) / 2, (pts[0]![1] + pts[1]![1]) / 2, (pts[0]![2] + pts[1]![2]) / 2] as Vec3);
      const label = this.label(it.label, it.color, 0.1);
      label.position.set(anchor[0], anchor[1], anchor[2] + 0.07);
      group.add(label);
    } else if (it.kind === 'annotation') {
      const label = this.label(it.text, it.color, 0.1);
      label.position.set(...it.anchor);
      group.add(label);
    }
    return group;
  }

  private updateClipping(): void {
    const planes: THREE.Plane[] = [];
    for (const it of this.overlayItems) {
      if (it.kind !== 'plane' || !it.clip || !it.visible) continue;
      const n = new THREE.Vector3(...it.data.normal).negate();
      const p = new THREE.Vector3(...it.data.centro);
      const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(n, p);
      plane.applyMatrix4(this.frame.matrixWorld);
      planes.push(plane);
    }
    const changed = planes.length !== this.clipPlanes.length;
    this.clipPlanes.length = 0;
    this.clipPlanes.push(...planes);
    if (changed) {
      for (const b of this.batches) (b.mesh.material as THREE.Material).needsUpdate = true;
      if (this.edgeMaterial) this.edgeMaterial.needsUpdate = true;
      this.bondsGroup.traverse((o) => { const m = (o as THREE.Mesh).material as THREE.Material | undefined; if (m) m.needsUpdate = true; });
    }
  }

  /** Átomos contidos no plano/direção selecionado (índices da célula do motor) recebem brilho. */
  private updateHighlights(): void {
    const sel = this.overlayItems.find((o) => o.id === this.selectedOverlay && o.visible);
    const highlight = new Set<number>(sel && (sel.kind === 'plane' || sel.kind === 'direction') ? sel.data.atomos : []);
    const glow = sel ? new THREE.Color(sel.color).lerp(new THREE.Color(0xffffff), 0.15) : null;
    for (const b of this.batches) {
      b.atoms.forEach((a, i) => {
        const on = glow && !a.replica && a.ref.cell.join() === '0,0,0' && highlight.has(a.ref.index);
        b.mesh.setColorAt(i, on ? glow : b.color);
      });
      if (b.mesh.instanceColor) b.mesh.instanceColor.needsUpdate = true;
    }
  }

  // ------------------------------------------------------------------ seleção e marcadores
  setSelection(ref: AtomRef | null, picks: AtomRef[]): void {
    this.selection = ref;
    this.picks = picks;
    this.updateMarkers();
    this.requestRender();
  }

  private findAtom(ref: AtomRef): DisplayAtom | undefined {
    const key = `${ref.index}@${ref.cell.join(',')}`;
    return this.atoms.find((a) => a.key === key);
  }

  private updateMarkers(): void {
    clearGroup(this.markersGroup, this.shared);
    if (!this.structure || !this.display) return;
    const radius = this.structure.raio_relativo * MODE_SCALE[this.display.atoms];
    const add = (ref: AtomRef, color: string, scale: number, opacity: number) => {
      const a = this.findAtom(ref);
      if (!a) return;
      const mesh = new THREE.Mesh(this.geometries.sphere, new THREE.MeshBasicMaterial({ color: new THREE.Color(color), transparent: true, opacity, depthWrite: false, wireframe: true }));
      mesh.position.set(...a.pos);
      mesh.scale.setScalar(Math.max(radius * scale, 0.05));
      this.markersGroup.add(mesh);
    };
    if (this.selection) add(this.selection, this.tokens.selection, 1.35, 0.55);
    this.picks.forEach((p) => add(p, '#D55E00', 1.5, 0.8));
  }

  // ------------------------------------------------------------------ câmera
  resetView(): void {
    const distance = Math.max(2.4, this.boundRadius * 3.3);
    const dir = new THREE.Vector3(1, 0.62, -0.48).normalize();
    this.camera.position.copy(dir.multiplyScalar(distance));
    this.controls.target.set(0, 0, 0);
    this.controls.minDistance = distance * 0.3;
    this.controls.maxDistance = distance * 3.5;
    this.camera.lookAt(0, 0, 0);
    this.controls.update();
    this.requestRender();
  }

  getCamera(): CameraState {
    const p = this.camera.position;
    const t = this.controls.target;
    return { position: [p.x, p.y, p.z], target: [t.x, t.y, t.z] };
  }

  setCamera(cam: CameraState | null): void {
    if (!cam) { this.resetView(); return; }
    this.camera.position.set(...cam.position);
    this.controls.target.set(...cam.target);
    this.camera.lookAt(this.controls.target);
    this.controls.update();
    this.requestRender();
  }

  /** Teclado (3.4): setas giram em torno do alvo, +/− aproximam. */
  orbit(dAzimuth: number, dPolar: number): void {
    const offset = this.camera.position.clone().sub(this.controls.target);
    const sph = new THREE.Spherical().setFromVector3(offset);
    sph.theta += dAzimuth;
    sph.phi = Math.min(Math.PI - 0.05, Math.max(0.05, sph.phi + dPolar));
    offset.setFromSpherical(sph);
    this.camera.position.copy(this.controls.target).add(offset);
    this.camera.lookAt(this.controls.target);
    this.onControlsChange();
  }

  zoom(factor: number): void {
    const offset = this.camera.position.clone().sub(this.controls.target).multiplyScalar(factor);
    const len = Math.min(this.controls.maxDistance, Math.max(this.controls.minDistance, offset.length()));
    offset.setLength(len);
    this.camera.position.copy(this.controls.target).add(offset);
    this.onControlsChange();
  }

  /** Toque (7.9): travada → um dedo rola a página; dois dedos giram/aproximam. Destravada → um dedo gira. */
  setTouchLocked(locked: boolean): void {
    this.touchLocked = locked;
    this.controls.touches = locked ? { ONE: -1 as unknown as THREE.TOUCH, TWO: THREE.TOUCH.DOLLY_ROTATE } : { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
    this.renderer.domElement.style.touchAction = locked ? 'pan-y' : 'none';
  }

  get touchMode(): 'locked' | 'unlocked' {
    return this.touchLocked ? 'locked' : 'unlocked';
  }

  // ------------------------------------------------------------------ seleção por raycasting (3.7)
  private downAt: { x: number; y: number } | null = null;
  private readonly onPointerDown = (e: PointerEvent): void => { this.downAt = { x: e.clientX, y: e.clientY }; };
  private readonly onPointerUp = (e: PointerEvent): void => {
    if (!this.downAt) return;
    const moved = Math.hypot(e.clientX - this.downAt.x, e.clientY - this.downAt.y);
    this.downAt = null;
    if (moved > 5) return; // foi arraste de câmera, não clique
    const t0 = performance.now();
    const ref = this.pickAt(e.clientX, e.clientY);
    this.callbacks.onPick?.(ref);
    this.stats.lastPickMs = performance.now() - t0;
    this.pendingPick = { t0, work: this.stats.lastPickMs };
    this.requestRender();
  };

  pickAt(clientX: number, clientY: number): AtomRef | null {
    if (this.animGroup.visible && this.animGroup.children.length) return null;
    const rect = this.renderer.domElement.getBoundingClientRect();
    const ndc = new THREE.Vector2(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
    this.raycaster.setFromCamera(ndc, this.camera);
    const hits = this.raycaster.intersectObjects(this.batches.map((b) => b.mesh), false);
    const hit = hits.find((h) => h.instanceId !== undefined && this.isUnclipped(h.point));
    if (!hit || hit.instanceId === undefined) return null;
    const batch = this.batches[(hit.object as THREE.InstancedMesh).userData.batch as number];
    const atom = batch?.atoms[hit.instanceId];
    return atom ? { index: atom.ref.index, cell: [...atom.ref.cell] as [number, number, number] } : null;
  }

  private isUnclipped(p: THREE.Vector3): boolean {
    return this.clipPlanes.every((pl) => pl.distanceToPoint(p) >= 0);
  }

  /** Posição na tela de um átomo (para testes automatizados e anúncios). */
  screenPosition(ref: AtomRef): { x: number; y: number } | null {
    const a = this.findAtom(ref);
    if (!a) return null;
    this.crystal.updateMatrixWorld(true);
    const v = new THREE.Vector3(...a.pos).applyMatrix4(this.frame.matrixWorld).project(this.camera);
    const rect = this.renderer.domElement.getBoundingClientRect();
    return { x: rect.left + ((v.x + 1) / 2) * rect.width, y: rect.top + ((1 - v.y) / 2) * rect.height };
  }

  // ------------------------------------------------------------------ animações didáticas (3.14–3.16)
  setAnimationFrame(frame: AnimationFrame | null): void {
    clearGroup(this.animGroup, this.shared);
    this.animating = false;
    const active = Boolean(frame);
    this.frame.visible = !active || frame?.kind === 'thermal';
    this.animGroup.visible = active;
    if (!frame) { this.frame.scale.setScalar(1); this.requestRender(); return; }
    if (frame.kind === 'thermal') {
      this.frame.scale.setScalar(frame.scale ?? 1);
    } else if (frame.kind === 'stacking') {
      this.frame.scale.setScalar(1);
      const layers = stackingLayers(frame.sequence ?? ['A', 'B', 'C'], 3);
      const visible = layers.slice(0, Math.max(1, frame.visibleLayers ?? 1));
      const all = layers.flatMap((l) => l.points);
      const b = bounds(all);
      const offset = new THREE.Vector3(-b.center[0], -b.center[1], -b.center[2]);
      const scale = 1.2 / Math.max(1, b.radius) ;
      visible.forEach((layer, li) => {
        const color = frame.layerColors?.[layer.letter] ?? '#0072B2';
        const mesh = new THREE.InstancedMesh(this.geometries.sphere, new THREE.MeshStandardMaterial({ color: new THREE.Color(color), roughness: 0.4, transparent: li < visible.length - 1, opacity: li < visible.length - 1 ? 0.75 : 1 }), layer.points.length);
        const m = new THREE.Matrix4();
        layer.points.forEach((p, i) => { m.compose(new THREE.Vector3(...p).add(offset).multiplyScalar(scale), new THREE.Quaternion(), new THREE.Vector3(0.5 * scale, 0.5 * scale, 0.5 * scale)); mesh.setMatrixAt(i, m); });
        mesh.instanceMatrix.needsUpdate = true;
        this.animGroup.add(mesh);
        const label = this.label(`${layer.letter} (${li + 1})`, color, 0.13);
        const p0 = new THREE.Vector3(b.max[0] + 0.8, b.center[1], layer.points[0]?.[2] ?? 0).add(offset).multiplyScalar(scale);
        label.position.copy(p0);
        this.animGroup.add(label);
      });
    } else if (frame.kind === 'alpha-gamma' && frame.from && frame.to) {
      this.frame.scale.setScalar(1);
      const mix = frame.mix ?? 0;
      const draw = (r: StructureResult, opacity: number, color: string) => {
        if (opacity <= 0.01) return;
        const atoms = buildAtoms(r, [1, 1, 1]);
        const b = bounds(atoms.map((a) => a.pos));
        const scale = (r.a_nm ?? 1) / ((frame.from?.a_nm ?? 1) || 1);
        const mesh = new THREE.InstancedMesh(this.geometries.sphere, new THREE.MeshStandardMaterial({ color: new THREE.Color(color), transparent: true, opacity, roughness: 0.35 }), atoms.length);
        const m = new THREE.Matrix4();
        atoms.forEach((a, i) => {
          const p = new THREE.Vector3(...a.pos).sub(new THREE.Vector3(...b.center)).multiplyScalar(scale);
          const s = r.raio_relativo * 0.32 * scale;
          m.compose(p, new THREE.Quaternion(), new THREE.Vector3(s, s, s));
          mesh.setMatrixAt(i, m);
        });
        mesh.instanceMatrix.needsUpdate = true;
        this.animGroup.add(mesh);
        const segs = buildEdges(r, [1, 1, 1]);
        const pos = new Float32Array(segs.length * 6);
        segs.forEach(([p, q], i) => pos.set([...p, ...q].map((v, k) => (v - (b.center[k % 3] as number)) * scale), i * 6));
        const g = new THREE.BufferGeometry();
        g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
        this.animGroup.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: new THREE.Color(color), transparent: true, opacity })));
      };
      draw(frame.from, 1 - mix, this.tokens.site.centro ?? '#d79319');
      draw(frame.to, mix, this.tokens.site.face ?? '#19a56b');
    }
    this.requestRender();
  }

  // ------------------------------------------------------------------ utilidades gráficas
  private label(text: string, color: string, size: number): THREE.Sprite {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const font = '700 64px "Segoe UI", system-ui, Arial';
    if (ctx) ctx.font = font;
    const width = Math.ceil((ctx?.measureText(text).width ?? 64) + 36);
    canvas.width = width;
    canvas.height = 96;
    if (ctx) {
      ctx.font = font;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.lineWidth = 10;
      ctx.strokeStyle = this.tokens.labelStroke;
      ctx.strokeText(text, width / 2, 50);
      ctx.fillStyle = color;
      ctx.fillText(text, width / 2, 50);
    }
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthTest: false, transparent: true }));
    sprite.scale.set(size * (width / 96), size, 1);
    sprite.renderOrder = 10;
    return sprite;
  }

  private arrow(start: Vec3, end: Vec3, color: string, radius: number): THREE.Group {
    const s = new THREE.Vector3(...start);
    const e = new THREE.Vector3(...end);
    const dir = e.clone().sub(s);
    const length = dir.length();
    dir.normalize();
    const head = Math.min(0.13, length * 0.3);
    const material = new THREE.MeshStandardMaterial({ color: new THREE.Color(color), roughness: 0.4, metalness: 0.1 });
    const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, Math.max(0.001, length - head), 14), material);
    shaft.position.copy(s).addScaledVector(dir, (length - head) / 2);
    shaft.quaternion.copy(q);
    const cone = new THREE.Mesh(new THREE.ConeGeometry(radius * 3, head, 18), material);
    cone.position.copy(s).addScaledVector(dir, length - head / 2);
    cone.quaternion.copy(q);
    const g = new THREE.Group();
    g.add(shaft, cone);
    return g;
  }

  // ------------------------------------------------------------------ exportação e medição
  capturePng(): string {
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
    return this.renderer.domElement.toDataURL('image/png');
  }

  /** Medição de FPS (3.18): força renderização contínua com rotação por `ms` milissegundos. */
  benchmark(ms: number): Promise<{ fps: number; frames: number; ms: number }> {
    return new Promise((resolve) => {
      this.continuous += 1;
      const prevRotate = this.autoRotate;
      this.setAutoRotate(true);
      this.controls.autoRotateSpeed = 6;
      const start = performance.now();
      const startRenders = this.stats.renders;
      this.requestRender();
      window.setTimeout(() => {
        const frames = this.stats.renders - startRenders;
        const elapsed = performance.now() - start;
        this.continuous -= 1;
        this.controls.autoRotateSpeed = 1.6;
        this.setAutoRotate(prevRotate);
        resolve({ fps: (frames * 1000) / elapsed, frames, ms: elapsed });
      }, ms);
    });
  }

  dispose(): void {
    this.disposed = true;
    if (this.rafId) cancelAnimationFrame(this.rafId);
    window.clearTimeout(this.cameraTimer);
    document.removeEventListener('visibilitychange', this.onVisibility);
    this.renderer.domElement.removeEventListener('pointerdown', this.onPointerDown);
    this.renderer.domElement.removeEventListener('pointerup', this.onPointerUp);
    this.resizeObserver?.disconnect();
    this.controls.removeEventListener('change', this.onControlsChange);
    this.controls.dispose();
    for (const g of [this.atomsGroup, this.edgesGroup, this.bondsGroup, this.latticeGroup, this.overlaysGroup, this.axesGroup, this.markersGroup, this.animGroup]) clearGroup(g, this.shared);
    Object.values(this.geometries).forEach((g) => g.dispose());
    this.renderer.dispose();
    this.renderer.forceContextLoss();
    this.renderer.domElement.remove();
  }
}
