import * as THREE from "../vendor/three/three.module.js";
import { OrbitControls } from "../vendor/three/OrbitControls.js";

export { THREE };

function buildBoundaryMesh(size) {
  const geometry = new THREE.EdgesGeometry(new THREE.BoxGeometry(size.x, size.y, size.z));
  const material = new THREE.LineBasicMaterial({ color: 0x58a6ff, transparent: true, opacity: 0.45 });
  return new THREE.LineSegments(geometry, material);
}

export function createWorkspaceScene(canvas, options = {}) {
  const background = options.background ?? 0x0d1117;
  const cameraPosition = options.cameraPosition ?? [3.6, 2.8, 4.6];
  const target = options.target ?? [0, 0.6, 0];
  const pointerColor = options.pointerColor ?? 0xf2cc60;
  const boundarySize = options.boundarySize ?? new THREE.Vector3(4, 2.8, 4);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(background);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const camera = new THREE.PerspectiveCamera(48, 1, 0.01, 100);
  camera.position.set(...cameraPosition);

  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.target.set(...target);
  controls.update();

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

  const pointer = new THREE.Mesh(
    new THREE.SphereGeometry(0.08, 24, 18),
    new THREE.MeshStandardMaterial({
      color: pointerColor,
      emissive: 0x664400,
      roughness: 0.3,
      metalness: 0.08,
    }),
  );
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
    controls.target.copy(center);
    camera.position.set(center.x + distance * 0.62, center.y + distance * 0.54, center.z + distance);
    controls.update();
  }

  function resetCamera() {
    camera.position.set(...cameraPosition);
    controls.target.set(...target);
    controls.update();
  }

  function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    world.children.forEach((child) => {
      if (child.userData.rotateOnIdle) {
        child.rotation.y += delta * 0.18;
      }
    });
    controls.update();
    renderer.render(scene, camera);
  }

  resizeRenderer();
  animate();
  window.addEventListener("resize", resizeRenderer);

  return {
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
    resizeRenderer,
    setBoundarySize,
    setBoundaryVisible,
    setGridVisible,
    setPointerPosition,
    setPointerVisible,
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
  draw.beginPath();
  draw.roundRect(0, 0, canvas.width, canvas.height, 18);
  draw.fill();
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
