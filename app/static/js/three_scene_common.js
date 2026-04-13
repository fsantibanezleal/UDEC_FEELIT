import * as THREE from "../vendor/three/three.module.js";
import { OrbitControls } from "../vendor/three/OrbitControls.js";

export { THREE };

function buildBoundaryMesh(size) {
  const geometry = new THREE.EdgesGeometry(new THREE.BoxGeometry(size.x, size.y, size.z));
  const material = new THREE.LineBasicMaterial({ color: 0x58a6ff, transparent: true, opacity: 0.45 });
  return new THREE.LineSegments(geometry, material);
}

function buildPointerProxy(pointerColor) {
  const group = new THREE.Group();

  const tipMaterial = new THREE.MeshStandardMaterial({
    color: pointerColor,
    emissive: 0x664400,
    roughness: 0.24,
    metalness: 0.2,
  });
  const shaftMaterial = new THREE.MeshStandardMaterial({
    color: 0xc9d1d9,
    emissive: 0x09111c,
    roughness: 0.26,
    metalness: 0.82,
  });
  const gripMaterial = new THREE.MeshStandardMaterial({
    color: 0x1f2937,
    emissive: 0x09111c,
    roughness: 0.72,
    metalness: 0.12,
  });
  const ringMaterial = new THREE.MeshStandardMaterial({
    color: pointerColor,
    emissive: 0x664400,
    transparent: true,
    opacity: 0.7,
    roughness: 0.34,
    metalness: 0.06,
  });

  const tip = new THREE.Mesh(new THREE.SphereGeometry(0.055, 24, 18), tipMaterial);
  tip.userData.kind = "pointer-tip";
  group.add(tip);

  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.026, 0.034, 0.68, 24), shaftMaterial);
  shaft.rotation.z = Math.PI / 5;
  shaft.position.set(-0.16, 0.24, 0.14);
  shaft.userData.kind = "pointer-shaft";
  group.add(shaft);

  const grip = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.18, 18), gripMaterial);
  grip.rotation.z = Math.PI / 5;
  grip.position.set(-0.28, 0.41, 0.24);
  grip.userData.kind = "pointer-grip";
  group.add(grip);

  const collar = new THREE.Mesh(
    new THREE.TorusGeometry(0.092, 0.008, 12, 32),
    ringMaterial,
  );
  collar.rotation.x = Math.PI / 2;
  collar.position.y = 0.01;
  collar.userData.kind = "pointer-collar";
  group.add(collar);

  group.userData.pointerMaterials = {
    tipMaterial,
    shaftMaterial,
    gripMaterial,
    ringMaterial,
  };
  return group;
}

function isEditableTarget(target) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  return (
    target.isContentEditable
    || target.tagName === "INPUT"
    || target.tagName === "TEXTAREA"
    || target.tagName === "SELECT"
    || target.tagName === "OPTION"
  );
}

export function createWorkspaceScene(canvas, options = {}) {
  const background = options.background ?? 0x0d1117;
  const cameraPosition = options.cameraPosition ?? [3.6, 2.8, 4.6];
  const target = options.target ?? [0, 0.6, 0];
  const pointerColor = options.pointerColor ?? 0xf2cc60;
  const boundarySize = options.boundarySize ?? new THREE.Vector3(4, 2.8, 4);
  const frameCallbacks = new Set();
  const debugKey = options.debugKey ?? document.body?.dataset?.page ?? window.location.pathname;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(background);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.04;

  const camera = new THREE.PerspectiveCamera(48, 1, 0.01, 100);
  camera.position.set(...cameraPosition);
  const defaultViewState = {
    position: [...cameraPosition],
    target: [...target],
    zoom: camera.zoom,
  };
  let persistedViewState = null;
  let suppressViewTracking = 0;
  let idleAnimationEnabled = true;

  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.target.set(...target);
  controls.update();

  function getViewState() {
    return {
      position: camera.position.toArray(),
      target: controls.target.toArray(),
      zoom: camera.zoom,
    };
  }

  function withSuppressedViewTracking(callback) {
    suppressViewTracking += 1;
    try {
      callback();
    } finally {
      suppressViewTracking -= 1;
    }
  }

  function applyRawViewState(viewState) {
    camera.position.set(...viewState.position);
    controls.target.set(...viewState.target);
    if (typeof viewState.zoom === "number" && camera.zoom !== viewState.zoom) {
      camera.zoom = viewState.zoom;
      camera.updateProjectionMatrix();
    }
    controls.update();
  }

  function persistViewState() {
    persistedViewState = getViewState();
    return persistedViewState;
  }

  function clearPersistedViewState() {
    persistedViewState = null;
  }

  function hasPersistedViewState() {
    return persistedViewState !== null;
  }

  function applySceneView(nextPosition, nextTarget, options = {}) {
    const { preserveUserView = true } = options;
    const desiredViewState = {
      position: [...nextPosition],
      target: [...nextTarget],
      zoom: defaultViewState.zoom,
    };

    withSuppressedViewTracking(() => {
      if (preserveUserView && persistedViewState) {
        applyRawViewState(persistedViewState);
        return;
      }
      applyRawViewState(desiredViewState);
    });
  }

  function setViewState(viewState, options = {}) {
    const { persist = false } = options;
    withSuppressedViewTracking(() => {
      applyRawViewState(viewState);
    });
    if (persist) {
      persistedViewState = getViewState();
    }
    return getViewState();
  }

  controls.addEventListener("change", () => {
    if (suppressViewTracking > 0) {
      return;
    }
    persistViewState();
  });

  scene.add(new THREE.HemisphereLight(0xdde7ff, 0x0b1220, 1.1));
  const keyLight = new THREE.DirectionalLight(0xffffff, 1.15);
  keyLight.position.set(5, 8, 4);
  scene.add(keyLight);
  const rimLight = new THREE.DirectionalLight(0x39d2c0, 0.45);
  rimLight.position.set(-4, 2.5, -3);
  scene.add(rimLight);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(6, 6),
    new THREE.MeshStandardMaterial({
      color: 0x111827,
      roughness: 0.94,
      metalness: 0.04,
      side: THREE.DoubleSide,
    }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.02;
  scene.add(floor);

  const grid = new THREE.GridHelper(6, 18, 0x30363d, 0x1f2937);
  grid.position.y = 0;
  scene.add(grid);

  const world = new THREE.Group();
  scene.add(world);

  let boundary = buildBoundaryMesh(boundarySize);
  boundary.position.y = boundarySize.y / 2;
  scene.add(boundary);

  const pointer = buildPointerProxy(pointerColor);
  pointer.position.set(0, 0.45, 0);
  scene.add(pointer);

  const pointerShadow = new THREE.Mesh(
    new THREE.RingGeometry(0.08, 0.12, 32),
    new THREE.MeshBasicMaterial({ color: 0xf2cc60, transparent: true, opacity: 0.4, side: THREE.DoubleSide }),
  );
  pointerShadow.rotation.x = -Math.PI / 2;
  pointerShadow.position.set(0, 0.001, 0);
  scene.add(pointerShadow);

  const clock = new THREE.Clock();

  function resizeRenderer() {
    const parent = canvas.parentElement;
    const width = parent.clientWidth;
    const height = parent.clientHeight;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }

  function setBoundarySize(size) {
    scene.remove(boundary);
    boundary.geometry.dispose();
    boundary.material.dispose();
    boundary = buildBoundaryMesh(size);
    boundary.position.y = size.y / 2;
    scene.add(boundary);
  }

  function setPointerPosition(position) {
    pointer.position.copy(position);
    pointerShadow.position.set(position.x, 0.002, position.z);
  }

  function setPointerState(mode = "idle") {
    const pointerMaterials = pointer.userData.pointerMaterials;
    const palette = {
      idle: {
        tip: pointerColor,
        emissive: 0x664400,
        shaft: 0xc9d1d9,
        shaftEmissive: 0x09111c,
        grip: 0x1f2937,
        ring: pointerColor,
        shadow: pointerColor,
        shadowOpacity: 0.4,
      },
      focus: {
        tip: 0x7ee787,
        emissive: 0x12311b,
        shaft: 0xd2f1dc,
        shaftEmissive: 0x102315,
        grip: 0x1b3a28,
        ring: 0x7ee787,
        shadow: 0x7ee787,
        shadowOpacity: 0.58,
      },
      active: {
        tip: 0x79c0ff,
        emissive: 0x163f63,
        shaft: 0xe6f3ff,
        shaftEmissive: 0x10263a,
        grip: 0x1a2c3f,
        ring: 0x79c0ff,
        shadow: 0x79c0ff,
        shadowOpacity: 0.7,
      },
    }[mode] ?? null;

    if (!palette) {
      return;
    }

    pointerMaterials.tipMaterial.color.setHex(palette.tip);
    pointerMaterials.tipMaterial.emissive.setHex(palette.emissive);
    pointerMaterials.shaftMaterial.color.setHex(palette.shaft);
    pointerMaterials.shaftMaterial.emissive.setHex(palette.shaftEmissive);
    pointerMaterials.gripMaterial.color.setHex(palette.grip);
    pointerMaterials.ringMaterial.color.setHex(palette.ring);
    pointerMaterials.ringMaterial.emissive.setHex(palette.emissive);
    pointerShadow.material.color.setHex(palette.shadow);
    pointerShadow.material.opacity = palette.shadowOpacity;
  }

  function setPointerVisible(visible) {
    pointer.visible = visible;
    pointerShadow.visible = visible;
  }

  function setGridVisible(visible) {
    grid.visible = visible;
  }

  function setBoundaryVisible(visible) {
    boundary.visible = visible;
  }

  function clearWorld() {
    while (world.children.length > 0) {
      const child = world.children[0];
      world.remove(child);
      child.traverse?.((node) => {
        node.geometry?.dispose?.();
        if (Array.isArray(node.material)) {
          node.material.forEach((material) => material.dispose?.());
        } else {
          node.material?.dispose?.();
        }
      });
    }
  }

  function normalizeObject(object, targetSize = 2.2) {
    const box = new THREE.Box3().setFromObject(object);
    const size = box.getSize(new THREE.Vector3());
    const maxDimension = Math.max(size.x, size.y, size.z) || 1;
    const scale = targetSize / maxDimension;
    object.scale.multiplyScalar(scale);

    const scaledBox = new THREE.Box3().setFromObject(object);
    const center = scaledBox.getCenter(new THREE.Vector3());
    object.position.sub(center);
    const groundBox = new THREE.Box3().setFromObject(object);
    object.position.y -= groundBox.min.y;
    return scale;
  }

  function frameObject(object, distance = 4.8) {
    const box = new THREE.Box3().setFromObject(object);
    const center = box.getCenter(new THREE.Vector3());
    applySceneView(
      [center.x + distance * 0.62, center.y + distance * 0.54, center.z + distance],
      center.toArray(),
      { preserveUserView: true },
    );
  }

  function resetCamera() {
    clearPersistedViewState();
    applySceneView(defaultViewState.position, defaultViewState.target, { preserveUserView: false });
  }

  function setIdleAnimationEnabled(enabled) {
    idleAnimationEnabled = Boolean(enabled);
    return idleAnimationEnabled;
  }

  function setDampingEnabled(enabled) {
    controls.enableDamping = Boolean(enabled);
    controls.update();
    return controls.enableDamping;
  }

  function resetIdleAnimatedObjects() {
    world.children.forEach((child) => {
      if (child.userData.rotateOnIdle) {
        child.rotation.y = 0;
      }
    });
  }

  function renderNow() {
    controls.update();
    renderer.render(scene, camera);
  }

  function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    world.children.forEach((child) => {
      if (idleAnimationEnabled && child.userData.rotateOnIdle) {
        child.rotation.y += delta * 0.18;
      }
    });
    frameCallbacks.forEach((callback) => callback(delta));
    renderNow();
  }

  resizeRenderer();
  setPointerState("idle");
  animate();
  window.addEventListener("resize", resizeRenderer);

  const api = {
    THREE,
    scene,
    world,
    camera,
    controls,
    renderer,
    pointer,
    floor,
    grid,
    boundary,
    clearWorld,
    normalizeObject,
    frameObject,
    resetCamera,
    renderNow,
    resizeRenderer,
    getViewState,
    setViewState,
    applySceneView,
    persistViewState,
    clearPersistedViewState,
    hasPersistedViewState,
    registerFrameCallback(callback) {
      frameCallbacks.add(callback);
      return () => frameCallbacks.delete(callback);
    },
    setBoundarySize,
    setBoundaryVisible,
    setGridVisible,
    setPointerPosition,
    setPointerState,
    setPointerVisible,
    setDampingEnabled,
    setIdleAnimationEnabled,
    resetIdleAnimatedObjects,
  };

  window.__feelitSceneDebug ??= {};
  window.__feelitSceneDebug[debugKey] = api;

  return api;
}

export function attachPointerEmulation(sceneApi, options = {}) {
  const keyMap = {
    forward: "KeyW",
    backward: "KeyS",
    left: "KeyA",
    right: "KeyD",
    up: "KeyQ",
    down: "KeyE",
    ...(options.keyMap ?? {}),
  };
  const activationKeys = new Set(options.activationKeys ?? ["Space", "Enter"]);
  const keysDown = new Set();
  const boundsMin = (options.boundsMin ?? new THREE.Vector3(-1.8, 0.12, -1.8)).clone();
  const boundsMax = (options.boundsMax ?? new THREE.Vector3(1.8, 2.4, 1.8)).clone();
  const position = (options.initialPosition ?? sceneApi.pointer.position).clone();
  const speed = options.speed ?? 1.2;
  let lastActivation = 0;

  function clampPosition() {
    position.x = Math.max(boundsMin.x, Math.min(boundsMax.x, position.x));
    position.y = Math.max(boundsMin.y, Math.min(boundsMax.y, position.y));
    position.z = Math.max(boundsMin.z, Math.min(boundsMax.z, position.z));
  }

  function setBounds(min, max) {
    boundsMin.copy(min);
    boundsMax.copy(max);
    clampPosition();
    sceneApi.setPointerPosition(position);
    options.onMove?.(position.clone());
  }

  function setPosition(nextPosition) {
    position.copy(nextPosition);
    clampPosition();
    sceneApi.setPointerPosition(position);
    options.onMove?.(position.clone());
  }

  function getBounds() {
    return {
      min: boundsMin.toArray(),
      max: boundsMax.toArray(),
    };
  }

  function activate() {
    options.onActivate?.(position.clone());
  }

  function handleKeyDown(event) {
    if (isEditableTarget(event.target)) {
      return;
    }

    const wasAlreadyDown = keysDown.has(event.code);
    if (
      Object.values(keyMap).includes(event.code)
      || activationKeys.has(event.code)
      || activationKeys.has(event.key)
    ) {
      event.preventDefault();
    }
    keysDown.add(event.code);
    if (!wasAlreadyDown && (activationKeys.has(event.code) || activationKeys.has(event.key))) {
      const now = performance.now();
      if (now - lastActivation > 120) {
        activate();
        lastActivation = now;
      }
    }
  }

  function handleKeyUp(event) {
    if (isEditableTarget(event.target)) {
      return;
    }
    keysDown.delete(event.code);
  }

  function update(delta) {
    let changed = false;
    const step = speed * Math.max(delta, 1 / 120);

    if (keysDown.has(keyMap.forward)) {
      position.z -= step;
      changed = true;
    }
    if (keysDown.has(keyMap.backward)) {
      position.z += step;
      changed = true;
    }
    if (keysDown.has(keyMap.left)) {
      position.x -= step;
      changed = true;
    }
    if (keysDown.has(keyMap.right)) {
      position.x += step;
      changed = true;
    }
    if (keysDown.has(keyMap.up)) {
      position.y += step;
      changed = true;
    }
    if (keysDown.has(keyMap.down)) {
      position.y -= step;
      changed = true;
    }

    if (!changed) {
      return;
    }

    clampPosition();
    sceneApi.setPointerPosition(position);
    options.onMove?.(position.clone());
  }

  document.addEventListener("keydown", handleKeyDown);
  document.addEventListener("keyup", handleKeyUp);
  const unregisterFrame = sceneApi.registerFrameCallback(update);
  setPosition(position);

  return {
    position,
    setBounds,
    setPosition,
    getBounds,
    activate,
    destroy() {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("keyup", handleKeyUp);
      unregisterFrame();
    },
  };
}

export function createLabelSprite(text, options = {}) {
  const color = options.color ?? "#e6edf3";
  const background = options.background ?? "rgba(13, 17, 23, 0.85)";
  const padding = 18;
  const fontSize = options.fontSize ?? 36;
  const font = `600 ${fontSize}px Segoe UI`;

  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  context.font = font;
  const metrics = context.measureText(text);
  canvas.width = Math.ceil(metrics.width + padding * 2);
  canvas.height = Math.ceil(fontSize + padding * 2);

  const draw = canvas.getContext("2d");
  draw.font = font;
  draw.fillStyle = background;
  if (typeof draw.roundRect === "function") {
    draw.beginPath();
    draw.roundRect(0, 0, canvas.width, canvas.height, 18);
    draw.fill();
  } else {
    draw.fillRect(0, 0, canvas.width, canvas.height);
  }
  draw.fillStyle = color;
  draw.textBaseline = "middle";
  draw.fillText(text, padding, canvas.height / 2 + 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(canvas.width / 140, canvas.height / 140, 1);
  return sprite;
}
