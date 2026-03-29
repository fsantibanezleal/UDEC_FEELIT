import { OBJLoader } from "../vendor/three/OBJLoader.js";
import { THREE, attachPointerEmulation, createWorkspaceScene } from "./three_scene_common.js";

const materialsUrl = "/api/materials";
const demoModelsUrl = "/api/demo-models";

const state = {
  models: [],
  materials: [],
  currentModel: null,
  currentMaterial: null,
  currentObject: null,
  currentBounds: null,
  pointerController: null,
};

function byId(id) {
  return document.getElementById(id);
}

function setStatus(message) {
  byId("object-stage-status").textContent = message;
  byId("explorer-page-status").textContent = message;
}

function materialBySlug(slug) {
  return state.materials.find((material) => material.slug === slug) ?? state.materials[0];
}

function modelBySlug(slug) {
  return state.models.find((model) => model.slug === slug) ?? state.models[0];
}

function updateMaterialPanel(material) {
  byId("telemetry-material").textContent = material.title;
  byId("metric-stiffness").textContent = `${material.stiffness_n_per_mm.toFixed(2)} N/mm`;
  byId("metric-static-friction").textContent = material.static_friction.toFixed(2);
  byId("metric-texture").textContent = `${material.texture_amplitude_mm.toFixed(2)} mm`;
  byId("metric-vibration").textContent = `${material.vibration_hz} Hz`;
  byId("material-summary").textContent = material.capability_note;
}

function updateModelInspector(model) {
  byId("inspector-model-name").textContent = model.title;
  byId("inspector-model-category").textContent = model.category;
  byId("inspector-model-source").textContent = model.source_name;
  byId("inspector-scale-hint").textContent = `${model.scale_hint.toFixed(2)}x`;
  byId("stage-model-description").textContent = model.description;
}

function populateSelect(select, items, valueField, labelField) {
  select.innerHTML = "";
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item[valueField];
    option.textContent = item[labelField];
    select.appendChild(option);
  });
}

function buildExplorationPlinth(material) {
  const group = new THREE.Group();
  const accent = new THREE.Color(material.visual_color);

  const base = new THREE.Mesh(
    new THREE.CylinderGeometry(1.32, 1.42, 0.12, 42),
    new THREE.MeshStandardMaterial({
      color: 0x0f1724,
      roughness: 0.9,
      metalness: 0.06,
    }),
  );
  base.position.y = 0.06;
  group.add(base);

  const topPlate = new THREE.Mesh(
    new THREE.CylinderGeometry(1.06, 1.12, 0.045, 42),
    new THREE.MeshStandardMaterial({
      color: accent.clone().multiplyScalar(0.72),
      roughness: Math.min(0.96, material.visual_roughness + 0.08),
      metalness: Math.max(0.02, material.visual_metalness * 0.5),
      emissive: accent.clone().multiplyScalar(0.05),
    }),
  );
  topPlate.position.y = 0.145;
  group.add(topPlate);

  const guideRing = new THREE.Mesh(
    new THREE.TorusGeometry(1.08, 0.028, 12, 64),
    new THREE.MeshStandardMaterial({
      color: 0x39d2c0,
      emissive: 0x0e2b29,
      roughness: 0.34,
      metalness: 0.16,
    }),
  );
  guideRing.rotation.x = Math.PI / 2;
  guideRing.position.y = 0.17;
  group.add(guideRing);

  return group;
}

function applyMaterialToObject(root, material) {
  const color = new THREE.Color(material.visual_color);
  root.traverse((node) => {
    if (!node.isMesh) {
      return;
    }
    if (Array.isArray(node.material)) {
      node.material.forEach((currentMaterial) => currentMaterial.dispose?.());
    } else {
      node.material?.dispose?.();
    }
    const meshMaterial = new THREE.MeshStandardMaterial({
      color,
      roughness: material.visual_roughness,
      metalness: material.visual_metalness,
      emissive: color.clone().multiplyScalar(0.06),
    });
    node.material = meshMaterial;
    node.castShadow = false;
    node.receiveShadow = true;
  });
}

function updatePointerFeedback(sceneApi, position) {
  if (!state.currentBounds) {
    byId("explorer-stage-pill").textContent = "Pointer emulator";
    sceneApi.setPointerState("idle");
    return;
  }

  const distance = state.currentBounds.distanceToPoint(position);
  if (distance < 0.04) {
    byId("explorer-stage-pill").textContent = "Pointer near surface";
    sceneApi.setPointerState("focus");
    return;
  }

  byId("explorer-stage-pill").textContent = "Pointer in workspace";
  sceneApi.setPointerState("idle");
}

function activatePointer(sceneApi) {
  if (!state.currentBounds) {
    setStatus("No object is loaded for pointer activation.");
    return;
  }

  const distance = state.currentBounds.distanceToPoint(state.pointerController.position);
  if (distance < 0.12) {
    setStatus("Pointer activation registered on the current object surface.");
    sceneApi.setPointerState("active");
    window.setTimeout(() => updatePointerFeedback(sceneApi, state.pointerController.position), 180);
    return;
  }

  setStatus("Pointer activation is outside the current object envelope.");
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

async function loadObjectIntoScene(sceneApi, object, model) {
  const scaleFactor = Number(byId("workspace-scale").value) / 100;
  sceneApi.clearWorld();
  sceneApi.world.add(buildExplorationPlinth(state.currentMaterial));
  applyMaterialToObject(object, state.currentMaterial);
  object.userData.rotateOnIdle = true;
  sceneApi.world.add(object);
  const targetSize = 2.2 * scaleFactor * model.scale_hint;
  sceneApi.normalizeObject(object, targetSize);
  object.position.y += 0.18;
  sceneApi.frameObject(object);
  state.currentObject = object;
  state.currentBounds = new THREE.Box3().setFromObject(object);
  const objectSize = state.currentBounds.getSize(new THREE.Vector3());
  const objectCenter = state.currentBounds.getCenter(new THREE.Vector3());
  sceneApi.setBoundarySize(
    new THREE.Vector3(
      Math.max(3.8, objectSize.x + 1.8),
      Math.max(2.2, objectSize.y + 0.9),
      Math.max(3.8, objectSize.z + 1.8),
    ),
  );
  state.pointerController?.setBounds(
    new THREE.Vector3(objectCenter.x - objectSize.x * 0.7, 0.14, objectCenter.z - objectSize.z * 0.7),
    new THREE.Vector3(objectCenter.x + objectSize.x * 0.7, Math.max(1.4, objectSize.y + 0.8), objectCenter.z + objectSize.z * 0.7),
  );
  state.pointerController?.setPosition(
    objectCenter.clone().add(new THREE.Vector3(objectSize.x * 0.35, Math.min(objectSize.y + 0.35, 1.2), objectSize.z * 0.35)),
  );
  updateModelInspector(model);
  setStatus(`Loaded ${model.title} into the bounded scene.`);
}

async function loadSelectedModel(sceneApi) {
  const model = modelBySlug(byId("sample-model").value);
  const localFile = byId("model-file").files[0];
  const loader = new OBJLoader();

  state.currentModel = model;
  state.currentMaterial = materialBySlug(byId("material-select").value || model.default_material);
  updateMaterialPanel(state.currentMaterial);

  if (localFile) {
    const text = await localFile.text();
    const object = loader.parse(text);
    const localModel = {
      ...model,
      title: localFile.name,
      category: "local_obj",
      source_name: "Local upload",
      description: "Local OBJ file parsed in-browser for visual and future haptic staging.",
      scale_hint: 1.0,
    };
    await loadObjectIntoScene(sceneApi, object, localModel);
    return;
  }

  return new Promise((resolve, reject) => {
    setStatus(`Loading ${model.title}...`);
    loader.load(
      model.file_url,
      async (object) => {
        await loadObjectIntoScene(sceneApi, object, model);
        resolve();
      },
      undefined,
      (error) => {
        setStatus(`Unable to load ${model.title}.`);
        reject(error);
      },
    );
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  const shell = await window.FeelITShell.loadShell();
  const sceneApi = createWorkspaceScene(byId("object-canvas"), {
    cameraPosition: [3.8, 2.9, 4.8],
    target: [0, 0.8, 0],
  });

  state.pointerController = attachPointerEmulation(sceneApi, {
    initialPosition: new THREE.Vector3(0, 0.45, 0),
    boundsMin: new THREE.Vector3(-1.9, 0.12, -1.9),
    boundsMax: new THREE.Vector3(1.9, 2.3, 1.9),
    speed: 1.65,
    onMove: (position) => updatePointerFeedback(sceneApi, position),
    onActivate: () => activatePointer(sceneApi),
  });

  const [materialPayload, modelPayload] = await Promise.all([
    fetchJson(materialsUrl),
    fetchJson(demoModelsUrl),
  ]);

  state.materials = materialPayload.materials;
  state.models = modelPayload.models;

  populateSelect(byId("material-select"), state.materials, "slug", "title");
  populateSelect(byId("sample-model"), state.models, "slug", "title");

  const initialModel = state.models[0];
  byId("sample-model").value = initialModel.slug;
  byId("material-select").value = initialModel.default_material;
  state.currentMaterial = materialBySlug(initialModel.default_material);
  updateMaterialPanel(state.currentMaterial);

  byId("explorer-stage-pill").textContent =
    shell.health.haptics.mode === "available" ? "Haptic ready" : "Pointer emulator";

  byId("load-selection").addEventListener("click", () => {
    loadSelectedModel(sceneApi).catch(() => {
      setStatus("Model loading failed.");
    });
  });

  byId("reset-camera").addEventListener("click", () => {
    sceneApi.resetCamera();
    setStatus("Camera reset to default framing.");
  });

  byId("sample-model").addEventListener("change", () => {
    const model = modelBySlug(byId("sample-model").value);
    byId("material-select").value = model.default_material;
    state.currentMaterial = materialBySlug(model.default_material);
    updateMaterialPanel(state.currentMaterial);
    updateModelInspector(model);
    setStatus(`Selected ${model.title}.`);
  });

  byId("material-select").addEventListener("change", () => {
    state.currentMaterial = materialBySlug(byId("material-select").value);
    updateMaterialPanel(state.currentMaterial);
    if (state.currentObject) {
      applyMaterialToObject(state.currentObject, state.currentMaterial);
    }
    setStatus(`Applied ${state.currentMaterial.title}.`);
  });

  byId("workspace-scale").addEventListener("input", () => {
    const value = Number(byId("workspace-scale").value);
    byId("workspace-scale-value").textContent = `${value}%`;
  });

  byId("guidance-grid-toggle").addEventListener("change", (event) => {
    sceneApi.setGridVisible(event.target.checked);
  });

  byId("boundary-toggle").addEventListener("change", (event) => {
    sceneApi.setBoundaryVisible(event.target.checked);
  });

  byId("pointer-toggle").addEventListener("change", (event) => {
    sceneApi.setPointerVisible(event.target.checked);
  });

  updateModelInspector(initialModel);
  await loadSelectedModel(sceneApi);
  updatePointerFeedback(sceneApi, state.pointerController.position);
});
