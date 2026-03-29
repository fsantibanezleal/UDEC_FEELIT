import { THREE, createLabelSprite, createWorkspaceScene } from "./three_scene_common.js";

const desktopItems = [
  {
    label: "Models Library",
    type: "Folder",
    action: "Open models library",
    description: "Curated collection of tactile 3D objects.",
    color: 0x58a6ff,
  },
  {
    label: "Braille Shelf",
    type: "Reader",
    action: "Open reading shelf",
    description: "Entry point for tactile reading sessions.",
    color: 0x7ee787,
  },
  {
    label: "Audio Notes",
    type: "Media",
    action: "Play audio notes",
    description: "Short guidance clips that accompany tactile tasks.",
    color: 0xf2cc60,
  },
  {
    label: "Recent Scenes",
    type: "Workspace",
    action: "Open recent scenes",
    description: "Resume an object exploration or reading world.",
    color: 0xc297ff,
  },
  {
    label: "Device Setup",
    type: "Settings",
    action: "Open device settings",
    description: "Review available haptic backends and calibration.",
    color: 0xffa657,
  },
  {
    label: "Help Desk",
    type: "Support",
    action: "Open help desk",
    description: "Access instructions, labels, and support notes.",
    color: 0x39d2c0,
  },
];

const state = {
  focusIndex: 0,
  meshes: [],
  layout: "grid",
};

function byId(id) {
  return document.getElementById(id);
}

function announce(text) {
  byId("desktop-announcement").textContent = text;
  byId("desktop-status-bar").textContent = text;
  byId("desktop-page-status").textContent = text;
}

function layoutPositions(layout) {
  if (layout === "arc") {
    return desktopItems.map((_, index) => {
      const angle = -0.9 + index * 0.36;
      return new THREE.Vector3(Math.sin(angle) * 1.55, 0.25, Math.cos(angle) * 1.1 - 0.2);
    });
  }
  if (layout === "cluster") {
    return [
      new THREE.Vector3(-1.0, 0.25, -0.7),
      new THREE.Vector3(0.0, 0.25, -0.75),
      new THREE.Vector3(1.0, 0.25, -0.68),
      new THREE.Vector3(-0.8, 0.25, 0.55),
      new THREE.Vector3(0.2, 0.25, 0.48),
      new THREE.Vector3(1.1, 0.25, 0.62),
    ];
  }
  return [
    new THREE.Vector3(-1.1, 0.25, -0.65),
    new THREE.Vector3(0, 0.25, -0.65),
    new THREE.Vector3(1.1, 0.25, -0.65),
    new THREE.Vector3(-1.1, 0.25, 0.65),
    new THREE.Vector3(0, 0.25, 0.65),
    new THREE.Vector3(1.1, 0.25, 0.65),
  ];
}

function buildDesktopObject(item, position) {
  const group = new THREE.Group();
  group.position.copy(position);

  const pedestal = new THREE.Mesh(
    new THREE.CylinderGeometry(0.32, 0.36, 0.08, 32),
    new THREE.MeshStandardMaterial({ color: 0x0f1724, roughness: 0.88, metalness: 0.04 }),
  );
  pedestal.position.y = 0.04;
  group.add(pedestal);

  const block = new THREE.Mesh(
    new THREE.BoxGeometry(0.48, 0.34, 0.38),
    new THREE.MeshStandardMaterial({
      color: item.color,
      roughness: 0.42,
      metalness: 0.12,
      emissive: 0x061018,
    }),
  );
  block.position.y = 0.24;
  block.userData.kind = "focus-block";
  group.add(block);

  const label = createLabelSprite(item.label, {
    background: "rgba(13,17,23,0.88)",
    color: "#e6edf3",
    fontSize: 28,
  });
  label.position.set(0, 0.68, 0);
  group.add(label);

  return group;
}

function renderLayout(sceneApi) {
  sceneApi.clearWorld();
  state.meshes = [];

  const desk = new THREE.Mesh(
    new THREE.BoxGeometry(4.4, 0.1, 3.2),
    new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.94, metalness: 0.06 }),
  );
  desk.position.y = 0.05;
  sceneApi.world.add(desk);

  const positions = layoutPositions(state.layout);
  desktopItems.forEach((item, index) => {
    const group = buildDesktopObject(item, positions[index]);
    group.userData.itemIndex = index;
    state.meshes.push(group);
    sceneApi.world.add(group);
  });

  sceneApi.setBoundarySize(new THREE.Vector3(5.0, 1.4, 3.8));
  updateFocus(sceneApi);
}

function updateFocus(sceneApi) {
  const item = desktopItems[state.focusIndex];
  state.meshes.forEach((group, index) => {
    group.traverse((node) => {
      if (!node.isMesh || node.userData.kind !== "focus-block") {
        return;
      }
      node.material.emissive.setHex(index === state.focusIndex ? 0x1f6feb : 0x061018);
      node.material.roughness = index === state.focusIndex ? 0.28 : 0.42;
    });
  });

  const focusPosition = state.meshes[state.focusIndex].position.clone();
  sceneApi.setPointerPosition(focusPosition.clone().add(new THREE.Vector3(0, 0.62, 0.42)));

  byId("desktop-focus-count").textContent = `${state.focusIndex + 1} / ${desktopItems.length}`;
  byId("desktop-focus-label").textContent = item.label;
  byId("desktop-focus-type").textContent = item.type;
  byId("desktop-focus-action").textContent = item.action;
  announce(`${item.label}. ${item.description}`);
}

function moveFocus(sceneApi, step) {
  state.focusIndex = (state.focusIndex + step + desktopItems.length) % desktopItems.length;
  updateFocus(sceneApi);
}

function activateFocusedItem() {
  const item = desktopItems[state.focusIndex];
  announce(`${item.label}. ${item.action}.`);
}

document.addEventListener("DOMContentLoaded", async () => {
  await window.FeelITShell.loadShell();

  const sceneApi = createWorkspaceScene(byId("desktop-canvas"), {
    cameraPosition: [4.2, 3.0, 4.2],
    target: [0, 0.38, 0],
    boundarySize: new THREE.Vector3(5.0, 1.4, 3.8),
  });

  renderLayout(sceneApi);

  byId("focus-prev").addEventListener("click", () => moveFocus(sceneApi, -1));
  byId("focus-next").addEventListener("click", () => moveFocus(sceneApi, 1));
  byId("focus-activate").addEventListener("click", activateFocusedItem);

  byId("layout-preset").addEventListener("change", (event) => {
    state.layout = event.target.value;
    renderLayout(sceneApi);
    announce(`Layout preset changed to ${event.target.value}.`);
  });

  byId("audio-cues-toggle").addEventListener("change", (event) => {
    byId("desktop-audio-state").textContent = event.target.checked ? "On" : "Off";
    announce(event.target.checked ? "Audio cue labels enabled." : "Audio cue labels disabled.");
  });

  byId("pointer-toggle").addEventListener("change", (event) => {
    sceneApi.setPointerVisible(event.target.checked);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      moveFocus(sceneApi, -1);
    }
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      moveFocus(sceneApi, 1);
    }
    if (event.key === "Enter") {
      activateFocusedItem();
    }
  });
});
