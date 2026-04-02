import { bootWorkspace } from "./app.js";
import { loadModelFromUrl, modelFormatLabel } from "./model_loading.js";
import {
  THREE,
  attachPointerEmulation,
  createLabelSprite,
  createWorkspaceScene,
} from "./three_scene_common.js";

const workspaceCatalogUrl = "/api/haptic-workspaces";
const workspaceDetailUrl = (slug) => `/api/haptic-workspaces/${encodeURIComponent(slug)}`;
const workspaceBrowseUrl = (slug, path = "", page = 0, pageSize = FILE_BROWSER_PAGE_SIZE) =>
  `/api/haptic-workspaces/${encodeURIComponent(slug)}/browse?path=${encodeURIComponent(path)}&page=${page}&page_size=${pageSize}`;
const workspaceTextUrl = (slug, path, offset, maxChars) =>
  `/api/haptic-workspaces/${encodeURIComponent(slug)}/text-file?path=${encodeURIComponent(path)}&offset=${offset}&max_chars=${maxChars}`;
const workspaceRawUrl = (slug, path) =>
  `/api/haptic-workspaces/${encodeURIComponent(slug)}/raw-file?path=${encodeURIComponent(path)}`;
const braillePreviewUrl = "/api/braille/preview";

const GALLERY_PAGE_SIZE = 3;
const FILE_BROWSER_PAGE_SIZE = 6;
const TEXT_COLUMNS = 8;
const TEXT_ROWS_PER_PAGE = 4;
const DETAIL_BRAILLE_COLUMNS = 10;
const SEEK_SECONDS = 10;

const CATEGORY_META = {
  models: {
    title: "Models Gallery",
    sceneCode: "models-gallery",
    color: 0x58a6ff,
    description: "Curated 3D models prepared for bounded tactile exploration.",
  },
  texts: {
    title: "Text Library",
    sceneCode: "texts-gallery",
    color: 0x7ee787,
    description: "Curated text and book assets prepared for tactile Braille reading scenes.",
  },
  audio: {
    title: "Audio Library",
    sceneCode: "audio-gallery",
    color: 0xf2cc60,
    description: "Curated audio material with tactile transport controls and spoken naming support.",
  },
};

const FILE_KIND_META = {
  directory: { title: "Folder", color: 0x58a6ff, actionLabel: "Open folder in the workspace file browser" },
  model: { title: "3D Model", color: 0x58a6ff, actionLabel: "Open in the 3D model scene" },
  text: { title: "Text", color: 0x7ee787, actionLabel: "Open in the Braille reading scene" },
  audio: { title: "Audio", color: 0xf2cc60, actionLabel: "Open in the audio transport scene" },
  unsupported: {
    title: "Unsupported file",
    color: 0xff7b72,
    actionLabel: "Inspect unsupported file details",
  },
};

const state = {
  workspaceCatalog: [],
  activeWorkspace: null,
  currentScene: null,
  targets: new Map(),
  focusOrder: [],
  focusedTargetId: null,
  hoveredTargetId: null,
  fallbackFocusIndex: -1,
  pointerController: null,
  sceneApi: null,
  speechEnabled: true,
  lastStatusKey: "",
  lastAnnouncementKey: "",
  brailleCache: new Map(),
  textScene: null,
  audioScene: null,
  sceneBuildToken: 0,
};

function byId(id) {
  return document.getElementById(id);
}

function audioPlayer() {
  return byId("desktop-audio-player");
}

function fetchJson(url, options = {}) {
  return fetch(url, options).then(async (response) => {
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || `Request failed: ${url}`);
    }
    return response.json();
  });
}

function setRuntimePill(text, className = "status-pill-green") {
  const pill = byId("desktop-runtime-pill");
  pill.textContent = text;
  pill.classList.remove(
    "status-pill-cyan",
    "status-pill-green",
    "status-pill-purple",
    "status-pill-danger",
  );
  pill.classList.add(className);
}

function setStatus(message, shortLabel = "Ready") {
  byId("desktop-status-bar").textContent = message;
  byId("desktop-page-status").textContent = shortLabel;
}

function speak(text) {
  if (!state.speechEnabled || !("speechSynthesis" in window) || !text) {
    return;
  }
  try {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;
    window.speechSynthesis.speak(utterance);
  } catch (error) {
    console.warn("Speech synthesis is unavailable.", error);
  }
}

function announce(message, key = message, options = {}) {
  const { speakMessage = true } = options;
  if (state.lastAnnouncementKey === key) {
    return;
  }
  state.lastAnnouncementKey = key;
  byId("desktop-announcement").textContent = message;
  if (speakMessage) {
    speak(message);
  }
}

function publishStatus(message, shortLabel = "Ready", key = message, options = {}) {
  if (state.lastStatusKey !== key) {
    state.lastStatusKey = key;
    setStatus(message, shortLabel);
  }
  announce(message, key, options);
}

function updateFocusedInspector(target) {
  if (!target) {
    byId("desktop-focus-label").textContent = "--";
    byId("desktop-focus-type").textContent = "--";
    byId("desktop-focus-action").textContent = "--";
    return;
  }
  byId("desktop-focus-label").textContent = target.title;
  byId("desktop-focus-type").textContent = target.type;
  byId("desktop-focus-action").textContent = target.actionLabel;
}

function updateWorkspaceSummary() {
  const workspace = state.activeWorkspace;
  if (!workspace) {
    byId("desktop-workspace-title").textContent = "No workspace";
    byId("desktop-workspace-chip").textContent = "--";
    return;
  }
  byId("desktop-workspace-title").textContent = workspace.title;
  byId("desktop-workspace-chip").textContent = workspace.slug;
}

function renderSceneTrail(scene = null) {
  const activeScene = scene ?? state.currentScene;
  const container = byId("desktop-scene-trail");
  const summary = byId("desktop-scene-trail-summary");
  container.innerHTML = "";

  if (!activeScene?.trail?.length) {
    summary.textContent = "--";
    return;
  }

  activeScene.trail.forEach((segment, index) => {
    const pill = document.createElement("span");
    pill.className = "scene-trail-pill";
    pill.textContent = segment;
    container.appendChild(pill);
    if (index < activeScene.trail.length - 1) {
      const separator = document.createElement("span");
      separator.className = "scene-trail-separator";
      separator.textContent = ">";
      container.appendChild(separator);
    }
  });

  summary.textContent = activeScene.trailSummary || activeScene.trail.join(" > ");
}

function updateSceneSummary(scene = null) {
  const activeScene = scene ?? state.currentScene;
  if (!activeScene) {
    byId("desktop-scene-code").textContent = "--";
    byId("desktop-scene-chip").textContent = "--";
    byId("desktop-scene-label").textContent = "--";
    byId("desktop-scene-context").textContent = "--";
    byId("desktop-scene-path").textContent = "--";
    byId("desktop-pagination").textContent = "--";
    byId("desktop-scene-subtitle").textContent =
      "Workspace-driven launcher, galleries, and opened-content scenes for blind-first exploration.";
    renderSceneTrail(null);
    return;
  }
  byId("desktop-scene-code").textContent = activeScene.code;
  byId("desktop-scene-chip").textContent = activeScene.code;
  byId("desktop-scene-label").textContent = activeScene.title;
  byId("desktop-scene-context").textContent = activeScene.context || "--";
  byId("desktop-scene-path").textContent = activeScene.path || "--";
  byId("desktop-pagination").textContent = activeScene.pagination || "--";
  byId("desktop-scene-subtitle").textContent = activeScene.subtitle;
  renderSceneTrail(activeScene);
}

function formatSeconds(value) {
  if (!Number.isFinite(value)) {
    return "--";
  }
  return `${value.toFixed(1)} s`;
}

function updateAudioSession(audioItem = state.audioScene?.item ?? null) {
  const player = audioPlayer();
  byId("desktop-audio-track").textContent = audioItem?.title ?? "--";
  byId("desktop-audio-playback").textContent = player.paused ? "paused" : "playing";
  byId("desktop-audio-position").textContent = formatSeconds(player.currentTime || 0);
  byId("desktop-audio-duration").textContent = formatSeconds(player.duration);
  byId("desktop-audio-state").textContent =
    audioItem ? (player.paused ? "Paused" : "Playing") : "Off";
}

function resetAudioSession() {
  const player = audioPlayer();
  player.pause();
  player.removeAttribute("src");
  player.load();
  state.audioScene = null;
  byId("desktop-audio-track").textContent = "--";
  byId("desktop-audio-playback").textContent = "idle";
  byId("desktop-audio-position").textContent = "0.0 s";
  byId("desktop-audio-duration").textContent = "--";
  byId("desktop-audio-state").textContent = "Off";
}

function pauseSceneAudio() {
  const player = audioPlayer();
  player.pause();
  updateAudioSession();
}

function bindAudioPlayer() {
  const player = audioPlayer();
  ["play", "pause", "timeupdate", "loadedmetadata", "ended"].forEach((eventName) => {
    player.addEventListener(eventName, () => {
      updateAudioSession();
      if (eventName === "ended") {
        publishStatus("Audio playback finished.", "Ready", "audio-ended", {
          speakMessage: false,
        });
      }
    });
  });
}

function setCamera(position, target) {
  state.sceneApi.applySceneView(position, target, { preserveUserView: true });
}

function normalizePage(page, pageCount) {
  return Math.max(0, Math.min(pageCount - 1, page));
}

function slicePage(items, pageSize, page) {
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const resolvedPage = normalizePage(page, pageCount);
  const start = resolvedPage * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    pageCount,
    page: resolvedPage,
  };
}

function buildWorkspaceSelect() {
  const select = byId("desktop-workspace-select");
  select.innerHTML = "";
  state.workspaceCatalog.forEach((workspace) => {
    const option = document.createElement("option");
    option.value = workspace.slug;
    option.textContent = workspace.title;
    select.appendChild(option);
  });
  const defaultWorkspace =
    state.workspaceCatalog.find((workspace) => workspace.is_default) ??
    state.workspaceCatalog[0] ??
    null;
  if (defaultWorkspace) {
    select.value = defaultWorkspace.slug;
  }
}

function currentSelectedWorkspaceSlug() {
  return byId("desktop-workspace-select").value;
}

function registerInteractiveMesh(mesh, role = "base") {
  mesh.userData.interactiveRole = role;
  if (mesh.material?.emissive) {
    mesh.userData.baseEmissive = mesh.material.emissive.getHex();
  }
  if (typeof mesh.material?.opacity === "number") {
    mesh.userData.baseOpacity = mesh.material.opacity;
  }
  return mesh;
}

function createBasePlatform(width, depth, accent = 0x39d2c0) {
  const group = new THREE.Group();
  const deck = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.12, depth),
    new THREE.MeshStandardMaterial({
      color: 0x132136,
      roughness: 0.92,
      metalness: 0.05,
    }),
  );
  deck.position.y = 0.06;
  group.add(deck);

  const topPlate = new THREE.Mesh(
    new THREE.BoxGeometry(width - 0.18, 0.028, depth - 0.18),
    new THREE.MeshStandardMaterial({
      color: 0x0f1724,
      roughness: 0.84,
      metalness: 0.06,
      emissive: 0x07111d,
    }),
  );
  topPlate.position.y = 0.135;
  group.add(topPlate);

  const frontLip = new THREE.Mesh(
    new THREE.BoxGeometry(width - 0.26, 0.06, 0.08),
    new THREE.MeshStandardMaterial({
      color: 0x0f1724,
      roughness: 0.88,
      metalness: 0.04,
    }),
  );
  frontLip.position.set(0, 0.105, depth / 2 - 0.12);
  group.add(frontLip);

  const originMarker = new THREE.Mesh(
    new THREE.ConeGeometry(0.08, 0.14, 3),
    new THREE.MeshStandardMaterial({
      color: accent,
      roughness: 0.32,
      metalness: 0.05,
      emissive: new THREE.Color(accent).multiplyScalar(0.18),
    }),
  );
  originMarker.rotation.y = Math.PI;
  originMarker.position.set(-width / 2 + 0.24, 0.17, depth / 2 - 0.24);
  group.add(originMarker);
  return group;
}

function addSceneTitle(world, title, subtitle) {
  const titleSprite = createLabelSprite(title, {
    background: "rgba(13, 17, 23, 0.88)",
    color: "#e6edf3",
    fontSize: 24,
  });
  titleSprite.position.set(0, 1.18, -1.5);
  world.add(titleSprite);

  const subtitleSprite = createLabelSprite(subtitle, {
    background: "rgba(13, 17, 23, 0.76)",
    color: "#8b949e",
    fontSize: 15,
  });
  subtitleSprite.position.set(0, 0.92, -1.5);
  world.add(subtitleSprite);
}

function addFloatingLabel(group, text, y = 0.72, color = "#8b949e") {
  const sprite = createLabelSprite(text, {
    background: "rgba(13, 17, 23, 0.80)",
    color,
    fontSize: 15,
  });
  sprite.position.set(0, y, 0);
  group.add(sprite);
}

function truncateLabelLine(text, maxLength = 84) {
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text;
}

function addGallerySummary(category, pageSlice, totalCount) {
  if (pageSlice.items.length === 0) {
    return;
  }
  const firstItem = pageSlice.page * GALLERY_PAGE_SIZE + 1;
  const lastItem = firstItem + pageSlice.items.length - 1;
  const rangeLine = `${CATEGORY_META[category].title} • page ${pageSlice.page + 1} of ${pageSlice.pageCount} • items ${firstItem}-${lastItem} of ${totalCount}`;
  const titlesLine = truncateLabelLine(
    `Visible now: ${pageSlice.items.map((item) => item.title).join(" | ")}`,
  );

  const rangeSprite = createLabelSprite(rangeLine, {
    background: "rgba(13, 17, 23, 0.76)",
    color: "#e6edf3",
    fontSize: 14,
  });
  rangeSprite.position.set(0, 0.64, -1.5);
  state.sceneApi.world.add(rangeSprite);

  const titlesSprite = createLabelSprite(titlesLine, {
    background: "rgba(13, 17, 23, 0.68)",
    color: "#8b949e",
    fontSize: 13,
  });
  titlesSprite.position.set(0, 0.46, -1.5);
  state.sceneApi.world.add(titlesSprite);
}

function beginSceneBuild(title) {
  const token = ++state.sceneBuildToken;
  setRuntimePill(`Loading ${title}`, "status-pill-purple");
  setStatus(`Loading ${title}.`, "Loading");
  return token;
}

function assertSceneToken(token) {
  if (token !== state.sceneBuildToken) {
    throw new Error("Stale scene build interrupted.");
  }
}

function finishSceneBuild(scene) {
  state.currentScene = scene;
  updateSceneSummary(scene);
  setRuntimePill("Desktop active", "status-pill-green");
}

function buildControlButton(kind, accent, disabled = false) {
  const group = new THREE.Group();
  const accentColor = disabled ? 0x4b5563 : accent;

  const base = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.BoxGeometry(0.44, 0.08, 0.32),
      new THREE.MeshStandardMaterial({
        color: disabled ? 0x1b222d : 0x16213a,
        roughness: 0.78,
        metalness: 0.08,
        emissive: 0x08111a,
      }),
    ),
    "base",
  );
  base.position.y = 0.04;
  group.add(base);

  const material = new THREE.MeshStandardMaterial({
    color: accentColor,
    roughness: 0.34,
    metalness: 0.08,
    emissive: new THREE.Color(accentColor).multiplyScalar(0.12),
  });

  if (kind === "home") {
    const roof = registerInteractiveMesh(new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.14, 4), material), "accent");
    roof.position.set(0, 0.16, -0.02);
    roof.rotation.y = Math.PI / 4;
    group.add(roof);
    const body = registerInteractiveMesh(
      new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.14, 0.14), material.clone()),
      "accent",
    );
    body.position.set(0, 0.12, 0.04);
    group.add(body);
  } else if (kind === "back") {
    [-0.07, 0.03].forEach((offset) => {
      const arrow = registerInteractiveMesh(
        new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.12, 3), material.clone()),
        "accent",
      );
      arrow.rotation.z = Math.PI / 2;
      arrow.position.set(offset, 0.13, 0);
      group.add(arrow);
    });
    const bar = registerInteractiveMesh(
      new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.04, 0.06), material.clone()),
      "accent",
    );
    bar.position.set(0.1, 0.13, 0);
    group.add(bar);
  } else if (kind === "up") {
    const shaft = registerInteractiveMesh(
      new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 0.16, 18), material),
      "accent",
    );
    shaft.position.y = 0.13;
    group.add(shaft);
    const arrow = registerInteractiveMesh(
      new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.12, 3), material.clone()),
      "accent",
    );
    arrow.position.y = 0.24;
    group.add(arrow);
  } else if (kind === "open") {
    const frame = registerInteractiveMesh(
      new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.16, 0.04), material),
      "accent",
    );
    frame.position.set(-0.03, 0.14, 0);
    group.add(frame);
    const arrow = registerInteractiveMesh(
      new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.12, 3), material.clone()),
      "accent",
    );
    arrow.rotation.z = -Math.PI / 2;
    arrow.position.set(0.12, 0.14, 0);
    group.add(arrow);
  } else if (kind === "start") {
    const marker = registerInteractiveMesh(
      new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.12, 4), material.clone()),
      "accent",
    );
    marker.rotation.y = Math.PI / 4;
    marker.position.set(-0.08, 0.18, 0);
    group.add(marker);
    const ridge = registerInteractiveMesh(
      new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.05, 0.08), material),
      "accent",
    );
    ridge.position.set(0.06, 0.12, 0);
    group.add(ridge);
    const stop = registerInteractiveMesh(
      new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.16, 0.08), material.clone()),
      "accent",
    );
    stop.position.set(-0.18, 0.12, 0);
    group.add(stop);
  } else if (kind === "previous") {
    [-0.1, 0, 0.1].forEach((offset) => {
      const ridge = registerInteractiveMesh(
        new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.2, 18), material.clone()),
        "accent",
      );
      ridge.rotation.z = Math.PI / 2;
      ridge.position.set(offset, 0.12, 0);
      group.add(ridge);
    });
  } else if (kind === "next") {
    const dome = registerInteractiveMesh(
      new THREE.Mesh(new THREE.SphereGeometry(0.08, 20, 16), material),
      "accent",
    );
    dome.scale.set(1, 0.72, 1);
    dome.position.set(0, 0.11, 0);
    group.add(dome);
    const arrow = registerInteractiveMesh(
      new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.12, 3), material.clone()),
      "accent",
    );
    arrow.rotation.z = -Math.PI / 2;
    arrow.position.set(0.14, 0.11, 0);
    group.add(arrow);
  } else if (kind === "playpause") {
    const left = registerInteractiveMesh(
      new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.15, 0.06), material),
      "accent",
    );
    left.position.set(-0.04, 0.12, 0);
    group.add(left);
    const right = registerInteractiveMesh(
      new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.15, 0.06), material.clone()),
      "accent",
    );
    right.position.set(0.04, 0.12, 0);
    group.add(right);
  } else if (kind === "seek-back" || kind === "seek-forward") {
    [-0.05, 0.05].forEach((offset) => {
      const arrow = registerInteractiveMesh(
        new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.12, 3), material.clone()),
        "accent",
      );
      arrow.rotation.z = kind === "seek-back" ? Math.PI / 2 : -Math.PI / 2;
      arrow.position.set(offset, 0.12, 0);
      group.add(arrow);
    });
  } else if (kind === "hub") {
    const outer = registerInteractiveMesh(
      new THREE.Mesh(
        new THREE.CylinderGeometry(0.12, 0.12, 0.06, 24),
        material,
      ),
      "accent",
    );
    outer.position.y = 0.12;
    group.add(outer);
    const inner = registerInteractiveMesh(
      new THREE.Mesh(
        new THREE.CylinderGeometry(0.055, 0.055, 0.075, 20),
        material.clone(),
      ),
      "accent",
    );
    inner.position.y = 0.17;
    group.add(inner);
    const marker = registerInteractiveMesh(
      new THREE.Mesh(
        new THREE.SphereGeometry(0.028, 18, 14),
        material.clone(),
      ),
      "accent",
    );
    marker.position.set(0.1, 0.2, 0);
    group.add(marker);
  }

  return group;
}

function buildFolderSymbol(color) {
  const group = new THREE.Group();
  const body = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.BoxGeometry(0.42, 0.2, 0.28),
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.46,
        metalness: 0.08,
        emissive: new THREE.Color(color).multiplyScalar(0.08),
      }),
    ),
    "accent",
  );
  body.position.y = 0.16;
  group.add(body);
  const tab = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.BoxGeometry(0.18, 0.08, 0.22),
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.42,
        metalness: 0.06,
        emissive: new THREE.Color(color).multiplyScalar(0.1),
      }),
    ),
    "accent",
  );
  tab.position.set(-0.08, 0.28, -0.03);
  group.add(tab);
  return group;
}

function buildTextSymbol(color) {
  const group = new THREE.Group();
  const slab = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.BoxGeometry(0.4, 0.14, 0.3),
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.52,
        metalness: 0.06,
        emissive: new THREE.Color(color).multiplyScalar(0.06),
      }),
    ),
    "accent",
  );
  slab.position.y = 0.14;
  group.add(slab);
  [
    [-0.08, 0.06],
    [0, 0.06],
    [-0.08, -0.02],
    [0, -0.02],
    [-0.08, -0.1],
    [0, -0.1],
  ].forEach(([x, z], index) => {
    if ([0, 1, 3, 5].includes(index)) {
      const dot = registerInteractiveMesh(
        new THREE.Mesh(
          new THREE.SphereGeometry(0.026, 18, 14, 0, Math.PI * 2, 0, Math.PI / 2),
          new THREE.MeshStandardMaterial({
            color: 0xe6edf3,
            roughness: 0.22,
            metalness: 0.04,
            emissive: 0x14263d,
          }),
        ),
        "accent",
      );
      dot.rotation.x = Math.PI;
      dot.position.set(x, 0.22, z);
      group.add(dot);
    }
  });
  return group;
}

function buildAudioSymbol(color) {
  const group = new THREE.Group();
  const speaker = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.CylinderGeometry(0.16, 0.2, 0.36, 24),
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.38,
        metalness: 0.18,
        emissive: new THREE.Color(color).multiplyScalar(0.08),
      }),
    ),
    "accent",
  );
  speaker.position.y = 0.22;
  group.add(speaker);
  [0.14, 0.24].forEach((radius, index) => {
    const wave = registerInteractiveMesh(
      new THREE.Mesh(
        new THREE.TorusGeometry(radius, 0.014, 10, 28),
        new THREE.MeshStandardMaterial({
          color,
          roughness: 0.28,
          metalness: 0.04,
          emissive: new THREE.Color(color).multiplyScalar(0.12),
          transparent: true,
          opacity: 0.88 - index * 0.24,
        }),
      ),
      "halo",
    );
    wave.rotation.y = Math.PI / 2;
    wave.position.set(0.14 + index * 0.1, 0.24, 0);
    group.add(wave);
  });
  return group;
}

function buildModelSymbol(color) {
  const group = new THREE.Group();
  const base = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.CylinderGeometry(0.24, 0.28, 0.08, 28),
      new THREE.MeshStandardMaterial({
        color: 0x101722,
        roughness: 0.86,
        metalness: 0.06,
        emissive: 0x09111c,
      }),
    ),
    "base",
  );
  base.position.y = 0.04;
  group.add(base);
  const peak = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.IcosahedronGeometry(0.18, 0),
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.42,
        metalness: 0.08,
        emissive: new THREE.Color(color).multiplyScalar(0.1),
      }),
    ),
    "accent",
  );
  peak.position.y = 0.25;
  peak.scale.set(1.1, 0.88, 1);
  group.add(peak);
  return group;
}

function buildUnsupportedSymbol(color) {
  const group = new THREE.Group();
  const body = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.OctahedronGeometry(0.2, 0),
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.62,
        metalness: 0.08,
        emissive: new THREE.Color(color).multiplyScalar(0.1),
      }),
    ),
    "accent",
  );
  body.position.y = 0.18;
  group.add(body);
  const band = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.TorusGeometry(0.22, 0.014, 10, 32),
      new THREE.MeshStandardMaterial({
        color: 0xffb4ab,
        roughness: 0.28,
        metalness: 0.06,
        emissive: 0x412320,
      }),
    ),
    "accent",
  );
  band.rotation.x = Math.PI / 2;
  band.position.y = 0.18;
  group.add(band);
  return group;
}

function buildTileBase(color) {
  const group = new THREE.Group();
  const pedestal = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.CylinderGeometry(0.34, 0.38, 0.08, 32),
      new THREE.MeshStandardMaterial({
        color: 0x0f1724,
        roughness: 0.88,
        metalness: 0.04,
        emissive: 0x09111c,
      }),
    ),
    "base",
  );
  pedestal.position.y = 0.04;
  group.add(pedestal);
  const halo = registerInteractiveMesh(
    new THREE.Mesh(
      new THREE.TorusGeometry(0.38, 0.022, 10, 40),
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.32,
        metalness: 0.04,
        emissive: new THREE.Color(color).multiplyScalar(0.12),
        transparent: true,
        opacity: 0.42,
      }),
    ),
    "halo",
  );
  halo.rotation.x = Math.PI / 2;
  halo.position.y = 0.088;
  group.add(halo);
  return group;
}

function buildInteractiveTile(title, symbolBuilder, color) {
  const group = new THREE.Group();
  group.add(buildTileBase(color));
  group.add(symbolBuilder(color));
  addFloatingLabel(group, title, 0.78, "#8b949e");
  return group;
}

function createTarget({
  id,
  title,
  type,
  actionLabel,
  group,
  position,
  radius,
  onActivate,
  color = 0x39d2c0,
  disabled = false,
}) {
  group.position.copy(position);
  group.userData.basePosition = position.clone();
  state.targets.set(id, {
    id,
    title,
    type,
    actionLabel,
    group,
    position,
    radius,
    onActivate,
    highlightHex: color,
    disabled,
  });
  state.focusOrder.push(id);
  state.sceneApi.world.add(group);
}

function clearTargets() {
  state.targets.clear();
  state.focusOrder = [];
  state.focusedTargetId = null;
  state.hoveredTargetId = null;
  state.fallbackFocusIndex = -1;
  updateFocusedInspector(null);
}

function refreshTargetVisuals() {
  state.targets.forEach((target) => {
    const isFocused = target.id === state.focusedTargetId || target.id === state.hoveredTargetId;
    const highlight = new THREE.Color(target.highlightHex);
    const restingY = target.group.userData.basePosition?.y ?? target.group.position.y;
    target.group.position.y = restingY + (isFocused ? 0.035 : 0);
    target.group.scale.setScalar(target.disabled ? 0.94 : isFocused ? 1.06 : 1);
    target.group.traverse((node) => {
      if (!node.isMesh) {
        return;
      }
      const role = node.userData.interactiveRole;
      const baseEmissive = node.userData.baseEmissive ?? 0x000000;
      const baseOpacity = node.userData.baseOpacity ?? 1;
      if (node.material?.emissive) {
        node.material.emissive.setHex(
          isFocused
            ? highlight.clone().multiplyScalar(role === "accent" ? 0.18 : 0.1).getHex()
            : baseEmissive,
        );
      }
      if (role === "halo" && typeof node.material?.opacity === "number") {
        node.material.opacity = isFocused ? Math.min(0.8, baseOpacity + 0.26) : baseOpacity;
      }
    });
  });
}

function focusTarget(targetId, options = {}) {
  const { source = "fallback", announceFocus = true, movePointer = true } = options;
  const target = state.targets.get(targetId);
  if (!target) {
    return;
  }
  state.focusedTargetId = targetId;
  state.fallbackFocusIndex = state.focusOrder.indexOf(targetId);
  updateFocusedInspector(target);
  refreshTargetVisuals();
  if (movePointer && source !== "pointer") {
    state.pointerController?.setPosition(
      target.position.clone().setY(Math.max(target.position.y + 0.22, 0.24)),
    );
  }
  state.sceneApi.setPointerState(source === "pointer" ? "focus" : "idle");
  if (announceFocus) {
    publishStatus(`${target.title}. ${target.actionLabel}.`, "Ready", `focus-${targetId}`);
  }
}

function moveFallbackFocus(step) {
  if (state.focusOrder.length === 0) {
    return;
  }
  const nextIndex =
    ((state.fallbackFocusIndex < 0 ? 0 : state.fallbackFocusIndex) + step + state.focusOrder.length) %
    state.focusOrder.length;
  focusTarget(state.focusOrder[nextIndex], { source: "fallback" });
}

function updatePointerHover(position) {
  let nearestTarget = null;
  let nearestDistance = Number.POSITIVE_INFINITY;
  state.targets.forEach((target) => {
    const distance = target.position.distanceTo(position);
    if (distance <= target.radius && distance < nearestDistance) {
      nearestTarget = target;
      nearestDistance = distance;
    }
  });
  if (!nearestTarget) {
    if (state.hoveredTargetId !== null) {
      state.hoveredTargetId = null;
      refreshTargetVisuals();
    }
    state.sceneApi.setPointerState("idle");
    publishStatus(
      state.currentScene?.idleMessage ?? "Pointer moving across the current tactile scene.",
      "Ready",
      state.currentScene?.idleMessage ?? "pointer-idle",
      { speakMessage: false },
    );
    return;
  }
  if (state.hoveredTargetId !== nearestTarget.id || state.focusedTargetId !== nearestTarget.id) {
    state.hoveredTargetId = nearestTarget.id;
    focusTarget(nearestTarget.id, { source: "pointer", movePointer: false });
  }
}

async function activateFocusedTarget(source = "pointer") {
  const targetId =
    source === "pointer"
      ? state.hoveredTargetId ?? state.focusedTargetId
      : state.focusedTargetId ?? state.hoveredTargetId;
  const target = state.targets.get(targetId);
  if (!target) {
    publishStatus("No tactile control is currently under the pointer.", "Ready", "no-target");
    return;
  }
  if (target.disabled) {
    publishStatus(`${target.title} is unavailable in this state.`, "Ready", `disabled-${target.id}`);
    return;
  }
  state.sceneApi.setPointerState("active");
  publishStatus(`${target.title}. ${target.actionLabel}.`, "Active", `activate-${target.id}`);
  try {
    await target.onActivate?.(source);
  } finally {
    window.setTimeout(() => {
      state.sceneApi.setPointerState(source === "pointer" ? "focus" : "idle");
    }, 160);
  }
}

function prepareScene(
  width,
  depth,
  title,
  subtitle,
  cameraPosition = [4.9, 3.2, 5.1],
  target = [0, 0.28, 0.08],
  keepAudioSession = false,
) {
  if (!keepAudioSession) {
    resetAudioSession();
  }
  clearTargets();
  state.sceneApi.clearWorld();
  state.sceneApi.setBoundarySize(new THREE.Vector3(width + 0.6, 1.6, depth + 0.6));
  state.sceneApi.setGridVisible(true);
  state.sceneApi.setBoundaryVisible(true);
  setCamera(cameraPosition, target);
  state.sceneApi.world.add(createBasePlatform(width, depth));
  addSceneTitle(state.sceneApi.world, title, subtitle);
}

async function fetchBraillePreview(text, columns) {
  const normalizedText = (text || "").trim() || "FeelIT";
  const key = `${columns}:${normalizedText}`;
  if (state.brailleCache.has(key)) {
    return state.brailleCache.get(key);
  }
  const payload = await fetchJson(braillePreviewUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: normalizedText, columns }),
  });
  state.brailleCache.set(key, payload);
  return payload;
}

function createBrailleCellGroup(cell, columns, rowOffset = 0, options = {}) {
  const spacingX = options.spacingX ?? 0.28;
  const spacingZ = options.spacingZ ?? 0.38;
  const originX = -((columns - 1) * spacingX) / 2;
  const localRow = cell.row - rowOffset;
  const x = originX + cell.column * spacingX;
  const z = localRow * spacingZ;
  const group = new THREE.Group();
  group.position.set(x, 0, z);

  const cellBase = new THREE.Mesh(
    new THREE.BoxGeometry(0.18, 0.02, 0.24),
    new THREE.MeshStandardMaterial({
      color: options.baseColor ?? 0x111827,
      roughness: 0.86,
      metalness: 0.04,
      emissive: 0x08111a,
    }),
  );
  cellBase.position.y = 0.01;
  group.add(cellBase);

  [
    [-0.04, 0.05],
    [0.04, 0.05],
    [-0.04, 0],
    [0.04, 0],
    [-0.04, -0.05],
    [0.04, -0.05],
  ].forEach(([dotX, dotZ], index) => {
    if (cell.dots[index]) {
      const dot = new THREE.Mesh(
        new THREE.SphereGeometry(0.024, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2),
        new THREE.MeshStandardMaterial({
          color: options.dotColor ?? 0xf2cc60,
          roughness: 0.35,
          metalness: 0.04,
          emissive: 0x422800,
        }),
      );
      dot.rotation.x = Math.PI;
      dot.position.set(dotX, 0.038, dotZ);
      group.add(dot);
    }
  });

  return group;
}

function buildBraillePlaque(cells, columns, options = {}) {
  const rowCount = cells.length ? Math.max(...cells.map((cell) => cell.row)) + 1 : 1;
  const maxRows = options.maxRows ?? rowCount;
  const visibleCells = cells.filter((cell) => cell.row < maxRows);
  const width = Math.max(1.4, columns * (options.spacingX ?? 0.28) + 0.6);
  const depth = Math.max(0.9, maxRows * (options.spacingZ ?? 0.38) + 0.5);
  const group = new THREE.Group();

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.08, depth),
    new THREE.MeshStandardMaterial({
      color: options.surfaceColor ?? 0x16213a,
      roughness: 0.9,
      metalness: 0.05,
      emissive: 0x08111a,
    }),
  );
  base.position.y = 0.04;
  group.add(base);

  const orientation = new THREE.Mesh(
    new THREE.ConeGeometry(0.07, 0.12, 3),
    new THREE.MeshStandardMaterial({
      color: options.markerColor ?? 0x39d2c0,
      roughness: 0.32,
      metalness: 0.04,
      emissive: 0x0f2c2a,
    }),
  );
  orientation.rotation.y = Math.PI;
  orientation.position.set(-width / 2 + 0.14, 0.13, depth / 2 - 0.16);
  group.add(orientation);

  visibleCells.forEach((cell) => {
    const cellGroup = createBrailleCellGroup(cell, columns, 0, options);
    cellGroup.position.z -= ((maxRows - 1) * (options.spacingZ ?? 0.38)) / 2;
    group.add(cellGroup);
  });

  return group;
}

function galleryTilePositions(count) {
  if (count <= 1) {
    return [new THREE.Vector3(0, 0.12, 0.02)].slice(0, count);
  }
  if (count === 2) {
    return [
      new THREE.Vector3(-1.18, 0.12, 0.02),
      new THREE.Vector3(1.18, 0.12, 0.02),
    ];
  }
  if (count <= 3) {
    return [
      new THREE.Vector3(-1.48, 0.12, -0.26),
      new THREE.Vector3(0, 0.12, 0.56),
      new THREE.Vector3(1.48, 0.12, -0.26),
    ].slice(0, count);
  }
  return [
    new THREE.Vector3(-1.48, 0.12, -0.72),
    new THREE.Vector3(0, 0.12, -0.08),
    new THREE.Vector3(1.48, 0.12, -0.72),
    new THREE.Vector3(-1.48, 0.12, 0.62),
    new THREE.Vector3(0, 0.12, 1.26),
    new THREE.Vector3(1.48, 0.12, 0.62),
  ].slice(0, count);
}

function resolveItemKind(item) {
  return item.kind ?? item.category?.slice(0, -1) ?? "unsupported";
}

function kindMeta(kind) {
  return FILE_KIND_META[kind] ?? FILE_KIND_META.unsupported;
}

function kindSymbolBuilder(kind) {
  if (kind === "model") {
    return buildModelSymbol;
  }
  if (kind === "text") {
    return buildTextSymbol;
  }
  if (kind === "audio") {
    return buildAudioSymbol;
  }
  if (kind === "directory") {
    return buildFolderSymbol;
  }
  return buildUnsupportedSymbol;
}

function itemRawFileUrl(item) {
  if (item.source?.kind === "demo_model" || item.source?.kind === "library_audio") {
    return item.source.file_url;
  }
  if (item.source?.kind === "workspace_file") {
    return workspaceRawUrl(state.activeWorkspace.slug, item.source.relative_path);
  }
  return item.source?.file_url ?? "";
}

function itemModelFormat(item) {
  const explicitFormat = item.source?.format;
  if (explicitFormat) {
    return explicitFormat;
  }
  const extension = item.source?.extension;
  if (extension) {
    return extension.replace(/^\./, "");
  }
  const rawUrl = itemRawFileUrl(item);
  const match = /\.([a-z0-9]+)(?:$|[?#])/i.exec(rawUrl);
  return match ? match[1].toLowerCase() : "obj";
}

function itemModelFormatLabel(item) {
  try {
    return item.source?.format_label ?? modelFormatLabel(itemModelFormat(item));
  } catch {
    return item.source?.format_label ?? "3D";
  }
}

function itemTextEndpoint(item, offset, maxChars) {
  if (item.source?.kind === "library_document") {
    return `${item.source.text_endpoint}?offset=${offset}&max_chars=${maxChars}`;
  }
  if (item.source?.kind === "workspace_file") {
    return workspaceTextUrl(state.activeWorkspace.slug, item.source.relative_path, offset, maxChars);
  }
  throw new Error("This item does not expose a readable text payload.");
}

function detailOriginLabel(origin) {
  if (!origin) {
    return "Launcher";
  }
  if (origin.type === "gallery") {
    return `${CATEGORY_META[origin.category].title}, page ${origin.page + 1}`;
  }
  if (origin.type === "file-browser") {
    return origin.path ? `File browser: ${origin.path}` : "File browser root";
  }
  return "Launcher";
}

function launcherTrail(workspace) {
  return [workspace.title, "Launcher"];
}

function galleryTrail(workspace, category, page) {
  return [workspace.title, CATEGORY_META[category].title, `Page ${page + 1}`];
}

function fileBrowserTrail(workspace, path, page, label = "Root") {
  return [workspace.title, "File Browser", path || label, `Page ${page + 1}`];
}

function originTrail(workspace, origin) {
  if (!origin) {
    return launcherTrail(workspace);
  }
  if (origin.type === "gallery") {
    return galleryTrail(workspace, origin.category, origin.page ?? 0);
  }
  if (origin.type === "file-browser") {
    return fileBrowserTrail(workspace, origin.path ?? "", origin.page ?? 0);
  }
  return launcherTrail(workspace);
}

function detailTrail(workspace, item, origin) {
  return [...originTrail(workspace, origin), "Detail", item.title];
}

function openedSceneTrail(workspace, item, origin, sceneLabel) {
  return [...originTrail(workspace, origin), sceneLabel, item.title];
}

function originReturnConfig(origin) {
  if (!origin) {
    return {
      label: "Launcher",
      actionLabel: "Return to the workspace launcher",
    };
  }
  if (origin.type === "gallery") {
    return {
      label: "Gallery",
      actionLabel: `Return to ${CATEGORY_META[origin.category].title}, page ${origin.page + 1}`,
    };
  }
  if (origin.type === "file-browser") {
    return {
      label: "Browser",
      actionLabel: origin.path
        ? `Return to the file browser at ${origin.path}`
        : "Return to the workspace file browser root",
    };
  }
  return {
    label: "Launcher",
    actionLabel: "Return to the workspace launcher",
  };
}

function originStartConfig(origin) {
  if (!origin) {
    return null;
  }
  if (origin.type === "gallery") {
    return {
      label: "Start",
      actionLabel: `Return to the first page of ${CATEGORY_META[origin.category].title}`,
      color: CATEGORY_META[origin.category].color,
    };
  }
  if (origin.type === "file-browser") {
    return {
      label: "Root",
      actionLabel: "Return to the workspace file browser root",
      color: 0xc297ff,
    };
  }
  return null;
}

function galleryHubTargetId(category) {
  return `gallery-${category}-hub`;
}

function galleryHubMessage(category, pageSlice, totalCount) {
  const firstItem = pageSlice.items.length ? pageSlice.page * GALLERY_PAGE_SIZE + 1 : 0;
  const lastItem = pageSlice.items.length ? firstItem + pageSlice.items.length - 1 : 0;
  const rangeText =
    firstItem > 0
      ? `Items ${firstItem} through ${lastItem} of ${totalCount}`
      : `No items are currently visible on this page`;
  return `${CATEGORY_META[category].title}, page ${pageSlice.page + 1} of ${pageSlice.pageCount}. ${rangeText}.`;
}

function browserHubTargetId() {
  return "file-browser-hub";
}

function fileBrowserHubMessage(payload, pageSlice) {
  const location = payload.current_path ? `Path ${payload.current_path}` : "Workspace file browser root";
  const firstItem = pageSlice.items.length ? pageSlice.page * payload.page_size + 1 : 0;
  const lastItem = pageSlice.items.length ? firstItem + pageSlice.items.length - 1 : 0;
  const rangeText =
    firstItem > 0
      ? `Visible entries ${firstItem} through ${lastItem} of ${payload.total_entries}`
      : "No entries are currently visible on this page";
  return `${location}. Page ${pageSlice.page + 1} of ${pageSlice.pageCount}. ${rangeText}.`;
}

async function navigateToOriginStart(origin) {
  if (!origin) {
    await navigateToLauncher();
    return;
  }
  if (origin.type === "gallery") {
    await navigateToGallery(origin.category, 0);
    return;
  }
  if (origin.type === "file-browser") {
    await navigateToFileBrowser("", 0);
    return;
  }
  await navigateToLauncher();
}

async function navigateHome(origin) {
  if (!origin) {
    await navigateToLauncher();
    return;
  }
  if (origin.type === "gallery") {
    await navigateToGallery(origin.category, origin.page);
    return;
  }
  if (origin.type === "file-browser") {
    await navigateToFileBrowser(origin.path ?? "", origin.page ?? 0);
    return;
  }
  await navigateToLauncher();
}

function createGalleryItemTarget(item, position, onActivate, actionLabel = null) {
  const kind = resolveItemKind(item);
  const meta = kindMeta(kind);
  const symbolBuilder = kindSymbolBuilder(kind);
  const group = buildInteractiveTile(item.title, symbolBuilder, meta.color);
  createTarget({
    id: `item-${item.slug}`,
    title: item.title,
    type: meta.title,
    actionLabel: actionLabel ?? item.open_label ?? meta.actionLabel,
    group,
    position,
    radius: 0.52,
    onActivate,
    color: meta.color,
  });
}

function addControlTarget({
  id,
  label,
  type,
  actionLabel,
  kind,
  color,
  position,
  onActivate,
  disabled = false,
}) {
  const group = buildControlButton(kind, color, disabled);
  addFloatingLabel(group, label, 0.42, disabled ? "#6e7681" : "#8b949e");
  createTarget({
    id,
    title: label,
    type,
    actionLabel,
    group,
    position,
    radius: 0.34,
    onActivate,
    color,
    disabled,
  });
}

async function loadWorkspaceCatalog() {
  const payload = await fetchJson(workspaceCatalogUrl);
  state.workspaceCatalog = payload.workspaces;
  buildWorkspaceSelect();
  if (state.workspaceCatalog.length === 0) {
    throw new Error("No Haptic Desktop workspace descriptors are available.");
  }
  return payload;
}

async function loadWorkspaceBySlug(slug) {
  const workspace = await fetchJson(workspaceDetailUrl(slug));
  state.activeWorkspace = workspace;
  updateWorkspaceSummary();
  publishStatus(`Workspace ${workspace.title} loaded.`, "Ready", `workspace-${workspace.slug}`);
  await navigateToLauncher();
}

async function navigateToLauncher() {
  const token = beginSceneBuild("workspace launcher");
  const workspace = state.activeWorkspace;
  prepareScene(
    5.2,
    4.2,
    workspace.title,
    "Scene 1: tactile launcher with direct access to curated galleries and file browsing.",
  );

  addControlTarget({
    id: "launcher-hub",
    label: "Launcher",
    type: "Launcher",
    actionLabel: "Stay at the main launcher and survey the available entry points",
    kind: "home",
    color: 0x39d2c0,
    position: new THREE.Vector3(0, 0.12, 0.12),
    onActivate: async () => {
      publishStatus(
        `Main launcher. Models ${workspace.libraries.models.length}, texts ${workspace.libraries.texts.length}, audio ${workspace.libraries.audio.length}, plus workspace file browsing.`,
        "Ready",
        "launcher-hub",
      );
    },
  });

  [
    {
      id: "launcher-models",
      title: "Models Gallery",
      type: "Launcher",
      actionLabel: "Open the 3D model gallery",
      color: CATEGORY_META.models.color,
      symbolBuilder: buildModelSymbol,
      position: new THREE.Vector3(-1.25, 0.12, -0.72),
      onActivate: async () => navigateToGallery("models", 0),
    },
    {
      id: "launcher-texts",
      title: "Text Library",
      type: "Launcher",
      actionLabel: "Open the text gallery",
      color: CATEGORY_META.texts.color,
      symbolBuilder: buildTextSymbol,
      position: new THREE.Vector3(1.25, 0.12, -0.72),
      onActivate: async () => navigateToGallery("texts", 0),
    },
    {
      id: "launcher-audio",
      title: "Audio Library",
      type: "Launcher",
      actionLabel: "Open the audio gallery",
      color: CATEGORY_META.audio.color,
      symbolBuilder: buildAudioSymbol,
      position: new THREE.Vector3(-1.25, 0.12, 0.92),
      onActivate: async () => navigateToGallery("audio", 0),
    },
    {
      id: "launcher-files",
      title: "File Browser",
      type: "Launcher",
      actionLabel: "Open workspace file navigation",
      color: 0xc297ff,
      symbolBuilder: buildFolderSymbol,
      position: new THREE.Vector3(1.25, 0.12, 0.92),
      onActivate: async () => navigateToFileBrowser("", 0),
    },
  ].forEach((item) => {
    const group = buildInteractiveTile(item.title, item.symbolBuilder, item.color);
    createTarget({
      id: item.id,
      title: item.title,
      type: item.type,
      actionLabel: item.actionLabel,
      group,
      position: item.position,
      radius: 0.56,
      onActivate: item.onActivate,
      color: item.color,
    });
  });

  const info = createLabelSprite(
    `Models ${workspace.libraries.models.length} | Texts ${workspace.libraries.texts.length} | Audio ${workspace.libraries.audio.length}`,
    {
      background: "rgba(13, 17, 23, 0.72)",
      color: "#8b949e",
      fontSize: 15,
    },
  );
  info.position.set(0, 0.3, 1.52);
  state.sceneApi.world.add(info);

  state.pointerController.setBounds(
    new THREE.Vector3(-2.2, 0.14, -1.6),
    new THREE.Vector3(2.2, 1.1, 1.8),
  );
  state.pointerController.setPosition(new THREE.Vector3(0, 0.36, 0.18));
  assertSceneToken(token);
  finishSceneBuild({
    code: "launcher",
    title: "Workspace Launcher",
    subtitle: "Tactile launcher for curated models, text, audio, and direct file browsing.",
    context: workspace.title,
    path: workspace.file_browser.root_label,
    pagination: "1 / 1",
    trail: launcherTrail(workspace),
    idleMessage: "Pointer moving across the launcher scene.",
  });
  focusTarget("launcher-hub", { source: "scene", movePointer: false });
}

async function navigateToGallery(category, page = 0) {
  const token = beginSceneBuild(`${CATEGORY_META[category].title.toLowerCase()}`);
  const workspace = state.activeWorkspace;
  const pageSlice = slicePage(workspace.libraries[category], GALLERY_PAGE_SIZE, page);
  prepareScene(
    6.2,
    4.6,
    CATEGORY_META[category].title,
    `Scene 2: paginated tactile gallery for ${category}.`,
    [0, 3.75, 5.45],
    [0, 0.3, 0.08],
  );

  const positions = galleryTilePositions(pageSlice.items.length);
  pageSlice.items.forEach((item, index) => {
    createGalleryItemTarget(
      item,
      positions[index],
      async () => navigateToDetail(item, { type: "gallery", category, page: pageSlice.page }),
      "Inspect item details and continue to the corresponding runtime scene",
    );
  });
  addGallerySummary(category, pageSlice, workspace.libraries[category].length);

  addControlTarget({
    id: `gallery-${category}-launcher`,
    label: "Launcher",
    type: "Control",
    actionLabel: "Return to the main launcher",
    kind: "home",
    color: 0x39d2c0,
    position: new THREE.Vector3(-2.32, 0.12, 1.78),
    onActivate: async () => navigateToLauncher(),
  });
  addControlTarget({
    id: galleryHubTargetId(category),
    label: "Gallery",
    type: "Control",
    actionLabel: `Stay on ${CATEGORY_META[category].title}, page ${pageSlice.page + 1}, and survey the paginated gallery`,
    kind: "hub",
    color: CATEGORY_META[category].color,
    position: new THREE.Vector3(-1.16, 0.12, 1.78),
    onActivate: async () =>
      publishStatus(
        galleryHubMessage(category, pageSlice, workspace.libraries[category].length),
        "Ready",
        `gallery-hub-${category}-${pageSlice.page}`,
      ),
  });
  addControlTarget({
    id: `gallery-${category}-start`,
    label: "Start",
    type: "Control",
    actionLabel: `Return to the first page of ${CATEGORY_META[category].title}`,
    kind: "start",
    color: CATEGORY_META[category].color,
    position: new THREE.Vector3(0, 0.12, 1.78),
    onActivate: async () => navigateToGallery(category, 0),
    disabled: pageSlice.page === 0,
  });
  addControlTarget({
    id: `gallery-${category}-prev`,
    label: "Previous",
    type: "Control",
    actionLabel: "Move to the previous gallery page",
    kind: "previous",
    color: CATEGORY_META[category].color,
    position: new THREE.Vector3(1.16, 0.12, 1.78),
    onActivate: async () => navigateToGallery(category, pageSlice.page - 1),
    disabled: pageSlice.page === 0,
  });
  addControlTarget({
    id: `gallery-${category}-next`,
    label: "Next",
    type: "Control",
    actionLabel: "Move to the next gallery page",
    kind: "next",
    color: CATEGORY_META[category].color,
    position: new THREE.Vector3(2.32, 0.12, 1.78),
    onActivate: async () => navigateToGallery(category, pageSlice.page + 1),
    disabled: pageSlice.page >= pageSlice.pageCount - 1,
  });

  state.pointerController.setBounds(
    new THREE.Vector3(-2.8, 0.14, -1.6),
    new THREE.Vector3(2.8, 1.1, 2.0),
  );
  state.pointerController.setPosition(
    new THREE.Vector3(-1.16, 0.36, 1.32),
  );
  assertSceneToken(token);
  finishSceneBuild({
    code: CATEGORY_META[category].sceneCode,
    title: CATEGORY_META[category].title,
    subtitle: CATEGORY_META[category].description,
    context: workspace.title,
    path: CATEGORY_META[category].title,
    pagination: `${pageSlice.page + 1} / ${pageSlice.pageCount}`,
    trail: galleryTrail(workspace, category, pageSlice.page),
    idleMessage: `Pointer moving across the ${CATEGORY_META[category].title.toLowerCase()}.`,
  });
  focusTarget(
    galleryHubTargetId(category),
    { source: "scene", movePointer: false },
  );
}

async function navigateToFileBrowser(relativePath = "", page = 0) {
  const token = beginSceneBuild("file browser");
  const workspace = state.activeWorkspace;
  const payload = await fetchJson(
    workspaceBrowseUrl(workspace.slug, relativePath, page, FILE_BROWSER_PAGE_SIZE),
  );
  const pageSlice = {
    items: payload.entries,
    page: payload.page,
    pageCount: payload.page_count,
  };
  prepareScene(
    6.8,
    4.5,
    "Workspace File Browser",
    "Scene 2: tactile filesystem navigation rooted in the active workspace.",
    [5.8, 3.6, 5.9],
    [0, 0.28, 0.16],
  );

  const positions = galleryTilePositions(pageSlice.items.length);
  pageSlice.items.forEach((entry, index) => {
    const origin = { type: "file-browser", path: payload.current_path, page: payload.page };
    const onActivate =
      entry.kind === "directory"
        ? async () => navigateToFileBrowser(entry.relative_path, 0)
        : entry.kind === "unsupported"
          ? async () =>
              navigateToDetail(
                {
                  ...entry,
                  source: entry.source ?? {
                    kind: "workspace_file",
                    relative_path: entry.relative_path,
                  },
                },
                origin,
              )
        : async () =>
            openItemScene(
              {
                ...entry,
                source: entry.source ?? {
                  kind: "workspace_file",
                  relative_path: entry.relative_path,
                },
              },
              origin,
            );
    createGalleryItemTarget(entry, positions[index], onActivate);
  });

  addControlTarget({
    id: "file-browser-launcher",
    label: "Launcher",
    type: "Control",
    actionLabel: "Return to the main launcher",
    kind: "home",
    color: 0x39d2c0,
    position: new THREE.Vector3(-2.85, 0.12, 1.78),
    onActivate: async () => navigateToLauncher(),
  });
  addControlTarget({
    id: browserHubTargetId(),
    label: "Browser",
    type: "Control",
    actionLabel: "Stay in the current workspace browser page and survey the visible entries",
    kind: "hub",
    color: 0xc297ff,
    position: new THREE.Vector3(-1.71, 0.12, 1.78),
    onActivate: async () =>
      publishStatus(
        fileBrowserHubMessage(payload, pageSlice),
        "Ready",
        `browser-hub-${payload.current_path}-${pageSlice.page}`,
      ),
  });
  addControlTarget({
    id: "file-browser-root",
    label: "Root",
    type: "Control",
    actionLabel: "Return to the workspace file browser root",
    kind: "start",
    color: 0xc297ff,
    position: new THREE.Vector3(-0.57, 0.12, 1.78),
    onActivate: async () => navigateToFileBrowser("", 0),
    disabled: payload.current_path === "",
  });
  addControlTarget({
    id: "file-browser-up",
    label: "Up",
    type: "Control",
    actionLabel: "Return to the parent folder",
    kind: "up",
    color: 0xc297ff,
    position: new THREE.Vector3(0.57, 0.12, 1.78),
    onActivate: async () => navigateToFileBrowser(payload.parent_path ?? "", 0),
    disabled: !payload.parent_path,
  });
  addControlTarget({
    id: "file-browser-prev",
    label: "Previous",
    type: "Control",
    actionLabel: "Move to the previous file page",
    kind: "previous",
    color: 0x58a6ff,
    position: new THREE.Vector3(1.71, 0.12, 1.78),
    onActivate: async () => navigateToFileBrowser(payload.current_path, payload.page - 1),
    disabled: payload.page === 0,
  });
  addControlTarget({
    id: "file-browser-next",
    label: "Next",
    type: "Control",
    actionLabel: "Move to the next file page",
    kind: "next",
    color: 0x58a6ff,
    position: new THREE.Vector3(2.85, 0.12, 1.78),
    onActivate: async () => navigateToFileBrowser(payload.current_path, payload.page + 1),
    disabled: payload.page >= payload.page_count - 1,
  });

  state.pointerController.setBounds(
    new THREE.Vector3(-3.2, 0.14, -1.6),
    new THREE.Vector3(3.2, 1.1, 2.0),
  );
  state.pointerController.setPosition(
    new THREE.Vector3(-1.71, 0.36, 1.32),
  );
  assertSceneToken(token);
  finishSceneBuild({
    code: "file-browser",
    title: "Workspace File Browser",
    subtitle: "Directory buttons and typed file buttons share one tactile map, while supported files dispatch directly into their corresponding runtime scenes.",
    context: workspace.title,
    path: payload.current_path || payload.current_label,
    pagination: `${payload.page + 1} / ${payload.page_count}`,
    trail: fileBrowserTrail(workspace, payload.current_path, payload.page, payload.current_label),
    idleMessage: "Pointer moving across the workspace file browser.",
  });
  focusTarget(
    browserHubTargetId(),
    { source: "scene", movePointer: false },
  );
}

function truncateDetailText(text) {
  return text.length > 24 ? `${text.slice(0, 24)}…` : text;
}

async function navigateToDetail(item, origin) {
  const token = beginSceneBuild("content detail");
  const kind = resolveItemKind(item);
  const meta = kindMeta(kind);
  const preview = await fetchBraillePreview(truncateDetailText(item.title), DETAIL_BRAILLE_COLUMNS);

  prepareScene(
    5.0,
    4.0,
    item.title,
    "Scene 3: tactile detail plaque with braille naming and open controls.",
    [4.6, 3.0, 4.6],
    [0, 0.28, 0],
  );

  const plaque = buildBraillePlaque(preview.cells, DETAIL_BRAILLE_COLUMNS, {
    maxRows: 2,
    spacingX: 0.25,
    spacingZ: 0.34,
    surfaceColor: 0x16213a,
  });
  plaque.position.set(-0.2, 0.12, -0.22);
  state.sceneApi.world.add(plaque);

  const symbolBuilder = kindSymbolBuilder(kind);
  const icon = buildInteractiveTile(meta.title, symbolBuilder, meta.color);
  icon.position.set(1.6, 0.12, -0.2);
  icon.scale.setScalar(0.92);
  state.sceneApi.world.add(icon);

  const summarySprite = createLabelSprite(item.summary || "No description recorded.", {
    background: "rgba(13, 17, 23, 0.72)",
    color: "#8b949e",
    fontSize: 15,
  });
  summarySprite.position.set(0, 0.32, 1.18);
  state.sceneApi.world.add(summarySprite);

  const originStart = originStartConfig(origin);
  const originReturn = originReturnConfig(origin);
  addControlTarget({
    id: "detail-launcher",
    label: "Launcher",
    type: "Control",
    actionLabel: "Return to the main launcher",
    kind: "home",
    color: 0x39d2c0,
    position: new THREE.Vector3(-1.62, 0.12, 1.42),
    onActivate: async () => navigateToLauncher(),
  });
  if (originStart) {
    addControlTarget({
      id: "detail-origin-start",
      label: originStart.label,
      type: "Control",
      actionLabel: originStart.actionLabel,
      kind: "start",
      color: originStart.color,
      position: new THREE.Vector3(-0.5, 0.12, 1.42),
      onActivate: async () => navigateToOriginStart(origin),
    });
  }
  addControlTarget({
    id: "detail-return",
    label: originReturn.label,
    type: "Control",
    actionLabel: originReturn.actionLabel,
    kind: "back",
    color: 0x58a6ff,
    position: new THREE.Vector3(originStart ? 0.62 : 0, 0.12, 1.42),
    onActivate: async () => navigateHome(origin),
  });
  addControlTarget({
    id: "detail-open",
    label: kind === "unsupported" ? "Unavailable" : "Open",
    type: "Control",
    actionLabel: kind === "unsupported" ? "The selected file is not supported yet" : item.open_label ?? `Open ${item.title}`,
    kind: "open",
    color: meta.color,
    position: new THREE.Vector3(originStart ? 1.74 : 1.2, 0.12, 1.42),
    onActivate: async () => openItemScene(item, origin),
    disabled: kind === "unsupported",
  });

  state.pointerController.setBounds(
    new THREE.Vector3(-2.2, 0.14, -1.4),
    new THREE.Vector3(2.2, 1.0, 1.7),
  );
  state.pointerController.setPosition(new THREE.Vector3(-0.1, 0.34, 1.0));
  assertSceneToken(token);
  finishSceneBuild({
    code: `detail-${kind}`,
    title: `${meta.title} Detail`,
    subtitle: "Item naming is represented as a tactile plaque before opening the content scene.",
    context: detailOriginLabel(origin),
    path:
      item.source?.relative_path ??
      item.source?.document_slug ??
      item.source?.audio_slug ??
      item.source?.demo_model_slug ??
      item.slug,
    pagination: "1 / 1",
    trail: detailTrail(state.activeWorkspace, item, origin),
    idleMessage: `Pointer moving across the detail scene for ${item.title}.`,
  });
  focusTarget("detail-return", { source: "scene", movePointer: false });
  publishStatus(`${item.title}. ${item.summary || meta.title}.`, "Ready", `detail-${item.slug}`);
}

async function loadModelSceneAsset(item) {
  const { modelRoot } = await loadModelFromUrl(itemRawFileUrl(item), itemModelFormat(item));
  return modelRoot;
}

async function navigateToModelScene(item, origin) {
  const token = beginSceneBuild("model scene");
  prepareScene(
    6.2,
    4.8,
    item.title,
    "Scene 4: bounded model exploration with direct tactile return controls.",
    [5.2, 3.8, 6.2],
    [0, 0.72, 0],
  );

  const object = await loadModelSceneAsset(item);
  object.traverse((node) => {
    if (node.isMesh) {
      node.material = new THREE.MeshStandardMaterial({
        color: 0x6f8fb4,
        roughness: 0.6,
        metalness: 0.08,
        emissive: 0x0b1522,
      });
    }
  });

  const plinth = new THREE.Mesh(
    new THREE.CylinderGeometry(1.42, 1.52, 0.12, 36),
    new THREE.MeshStandardMaterial({
      color: 0x0f1724,
      roughness: 0.9,
      metalness: 0.06,
      emissive: 0x08111a,
    }),
  );
  plinth.position.y = 0.06;
  state.sceneApi.world.add(plinth);
  state.sceneApi.world.add(object);
  state.sceneApi.normalizeObject(object, 2.4);
  object.position.y += 0.16;
  state.sceneApi.frameObject(object, 5.6);

  const bounds = new THREE.Box3().setFromObject(object);
  const size = bounds.getSize(new THREE.Vector3());
  const center = bounds.getCenter(new THREE.Vector3());
  const originStart = originStartConfig(origin);
  const originReturn = originReturnConfig(origin);

  addControlTarget({
    id: "model-launcher",
    label: "Launcher",
    type: "Control",
    actionLabel: "Return to the main launcher",
    kind: "home",
    color: 0x39d2c0,
    position: new THREE.Vector3(-1.76, 0.12, 1.7),
    onActivate: async () => navigateToLauncher(),
  });
  if (originStart) {
    addControlTarget({
      id: "model-origin-start",
      label: originStart.label,
      type: "Control",
      actionLabel: originStart.actionLabel,
      kind: "start",
      color: originStart.color,
      position: new THREE.Vector3(-0.58, 0.12, 1.7),
      onActivate: async () => navigateToOriginStart(origin),
    });
  }
  addControlTarget({
    id: "model-return",
    label: originReturn.label,
    type: "Control",
    actionLabel: originReturn.actionLabel,
    kind: "back",
    color: 0x58a6ff,
    position: new THREE.Vector3(originStart ? 0.6 : 0, 0.12, 1.7),
    onActivate: async () => navigateHome(origin),
  });

  state.sceneApi.setBoundarySize(
    new THREE.Vector3(
      Math.max(5.6, size.x + 2.4),
      Math.max(2.6, size.y + 1.2),
      Math.max(4.8, size.z + 3.0),
    ),
  );
  state.pointerController.setBounds(
    new THREE.Vector3(Math.min(center.x - size.x * 0.72, -1.95), 0.14, -1.8),
    new THREE.Vector3(Math.max(center.x + size.x * 0.72, 1.0), Math.max(1.8, size.y + 0.9), 2.1),
  );
  state.pointerController.setPosition(
    new THREE.Vector3(center.x + 0.8, Math.min(size.y + 0.5, 1.25), 0.6),
  );
  assertSceneToken(token);
  finishSceneBuild({
    code: "open-model",
    title: "3D Model Scene",
    subtitle: "The opened object shares space with tactile launcher, origin-start, and home-return controls.",
    context: detailOriginLabel(origin),
    path: item.source?.relative_path ?? item.source?.demo_model_slug ?? item.slug,
    pagination: "1 / 1",
    trail: openedSceneTrail(state.activeWorkspace, item, origin, "Model Scene"),
    idleMessage: `Pointer moving across the opened 3D model ${item.title}.`,
  });
  focusTarget("model-return", { source: "scene", movePointer: false });
  publishStatus(
    `Opened ${item.title} in the model scene as ${itemModelFormatLabel(item)} geometry.`,
    "Ready",
    `open-model-${item.slug}`,
  );
}

function textPageCount(textScene) {
  const maxRow = textScene.cells.length ? Math.max(...textScene.cells.map((cell) => cell.row)) + 1 : 0;
  return Math.max(1, Math.ceil(maxRow / TEXT_ROWS_PER_PAGE));
}

function textPageCells(textScene) {
  const rowStart = textScene.page * TEXT_ROWS_PER_PAGE;
  const rowEnd = rowStart + TEXT_ROWS_PER_PAGE;
  return textScene.cells
    .filter((cell) => cell.row >= rowStart && cell.row < rowEnd)
    .map((cell) => ({ ...cell, localRow: cell.row - rowStart }));
}

function buildTextBoard(pageCells) {
  const width = Math.max(2.4, TEXT_COLUMNS * 0.34 + 0.8);
  const depth = Math.max(1.9, TEXT_ROWS_PER_PAGE * 0.48 + 1.12);
  const group = new THREE.Group();

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.12, depth),
    new THREE.MeshStandardMaterial({
      color: 0x16213a,
      roughness: 0.9,
      metalness: 0.05,
      emissive: 0x08111a,
    }),
  );
  base.position.y = 0.06;
  group.add(base);

  const leftRail = new THREE.Mesh(
    new THREE.BoxGeometry(0.1, 0.08, depth - 0.16),
    new THREE.MeshStandardMaterial({
      color: 0x0f1724,
      roughness: 0.88,
      metalness: 0.04,
      emissive: 0x08111a,
    }),
  );
  leftRail.position.set(-width / 2 + 0.1, 0.1, -0.02);
  group.add(leftRail);

  const frontLip = new THREE.Mesh(
    new THREE.BoxGeometry(width - 0.2, 0.06, 0.08),
    new THREE.MeshStandardMaterial({
      color: 0x111827,
      roughness: 0.86,
      metalness: 0.04,
      emissive: 0x08111a,
    }),
  );
  frontLip.position.set(0, 0.085, depth / 2 - 0.14);
  group.add(frontLip);

  const orientation = new THREE.Mesh(
    new THREE.ConeGeometry(0.08, 0.14, 3),
    new THREE.MeshStandardMaterial({
      color: 0xf2cc60,
      roughness: 0.34,
      metalness: 0.04,
      emissive: 0x4a2d00,
    }),
  );
  orientation.rotation.y = Math.PI;
  orientation.position.set(-width / 2 + 0.18, 0.14, -depth / 2 + 0.22);
  group.add(orientation);

  pageCells.forEach((cell) => {
    const cellGroup = createBrailleCellGroup(cell, TEXT_COLUMNS, 0, {
      spacingX: 0.34,
      spacingZ: 0.48,
      baseColor: 0x111827,
      dotColor: 0xf2cc60,
    });
    cellGroup.position.y = 0.12;
    cellGroup.position.z -= ((TEXT_ROWS_PER_PAGE - 1) * 0.48) / 2 + 0.18;
    group.add(cellGroup);
  });

  return { group, width, depth };
}

async function loadTextScene(item, origin, offset = 0) {
  const maxChars = Number(byId("desktop-text-segment-size").value) || 1200;
  const payload = await fetchJson(itemTextEndpoint(item, offset, maxChars));
  const preview = await fetchBraillePreview(payload.text, TEXT_COLUMNS);
  state.textScene = {
    item,
    origin,
    payload,
    cells: preview.cells,
    page: 0,
  };
}

function renderTextScene(token = state.sceneBuildToken) {
  assertSceneToken(token);
  const textScene = state.textScene;
  const pageCells = textPageCells(textScene);
  const board = buildTextBoard(pageCells);
  prepareScene(
    5.2,
    4.2,
    textScene.item.title,
    "Scene 4: tactile Braille reading board with gallery and launcher return controls.",
    [3.2, 2.8, 4.2],
    [0, 0.18, 0.16],
  );

  state.sceneApi.world.add(board.group);
  const header = createLabelSprite(
    `${textScene.payload.offset + 1} - ${textScene.payload.offset + textScene.payload.loaded_characters} / ${textScene.payload.total_characters}`,
    {
      background: "rgba(13, 17, 23, 0.74)",
      color: "#8b949e",
      fontSize: 15,
    },
  );
  header.position.set(0, 0.3, 1.44);
  state.sceneApi.world.add(header);

  const originStart = originStartConfig(textScene.origin);
  const originReturn = originReturnConfig(textScene.origin);
  addControlTarget({
    id: "text-launcher",
    label: "Launcher",
    type: "Control",
    actionLabel: "Return to the main launcher",
    kind: "home",
    color: 0x39d2c0,
    position: new THREE.Vector3(-2.12, 0.12, 1.78),
    onActivate: async () => navigateToLauncher(),
  });
  if (originStart) {
    addControlTarget({
      id: "text-origin-start",
      label: originStart.label,
      type: "Control",
      actionLabel: originStart.actionLabel,
      kind: "start",
      color: originStart.color,
      position: new THREE.Vector3(-0.98, 0.12, 1.78),
      onActivate: async () => navigateToOriginStart(textScene.origin),
    });
  }
  addControlTarget({
    id: "text-return",
    label: originReturn.label,
    type: "Control",
    actionLabel: originReturn.actionLabel,
    kind: "back",
    color: 0x58a6ff,
    position: new THREE.Vector3(0.16, 0.12, 1.78),
    onActivate: async () => navigateHome(textScene.origin),
  });
  addControlTarget({
    id: "text-prev",
    label: "Previous",
    type: "Control",
    actionLabel: "Move to the previous reading page",
    kind: "previous",
    color: 0x7ee787,
    position: new THREE.Vector3(1.3, 0.12, 1.78),
    onActivate: async () => moveTextScene(-1),
    disabled: textScene.page === 0 && textScene.payload.previous_offset === null,
  });
  addControlTarget({
    id: "text-next",
    label: "Next",
    type: "Control",
    actionLabel: "Move to the next reading page",
    kind: "next",
    color: 0x7ee787,
    position: new THREE.Vector3(2.44, 0.12, 1.78),
    onActivate: async () => moveTextScene(1),
    disabled:
      textScene.page >= textPageCount(textScene) - 1 &&
      textScene.payload.next_offset === null,
  });

  state.sceneApi.setBoundarySize(
    new THREE.Vector3(Math.max(board.width + 1.8, 5.4), 1.0, board.depth + 1.1),
  );
  state.pointerController.setBounds(
    new THREE.Vector3(-2.55, 0.14, -board.depth / 2 + 0.02),
    new THREE.Vector3(2.55, 0.34, 1.95),
  );
  state.pointerController.setPosition(new THREE.Vector3(-0.44, 0.24, 1.22));
  finishSceneBuild({
    code: "open-text",
    title: "Text Reading Scene",
    subtitle: "The reading surface, pagination, and return flow remain inside the bounded 3D scene.",
    context: detailOriginLabel(textScene.origin),
    path: textScene.item.source?.relative_path ?? textScene.item.source?.document_slug ?? textScene.item.slug,
    pagination: `${textScene.page + 1} / ${textPageCount(textScene)}`,
    trail: openedSceneTrail(state.activeWorkspace, textScene.item, textScene.origin, "Reading Scene"),
    idleMessage: `Pointer moving across the reading surface for ${textScene.item.title}.`,
  });
  focusTarget("text-return", { source: "scene", movePointer: false });
}

async function navigateToTextScene(item, origin, offset = 0) {
  const token = beginSceneBuild("text scene");
  await loadTextScene(item, origin, offset);
  renderTextScene(token);
  publishStatus(`Opened ${item.title} in the Braille reading scene.`, "Ready", `open-text-${item.slug}`);
}

async function moveTextScene(step) {
  const textScene = state.textScene;
  if (!textScene) {
    return;
  }
  const pageCount = textPageCount(textScene);
  if (step < 0) {
    if (textScene.page > 0) {
      textScene.page -= 1;
      renderTextScene();
      return;
    }
    if (textScene.payload.previous_offset !== null) {
      await loadTextScene(textScene.item, textScene.origin, textScene.payload.previous_offset);
      state.textScene.page = Math.max(0, textPageCount(state.textScene) - 1);
      renderTextScene();
      return;
    }
    publishStatus("The text scene is already at the first reading page.", "Ready", "text-first");
    return;
  }
  if (textScene.page < pageCount - 1) {
    textScene.page += 1;
    renderTextScene();
    return;
  }
  if (textScene.payload.next_offset !== null) {
    await loadTextScene(textScene.item, textScene.origin, textScene.payload.next_offset);
    renderTextScene();
    return;
  }
  publishStatus("The text scene is already at the last reading page.", "Ready", "text-last");
}

function seekAudio(delta) {
  const player = audioPlayer();
  if (!player.src) {
    return;
  }
  player.currentTime = Math.max(0, Math.min(player.duration || player.currentTime + delta, player.currentTime + delta));
  updateAudioSession();
}

function renderAudioScene(token = state.sceneBuildToken) {
  assertSceneToken(token);
  const audioScene = state.audioScene;
  const player = audioPlayer();
  prepareScene(
    6.4,
    4.2,
    audioScene.item.title,
    "Scene 4: tactile audio transport with seek, return, and launcher controls.",
    [5.2, 3.2, 5.4],
    [0, 0.28, 0],
    true,
  );

  const speaker = buildAudioSymbol(0xf2cc60);
  speaker.position.set(0, 0.12, -0.22);
  speaker.scale.setScalar(1.8);
  state.sceneApi.world.add(speaker);
  const transport = createLabelSprite(
    `${formatSeconds(player.currentTime || 0)} / ${formatSeconds(player.duration)}`,
    {
      background: "rgba(13, 17, 23, 0.72)",
      color: "#8b949e",
      fontSize: 15,
    },
  );
  transport.position.set(0, 0.34, 1.16);
  state.sceneApi.world.add(transport);

  const originStart = originStartConfig(audioScene.origin);
  const originReturn = originReturnConfig(audioScene.origin);
  addControlTarget({
    id: "audio-launcher",
    label: "Launcher",
    type: "Control",
    actionLabel: "Return to the main launcher",
    kind: "home",
    color: 0x39d2c0,
    position: new THREE.Vector3(-2.32, 0.12, 1.46),
    onActivate: async () => navigateToLauncher(),
  });
  if (originStart) {
    addControlTarget({
      id: "audio-origin-start",
      label: originStart.label,
      type: "Control",
      actionLabel: originStart.actionLabel,
      kind: "start",
      color: originStart.color,
      position: new THREE.Vector3(-1.18, 0.12, 1.46),
      onActivate: async () => navigateToOriginStart(audioScene.origin),
    });
  }
  addControlTarget({
    id: "audio-return",
    label: originReturn.label,
    type: "Control",
    actionLabel: originReturn.actionLabel,
    kind: "back",
    color: 0x58a6ff,
    position: new THREE.Vector3(-0.04, 0.12, 1.46),
    onActivate: async () => navigateHome(audioScene.origin),
  });
  addControlTarget({
    id: "audio-toggle",
    label: player.paused ? "Play" : "Pause",
    type: "Control",
    actionLabel: player.paused ? "Start playback" : "Pause playback",
    kind: "playpause",
    color: 0xf2cc60,
    position: new THREE.Vector3(1.12, 0.12, 1.46),
    onActivate: async () => {
      if (player.paused) {
        await player.play();
      } else {
        player.pause();
      }
      renderAudioScene();
    },
  });
  addControlTarget({
    id: "audio-seek-back",
    label: "Back 10s",
    type: "Control",
    actionLabel: "Seek backward ten seconds",
    kind: "seek-back",
    color: 0xf2cc60,
    position: new THREE.Vector3(2.28, 0.12, 1.46),
    onActivate: async () => {
      seekAudio(-SEEK_SECONDS);
      renderAudioScene();
    },
  });
  addControlTarget({
    id: "audio-seek-forward",
    label: "Forward 10s",
    type: "Control",
    actionLabel: "Seek forward ten seconds",
    kind: "seek-forward",
    color: 0xf2cc60,
    position: new THREE.Vector3(3.44, 0.12, 1.46),
    onActivate: async () => {
      seekAudio(SEEK_SECONDS);
      renderAudioScene();
    },
  });

  state.pointerController.setBounds(
    new THREE.Vector3(-2.6, 0.14, -1.5),
    new THREE.Vector3(3.8, 1.0, 1.7),
  );
  state.pointerController.setPosition(new THREE.Vector3(1.12, 0.3, 1.08));
  finishSceneBuild({
    code: "open-audio",
    title: "Audio Scene",
    subtitle: "Playback control is expressed as tactile objects in the same 3D scene.",
    context: detailOriginLabel(audioScene.origin),
    path: audioScene.item.source?.relative_path ?? audioScene.item.source?.audio_slug ?? audioScene.item.slug,
    pagination: "1 / 1",
    trail: openedSceneTrail(state.activeWorkspace, audioScene.item, audioScene.origin, "Audio Scene"),
    idleMessage: `Pointer moving across the audio scene for ${audioScene.item.title}.`,
  });
  focusTarget("audio-toggle", { source: "scene", movePointer: false });
}

async function navigateToAudioScene(item, origin) {
  const token = beginSceneBuild("audio scene");
  const player = audioPlayer();
  player.src = itemRawFileUrl(item);
  player.load();
  state.audioScene = { item, origin };
  updateAudioSession(item);
  renderAudioScene(token);
  publishStatus(`Opened ${item.title} in the audio transport scene.`, "Ready", `open-audio-${item.slug}`);
}

async function openItemScene(item, origin) {
  const kind = resolveItemKind(item);
  if (kind === "model") {
    await navigateToModelScene(item, origin);
    return;
  }
  if (kind === "text") {
    await navigateToTextScene(item, origin);
    return;
  }
  if (kind === "audio") {
    await navigateToAudioScene(item, origin);
    return;
  }
  publishStatus(`${item.title} is not a supported content type yet.`, "Ready", `unsupported-${item.slug}`);
}

function bindFallbackControls() {
  byId("focus-prev").addEventListener("click", () => moveFallbackFocus(-1));
  byId("focus-next").addEventListener("click", () => moveFallbackFocus(1));
  byId("focus-activate").addEventListener("click", () => {
    activateFocusedTarget("fallback").catch((error) =>
      publishStatus(error.message, "Error", "fallback-activate-error"),
    );
  });

  byId("pointer-toggle").addEventListener("change", (event) => {
    state.sceneApi.setPointerVisible(event.target.checked);
  });
  byId("audio-cues-toggle").addEventListener("change", (event) => {
    state.speechEnabled = event.target.checked;
    if (!state.speechEnabled && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    byId("desktop-audio-state").textContent = state.audioScene
      ? audioPlayer().paused
        ? "Paused"
        : "Playing"
      : event.target.checked
        ? "On"
        : "Off";
    publishStatus(
      event.target.checked ? "Spoken cue announcements enabled." : "Spoken cue announcements disabled.",
      "Ready",
      event.target.checked ? "speech-on" : "speech-off",
      { speakMessage: false },
    );
  });
  byId("load-desktop-workspace").addEventListener("click", () => {
    loadWorkspaceBySlug(currentSelectedWorkspaceSlug()).catch((error) =>
      publishStatus(error.message, "Error", "load-workspace-error"),
    );
  });

  document.addEventListener("keydown", (event) => {
    if (
      event.target instanceof HTMLElement &&
      ["INPUT", "TEXTAREA", "SELECT", "OPTION"].includes(event.target.tagName)
    ) {
      return;
    }
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      moveFallbackFocus(-1);
    }
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      moveFallbackFocus(1);
    }
    if (event.key === "Enter") {
      event.preventDefault();
      activateFocusedTarget("fallback").catch((error) =>
        publishStatus(error.message, "Error", "keyboard-activate-error"),
      );
    }
  });
}

function desktopDebugTargets() {
  return Array.from(state.targets.values()).map((target) => ({
    id: target.id,
    title: target.title,
    type: target.type,
    actionLabel: target.actionLabel,
    disabled: target.disabled,
  }));
}

async function activateDebugTarget(targetId) {
  const target = state.targets.get(targetId);
  if (!target) {
    return false;
  }
  state.hoveredTargetId = targetId;
  focusTarget(targetId, { source: "scene", movePointer: false, announceFocus: false });
  await activateFocusedTarget("fallback");
  return true;
}

async function stabilizeDesktopForCapture() {
  state.speechEnabled = false;
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
  await navigateToLauncher();
  state.sceneApi.clearPersistedViewState();
  state.sceneApi.setIdleAnimationEnabled(false);
  state.sceneApi.resetIdleAnimatedObjects();
  state.sceneApi.setViewState(
    {
      position: [4.9, 3.2, 5.1],
      target: [0, 0.28, 0.08],
      zoom: 1,
    },
    { persist: false },
  );
  focusTarget("launcher-hub", { source: "scene", movePointer: false, announceFocus: false });
  state.sceneApi.renderNow();
  return true;
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
      summaryIds: [
        "desktop-scene-label",
        "desktop-scene-context",
        "desktop-scene-path",
        "desktop-announcement",
      ],
    },
    async () => {
      state.sceneApi = createWorkspaceScene(byId("desktop-canvas"), {
        cameraPosition: [4.9, 3.2, 5.1],
        target: [0, 0.28, 0.08],
        boundarySize: new THREE.Vector3(6, 1.8, 5),
        debugKey: "haptic-desktop",
      });

      state.pointerController = attachPointerEmulation(state.sceneApi, {
        initialPosition: new THREE.Vector3(-1.25, 0.36, -0.4),
        boundsMin: new THREE.Vector3(-2.4, 0.14, -1.8),
        boundsMax: new THREE.Vector3(2.4, 1.1, 1.9),
        speed: 1.7,
        onMove: (position) => updatePointerHover(position),
        onActivate: () => {
          activateFocusedTarget("pointer").catch((error) =>
            publishStatus(error.message, "Error", "pointer-activate-error"),
          );
        },
      });

      bindAudioPlayer();
      bindFallbackControls();
      updateWorkspaceSummary();
      updateSceneSummary();
      await loadWorkspaceCatalog();
      await loadWorkspaceBySlug(currentSelectedWorkspaceSlug());
      window.__feelitDesktopDebug = {
        currentScene: () => state.currentScene,
        targetIds: () => Array.from(state.targets.keys()),
        targets: () => desktopDebugTargets(),
        focusTarget: (targetId) => {
          if (!state.targets.has(targetId)) {
            return false;
          }
          focusTarget(targetId, { source: "scene", movePointer: false, announceFocus: false });
          return true;
        },
        activateTarget: async (targetId) => activateDebugTarget(targetId),
        navigateToLauncher: async () => navigateToLauncher(),
        navigateToFileBrowser: async (relativePath = "", page = 0) =>
          navigateToFileBrowser(relativePath, page),
        stabilizeForCapture: async () => stabilizeDesktopForCapture(),
      };
    },
  );
});
