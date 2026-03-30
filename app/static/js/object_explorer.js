import { bootWorkspace } from "./app.js";
import {
  loadLocalModelBundle,
  loadLocalModelFile,
  loadModelFromUrl,
  modelFileAcceptString,
  modelFormatFromFilename,
  modelFormatLabel,
} from "./model_loading.js";
import {
  THREE,
  attachPointerEmulation,
  createLabelSprite,
  createWorkspaceScene,
} from "./three_scene_common.js";

const materialsUrl = "/api/materials";
const demoModelsUrl = "/api/demo-models";
const modelValidationUrl = "/api/models/validate-local-upload";
const modelBundleValidationUrl = "/api/models/validate-local-bundle";
const LAUNCHER_PAGE_SIZE = 3;
const LAUNCHER_VIEW_STATE = {
  position: [4.6, 2.8, 5.2],
  target: [0, 0.32, 0.12],
  zoom: 1,
};

const state = {
  models: [],
  materials: [],
  currentModel: null,
  currentMaterial: null,
  currentObject: null,
  currentBounds: null,
  pointerController: null,
  sceneApi: null,
  sceneMode: "launcher",
  launcherPage: 0,
  hoveredTargetId: null,
  interactiveGroups: new Map(),
  targetById: new Map(),
  modelTemplateCache: new Map(),
  renderGeneration: 0,
  localValidation: null,
  localValidationFingerprint: null,
};

function byId(id) {
  return document.getElementById(id);
}

function setStatus(message) {
  byId("object-stage-status").textContent = message;
  byId("explorer-page-status").textContent = message;
}

function setSceneMode(mode) {
  state.sceneMode = mode;
  byId("explorer-scene-mode").textContent =
    mode === "launcher" ? "Scene launcher" : "Exploration scene";
}

function updateLauncherPageIndicator(page = state.launcherPage) {
  byId("explorer-launcher-page").textContent = `${page + 1} / ${Math.max(1, launcherPageCount())}`;
}

function materialBySlug(slug) {
  return state.materials.find((material) => material.slug === slug) ?? state.materials[0] ?? null;
}

function modelBySlug(slug) {
  return state.models.find((model) => model.slug === slug) ?? state.models[0] ?? null;
}

function launcherPageCount() {
  return Math.max(1, Math.ceil(state.models.length / LAUNCHER_PAGE_SIZE));
}

function launcherPageSlice(page = state.launcherPage) {
  const pageCount = launcherPageCount();
  const safePage = Math.min(Math.max(page, 0), pageCount - 1);
  const start = safePage * LAUNCHER_PAGE_SIZE;
  return {
    page: safePage,
    pageCount,
    models: state.models.slice(start, start + LAUNCHER_PAGE_SIZE),
  };
}

function launcherPageForModel(slug) {
  const index = state.models.findIndex((model) => model.slug === slug);
  if (index < 0) {
    return 0;
  }
  return Math.floor(index / LAUNCHER_PAGE_SIZE);
}

function updateMaterialPanel(material) {
  if (!material) {
    return;
  }
  byId("telemetry-material").textContent = material.title;
  byId("metric-stiffness").textContent = `${material.stiffness_n_per_mm.toFixed(2)} N/mm`;
  byId("metric-static-friction").textContent = material.static_friction.toFixed(2);
  byId("metric-texture").textContent = `${material.texture_amplitude_mm.toFixed(2)} mm`;
  byId("metric-vibration").textContent = `${material.vibration_hz} Hz`;
  byId("material-summary").textContent = material.capability_note;
}

function updateModelInspector(model) {
  if (!model) {
    return;
  }
  byId("inspector-model-name").textContent = model.title;
  byId("inspector-model-format").textContent = model.format_label ?? model.file_format?.toUpperCase?.() ?? "--";
  byId("inspector-model-category").textContent = model.category;
  byId("inspector-model-source").textContent = model.source_name;
  byId("inspector-scale-hint").textContent = `${model.scale_hint.toFixed(2)}x`;
  byId("stage-model-description").textContent = model.description;
}

function fileFingerprint(file) {
  return `${file.name}:${file.size}:${file.lastModified}`;
}

function bundleFingerprint(mainFilename, files) {
  return Array.from(files ?? [])
    .map((file) => fileFingerprint(file))
    .sort()
    .join("|") + `::${mainFilename ?? ""}`;
}

function supportedMainCandidates(files) {
  return Array.from(files ?? []).filter((file) => {
    try {
      modelFormatFromFilename(file.name);
      return true;
    } catch {
      return false;
    }
  });
}

function updateLocalBundleSummary(message) {
  byId("local-bundle-summary").textContent = message;
}

function resetLocalBundleControls() {
  byId("local-bundle-main-group").hidden = true;
  byId("model-main-file").innerHTML = "";
  updateLocalBundleSummary("No local bundle selected.");
}

function refreshLocalBundleControls() {
  const files = Array.from(byId("model-file").files ?? []);
  if (!files.length) {
    resetLocalBundleControls();
    return [];
  }

  const mainCandidates = supportedMainCandidates(files);
  const mainSelect = byId("model-main-file");
  if (mainCandidates.length > 1) {
    const previousSelection = mainSelect.value;
    populateSelect(mainSelect, mainCandidates, "name", "name");
    if (mainCandidates.some((file) => file.name === previousSelection)) {
      mainSelect.value = previousSelection;
    }
    byId("local-bundle-main-group").hidden = false;
  } else {
    byId("local-bundle-main-group").hidden = true;
    mainSelect.innerHTML = "";
  }

  const sidecarCount = Math.max(0, files.length - mainCandidates.length);
  updateLocalBundleSummary(
    `${files.length} selected file${files.length === 1 ? "" : "s"} / ${mainCandidates.length} supported model candidate${mainCandidates.length === 1 ? "" : "s"} / ${sidecarCount} sidecar resource${sidecarCount === 1 ? "" : "s"}.`,
  );
  return mainCandidates;
}

function selectedLocalBundle() {
  const files = Array.from(byId("model-file").files ?? []);
  if (!files.length) {
    return null;
  }
  const mainCandidates = refreshLocalBundleControls();

  if (!mainCandidates.length) {
    throw new Error("Select one supported main 3D model file together with any required sidecar resources.");
  }

  const selectedMainName =
    mainCandidates.length === 1 ? mainCandidates[0].name : byId("model-main-file").value || mainCandidates[0].name;
  const mainFile = mainCandidates.find((file) => file.name === selectedMainName) ?? mainCandidates[0];
  const sidecarCount = Math.max(0, files.length - 1);

  return {
    mainFile,
    files,
    mainCandidates,
    sidecarCount,
    bundleFileCount: files.length,
  };
}

function formatBytes(byteCount) {
  if (!Number.isFinite(byteCount) || byteCount < 0) {
    return "--";
  }
  if (byteCount < 1024) {
    return `${byteCount} B`;
  }
  const units = ["KB", "MB", "GB"];
  let value = byteCount / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const digits = value >= 100 ? 0 : value >= 10 ? 1 : 2;
  return `${value.toFixed(digits)} ${units[unitIndex]}`;
}

function humanizeResourceMode(resourceMode) {
  if (!resourceMode) {
    return "--";
  }
  return resourceMode.replaceAll("-", " ");
}

function geometrySummary(result) {
  if (!result) {
    return "--";
  }
  const metrics = result.metrics ?? {};
  if (result.file_format === "obj") {
    return `${metrics.vertex_count ?? 0} vertices / ${metrics.face_count ?? 0} faces`;
  }
  if (result.file_format === "stl") {
    return `${metrics.triangle_count ?? 0} triangles / ${metrics.encoding ?? "unknown"} encoding`;
  }
  if (result.file_format === "gltf" || result.file_format === "glb") {
    return `${metrics.mesh_count ?? 0} meshes / ${metrics.node_count ?? 0} nodes / ${metrics.scene_count ?? 0} scenes`;
  }
  return "--";
}

function formatAxisTriplet(values) {
  if (!Array.isArray(values) || values.length < 3) {
    return "--";
  }
  return `X ${Number(values[0]).toFixed(2)} / Y ${Number(values[1]).toFixed(2)} / Z ${Number(values[2]).toFixed(2)}`;
}

function boundsSummary(result) {
  const stagingProfile = result?.staging_profile ?? {};
  if (!stagingProfile.bounds_available) {
    return "Unavailable";
  }
  return formatAxisTriplet(stagingProfile.bounds_size);
}

function stagingSummary(result) {
  const stagingProfile = result?.staging_profile ?? {};
  if (!stagingProfile.bounds_available) {
    return "Default scale";
  }
  return `${stagingProfile.size_band} / ${stagingProfile.recommended_workspace_scale_percent}% / dominant ${String(stagingProfile.dominant_axis ?? "--").toUpperCase()}`;
}

function updateWorkspaceScaleDisplay(value) {
  byId("workspace-scale-value").textContent = `${Number(value)}%`;
}

function applySuggestedWorkspaceScale(result) {
  const stagingProfile = result?.staging_profile ?? {};
  const suggestedScale = Number(stagingProfile.recommended_workspace_scale_percent);
  if (!stagingProfile.bounds_available || !Number.isFinite(suggestedScale)) {
    return false;
  }
  byId("workspace-scale").value = `${suggestedScale}`;
  updateWorkspaceScaleDisplay(suggestedScale);
  return true;
}

function setValidationFindingItems(items, tone = "neutral") {
  const list = byId("validation-findings");
  list.innerHTML = "";
  if (!items.length) {
    return;
  }
  items.forEach((item) => {
    const entry = document.createElement("li");
    entry.className = tone === "danger" ? "compact-list-item compact-list-item-danger" : "compact-list-item";
    entry.textContent = item;
    list.appendChild(entry);
  });
}

function resetValidationPanel(message = "Select a local model to inspect whether it is safe for direct browser staging.") {
  state.localValidation = null;
  state.localValidationFingerprint = null;
  byId("validation-status").textContent = "No local file selected";
  byId("validation-format").textContent = "--";
  byId("validation-size").textContent = "--";
  byId("validation-main-file").textContent = "--";
  byId("validation-bundle").textContent = "--";
  byId("validation-resource-mode").textContent = "--";
  byId("validation-geometry").textContent = "--";
  byId("validation-bounds").textContent = "--";
  byId("validation-staging").textContent = "--";
  byId("validation-summary").textContent = message;
  setValidationFindingItems([]);
}

function setValidationPending(bundleSelection) {
  const file = bundleSelection?.mainFile ?? null;
  const filename = file?.name ?? "selected model";
  let formatLabel = "--";
  try {
    formatLabel = file ? modelFormatLabel(file.name) : "--";
  } catch {
    formatLabel = "--";
  }
  byId("validation-status").textContent = "Validating";
  byId("validation-format").textContent = formatLabel;
  byId("validation-size").textContent = file ? formatBytes(file.size) : "--";
  byId("validation-main-file").textContent = file?.name ?? "--";
  byId("validation-bundle").textContent = bundleSelection ? `${bundleSelection.bundleFileCount} files / ${bundleSelection.sidecarCount} sidecars` : "--";
  byId("validation-resource-mode").textContent = "--";
  byId("validation-geometry").textContent = "--";
  byId("validation-bounds").textContent = "--";
  byId("validation-staging").textContent = "--";
  byId("validation-summary").textContent = `Inspecting ${filename} before direct browser staging.`;
  setValidationFindingItems([]);
}

function setValidationTransportError(message) {
  state.localValidation = null;
  byId("validation-status").textContent = "Validation failed";
  byId("validation-format").textContent = "--";
  byId("validation-main-file").textContent = "--";
  byId("validation-bundle").textContent = "--";
  byId("validation-resource-mode").textContent = "--";
  byId("validation-geometry").textContent = "--";
  byId("validation-bounds").textContent = "--";
  byId("validation-staging").textContent = "--";
  byId("validation-summary").textContent = message;
  setValidationFindingItems([message], "danger");
}

function updateValidationPanel(result, bundleSelection = null) {
  const metrics = result.metrics ?? {};
  const findings = [
    ...(result.blockers ?? []),
    ...(result.warnings ?? []),
  ];
  if (Array.isArray(metrics.resolved_external_resources)) {
    metrics.resolved_external_resources.slice(0, 6).forEach((resourceName) => {
      findings.push(`Resolved bundle resource: ${resourceName}`);
    });
  }
  if (Array.isArray(metrics.missing_external_resources)) {
    metrics.missing_external_resources.slice(0, 6).forEach((resourceName) => {
      findings.push(`Missing bundle resource: ${resourceName}`);
    });
  }
  byId("validation-status").textContent = result.can_stage_locally ? "Ready for staging" : "Blocked";
  byId("validation-format").textContent = result.format_label ?? result.file_format?.toUpperCase?.() ?? "--";
  byId("validation-size").textContent = formatBytes(result.file_size_bytes);
  byId("validation-main-file").textContent = result.filename ?? bundleSelection?.mainFile?.name ?? "--";
  const bundleFileCount = metrics.bundle_file_count ?? bundleSelection?.bundleFileCount ?? 1;
  const sidecarCount = Math.max(0, bundleFileCount - 1);
  byId("validation-bundle").textContent = `${bundleFileCount} files / ${sidecarCount} sidecars`;
  byId("validation-resource-mode").textContent = humanizeResourceMode(result.resource_mode);
  byId("validation-geometry").textContent = geometrySummary(result);
  byId("validation-bounds").textContent = boundsSummary(result);
  byId("validation-staging").textContent = stagingSummary(result);
  byId("validation-summary").textContent = result.summary;
  if (findings.length) {
    const hasBlockers = (result.blockers ?? []).length > 0;
    setValidationFindingItems(findings, hasBlockers ? "danger" : "neutral");
    return;
  }
  setValidationFindingItems(["No blocking issues detected for the current direct browser staging workflow."]);
}

function populateSelect(select, items, valueField, labelField) {
  select.innerHTML = "";
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item[valueField];
    option.textContent = typeof labelField === "function" ? labelField(item) : item[labelField];
    select.appendChild(option);
  });
}

function cloneObjectForScene(template) {
  const clone = template.clone(true);
  clone.traverse((node) => {
    if (!node.isMesh) {
      return;
    }
    if (Array.isArray(node.material)) {
      node.material = node.material.map((material) => material?.clone?.() ?? material);
      return;
    }
    node.material = node.material?.clone?.() ?? node.material;
  });
  return clone;
}

function stampBaseEmissive(root) {
  root.traverse((node) => {
    if (!node.material || Array.isArray(node.material)) {
      return;
    }
    node.userData.baseEmissiveHex = node.material.emissive?.getHex?.() ?? 0x000000;
  });
}

function normalizeLocalObject(object, targetSize = 0.72) {
  const box = new THREE.Box3().setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const maxDimension = Math.max(size.x, size.y, size.z) || 1;
  const scale = targetSize / maxDimension;
  object.scale.multiplyScalar(scale);

  const scaledBox = new THREE.Box3().setFromObject(object);
  const center = scaledBox.getCenter(new THREE.Vector3());
  object.position.sub(center);
  const groundedBox = new THREE.Box3().setFromObject(object);
  object.position.y -= groundedBox.min.y;
  return scale;
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

async function validateLocalUpload(bundleSelection, options = {}) {
  const { announce = true, applySuggestedScale = false } = options;
  const { mainFile, files } = bundleSelection;
  const fingerprint = bundleFingerprint(mainFile.name, files);
  if (state.localValidation && state.localValidationFingerprint === fingerprint) {
    return state.localValidation;
  }

  state.localValidationFingerprint = fingerprint;
  setValidationPending(bundleSelection);

  const formData = new FormData();
  const isBundle = files.length > 1;
  if (isBundle) {
    formData.append("main_filename", mainFile.name);
    files.forEach((file) => {
      formData.append("files", file, file.name);
    });
  } else {
    formData.append("file", mainFile, mainFile.name);
  }

  try {
    const response = await fetch(isBundle ? modelBundleValidationUrl : modelValidationUrl, {
      method: "POST",
      body: formData,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail ?? "The backend validation request failed.");
    }
    state.localValidation = payload;
    updateValidationPanel(payload, bundleSelection);
    const suggestedScaleApplied = applySuggestedScale && payload.can_stage_locally && applySuggestedWorkspaceScale(payload);
    if (announce) {
      setStatus(
        payload.can_stage_locally
          ? `${mainFile.name} passed backend validation and is ready for direct browser staging.${suggestedScaleApplied ? " Suggested workspace scale applied." : ""}`
          : `${mainFile.name} is blocked for direct browser staging. ${payload.blockers?.[0] ?? payload.summary}`,
      );
    }
    return payload;
  } catch (error) {
    state.localValidation = null;
    state.localValidationFingerprint = null;
    const message = error instanceof Error ? error.message : "The backend validation request failed.";
    setValidationTransportError(message);
    if (announce) {
      setStatus(`Local upload validation failed. ${message}`);
    }
    throw error;
  }
}

async function loadDemoObjectTemplate(model) {
  const cached = state.modelTemplateCache.get(model.slug);
  if (cached) {
    return cached;
  }
  const { modelRoot: template } = await loadModelFromUrl(model.file_url, model.file_format);
  state.modelTemplateCache.set(model.slug, template);
  return template;
}

function setSelectedModel(slug, options = {}) {
  const { syncSelect = true, useDefaultMaterial = false } = options;
  const model = modelBySlug(slug);
  if (!model) {
    return null;
  }

  state.currentModel = model;
  if (syncSelect) {
    byId("sample-model").value = model.slug;
  }
  updateModelInspector(model);
  if (useDefaultMaterial || !state.currentMaterial) {
    selectMaterial(model.default_material, {
      syncSelect: true,
      reapplyCurrentObject: false,
      announce: false,
    });
  }
  return model;
}

function selectMaterial(slug, options = {}) {
  const {
    syncSelect = true,
    reapplyCurrentObject = true,
    announce = true,
  } = options;
  const material = materialBySlug(slug);
  if (!material) {
    return null;
  }
  state.currentMaterial = material;
  if (syncSelect) {
    byId("material-select").value = material.slug;
  }
  updateMaterialPanel(material);
  if (reapplyCurrentObject && state.currentObject) {
    applyMaterialToObject(state.currentObject, material);
    stampBaseEmissive(state.currentObject);
  }
  if (announce) {
    setStatus(`Applied ${material.title}.`);
  }
  return material;
}

function cycleMaterial(delta) {
  const currentIndex = state.materials.findIndex((material) => material.slug === state.currentMaterial?.slug);
  const nextIndex = (currentIndex + delta + state.materials.length) % state.materials.length;
  const nextMaterial = state.materials[nextIndex];
  selectMaterial(nextMaterial.slug, { syncSelect: true, reapplyCurrentObject: true, announce: false });
  setStatus(`Applied ${nextMaterial.title} in the active exploration scene.`);
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
      emissive: 0x071019,
    }),
  );
  base.position.y = 0.06;
  base.userData.baseEmissiveHex = 0x071019;
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
  topPlate.userData.baseEmissiveHex = topPlate.material.emissive.getHex();
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
  guideRing.userData.baseEmissiveHex = 0x0e2b29;
  group.add(guideRing);

  return group;
}

function buildSceneDeck(width, depth, accentHex = 0x1b2940) {
  const group = new THREE.Group();

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.12, depth),
    new THREE.MeshStandardMaterial({
      color: 0x16213a,
      roughness: 0.88,
      metalness: 0.05,
      emissive: 0x08111b,
    }),
  );
  base.position.y = 0.06;
  base.userData.baseEmissiveHex = 0x08111b;
  group.add(base);

  const frontRail = new THREE.Mesh(
    new THREE.BoxGeometry(width - 0.22, 0.05, 0.08),
    new THREE.MeshStandardMaterial({
      color: 0x111827,
      roughness: 0.85,
      metalness: 0.06,
      emissive: 0x06101a,
    }),
  );
  frontRail.position.set(0, 0.09, depth / 2 - 0.14);
  frontRail.userData.baseEmissiveHex = 0x06101a;
  group.add(frontRail);

  const backRail = frontRail.clone();
  backRail.position.z = -depth / 2 + 0.14;
  group.add(backRail);

  const accentRail = new THREE.Mesh(
    new THREE.BoxGeometry(width - 0.38, 0.035, 0.06),
    new THREE.MeshStandardMaterial({
      color: accentHex,
      roughness: 0.48,
      metalness: 0.08,
      emissive: 0x0d1726,
    }),
  );
  accentRail.position.set(0, 0.125, -depth / 2 + 0.24);
  accentRail.userData.baseEmissiveHex = 0x0d1726;
  group.add(accentRail);

  return group;
}

function buildSceneBridge(title, subtitle, zPosition, width = 2.7) {
  const bridge = new THREE.Group();

  const pillarLeft = new THREE.Mesh(
    new THREE.BoxGeometry(0.06, 0.28, 0.06),
    new THREE.MeshStandardMaterial({ color: 0x0f1724, roughness: 0.9, metalness: 0.05, emissive: 0x06101a }),
  );
  pillarLeft.position.set(-width / 2 + 0.22, 0.16, zPosition);
  pillarLeft.userData.baseEmissiveHex = 0x06101a;
  bridge.add(pillarLeft);

  const pillarRight = pillarLeft.clone();
  pillarRight.position.x = width / 2 - 0.22;
  bridge.add(pillarRight);

  const header = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.05, 0.09),
    new THREE.MeshStandardMaterial({
      color: 0x1a2940,
      roughness: 0.76,
      metalness: 0.08,
      emissive: 0x0a1420,
    }),
  );
  header.position.set(0, 0.29, zPosition);
  header.userData.baseEmissiveHex = 0x0a1420;
  bridge.add(header);

  const titleSprite = createLabelSprite(title, {
    background: "rgba(13,17,23,0.84)",
    fontSize: 19,
  });
  titleSprite.position.set(0, 0.38, zPosition);
  bridge.add(titleSprite);

  if (subtitle) {
    const subtitleSprite = createLabelSprite(subtitle, {
      background: "rgba(13,17,23,0.72)",
      fontSize: 15,
      color: "#c7d2df",
    });
    subtitleSprite.position.set(0, 0.26, zPosition + 0.01);
    bridge.add(subtitleSprite);
  }

  return bridge;
}

function createLauncherHubGroup(position) {
  const group = new THREE.Group();
  group.position.copy(position.clone().setY(0.12));

  const base = new THREE.Mesh(
    new THREE.CylinderGeometry(0.26, 0.3, 0.08, 28),
    new THREE.MeshStandardMaterial({
      color: 0x152132,
      roughness: 0.82,
      metalness: 0.08,
      emissive: 0x09111b,
    }),
  );
  base.position.y = 0.04;
  base.userData.baseEmissiveHex = 0x09111b;
  group.add(base);

  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(0.22, 0.035, 14, 48),
    new THREE.MeshStandardMaterial({
      color: 0x79c0ff,
      roughness: 0.34,
      metalness: 0.1,
      emissive: 0x163f63,
    }),
  );
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.11;
  ring.userData.baseEmissiveHex = 0x163f63;
  group.add(ring);

  const label = createLabelSprite("Launcher", {
    background: "rgba(13,17,23,0.78)",
    fontSize: 17,
  });
  label.position.set(0, 0.38, 0);
  group.add(label);

  return {
    group,
    target: {
      id: "launcher-hub",
      title: "Launcher hub",
      type: "launcher-hub",
      actionLabel: "Orientation marker for the object session launcher.",
      position: position.clone().setY(0.24),
      radius: 0.34,
      disabled: true,
      hoverHex: 0x1f6feb,
      action: null,
    },
  };
}

function buildControlMesh(kind, accentHex = 0x79c0ff) {
  const group = new THREE.Group();

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(0.46, 0.07, 0.28),
    new THREE.MeshStandardMaterial({
      color: 0x1a1f28,
      roughness: 0.82,
      metalness: 0.08,
      emissive: 0x0b1118,
    }),
  );
  base.position.y = 0.035;
  base.userData.baseEmissiveHex = 0x0b1118;
  group.add(base);

  const accentMaterial = new THREE.MeshStandardMaterial({
    color: accentHex,
    roughness: 0.34,
    metalness: 0.08,
    emissive: 0x14263d,
  });

  if (kind === "previous") {
    [-0.11, 0, 0.11].forEach((offset) => {
      const ridge = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.18, 18), accentMaterial.clone());
      ridge.rotation.z = Math.PI / 2;
      ridge.position.set(offset, 0.11, 0);
      ridge.userData.baseEmissiveHex = 0x14263d;
      group.add(ridge);
    });
  } else if (kind === "next") {
    const dome = new THREE.Mesh(new THREE.SphereGeometry(0.08, 20, 16), accentMaterial.clone());
    dome.scale.set(1, 0.74, 1);
    dome.position.set(-0.05, 0.1, 0);
    dome.userData.baseEmissiveHex = 0x14263d;
    group.add(dome);

    const arrow = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.14, 3), accentMaterial.clone());
    arrow.rotation.z = -Math.PI / 2;
    arrow.position.set(0.13, 0.1, 0);
    arrow.userData.baseEmissiveHex = 0x14263d;
    group.add(arrow);
  } else if (kind === "launcher") {
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.12, 0.16), accentMaterial.clone());
    body.position.set(0, 0.11, 0);
    body.userData.baseEmissiveHex = 0x14263d;
    group.add(body);

    const roof = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.12, 4), accentMaterial.clone());
    roof.rotation.y = Math.PI / 4;
    roof.position.set(0, 0.2, 0);
    roof.userData.baseEmissiveHex = 0x14263d;
    group.add(roof);
  } else if (kind === "material-prev") {
    [-0.08, 0.08].forEach((offset) => {
      const slab = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.06, 0.16), accentMaterial.clone());
      slab.position.set(offset, 0.1, 0);
      slab.userData.baseEmissiveHex = 0x14263d;
      group.add(slab);
    });
  } else if (kind === "material-next") {
    [0.06, 0.11, 0.16].forEach((height, index) => {
      const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.09 - index * 0.018, 0.09 - index * 0.018, 0.03, 18), accentMaterial.clone());
      disc.position.set(0, height, 0);
      disc.userData.baseEmissiveHex = 0x14263d;
      group.add(disc);
    });
  }

  return group;
}

function createControlGroup({
  id,
  title,
  type,
  label,
  kind,
  position,
  actionLabel,
  accentHex = 0x79c0ff,
  action,
  disabled = false,
}) {
  const group = buildControlMesh(kind, accentHex);
  group.position.copy(position.clone().setY(0.12));

  const labelSprite = createLabelSprite(label, {
    background: "rgba(13,17,23,0.82)",
    fontSize: 16,
  });
  labelSprite.position.set(0, 0.38, 0);
  group.add(labelSprite);

  return {
    group,
    target: {
      id,
      title,
      type,
      actionLabel,
      position: position.clone().setY(0.24),
      radius: 0.32,
      disabled,
      hoverHex: 0x1f6feb,
      action,
    },
  };
}

async function createLauncherItemGroup(model, position) {
  const group = new THREE.Group();
  group.position.copy(position.clone().setY(0.12));
  const defaultMaterial = materialBySlug(model.default_material);

  const pedestal = new THREE.Mesh(
    new THREE.CylinderGeometry(0.42, 0.5, 0.12, 26),
    new THREE.MeshStandardMaterial({
      color: 0x0f1724,
      roughness: 0.9,
      metalness: 0.05,
      emissive: 0x071019,
    }),
  );
  pedestal.position.y = 0.06;
  pedestal.userData.baseEmissiveHex = 0x071019;
  group.add(pedestal);

  const topPlate = new THREE.Mesh(
    new THREE.CylinderGeometry(0.34, 0.36, 0.04, 26),
    new THREE.MeshStandardMaterial({
      color: defaultMaterial ? new THREE.Color(defaultMaterial.visual_color).multiplyScalar(0.7) : 0x27415e,
      roughness: 0.62,
      metalness: 0.08,
      emissive: 0x102134,
    }),
  );
  topPlate.position.y = 0.145;
  topPlate.userData.baseEmissiveHex = 0x102134;
  group.add(topPlate);

  const previewTemplate = await loadDemoObjectTemplate(model);
  const previewObject = cloneObjectForScene(previewTemplate);
  if (defaultMaterial) {
    applyMaterialToObject(previewObject, defaultMaterial);
  }
  normalizeLocalObject(previewObject, 0.72 * Math.max(0.8, Math.min(model.scale_hint, 1.25)));
  previewObject.position.y += 0.18;
  stampBaseEmissive(previewObject);
  group.add(previewObject);

  const titleSprite = createLabelSprite(model.title, {
    background: "rgba(13,17,23,0.82)",
    fontSize: 17,
  });
  titleSprite.position.set(0, 0.78, 0);
  group.add(titleSprite);

  const metaSprite = createLabelSprite(model.category.replaceAll("_", " "), {
    background: "rgba(13,17,23,0.68)",
    fontSize: 14,
    color: "#b6c2cf",
  });
  metaSprite.position.set(0, 0.63, 0);
  group.add(metaSprite);

  return {
    group,
    target: {
      id: `launcher-model-${model.slug}`,
      title: model.title,
      type: "launcher-model",
      actionLabel: "Open this demo model in the object exploration scene.",
      position: position.clone().setY(0.28),
      radius: 0.46,
      disabled: false,
      hoverHex: 0x1f6feb,
      action: async () => {
        await openDemoSession(state.sceneApi, model, { originPage: launcherPageForModel(model.slug) });
      },
    },
  };
}

function clearInteractiveState() {
  state.interactiveGroups.clear();
  state.targetById.clear();
  state.hoveredTargetId = null;
}

function registerInteractiveTarget(group, target) {
  group.userData.basePosition = group.position.clone();
  state.interactiveGroups.set(target.id, group);
  state.targetById.set(target.id, target);
  state.sceneApi.world.add(group);
}

function refreshInteractiveVisuals() {
  state.interactiveGroups.forEach((group, targetId) => {
    const target = state.targetById.get(targetId);
    if (!target) {
      return;
    }
    const isHovered = targetId === state.hoveredTargetId;
    const basePosition = group.userData.basePosition;
    group.position.set(basePosition.x, basePosition.y + (isHovered ? 0.035 : 0), basePosition.z);
    group.scale.setScalar(target.disabled ? 0.96 : isHovered ? 1.05 : 1);
    group.traverse((node) => {
      if (!node.material || Array.isArray(node.material)) {
        return;
      }
      if (node.material.emissive) {
        node.material.emissive.setHex(isHovered && !target.disabled ? target.hoverHex ?? 0x1f6feb : node.userData.baseEmissiveHex ?? 0x000000);
      }
    });
  });
}

function nearestInteractiveTarget(position) {
  let nearestTarget = null;
  let nearestDistance = Number.POSITIVE_INFINITY;

  state.targetById.forEach((target) => {
    const distance = target.position.distanceTo(position);
    if (distance <= target.radius && distance < nearestDistance) {
      nearestTarget = target;
      nearestDistance = distance;
    }
  });

  return nearestTarget;
}

function updatePointerFeedback(sceneApi, position) {
  const nearestTarget = nearestInteractiveTarget(position);
  const nextHoveredId = nearestTarget?.id ?? null;
  if (state.hoveredTargetId !== nextHoveredId) {
    state.hoveredTargetId = nextHoveredId;
    refreshInteractiveVisuals();
  }

  if (nearestTarget) {
    byId("explorer-stage-pill").textContent = nearestTarget.type.startsWith("launcher") ? "Session target" : "Scene control";
    sceneApi.setPointerState("focus");
    setStatus(`${nearestTarget.title}. ${nearestTarget.actionLabel}`);
    return;
  }

  if (state.sceneMode === "exploration" && state.currentBounds) {
    const distance = state.currentBounds.distanceToPoint(position);
    if (distance < 0.04) {
      byId("explorer-stage-pill").textContent = "Pointer near surface";
      sceneApi.setPointerState("focus");
      setStatus("Pointer near the staged object surface.");
      return;
    }
    byId("explorer-stage-pill").textContent = "Pointer in workspace";
    sceneApi.setPointerState("idle");
    setStatus("Pointer moving inside the object exploration workspace.");
    return;
  }

  byId("explorer-stage-pill").textContent = "Launcher ready";
  sceneApi.setPointerState("idle");
  setStatus("Pointer moving across the object session launcher.");
}

function activatePointer(sceneApi) {
  const target = state.targetById.get(state.hoveredTargetId);
  if (target) {
    if (target.disabled || !target.action) {
      setStatus(`${target.title} is an orientation marker, not an activatable control.`);
      return;
    }
    sceneApi.setPointerState("active");
    Promise.resolve(target.action()).catch(() => {
      setStatus(`Activation failed for ${target.title}.`);
    });
    window.setTimeout(() => updatePointerFeedback(sceneApi, state.pointerController.position), 180);
    return;
  }

  if (!state.currentBounds) {
    setStatus("No object is staged yet. Use the launcher or the outer controls to open a session.");
    return;
  }

  const distance = state.currentBounds.distanceToPoint(state.pointerController.position);
  if (distance < 0.12) {
    setStatus("Pointer activation registered on the staged model surface.");
    sceneApi.setPointerState("active");
    window.setTimeout(() => updatePointerFeedback(sceneApi, state.pointerController.position), 180);
    return;
  }

  setStatus("Pointer activation is outside the current object envelope.");
}

async function activateDebugTarget(targetId) {
  const target = state.targetById.get(targetId);
  if (!target || target.disabled || !target.action) {
    return false;
  }
  state.hoveredTargetId = targetId;
  refreshInteractiveVisuals();
  await Promise.resolve(target.action());
  return true;
}

async function renderLauncher(sceneApi, page = state.launcherPage) {
  const pageSlice = launcherPageSlice(page);
  const renderGeneration = ++state.renderGeneration;
  state.launcherPage = pageSlice.page;
  state.currentObject = null;
  state.currentBounds = null;
  setSceneMode("launcher");
  updateLauncherPageIndicator(pageSlice.page);

  sceneApi.clearWorld();
  clearInteractiveState();
  sceneApi.setBoundarySize(new THREE.Vector3(6.8, 1.15, 4.8));
  sceneApi.applySceneView(LAUNCHER_VIEW_STATE.position, LAUNCHER_VIEW_STATE.target, {
    preserveUserView: true,
  });
  sceneApi.world.add(buildSceneDeck(6.2, 4.1, 0x1f3855));
  sceneApi.world.add(buildSceneBridge("Object Session Launcher", `Page ${pageSlice.page + 1} / ${pageSlice.pageCount}`, -1.42, 3.3));

  const hub = createLauncherHubGroup(new THREE.Vector3(0, 0, 1.05));
  registerInteractiveTarget(hub.group, hub.target);

  if (pageSlice.page > 0) {
    const previousControl = createControlGroup({
      id: "launcher-prev-page",
      title: "Previous page",
      type: "launcher-control",
      label: "Previous",
      kind: "previous",
      position: new THREE.Vector3(-2.2, 0, 1.02),
      actionLabel: "Return to the previous page of demo model sessions.",
      accentHex: 0x7ee787,
      action: async () => renderLauncher(sceneApi, pageSlice.page - 1),
    });
    registerInteractiveTarget(previousControl.group, previousControl.target);
  }

  if (pageSlice.page < pageSlice.pageCount - 1) {
    const nextControl = createControlGroup({
      id: "launcher-next-page",
      title: "Next page",
      type: "launcher-control",
      label: "Next",
      kind: "next",
      position: new THREE.Vector3(2.2, 0, 1.02),
      actionLabel: "Advance to the next page of demo model sessions.",
      accentHex: 0x58a6ff,
      action: async () => renderLauncher(sceneApi, pageSlice.page + 1),
    });
    registerInteractiveTarget(nextControl.group, nextControl.target);
  }

  const positions = [
    new THREE.Vector3(-1.75, 0, -0.1),
    new THREE.Vector3(0, 0, -0.1),
    new THREE.Vector3(1.75, 0, -0.1),
  ];
  const launcherEntries = await Promise.all(
    pageSlice.models.map((model, index) => createLauncherItemGroup(model, positions[index])),
  );
  if (renderGeneration !== state.renderGeneration) {
    return;
  }
  launcherEntries.forEach(({ group, target }) => registerInteractiveTarget(group, target));

  const selectedOnPage = pageSlice.models.find((model) => model.slug === state.currentModel?.slug);
  if (!selectedOnPage && pageSlice.models[0]) {
    setSelectedModel(pageSlice.models[0].slug, { syncSelect: true, useDefaultMaterial: true });
  }

  const defaultTargetId = selectedOnPage ? `launcher-model-${selectedOnPage.slug}` : "launcher-hub";
  const defaultTarget = state.targetById.get(defaultTargetId);
  state.pointerController?.setBounds(
    new THREE.Vector3(-3.0, 0.14, -1.5),
    new THREE.Vector3(3.0, 0.42, 1.35),
  );
  state.pointerController?.setPosition(defaultTarget?.position?.clone() ?? new THREE.Vector3(0, 0.24, 1.05));
  updatePointerFeedback(sceneApi, state.pointerController.position);
  setStatus("Object session launcher ready. Activate a model preview to stage it in the exploration world.");
}

async function loadObjectIntoScene(sceneApi, object, model, statusMessage) {
  const scaleFactor = Number(byId("workspace-scale").value) / 100;
  const pageLabel = `Launcher page ${state.launcherPage + 1} / ${launcherPageCount()}`;

  setSceneMode("exploration");
  updateLauncherPageIndicator(state.launcherPage);
  sceneApi.clearWorld();
  clearInteractiveState();
  sceneApi.world.add(buildSceneDeck(5.6, 4.2, 0x20324a));
  sceneApi.world.add(buildSceneBridge(model.title, pageLabel, -1.48, 2.9));
  sceneApi.world.add(buildExplorationPlinth(state.currentMaterial));

  applyMaterialToObject(object, state.currentMaterial);
  object.userData.rotateOnIdle = true;
  stampBaseEmissive(object);
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
      Math.max(4.2, objectSize.x + 2.1),
      Math.max(2.3, objectSize.y + 1.0),
      Math.max(4.2, objectSize.z + 2.1),
    ),
  );

  const launcherControl = createControlGroup({
    id: "exploration-launcher",
    title: "Launcher",
    type: "exploration-control",
    label: "Launcher",
    kind: "launcher",
    position: new THREE.Vector3(-1.65, 0, 1.18),
    actionLabel: "Return to the object session launcher on the current page.",
    accentHex: 0xf2cc60,
    action: async () => renderLauncher(sceneApi, state.launcherPage),
  });
  registerInteractiveTarget(launcherControl.group, launcherControl.target);

  const previousMaterial = createControlGroup({
    id: "exploration-material-prev",
    title: "Previous material",
    type: "exploration-control",
    label: "Material -",
    kind: "material-prev",
    position: new THREE.Vector3(0, 0, 1.18),
    actionLabel: "Cycle to the previous tactile material profile.",
    accentHex: 0x7ee787,
    action: async () => {
      cycleMaterial(-1);
    },
  });
  registerInteractiveTarget(previousMaterial.group, previousMaterial.target);

  const nextMaterial = createControlGroup({
    id: "exploration-material-next",
    title: "Next material",
    type: "exploration-control",
    label: "Material +",
    kind: "material-next",
    position: new THREE.Vector3(1.65, 0, 1.18),
    actionLabel: "Cycle to the next tactile material profile.",
    accentHex: 0x58a6ff,
    action: async () => {
      cycleMaterial(1);
    },
  });
  registerInteractiveTarget(nextMaterial.group, nextMaterial.target);

  state.pointerController?.setBounds(
    new THREE.Vector3(objectCenter.x - objectSize.x * 0.8, 0.14, objectCenter.z - objectSize.z * 0.82),
    new THREE.Vector3(objectCenter.x + objectSize.x * 0.8, Math.max(1.45, objectSize.y + 0.82), objectCenter.z + objectSize.z * 0.82),
  );
  state.pointerController?.setPosition(
    objectCenter.clone().add(new THREE.Vector3(objectSize.x * 0.35, Math.min(objectSize.y + 0.38, 1.26), objectSize.z * 0.35)),
  );

  updateModelInspector(model);
  updatePointerFeedback(sceneApi, state.pointerController.position);
  setStatus(statusMessage);
}

async function openDemoSession(sceneApi, model, options = {}) {
  const { originPage = launcherPageForModel(model.slug) } = options;
  state.launcherPage = originPage;
  setSelectedModel(model.slug, { syncSelect: true, useDefaultMaterial: true });
  const renderGeneration = ++state.renderGeneration;
  setStatus(`Loading ${model.title} into the exploration scene...`);
  const template = await loadDemoObjectTemplate(model);
  if (renderGeneration !== state.renderGeneration) {
    return;
  }
  const object = cloneObjectForScene(template);
  await loadObjectIntoScene(sceneApi, object, model, `Loaded ${model.title} into the bounded scene.`);
}

async function openLocalUploadSession(sceneApi, bundleSelection, validation) {
  const { mainFile, files } = bundleSelection;
  const baseModel = modelBySlug(byId("sample-model").value) ?? state.models[0];
  const loader = files.length > 1 ? loadLocalModelBundle : loadLocalModelFile;
  const { modelRoot: object, format, formatLabel } = await loader(mainFile, files);
  const validationSummary = validation?.summary ?? `Local ${formatLabel} file validated for direct browser staging.`;
  const resourceMode = humanizeResourceMode(validation?.resource_mode ?? "single-file");
  const normalizationHint = validation?.staging_profile?.normalization_hint ?? "Manual workspace scale may still be required after staging.";
  const scaleSuggestion = validation?.staging_profile?.recommended_workspace_scale_percent;
  const localModel = {
    ...baseModel,
    slug: "local_model_session",
    title: mainFile.name,
    category: "local_model",
    file_format: format,
    format_label: formatLabel,
    source_name: files.length > 1 ? `Local ${formatLabel} bundle` : `Local ${formatLabel} upload`,
    description: `${validationSummary} Resource mode: ${resourceMode}. ${normalizationHint}${Number.isFinite(scaleSuggestion) ? ` Suggested workspace scale: ${scaleSuggestion}%.` : ""}${files.length > 1 ? ` Bundle files: ${files.length}.` : ""}`,
    scale_hint: 1.0,
  };
  setSelectedModel(baseModel.slug, { syncSelect: true, useDefaultMaterial: false });
  setStatus(`Loading local ${formatLabel} ${mainFile.name} into the exploration scene...`);
  await loadObjectIntoScene(
    sceneApi,
    object,
    localModel,
    `Loaded local ${formatLabel} ${mainFile.name} into the bounded scene.`,
  );
}

async function loadSelectedModel(sceneApi) {
  const bundleSelection = selectedLocalBundle();
  if (bundleSelection) {
    const validation = await validateLocalUpload(bundleSelection, { announce: false });
    if (!validation.can_stage_locally) {
      setStatus(validation.blockers?.[0] ?? validation.summary);
      return;
    }
    await openLocalUploadSession(sceneApi, bundleSelection, validation);
    return;
  }
  const model = modelBySlug(byId("sample-model").value);
  await openDemoSession(sceneApi, model, { originPage: launcherPageForModel(model.slug) });
}

async function stabilizeObjectExplorerForCapture() {
  state.sceneApi.clearPersistedViewState();
  state.sceneApi.setDampingEnabled(false);
  state.sceneApi.setIdleAnimationEnabled(false);
  state.sceneApi.resetIdleAnimatedObjects();
  await renderLauncher(state.sceneApi, 0);
  state.sceneApi.setViewState(LAUNCHER_VIEW_STATE, { persist: false });
  state.sceneApi.setPointerVisible(false);
  state.pointerController?.setPosition(new THREE.Vector3(0, 0.18, 1.48));
  state.hoveredTargetId = null;
  state.sceneApi.setPointerState("idle");
  byId("explorer-stage-pill").textContent = "Launcher ready";
  refreshInteractiveVisuals();
  state.sceneApi.renderNow();
  return true;
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
    node.material = new THREE.MeshStandardMaterial({
      color,
      roughness: material.visual_roughness,
      metalness: material.visual_metalness,
      emissive: color.clone().multiplyScalar(0.06),
    });
    node.castShadow = false;
    node.receiveShadow = true;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bootWorkspace(
    {
      title: "3D Object Explorer startup failed",
      stageSelector: "#object-canvas",
      runtimePillId: "explorer-stage-pill",
      runtimePillText: "Runtime error",
      pageStatusId: "explorer-page-status",
      pageStatusText: "Boot failed",
      stageStatusId: "object-stage-status",
      summaryIds: ["material-summary", "stage-model-description"],
    },
    async (shell) => {
      const sceneApi = createWorkspaceScene(byId("object-canvas"), {
        cameraPosition: LAUNCHER_VIEW_STATE.position,
        target: LAUNCHER_VIEW_STATE.target,
        debugKey: "object-explorer",
      });

      state.sceneApi = sceneApi;
      state.pointerController = attachPointerEmulation(sceneApi, {
        initialPosition: new THREE.Vector3(0, 0.24, 1.05),
        boundsMin: new THREE.Vector3(-3.0, 0.14, -1.5),
        boundsMax: new THREE.Vector3(3.0, 0.42, 1.35),
        speed: 1.55,
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
      populateSelect(byId("sample-model"), state.models, "slug", (model) => `${model.title} (${model.format_label})`);
      byId("model-file").setAttribute("accept", modelFileAcceptString());
      resetLocalBundleControls();
      resetValidationPanel();

      const initialModel = state.models[0];
      setSelectedModel(initialModel.slug, { syncSelect: true, useDefaultMaterial: true });

      byId("explorer-stage-pill").textContent =
        shell.health.haptics.mode === "available" ? "Haptic ready" : "Pointer emulator";

      byId("load-selection").addEventListener("click", () => {
        loadSelectedModel(sceneApi).catch(() => {
          setStatus("Model loading failed.");
        });
      });

      byId("model-file").addEventListener("change", () => {
        let bundleSelection = null;
        try {
          bundleSelection = selectedLocalBundle();
        } catch (error) {
          resetValidationPanel();
          setStatus(error instanceof Error ? error.message : "Local bundle selection is invalid.");
          return;
        }
        if (!bundleSelection) {
          resetValidationPanel();
          setStatus("Local upload cleared. Select a bundled demo or choose another local file.");
          return;
        }
        validateLocalUpload(bundleSelection, { applySuggestedScale: true }).catch(() => {});
      });

      byId("model-main-file").addEventListener("change", () => {
        let bundleSelection = null;
        try {
          bundleSelection = selectedLocalBundle();
        } catch (error) {
          resetValidationPanel();
          setStatus(error instanceof Error ? error.message : "Local bundle selection is invalid.");
          return;
        }
        if (!bundleSelection) {
          resetValidationPanel();
          return;
        }
        setStatus(`Selected ${bundleSelection.mainFile.name} as the main model file for the current local bundle.`);
        validateLocalUpload(bundleSelection, { applySuggestedScale: true }).catch(() => {});
      });

      byId("clear-local-bundle").addEventListener("click", () => {
        byId("model-file").value = "";
        resetLocalBundleControls();
        resetValidationPanel();
        setStatus("Local bundle cleared. Select a bundled demo or choose another local file set.");
      });

      byId("reset-camera").addEventListener("click", () => {
        sceneApi.resetCamera();
        setStatus("Camera reset to the canonical view for this route.");
      });

      byId("sample-model").addEventListener("change", () => {
        const model = setSelectedModel(byId("sample-model").value, {
          syncSelect: false,
          useDefaultMaterial: true,
        });
        if (!model) {
          return;
        }
        state.launcherPage = launcherPageForModel(model.slug);
        updateLauncherPageIndicator(state.launcherPage);
        if (state.sceneMode === "launcher") {
          renderLauncher(sceneApi, state.launcherPage).catch(() => {
            setStatus("Unable to refresh the object session launcher.");
          });
        } else {
          setStatus(`Selected ${model.title}. Load the selection to start a new session.`);
        }
      });

      byId("material-select").addEventListener("change", () => {
        selectMaterial(byId("material-select").value, { syncSelect: false, reapplyCurrentObject: true, announce: false });
        setStatus(`Applied ${state.currentMaterial.title}.`);
      });

      byId("workspace-scale").addEventListener("input", () => {
        const value = Number(byId("workspace-scale").value);
        updateWorkspaceScaleDisplay(value);
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

      window.__feelitObjectExplorerDebug = {
        getSceneMode: () => state.sceneMode,
        getLauncherPage: () => state.launcherPage,
        getCurrentModelSlug: () => state.currentModel?.slug ?? null,
        targetIds: () => Array.from(state.targetById.keys()),
        targets: () =>
          Array.from(state.targetById.values()).map((target) => ({
            id: target.id,
            title: target.title,
            type: target.type,
            actionLabel: target.actionLabel,
            disabled: target.disabled,
          })),
        activateTarget: async (targetId) => activateDebugTarget(targetId),
        navigateToLauncher: async (page = state.launcherPage) => renderLauncher(sceneApi, page),
        stabilizeForCapture: async () => stabilizeObjectExplorerForCapture(),
      };

      await renderLauncher(sceneApi, 0);
      updatePointerFeedback(sceneApi, state.pointerController.position);
    },
  );
});
