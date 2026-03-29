import { OBJLoader } from "../vendor/three/OBJLoader.js";
import { THREE, createWorkspaceScene } from "./three_scene_common.js";

const materialsUrl = "/api/materials";
const demoModelsUrl = "/api/demo-models";

const state = {
  models: [],
  materials: [],
  currentModel: null,
  currentMaterial: null,
  currentObject: null,
  currentBounds: null,
  pointer: new THREE.Vector3(0, 0.45, 0),
  keysDown: new Set(),
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

function applyMaterialToObject(root, material) {
  const color = new THREE.Color(material.visual_color);
  root.traverse((node) => {
    if (!node.isMesh) {
      return;
    }
    const meshMaterial = new THREE.MeshStandardMaterial({
      color,
      roughness: material.visual_roughness,
      metalness: material.visual_metalness,
      emissive: color.clone().multiplyScalar(0.06),
    });
    node.material.dispose?.();
    node.material = meshMaterial;
    node.castShadow = false;
    node.receiveShadow = true;
  });
}

function registerPointerMovement(sceneApi) {
  document.addEventListener("keydown", (event) => {
    state.keysDown.add(event.code);
  });
  document.addEventListener("keyup", (event) => {
    state.keysDown.delete(event.code);
  });

  setInterval(() => {
    const speed = 0.06;
    if (state.keysDown.has("KeyW")) state.pointer.z -= speed;
    if (state.keysDown.has("KeyS")) state.pointer.z += speed;
    if (state.keysDown.has("KeyA")) state.pointer.x -= speed;
    if (state.keysDown.has("KeyD")) state.pointer.x += speed;
    if (state.keysDown.has("KeyQ")) state.pointer.y += speed;
    if (state.keysDown.has("KeyE")) state.pointer.y -= speed;

    state.pointer.x = Math.max(-1.9, Math.min(1.9, state.pointer.x));
    state.pointer.z = Math.max(-1.9, Math.min(1.9, state.pointer.z));
    state.pointer.y = Math.max(0.12, Math.min(2.3, state.pointer.y));
    sceneApi.setPointerPosition(state.pointer);

    if (state.currentBounds) {
      const distance = state.currentBounds.distanceToPoint(state.pointer);
      if (distance < 0.08) {
        byId("explorer-stage-pill").textContent = "Pointer near surface";
      } else {
        byId("explorer-stage-pill").textContent = "Visual fallback";
      }
    }
  }, 35);
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
  applyMaterialToObject(object, state.currentMaterial);
  object.userData.rotateOnIdle = true;
  sceneApi.world.add(object);
  const targetSize = 2.2 * scaleFactor * model.scale_hint;
  sceneApi.normalizeObject(object, targetSize);
  sceneApi.frameObject(object);
  state.currentObject = object;
  state.currentBounds = new THREE.Box3().setFromObject(object);
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

  state.pointer.set(0, 0.45, 0);
  sceneApi.setPointerPosition(state.pointer);
  registerPointerMovement(sceneApi);

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
    shell.health.haptics.mode === "available" ? "Haptic ready" : "Visual fallback";

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
});
