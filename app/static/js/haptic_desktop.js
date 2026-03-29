import { bootWorkspace } from "./app.js";
import {
  THREE,
  attachPointerEmulation,
  createWorkspaceScene,
} from "./three_scene_common.js";

const desktopItems = [
  {
    slug: "models_library",
    label: "Models Library",
    type: "Folder",
    action: "Open models library",
    description: "Curated collection of tactile 3D objects.",
    color: 0x58a6ff,
  },
  {
    slug: "braille_shelf",
    label: "Braille Shelf",
    type: "Reader",
    action: "Open reading shelf",
    description: "Entry point for tactile reading sessions.",
    color: 0x7ee787,
  },
  {
    slug: "audio_notes",
    label: "Audio Notes",
    type: "Media",
    action: "Play audio notes",
    description: "Short guidance clips that accompany tactile tasks.",
    color: 0xf2cc60,
  },
  {
    slug: "recent_scenes",
    label: "Recent Scenes",
    type: "Workspace",
    action: "Open recent scenes",
    description: "Resume an object exploration or reading world.",
    color: 0xc297ff,
  },
  {
    slug: "device_setup",
    label: "Device Setup",
    type: "Settings",
    action: "Open device settings",
    description: "Review available haptic backends and calibration.",
    color: 0xffa657,
  },
  {
    slug: "help_desk",
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
  pointerController: null,
  hoveredIndex: null,
};

function byId(id) {
  return document.getElementById(id);
}

function announce(text) {
  if (byId("desktop-announcement").textContent === text) {
    return;
  }
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

function buildPedestal(item) {
  const group = new THREE.Group();

  const pedestal = new THREE.Mesh(
    new THREE.CylinderGeometry(0.32, 0.36, 0.08, 32),
    new THREE.MeshStandardMaterial({ color: 0x0f1724, roughness: 0.88, metalness: 0.04 }),
  );
  pedestal.position.y = 0.04;
  group.add(pedestal);

  const halo = new THREE.Mesh(
    new THREE.TorusGeometry(0.36, 0.024, 10, 40),
    new THREE.MeshStandardMaterial({
      color: item.color,
      emissive: 0x08111a,
      transparent: true,
      opacity: 0.42,
      roughness: 0.34,
      metalness: 0.08,
    }),
  );
  halo.rotation.x = Math.PI / 2;
  halo.position.y = 0.095;
  halo.userData.kind = "focus-halo";
  halo.userData.baseOpacity = halo.material.opacity;
  group.add(halo);

  return group;
}

function markAccent(mesh) {
  mesh.userData.kind = "focus-target";
  if (typeof mesh.material.roughness === "number") {
    mesh.userData.baseRoughness = mesh.material.roughness;
  }
  return mesh;
}

function buildLibraryShape(item) {
  const group = new THREE.Group();
  [-0.14, 0, 0.14].forEach((offset, index) => {
    const slab = markAccent(
      new THREE.Mesh(
        new THREE.BoxGeometry(0.11, 0.38 + index * 0.04, 0.28),
        new THREE.MeshStandardMaterial({
          color: item.color,
          roughness: 0.42,
          metalness: 0.16,
          emissive: 0x061018,
        }),
      ),
    );
    slab.position.set(offset, 0.24 + index * 0.02, 0);
    slab.rotation.z = index === 1 ? 0 : (index === 0 ? -0.08 : 0.08);
    group.add(slab);
  });
  return group;
}

function buildBrailleShelfShape(item) {
  const group = new THREE.Group();
  const slab = markAccent(
    new THREE.Mesh(
      new THREE.BoxGeometry(0.46, 0.14, 0.34),
      new THREE.MeshStandardMaterial({
        color: item.color,
        roughness: 0.5,
        metalness: 0.08,
        emissive: 0x08111a,
      }),
    ),
  );
  slab.position.y = 0.14;
  group.add(slab);

  const offsets = [
    [-0.09, 0.05],
    [0.01, 0.05],
    [-0.09, -0.02],
    [0.01, -0.02],
    [-0.09, -0.09],
    [0.01, -0.09],
  ];
  offsets.forEach(([x, z], index) => {
    if (index === 1 || index === 2 || index === 4 || index === 5) {
      const dot = markAccent(
        new THREE.Mesh(
          new THREE.SphereGeometry(0.03, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2),
          new THREE.MeshStandardMaterial({
            color: 0xe6edf3,
            roughness: 0.22,
            metalness: 0.04,
            emissive: 0x14263d,
          }),
        ),
      );
      dot.rotation.x = Math.PI;
      dot.position.set(x, 0.225, z);
      group.add(dot);
    }
  });
  return group;
}

function buildAudioShape(item) {
  const group = new THREE.Group();
  const speaker = markAccent(
    new THREE.Mesh(
      new THREE.CylinderGeometry(0.18, 0.22, 0.42, 32),
      new THREE.MeshStandardMaterial({
        color: item.color,
        roughness: 0.4,
        metalness: 0.18,
        emissive: 0x08111a,
      }),
    ),
  );
  speaker.position.y = 0.25;
  group.add(speaker);

  [0.16, 0.25].forEach((radius, index) => {
    const ring = markAccent(
      new THREE.Mesh(
        new THREE.TorusGeometry(radius, 0.016, 10, 32),
        new THREE.MeshStandardMaterial({
          color: item.color,
          roughness: 0.26,
          metalness: 0.08,
          emissive: 0x302300,
          transparent: true,
          opacity: 0.85 - index * 0.18,
        }),
      ),
    );
    ring.rotation.y = Math.PI / 2;
    ring.position.set(0.16 + index * 0.12, 0.28, 0);
    group.add(ring);
  });
  return group;
}

function buildRecentScenesShape(item) {
  const group = new THREE.Group();
  [0, 1, 2].forEach((index) => {
    const frame = markAccent(
      new THREE.Mesh(
        new THREE.BoxGeometry(0.34, 0.06, 0.42),
        new THREE.MeshStandardMaterial({
          color: item.color,
          roughness: 0.46,
          metalness: 0.1,
          emissive: 0x08111a,
        }),
      ),
    );
    frame.position.set(-0.08 + index * 0.08, 0.14 + index * 0.1, 0);
    frame.rotation.x = -0.3;
    frame.rotation.y = -0.12 + index * 0.08;
    group.add(frame);
  });
  return group;
}

function buildDeviceSetupShape(item) {
  const group = new THREE.Group();
  const hub = markAccent(
    new THREE.Mesh(
      new THREE.CylinderGeometry(0.16, 0.16, 0.18, 28),
      new THREE.MeshStandardMaterial({
        color: item.color,
        roughness: 0.34,
        metalness: 0.28,
        emissive: 0x14100a,
      }),
    ),
  );
  hub.position.y = 0.22;
  group.add(hub);

  for (let index = 0; index < 8; index += 1) {
    const tooth = markAccent(
      new THREE.Mesh(
        new THREE.BoxGeometry(0.08, 0.12, 0.08),
        new THREE.MeshStandardMaterial({
          color: item.color,
          roughness: 0.36,
          metalness: 0.24,
          emissive: 0x14100a,
        }),
      ),
    );
    const angle = (index / 8) * Math.PI * 2;
    tooth.position.set(Math.cos(angle) * 0.24, 0.22, Math.sin(angle) * 0.24);
    tooth.rotation.y = angle;
    group.add(tooth);
  }
  return group;
}

function buildHelpDeskShape(item) {
  const group = new THREE.Group();
  const pillar = markAccent(
    new THREE.Mesh(
      new THREE.CylinderGeometry(0.12, 0.16, 0.52, 24),
      new THREE.MeshStandardMaterial({
        color: item.color,
        roughness: 0.38,
        metalness: 0.1,
        emissive: 0x08111a,
      }),
    ),
  );
  pillar.position.y = 0.3;
  group.add(pillar);

  const cap = markAccent(
    new THREE.Mesh(
      new THREE.SphereGeometry(0.12, 18, 14),
      new THREE.MeshStandardMaterial({
        color: 0xe6edf3,
        roughness: 0.22,
        metalness: 0.14,
        emissive: 0x10263a,
      }),
    ),
  );
  cap.position.y = 0.6;
  cap.scale.set(1, 0.7, 1);
  group.add(cap);
  return group;
}

function buildDesktopObject(item, position) {
  const group = new THREE.Group();
  group.position.copy(position);
  group.userData.accentColor = item.color;
  group.add(buildPedestal(item));

  const shapeBuilders = {
    models_library: buildLibraryShape,
    braille_shelf: buildBrailleShelfShape,
    audio_notes: buildAudioShape,
    recent_scenes: buildRecentScenesShape,
    device_setup: buildDeviceSetupShape,
    help_desk: buildHelpDeskShape,
  };
  group.add(shapeBuilders[item.slug](item));

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

  const frontRidge = new THREE.Mesh(
    new THREE.BoxGeometry(4.0, 0.06, 0.08),
    new THREE.MeshStandardMaterial({ color: 0x0f1724, roughness: 0.88, metalness: 0.04 }),
  );
  frontRidge.position.set(0, 0.11, 1.44);
  sceneApi.world.add(frontRidge);

  const originMarker = new THREE.Mesh(
    new THREE.ConeGeometry(0.09, 0.16, 3),
    new THREE.MeshStandardMaterial({
      color: 0x39d2c0,
      roughness: 0.32,
      metalness: 0.04,
      emissive: 0x0e2b29,
    }),
  );
  originMarker.rotation.y = Math.PI;
  originMarker.position.set(-1.82, 0.17, 1.22);
  sceneApi.world.add(originMarker);

  const positions = layoutPositions(state.layout);
  desktopItems.forEach((item, index) => {
    const group = buildDesktopObject(item, positions[index]);
    group.userData.itemIndex = index;
    state.meshes.push(group);
    sceneApi.world.add(group);
  });

  sceneApi.setBoundarySize(new THREE.Vector3(5.0, 1.4, 3.8));
  state.pointerController?.setBounds(
    new THREE.Vector3(-2.1, 0.18, -1.55),
    new THREE.Vector3(2.1, 0.95, 1.55),
  );
  updateFocus(sceneApi, "layout");
}

function updateFocus(sceneApi, source = "focus") {
  const item = desktopItems[state.focusIndex];
  state.meshes.forEach((group, index) => {
    group.traverse((node) => {
      if (!node.isMesh) {
        return;
      }

      if (node.userData.kind === "focus-target") {
        node.material.emissive.setHex(index === state.focusIndex ? 0x1f6feb : 0x08111a);
        if (typeof node.userData.baseRoughness === "number") {
          node.material.roughness = index === state.focusIndex
            ? Math.max(0.2, node.userData.baseRoughness - 0.08)
            : node.userData.baseRoughness;
        }
      }

      if (node.userData.kind === "focus-halo") {
        node.material.opacity = index === state.focusIndex ? 0.78 : node.userData.baseOpacity;
        node.material.emissive.setHex(index === state.focusIndex ? 0x1f6feb : 0x08111a);
      }
    });
  });

  const focusPosition = state.meshes[state.focusIndex].position.clone();
  if (source !== "pointer") {
    state.pointerController?.setPosition(focusPosition.clone().add(new THREE.Vector3(0, 0.62, 0.42)));
  }
  sceneApi.setPointerState(source === "pointer" ? "focus" : "idle");

  byId("desktop-focus-count").textContent = `${state.focusIndex + 1} / ${desktopItems.length}`;
  byId("desktop-focus-label").textContent = item.label;
  byId("desktop-focus-type").textContent = item.type;
  byId("desktop-focus-action").textContent = item.action;
  announce(
    source === "pointer"
      ? `Pointer over ${item.label}. ${item.description}`
      : `${item.label}. ${item.description}`,
  );
}

function moveFocus(sceneApi, step) {
  state.focusIndex = (state.focusIndex + step + desktopItems.length) % desktopItems.length;
  updateFocus(sceneApi);
}

function activateFocusedItem(sceneApi, source = "pointer") {
  const item = desktopItems[state.focusIndex];
  sceneApi.setPointerState("active");
  window.setTimeout(() => {
    sceneApi.setPointerState(source === "pointer" ? "focus" : "idle");
  }, 180);
  announce(
    source === "pointer"
      ? `${item.label}. ${item.action}. Pointer activation confirmed.`
      : `${item.label}. ${item.action}.`,
  );
}

function updatePointerFocus(sceneApi, position) {
  let nearestIndex = null;
  let nearestDistance = Number.POSITIVE_INFINITY;

  state.meshes.forEach((group, index) => {
    const target = group.position.clone().add(new THREE.Vector3(0, 0.32, 0));
    const distance = target.distanceTo(position);
    if (distance <= 0.68 && distance < nearestDistance) {
      nearestDistance = distance;
      nearestIndex = index;
    }
  });

  if (nearestIndex === null) {
    state.hoveredIndex = null;
    sceneApi.setPointerState("idle");
    announce("Pointer moving across the desktop workspace.");
    return;
  }

  if (state.hoveredIndex !== nearestIndex || state.focusIndex !== nearestIndex) {
    state.hoveredIndex = nearestIndex;
    state.focusIndex = nearestIndex;
    updateFocus(sceneApi, "pointer");
  }
}

function activatePointerTarget(sceneApi) {
  if (state.hoveredIndex === null) {
    announce("No desktop object is currently under the pointer.");
    return;
  }
  state.focusIndex = state.hoveredIndex;
  activateFocusedItem(sceneApi, "pointer");
}

document.addEventListener("DOMContentLoaded", () => {
  bootWorkspace(
    {
      title: "Haptic Desktop startup failed",
      stageSelector: "#desktop-canvas",
      runtimePillId: "desktop-runtime-pill",
      runtimePillText: "Runtime error",
      pageStatusId: "desktop-page-status",
      pageStatusText: "Boot failed",
      stageStatusId: "desktop-status-bar",
      summaryIds: ["desktop-focus-label", "desktop-focus-type", "desktop-focus-action", "desktop-announcement"],
    },
    async () => {
      const sceneApi = createWorkspaceScene(byId("desktop-canvas"), {
        cameraPosition: [4.2, 3.0, 4.2],
        target: [0, 0.38, 0],
        boundarySize: new THREE.Vector3(5.0, 1.4, 3.8),
      });

      state.pointerController = attachPointerEmulation(sceneApi, {
        initialPosition: new THREE.Vector3(-1.1, 0.72, -0.2),
        boundsMin: new THREE.Vector3(-2.1, 0.18, -1.55),
        boundsMax: new THREE.Vector3(2.1, 0.95, 1.55),
        speed: 1.7,
        onMove: (position) => updatePointerFocus(sceneApi, position),
        onActivate: () => activatePointerTarget(sceneApi),
      });

      renderLayout(sceneApi);

      byId("focus-prev").addEventListener("click", () => moveFocus(sceneApi, -1));
      byId("focus-next").addEventListener("click", () => moveFocus(sceneApi, 1));
      byId("focus-activate").addEventListener("click", () => activateFocusedItem(sceneApi, "fallback"));

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
          activateFocusedItem(sceneApi, "fallback");
        }
      });
    },
  );
});
