// Visualizador 3D (Three.js r128, global window.THREE carregado localmente).
// v1.1: renderização sob demanda e pausa com a aba oculta (FE-03); DOM sem innerHTML (SE-02).
import { state, TYPE_COLORS, TYPE_LABELS } from "./estado.js";
import { logLine } from "./log.js";
import { $, h } from "./util.js";

function disposeGroup(group) {
  while (group.children.length) {
    const child = group.children[0];
    group.remove(child);
    child.traverse((object) => {
      if (object.geometry && object.geometry !== viewer.sphereGeometry) object.geometry.dispose();
      if (object.material) {
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach((material) => { if (material.map) material.map.dispose(); material.dispose(); });
      }
    });
  }
}

function makeLabel(text, color, size = 0.13) {
  const THREE = window.THREE;
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  const font = "700 64px Segoe UI, Arial";
  context.font = font;
  const width = Math.ceil(context.measureText(text).width) + 36;
  canvas.width = width; canvas.height = 96;
  context.font = font; context.textAlign = "center"; context.textBaseline = "middle";
  context.lineWidth = 10;
  context.strokeStyle = state.theme === "dark" ? "rgba(10,14,19,0.9)" : "rgba(255,255,255,0.92)";
  context.strokeText(text, width / 2, 50);
  context.fillStyle = color; context.fillText(text, width / 2, 50);
  const texture = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthTest: false, transparent: true }));
  sprite.scale.set(size * (width / 96), size, 1);
  sprite.renderOrder = 10;
  return sprite;
}

function makeArrow(start, end, color, radius) {
  const THREE = window.THREE;
  const s = new THREE.Vector3(...start);
  const e = new THREE.Vector3(...end);
  const direction = e.clone().sub(s);
  const length = direction.length();
  direction.normalize();
  const headLength = Math.min(0.13, length * 0.3);
  const material = new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.1 });
  const orientation = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, length - headLength, 14), material);
  shaft.position.copy(s).addScaledVector(direction, (length - headLength) / 2);
  shaft.quaternion.copy(orientation);
  const head = new THREE.Mesh(new THREE.ConeGeometry(radius * 3, headLength, 18), material);
  head.position.copy(s).addScaledVector(direction, length - headLength / 2);
  head.quaternion.copy(orientation);
  const group = new THREE.Group();
  group.add(shaft, head);
  return group;
}

export const viewer = {
  ready: false,
  dirty: true,
  atomMeshes: [],
  boundRadius: 1,

  requestRender() { this.dirty = true; },

  init() {
    const THREE = window.THREE;
    const viewerStage = $("viewerStage");
    const viewerLegend = $("viewerLegend");
    if (!THREE) {
      viewerStage.append(h("div", { class: "viewer-fallback" },
        "Não foi possível carregar o Three.js.", h("br"), "Os cálculos continuam disponíveis."));
      logLine("Three.js indisponível: visualização 3D desativada.", "terminal-error");
      return;
    }
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x000000, 0);
    viewerStage.insertBefore(renderer.domElement, viewerLegend);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(36, 1, 0.01, 100);
    scene.add(new THREE.AmbientLight(0xffffff, 0.55));
    const keyLight = new THREE.DirectionalLight(0xffffff, 0.85);
    keyLight.position.set(4, 6, 5);
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.35);
    fillLight.position.set(-5, -2, -4);
    scene.add(keyLight, fillLight);
    const pivot = new THREE.Group();
    const crystal = new THREE.Group();
    crystal.rotation.x = -Math.PI / 2;
    const frame = new THREE.Group();
    const atomsGroup = new THREE.Group();
    const edgesGroup = new THREE.Group();
    const overlaysGroup = new THREE.Group();
    const axesGroup = new THREE.Group();
    frame.add(edgesGroup, atomsGroup, overlaysGroup, axesGroup);
    crystal.add(frame);
    pivot.add(crystal);
    scene.add(pivot);
    Object.assign(this, { renderer, scene, camera, pivot, frame, atomsGroup, edgesGroup, overlaysGroup, axesGroup, viewerLegend });
    this.sphereGeometry = new THREE.SphereGeometry(1, 36, 24);
    if (THREE.OrbitControls) {
      this.controls = new THREE.OrbitControls(camera, renderer.domElement);
      this.controls.enableDamping = true; this.controls.dampingFactor = 0.08;
      this.controls.autoRotateSpeed = 1.6; this.controls.enablePan = false;
    } else {
      this.setupManualControls();
    }
    const resize = () => {
      const width = viewerStage.clientWidth || 600;
      const height = viewerStage.clientHeight || 420;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      this.requestRender();
    };
    if (window.ResizeObserver) new ResizeObserver(resize).observe(viewerStage);
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", () => { if (!document.hidden) this.requestRender(); });
    resize();
    const loop = () => {
      requestAnimationFrame(loop);
      if (document.hidden) return;
      let changed = false;
      if (this.controls) {
        this.controls.autoRotate = state.autoRotate;
        changed = this.controls.update();
      } else if (state.autoRotate) {
        this.pivot.rotation.y += 0.006;
        changed = true;
      }
      if (changed || this.dirty) {
        renderer.render(scene, camera);
        this.dirty = false;
      }
    };
    this.ready = true;
    loop();
  },

  setupManualControls() {
    const canvas = this.renderer.domElement;
    let dragging = false, lastX = 0, lastY = 0;
    canvas.addEventListener("pointerdown", (event) => { dragging = true; lastX = event.clientX; lastY = event.clientY; canvas.setPointerCapture(event.pointerId); });
    canvas.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      this.pivot.rotation.y += (event.clientX - lastX) * 0.01;
      this.pivot.rotation.x = Math.max(-1.4, Math.min(1.4, this.pivot.rotation.x + (event.clientY - lastY) * 0.01));
      lastX = event.clientX; lastY = event.clientY;
      this.requestRender();
    });
    canvas.addEventListener("pointerup", () => { dragging = false; });
    canvas.addEventListener("wheel", (event) => {
      event.preventDefault();
      const factor = event.deltaY > 0 ? 1.08 : 0.92;
      this.camera.position.multiplyScalar(factor);
      this.requestRender();
    }, { passive: false });
  },

  edgeColor() { return state.theme === "dark" ? 0xa9b6c6 : 0x29313f; },

  build(result) {
    if (!this.ready) return;
    const THREE = window.THREE;
    [this.atomsGroup, this.edgesGroup, this.overlaysGroup, this.axesGroup].forEach(disposeGroup);
    const min = [Infinity, Infinity, Infinity];
    const max = [-Infinity, -Infinity, -Infinity];
    const positions = [];
    result.arestas.forEach(([a, b]) => {
      positions.push(...a, ...b);
      [a, b].forEach((p) => p.forEach((v, i) => { min[i] = Math.min(min[i], v); max[i] = Math.max(max[i], v); }));
    });
    const center = min.map((v, i) => (v + max[i]) / 2);
    this.frame.position.set(-center[0], -center[1], -center[2]);
    this.boundRadius = Math.hypot(max[0] - min[0], max[1] - min[1], max[2] - min[2]) / 2;
    const edgeGeometry = new THREE.BufferGeometry();
    edgeGeometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    this.edgeMaterial = new THREE.LineBasicMaterial({ color: this.edgeColor() });
    this.edgesGroup.add(new THREE.LineSegments(edgeGeometry, this.edgeMaterial));
    this.atomMeshes = result.atomos.map((atom) => {
      const material = new THREE.MeshStandardMaterial({ color: TYPE_COLORS[atom.tipo] || "#1aa7d9", roughness: 0.32, metalness: 0.22, emissive: 0x000000 });
      const mesh = new THREE.Mesh(this.sphereGeometry, material);
      mesh.position.set(...atom.pos);
      this.atomsGroup.add(mesh);
      return mesh;
    });
    this.updateAtomScale();
    this.buildAxes(result);
    this.renderLegend(result);
    this.resetView();
  },

  updateAtomScale() {
    if (!this.ready || !state.current) return;
    const radius = state.current.raio_relativo * (state.rigid ? 1 : 0.32);
    this.atomMeshes.forEach((mesh) => mesh.scale.setScalar(radius));
    this.requestRender();
  },

  buildAxes(result) {
    disposeGroup(this.axesGroup);
    const vectors = result.estrutura === "HC"
      ? [[[1.3, 0, 0], "a₁", "#ce3f4f"], [[-0.65, 1.126, 0], "a₂", "#19a56b"], [[-0.65, -1.126, 0], "a₃", "#d79319"], [[0, 0, result.c_a * 1.28], "c", "#1aa7d9"]]
      : [[[1.32, 0, 0], "x", "#ce3f4f"], [[0, 1.32, 0], "y", "#19a56b"], [[0, 0, 1.32], "z", "#1aa7d9"]];
    vectors.forEach(([tip, label, color]) => {
      this.axesGroup.add(makeArrow([0, 0, 0], tip, color, 0.007));
      const sprite = makeLabel(label, color, 0.11);
      sprite.position.set(tip[0] * 1.08, tip[1] * 1.08, tip[2] * 1.06);
      this.axesGroup.add(sprite);
    });
    const origin = makeLabel("O", state.theme === "dark" ? "#c6d0dc" : "#29313f", 0.09);
    origin.position.set(-0.07, -0.07, -0.07);
    this.axesGroup.add(origin);
    this.axesGroup.visible = state.showAxes;
    this.requestRender();
  },

  setAxesVisible(value) {
    if (!this.ready) return;
    this.axesGroup.visible = value;
    this.requestRender();
  },

  renderLegend(result) {
    this.viewerLegend.replaceChildren(...result.contagem.map((group) => h("span", { class: "legend-chip" },
      h("i", { style: { background: TYPE_COLORS[group.tipo] || "#1aa7d9" } }),
      `${TYPE_LABELS[group.tipo] || group.tipo} (${group.fracao_txt})`)));
  },

  resetView() {
    if (!this.ready) return;
    const THREE = window.THREE;
    const distance = Math.max(2.4, this.boundRadius * 3.3);
    const direction = new THREE.Vector3(1, 0.62, -0.48).normalize();
    this.camera.position.copy(direction.multiplyScalar(distance));
    this.camera.lookAt(0, 0, 0);
    this.pivot.rotation.set(0, 0, 0);
    if (this.controls) {
      this.controls.target.set(0, 0, 0);
      this.controls.minDistance = distance * 0.35;
      this.controls.maxDistance = distance * 3;
      this.controls.update();
    }
    this.requestRender();
  },

  addOverlay(overlay) {
    if (!this.ready) return;
    const THREE = window.THREE;
    const group = new THREE.Group();
    if (overlay.tipo === "plano") {
      const points = overlay.poligono;
      const center = overlay.centro;
      const triangles = [];
      for (let i = 0; i < points.length; i++) triangles.push(...center, ...points[i], ...points[(i + 1) % points.length]);
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.Float32BufferAttribute(triangles, 3));
      const fill = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color: overlay.color, transparent: true, opacity: 0.32, side: THREE.DoubleSide, depthWrite: false }));
      fill.renderOrder = 2;
      const outlineGeometry = new THREE.BufferGeometry();
      outlineGeometry.setAttribute("position", new THREE.Float32BufferAttribute(points.flat(), 3));
      const outline = new THREE.LineLoop(outlineGeometry, new THREE.LineBasicMaterial({ color: overlay.color }));
      const label = makeLabel(overlay.notacao, overlay.color, 0.12);
      label.position.set(center[0] + overlay.normal[0] * 0.06, center[1] + overlay.normal[1] * 0.06, center[2] + overlay.normal[2] * 0.06);
      group.add(fill, outline, label);
    } else {
      group.add(makeArrow(overlay.inicio, overlay.fim, overlay.color, 0.016));
      const label = makeLabel(overlay.notacao, overlay.color, 0.12);
      label.position.set(
        overlay.inicio[0] + (overlay.fim[0] - overlay.inicio[0]) * 0.6,
        overlay.inicio[1] + (overlay.fim[1] - overlay.inicio[1]) * 0.6,
        overlay.inicio[2] + (overlay.fim[2] - overlay.inicio[2]) * 0.6 + 0.08);
      group.add(label);
    }
    this.overlaysGroup.add(group);
    this.highlightAtoms();
  },

  clearOverlays() {
    if (!this.ready) return;
    disposeGroup(this.overlaysGroup);
    this.highlightAtoms();
  },

  highlightAtoms() {
    const colorByAtom = new Map();
    state.overlays.forEach((overlay) => {
      overlay.atomos.forEach((index) => { if (!colorByAtom.has(index)) colorByAtom.set(index, overlay.color); });
    });
    this.atomMeshes.forEach((mesh, index) => {
      const color = colorByAtom.get(index);
      mesh.material.emissive.set(color || 0x000000);
      mesh.material.emissiveIntensity = color ? 0.45 : 0;
    });
    this.requestRender();
  },

  applyTheme() {
    if (!this.ready || !state.current) return;
    if (this.edgeMaterial) this.edgeMaterial.color.setHex(this.edgeColor());
    this.buildAxes(state.current);
    disposeGroup(this.overlaysGroup);
    state.overlays.forEach((overlay) => this.addOverlay(overlay));
    this.requestRender();
  },
};
